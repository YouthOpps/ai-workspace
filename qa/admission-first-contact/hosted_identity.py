"""Identity checks for this temporary, nonpublishing GitHub Actions workflow."""

import hashlib
import json
import os
import re
import subprocess
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPOSITORY = "YouthOpps/ai-workspace"
WORKFLOW = ".github/workflows/qa-gm-complete-inventory-254.yml"
BRANCH = "qa/gm-complete-inventory-254"
REF = "refs/heads/" + BRANCH
SOURCES = frozenset(("gm254",))
PIPELINE = "YouthOpps/data-pipeline"
ISSUE = 254
SUBTREE = "qa/admission-first-contact"
PIPELINE_SHA = "5f4d0f7c6b485a88e9f2901d6fe515ca5c1094db"
MAINTAINER_ID = 12278069
UTC_SECOND = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z")
STARTUP_STATES = frozenset(("queued", "requested", "pending", "waiting"))
STATE_POLLS = 5
POLL_GAP_SECONDS = 2


class IdentityFailure(RuntimeError):
    """Carry only explicit, sanitized GitHub identity mismatches."""

    def __init__(self, reason, fields):
        self.reason = reason
        self.fields = fields
        super().__init__(f"{reason}: {json.dumps(fields, sort_keys=True)}")


class GitHubControlFailure(IdentityFailure):
    """Report the requested GitHub control and safe status metadata only."""


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


class RejectRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


ETAGS = {}


def control_json(repository, path):
    allowed = (
        repository == REPOSITORY and re.fullmatch(r"/actions/[a-zA-Z0-9/?=_&%-]+", path)
        or repository == PIPELINE and (
            path == "/git/ref/heads/main"
            or re.fullmatch(rf"/issues/{ISSUE}/comments\?per_page=100&page=[1-5]", path)))
    require(allowed, "Unreviewed GitHub control endpoint")
    request = urllib.request.Request(
        "https://api.github.com/repos/" + repository + path,
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": "Bearer " + os.environ["GITHUB_TOKEN"],
            "X-GitHub-Api-Version": "2022-11-28",
        },
        method="GET",
    )
    endpoint = f"/repos/{repository}{path}"
    cached = ETAGS.get(endpoint)
    if cached:
        request.add_header("If-None-Match", cached[0])
    try:
        with urllib.request.build_opener(RejectRedirect()).open(request, timeout=15) as response:
            require(response.status == 200, "Unexpected GitHub control response")
            etag = response.headers.get("ETag")
            payload = response.read(2_000_001)
    except urllib.error.HTTPError as failure:
        if failure.code == 304 and cached:
            failure.close()
            return json.loads(cached[1])
        fields = {"endpoint": endpoint, "status": failure.code}
        for header, field in (
            ("X-RateLimit-Limit", "rate_limit"),
            ("X-RateLimit-Remaining", "rate_limit_remaining"),
            ("X-RateLimit-Reset", "rate_limit_reset"),
            ("Retry-After", "retry_after_seconds"),
        ):
            value = failure.headers.get(header) if failure.headers is not None else None
            if isinstance(value, str) and re.fullmatch(r"[0-9]{1,12}", value):
                fields[field] = int(value)
        try:
            failure.close()
        except Exception:
            fields["close_error"] = True
        raise GitHubControlFailure("GitHub control HTTP failure", fields) from None
    except urllib.error.URLError:
        raise GitHubControlFailure("GitHub control connection failure", {"endpoint": endpoint}) from None
    require(len(payload) <= 2_000_000, "GitHub control response too large")
    if etag:
        ETAGS[endpoint] = (etag, payload)
    else:
        ETAGS.pop(endpoint, None)
    return json.loads(payload)


def github_json(path):
    return control_json(REPOSITORY, path)


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


