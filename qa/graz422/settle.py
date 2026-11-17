"""Derive a continuation from the authenticated, already closed TU Graz response."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import urllib.request


ROOT = Path(__file__).resolve().parent
REPOSITORY = 'YouthOpps/ai-workspace'
BRANCH = 'qa/422-graz-received-response-settlement'
WORKFLOW = '.github/workflows/qa-graz-received-response-settlement.yml'
REVIEWER_SHA256 = 'c8bfa742ffcd2638a1926c8068b58c3f0cc9bcda7077b95ab3ac8a8ac5b01531'
REVIEW_SHA256 = 'd80369bcab07bb22fa3d7f221bea58295a069f63f0c73b5e7e49471ea0f907ef'


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, message, headers, url):
        return None


def github(path):
    request = urllib.request.Request('https://api.github.com/repos/' + REPOSITORY + path, headers={
        'Authorization': 'Bearer ' + os.environ['GITHUB_TOKEN'],
        'Accept': 'application/vnd.github+json',
        'X-GitHub-Api-Version': '2022-11-28',
    })
    with urllib.request.build_opener(NoRedirect()).open(request, timeout=20) as response:
        raw = response.read(2_000_001)
    require(len(raw) <= 2_000_000, 'Excessive GitHub response')
    return json.loads(raw)


def settlement(original, proof):
    robots, entry = proof['responses']
    prior = original['policy']
    require(original['in_flight'] and original['physical_pending'] and not original['blocked'],
            'Expected exactly one unresolved admitted response')
    require(original['target'] == entry['url'] and original['physical_id'] == entry['physical_id']
            and original['physical_started'] == original['starts'][-1]
            and original['starts'] == proof['original_reservations'], 'Original physical identity differs')
    require(prior['url'] == robots['url'] and prior['body_sha256'] == robots['sha256']
            and prior['new_allowed'] and prior['legacy_allowed'], 'Original robots evidence differs')
    require(all(row['closed'] and row['complete_eof'] and row['status'] == 200
                for row in (robots, entry)), 'Both already-received responses must be complete')
    require(entry['wall_start'] - robots['wall_completion'] >= original['interval'],
            'Actual physical gap is shorter than preserved floor')
    require([robots['wall_start'], entry['wall_start']] == proof['known_physical_start_observations'],
            'Actual physical starts changed')
    closed = entry['wall_completion']
    require(closed >= max(original['observed_at'], entry['wall_start']), 'Closure precedes observation')
    return dict(original, completed=closed, inventory_completed=closed, observed_at=closed,
                not_before=max(original['not_before'], closed + original['interval']),
                completed_logical_id=original['logical_id'], completed_physical_id=original['physical_id'],
                in_flight=False, physical_pending=False, outcome='response_assessed')


def main():
    env = os.environ
    event = json.loads(Path(env['GITHUB_EVENT_PATH']).read_bytes())
    require(env['GITHUB_REPOSITORY'] == REPOSITORY and env['GITHUB_RUN_ATTEMPT'] == '1'
            and env['GITHUB_REF'] == 'refs/heads/' + BRANCH and env['GITHUB_EVENT_NAME'] == 'push'
            and env['GITHUB_WORKFLOW_REF'] == REPOSITORY + '/' + WORKFLOW + '@' + env['GITHUB_REF']
            and event['created'] is True and event['deleted'] is False and event['before'] == '0' * 40
            and event['after'] == env['GITHUB_SHA'] and 'DATA_SOURCE_TOKEN' not in env,
            'Wrong one-use settlement scope')
    run_id = int(env['GITHUB_RUN_ID'])
    active = github(f'/actions/runs/{run_id}')
    require(active['id'] == run_id and active['head_sha'] == env['GITHUB_SHA']
            and active['run_attempt'] == 1 and active['head_branch'] == BRANCH
            and active['event'] == 'push' and active['path'] == WORKFLOW, 'Settlement run owner differs')
    reviewed = ROOT / 'reviewed-settlement.json'
    reviewer = ROOT / 'reviewer.pem'
    require(digest(reviewed.read_bytes()) == REVIEW_SHA256 and digest(reviewer.read_bytes()) == REVIEWER_SHA256,
            'Frozen review inputs differ')
    verified = subprocess.check_output([
        'openssl', 'cms', '-verify', '-binary', '-inform', 'DER', '-nointern', '-noverify',
        '-certfile', str(reviewer), '-content', str(reviewed), '-in', str(ROOT / 'reviewer-signature.cms'),
    ])
    require(verified == reviewed.read_bytes(), 'Reviewer signature output differs')
    bundle = json.loads(verified)
    original, proof = bundle['original_state'], bundle['proof']
    owner = proof['scope']
    run = github(f"/actions/runs/{owner['run_id']}")
    workflow = github(f"/actions/workflows/{owner['workflow_id']}")
    require(owner['repository'] == REPOSITORY and owner['source'] == 'graz422'
            and run['head_sha'] == owner['head_sha'] and run['status'] == 'completed'
            and run['conclusion'] == 'failure' and run['path'] == owner['workflow']
            and run['run_attempt'] == owner['run_attempt'] and run['workflow_id'] == owner['workflow_id']
            and 'refs/heads/' + run['head_branch'] == owner['ref']
            and workflow['state'] == 'disabled_manually', 'Original run or retirement changed')
    jobs = github(f"/actions/runs/{owner['run_id']}/attempts/1/jobs")['jobs']
    match = [row for row in jobs if row['id'] == owner['job_id']]
    require(len(match) == 1 and match[0]['conclusion'] == 'failure'
            and match[0]['name'] == 'First contact graz422', 'Original job identity differs')
    artifact = github(f"/actions/artifacts/{bundle['owned_artifact_id']}")
    require(artifact['workflow_run']['id'] == owner['run_id']
            and artifact['workflow_run']['head_sha'] == owner['head_sha']
            and artifact['digest'] == 'sha256:' + proof['retained_archive_sha256']
            and not artifact['expired'], 'Original archive ownership differs')
    require(digest(canonical(original)) == proof['original_state_sha256'], 'Original state differs')
    successor = settlement(original, proof)
    successor_bytes = canonical(successor)
    require(successor == bundle['proposed_state']
            and digest(successor_bytes) == proof['settlement']['proposed_state_sha256'],
            'Derived continuation differs from reviewed bytes')
    out = Path(env['RUNNER_TEMP']) / 'graz-received-response-settlement'
    out.mkdir(mode=0o700)
    result = {'repository': REPOSITORY, 'run_id': run_id, 'head_sha': env['GITHUB_SHA'],
              'previous_owner': owner, 'previous_archive_id': bundle['owned_artifact_id'],
              'previous_archive_sha256': proof['retained_archive_sha256'],
              'previous_pending_state_sha256': proof['original_state_sha256'],
              'review_sha256': REVIEW_SHA256, 'state_sha256': digest(successor_bytes),
              'known_physical_start_observations': proof['known_physical_start_observations'],
              'publisher_requests': 0}
    (out / 'state.json').write_bytes(successor_bytes)
    (out / 'provenance.json').write_bytes(canonical(result))
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
