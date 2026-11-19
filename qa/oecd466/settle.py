"""Settle only the exact, already closed OECD REP receipt without publisher access."""

import hashlib
import json
import os
from pathlib import Path
import subprocess
import urllib.request


ROOT = Path(__file__).resolve().parent
REPOSITORY = "YouthOpps/ai-workspace"
BRANCH = "qa/466-oecd-received-rep-settlement"
WORKFLOW = ".github/workflows/qa-oecd-received-rep-settlement.yml"
REVIEWER_SHA256 = "c8bfa742ffcd2638a1926c8068b58c3f0cc9bcda7077b95ab3ac8a8ac5b01531"
REVIEW_SHA256 = "a437f9282bb7403938267bdb4da43191ed885850bff67d470051b3635dc530a8"
ARCHIVE_SHA256 = "4bca638b64fe19f4f09cc7b04224e98c9d3d650b6f5df7d0ee0f1ad15e9ab1bd"
STATE_SHA256 = "d38d70344bd2cfc585f414d4189ef908cb41ab8e068a76d7525319f68ea22dcc"
OLD_HEAD = "19b66041abb14dc185a3d057e51f75067d1dfa34"
OLD_WORKFLOW = ".github/workflows/qa-oecd-internship-first-contact.yml"
ORIGIN = "https://www.oecd.org"
ROBOTS = ORIGIN + "/robots.txt"
ENTRY = ORIGIN + "/en/about/careers/internships.html"
POLICY_SHA256 = "7cd830be68ea9e7cc99de8013fbb71855a72fc9b301c90273ac11f8c40cd83a8"
WILDCARD_DENIES = ["/content/dam/oecd/", "/adobe/dynamicmedia/deliver/"]
SCOPE_SHA256 = "d713127196c219fb86f3428654796c7f00b4ec54f08fa64070021d0f6ba183e0"
OWNER = {
    "decision": "https://github.com/YouthOpps/data-pipeline/issues/466#issuecomment-7004745562",
    "repository": REPOSITORY,
    "run_id": 44493996966,
    "workflow_id": 423618840,
    "workflow": OLD_WORKFLOW,
    "head_sha": OLD_HEAD,
    "ref": "refs/heads/qa/oecd-internship-first-contact",
    "source": "oecd466",
    "scope_sha256": SCOPE_SHA256,
    "run_attempt": 1,
    "job_id": 135456424153,
}
ARTIFACT_ID = 14513987716


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def settlement(original, proof):
    """Persist one adjudicated physical completion and retain all inherited limits."""
    require(digest(canonical(original)) == STATE_SHA256, "Original state differs")
    require(proof["scope"] == OWNER and proof["archive_sha256"] == ARCHIVE_SHA256
            and proof["artifact_id"] == ARTIFACT_ID and proof["original_body_sha256"] == POLICY_SHA256
            and proof["body_length"] == 237 and proof["wildcard_denies"] == WILDCARD_DENIES
            and proof["assessment_targets"] == [ENTRY, *(ORIGIN + path for path in WILDCARD_DENIES)]
            and proof["strict_original_matcher_results"] == [[True, True], [False, False], [False, False]]
            and proof["omitted_only"] == "Spacecat/1.0 allow-only group",
            "Exact original scoped matcher evidence differs")
    require(original["family"] == "youthopps-oecd-internship-publisher-v1"
            and original["in_flight"] is True and original["physical_pending"] is True
            and original["blocked"] is False and original["policy"] is None
            and original["outcome"] == "reserved" and original["target"] == ROBOTS,
            "Original reserved REP receipt differs")
    receipt = proof["response"]
    require(receipt["url"] == ROBOTS and receipt["status"] == 200
            and receipt["request_id"] == original["physical_id"]
            and receipt["complete_eof"] is True and receipt["transport_closed"] is True
            and receipt["retry_after"] is False and receipt["chunked"] is True
            and receipt["stop"] == "Unassessed invalid REP product token",
            "Exact completed receipt differs")
    start, end = receipt["wall_start"], receipt["wall_completion"]
    require(original["physical_started"] == original["starts"][-1]
            and original["observed_at"] <= start <= end,
            "Original request ordering differs")
    # The policy digest always identifies the unmodified publisher bytes.
    policy = {"url": ROBOTS, "status": 200, "body_sha256": POLICY_SHA256,
              "unavailable": False, "new_allowed": True, "legacy_allowed": True}
    return dict(original, completed=end, observed_at=end, policy=policy,
                starts=sorted(set(original["starts"] + [start])),
                not_before=max(original["not_before"], end + original["interval"]),
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
    run = github("/actions/runs/44493996966")
    workflow = github("/actions/workflows/423618840")
    require(workflow["state"] == "disabled_manually" and workflow["path"] == OLD_WORKFLOW
            and run["head_sha"] == OLD_HEAD and run["status"] == "completed"
            and run["conclusion"] == "failure" and run["path"] == OLD_WORKFLOW
            and run["run_attempt"] == 1 and run["workflow_id"] == OWNER["workflow_id"]
            and "refs/heads/" + run["head_branch"] == OWNER["ref"],
            "Original run or its explicit retirement differs")
    history = github("/actions/workflows/423618840/runs?per_page=2")
    require(history["total_count"] == 1 and len(history["workflow_runs"]) == 1
            and history["workflow_runs"][0]["id"] == OWNER["run_id"],
            "Unexpected predecessor run history")
    jobs = github("/actions/runs/44493996966/attempts/1/jobs")["jobs"]
    require(len(jobs) == 1 and jobs[0]["id"] == OWNER["job_id"]
            and jobs[0]["run_id"] == OWNER["run_id"] and jobs[0]["head_sha"] == OLD_HEAD
            and jobs[0]["conclusion"] == "failure" and jobs[0]["name"] == "First contact oecd466",
            "Original job identity differs")
    artifact = github("/actions/artifacts/14513987716")
    require(artifact["workflow_run"]["id"] == OWNER["run_id"]
            and artifact["workflow_run"]["head_sha"] == OLD_HEAD
            and artifact["digest"] == "sha256:" + ARCHIVE_SHA256 and not artifact["expired"]
            and artifact["name"] == "first-contact-oecd466-44493996966-1"
            and artifact["size_in_bytes"] == 11674,
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
    out = Path(env["RUNNER_TEMP"]) / "oecd466-rep-settlement"
    out.mkdir(mode=0o700)
    provenance = {
        "repository": REPOSITORY, "run_id": run_id, "head_sha": head,
        "previous_owner": OWNER, "previous_archive_id": ARTIFACT_ID,
        "previous_archive_sha256": ARCHIVE_SHA256, "previous_pending_state_sha256": STATE_SHA256,
        "review_sha256": digest(verified), "state_sha256": digest(successor_bytes),
        "assessed_target": ENTRY, "original_policy_sha256": POLICY_SHA256,
        "retained_wildcard_denies": WILDCARD_DENIES, "publisher_requests": 0,
    }
    (out / "state.json").write_bytes(successor_bytes)
    (out / "provenance.json").write_bytes(canonical(provenance))
    print(json.dumps(provenance, indent=2))


if __name__ == "__main__":
    main()