def exact_checkout(head, source, scope_bytes):
    workspace = Path(os.environ["GITHUB_WORKSPACE"])
    required = (
        WORKFLOW, f"{SUBTREE}/hosted_identity.py", f"{SUBTREE}/run.py",
        f"{SUBTREE}/scope-OFF.json", f"{SUBTREE}/reviewer.pem",
        f"{SUBTREE}/{source}/foundation.py", f"{SUBTREE}/{source}/history-manifest.json",
    )
    checked_out = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=workspace, timeout=10, text=True,
    ).strip()
    require(checked_out == head, "Checkout head differs from the authorized Actions run")
    for relative in required:
        committed = subprocess.check_output(
            ["git", "show", f"{head}:{relative}"], cwd=workspace, timeout=10,
        )
        local = workspace / relative
        require(local.resolve() == local and local.read_bytes() == committed,
                "Immutable checked-out input differs: " + relative)
        if relative == f"{SUBTREE}/scope-OFF.json":
            require(scope_bytes == committed, "Scope bytes used to authorize differ from the commit")


def verify_approval(scope, scope_sha256):
    head_line = f"Approved General Motors complete inventory research head {scope['head_sha']}"
    scope_line = f"General Motors complete inventory research scope {scope_sha256}"
    matches = []
    for page in range(1, 6):
        rows = public_pipeline_json(f"/issues/{ISSUE}/comments?per_page=100&page={page}")
        require(type(rows) is list, "Invalid approval comment inventory")
        for comment in rows:
            user = comment.get("user") or {}
            if user.get("id") != MAINTAINER_ID or user.get("type") != "User":
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


def public_pipeline_json(path):
    """Authenticate the approved read-only public pipeline control endpoints."""
    return control_json(PIPELINE, path)


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
        "after": sha, "repository.full_name": REPOSITORY,
        "sender.id": MAINTAINER_ID, "sender.type": "User",
    }, "Not an exact first branch creation")
    run_id = int(run_text)
    run = poll_active(f"/actions/runs/{run_id}", {
        "id": run_id, "event": "push", "run_attempt": 1, "head_branch": BRANCH,
        "head_sha": sha, "path": WORKFLOW, "head_repository.full_name": REPOSITORY,
        "repository.full_name": REPOSITORY, "actor.id": MAINTAINER_ID,
        "triggering_actor.id": MAINTAINER_ID, "actor.type": "User",
        "triggering_actor.type": "User",
    }, "Run API")
    branch = urllib.parse.quote(BRANCH, safe="")
    for poll in range(STATE_POLLS):
        history = github_json(f"/actions/runs?branch={branch}&event=push&per_page=2")
        if history.get("total_count") != 0 or history.get("workflow_runs") != []:
            break
        if poll < STATE_POLLS - 1:
            time.sleep(POLL_GAP_SECONDS)
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
    require(public_pipeline_json("/git/ref/heads/main")["object"]["sha"] == PIPELINE_SHA,
            "Published producer inventory changed since scope review")
    registered = github_json(f"/actions/workflows/{run['workflow_id']}")
    check_fields(registered, {"id": run["workflow_id"], "path": WORKFLOW, "state": "active"},
                 "Current discovery workflow differs")
    created = run.get("created_at")
    require(type(created) is str and UTC_SECOND.fullmatch(created), "Invalid run creation time")
    return {
        "repository": REPOSITORY, "ref": REF, "workflow": WORKFLOW, "head_sha": sha,
        "run_id": run_id, "run_attempt": 1, "workflow_id": run["workflow_id"],
        "job_id": job["id"], "source": source, "created_at": created,
    }


