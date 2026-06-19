#!/usr/bin/env python3
"""Generate the GitHub profile README from the site itself.

Top section: the home page intro (content/_index.md, shortcodes stripped).
Then: the latest 5 posts pulled from the built blog RSS feed.
No static content lives here; everything comes from the site.
"""
import os
import re
import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime

ROOT = os.environ.get("GITHUB_WORKSPACE", ".")


def read(path):
    try:
        with open(os.path.join(ROOT, path), encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return ""


# Site base URL (so relative links and RSS resolve absolutely).
cfg = read("hugo.toml")
m = re.search(r"baseURL\s*=\s*['\"]([^'\"]+)['\"]", cfg)
base = (m.group(1) if m else "https://mhd64.dev/").rstrip("/")

# 1. Intro: the home page content, minus front matter and Hugo shortcodes.
raw = read("content/_index.md")
raw = re.sub(r"^---.*?\n---\s*", "", raw, count=1, flags=re.DOTALL)
raw = re.sub(r"\{\{[<%]\s*(\w+).*?[%>]\}\}.*?\{\{[<%]\s*/\s*\1\s*[%>]\}\}", "", raw, flags=re.DOTALL)
raw = re.sub(r"\{\{[<%].*?[%>]\}\}", "", raw)
raw = re.sub(r"\]\(/", "](" + base + "/", raw)  # relative -> absolute links
intro = raw.strip()

# 2. Latest 5 posts from the blog RSS feed.
posts = []
rss = read("public/blog/index.xml")
if rss:
    try:
        root = ET.fromstring(rss)
        for item in root.findall(".//item")[:5]:
            title = (item.findtext("title") or "").strip()
            link = (item.findtext("link") or "").strip()
            pub = (item.findtext("pubDate") or "").strip()
            date = ""
            if pub:
                try:
                    date = parsedate_to_datetime(pub).strftime("%d/%m/%Y")
                except (TypeError, ValueError):
                    date = ""
            if title and link:
                posts.append((title, link, date))
    except ET.ParseError:
        pass

# 3. Assemble.
lines = []
if intro:
    lines.append(intro)
lines.append("\n---\n")
lines.append("### Latest posts\n")
if posts:
    for title, link, date in posts:
        suffix = f" <sub>({date})</sub>" if date else ""
        lines.append(f"- [{title}]({link}){suffix}")
else:
    lines.append("Nothing published yet, but the ink is drying. Check back soon.")
lines.append("\n---\n")
host = base.split("//")[-1]
lines.append(f'<sub><a href="{base}/">{host}</a> &middot; this page updates automatically on every push.</sub>')

readme = "\n".join(lines).strip() + "\n"
with open(os.path.join(ROOT, "README.md"), "w", encoding="utf-8") as f:
    f.write(readme)
print(readme)
