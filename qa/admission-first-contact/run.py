"""Run the original bounded first-contact protocol inside the reviewed job."""

import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

from notice import notice_facts

from hosted_identity import IdentityFailure, ROOT, SOURCES, display, require, verify_authority

LIMIT = 16_384


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def write_once(path, raw):
    with path.open("xb") as file:
        file.write(raw)
        file.flush()
        os.fsync(file.fileno())


def checked_bytes(path, digest):
    raw = path.read_bytes()
    require(sha(raw) == digest, f"Frozen input differs: {path.name}")
    return raw


def load(path):
    spec = importlib.util.spec_from_file_location("first_contact_foundation", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def prepare(source, row, directory):
    source_path = ROOT / source
    original = checked_bytes(source_path / "foundation.py", row["foundation_sha256"])
    history = checked_bytes(source_path / "history-manifest.json", row["history_sha256"])
    write_once(directory / "history-manifest.json", history)

    old_gate = (
        b"    if ('DATA_SOURCE_TOKEN' in os.environ\n"
        b"            or os.environ.get('GITHUB_ACTIONS') == 'true'):\n"
        b"        raise Stop('Nonpublishing local research only')"
    )
    new_gate = (
        b"    from hosted_identity import verify_authority\n"
        + f"    _, _, authority = verify_authority({source!r})\n".encode("ascii")
        + b"    if authority['decision'] != selected:\n"
        + b"        raise Stop('Original maintainer decision differs')"
    )
    bindings = (
        (old_gate, new_gate),
        (f"WORK = Path('/workspace/work/{source}')".encode(),
         b"WORK = Path(__file__).resolve().parent"),
        (b"ROOT_INITIALIZATION_DECISION = None",
         f"ROOT_INITIALIZATION_DECISION = {row['decision']!r}".encode("ascii")),
        (b"ROOT_CAPTURE_DECISION = None",
         f"ROOT_CAPTURE_DECISION = {row['decision']!r}".encode("ascii")),
        (b"HISTORY_SHA256 = None",
         f"HISTORY_SHA256 = {row['history_sha256']!r}".encode("ascii")),
        (b"MACHINE_SHA256 = None",
         f"MACHINE_SHA256 = {sha(Path('/etc/machine-id').read_bytes())!r}".encode("ascii")),
    )
    active = original
    for old, new in bindings:
        require(active.count(old) == 1, "First-contact binding is not unique")
        active = active.replace(old, new, 1)
    restored = active
    for old, new in reversed(bindings):
        require(restored.count(new) == 1, "First-contact reversal is not unique")
        restored = restored.replace(new, old, 1)
    require(restored == original, "Published foundation does not reverse")
    path = directory / "foundation.py"
    write_once(path, active)
    return path, sha(active)


def initialize(path):
    module = load(path)
    result = module.initialize()
    sys.stdout.buffer.write(canonical(result) + b"\n")


def collect_state(module, result, journal_directory, output):
    complete_ack = [item for item in module.AUDIT["persistence"] if item.get("acknowledged")]
    summary = {
        "persistence_attempts": len(module.AUDIT["persistence"]),
        "persistence_acknowledgements": len(complete_ack),
        "state": "missing_unverified",
    }
    try:
        require(result is not None, "Missing accepted initializer outcome")
        require(journal_directory == module.paths()[0], "Source journal path differs")
        # The original Journal opens the parent, family and owned files with
        # no-follow descriptors, binds their identities and permissions to the
        # original initializer, and retains both locks throughout the read.
        with module.Journal(result) as journal:
            state = journal.read()
            state_raw = journal.ack
            require(len(state_raw) <= LIMIT and canonical(state) == state_raw,
                    "Current state bytes are not a valid canonical generation")
            expected = (complete_ack[-1]["bytes"] if complete_ack
                        else state_raw if sha(state_raw) == result["state_sha256"] else None)
            require(expected == state_raw, "Current state differs from the last acknowledgement")
        # Closing and the Journal's final generation check must also succeed
        # before these bytes can qualify for a transfer.
        write_once(output / "acknowledged-state.json", state_raw)
        summary.update({
            "state": "acknowledged",
            "state_sha256": sha(state_raw),
            "pending": state["in_flight"] or state["physical_pending"],
            "blocked": state["blocked"],
        })
    except (KeyError, OSError, ValueError, RuntimeError, module.Stop) as error:
        summary["state_error"] = type(error).__name__
    if complete_ack and summary["state"] != "acknowledged":
        write_once(output / "last-acknowledgement-unqualified.json", complete_ack[-1]["bytes"])
    return summary


def run():
    source = os.environ.get("SOURCE")
    require(source in SOURCES, "Unknown contact source")
    output = Path(os.environ["RUNNER_TEMP"]) / "admissions-first-contact" / source
    output.mkdir(parents=True, exist_ok=False, mode=0o700)
    write_once(output / "preflight.json", canonical({
        "classification": "unverified_preflight_no_collection_authority",
        "source": source,
        "event": display(os.environ.get("GITHUB_EVENT_NAME")),
        "ref": display(os.environ.get("GITHUB_REF")),
        "head_sha": display(os.environ.get("GITHUB_SHA")),
        "run_id": display(os.environ.get("GITHUB_RUN_ID")),
        "attempt": display(os.environ.get("GITHUB_RUN_ATTEMPT")),
    }))
    try:
        scope, manifest, row = verify_authority(source)
    except Exception as error:
        evidence = {
            "classification": "failed_before_initializer_or_publisher",
            "source": source,
            "error_type": type(error).__name__,
        }
        if isinstance(error, IdentityFailure):
            evidence.update({"reason": error.reason, "fields": error.fields})
        write_once(output / "preflight-failure.json", canonical(evidence))
        if isinstance(error, IdentityFailure):
            print(error)
        else:
            print(f"{source}: preflight failed ({type(error).__name__})")
        raise SystemExit(1)
    write_once(output / "attempt.json", canonical({"scope": scope, "decision": row["decision"],
                                                    "classification": "unresolved_until_result"}))

    with tempfile.TemporaryDirectory(prefix="publisher-scope-") as temporary:
        path, active_sha = prepare(source, row, Path(temporary))
        os.environ[row["env_prefix"] + "_ACCEPTED_FOUNDATION_SHA256"] = active_sha
        module = load(path)
        require(module.decision(row["decision"]) and module.REQUEST_URLS == tuple(row["urls"]),
                "Exact publisher frontier differs")
        preceding = None
        assessment = None
        result = None
        error = None
        journal_directory, _ = module.paths()
        try:
            child = subprocess.run(
                [sys.executable, "-B", str(Path(__file__).resolve()), "initialize", str(path)],
                capture_output=True, timeout=45, check=False,
            )
            require(child.returncode == 0 and not child.stderr, "Original initializer did not exit cleanly")
            candidate = json.loads(child.stdout)
            require(child.stdout == canonical(candidate) + b"\n"
                    and candidate["source_sha256"] == active_sha
                    and candidate["history_sha256"] == row["history_sha256"]
                    and candidate["publisher_requests"] == 0, "Original initializer receipt differs")
            preceding = candidate
            proof = {
                "initializer_exit": child.returncode, "source_sha256": active_sha,
                "result": preceding, "hosted_authority": scope,
            }
            parent = os.open(path.parent, os.O_DIRECTORY | os.O_RDONLY | os.O_NOFOLLOW)
            identity = module.identity(os.fstat(parent))
            primary = None
            try:
                proof_raw, _ = module.create_once(parent, "initialization-success-proof.json", proof)
            except BaseException as failure:
                primary = failure
                raise
            finally:
                module.checked_close([(parent, identity)], primary)
            os.environ[row["env_prefix"] + "_OBSERVED_INIT_PROOF_SHA256"] = sha(proof_raw)
            result = module.capture(preceding)
            assessment = notice_facts(module.AUDIT["requests"][-1])
        except Exception as failure:
            error = {"type": type(failure).__name__}
        summary = collect_state(module, preceding, journal_directory, output)
        requests = module.AUDIT["requests"]
        settled = result is not None and summary["state"] == "acknowledged" \
            and result["state_sha256"] == summary["state_sha256"] \
            and not summary["blocked"] and not summary["pending"]
        evidence = {
            **summary,
            "scope": scope,
            "decision": row["decision"],
            "original_foundation_sha256": row["foundation_sha256"],
            "active_foundation_sha256": active_sha,
            "initialization_success": preceding is not None,
            "capture_outcome": "settled" if settled and assessment is not None else "stopped",
            "requests": [
                {key: row.get(key) for key in ("url", "status", "request_id", "wall_start",
                                              "wall_completion", "start", "completion")}
                for row in requests
            ],
            "notice": assessment,
            "raw_response_bytes_stored": False,
            "failure_type": error["type"] if error else None,
            "publisher_access_clearance": False,
            "native_test": False,
        }
        write_once(output / "result.json", canonical(evidence))
        print(f"{source}: {evidence['capture_outcome']}, requests={len(requests)}")
        require(settled and assessment is not None, "The scoped notice requires review")


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "initialize":
        initialize(Path(sys.argv[2]))
    elif len(sys.argv) == 1:
        run()
    else:
        raise SystemExit("Unexpected first-contact command")