def verify_predecessor():
    """Require every prior owner to retain its only retired attempt and artifact."""
    predecessors = ((426090445, 44921395475, 136897992143, '55b11540bc617b3b58dc05532122bd97cb0d229e', 'qa/gm-inventory-discovery-254', '.github/workflows/qa-gm-inventory-discovery-254.yml', 'success', 'First contact gm254', 14713554753, 'first-contact-gm254-44921395475-1', 170325, '0f374f794f8f73a0404df6ed32dd2a6dc0cdcb9c69494b033084b87d4d0d8f22'), (426095264, 44921966565, 136899763225, '8cc2e39c30a61a723db6cd779873622ee6f9adfe', 'qa/gm-specific-discovery-254', '.github/workflows/qa-gm-specific-discovery-254.yml', 'success', 'First contact gm254', 14713818663, 'first-contact-gm254-44921966565-1', 151583, '95fe062965bef229c39a46db14168b790b6139092af9541c5e3e4a28dd6ae532'), (431478707, 45803204708, 139851505482, '6f6bca1855828779dd52cb671a2aea472e5d806a', 'qa/gm-students-inventory-254', '.github/workflows/qa-gm-students-inventory-254.yml', 'success', 'First contact gm254', 15108427520, 'first-contact-gm254-45803204708-1', 187336, '6480efaa1e1376b9cb322e573f433e18f8c8d8f29817775cf012b18b41330c70'))
    for (workflow, run_id, job_id, head, branch, path, conclusion, job_name,
         artifact_id, artifact_name, size, archive_digest) in predecessors:
        expected = {
            "id": run_id, "workflow_id": workflow, "run_attempt": 1, "event": "push",
            "head_sha": head, "head_branch": branch, "path": path,
            "status": "completed", "conclusion": conclusion,
            "repository.full_name": REPOSITORY, "head_repository.full_name": REPOSITORY,
            "actor.id": MAINTAINER_ID, "actor.type": "User",
            "triggering_actor.id": MAINTAINER_ID, "triggering_actor.type": "User",
        }
        check_fields(github_json(f"/actions/workflows/{workflow}"), {
            "id": workflow, "path": path, "state": "disabled_manually",
        }, "Exact predecessor owner or retirement differs")
        check_fields(github_json(f"/actions/runs/{run_id}"), expected, "Latest predecessor attempt differs")
        check_fields(github_json(f"/actions/runs/{run_id}/attempts/1"), expected, "Predecessor run differs")
        inventory = github_json(f"/actions/workflows/{workflow}/runs?per_page=2")
        require(inventory["total_count"] == 1 and len(inventory["workflow_runs"]) == 1,
                "Exact predecessor run inventory differs")
        check_fields(inventory["workflow_runs"][0], expected, "Predecessor workflow inventory differs")
        jobs = github_json(f"/actions/runs/{run_id}/attempts/1/jobs?per_page=2")
        require(jobs["total_count"] == 1 and len(jobs["jobs"]) == 1, "Exact predecessor job inventory differs")
        check_fields(jobs["jobs"][0], {
            "id": job_id, "run_id": run_id, "head_sha": head, "name": job_name,
            "head_branch": branch, "run_attempt": 1, "status": "completed", "conclusion": conclusion,
        }, "Predecessor job differs")
        artifacts = github_json(f"/actions/runs/{run_id}/artifacts?per_page=2")
        require(artifacts["total_count"] == 1 and len(artifacts["artifacts"]) == 1,
                "Exact predecessor artifact inventory differs")
        check_fields(artifacts["artifacts"][0], {
            "id": artifact_id, "name": artifact_name, "size_in_bytes": size,
            "expired": False, "digest": "sha256:" + archive_digest,
            "workflow_run.id": run_id, "workflow_run.head_sha": head, "workflow_run.head_branch": branch,
        }, "Predecessor artifact differs")


def verify_authority(source):
    raw = (ROOT / "scope-OFF.json").read_bytes()
    manifest = json.loads(raw)
    require(__debug__ and manifest.get("enabled") is True and set(manifest["sources"]) == SOURCES,
            "General Motors careers inventory contact is OFF")
    row = dict(manifest["sources"][source])
    require(row.get("issue") == ISSUE and "decision" not in row, "Invalid committed maintainer gate")
    scope = verify_run(source)
    verify_predecessor()
    exact_checkout(scope["head_sha"], source, raw)
    scope["scope_sha256"] = hashlib.sha256(raw).hexdigest()
    row["decision"] = verify_approval(scope, scope["scope_sha256"])
    return scope, manifest, row
