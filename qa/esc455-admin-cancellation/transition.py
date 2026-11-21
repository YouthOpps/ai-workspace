"""Record the exact abandoned ESC reservation as an administrative transition."""

import base64
import hashlib
import io
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import urllib.error
import urllib.parse
import urllib.request
import zipfile

ROOT = Path(__file__).resolve().parent
REPO = "YouthOpps/ai-workspace"
PIPELINE = "YouthOpps/data-pipeline"
OWNER_ID = 12278069
BRANCH = "qa/455-esc-administrative-cancellation"
WORKFLOW = ".github/workflows/qa-esc-administrative-cancellation.yml"
SUBTREE = "qa/esc455-admin-cancellation/"
GATE = "scope.json"
ORIGINAL = (44506936284, 135500878841, 423697576, "27f55109841b977400b1b32b1d048cf30e9418d3",
            "qa/esc-volunteering-continuation-recovery-r2", "failure")
RECEIPT = (44512977477, 135521646461, 423735859, "30e450ffdb4069a4710d37a294741dc571f36e4f",
           "qa/455-esc-unsent-reservation-receipt", "success")
RETIRED = {
    423590700: (44489312404, ".github/workflows/qa-esc-volunteering-first-contact.yml"),
    423614905: (44493281462, ".github/workflows/qa-esc-volunteering-continuation.yml"),
    423621888: (44494524200, ".github/workflows/qa-esc-volunteering-continuation-recovery.yml"),
    ORIGINAL[2]: (ORIGINAL[0], ".github/workflows/qa-esc-volunteering-continuation-recovery-r2.yml"),
    RECEIPT[2]: (RECEIPT[0], ".github/workflows/qa-esc-unsent-reservation-receipt.yml"),
}
PROOF = {
    "reviewed-receipt.json": "d02ef88dd46b625e62ff1baddaef744c4b54dc77aea1f2e172d81b008c194884",
    "reviewer-signature.cms": "2b6a8935a349d086ef7baff28fb789cc3631685115442f378eea20a313875c2b",
    "reviewer.pem": "c8bfa742ffcd2638a1926c8068b58c3f0cc9bcda7077b95ab3ac8a8ac5b01531",
}
ORIGINAL_ARCHIVE = (14519513187, 1715575,
                    "60c31ed094ea247df7eec6fb55d4a12cd76c13c9f53005cf8b9df078e2645b27")
RECEIPT_ARCHIVE = (14522679574, 1546,
                   "65d29577ef62dc15ff7de051b06fafcd06f417f897b298fa33850b9040e7675d")
JOURNAL_SHA = "8cf48a4bb7e499fafea19817212aa0172b2dd3fedd278aebffa276937b7af13e"
JOURNAL_NAME = "original-pending-journal.json"
RECEIPT_NAME = "administrative-receipt.json"
OUTPUT_FOLDER = "esc455-cancelled-before-send"


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def verified_bundle():
    for name, digest in PROOF.items():
        require(sha((ROOT / name).read_bytes()) == digest, "Exact signed review input differs")
    content = ROOT / "reviewed-receipt.json"
    verified = subprocess.check_output([
        "openssl", "cms", "-verify", "-binary", "-inform", "DER", "-nointern", "-noverify",
        "-certfile", str(ROOT / "reviewer.pem"), "-content", str(content),
        "-in", str(ROOT / "reviewer-signature.cms"),
    ], timeout=20)
    require(verified == content.read_bytes(), "Exact independently signed bytes differ")
    return json.loads(verified)


def receipt_parts(archive):
    require(len(archive) == RECEIPT_ARCHIVE[1] and sha(archive) == RECEIPT_ARCHIVE[2],
            "Exact hosted receipt archive bytes differ")
    with zipfile.ZipFile(io.BytesIO(archive)) as packed:
        entries = packed.infolist()
        require(len(entries) == 2 and {e.filename for e in entries} == {JOURNAL_NAME, RECEIPT_NAME}
                and all(0 < e.file_size <= 4096 and not e.flag_bits & 1
                        and not stat.S_ISLNK(e.external_attr >> 16) for e in entries),
                "Unexpected hosted receipt archive member")
        return packed.read(JOURNAL_NAME), packed.read(RECEIPT_NAME)


