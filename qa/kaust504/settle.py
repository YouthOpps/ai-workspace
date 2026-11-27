"""Advance only the exact, fully received historical redirect without publisher access."""

import hashlib
import json
import os
from pathlib import Path
import subprocess
import urllib.request


ROOT = Path(__file__).resolve().parent
REPOSITORY = "YouthOpps/ai-workspace"
BRANCH = "qa/504-kaust-response-settlement"
WORKFLOW = ".github/workflows/qa-kaust-response-settlement.yml"
REVIEWER_SHA256 = '52142fa8914e54217cf7b7dcf776b1a9fcafa04080298e1649bf6c8fc42d5969'
REVIEW_SHA256 = 'b73298ada680010ce7f7c9dd2a6f086ae9e87d25186f7453730ac15797328ee4'
ARCHIVE_SHA256 = '2a5891a13f7d9e1028171990d0a53b679fa0073b21f1f7826d302f6da6c23327'
STATE_SHA256 = 'cf1eef37e0edb328ee5195ee5f95f979f3072ce37cc04cb5d563f600ab7dc31b'
OLD_HEAD = '62f90276e1c584fed85daf351600d524569d2d13'
OLD_WORKFLOW = '.github/workflows/qa-kaust-inventory-discovery-504.yml'
LOCATION = 'https://admissions.kaust.edu.sa/internship/search'
OWNER = {'created_at': '2026-11-27T07:42:49Z', 'head_sha': '62f90276e1c584fed85daf351600d524569d2d13', 'job_id': 140376451985, 'ref': 'refs/heads/qa/kaust-inventory-discovery-504', 'repository': 'YouthOpps/ai-workspace', 'run_attempt': 1, 'run_id': 45960351478, 'scope_sha256': 'abe09f9fe7ec9a1ecf3225859144b06a59ce1d558b2ef885bcd7012e8a0e5e73', 'source': 'kaust504', 'workflow': '.github/workflows/qa-kaust-inventory-discovery-504.yml', 'workflow_id': 432476070}
ARTIFACT_ID = 15181200453


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def settlement(original, proof):
    """Update the original receipt and retain its restrictions and historical reservations."""
    require(digest(canonical(original)) == STATE_SHA256, "Original state differs")
    robots, overview = proof['responses']
    require(proof['inventory'] == LOCATION and proof['complete'] and proof['closed']
            and proof['stop'] == 'Unassessed encoding; raw body retained'
            and proof['decoded_hash'] == '4b2cd085e7e4fd61d97b171c398e4197a990ce8061b5b3394b80239432527d0d',
            'Unexpected reviewed body or stop')
    require(robots['status'] == 404 and overview['status'] == 200
            and original['physical_pending'] and original['in_flight'] and not original['blocked']
            and robots['request_id'] == original['completed_physical_id']
            and overview['request_id'] == original['physical_id']
            and overview['url'] == original['target']
            and robots['wall_completion'] + original['interval'] <= overview['wall_start'],
            'Responses differ from retained journal')
    closed = overview['wall_completion']
    require(closed >= original['observed_at'] and closed >= overview['wall_start'], 'Clock mismatch')
    return dict(original, completed=closed, observed_at=closed,
                starts=sorted(set(original['starts'] + [robots['wall_start'],overview['wall_start']])),
                not_before=max(original['not_before'],closed + original['interval']),
                completed_physical_id=original['physical_id'],completed_logical_id=original['logical_id'],
                inventory_completed=max(original['inventory_completed'],closed),
                in_flight=False,physical_pending=False,outcome='response_assessed')


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, message, headers, url):
        return None


def github(path):
    request = urllib.request.Request("https://api.github.com/repos/" + REPOSITORY + path, headers={
        "Authorization": "Bearer " + os.environ["GITHUB_TOKEN"],
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    })
    with urllib.request.build_opener(NoRedirect()).open(request, timeout=20) as response:
        raw = response.read(2_000_001)
    require(len(raw) <= 2_000_000, "Excessive GitHub response")
    return json.loads(raw)


