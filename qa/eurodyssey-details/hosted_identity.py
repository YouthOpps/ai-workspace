"""Identity checks for this temporary, nonpublishing GitHub Actions workflow."""

import hashlib
import json
import os
import re
import subprocess
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPOSITORY = "YouthOpps/ai-workspace"
WORKFLOW = ".github/workflows/qa-eurodyssey-internships-details.yml"
BRANCH = "qa/eurodyssey-internships-details"
REF = "refs/heads/" + BRANCH
SOURCES = frozenset(("eurodyssey",))
STARTUP_STATES = frozenset(("queued", "requested", "pending", "waiting"))
STATE_POLLS = 5
POLL_GAP_SECONDS = 2
UTC_SECOND = re.compile(r"[0-9]{4}(?:-[0-9]{2}){2}T[0-9]{2}(?::[0-9]{2}){2}Z")


class IdentityFailure(RuntimeError):
    """Carry only explicit, sanitized GitHub identity mismatches."""

    def __init__(self, reason, fields):
        self.reason = reason
        self.fields = fields
        super().__init__(f"{reason}: {json.dumps(fields, sort_keys=True)}")


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


class RejectRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def github_json(path, repository=REPOSITORY):
    request = urllib.request.Request(
        "https://api.github.com/repos/" + repository + path,
        headers={
            "Accept": "application/vnd.github+json",
            **({"Authorization": "Bearer " + os.environ["GITHUB_TOKEN"]}
               if repository == REPOSITORY else {}),
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    with urllib.request.build_opener(RejectRedirect()).open(request, timeout=15) as response:
        require(response.status == 200, "Unexpected GitHub identity response")
        payload = response.read(2_000_001)
    require(len(payload) <= 2_000_000, "GitHub identity response too large")
    return json.loads(payload)


def nested(row, field):
    for key in field.split("."):
        if type(row) is not dict:
            return None
        row = row.get(key)
    return row


def display(value):
    if type(value) in (bool, int) or value is None:
        return value
    if type(value) is str and re.fullmatch(r"[a-zA-Z0-9_. /@-]{1,165}", value):
        return value
    return f"invalid {type(value).__name__}"


def check_fields(row, expected, reason):
    fields = {}
    for field, wanted in expected.items():
        observed = nested(row, field)
        if type(observed) is not type(wanted) or observed != wanted:
            fields[field] = {"expected": display(wanted), "observed": display(observed)}
    if fields:
        raise IdentityFailure(reason, fields)


def poll_active(path, immutable, kind, select=lambda rows: rows):
    for poll in range(STATE_POLLS):
        row = select(github_json(path))
        check_fields(row, immutable, f"{kind} immutable identity mismatch")
        state = nested(row, "status")
        if state == "in_progress":
            return row
        # Poll only an exact immutable match with a recognized startup status.
        # Terminal states, missing fields or unrelated jobs are not eventuality.
        if type(state) is not str or state not in STARTUP_STATES or poll == STATE_POLLS - 1:
            raise IdentityFailure(
                f"{kind} not active",
                {"status": {"expected": "in_progress", "observed": display(state)},
                 "checks": poll + 1},
            )
        time.sleep(POLL_GAP_SECONDS)


def verify_run(source):
    """Accept only the sole, actual first-creation run and its active named job."""
    env = os.environ
    require(source in SOURCES and env.get("SOURCE") == source, "Source identity mismatch")
    required = {
        "GITHUB_ACTIONS": "true",
        "GITHUB_REPOSITORY": REPOSITORY,
        "GITHUB_REF": REF,
        "GITHUB_EVENT_NAME": "push",
        "GITHUB_RUN_ATTEMPT": "1",
        "GITHUB_WORKFLOW_REF": f"{REPOSITORY}/{WORKFLOW}@{REF}",
        "GITHUB_JOB": "contact",
        "GITHUB_ACTOR_ID": "12278069",
    }
    check_fields(dict(env), required, "Wrong hosted scope")
    require("DATA_SOURCE_TOKEN" not in env and "GITHUB_TOKEN" in env, "Wrong credential scope")
    event = json.loads(Path(env["GITHUB_EVENT_PATH"]).read_bytes())
    sha, run_text = env["GITHUB_SHA"], env["GITHUB_RUN_ID"]
    require(re.fullmatch(r"[0-9a-f]{40}", sha) and re.fullmatch(r"[1-9][0-9]*", run_text),
            "Invalid hosted identity")
    require(env.get("GITHUB_WORKFLOW_SHA") == sha, "Workflow revision differs from job head")
    check_fields(event, {
        "created": True, "deleted": False, "ref": REF, "before": "0" * 40,
        "after": sha, "repository.full_name": REPOSITORY,
        "sender.id": 12278069, "sender.type": "User",
    }, "Not an exact first branch creation")
    run_id = int(run_text)
    run = poll_active(f"/actions/runs/{run_id}", {
        "id": run_id, "event": "push", "run_attempt": 1, "head_branch": BRANCH,
        "head_sha": sha, "path": WORKFLOW, "head_repository.full_name": REPOSITORY,
        "repository.full_name": REPOSITORY, "actor.id": 12278069,
        "triggering_actor.id": 12278069, "triggering_actor.type": "User",
        "actor.type": "User",
    }, "Run API")
    branch = urllib.parse.quote(BRANCH, safe="")
    history = github_json(f"/actions/runs?branch={branch}&event=push&per_page=2")
    require(history["total_count"] == 1 and [x["id"] for x in history["workflow_runs"]] == [run_id],
            "Branch already has a run or history is ambiguous")

    def select_job(jobs):
        selected = [job for job in jobs["jobs"] if job["name"] == f"First contact {source}"]
        if len(selected) != 1:
            raise IdentityFailure("Active job inventory mismatch", {"exact_matches": len(selected)})
        return selected[0]

    job = poll_active(f"/actions/runs/{run_id}/attempts/1/jobs?per_page=10", {
        "run_id": run_id, "head_sha": sha,
    }, "Job API", select_job)
    require(type(run.get("workflow_id")) is int and type(job.get("id")) is int,
            "Unexpected current workflow or job identifier")
    created = run.get("created_at")
    require(type(created) is str and UTC_SECOND.fullmatch(created), "Invalid run creation time")
    return {
        "repository": REPOSITORY, "ref": REF, "workflow": WORKFLOW, "head_sha": sha,
        "run_id": run_id, "run_attempt": 1, "workflow_id": run["workflow_id"],
        "job_id": job["id"], "source": source,
        "created_at": created,
    }


PIPELINE = "YouthOpps/data-pipeline"
ISSUE = 460
ACTOR_ID = 12278069
BRANCH_SUBTREE = "qa/eurodyssey-details"
COLLISION = r"euro[-_ ]?dyssey|eurodyss[ée]e|eurodyssey\.aer\.eu"
WORKFLOW_COLLISION = re.compile(r"euro[-_ ]?dyssey|eurodyss[ée]e", re.I)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def exact_checkout(scope, scope_bytes):
    workspace = Path(os.environ["GITHUB_WORKSPACE"])
    head = scope["head_sha"]
    required = (
        f"{BRANCH_SUBTREE}/scope-OFF.json", f"{BRANCH_SUBTREE}/hosted_identity.py",
        f"{BRANCH_SUBTREE}/run.py", f"{BRANCH_SUBTREE}/eurodyssey/foundation.py",
        f"{BRANCH_SUBTREE}/eurodyssey/history-manifest.json", f"{BRANCH_SUBTREE}/reviewer.pem",
        WORKFLOW,
    )
    actual_head = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=workspace, timeout=10, text=True,
    ).strip()
    require(actual_head == head, "Checkout head differs from the authorized Actions run")
    for relative in required:
        committed = subprocess.check_output(
            ["git", "show", f"{head}:{relative}"], cwd=workspace, timeout=10,
        )
        local = workspace / relative
        require(local.resolve() == local and local.read_bytes() == committed,
                "Immutable checked-out input differs: " + relative)
        if relative == f"{BRANCH_SUBTREE}/scope-OFF.json":
            require(scope_bytes == committed, "Scope bytes used to authorize differ from the commit")


def verify_pipeline_inventory(scope):
    """Bind the actual pipeline input and check possible publisher collisions."""
    checkout = Path(os.environ["GITHUB_WORKSPACE"]) / ".eurodyssey-pipeline"
    current = github_json("/branches/main", PIPELINE)["commit"]["sha"]
    checked_out = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=checkout, timeout=10,
    ).decode("ascii").strip()
    require(re.fullmatch(r"[0-9a-f]{40}", current) and checked_out == current,
            "Pipeline main changed since its independent checkout")
    matches = subprocess.run(
        ["git", "grep", "-ilE", COLLISION, current, "--", "adapters", ".github/workflows"],
        cwd=checkout, capture_output=True, timeout=15, check=False,
    )
    require(matches.returncode == 1 and not matches.stdout and not matches.stderr,
            "Possible Eurodyssey production publisher ownership")
    for repository in (REPOSITORY, PIPELINE):
        for page in range(1, 11):
            batch = github_json(f"/actions/workflows?per_page=100&page={page}", repository)
            workflows = batch.get("workflows")
            require(type(workflows) is list, "Incomplete workflow inventory")
            for workflow in workflows:
                known = (workflow.get("id"), workflow.get("path"))
                if (repository == REPOSITORY and known in (
                        (scope["workflow_id"], WORKFLOW), (423622763, '.github/workflows/qa-eurodyssey-internships-first-contact.yml'))):
                    continue
                require(not WORKFLOW_COLLISION.search(workflow["name"] + " " + workflow["path"]),
                        "Possible Eurodyssey workflow history")
            if len(workflows) < 100:
                break
        else:
            raise RuntimeError("Incomplete workflow pagination")
    return current


