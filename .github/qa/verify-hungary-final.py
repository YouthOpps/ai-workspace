"""Read-only complete corpus/index verification for one immutable data pin."""
import argparse
import concurrent.futures
import hashlib
import html
import html.parser
import json
from pathlib import Path
import os
import pathlib
import re
import subprocess
import time
import urllib.error
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
def git_rev(path, ref):
    return subprocess.check_output(['git', '-C', str(path), 'rev-parse', ref], text=True).strip()

assert git_rev(root/'website', 'HEAD') == args.website_revision
assert git_rev(root/'website', 'HEAD:data-source') == git_rev(repository, 'HEAD') == args.pin
award_ids = {'23263163912fe5430b6f00a2', '30f5c843ffb40ae0da52cd6a',
             'bab4462a15963cb99b2d7a29', 'f4b2b67733189e4485d725e0'}
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


class OwnerRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, message, headers, target):
        new_url = urllib.parse.urljoin(request.full_url, target)
        parsed = urllib.parse.urlsplit(new_url)
        assert parsed.scheme == 'https' and parsed.netloc == 'youthopps.org', 'Foreign redirect from verification host'
        return super().redirect_request(request, fp, code, message, headers, new_url)


site_opener = urllib.request.build_opener(OwnerRedirect())


def fetch(path):
    url = urllib.parse.urljoin('https://youthopps.org', path)
    parsed = urllib.parse.urlsplit(url)
    assert parsed.scheme == 'https' and parsed.netloc == 'youthopps.org', 'Unexpected verification origin'
    cache_buster = urllib.parse.urlencode({'verification': args.pin, 'observed': time.time_ns()})
    separator = '&' if urllib.parse.urlsplit(url).query else '?'
    request = urllib.request.Request(url + separator + cache_buster, headers={
        'User-Agent': 'YouthOppsBot/1.0 (+https://youthopps.org/bot/)',
        'Cache-Control': 'no-cache'})
    with site_opener.open(request, timeout=30) as response:
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
    rel = path.strip('/')
    expected_index = Collection(
        (Path('website/dist') / rel / 'index.html').read_bytes()).indexes
    assert len(expected_index) == 1, path
    last = None
    for attempt in range(5):
        indexes = Collection(fetch(path)).indexes
        assert len(indexes) == 1, path
        index_url = urllib.parse.urljoin('https://youthopps.org' + path, indexes[0])
        assert urllib.parse.urlsplit(index_url).netloc == 'youthopps.org', index_url
        print(json.dumps({'collection': path, 'live_index': indexes[0],
                          'generated_index': expected_index[0]}), flush=True)
        try:
            return json.loads(fetch(index_url))
        except urllib.error.HTTPError as failure:
            last = failure
            print(json.dumps({'status': failure.code, 'url': index_url,
                              'cache_status': failure.headers.get('CF-Cache-Status'),
                              'age': failure.headers.get('Age')}), flush=True)
            if failure.code != 404 or attempt == 4:
                raise
            time.sleep(15)
    raise last


for attempt in range(15):
    report = json.loads(fetch('/build-report.json'))
    deployed_ids = {row['id'] for row in report['records']}
    if deployed_ids == expected:
        break
    print(json.dumps({'published_count': len(deployed_ids), 'expected_count': len(expected),
                      'unpublished': sorted(expected - deployed_ids)[:8],
                      'unexpected': sorted(deployed_ids - expected)[:8]}), flush=True)
    if attempt < 14:
        time.sleep(12)
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
canonical_details = {'https://youthopps.org/opportunity/' + slug + '/' for slug in route_ids.values()}
sitemap_details = [url for url in sitemap_locations
                   if urllib.parse.urlsplit(url).path.startswith('/opportunity/')]
assert len(sitemap_details) == len(canonical_details) and set(sitemap_details) == canonical_details

source_results = {}
samples = []
for source in args.sources:
    rows = [row for row in records if row['source'] == source]
    ids = {row['id'] for row in rows}
    assert ids == award_ids and source == "hu-fulbright-hungary", source
    index = collection('/sources/publisher/' + source + '/')
    searchable_ids = ids & browse
    assert len(index) == len(searchable_ids)
    assert {row['id'] for row in index} == searchable_ids
    assert {row['id'] for row in global_index if row['source'] == source} == searchable_ids
    assert searchable_ids == ids
    for row in rows:
        assert '/opportunity/' + route_ids[row['id']] + '/' in report['routes']
    selected = rows
    assert 'https://youthopps.org/sitemap-source-' + source + '.xml' in locations
    scoped_xml = ET.fromstring(fetch('/sitemap-source-' + source + '.xml'))
    scoped = [node.text for node in scoped_xml.iter() if node.tag.endswith('}loc')]
    expected_urls = {'https://youthopps.org/opportunity/' + route_ids[row['id']] + '/' for row in rows}
    assert len(scoped) == len(expected_urls) and set(scoped) == expected_urls
    samples.extend(selected)
    source_results[source] = {'records': len(ids), 'source_index_exact': True,
                              'global_index_exact': True,
                              'all_generated_routes_present': True,
                              'detail_HTTP_samples': len(selected), 'ids': sorted(ids)}


def check_detail(row):
    body = html.unescape(fetch('/opportunity/' + route_ids[row['id']] + '/').decode())
    assert row['url'] in body and row['title'] in body, row['id']


with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
    list(executor.map(check_detail, samples))

for source in args.sources:
    metadata = json.loads(subprocess.check_output([
        'git', '-C', repository, 'show', args.pin + ':datas/' + source + '/metadata.json']))
    assert metadata['status'] == 'success'
    for attempt in range(15):
        source_body = html.unescape(fetch('/sources/publisher/' + source + '/').decode())
        if metadata['last_success_at'] in source_body:
            source_results[source]['live_last_success_at'] = metadata['last_success_at']
            directory_routes = [route for route in report["routes"] if re.fullmatch(r"/sources/(?:page/[0-9]+/)?", route)]
            cards = []
            for route in directory_routes:
                body = fetch(route).decode()
                cards.extend(card for card in re.findall(r'<article class="source-card publisher-card">.*?</article>', body, re.S)
                             if '/sources/publisher/' + source + '/' in card)
            assert len(cards) == 1
            if ('<span class="source-status active">Success</span>' in cards[0]
                    and metadata['last_success_at'] in cards[0]):
                source_results[source]['sources_directory_card'] = 'Success'
                break
        if attempt < 14:
            time.sleep(12)
    else:
        raise RuntimeError('Source page did not reach the successful collection timestamp')

result = {'data_pin': args.pin, 'all_corpus_ids_equal': True,
          'website_revision': args.website_revision,
          'actual_build_slug_helper_blob': local_blob,
          'global_records': len(expected), 'browse_records': len(browse),
          'complete_sitemap_ids_equal': True, 'sources': source_results,
          'detail_HTTP_sample_titles_and_original_links_verified': True,
          'publisher_requests': 0, 'all_four_awards_visible_on_both_search_indexes_and_source_sitemap': True, 'responses': responses}
pathlib.Path(args.output).write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps({key: value for key, value in result.items()
                  if key != 'responses'}, indent=2))