def verify_predecessor():
    run = github(f"/actions/runs/{OWNER['run_id']}")
    workflow = github(f"/actions/workflows/{OWNER['workflow_id']}")
    require(workflow["state"] == "disabled_manually" and workflow["path"] == OLD_WORKFLOW
            and run["head_sha"] == OLD_HEAD and run["status"] == "completed"
            and run["conclusion"] == "failure" and run["path"] == OLD_WORKFLOW
            and run["run_attempt"] == 1 and run["workflow_id"] == OWNER["workflow_id"]
            and run["created_at"] == OWNER["created_at"]
            and "refs/heads/" + run["head_branch"] == OWNER["ref"],
            "Original run or its explicit retirement differs")
    history = github(f"/actions/workflows/{OWNER['workflow_id']}/runs?per_page=2")
    require(history["total_count"] == 1 and len(history["workflow_runs"]) == 1
            and history["workflow_runs"][0]["id"] == OWNER["run_id"],
            "Unexpected predecessor run history")
    jobs = github(f"/actions/runs/{OWNER['run_id']}/attempts/1/jobs")["jobs"]
    require(len(jobs) == 1 and jobs[0]["id"] == OWNER["job_id"]
            and jobs[0]["run_id"] == OWNER["run_id"] and jobs[0]["head_sha"] == OLD_HEAD
            and jobs[0]["conclusion"] == "failure" and jobs[0]["name"] == "First contact kaust504",
            "Original job identity differs")
    artifacts = github(f"/actions/runs/{OWNER['run_id']}/artifacts?per_page=2")
    require(artifacts["total_count"] == 1 and len(artifacts["artifacts"]) == 1,
            "Original archive inventory differs")
    artifact = artifacts["artifacts"][0]
    require(artifact["id"] == ARTIFACT_ID
            and artifact["name"] == "first-contact-kaust504-45960351478-1"
            and artifact["size_in_bytes"] == 127748
            and artifact["workflow_run"]["id"] == OWNER["run_id"]
            and artifact["workflow_run"]["head_sha"] == OLD_HEAD
            and artifact["digest"] == "sha256:" + ARCHIVE_SHA256 and not artifact["expired"],
            "Original archive ownership differs")


def main():
    env = os.environ
    event = json.loads(Path(env["GITHUB_EVENT_PATH"]).read_bytes())
    ref = "refs/heads/" + BRANCH
    head = env["GITHUB_SHA"]
    require(env["GITHUB_REPOSITORY"] == REPOSITORY and env["GITHUB_RUN_ATTEMPT"] == "1"
            and env["GITHUB_REF"] == ref and env["GITHUB_EVENT_NAME"] == "push"
            and env["GITHUB_WORKFLOW_REF"] == REPOSITORY + "/" + WORKFLOW + "@" + ref
            and env["GITHUB_WORKFLOW_SHA"] == head and "DATA_SOURCE_TOKEN" not in env
            and event["created"] is True and event["deleted"] is False and event["before"] == "0" * 40
            and event["after"] == head, "Wrong one-use settlement scope")
    require(subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip() == head,
            "Checkout head differs")
    run_id = int(env["GITHUB_RUN_ID"])
    active = github(f"/actions/runs/{run_id}")
    require(active["id"] == run_id and active["head_sha"] == head
            and active["run_attempt"] == 1 and active["head_branch"] == BRANCH
            and active["event"] == "push" and active["path"] == WORKFLOW,
            "Settlement run owner differs")
    history = github(f"/actions/workflows/{active['workflow_id']}/runs?per_page=2")
    require(history["total_count"] == 1 and len(history["workflow_runs"]) == 1
            and history["workflow_runs"][0]["id"] == run_id,
            "An existing attempt consumed the one-use settlement")
    reviewed = ROOT / "reviewed-settlement.json"
    reviewer = ROOT / "reviewer.pem"
    signature = ROOT / "reviewer-signature.cms"
    require(digest(reviewer.read_bytes()) == REVIEWER_SHA256
            and digest(reviewed.read_bytes()) == REVIEW_SHA256, "Frozen review inputs differ")
    require(signature.is_file(), "Independent detached signature is required")
    verified = subprocess.check_output([
        "openssl", "cms", "-verify", "-binary", "-inform", "DER", "-nointern", "-noverify",
        "-certfile", str(reviewer), "-content", str(reviewed), "-in", str(signature),
    ], timeout=20)
    require(verified == reviewed.read_bytes(), "Reviewer signature output differs")
    bundle = json.loads(verified)
    verify_predecessor()
    derived = settlement(bundle["original_state"], bundle["proof"])
    require(derived == bundle["proposed_state"], "Derived continuation differs from reviewed bytes")
    successor_bytes = canonical(derived)
    out = Path(env["RUNNER_TEMP"]) / "kaust504-response-settlement"
    out.mkdir(mode=0o700)
    provenance = {
        "repository": REPOSITORY, "run_id": run_id, "head_sha": head,
        "previous_owner": OWNER, "previous_archive_id": ARTIFACT_ID,
        "previous_archive_sha256": ARCHIVE_SHA256, "previous_pending_state_sha256": STATE_SHA256,
        "review_sha256": digest(verified), "state_sha256": digest(successor_bytes),
        "discovered_inventory": LOCATION, "publisher_requests": 0,
    }
    (out / "state.json").write_bytes(successor_bytes)
    (out / "provenance.json").write_bytes(canonical(provenance))
    print(json.dumps(provenance, indent=2))


if __name__ == "__main__":
    main()
