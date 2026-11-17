"""Identity checks for this temporary, nonpublishing GitHub Actions workflow."""

import json
import os
import re
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPOSITORY = "YouthOpps/ai-workspace"
WORKFLOW = ".github/workflows/qa-admissions-first-contacts.yml"
BRANCH = "qa/admission-first-contacts-422-423-425"
REF = "refs/heads/" + BRANCH
SOURCES = frozenset(("graz422", "anu423", "coimbra425"))


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
    require(all(env.get(k) == v for k, v in required.items()), "Wrong hosted scope")
    require("DATA_SOURCE_TOKEN" not in env and "GITHUB_TOKEN" in env, "Wrong credential scope")
    event = json.loads(Path(env["GITHUB_EVENT_PATH"]).read_bytes())
    sha, run_text = env["GITHUB_SHA"], env["GITHUB_RUN_ID"]
    require(re.fullmatch(r"[0-9a-f]{40}", sha) and re.fullmatch(r"[1-9][0-9]*", run_text),
            "Invalid hosted identity")
    require(event.get("created") is True and event.get("deleted") is False
            and event.get("ref") == REF and event.get("before") == "0" * 40
            and event.get("after") == sha and event["repository"]["full_name"] == REPOSITORY,
            "Not an exact first branch creation")
    run_id = int(run_text)
    run = github_json(f"/actions/runs/{run_id}")
    require(run["id"] == run_id and run["event"] == "push" and run["run_attempt"] == 1
            and run["status"] == "in_progress" and run["head_branch"] == BRANCH
            and run["head_sha"] == sha and run["path"] == WORKFLOW
            and run["head_repository"]["full_name"] == REPOSITORY
            and run["repository"]["full_name"] == REPOSITORY, "Run API identity mismatch")
    branch = urllib.parse.quote(BRANCH, safe="")
    history = github_json(f"/actions/runs?branch={branch}&event=push&per_page=2")
    require(history["total_count"] == 1 and [x["id"] for x in history["workflow_runs"]] == [run_id],
            "Branch already has a run or history is ambiguous")
    jobs = github_json(f"/actions/runs/{run_id}/attempts/1/jobs?per_page=10")
    active = [job for job in jobs["jobs"] if job["name"] == f"First contact {source}"]
    require(len(active) == 1 and active[0]["status"] == "in_progress"
            and active[0]["run_id"] == run_id and active[0]["head_sha"] == sha,
            "Current job is not the scoped active source job")
    return {
        "repository": REPOSITORY, "ref": REF, "workflow": WORKFLOW, "head_sha": sha,
        "run_id": run_id, "run_attempt": 1, "workflow_id": run["workflow_id"],
        "job_id": active[0]["id"], "source": source,
    }