def derive(raw_journal, raw_receipt, bundle):
    """Separate administrative cancellation from the last actual publisher completion."""
    require(sha(raw_journal) == JOURNAL_SHA, "The original pending journal differs")
    original = json.loads(raw_journal)
    administrative = json.loads(raw_receipt)
    require(raw_journal == canonical(original) and raw_receipt == canonical(administrative)
            and original == bundle["original_journal"]
            and bundle["original_journal_sha256"] == JOURNAL_SHA
            and bundle["enabled"] is False
            and bundle["authorized_publisher_requests"] == 0
            and bundle["successor_executable_authorized"] is False,
            "Signed original source and zero-request scope differ")
    expected = {
        **bundle["proposed_administrative_receipt"],
        "source_archive_id": ORIGINAL_ARCHIVE[0], "source_archive_sha256": ORIGINAL_ARCHIVE[2],
        "retained_pending_journal_sha256": JOURNAL_SHA, "review_packet_sha256": PROOF["reviewed-receipt.json"],
        "previous_run_id": ORIGINAL[0], "publisher_requests": 0,
        "successor_executable_authorized": False, "retained_pending_journal": True,
        "receipt_run_id": RECEIPT[0], "receipt_head": RECEIPT[3],
    }
    require(administrative == expected
            and administrative["classification"] == "abandoned_unsent_registration"
            and administrative["publisher_response_received"] is False
            and administrative["publisher_completion_recorded"] is False,
            "The exact receipt lacks a proven unsent disposition")
    require(original["schema"] == 1 and original["family"] == "youthopps-esc-publisher-v1"
            and original["in_flight"] is True and original["physical_pending"] is True
            and original["outcome"] == "reserved"
            and original["physical_id"] != original["completed_physical_id"]
            and original["logical_id"] != original["completed_logical_id"]
            and original["physical_id"] == administrative["reserved_physical_id"]
            and original["logical_id"] == administrative["reserved_logical_id"]
            and original["target"] == administrative["reserved_target"]
            and original["physical_started"] == administrative["reserved_wall_time"]
            and original["physical_started"] in original["starts"]
            and original["completed_physical_id"] == administrative["publisher_response_last_completed_physical_id"]
            and original["completed"] == administrative["publisher_response_last_completed_wall_time"],
            "Cancellation does not describe this one unmatched owner")
    require(not original["blocked"] and original["legacy_rate_history_unknown"]
            and original["legacy_policy_history_unknown"]
            and administrative["additional_quiet_seconds"] == 300
            and administrative["original_cooldown"] == original["rate_limit_until"],
            "An independent hold or different inherited constraints require a separate decision")
    floor = max(original["not_before"], original["rate_limit_until"],
                original["physical_started"] + max(300, original["interval"], original["page_interval"]))
    require(floor == administrative["proposed_not_before"], "Administrative transition weakens timing")
    return {
        "schema": 2, "kind": "esc455_administrative_ownership_transition",
        "family": original["family"], "publisher_requests": 0,
        "publisher_transport_authorized": False, "successor_executable_authorized": False,
        "original_pending_journal": original, "original_pending_journal_sha256": JOURNAL_SHA,
        "original_owned_archive": list(ORIGINAL_ARCHIVE), "original_owned_run": list(ORIGINAL),
        "administrative_receipt": administrative, "administrative_receipt_sha256": sha(raw_receipt),
        "administrative_owned_archive": list(RECEIPT_ARCHIVE), "administrative_owned_run": list(RECEIPT),
        "ownership": {
            "active_owner": None,
            "terminal_owner": {
                "disposition": "cancelled_before_send",
                "physical_id": original["physical_id"], "logical_id": original["logical_id"],
                "target": original["target"], "reservation_wall_time": original["physical_started"],
                "response_received": False, "publisher_completion_recorded": False,
            },
        },
        "last_actual_publisher_response": {
            "physical_id": original["completed_physical_id"],
            "logical_id": original["completed_logical_id"],
            "completed": original["completed"], "inventory_completed": original["inventory_completed"],
        },
        "pacing_floor": {
            **{key: original[key] for key in (
                "observed_at", "interval", "page_interval", "starts", "rate_limit_strikes",
                "rate_limit_until", "legacy_rate_history_unknown", "legacy_policy_history_unknown",
                "blocked", "rates", "policy")},
            "not_before": floor,
            "fresh_startup_quiet_required": True,
        },
    }


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, message, headers, url):
        return None


