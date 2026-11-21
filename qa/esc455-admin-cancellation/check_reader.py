"""GitHub-only replay of the exact ESC transition and parent receipt."""
from reader import ARCHIVE_ID, ARCHIVE_SIZE, ARCHIVE_SHA, OWNER, restore_history
from transition import RECEIPT_ARCHIVE, download_receipt, github, read_url, require


def main():
    meta = github(f"/actions/artifacts/{ARCHIVE_ID}")
    require(meta["id"] == ARCHIVE_ID and meta["expired"] is False
            and meta["name"] == "esc455-cancelled-before-send" and meta["size_in_bytes"] == ARCHIVE_SIZE
            and meta["digest"] == "sha256:" + ARCHIVE_SHA
            and meta["workflow_run"]["id"] == OWNER["run_id"]
            and meta["workflow_run"]["head_sha"] == OWNER["head"], "Transition archive owner differs")
    url = f"https://api.github.com/repos/YouthOpps/ai-workspace/actions/artifacts/{ARCHIVE_ID}/zip"
    status, headers, _ = read_url(url, authorized=True, size=16384)
    destinations = headers.get_all("Location", [])
    require(status == 302 and len(destinations) == 1, "Missing authenticated archive redirect")
    status, _, archive = read_url(destinations[0], authorized=False, size=ARCHIVE_SIZE)
    require(status == 200, "Missing transition archive")
    receipt = download_receipt()
    stamp = 1795084621.674231
    early = restore_history(archive, receipt, startup_time=stamp)
    later = restore_history(archive, receipt, startup_time=stamp + 600)
    original = early["original_pending_journal"]
    assert original["physical_pending"] and early["ownership"]["active_owner"] is None
    assert not early["ownership"]["terminal_owner"]["publisher_completion_recorded"]
    assert early["last_actual_publisher_response"]["physical_id"] == original["completed_physical_id"]
    assert early["ownership"]["terminal_owner"]["physical_id"] != original["completed_physical_id"]
    assert early["pacing_floor"]["not_before"] == stamp + 300
    assert later["pacing_floor"]["not_before"] == stamp + 660
    assert early["pacing_floor"]["starts"] == later["pacing_floor"]["starts"] == original["starts"]
    assert len(original["starts"]) == 9 and not later["publisher_transport_authorized"]
    for source, parent, clock in [(archive[:-1], receipt, stamp), (archive, receipt[:-1], stamp),
                                  (archive, receipt, stamp - 1), (archive, receipt, float("nan"))]:
        try:
            restore_history(source, parent, startup_time=clock)
        except ValueError:
            continue
        raise AssertionError("Invalid state or clock was accepted")
    print(f"Verified schema-2 reader: {ARCHIVE_ID} with receipt {RECEIPT_ARCHIVE[0]}; 0 publisher requests")


if __name__ == "__main__":
    main()
