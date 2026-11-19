"""Advance only the exact, fully received historical redirect without publisher access."""

import hashlib
import json
import os
from pathlib import Path
import subprocess
import urllib.request


ROOT = Path(__file__).resolve().parent
REPOSITORY = "YouthOpps/ai-workspace"
BRANCH = "qa/468-loreal-received-sitemap-redirect-settlement"
WORKFLOW = ".github/workflows/qa-loreal-received-sitemap-redirect-settlement.yml"
REVIEWER_SHA256 = "c8bfa742ffcd2638a1926c8068b58c3f0cc9bcda7077b95ab3ac8a8ac5b01531"
REVIEW_SHA256 = '2ac91148d4bc51f46c3e6aa4a5ff04df292e5d2d221d62adde54df60cdeb0f1f'
ARCHIVE_SHA256 = "1f65dc017eea50a175036499279732777f271d479a47cbb817779b679b43c292"
STATE_SHA256 = 'bde79f153d901c211456f56b4343b3b90d83a06d93d0f4116cdbd61d51b74267'
OLD_HEAD = '2544b743a07994e9c5fb67fcc8c715d72645e441'
OLD_WORKFLOW = '.github/workflows/qa-loreal-careers-sitemap-research.yml'
ORIGIN = "https://careers.loreal.com"
OLD_ENTRY = ORIGIN + "/sitemap.xml"
LOCATION = ORIGIN + "/en/sitemap.xml"
DECISION = 'https://github.com/YouthOpps/data-pipeline/issues/468#issuecomment-7007435587'
OWNER = {
    "created_at": "2026-11-19T11:12:10Z",
    "head_sha": "2544b743a07994e9c5fb67fcc8c715d72645e441",
    "job_id": 135520585401,
    "ref": "refs/heads/qa/loreal-careers-sitemap-research",
    "repository": "YouthOpps/ai-workspace",
    "run_attempt": 1,
    "run_id": 44512663014,
    "scope_sha256": "0dca10f99481441e5d6dedc34af6430600fc39776976d0b6f4bc1d9f1772563f",
    "source": "loreal468sitemap",
    "workflow": ".github/workflows/qa-loreal-careers-sitemap-research.yml",
    "workflow_id": 423733916
}
ARTIFACT_ID = 14524247971


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
    robots, redirect = proof["responses"]
    require(proof["scope"] == OWNER and proof["archive_sha256"] == ARCHIVE_SHA256
            and proof["artifact_id"] == ARTIFACT_ID and proof["location"] == LOCATION
            and proof["decision"] == DECISION,
            "Exact historical redirect proof differs")
    require(original["family"] == "youthopps-loreal-careers-publisher-v1"
            and original["in_flight"] is True and original["physical_pending"] is True
            and original["blocked"] is False and original["outcome"] == "reserved",
            "Expected only the original reserved redirect")
    require(robots["status"] == 200 and robots["url"] == ORIGIN + "/robots.txt"
            and robots["request_id"] == original["completed_physical_id"]
            and original["policy"]["body_sha256"] == robots["body_sha256"]
            and original["policy"]["new_allowed"] and original["policy"]["legacy_allowed"],
            "Original policy receipt differs")
    require(redirect["status"] == 301 and redirect["url"] == OLD_ENTRY
            and redirect["request_id"] == original["physical_id"]
            and original["target"] == OLD_ENTRY and type(redirect["body_length"]) is int
            and redirect["body_length"] == 0
            and type(redirect["content_length"]) is int and redirect["content_length"] == 0
            and redirect["transfer_encoding_present"] is False
            and redirect["retry_after"] is False
            and redirect["stop"] == "Redirect captured, never followed",
            "Exact redirect disposition differs")
    require(all(row["complete_eof"] is True and row["transport_closed"] is True
                for row in (robots, redirect)), "Both original responses must have closed after EOF")
    starts = [robots["wall_start"], redirect["wall_start"]]
    require(original["physical_started"] == original["starts"][-1]
            and starts[0] in original["starts"] and starts[0] <= robots["wall_completion"]
            and robots["wall_completion"] + original["interval"] <= starts[1]
            and original["physical_started"] <= starts[1] <= redirect["wall_completion"],
            "Original request order or preserved spacing differs")
    closed = redirect["wall_completion"]
    require(closed >= max(original["observed_at"], original["completed"]),
            "Closure precedes retained timing")
    # A closed redirect is a physical completion. It did not complete the inventory.
    return dict(original, completed=closed, observed_at=closed,
                starts=sorted(set(original["starts"] + starts)),
                not_before=max(original["not_before"], closed + original["interval"]),
                completed_logical_id=original["logical_id"],
                completed_physical_id=original["physical_id"],
                in_flight=False, physical_pending=False, outcome="response_assessed")


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
    for workflow_id, path in (
            (423613642, ".github/workflows/qa-loreal-careers-terms-first-contact.yml"),
            (423723705, ".github/workflows/qa-loreal-careers-detail-research.yml")):
        prior = github(f"/actions/workflows/{workflow_id}")
        require(prior["id"] == workflow_id and prior["state"] == "disabled_manually"
                and prior["path"] == path, "An earlier publisher owner remains active")
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
            and jobs[0]["conclusion"] == "failure" and jobs[0]["name"] == "First contact loreal468sitemap",
            "Original job identity differs")
    artifacts = github(f"/actions/runs/{OWNER['run_id']}/artifacts?per_page=2")
    require(artifacts["total_count"] == 1 and len(artifacts["artifacts"]) == 1,
            "Original archive inventory differs")
    artifact = artifacts["artifacts"][0]
    require(artifact["id"] == ARTIFACT_ID
            and artifact["name"] == "sitemap-research-loreal468sitemap-44512663014-1"
            and artifact["size_in_bytes"] == 56625
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
    out = Path(env["RUNNER_TEMP"]) / "loreal468-sitemap-redirect-settlement"
    out.mkdir(mode=0o700)
    provenance = {
        "repository": REPOSITORY, "run_id": run_id, "head_sha": head,
        "previous_owner": OWNER, "previous_archive_id": ARTIFACT_ID,
        "previous_archive_sha256": ARCHIVE_SHA256, "previous_pending_state_sha256": STATE_SHA256,
        "review_sha256": digest(verified), "state_sha256": digest(successor_bytes),
        "redirect_location": LOCATION, "redirect_followed": False, "publisher_requests": 0,
    }
    (out / "state.json").write_bytes(successor_bytes)
    (out / "provenance.json").write_bytes(canonical(provenance))
    print(json.dumps(provenance, indent=2))


if __name__ == "__main__":
    main()