def read_url(url, *, authorized, size):
    parsed = urllib.parse.urlsplit(url)
    host = parsed.hostname or ""
    require(parsed.scheme == "https" and parsed.username is None and parsed.password is None
            and parsed.port is None and not parsed.fragment
            and (host == "api.github.com" if authorized else
                 host.endswith((".blob.core.windows.net", ".actions.githubusercontent.com"))),
            "Administrative workflow attempted an unreviewed network destination")
    headers = {}
    if authorized:
        headers = {"Authorization": "Bearer " + os.environ["GITHUB_TOKEN"],
                   "Accept": "application/vnd.github+json",
                   "X-GitHub-Api-Version": "2022-11-28"}
    request = urllib.request.Request(url, headers=headers, method="GET")
    try:
        response = urllib.request.build_opener(NoRedirect()).open(request, timeout=15)
    except urllib.error.HTTPError as error:
        response = error
    with response:
        body = response.read(size + 1)
        require(len(body) <= size, "Administrative response exceeds bounds")
        return response.status, response.headers, body


def github(path, repository=REPO):
    require(repository in {REPO, PIPELINE} and path.startswith("/") and not path.startswith("//"),
            "Unreviewed GitHub API namespace")
    status, _, body = read_url("https://api.github.com/repos/" + repository + path,
                               authorized=True, size=2_000_000)
    require(status == 200, "Exact authenticated GitHub control request failed")
    return json.loads(body)


def download_receipt():
    url = f"https://api.github.com/repos/{REPO}/actions/artifacts/{RECEIPT_ARCHIVE[0]}/zip"
    status, headers, _ = read_url(url, authorized=True, size=16384)
    redirect = headers.get_all("Location", [])
    require(status == 302 and len(redirect) == 1, "Exact receipt archive redirect differs")
    status, _, body = read_url(redirect[0], authorized=False, size=RECEIPT_ARCHIVE[1])
    require(status == 200, "Exact receipt storage response failed")
    return body


def verify_history():
    for workflow_id, (run_id, path) in RETIRED.items():
        workflow = github(f"/actions/workflows/{workflow_id}")
        runs = github(f"/actions/workflows/{workflow_id}/runs?per_page=2")
        require(workflow["id"] == workflow_id and workflow["path"] == path
                and workflow["state"] == "disabled_manually"
                and runs["total_count"] == len(runs["workflow_runs"]) == 1
                and runs["workflow_runs"][0]["id"] == run_id
                and runs["workflow_runs"][0]["run_attempt"] == 1
                and runs["workflow_runs"][0]["status"] == "completed",
                "Prior ESC workflow is not exclusively retired")
    for owner, archive in ((ORIGINAL, ORIGINAL_ARCHIVE), (RECEIPT, RECEIPT_ARCHIVE)):
        run, job_id, workflow, head, branch, outcome = owner
        old = github(f"/actions/runs/{run}/attempts/1")
        require((old["id"], old["head_sha"], old["workflow_id"], old["path"], old["head_branch"],
                 old["run_attempt"], old["event"], old["status"], old["conclusion"]) ==
                (run, head, workflow, RETIRED[workflow][1], branch, 1, "push", "completed", outcome)
                and all(old[key]["full_name"] == REPO for key in ("repository", "head_repository")),
                "Exact predecessor run identity differs")
        job = github(f"/actions/runs/{run}/attempts/1/jobs?per_page=2")
        require(job["total_count"] == len(job["jobs"]) == 1, "Exact predecessor job inventory differs")
        actual = job["jobs"][0]
        require((actual["id"], actual["run_id"], actual["run_attempt"], actual["head_sha"],
                 actual["status"], actual["conclusion"]) == (job_id, run, 1, head, "completed", outcome),
                "Exact predecessor job identity differs")
        artifact_id, size, digest = archive
        info = github(f"/actions/artifacts/{artifact_id}")
        require(info["id"] == artifact_id and info["size_in_bytes"] == size
                and info["digest"] == "sha256:" + digest and info["expired"] is False
                and info["workflow_run"]["id"] == run and info["workflow_run"]["head_sha"] == head,
                "Exact predecessor archive ownership differs")