def verify_approval(scope, scope_sha256):
    head_line = f"Approved Eurodyssey detail research head {scope['head_sha']}"
    scope_line = f"Eurodyssey detail research scope {scope_sha256}"
    matches = []
    for page in range(1, 6):
        rows = github_json(f"/issues/{ISSUE}/comments?per_page=100&page={page}", PIPELINE)
        require(type(rows) is list, "Invalid approval comment inventory")
        for comment in rows:
            user = comment.get("user") or {}
            if user.get("id") != ACTOR_ID or user.get("type") != "User":
                continue
            lines = (comment.get("body") or "").splitlines()
            if head_line not in lines or scope_line not in lines:
                continue
            comment_id = comment.get("id")
            url = f"https://github.com/{PIPELINE}/issues/{ISSUE}#issuecomment-{comment_id}"
            created = comment.get("created_at")
            require(
                type(comment_id) is int and comment_id > 0
                and comment.get("html_url") == url
                and comment.get("issue_url") == f"https://api.github.com/repos/{PIPELINE}/issues/{ISSUE}"
                and type(created) is str and UTC_SECOND.fullmatch(created)
                and created < scope["created_at"] and comment.get("updated_at") == created
                and lines.count(head_line) == lines.count(scope_line) == 1,
                "Exact maintainer grant is late, altered or malformed",
            )
            matches.append(url)
        if len(rows) < 100:
            break
    else:
        raise RuntimeError("Incomplete approval comment pagination")
    require(len(matches) == 1, "Expected exactly one pre-run unedited maintainer grant")
    return matches[0]


