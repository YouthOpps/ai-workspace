"""Reconcile current public source cards and source indexes with a pinned build."""
import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from html.parser import HTMLParser
import json
from pathlib import Path
import time
from urllib.error import HTTPError
from urllib.parse import urlencode, urlsplit
from urllib.request import Request, urlopen
from xml.etree import ElementTree


class IndexLink(HTMLParser):
    def __init__(self, page):
        super().__init__()
        self.links = []
        self.feed(page.decode('utf-8'))

    def handle_starttag(self, tag, attributes):
        attributes = dict(attributes)
        if 'collection' in attributes.get('class', '').split() and attributes.get('data-index'):
            self.links.append(attributes['data-index'])


def one_index(page):
    links = IndexLink(page).links
    assert len(links) == 1, links
    assert links[0].startswith('/assets/') and urlsplit(links[0]).netloc == '', links
    return links[0]


def read_local(path):
    relative = path.lstrip('/')
    if path.endswith('/'):
        relative += 'index.html'
    return (Path('website/dist') / relative).read_bytes()


def read_live(path):
    assert path.startswith('/') and urlsplit(path).netloc == '', path
    query = urlencode({'verification': args.pin, 'observed': time.time_ns()})
    request = Request('https://youthopps.org' + path + '?' + query, headers={
        'Cache-Control': 'no-cache',
        'User-Agent': 'YouthOppsBot/1.0 (+https://youthopps.org/bot/)',
    })
    for delay in (0, 5, 10, 15):
        time.sleep(delay)
        try:
            with urlopen(request, timeout=25) as response:
                assert response.status == 200
                assert urlsplit(response.url).hostname == 'youthopps.org'
                return response.read()
        except HTTPError as error:
            if error.code != 404 or delay == 15:
                raise


def locations(document):
    parsed = ElementTree.fromstring(document)
    return Counter(node.text for node in parsed.iter() if node.tag.endswith('}loc'))


def source_cards(index):
    cards = {}
    for row in index:
        data = json.loads(row['search'])
        assert data['status'] == row['status']
        assert f'/sources/publisher/{data["id"]}/' in row['html'], data['id']
        assert data['id'] not in cards, data['id']
        cards[data['id']] = {key: data.get(key) for key in (
            'status', 'last_success_at', 'last_attempt_at', 'last_checked_at')}
        if row['status'] == 'fail':
            assert '>Fail</span>' in row['html'], data['id']
    return cards


def collection(path):
    return (
        json.loads(read_local(one_index(read_local(path)))),
        json.loads(read_live(one_index(read_live(path)))),
    )


def check_source_page(source):
    path = f'/sources/publisher/{source}/'
    expected, actual = collection(path)
    assert Counter(row['id'] for row in actual) == Counter(row['id'] for row in expected), source
    return len(actual)


def check_sitemap(url):
    assert urlsplit(url).hostname == 'youthopps.org', url
    path = urlsplit(url).path
    expected = locations(read_local(path))
    assert locations(read_live(path)) == expected, path
    return len(expected)


parser = argparse.ArgumentParser()
parser.add_argument('pin')
parser.add_argument('--website-revision', required=True)
parser.add_argument('--output', required=True)
args = parser.parse_args()

local_directory, live_directory = collection('/sources/')
cards = source_cards(live_directory)
assert cards == source_cards(local_directory)
all_routes = set(json.loads(read_local('/build-report.json'))['routes'])
source_pages = sorted(source for source in cards if f'/sources/publisher/{source}/' in all_routes)
sitemaps = locations(read_local('/sitemap.xml'))
assert locations(read_live('/sitemap.xml')) == sitemaps
assert all(count == 1 for count in sitemaps.values())

with ThreadPoolExecutor(max_workers=4) as pool:
    source_counts = dict(zip(source_pages, pool.map(check_source_page, source_pages), strict=True))
    sitemap_counts = dict(zip(sitemaps, pool.map(check_sitemap, sitemaps), strict=True))

report = {
    'website_revision': args.website_revision,
    'data_pin': args.pin,
    'public_directory_sources': len(cards),
    'public_source_search_indexes': len(source_counts),
    'public_source_sitemaps': sum('/sitemap-source-' in url for url in sitemap_counts),
    'source_status_counts': dict(Counter(data['status'] for data in cards.values())),
    'public_fail_sources': {source: {**data, 'visible_records': source_counts.get(source)}
                            for source, data in cards.items() if data['status'] == 'fail'},
    'all_source_index_records': sum(source_counts.values()),
    'all_sitemap_records': sum(count for url, count in sitemap_counts.items()
                               if '/sitemap-source-' in url),
}
payload = json.dumps(report, ensure_ascii=False, indent=2) + '\n'
Path(args.output).write_text(payload)
print(payload)
