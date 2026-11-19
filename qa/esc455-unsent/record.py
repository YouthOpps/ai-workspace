"""Verify historical ESC evidence and record a receipt without a publisher request."""

import hashlib
import json
import os
from pathlib import Path
import subprocess
import urllib.request


ROOT = Path(__file__).resolve().parent
REPO = "YouthOpps/ai-workspace"
BRANCH = "qa/455-esc-unsent-reservation-receipt"
WORKFLOW = ".github/workflows/qa-esc-unsent-reservation-receipt.yml"
ORIGINAL_BRANCH = "qa/esc-volunteering-continuation-recovery-r2"
ORIGINAL_WORKFLOW = ".github/workflows/qa-esc-volunteering-continuation-recovery-r2.yml"
ORIGINAL_HEAD = "27f55109841b977400b1b32b1d048cf30e9418d3"
ORIGINAL_RUN, ORIGINAL_JOB, ORIGINAL_WORKFLOW_ID = 44506936284, 135500878841, 423697576
ARCHIVE_ID = 14519513187
ARCHIVE_SHA = "60c31ed094ea247df7eec6fb55d4a12cd76c13c9f53005cf8b9df078e2645b27"
JOURNAL_SHA = "8cf48a4bb7e499fafea19817212aa0172b2dd3fedd278aebffa276937b7af13e"
BUNDLE_SHA = "d02ef88dd46b625e62ff1baddaef744c4b54dc77aea1f2e172d81b008c194884"
CERT_SHA = "c8bfa742ffcd2638a1926c8068b58c3f0cc9bcda7077b95ab3ac8a8ac5b01531"


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, message, headers, url):
        return None


def github(path):
    request = urllib.request.Request("https://api.github.com/repos/" + REPO + path, headers={
        "Authorization": "Bearer " + os.environ["GITHUB_TOKEN"],
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    })
    with urllib.request.build_opener(NoRedirect()).open(request, timeout=15) as response:
        payload = response.read(2_000_001)
    require(len(payload) <= 2_000_000, "GitHub metadata exceeds bounds")
    return json.loads(payload)


def one_run(workflow, run_id):
    history = github(f"/actions/workflows/{workflow}/runs?per_page=2")
    require(history["total_count"] == 1 and len(history["workflow_runs"]) == 1
            and history["workflow_runs"][0]["id"] == run_id, "One-use run ownership differs")


def verify_predecessor():
    workflow = github(f"/actions/workflows/{ORIGINAL_WORKFLOW_ID}")
    require(workflow["state"] == "disabled_manually" and workflow["path"] == ORIGINAL_WORKFLOW,
            "Original workflow must be explicitly retired")
    old = github(f"/actions/runs/{ORIGINAL_RUN}/attempts/1")
    require((old["id"], old["workflow_id"], old["path"], old["head_sha"], old["head_branch"],
             old["run_attempt"], old["status"], old["conclusion"], old["event"]) ==
            (ORIGINAL_RUN, ORIGINAL_WORKFLOW_ID, ORIGINAL_WORKFLOW, ORIGINAL_HEAD,
             ORIGINAL_BRANCH, 1, "completed", "failure", "push"), "Original run differs")
    one_run(ORIGINAL_WORKFLOW_ID, ORIGINAL_RUN)
    jobs = github(f"/actions/runs/{ORIGINAL_RUN}/attempts/1/jobs")["jobs"]
    require(len(jobs) == 1, "Original job inventory differs")
    job = jobs[0]
    require((job["id"], job["run_id"], job["head_sha"], job["status"], job["conclusion"]) ==
            (ORIGINAL_JOB, ORIGINAL_RUN, ORIGINAL_HEAD, "completed", "failure"),
            "Original job differs")
    archive = github(f"/actions/artifacts/{ARCHIVE_ID}")
    owner = archive["workflow_run"]
    require(archive["id"] == ARCHIVE_ID and not archive["expired"]
            and archive["size_in_bytes"] == 1_715_575 and archive["digest"] == "sha256:" + ARCHIVE_SHA
            and owner["id"] == ORIGINAL_RUN and owner["head_sha"] == ORIGINAL_HEAD,
            "Original retained archive differs")


