"""Check generated HTML structure, local URLs, and publication integrity."""
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit, unquote
import json
import re

ROOT = Path(__file__).resolve().parents[1]
VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}


class Page(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids, self.links, self.stack, self.errors = set(), [], [], []
        self.h1 = 0
        self.title = False
        self.viewport = False
        self.lang = False
        self.publications = 0

    def handle_starttag(self, tag, attrs):
        attr = dict(attrs)
        if tag not in VOID:
            self.stack.append(tag)
        if tag == "html":
            self.lang = attr.get("lang") == "en"
        if tag == "h1":
            self.h1 += 1
        if tag == "title":
            self.title = True
        if tag == "meta" and attr.get("name") == "viewport":
            self.viewport = True
        if "id" in attr:
            if attr["id"] in self.ids:
                self.errors.append(f"Duplicate id: {attr['id']}")
            self.ids.add(attr["id"])
        if "data-publication" in attr:
            self.publications += 1
        if tag == "img" and not attr.get("alt"):
            self.errors.append("Image lacks useful alt text")
        for key in ("href", "src"):
            if key in attr:
                self.links.append(attr[key])

    def handle_endtag(self, tag):
        if tag in VOID:
            return
        if not self.stack or self.stack[-1] != tag:
            self.errors.append(f"Mismatched closing tag: {tag} after {self.stack[-1] if self.stack else 'empty stack'}")
        elif self.stack:
            self.stack.pop()


def main():
    pages, errors = {}, []
    for filename in ROOT.glob("*.html"):
        page = Page()
        content = filename.read_text(encoding="utf-8")
        page.feed(content)
        if page.stack:
            page.errors.append(f"Unclosed tags: {page.stack}")
        if not (page.lang and page.title and page.viewport):
            page.errors.append("Missing language, title, or viewport")
        if filename.name != "index_old.html" and page.h1 != 1:
            page.errors.append(f"Expected one h1, got {page.h1}")
        if re.search(r"\{\{\w+\}\}", content):
            page.errors.append("Unfilled template")
        pages[filename.name] = page
        errors.extend(f"{filename.name}: {error}" for error in page.errors)
    for name, page in pages.items():
        for href in page.links:
            url = urlsplit(href)
            if url.scheme or url.netloc:
                continue
            target_name = unquote(url.path) or name
            target = ROOT / target_name
            if not target.exists():
                errors.append(f"{name}: Missing local target {href}")
            if url.fragment and target_name in pages and unquote(url.fragment) not in pages[target_name].ids:
                errors.append(f"{name}: Missing local anchor {href}")
    records = json.loads((ROOT / "content/publications.json").read_text(encoding="utf-8"))
    if pages["publications.html"].publications != len(records):
        errors.append("Publication page and JSON record counts differ")
    if errors:
        raise SystemExit("\n".join(errors))
    print(f"Passed: {len(pages)} HTML pages; local files and anchors; {len(records)} publication records.")


if __name__ == "__main__":
    main()