def verify_current(scope):
    require(scope == {"enabled": True, "issue": 455, "publisher_requests": 0,
                      "schema": 1, "transition": "cancelled_before_send"},
            "Administrative transition is OFF")
    env = os.environ
    ref = "refs/heads/" + BRANCH
    head = env["GITHUB_SHA"]
    require(re.fullmatch("[0-9a-f]{40}", head) and re.fullmatch("[1-9][0-9]*", env["GITHUB_RUN_ID"]),
            "Malformed exact hosted head or run")
    require(env.get("GITHUB_ACTIONS") == "true" and env.get("GITHUB_REPOSITORY") == REPO
            and env.get("GITHUB_RUN_ATTEMPT") == "1" and env.get("GITHUB_EVENT_NAME") == "push"
            and env.get("GITHUB_REF") == ref and env.get("GITHUB_ACTOR_ID") == str(OWNER_ID)
            and env.get("GITHUB_WORKFLOW_REF") == REPO + "/" + WORKFLOW + "@" + ref
            and env.get("GITHUB_WORKFLOW_SHA") == head and "DATA_SOURCE_TOKEN" not in env,
            "Unreviewed hosted administrative transition scope")
    event = json.loads(Path(env["GITHUB_EVENT_PATH"]).read_bytes())
    require(event.get("created") is True and event.get("deleted") is False
            and event.get("before") == "0" * 40 and event.get("after") == head
            and event.get("ref") == ref and event["sender"]["id"] == OWNER_ID
            and event["repository"]["full_name"] == REPO, "Exact first creation event differs")
    identifier = int(env["GITHUB_RUN_ID"])
    run = github(f"/actions/runs/{identifier}/attempts/1")
    workflow_id = run["workflow_id"]
    require((run["id"], run["head_sha"], run["head_branch"], run["path"], run["event"],
              run["run_attempt"], run["status"], run["actor"]["id"]) ==
            (identifier, head, BRANCH, WORKFLOW, "push", 1, "in_progress", OWNER_ID)
            and all(run[key]["full_name"] == REPO for key in ("repository", "head_repository")),
            "Exact current administrative run differs")
    workflow = github(f"/actions/workflows/{workflow_id}")
    require(workflow["id"] == workflow_id and workflow["path"] == WORKFLOW
            and workflow["state"] == "active", "Exact current administrative workflow differs")
    history = github(f"/actions/workflows/{workflow_id}/runs?per_page=2")
    jobs = github(f"/actions/runs/{identifier}/attempts/1/jobs?per_page=2")
    branch = github("/git/ref/heads/" + BRANCH)
    require(history["total_count"] == len(history["workflow_runs"]) == 1
            and history["workflow_runs"][0]["id"] == identifier
            and history["workflow_runs"][0]["run_attempt"] == 1
            and history["workflow_runs"][0]["head_sha"] == head
            and jobs["total_count"] == len(jobs["jobs"]) == 1
            and branch["ref"] == ref and branch["object"]["sha"] == head
            and branch["object"]["type"] == "commit", "Administrative exclusive owner differs")
    job = jobs["jobs"][0]
    require((job["name"], job["run_id"], job["run_attempt"], job["head_sha"], job["status"]) ==
            ("transition", identifier, 1, head, "in_progress"), "Exact current administrative job differs")
    checkout = ROOT.parents[1]
    require(subprocess.check_output(["git", "-C", str(checkout), "rev-parse", "HEAD"],
                                    text=True, timeout=10).strip() == head, "Actual checkout differs")
    for path in (WORKFLOW, *(SUBTREE + name for name in (*PROOF, GATE, "transition.py"))):
        immutable = github(f"/contents/{path}?ref={head}")
        require(immutable["path"] == path and immutable["type"] == "file"
                and immutable["encoding"] == "base64"
                and base64.b64decode("".join(immutable["content"].splitlines()), validate=True)
                == (checkout / path).read_bytes(), "Immutable administrative input differs")
    comments = github("/issues/455/comments?per_page=100&page=1", PIPELINE)
    require(type(comments) is list and len(comments) < 100, "Exact grant pagination incomplete")
    head_line = f"Approved ESC administrative cancellation head {head}"
    scope_line = f"ESC administrative cancellation scope {sha((ROOT / GATE).read_bytes())}"
    decisions = [comment for comment in comments
                 if comment["user"]["id"] == OWNER_ID and comment["user"]["type"] == "User"
                 and comment["created_at"] == comment["updated_at"] < run["created_at"]
                 and comment["issue_url"] == f"https://api.github.com/repos/{PIPELINE}/issues/455"
                 and (comment["body"] or "").splitlines().count(head_line) == 1
                 and (comment["body"] or "").splitlines().count(scope_line) == 1]
    require(len(decisions) == 1 and decisions[0]["html_url"] ==
            f"https://github.com/{PIPELINE}/issues/455#issuecomment-{decisions[0]['id']}",
            "Exact independently reviewed zero-publisher grant missing")
    return {"run_id": identifier, "attempt": 1, "head": head, "workflow_id": workflow_id,
            "job_id": job["id"], "decision": decisions[0]["html_url"]}


