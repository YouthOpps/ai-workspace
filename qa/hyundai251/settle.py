"""Attest the historical, complete Hyundai robots response without publisher access."""

import hashlib
import json
import os
from pathlib import Path
import subprocess
import urllib.request


ROOT = Path(__file__).resolve().parent
REPOSITORY = "YouthOpps/ai-workspace"
BRANCH = "qa/251-hyundai-received-policy-attestation"
WORKFLOW = ".github/workflows/qa-hyundai-received-policy-attestation.yml"
REVIEWER_SHA256 = "c8bfa742ffcd2638a1926c8068b58c3f0cc9bcda7077b95ab3ac8a8ac5b01531"
REVIEW_SHA256 = 'da2cab55f82aea10d572ae2462f21f20d2c4798387195d62046557b789612df0'
ARCHIVE_SHA256 = '7060399db9ffe5995f653f438e4e588161d0e127a914b327dbb34c457cb9c82f'
STATE_SHA256 = 'd96454b26c4e48024e44caf94a02c033ad52090c2f1bca9218ea4fee9c5c027d'
POLICY_SHA256 = 'cd5aac514ef94339614d3e3c8b2e410e5c43d38d126b9c76d378685b9ba2d57a'
PROPOSAL_SHA256 = '56cde93f9270e014e2b56115b09224786733811939f497a4c15a8680443c224f'
OLD_HEAD = '98c4c84626cdf4dd23200136bdd766bd04c71805'
OLD_WORKFLOW = '.github/workflows/qa-hyundai-inventory-discovery-251.yml'
OWNER = {'created_at': '2026-11-21T15:45:57Z', 'head_sha': '98c4c84626cdf4dd23200136bdd766bd04c71805', 'job_id': 136896522389, 'ref': 'refs/heads/qa/hyundai-inventory-discovery-251', 'repository': 'YouthOpps/ai-workspace', 'run_attempt': 1, 'run_id': 44920912547, 'scope_sha256': 'dc0558a56cd038c78d3cd2f4801569c3b18543f1b69eca3b057686600ec8e306', 'source': 'hyundai251', 'workflow': '.github/workflows/qa-hyundai-inventory-discovery-251.yml', 'workflow_id': 426086692}
ARTIFACT_ID = 14713313110
DECISION = 'https://github.com/YouthOpps/data-pipeline/issues/251#issuecomment-7065124776'
ORIGIN = 'https://www.hyundai.com'


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def settlement(original, proof):
    require(digest(canonical(original)) == STATE_SHA256 and proof["scope"] == OWNER
            and proof["archive_sha256"] == ARCHIVE_SHA256
            and proof["artifact_id"] == ARTIFACT_ID and proof["decision"] == DECISION,
            "Wrong original owner or signed review")
    r = proof["response"]
    require(r["status"] == 200 and r["url"] == original["target"] == ORIGIN + "/robots.txt"
            and r["request_id"] == original["physical_id"] and original["logical_id"]
            and original["in_flight"] and original["physical_pending"]
            and not original["blocked"] and not original["rate_limit_strikes"] and original["policy"] is None
            and original["family"] == "youthopps-hyundai-careers-publisher-v1",
            "Wrong restrictive reservation")
    require(r["body_sha256"] == POLICY_SHA256 and r["content_length"] == r["body_length"] == 6953
            and r["complete_eof"] is True and r["clean_close"] is True and not r["retry_after"]
            and r["stop"] == "Unassessed invalid REP product token"
            and proof["policy_sha256"] == POLICY_SHA256
            and proof["entry"] == ORIGIN + "/sg/careers/joinus"
            and proof["ambiguity_disallows"] == ["/nl/nl/", "/it/it/"]
            and proof["both_identities_permitted"] is True, "Wrong policy assessment")
    require(original["starts"] == [original["physical_started"]]
            and original["starts"][0] <= r["wall_start"] <= r["wall_completion"] <= 1795276037
            and original["observed_at"] <= r["wall_completion"],
            "Unexpected original scan timing")
    policy = dict(url=original["target"],status=200,body_sha256=POLICY_SHA256,
                  unavailable=False,new_allowed=True,legacy_allowed=True)
    candidate = dict(original, completed=r["wall_completion"],
        observed_at=max(original["observed_at"],r["wall_completion"]),
        not_before=max(original["not_before"],1795276037 + original["interval"]),
        in_flight=False, physical_pending=False, outcome="response_assessed",
        completed_physical_id=original["physical_id"],completed_logical_id=original["logical_id"],
        policy=policy)
    require(digest(canonical(candidate)) == PROPOSAL_SHA256, "Independently reviewed floor differs")
    # Preserve the actual physical start alongside the pre-opener reservation for the next owner's MAX.
    return dict(candidate, starts=sorted(set(candidate["starts"]+[r["wall_start"]])))


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
            and jobs[0]["completed_at"] == "2026-11-21T15:47:17Z"
            and jobs[0]["conclusion"] == "failure" and jobs[0]["name"] == "First contact hyundai251",
            "Original job identity differs")
    artifacts = github(f"/actions/runs/{OWNER['run_id']}/artifacts?per_page=2")
    require(artifacts["total_count"] == 1 and len(artifacts["artifacts"]) == 1,
            "Original archive inventory differs")
    artifact = artifacts["artifacts"][0]
    require(artifact["id"] == ARTIFACT_ID
            and artifact["name"] == "first-contact-hyundai251-44920912547-1"
            and artifact["size_in_bytes"] == 20609
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
            and event["after"] == head and event["sender"]["id"] == 12278069
            and event["sender"]["type"] == "User" and env["GITHUB_ACTOR_ID"] == "12278069", "Wrong one-use settlement scope")
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
    out = Path(env["RUNNER_TEMP"]) / "hyundai251-policy-attestation"
    out.mkdir(mode=0o700)
    provenance = {
        "repository": REPOSITORY, "run_id": run_id, "head_sha": head,
        "previous_owner": OWNER, "previous_archive_id": ARTIFACT_ID,
        "previous_archive_sha256": ARCHIVE_SHA256, "previous_pending_state_sha256": STATE_SHA256,
        "review_sha256": digest(verified), "state_sha256": digest(successor_bytes),
        "policy_sha256": POLICY_SHA256, "reviewed_floor_sha256": PROPOSAL_SHA256, "publisher_requests": 0,
    }
    (out / "state.json").write_bytes(successor_bytes)
    (out / "provenance.json").write_bytes(canonical(provenance))
    print(json.dumps(provenance, indent=2))


if __name__ == "__main__":
    main()
