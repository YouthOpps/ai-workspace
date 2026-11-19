"""Extract only attributed facts from the scoped ENS French admissions page."""

from datetime import datetime
from email.message import Message
from hashlib import sha256
from html.parser import HTMLParser
import re
from unicodedata import normalize
from zoneinfo import ZoneInfo

URL = ('https://www.ens.psl.eu/une-formation-d-exception/admission-concours/'
       'international/concours-selection-internationale')
TRACKS = {'lettres': 'arts-humanities', 'sciences': 'sciences'}
MONTHS = dict(zip(('janvier', 'février', 'mars', 'avril', 'mai', 'juin', 'juillet',
                  'août', 'septembre', 'octobre', 'novembre', 'décembre'), range(1, 13)))
LOCAL_DATE = re.compile(
    r'\b(\d{1,2}) (' + '|'.join(MONTHS) + r') (\d{4})\s*\(\s*'
    r'(\d{1,2})\s*(?:heures?|h)\s*(\d{2})?\s*,?\s*(?:heure\s*|h\.?\s*)?de Paris\s*\)',
    re.IGNORECASE,
)
NO_INDEX = re.compile(r'\b(?:noindex|none)\b', flags=re.IGNORECASE)


class AdmissionPage(HTMLParser):
    """Read the headings, application bullets and table rows of visible main content."""

    def __init__(self):
        super().__init__()
        self.stack = []
        self.blocks = []
        self.rows = []
        self.table = 0
        self.noindex = False

    def handle_starttag(self, tag, attributes):
        attrs = {k: v or '' for k, v in attributes}
        if tag == 'meta' and attrs.get('name', '').lower() in {'robots', 'youthoppsbot'}:
            self.noindex = self.noindex or bool(NO_INDEX.search(attrs.get('content', '')))
        _, main, hidden, block = self.stack[-1] if self.stack else (None, False, False, None)
        main = main or tag == 'main' or attrs.get('role') == 'main'
        hidden = (hidden or tag in {'script', 'style', 'template', 'nav', 'footer', 'aside'}
                  or 'hidden' in attrs or attrs.get('aria-hidden') == 'true'
                  or bool(re.search(r'(?:display\s*:\s*none|visibility\s*:\s*hidden)', attrs.get('style', ''), re.I)))
        if tag in {'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input', 'link', 'meta',
                   'param', 'source', 'track', 'wbr'}:
            return
        if main and not hidden:
            if tag == 'table':
                self.table += 1
            if tag == 'tr':
                block = []
                self.rows.append((self.table, block))
            elif tag in {'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'li'} and not any(
                    row[0] == 'tr' for row in self.stack):
                block = []
                self.blocks.append((tag, block))
        self.stack.append((tag, main, hidden, block))

    def handle_endtag(self, tag):
        for index in reversed(range(len(self.stack))):
            if self.stack[index][0] == tag:
                del self.stack[index:]
                break

    def handle_data(self, text):
        if self.stack:
            _, _, hidden, block = self.stack[-1]
            if not hidden and block is not None:
                block.append(text)


def text(parts):
    return normalize('NFC', ' '.join(''.join(parts).split()))


def time_window(value):
    return tuple(datetime(int(year), MONTHS[month.casefold()], int(day), int(hour),
                          int(minute or 0), tzinfo=ZoneInfo('Europe/Paris'))
                 for day, month, year, hour, minute in LOCAL_DATE.findall(value))


def notice_facts(row):
    if row['url'] != URL or row['status'] != 200:
        raise ValueError('The exact French ENS selection page is required')
    headers = Message()
    for key, value in row['headers']:
        headers[key] = value
    if (headers.get_content_type() not in {'text/html', 'application/xhtml+xml'}
            or any(NO_INDEX.search(header) for header in headers.get_all('X-Robots-Tag', []))):
        raise ValueError('ENS selection response cannot support an index assessment')
    body = b''.join(row['segments'])
    parser = AdmissionPage()
    parser.feed(body.decode(headers.get_content_charset() or 'utf-8', errors='strict'))
    parser.close()
    if parser.noindex or not any(tag == 'h1' and re.search(r'sélection internationale', text(parts), re.I)
                                 for tag, parts in parser.blocks):
        raise ValueError('Missing indexable ENS selection heading')
    track = None
    summary = {}
    for tag, parts in parser.blocks:
        value = text(parts)
        if tag.startswith('h'):
            label = re.search(r'sélection internationale\s+(Lettres|Sciences)\s+2027\b', value, re.I)
            track = TRACKS[label[1].casefold()] if label else None
        elif track and re.match(r'Candidatures\s*:', value, re.I):
            if track in summary:
                raise ValueError('Duplicate ENS round summary')
            summary[track] = time_window(value)
    if (set(summary) != set(TRACKS.values())
            or any(len(window) != 2 or window[0] >= window[1]
                   or any(d.year != 2026 for d in window) for window in summary.values())
            or len(set(summary.values())) != 1):
        raise ValueError('ENS French track windows are ambiguous')
    tables = {}
    for table, parts in parser.rows:
        value = text(parts)
        if re.search(r'candidatur', value, re.I):
            window = time_window(value)
            if window:
                if len(window) != 2 or table in tables:
                    raise ValueError('Ambiguous dated ENS application row')
                tables[table] = window
    if len(tables) != 2 or set(tables.values()) != set(summary.values()):
        raise ValueError('French ENS summaries and detailed application calendars disagree')
    return {'url': URL, 'response_bytes': len(body), 'response_sha256': sha256(body).hexdigest(),
            'round_year': 2027, 'timezone': 'Europe/Paris', 'agreement': 'two_french_summaries_and_tables',
            'tracks': [{'track': key, 'apply_from': start.isoformat(), 'apply_until': end.isoformat()}
                       for key, (start, end) in sorted(summary.items())]}