def verify_exclusive(owner):
    collision = re.compile(
        r"(?<![a-z0-9])esc[-_ ]|european[-_ ]youth[-_ ]portal|european[-_ ]solidarity[-_ ]corps", re.I)
    allowed = {key: value[1] for key, value in RETIRED.items()}
    allowed[owner["workflow_id"]] = WORKFLOW
    for repository in (REPO, PIPELINE):
        seen, total = set(), None
        for page in range(1, 11):
            listing = github(f"/actions/workflows?per_page=100&page={page}", repository)
            rows, count = listing["workflows"], listing["total_count"]
            require(type(rows) is list and len(rows) <= 100 and type(count) is int
                    and (total is None or total == count), "Publisher workflow inventory differs")
            total = count
            for row in rows:
                identity = row["id"]
                require(identity not in seen, "Publisher workflow inventory duplicated")
                seen.add(identity)
                if repository == PIPELINE and identity == 378390058:
                    # DZS lists Czech grants on www.dzs.cz, outside the European Youth Portal.
                    # A changed, re-enabled or recently executed DZS owner needs review.
                    require((row["name"], row["path"], row["state"]) == (
                        "Fetch DZS European Solidarity Corps", ".github/workflows/fetch-cz-dzs.yml",
                        "disabled_manually"), "Reviewed DZS owner differs")
                    inventory = github("/actions/workflows/378390058/runs?per_page=100", repository)
                    dzs_runs = inventory["workflow_runs"]
                    require(inventory["total_count"] == len(dzs_runs) == 12
                            and all(run["status"] == "completed" for run in dzs_runs)
                            and (dzs_runs[0]["id"], dzs_runs[0]["run_attempt"]) == (38979389959, 1),
                            "Reviewed DZS history differs")
                    continue
                if collision.search(row["name"] + " " + row["path"]):
                    require(repository == REPO and allowed.get(identity) == row["path"],
                            "Other ESC workflow ownership requires review")
            if len(seen) == total:
                break
            require(len(seen) < total and len(rows) == 100, "Incomplete publisher workflow inventory")
        else:
            raise ValueError("Publisher workflow inventory exceeded bound")
        if repository == REPO:
            require(set(allowed) <= seen, "An exact ESC owner is missing from workflow inventory")


def persist(result, owner):
    root = Path(os.environ["RUNNER_TEMP"])
    require(root.is_absolute() and root == root.resolve(), "Unsafe runner output root")
    parent = root / OUTPUT_FOLDER
    parent.mkdir(mode=0o700)
    data = canonical({"owner": owner, "transition_sha256": sha(canonical(result)), "transition": result})
    descriptor = os.open(parent, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        info = os.fstat(descriptor)
        require(info.st_uid == os.getuid() and stat.S_IMODE(info.st_mode) == 0o700,
                "Unsafe cancellation output directory")
        entry = os.open(".unpublished", os.O_RDWR | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                        mode=0o600, dir_fd=descriptor)
        with os.fdopen(entry, "w+b") as output:
            output.write(data)
            output.flush()
            os.fsync(output.fileno())
            output.seek(0)
            original = os.fstat(output.fileno())
            require(output.read() == data and original.st_nlink == 1,
                    "Written administrative receipt bytes differ")
            named = os.stat(".unpublished", dir_fd=descriptor, follow_symlinks=False)
            identity = original.st_dev, original.st_ino
            require((named.st_dev, named.st_ino) == identity, "Written administrative receipt changed")
            os.link(".unpublished", "ownership-transition.json", src_dir_fd=descriptor,
                    dst_dir_fd=descriptor, follow_symlinks=False)
            named = os.stat("ownership-transition.json", dir_fd=descriptor, follow_symlinks=False)
            require((named.st_dev, named.st_ino) == identity, "Final administrative receipt changed")
            os.unlink(".unpublished", dir_fd=descriptor)
            output.seek(0)
            require(output.read() == data and os.fstat(output.fileno()).st_nlink == 1,
                    "Final administrative receipt bytes differ")
        current = parent.lstat()
        require((current.st_dev, current.st_ino) == (info.st_dev, info.st_ino),
                "Administrative output directory changed")
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def main():
    scope = json.loads((ROOT / GATE).read_bytes())
    owner = verify_current(scope)
    verify_history()
    verify_exclusive(owner)
    bundle = verified_bundle()
    original, receipt = receipt_parts(download_receipt())
    result = derive(original, receipt, bundle)
    verify_history()
    require(verify_current(scope) == owner, "Administrative owner changed before persistence")
    verify_exclusive(owner)
    persist(result, owner)
    print("Verified ESC administrative cancellation. Publisher requests: 0.")


if __name__ == "__main__":
    main()