def verify_predecessor():
    """Require the exact retired sole Eurodyssey owner and intact GitHub artifact."""
    workflow_id = 423622763
    run_id = 44494669298
    expected = {
        "id": run_id, "workflow_id": workflow_id, "run_attempt": 1, "event": "push",
        "head_sha": 'bf650e2eeaefbecff58513381b54b235ef5a9417', "head_branch": 'qa/eurodyssey-internships-first-contact',
        "path": '.github/workflows/qa-eurodyssey-internships-first-contact.yml', "status": "completed", "conclusion": "success",
        "repository.full_name": REPOSITORY, "head_repository.full_name": REPOSITORY,
        "actor.id": ACTOR_ID, "actor.type": "User",
        "triggering_actor.id": ACTOR_ID, "triggering_actor.type": "User",
    }
    check_fields(github_json(f"/actions/workflows/{workflow_id}"), {
        "id": workflow_id, "path": '.github/workflows/qa-eurodyssey-internships-first-contact.yml', "state": "disabled_manually",
    }, "Exact retired Eurodyssey owner differs")
    check_fields(github_json(f"/actions/runs/{run_id}/attempts/1"), expected,
                 "Exact retired Eurodyssey run differs")
    runs = github_json(f"/actions/workflows/{workflow_id}/runs?per_page=2")
    require(runs["total_count"] == 1 and len(runs["workflow_runs"]) == 1,
            "Retired Eurodyssey owner run inventory differs")
    check_fields(runs["workflow_runs"][0], expected, "Retired Eurodyssey history differs")
    jobs = github_json(f"/actions/runs/{run_id}/attempts/1/jobs?per_page=10")
    require(jobs["total_count"] == 1 and len(jobs["jobs"]) == 1,
            "Retired Eurodyssey job inventory differs")
    check_fields(jobs["jobs"][0], {
        "id": 135458713577, "run_id": run_id, "head_sha": 'bf650e2eeaefbecff58513381b54b235ef5a9417',
        "name": "First contact eurodyssey", "status": "completed", "conclusion": "success",
    }, "Exact predecessor job differs")
    artifacts = github_json(f"/actions/runs/{run_id}/artifacts?per_page=2")
    require(artifacts["total_count"] == 1 and len(artifacts["artifacts"]) == 1,
            "Retired Eurodyssey artifact inventory differs")
    check_fields(artifacts["artifacts"][0], {
        "id": 14515050477, "name": 'eurodyssey-first-contact-44494669298-1',
        "size_in_bytes": 137499, "expired": False,
        "digest": "sha256:6eb2ea7cefa43baff84956ac8fcd7ae85c1c7ac043cf8596f0f8b2427643b51d", "workflow_run.id": run_id,
        "workflow_run.head_sha": 'bf650e2eeaefbecff58513381b54b235ef5a9417',
    }, "Exact Eurodyssey predecessor artifact differs")


def verify_authority(source):
    raw = (ROOT / "scope-OFF.json").read_bytes()
    manifest = json.loads(raw)
    require(__debug__ and manifest.get("enabled") is True and set(manifest["sources"]) == SOURCES,
            "Eurodyssey bounded research is OFF")
    scope = verify_run(source)
    exact_checkout(scope, raw)
    row = dict(manifest["sources"][source])
    require(row.get("issue") == ISSUE and "decision" not in row, "Invalid committed maintainer gate")
    scope["scope_sha256"] = sha(raw)
    row["decision"] = verify_approval(scope, scope["scope_sha256"])
    verify_predecessor()
    scope["pipeline_inventory_head"] = verify_pipeline_inventory(scope)
    return scope, manifest, row