def adjudicate(bundle):
    """Keep the original pending state and return separate administrative evidence."""
    lineage = bundle["source_lineage"]
    journal = bundle["original_journal"]
    receipt = bundle["proposed_administrative_receipt"]
    require(bundle["enabled"] is False and bundle["independent_review_required"] is True
            and bundle["authorized_publisher_requests"] == 0
            and bundle["successor_executable_authorized"] is False, "Review scope was widened")
    require(lineage["archive_sha256"] == ARCHIVE_SHA and lineage["artifact_id"] == ARCHIVE_ID
            and lineage["run_id"] == ORIGINAL_RUN and lineage["head"] == ORIGINAL_HEAD
            and lineage["carried_lineage_runs"] == [44489312404, 44493281462, 44494524200, ORIGINAL_RUN],
            "Publisher run lineage differs")
    require(digest(canonical(journal)) == bundle["original_journal_sha256"] == JOURNAL_SHA
            and journal["outcome"] == "reserved"
            and journal["physical_pending"] is True and journal["in_flight"] is True,
            "Original pending journal differs")
    require(receipt["classification"] == "abandoned_unsent_registration"
            and receipt["publisher_response_received"] is False
            and receipt["publisher_completion_recorded"] is False
            and receipt["reserved_physical_id"] == journal["physical_id"]
            and receipt["reserved_logical_id"] == journal["logical_id"]
            and receipt["reserved_target"] == journal["target"]
            and receipt["reserved_wall_time"] == journal["physical_started"]
            and journal["physical_started"] in journal["starts"]
            and receipt["publisher_response_last_completed_wall_time"] == journal["completed"]
            and receipt["publisher_response_last_completed_physical_id"] == journal["completed_physical_id"],
            "Administrative receipt mislabels original transaction state")
    floor = max(journal["not_before"], journal["rate_limit_until"],
                journal["physical_started"] + max(300, journal["interval"], journal["page_interval"]))
    require(receipt["original_cooldown"] == journal["rate_limit_until"]
            and receipt["additional_quiet_seconds"] == 300 and receipt["proposed_not_before"] == floor,
            "Administrative waiting floor would weaken retained timing")
    return canonical(journal), {
        **receipt, "source_archive_id": ARCHIVE_ID, "source_archive_sha256": ARCHIVE_SHA,
        "retained_pending_journal_sha256": JOURNAL_SHA, "review_packet_sha256": BUNDLE_SHA,
        "previous_run_id": ORIGINAL_RUN, "publisher_requests": 0,
        "successor_executable_authorized": False, "retained_pending_journal": True,
    }


def verified_bundle():
    reviewed, certificate = ROOT / "reviewed-receipt.json", ROOT / "reviewer.pem"
    signature = ROOT / "reviewer-signature.cms"
    data = reviewed.read_bytes()
    require(digest(data) == BUNDLE_SHA and digest(certificate.read_bytes()) == CERT_SHA
            and signature.is_file(), "Exact independently signed review is required")
    verified = subprocess.check_output([
        "openssl", "cms", "-verify", "-binary", "-inform", "DER", "-nointern", "-noverify",
        "-certfile", str(certificate), "-content", str(reviewed), "-in", str(signature),
    ], timeout=20)
    require(verified == data, "Reviewed bytes differ")
    return json.loads(data)


def main():
    env = os.environ
    event = json.loads(Path(env["GITHUB_EVENT_PATH"]).read_bytes())
    ref = "refs/heads/" + BRANCH
    head = env["GITHUB_SHA"]
    require(env["GITHUB_REPOSITORY"] == REPO and env["GITHUB_RUN_ATTEMPT"] == "1"
            and env["GITHUB_REF"] == ref and env["GITHUB_EVENT_NAME"] == "push"
            and env["GITHUB_WORKFLOW_REF"] == REPO + "/" + WORKFLOW + "@" + ref
            and env["GITHUB_WORKFLOW_SHA"] == head and "DATA_SOURCE_TOKEN" not in env
            and event["created"] is True and event["deleted"] is False
            and event["before"] == "0" * 40 and event["after"] == head,
            "Wrong receipt execution scope")
    require(subprocess.check_output(["git", "rev-parse", "HEAD"], text=True, timeout=10).strip()
            == head, "Checkout differs")
    run_id = int(env["GITHUB_RUN_ID"])
    run = github(f"/actions/runs/{run_id}/attempts/1")
    require((run["id"], run["head_sha"], run["run_attempt"], run["head_branch"], run["event"], run["path"])
            == (run_id, head, 1, BRANCH, "push", WORKFLOW), "Receipt run ownership differs")
    one_run(run["workflow_id"], run_id)
    pending, receipt = adjudicate(verified_bundle())
    verify_predecessor()
    out = Path(env["RUNNER_TEMP"]) / "esc455-unsent-reservation-receipt"
    out.mkdir(mode=0o700)
    (out / "original-pending-journal.json").write_bytes(pending)
    (out / "administrative-receipt.json").write_bytes(canonical({
        **receipt, "receipt_run_id": run_id, "receipt_head": head,
    }))
    print("Verified abandoned unsent reservation receipt; publisher requests: 0")


if __name__ == "__main__":
    main()
