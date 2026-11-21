"""Preserve original public-programme research ZIPs without contacting publishers."""

import hashlib
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path


REPOSITORY = "YouthOpps/ai-workspace"
REPOSITORY_ID = 1410255493
API = f"https://api.github.com/repos/{REPOSITORY}"
OUTPUT = "public-programmes-evidence-custody"
PINS = json.loads(Path(__file__).with_name('issuer-pins.json').read_text(encoding='utf-8'))


class CustodyError(Exception):
    """A closed custody check. Its public message must not contain URLs."""


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def require(value, message):
    if not value:
        raise CustodyError(message)


def signed_destination(url):
    try:
        target = urllib.parse.urlsplit(url)
        require(
            target.scheme == "https"
            and re.fullmatch(
                r"productionresultssa[0-9]+\.blob\.core\.windows\.net",
                target.netloc,
            )
            and bool(target.path.strip("/"))
            and bool(target.query)
            and not target.fragment
            and not any(character.isspace() for character in url),
            "Unrecognized signed artifact delivery host",
        )
    except (TypeError, ValueError):
        raise CustodyError("Malformed signed artifact delivery URL") from None
    return url


def exact_fields(value, fields, message):
    require(isinstance(value, dict) and all(
        key in value and type(value[key]) is type(expected) and value[key] == expected
        for key, expected in fields.items()
    ), message)


class GitHubCustody:
    def __init__(self, token, opener=None):
        self.opener = opener if opener is not None else urllib.request.build_opener(
            NoRedirect()
        )
        self.github_headers = {
            "Authorization": "Bearer " + token,
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

    def open(self, url, headers=None):
        try:
            return self.opener.open(
                urllib.request.Request(url, headers=headers or {}), timeout=25
            )
        except urllib.error.HTTPError as response:
            return response
        except (OSError, ValueError):
            raise CustodyError("Artifact custody request failed") from None

    def api(self, path):
        with self.open(API + path, self.github_headers) as response:
            require(response.status == 200, "GitHub custody metadata request failed")
            raw = response.read(262145)
        require(len(raw) <= 262144, "GitHub custody metadata exceeded size bound")
        return json.loads(raw)

    def archive_metadata(self, pin):
        archive_id = pin["artifact"]
        download_endpoint = f"{API}/actions/artifacts/{archive_id}/zip"
        result = self.api(f"/actions/artifacts/{archive_id}")
        exact_fields(result, {
            "id": archive_id,
            "name": pin["artifact_name"],
            "size_in_bytes": pin["bytes"],
            "digest": "sha256:" + pin["sha256"],
            "expired": False,
            "expires_at": pin["expires_at"],
            "archive_download_url": download_endpoint,
        }, "GitHub archive properties do not match the reviewed pin")
        exact_fields(result.get("workflow_run"), {
            "id": pin["run"],
            "head_branch": pin["branch"],
            "head_sha": pin["head"],
            "repository_id": REPOSITORY_ID,
            "head_repository_id": REPOSITORY_ID,
        }, "GitHub archive ownership does not match the reviewed pin")
        return download_endpoint

    def details(self, pin):
        workflow = self.api(f"/actions/workflows/{pin['workflow']}")
        exact_fields(workflow, {
            "id": pin["workflow"],
            "path": pin["path"],
            "state": pin["workflow_state"],
        }, "Original workflow definition or state differs from its observed pin")
        attempt = f"/actions/runs/{pin['run']}/attempts/1"
        run = self.api(attempt)
        exact_fields(run, {
            "id": pin["run"],
            "run_attempt": 1,
            "head_sha": pin["head"],
            "head_branch": pin["branch"],
            "path": pin["path"],
            "workflow_id": pin["workflow"],
            "status": "completed",
            "conclusion": pin["conclusion"],
        }, "GitHub run does not match the reviewed attempt")
        for key in ("repository", "head_repository"):
            exact_fields(run.get(key), {
                "id": REPOSITORY_ID,
                "full_name": REPOSITORY,
            }, "GitHub run repository does not match the reviewed owner")
        jobs = self.api(attempt + "/jobs?per_page=2")
        require(
            jobs.get("total_count") == 1 and len(jobs.get("jobs", ())) == 1,
            "Unexpected job count for the reviewed GitHub attempt",
        )
        exact_fields(jobs["jobs"][0], {
            "id": pin["job"],
            "name": pin["job_name"],
            "run_id": pin["run"],
            "run_attempt": 1,
            "head_sha": pin["head"],
            "head_branch": pin["branch"],
            "status": "completed",
            "conclusion": pin["job_conclusion"],
            "completed_at": pin["completed_at"],
        }, "GitHub job does not match the reviewed owner")

    def archive(self, pin):
        self.details(pin)
        endpoint = self.archive_metadata(pin)
        with self.open(endpoint, self.github_headers) as response:
            require(response.status == 302, "An exact GitHub artifact redirect was expected")
            location = response.headers.get_all("Location", [])
            require(len(location) == 1, "Expected one signed artifact destination")
            destination = signed_destination(location[0])
        with self.open(destination) as response:
            require(response.status == 200, "Signed artifact delivery failed")
            require(
                response.headers.get("Content-Encoding") in (None, "identity"),
                "Artifact delivery transformed the original bytes",
            )
            data = response.read(pin["bytes"] + 1)
        require(len(data) == pin["bytes"], "Issuer ZIP size does not match")
        require(
            hashlib.sha256(data).hexdigest() == pin["sha256"],
            "Issuer ZIP digest does not match",
        )
        self.archive_metadata(pin)
        return data


def main():
    token = os.environ["GITHUB_TOKEN"]
    require(bool(token), "GitHub Actions custody token missing")
    client = GitHubCustody(token)
    copies = [(pin, client.archive(pin)) for pin in PINS]
    output = Path(os.environ["RUNNER_TEMP"]) / OUTPUT
    output.mkdir(mode=0o700)
    entries = []
    for pin, data in copies:
        filename = f"issuer-{pin['artifact']}.zip"
        (output / filename).write_bytes(data)
        entries.append({**pin, "attempt": 1, "filename": filename})
        print(f"Verified original GitHub ZIP {pin['artifact']}: {pin['bytes']} bytes.")
    (output / "issuer-manifest.json").write_text(
        json.dumps({
            "schema": 1,
            "purpose": "evidence_custody_only",
            "repository": REPOSITORY,
            "repository_id": REPOSITORY_ID,
            "archives": entries,
            "publisher_requests": 0,
        }, indent=2) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    try:
        main()
    except CustodyError as error:
        sys.exit(str(error))
    except Exception:
        sys.exit("Artifact custody failed without transferring unverified evidence.")
