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
WORKFLOW = ".github/workflows/qa-unina418-confirmed-302.yml"
BRANCH = "qa/418-unina-confirmed-302"
REF = "refs/heads/" + BRANCH
SOURCES = frozenset(("unina418state302",))
PIPELINE_SHA = "e8c156de2df09c6eddd1b010ebd30cc17417d37e"
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
        r"https://github\.com/YouthOpps/data-pipeline/issues/418#issuecomment-([1-9][0-9]*)",
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
        and result.get("issue_url") == "https://api.github.com/repos/YouthOpps/data-pipeline/issues/418"
        and result.get("user", {}).get("id") == MAINTAINER_ID
        and result.get("created_at") == result.get("updated_at")
        and type(result.get("created_at")) is str
        and f"Approved Unina #418 confirmed-302 continuation {digest}" in result.get("body", "").splitlines(),
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
    """Verify the original maintainer decision while the exact carry stays immutable."""
    row = public_pipeline_json('/issues/comments/6959114040')
    require(row.get('html_url') == 'https://github.com/YouthOpps/data-pipeline/issues/418#issuecomment-6959114040'
            and row.get('user', {}).get('id') == MAINTAINER_ID
            and row.get('created_at') == row.get('updated_at')
            and hashlib.sha256(row['body'].encode()).hexdigest() == '7da25d929838823c1bae16bc1fa74569bfe0abc61da98b84991f092eec34acaa',
            'Original university Phase A decision differs')


def verify_received_redirect_owner():
    """Require the exact retired failed scope and its consumed owned archive."""
    workflow, run_id = 422250211, 44249795804
    previous_path = '.github/workflows/qa-unina418-policy-continuation.yml'
    expected = {
        'id': run_id, 'workflow_id': workflow, 'run_attempt': 1, 'event': 'push',
        'head_sha': '1dea7bf6df8dd23022ba817cf50920c96ce16f09', 'head_branch': 'qa/418-unina-four-mark-policy', 'path': previous_path,
        'status': 'completed', 'conclusion': 'failure', 'actor.id': MAINTAINER_ID,
        'triggering_actor.id': MAINTAINER_ID, 'head_repository.full_name': REPOSITORY,
        'repository.full_name': REPOSITORY,
    }
    row = public_pipeline_json('/issues/comments/6970741002')
    require(row.get('html_url') == 'https://github.com/YouthOpps/data-pipeline/issues/418#issuecomment-6970741002'
            and row.get('user', {}).get('id') == MAINTAINER_ID
            and row.get('created_at') == row.get('updated_at')
            and hashlib.sha256(row['body'].encode()).hexdigest() == '33b99d9f3b8a8cd75729b0546f0e6872384741e2379494d5518b15a2637b465a',
            'Exact predecessor Phase B decision differs')
    check_fields(github_json(f'/actions/workflows/{workflow}'), {
        'id': workflow, 'path': previous_path, 'state': 'disabled_manually',
    }, 'Exact Phase B workflow is not retired')
    check_fields(github_json(f'/actions/runs/{run_id}/attempts/1'), expected,
                 'Exact captured 302 run differs')
    runs = github_json(f'/actions/workflows/{workflow}/runs?per_page=2')
    require(runs['total_count'] == 1 and len(runs['workflow_runs']) == 1, 'Phase B run history differs')
    check_fields(runs['workflow_runs'][0], expected, 'Exact captured run history differs')
    jobs = github_json(f'/actions/runs/{run_id}/attempts/1/jobs?per_page=2')
    require(jobs['total_count'] == 1 and len(jobs['jobs']) == 1, 'Phase B job inventory differs')
    check_fields(jobs['jobs'][0], {
        'id': 134617387470, 'name': 'First contact unina418phaseb', 'run_id': run_id,
        'run_attempt': 1, 'head_sha': '1dea7bf6df8dd23022ba817cf50920c96ce16f09', 'status': 'completed', 'conclusion': 'failure',
    }, 'Exact captured 302 job differs')
    rows = github_json(f'/actions/runs/{run_id}/artifacts?per_page=2')
    require(rows['total_count'] == 1 and len(rows['artifacts']) == 1, 'Phase B artifact inventory differs')
    check_fields(rows['artifacts'][0], {
        'id': 14403008259, 'name': 'linked-policy-unina418phaseb-44249795804-1',
        'digest': 'sha256:c5c03ceccca3c64f47f9f4801c3abfc842612f909576b4ecc593f91f4c5f339e', 'size_in_bytes': 21563, 'expired': False,
        'workflow_run.id': run_id, 'workflow_run.head_sha': '1dea7bf6df8dd23022ba817cf50920c96ce16f09',
    }, 'Exact original received-302 ZIP custody differs')


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
    verify_received_redirect_owner()
    return {
        "repository": REPOSITORY, "ref": REF, "workflow": WORKFLOW, "head_sha": sha,
        "run_id": run_id, "run_attempt": 1, "workflow_id": run["workflow_id"],
        "job_id": job["id"], "source": source,
    }
