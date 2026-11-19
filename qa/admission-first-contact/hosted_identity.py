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
WORKFLOW = ".github/workflows/qa-oecd-internship-current-policy.yml"
BRANCH = "qa/466-oecd-current-policy"
REF = "refs/heads/" + BRANCH
SOURCES = frozenset(("oecd466",))
PIPELINE_SHA = "11fa75c3e745c5e0d8c12ee8a5c9f8371417d764"
MAINTAINER_ID = 12278069
STARTUP_STATES = frozenset(("queued", "requested", "pending", "waiting"))
STATE_POLLS = 5
POLL_GAP_SECONDS = 2


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


def github_json(path):
    request = urllib.request.Request(
        "https://api.github.com/repos/" + REPOSITORY + path,
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": "Bearer " + os.environ["GITHUB_TOKEN"],
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


def verify_checkout(head, source, scope_bytes):
    """Compare the reviewed inputs to the actual authorized Git revision."""
    workspace = Path(os.environ["GITHUB_WORKSPACE"]).resolve()
    relative_root = ROOT.relative_to(workspace)
    current = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=workspace, timeout=10)
    require(current.decode("ascii").strip() == head, "Checkout HEAD differs from the authorized run")
    inputs = (
        Path(WORKFLOW), relative_root / "scope-OFF.json", relative_root / "reviewer.pem",
        relative_root / "hosted_identity.py", relative_root / "run.py",
        relative_root / source / "foundation.py", relative_root / source / "history-manifest.json",
    )
    for relative in inputs:
        committed = subprocess.check_output(
            ["git", "show", f"{head}:{relative.as_posix()}"], cwd=workspace, timeout=10,
        )
        local = workspace / relative
        require(local.resolve() == local and local.read_bytes() == committed,
                f"Checked-out input differs: {relative}")
        if relative == relative_root / "scope-OFF.json":
            require(scope_bytes == committed, "Scope bytes used to authorize differ from the commit")


def verify_grant(head, manifest_bytes, run_created):
    """Find the one unedited, pre-run authorization for this head and scope."""
    def timestamp(value):
        return type(value) is str and re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z", value)

    require(timestamp(run_created), "Missing exact workflow creation time")
    head_line = f"Approved OECD current-policy research head {head}"
    scope_line = f"OECD current-policy research scope {hashlib.sha256(manifest_bytes).hexdigest()}"
    matches = []
    for page in range(1, 6):
        comments = public_pipeline_json(f"/issues/466/comments?per_page=100&page={page}")
        require(type(comments) is list and len(comments) <= 100, "Unexpected OECD approval inventory")
        for comment in comments:
            body = comment.get("body")
            if type(body) is not str:
                continue
            lines = body.splitlines()
            if lines.count(head_line) != 1 or lines.count(scope_line) != 1:
                continue
            comment_id = comment.get("id")
            created = comment.get("created_at")
            url = f"https://github.com/YouthOpps/data-pipeline/issues/466#issuecomment-{comment_id}"
            if (type(comment_id) is int and comment_id > 0
                    and comment.get("html_url") == url
                    and comment.get("issue_url") == "https://api.github.com/repos/YouthOpps/data-pipeline/issues/466"
                    and nested(comment, "user.id") == MAINTAINER_ID
                    and nested(comment, "user.type") == "User"
                    and timestamp(created) and created < run_created
                    and created == comment.get("updated_at")):
                matches.append(url)
        if len(comments) < 100:
            break
    else:
        raise RuntimeError("Incomplete OECD approval inventory")
    require(len(matches) == 1, "Expected one exact unedited maintainer approval before the run")
    return matches[0]


def public_pipeline_json(path):
    """Read the public control plane without sending the job's repository token."""
    request = urllib.request.Request(
        "https://api.github.com/repos/YouthOpps/data-pipeline" + path,
        headers={"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"},
    )
    with urllib.request.build_opener(RejectRedirect()).open(request, timeout=15) as response:
        require(response.status == 200, "Unexpected public GitHub response")
        payload = response.read(2_000_001)
    require(len(payload) <= 2_000_000, "Public control response too large")
    return json.loads(payload)


