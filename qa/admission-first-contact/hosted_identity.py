"""Identity checks for this temporary, nonpublishing GitHub Actions workflow."""

import json
import os
import re
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPOSITORY = "YouthOpps/ai-workspace"
WORKFLOW = ".github/workflows/qa-admissions-first-contacts.yml"
BRANCH = "qa/admission-first-contacts-422-423-425-r2"
REF = "refs/heads/" + BRANCH
SOURCES = frozenset(("graz422", "anu423", "coimbra425"))
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


def verify_predecessor(proof):
    """Require the actual sole old run and all three original prewire failures."""
    old = proof["predecessor"]
    run_id = old["id"]
    check_fields(github_json(f"/actions/runs/{run_id}"), old, "Predecessor run changed")
    old_branch = urllib.parse.quote(old["head_branch"], safe="")
    branch_runs = github_json(f"/actions/runs?branch={old_branch}&event=push&per_page=2")
    require(branch_runs["total_count"] == 1
            and [row["id"] for row in branch_runs["workflow_runs"]] == [run_id],
            "Predecessor is no longer the sole old branch push run")
    jobs = github_json(f"/actions/runs/{run_id}/attempts/1/jobs?per_page=10")
    expected_ids = {row["id"] for row in proof["jobs"]}
    require(jobs["total_count"] == len(expected_ids) == 3
            and {row["id"] for row in jobs["jobs"]} == expected_ids,
            "Predecessor job inventory differs")
    by_id = {row["id"]: row for row in jobs["jobs"]}
    for expected in proof["jobs"]:
        check_fields(by_id[expected["id"]], expected, "Predecessor job changed")
    artifacts = github_json(f"/actions/runs/{run_id}/artifacts?per_page=10")
    require(artifacts["total_count"] == 0 and artifacts["artifacts"] == [],
            "Predecessor has an unexpected artifact")


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
    }
    check_fields(dict(env), required, "Wrong hosted scope")
    require("DATA_SOURCE_TOKEN" not in env and "GITHUB_TOKEN" in env, "Wrong credential scope")
    event = json.loads(Path(env["GITHUB_EVENT_PATH"]).read_bytes())
    sha, run_text = env["GITHUB_SHA"], env["GITHUB_RUN_ID"]
    require(re.fullmatch(r"[0-9a-f]{40}", sha) and re.fullmatch(r"[1-9][0-9]*", run_text),
            "Invalid hosted identity")
    check_fields(event, {
        "created": True, "deleted": False, "ref": REF, "before": "0" * 40,
        "after": sha, "repository.full_name": REPOSITORY,
    }, "Not an exact first branch creation")
    run_id = int(run_text)
    run = poll_active(f"/actions/runs/{run_id}", {
        "id": run_id, "event": "push", "run_attempt": 1, "head_branch": BRANCH,
        "head_sha": sha, "path": WORKFLOW, "head_repository.full_name": REPOSITORY,
        "repository.full_name": REPOSITORY,
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
    return {
        "repository": REPOSITORY, "ref": REF, "workflow": WORKFLOW, "head_sha": sha,
        "run_id": run_id, "run_attempt": 1, "workflow_id": run["workflow_id"],
        "job_id": job["id"], "source": source,
    }
