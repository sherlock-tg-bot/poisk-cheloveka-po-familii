#!/usr/bin/env python3
"""Offline content checks for this repository."""
from html.parser import HTMLParser
from pathlib import Path
import json
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
META = json.loads((ROOT / "metadata.json").read_text(encoding="utf-8"))
KEYWORD = META["keyword"]
CTA = META["target_url"]
CTA_TEXT = re.compile(r"открыть в telegram", re.I)
PROHIBITED = re.compile(r"https?://(?:www\.)?(?:sherlockbot\.is|glazboga\.is|t\.me|telegram\.me)(?:/|$)", re.I)

errors = []
def require(condition, message):
    if not condition:
        errors.append(message)

for name in ("README.md", "FAQ.md", "SECURITY.md", "index.html", "metadata.json", "scripts/validate.py", ".github/workflows/validate.yml"):
    require((ROOT / name).is_file(), f"missing required file: {name}")

readme = (ROOT / "README.md").read_text(encoding="utf-8")
faq = (ROOT / "FAQ.md").read_text(encoding="utf-8")
html = (ROOT / "index.html").read_text(encoding="utf-8")
require(KEYWORD.lower() in readme.lower(), "keyword is missing from README")
require(re.search(r"^# .*" + re.escape(KEYWORD), readme, re.I | re.M), "README H1 does not contain the exact keyword")
require(readme[:1800].find(CTA) >= 0, "CTA is missing near the beginning of README")
require(CTA in readme[readme.lower().rfind("## ответственное использование"):], "CTA is missing from README final block")
require(len(re.findall(r"^## .+\?$", faq, re.M)) == 6, "FAQ must contain 6 question headings")
require(not PROHIBITED.search(readme + faq + (ROOT / "SECURITY.md").read_text(encoding="utf-8") + html), "prohibited direct CTA domain found")
require("img.shields.io" not in readme, "external badge found in README")
require("Content validation" in (ROOT / ".github/workflows/validate.yml").read_text(encoding="utf-8"), "workflow name is incorrect")
require("python3 scripts/validate.py" in (ROOT / ".github/workflows/validate.yml").read_text(encoding="utf-8"), "workflow does not run validator")

class PageParser(HTMLParser):
    def __init__(self):
        super().__init__(); self.h1 = []; self.title = []; self.links = []; self.canonical = []
    def handle_starttag(self, tag, attrs):
        data = dict(attrs)
        if tag == "a": self.links.append((data.get("href", ""), ""))
        if tag == "link" and data.get("rel", "").lower() == "canonical": self.canonical.append(data.get("href", ""))
    def handle_endtag(self, tag): pass
    def handle_data(self, data):
        if self.h1 is not None: self.h1.append(data) if False else None

parser = PageParser(); parser.feed(html)
require(html.lower().count("<h1") == 1, "index.html must contain exactly one H1")
require(KEYWORD.lower() in html.lower(), "keyword is missing from index.html")
require(CTA in html.replace("&amp;", "&"), "CTA is missing from index.html")
require(not parser.canonical or all(url != CTA for url in parser.canonical), "canonical must not point to CTA")
require("<meta name=\"description\"" in html.lower(), "meta description is missing")
require("width=device-width" in html, "viewport is missing")

if errors:
    print("Validation failed:")
    print("\n".join(f"- {error}" for error in errors))
    sys.exit(1)
print("Validation passed: required files, keyword, CTA, FAQ, workflow and HTML checks are OK.")