def verify_predecessors():
    """Require both original owners to be retired with exact retained evidence."""
    expected_runs = (
        (423618840, 44493996966, 135456424153, '19b66041abb14dc185a3d057e51f75067d1dfa34',
         'qa/oecd-internship-first-contact', '.github/workflows/qa-oecd-internship-first-contact.yml',
         'failure', 'First contact oecd466', 14513987716,
         'first-contact-oecd466-44493996966-1', 11674, '4bca638b64fe19f4f09cc7b04224e98c9d3d650b6f5df7d0ee0f1ad15e9ab1bd'),
        (423737141, 44513148049, 135522229648, '9192a7c15ee0465986f16ab8dcf4ad11336f784a',
         'qa/466-oecd-received-rep-settlement', '.github/workflows/qa-oecd-received-rep-settlement.yml',
         'success', 'settle', 14524258160, 'oecd466-rep-settlement', 1469, 'fdb2d84f14a839157c486f32a54b5911ce749bdacfef1765bfc99be87cb395bf'),
    )
    for (workflow, run_id, job_id, head, branch, workflow_path, conclusion, job_name,
         artifact_id, artifact_name, size, archive_digest) in expected_runs:
        expected = {
            "id": run_id, "workflow_id": workflow, "run_attempt": 1, "event": "push",
            "head_sha": head, "head_branch": branch, "path": workflow_path,
            "status": "completed", "conclusion": conclusion,
            "repository.full_name": REPOSITORY, "head_repository.full_name": REPOSITORY,
            "actor.id": MAINTAINER_ID, "actor.type": "User",
            "triggering_actor.id": MAINTAINER_ID, "triggering_actor.type": "User",
        }
        check_fields(github_json(f"/actions/workflows/{workflow}"), {
            "id": workflow, "path": workflow_path, "state": "disabled_manually",
        }, "Exact predecessor owner or retirement differs")
        check_fields(github_json(f"/actions/runs/{run_id}/attempts/1"), expected, "Predecessor run differs")
        inventory = github_json(f"/actions/workflows/{workflow}/runs?per_page=2")
        require(inventory["total_count"] == 1 and len(inventory["workflow_runs"]) == 1,
                "Exact predecessor inventory differs")
        check_fields(inventory["workflow_runs"][0], expected, "Predecessor workflow inventory differs")
        jobs = github_json(f"/actions/runs/{run_id}/attempts/1/jobs?per_page=2")
        require(jobs["total_count"] == 1 and len(jobs["jobs"]) == 1, "Predecessor job inventory differs")
        check_fields(jobs["jobs"][0], {
            "id": job_id, "run_id": run_id, "head_sha": head, "name": job_name,
            "status": "completed", "conclusion": conclusion,
        }, "Predecessor exact job differs")
        rows = github_json(f"/actions/runs/{run_id}/artifacts?per_page=2")
        require(rows["total_count"] == 1 and len(rows["artifacts"]) == 1,
                "Exact predecessor artifact inventory differs")
        check_fields(rows["artifacts"][0], {
            "id": artifact_id, "name": artifact_name, "size_in_bytes": size,
            "expired": False, "digest": "sha256:" + archive_digest,
            "workflow_run.id": run_id, "workflow_run.head_sha": head,
        }, "Exact predecessor artifact differs")


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
        "GITHUB_ACTOR_ID": str(MAINTAINER_ID),
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
        "after": sha, "repository.full_name": REPOSITORY, "sender.id": MAINTAINER_ID,
        "sender.type": "User",
    }, "Not an exact first branch creation")
    run_id = int(run_text)
    run = poll_active(f"/actions/runs/{run_id}", {
        "id": run_id, "event": "push", "run_attempt": 1, "head_branch": BRANCH,
        "head_sha": sha, "path": WORKFLOW, "head_repository.full_name": REPOSITORY,
        "repository.full_name": REPOSITORY, "actor.id": MAINTAINER_ID,
        "triggering_actor.id": MAINTAINER_ID, "actor.type": "User", "triggering_actor.type": "User",
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
    require(public_pipeline_json("/branches/main")["commit"]["sha"] == PIPELINE_SHA,
            "Published producer inventory changed since scope review")
    raw = (ROOT / "scope-OFF.json").read_bytes()
    manifest = json.loads(raw)
    require(manifest["enabled"] is True and set(manifest["sources"]) == SOURCES,
            "First contact is OFF")
    row = manifest["sources"][source]
    require(row.get("issue") == 466 and "decision" not in row, "Invalid committed maintainer gate")
    verify_checkout(sha, source, raw)
    decision = verify_grant(sha, raw, run.get("created_at"))
    return {
        "repository": REPOSITORY, "ref": REF, "workflow": WORKFLOW, "head_sha": sha,
        "run_id": run_id, "run_attempt": 1, "workflow_id": run["workflow_id"],
        "job_id": job["id"], "source": source, "decision": decision,
        "scope_sha256": hashlib.sha256(raw).hexdigest(),
    }, manifest
