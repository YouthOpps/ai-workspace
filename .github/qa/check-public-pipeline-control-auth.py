"""Check whether the job credential can read public pipeline control data."""
import json
from os import environ
from urllib.error import HTTPError
from urllib.request import HTTPRedirectHandler, Request, build_opener


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


paths = {
    'current_pipeline_main': ('/git/ref/heads/main', lambda row: row['ref'] == 'refs/heads/main'),
    'loreal_authorization_inventory': ('/issues/468/comments?per_page=100&page=1',
                                       lambda rows: any(row['id'] == 7019583466 for row in rows)),
    'esc_authorization_inventory': ('/issues/455/comments?per_page=100&page=1', lambda rows: bool(rows)),
}
client = build_opener(NoRedirect())
success = True
for label, (path, validate) in paths.items():
    request = Request('https://api.github.com/repos/YouthOpps/data-pipeline' + path, headers={
        'Accept': 'application/vnd.github+json',
        'Authorization': 'Bearer ' + environ['GH_TOKEN'],
        'X-GitHub-Api-Version': '2022-11-28',
    })
    try:
        with client.open(request, timeout=20) as response:
            raw = response.read(2_000_001)
            matched = len(raw) <= 2_000_000 and validate(json.loads(raw))
            metadata = {'status': response.status, 'match': matched,
                        'rate_limit': response.headers.get('X-RateLimit-Limit'),
                        'remaining': response.headers.get('X-RateLimit-Remaining')}
            success = success and matched
    except HTTPError as error:
        metadata = {'status': error.code, 'match': False,
                    'rate_limit': error.headers.get('X-RateLimit-Limit'),
                    'remaining': error.headers.get('X-RateLimit-Remaining')}
        success = False
    print(json.dumps({'control': label, **metadata}), flush=True)
raise SystemExit(0 if success else 1)
