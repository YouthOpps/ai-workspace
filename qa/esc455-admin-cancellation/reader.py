"""Restore the reviewed ESC schema-2 research history without granting transport."""
import io
import json
import math
import zipfile

from transition import canonical, derive, receipt_parts, require, sha, verified_bundle


ARCHIVE_ID = 14713505609
ARCHIVE_SIZE = 1867
ARCHIVE_SHA = "47589ed35cfb97fba31ddb1c7ec321a9b1a37b822ba6ecc4d93b85944a0429a8"
OWNER = {
    "attempt": 1, "workflow_id": 426071578, "run_id": 44919039756, "job_id": 136890811766,
    "head": "b057c38341c0c94d8ede9fcfc0e9800585f81065",
    "decision": "https://github.com/YouthOpps/data-pipeline/issues/455#issuecomment-7064849037",
}


def restore_history(archive, receipt_archive, *, startup_time):
    """Read both authentic archives and apply the original 60-second startup quiet."""
    require(len(archive) == ARCHIVE_SIZE and sha(archive) == ARCHIVE_SHA,
            "ESC transition archive differs")
    with zipfile.ZipFile(io.BytesIO(archive)) as packed:
        require(packed.namelist() == ["ownership-transition.json"], "ESC transition members differ")
        raw = packed.read("ownership-transition.json")
    envelope = json.loads(raw)
    original, receipt = receipt_parts(receipt_archive)
    transition = derive(original, receipt, verified_bundle())
    require(raw == canonical({"owner": OWNER, "transition": transition,
                              "transition_sha256": sha(canonical(transition))}),
            "ESC transition owner or signed predecessor differs")
    floor = transition["pacing_floor"]
    require(type(startup_time) in (float, int) and math.isfinite(startup_time)
            and startup_time >= floor["observed_at"], "Invalid research startup time")
    deadline = startup_time + 60
    require(math.isfinite(deadline) and deadline > startup_time, "Invalid startup quiet deadline")
    return {
        "schema": 2, "family": transition["family"],
        "source_archive_id": ARCHIVE_ID, "source_archive_sha256": ARCHIVE_SHA,
        "original_pending_journal": transition["original_pending_journal"],
        "ownership": transition["ownership"],
        "last_actual_publisher_response": transition["last_actual_publisher_response"],
        "pacing_floor": {**floor, "observed_at": startup_time,
                         "not_before": max(deadline, floor["not_before"], floor["rate_limit_until"])},
        "publisher_transport_authorized": False, "successor_executable_authorized": False,
    }
