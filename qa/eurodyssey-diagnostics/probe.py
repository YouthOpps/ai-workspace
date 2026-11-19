"""Inspect only the GitHub API routes used by the failed Eurodyssey preflight."""

import json
import os
from pathlib import Path
import re
import subprocess
import urllib.error
import urllib.parse
import urllib.request


WORKSPACE = 'YouthOpps/ai-workspace'
PIPELINE = 'YouthOpps/data-pipeline'
BRANCH = 'qa/eurodyssey-internships-control-diagnostics'
REF = 'refs/heads/' + BRANCH
WORKFLOW = '.github/workflows/qa-eurodyssey-internships-control-diagnostics.yml'
GITHUB_API = 'https://api.github.com/repos/'
ACTOR_ID = 12278069
PREDECESSOR_ID = 44494669298
PREDECESSOR_WORKFLOW = 423622763
FAILED_ID = 44507457363
FAILED_WORKFLOW = 423700844
ALLOWED_HEADERS = ('X-RateLimit-Remaining', 'X-RateLimit-Reset', 'Retry-After')


class RejectRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def github_routes(current):
    return (
        ('run', WORKSPACE, f'/actions/runs/{current}'),
        ('branch run inventory', WORKSPACE,
         f'/actions/runs?branch={urllib.parse.quote(BRANCH, safe="")}&event=push&per_page=2'),
        ('jobs', WORKSPACE, f'/actions/runs/{current}/attempts/1/jobs?per_page=10'),
        ('approval comments', PIPELINE, '/issues/460/comments?per_page=100&page=1'),
        ('retired workflow', WORKSPACE, f'/actions/workflows/{PREDECESSOR_WORKFLOW}'),
        ('retired run attempt', WORKSPACE, f'/actions/runs/{PREDECESSOR_ID}/attempts/1'),
        ('retired run inventory', WORKSPACE, f'/actions/workflows/{PREDECESSOR_WORKFLOW}/runs?per_page=2'),
        ('retired jobs', WORKSPACE, f'/actions/runs/{PREDECESSOR_ID}/attempts/1/jobs?per_page=10'),
        ('retired artifact inventory', WORKSPACE, f'/actions/runs/{PREDECESSOR_ID}/artifacts?per_page=2'),
        ('pipeline main', PIPELINE, '/branches/main'),
        ('workspace workflow inventory', WORKSPACE, '/actions/workflows?per_page=100&page=1'),
        ('pipeline workflow inventory page 1', PIPELINE, '/actions/workflows?per_page=100&page=1'),
        ('pipeline workflow inventory page 2', PIPELINE, '/actions/workflows?per_page=100&page=2'),
        ('failed workflow', WORKSPACE, f'/actions/workflows/{FAILED_WORKFLOW}'),
        ('failed run attempt', WORKSPACE, f'/actions/runs/{FAILED_ID}/attempts/1'),
        ('failed artifact inventory', WORKSPACE, f'/actions/runs/{FAILED_ID}/artifacts?per_page=2'),
    )


def verify_runner(env):
    workflow_ref = f'{WORKSPACE}/{WORKFLOW}@{REF}'
    expected = {
        'GITHUB_ACTIONS': 'true', 'GITHUB_REPOSITORY': WORKSPACE, 'GITHUB_REF': REF,
        'GITHUB_EVENT_NAME': 'push', 'GITHUB_RUN_ATTEMPT': '1', 'GITHUB_ACTOR_ID': str(ACTOR_ID),
        'GITHUB_WORKFLOW_REF': workflow_ref, 'GITHUB_JOB': 'diagnostics',
    }
    if any(env.get(key) != value for key, value in expected.items()) or 'DATA_SOURCE_TOKEN' in env:
        raise RuntimeError('Wrong GitHub diagnostic execution scope')
    run_id = env.get('GITHUB_RUN_ID', '')
    sha = env.get('GITHUB_SHA', '')
    if (not env.get('GITHUB_TOKEN') or not re.fullmatch(r'[1-9][0-9]*', run_id)
            or not re.fullmatch(r'[0-9a-f]{40}', sha) or env.get('GITHUB_WORKFLOW_SHA') != sha):
        raise RuntimeError('Wrong GitHub diagnostic identity')
    event = json.loads(Path(env['GITHUB_EVENT_PATH']).read_bytes())
    if (event.get('created') is not True or event.get('deleted') is not False
            or event.get('before') != '0' * 40 or event.get('after') != sha
            or event.get('ref') != REF or event.get('sender', {}).get('id') != ACTOR_ID
            or event.get('sender', {}).get('type') != 'User'
            or event.get('repository', {}).get('full_name') != WORKSPACE):
        raise RuntimeError('The reviewed one-shot branch creation is required')
    checked_out = subprocess.check_output(['git', 'rev-parse', 'HEAD'], timeout=10, text=True).strip()
    if checked_out != sha:
        raise RuntimeError('Diagnostic checkout differs')
    return run_id


def annotate(entry, status, headers):
    entry['status'] = status
    for name in ALLOWED_HEADERS:
        value = headers.get(name, '')
        if re.fullmatch(r'[0-9]{1,12}', value):
            entry[name.lower()] = int(value)


def diagnose(route, token, opener):
    label, repository, path = route
    headers = {'Accept': 'application/vnd.github+json', 'X-GitHub-Api-Version': '2022-11-28'}
    if repository == WORKSPACE:
        headers['Authorization'] = 'Bearer ' + token
    request = urllib.request.Request(GITHUB_API + repository + path, headers=headers, method='GET')
    entry = {'check': label, 'repository': repository, 'authenticated': repository == WORKSPACE}
    try:
        with opener.open(request, timeout=15) as response:
            annotate(entry, response.status, response.headers)
            if label == 'pipeline main' and response.status == 200:
                payload = response.read(64 * 1024)
                sha = json.loads(payload)['commit']['sha']
                if re.fullmatch(r'[0-9a-f]{40}', sha):
                    entry['ref_sha'] = sha
    except urllib.error.HTTPError as failure:
        try:
            annotate(entry, failure.code, failure.headers or {})
        finally:
            failure.close()
    except (urllib.error.URLError, TimeoutError, ValueError, KeyError, OSError) as failure:
        entry['error_type'] = type(failure).__name__
    return entry


def main():
    run_id = verify_runner(os.environ)
    opener = urllib.request.build_opener(RejectRedirect())
    checks = [diagnose(route, os.environ['GITHUB_TOKEN'], opener) for route in github_routes(run_id)]
    print(json.dumps({'checks': checks, 'publisher_requests': 0, 'historical_failure_run': FAILED_ID},
                     sort_keys=True), flush=True)


if __name__ == '__main__':
    main()
