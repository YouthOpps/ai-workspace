"""Identity checks for this temporary, nonpublishing GitHub Actions workflow."""

import hashlib
import json
import os
import re
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPOSITORY = "YouthOpps/ai-workspace"
WORKFLOW = ".github/workflows/qa-strasbourg-legal-notice.yml"
BRANCH = "qa/strasbourg-legal-notice"
REF = "refs/heads/" + BRANCH
SOURCES = frozenset(("strasbourg443legal",))
PIPELINE_SHA = "14d919910e81aa3e9ad06fcd69051e8d9fbf8c9c"
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


def verify_grant(manifest, source):
    """Bind the explicit source decision to the frozen OFF scope."""
    row = manifest["sources"][source]
    decision = row["decision"]
    match = re.fullmatch(
        r"https://github\.com/YouthOpps/data-pipeline/issues/443#issuecomment-([1-9][0-9]*)",
        decision or "",
    )
    require(manifest["enabled"] is True and set(manifest["sources"]) == SOURCES
            and match is not None, "First contact is OFF or unreviewed")
    off = json.loads(json.dumps(manifest))
    off["enabled"] = False
    off["sources"][source]["decision"] = None
    canonical = json.dumps(off, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    digest = hashlib.sha256(canonical).hexdigest()
    result = public_pipeline_json(f"/issues/comments/{match[1]}")
    require(
        result.get("html_url") == decision
        and result.get("issue_url") == "https://api.github.com/repos/YouthOpps/data-pipeline/issues/443"
        and result.get("user", {}).get("id") == MAINTAINER_ID
        and result.get("created_at") == result.get("updated_at")
        and type(result.get("created_at")) is str
        and f"Approved Strasbourg #443 legal-notice scope {digest}" in result.get("body", "").splitlines(),
        "Exact maintainer decision is absent or changed",
    )


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


def verify_predecessor():
    """Refuse access if the exact retired source owner or artifact changes."""
    workflow = 422217365
    run_id = 44243944283
    expected = {
        "id": run_id, "workflow_id": workflow, "run_attempt": 1, "event": "push",
        "head_sha": '67fcdce0f697cb293dc9472089848f4c0dfdd77b', "head_branch": "qa/strasbourg-admission-first-contact",
        "path": '.github/workflows/qa-strasbourg-admission-first-contact.yml', "status": "completed", "conclusion": "success",
        "repository.full_name": REPOSITORY, "head_repository.full_name": REPOSITORY,
        "actor.id": MAINTAINER_ID, "triggering_actor.id": MAINTAINER_ID,
    }
    check_fields(github_json(f"/actions/workflows/{workflow}"), {
        "id": workflow, "path": '.github/workflows/qa-strasbourg-admission-first-contact.yml', "state": "disabled_manually",
    }, "Exact retired first-contact owner differs")
    check_fields(github_json(f"/actions/runs/{run_id}/attempts/1"), expected,
                 "Exact retired first-contact run differs")
    inventory = github_json(f"/actions/workflows/{workflow}/runs?per_page=2")
    require(inventory["total_count"] == 1 and len(inventory["workflow_runs"]) == 1,
            "Exact first-contact inventory differs")
    check_fields(inventory["workflow_runs"][0], expected, "Exact first-contact inventory differs")
    jobs = github_json(f"/actions/runs/{run_id}/attempts/1/jobs?per_page=10")
    require(jobs["total_count"] == 1 and len(jobs["jobs"]) == 1, "Original job inventory differs")
    check_fields(jobs["jobs"][0], {
        "id": 134598212592, "run_id": run_id, "head_sha": '67fcdce0f697cb293dc9472089848f4c0dfdd77b',
        "name": "First contact strasbourg424", "status": "completed", "conclusion": "success",
    }, "Exact predecessor job differs")
    rows = github_json(f"/actions/runs/{run_id}/artifacts?per_page=2")
    require(rows["total_count"] == 1 and len(rows["artifacts"]) == 1, "Original artifact inventory differs")
    check_fields(rows["artifacts"][0], {
        "id": 14401170733, "name": "first-contact-strasbourg424-44243944283-1",
        "size_in_bytes": 170694, "expired": False, "digest": "sha256:a98eea210b0f49138be042d733da7ab4e8684ebe081f0235d409143b071f2fd1",
        "workflow_run.id": run_id, "workflow_run.head_sha": '67fcdce0f697cb293dc9472089848f4c0dfdd77b',
    }, "Exact original ciphertext artifact differs")


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
    check_fields(event, {
        "created": True, "deleted": False, "ref": REF, "before": "0" * 40,
        "after": sha, "repository.full_name": REPOSITORY, "sender.id": MAINTAINER_ID,
    }, "Not an exact first branch creation")
    run_id = int(run_text)
    run = poll_active(f"/actions/runs/{run_id}", {
        "id": run_id, "event": "push", "run_attempt": 1, "head_branch": BRANCH,
        "head_sha": sha, "path": WORKFLOW, "head_repository.full_name": REPOSITORY,
        "repository.full_name": REPOSITORY, "actor.id": MAINTAINER_ID,
        "triggering_actor.id": MAINTAINER_ID,
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
    verify_grant(json.loads((ROOT / "scope-OFF.json").read_bytes()), source)
    verify_predecessor()
    return {
        "repository": REPOSITORY, "ref": REF, "workflow": WORKFLOW, "head_sha": sha,
        "run_id": run_id, "run_attempt": 1, "workflow_id": run["workflow_id"],
        "job_id": job["id"], "source": source,
    }
