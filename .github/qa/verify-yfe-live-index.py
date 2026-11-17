"""Read-only complete corpus/index verification for one immutable data pin."""
import argparse
import concurrent.futures
import hashlib
import html
import html.parser
import json
import os
import pathlib
import subprocess
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

parser = argparse.ArgumentParser()
parser.add_argument('pin')
parser.add_argument('sources', nargs='+')
parser.add_argument('--output', required=True)
parser.add_argument('--website-revision', required=True)
args = parser.parse_args()
root = pathlib.Path(os.environ['GITHUB_WORKSPACE'])
repository = str(root / 'data-source')
subprocess.run(['git', '-C', repository, 'fetch', '--no-recurse-submodules',
                'origin', 'main'], check=True, stdout=subprocess.DEVNULL)
paths = subprocess.check_output(['git', '-C', repository, 'ls-tree', '-r',
                                 '--name-only', args.pin, 'datas'], text=True).splitlines()
records = []
for path in paths:
    if path.endswith('/data.json'):
        records.extend(json.loads(subprocess.check_output(
            ['git', '-C', repository, 'show', args.pin + ':' + path])))
expected = {row['id'] for row in records}
assert len(expected) == len(records)
browse = {row['id'] for row in records if row.get('kind') != 'unknown'}
build_path = str(root / 'website/scripts/build.mjs')
remote_build = json.loads(subprocess.check_output([
    'gh', 'api', 'repos/YouthOpps/youthopps.github.io/contents/scripts/build.mjs?ref='
    + args.website_revision]))
local_blob = subprocess.check_output(['git', 'hash-object', build_path],
                                     text=True).strip()
assert local_blob == remote_build['sha']
route_ids = json.loads(subprocess.check_output([
    'node', '--input-type=module', '-e',
    "import {slug} from 'file://" + build_path + "';"
    "let text='';for await(const chunk of process.stdin)text+=chunk;"
    "console.log(JSON.stringify(Object.fromEntries(JSON.parse(text).map("
    "id=>[id,slug(id)]))));"], input=json.dumps(sorted(expected)).encode()))
assert len(set(route_ids.values())) == len(expected)
responses = []


def fetch(path):
    url = urllib.parse.urljoin('https://youthopps.org', path)
    cache_buster = urllib.parse.urlencode({'verification': args.pin, 'observed': time.time_ns()})
    separator = '&' if urllib.parse.urlsplit(url).query else '?'
    request = urllib.request.Request(url + separator + cache_buster, headers={
        'User-Agent': 'YouthOppsBot/1.0 (+https://youthopps.org/bot/)',
        'Cache-Control': 'no-cache'})
    with urllib.request.urlopen(request, timeout=30) as response:
        raw = response.read()
        assert response.status == 200
        responses.append({'url': url, 'status': response.status,
                          'bytes': len(raw),
                          'sha256': hashlib.sha256(raw).hexdigest()})
        return raw


class Collection(html.parser.HTMLParser):
    def __init__(self, raw):
        super().__init__()
        self.indexes = []
        self.feed(raw.decode())

    def handle_starttag(self, tag, attributes):
        values = dict(attributes)
        if ('collection' in values.get('class', '').split()
                and values.get('data-index')):
            self.indexes.append(values['data-index'])


def collection(path):
    indexes = Collection(fetch(path)).indexes
    assert len(indexes) == 1, path
    return json.loads(fetch(indexes[0]))


for attempt in range(6):
    report = json.loads(fetch('/build-report.json'))
    deployed_ids = {row['id'] for row in report['records']}
    if deployed_ids == expected:
        break
    print(json.dumps({'published_count': len(deployed_ids), 'expected_count': len(expected),
                      'unpublished': sorted(expected - deployed_ids)[:8],
                      'unexpected': sorted(deployed_ids - expected)[:8]}), flush=True)
    if attempt < 5:
        time.sleep(10)
else:
    raise RuntimeError('Published build report did not reach the immutable data pin')
global_index = collection('/opportunities/')
assert len(global_index) == len(browse)
assert {row['id'] for row in global_index} == browse

sitemap = ET.fromstring(fetch('/sitemap.xml'))
locations = [node.text for node in sitemap.iter() if node.tag.endswith('}loc')]
if sitemap.tag.endswith('}sitemapindex'):
    sitemap_locations = []
    for location in locations:
        sitemap_locations.extend(node.text for node in ET.fromstring(
            fetch(location)).iter() if node.tag.endswith('}loc'))
else:
    sitemap_locations = locations
sitemap_ids = {urllib.parse.urlsplit(url).path.split('/')[2]
               for url in sitemap_locations
               if urllib.parse.urlsplit(url).path.startswith('/opportunity/')}
assert sitemap_ids == set(route_ids.values())

source_results = {}
samples = []
for source in args.sources:
    rows = [row for row in records if row['source'] == source]
    ids = {row['id'] for row in rows}
    assert ids, source
    index = collection('/sources/publisher/' + source + '/')
    assert len(index) == len(ids)
    assert {row['id'] for row in index} == ids
    assert {row['id'] for row in global_index if row['source'] == source} == ids
    for row in rows:
        assert '/opportunity/' + route_ids[row['id']] + '/' in report['routes']
    positions = sorted({0, len(rows) // 2, len(rows) - 1})
    selected = rows if len(rows) <= 30 else [rows[position] for position in positions]
    samples.extend(selected)
    source_results[source] = {'records': len(ids), 'source_index_exact': True,
                              'global_index_exact': True,
                              'all_generated_routes_present': True,
                              'detail_HTTP_samples': len(selected)}


def check_detail(row):
    body = html.unescape(fetch('/opportunity/' + route_ids[row['id']] + '/').decode())
    assert row['url'] in body and row['title'] in body, row['id']


with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
    list(executor.map(check_detail, samples))

yfe_meta = json.loads(subprocess.check_output([
    'git', '-C', repository, 'show', args.pin + ':datas/youth-for-europe/metadata.json']))
assert yfe_meta['status'] == 'success'
last_collection = yfe_meta['last_success_at']
for attempt in range(6):
    source_body = html.unescape(fetch('/sources/publisher/youth-for-europe/').decode())
    if last_collection in source_body:
        break
    if attempt < 5:
        time.sleep(10)
else:
    raise RuntimeError('Youth for Europe source page has not reached the exact collection timestamp')
result = {'data_pin': args.pin, 'all_corpus_ids_equal': True,
          'website_revision': args.website_revision,
          'actual_build_slug_helper_blob': local_blob,
          'global_records': len(expected), 'browse_records': len(browse),
          'complete_sitemap_ids_equal': True, 'sources': source_results,
          'detail_HTTP_sample_titles_and_original_links_verified': True,
          'publisher_requests': 0, 'yfe_live_last_success_at': last_collection, 'responses': responses}
pathlib.Path(args.output).write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps({key: value for key, value in result.items()
                  if key != 'responses'}, indent=2))
