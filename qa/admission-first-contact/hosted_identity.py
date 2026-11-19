"""Identity checks for this temporary, nonpublishing GitHub Actions workflow."""

import hashlib
import json
import os
import re
import subprocess
import time
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPOSITORY = "YouthOpps/ai-workspace"
WORKFLOW = ".github/workflows/qa-france-higher-ed-dap-first-contact.yml"
BRANCH = "qa/france-higher-ed-dap-first-contact"
REF = "refs/heads/" + BRANCH
SOURCES = frozenset(("dapes462",))
PIPELINE_SHA = "1dcca6beb3023cf918f50cb87f68f3522b9978b2"
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


def utc_timestamp(value):
    require(type(value) is str and re.fullmatch(
        r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z", value),
        "Invalid GitHub timestamp")
    return datetime.fromisoformat(value)


def verify_checkout(sha):
    workspace = ROOT.parent.parent
    actual = subprocess.check_output(["git", "-C", str(workspace), "rev-parse", "HEAD"],
                                     text=True, timeout=10).strip()
    require(actual == sha, "Hosted checkout differs from the approved commit")
    owned = [WORKFLOW, "qa/admission-first-contact"]
    changes = subprocess.check_output(
        ["git", "-C", str(workspace), "status", "--porcelain", "--untracked-files=all", "--", *owned],
        timeout=10)
    require(not changes, "Hosted workflow or capture inputs have changed")


def verify_grant(manifest, source, sha, run_created):
    """Find the single unchanged scope and revision grant made before this run."""
    require(manifest["enabled"] is True and set(manifest["sources"]) == SOURCES
            and manifest["sources"][source]["decision"] is None, "First contact is OFF or unreviewed")
    manifest["enabled"] = False
    canonical = json.dumps(manifest, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    digest = hashlib.sha256(canonical).hexdigest()
    scope_line = f"Approved France DAP first-contact scope {digest}"
    head_line = f"Approved France DAP research head {sha}"
    pre_run = utc_timestamp(run_created)
    issue_api = "https://api.github.com/repos/YouthOpps/data-pipeline/issues/462"
    comments = []
    for page in range(1, 6):
        rows = public_pipeline_json(f"/issues/462/comments?per_page=100&page={page}")
        require(type(rows) is list, "Invalid approval inventory")
        for row in rows:
            lines = (row.get("body") or "").splitlines()
            if scope_line not in lines or head_line not in lines:
                continue
            identifier = row.get("id")
            url = f"https://github.com/YouthOpps/data-pipeline/issues/462#issuecomment-{identifier}"
            created = row.get("created_at")
            if (type(identifier) is int and identifier > 0
                    and row.get("html_url") == url and row.get("issue_url") == issue_api
                    and row.get("user", {}).get("id") == MAINTAINER_ID
                    and row.get("user", {}).get("type") == "User"
                    and created == row.get("updated_at") and utc_timestamp(created) < pre_run
                    and lines.count(scope_line) == lines.count(head_line) == 1):
                comments.append(url)
        if len(rows) < 100:
            break
    else:
        raise RuntimeError("Incomplete approval inventory")
    require(len(comments) == 1, "Exactly one prior maintainer head and scope grant is required")
    return comments[0]


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
    verify_checkout(sha)
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
    decision = verify_grant(json.loads((ROOT / "scope-OFF.json").read_bytes()),
                            source, sha, run.get("created_at"))
    return {
        "repository": REPOSITORY, "ref": REF, "workflow": WORKFLOW, "head_sha": sha,
        "run_id": run_id, "run_attempt": 1, "workflow_id": run["workflow_id"],
        "job_id": job["id"], "source": source, "decision": decision,
    }
