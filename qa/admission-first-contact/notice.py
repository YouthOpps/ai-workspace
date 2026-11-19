"""Use the departmental notice in memory and export a bounded policy receipt."""

from email.message import Message
from hashlib import sha256
from html.parser import HTMLParser
import re

URL = "https://inf.ethz.ch/footer/disclaimer-copyright.html"


class MainNotice(HTMLParser):
    def __init__(self):
        super().__init__()
        self.stack = []
        self.titles = []
        self.paragraphs = []

    def handle_starttag(self, tag, attributes):
        attrs = dict(attributes)
        _, main, hidden, block = self.stack[-1] if self.stack else (None, False, False, None)
        main = main or tag == "main" or attrs.get("id") == "contentMain"
        hidden = (hidden or tag in {"script", "style", "template", "nav", "footer", "aside"}
                  or "hidden" in attrs or attrs.get("aria-hidden") == "true")
        if tag in {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta",
                   "param", "source", "track", "wbr"}:
            return
        if main and not hidden and tag in {"h1", "p", "li"}:
            block = []
            (self.titles if tag == "h1" else self.paragraphs).append(block)
        self.stack.append((tag, main, hidden, block))

    def handle_endtag(self, tag):
        for index in reversed(range(len(self.stack))):
            if self.stack[index][0] == tag:
                del self.stack[index:]
                break

    def handle_data(self, text):
        if self.stack:
            _, _, hidden, parts = self.stack[-1]
            if parts is not None and not hidden:
                parts.append(text)


def notice_facts(row):
    if row["url"] != URL or row["status"] != 200:
        raise ValueError("The exact departmental copyright notice is required")
    headers = Message()
    for key, value in row["headers"]:
        headers[key] = value
    if headers.get_content_type() not in {"text/html", "application/xhtml+xml"}:
        raise ValueError("Unexpected departmental notice content type")
    body = b"".join(row["segments"])
    parser = MainNotice()
    parser.feed(body.decode(headers.get_content_charset() or "utf-8", errors="strict"))
    parser.close()
    headings = [" ".join("".join(part).split()) for part in parser.titles]
    paragraphs = [" ".join("".join(part).split()) for part in parser.paragraphs]
    if not any(re.search(r"copyright|urheberrecht|disclaimer", title, re.I) for title in headings):
        raise ValueError("Departmental copyright heading is missing")
    groups = {
        "automated_access": r"scrap(?:e|ing)|crawler|automat(?:ed|ic)s+(?:access|retrieval)|automatisiert",
        "copy_storage": r"(?:stor(?:e|ed|age)|speicher(?:n|ung)).*(?:servers?|server)|cop(?:y|ies|ying)|kopi",
        "citation_or_linking": r"cit(?:e|ation|ing)|link(?:age|ing|s)|zitat|zitier|verlink",
        "consent": r"consent|permission|genehmigung|zustimmung",
    }
    assessment = {}
    for subject, pattern in groups.items():
        snippets = []
        for paragraph in paragraphs:
            match = re.search(pattern, paragraph, re.I)
            if match:
                words = paragraph[:match.start()].split()
                start = max(0, len(words) - 5)
                snippet = " ".join(paragraph.split()[start:start + 12])
                if snippet and snippet not in snippets:
                    snippets.append(snippet)
        assessment[subject] = {"matches": len(snippets), "example": snippets[0] if snippets else None}
    return {"url": URL, "response_sha256": sha256(body).hexdigest(),
            "response_bytes": len(body), "copyright_heading": True, "signals": assessment}
