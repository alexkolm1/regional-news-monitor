"""Collect publisher metadata and generate static newsroom pages."""
import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from email.utils import format_datetime, parsedate_to_datetime
import gzip
from html import escape
from html.parser import HTMLParser
import json
from pathlib import Path
import re
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit
from urllib.request import Request, urlopen
from xml.etree import ElementTree as ET
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent
SOURCES = json.loads((ROOT / "sources.json").read_text())
CLOCK = ZoneInfo("Europe/Nicosia")
NOW = datetime.now(timezone.utc)
TODAY = NOW.astimezone(CLOCK).date().isoformat()
EXCLUDED = re.compile(r"\b(sports?|football|entertainment|lifestyle|sponsored|advertorial|celebrity)\b", re.I)
OPINION = re.compile(r"\b(opinion|editorials?|tribunes?|chroniques?)\b", re.I)
TRACKING = {"fbclid", "gclid", "mc_cid", "mc_eid"}


class Text(HTMLParser):
    def __init__(self, value):
        super().__init__()
        self.parts = []
        self.feed(value)

    def handle_data(self, data):
        self.parts.append(data)


def plain(value):
    return " ".join(" ".join(Text(value or "").parts).split())


def canonical(url):
    parts = urlsplit(url)
    if parts.scheme not in {"https", "http"} or not parts.hostname or parts.username:
        return ""
    pairs = [(k, v) for k, v in parse_qsl(parts.query, keep_blank_values=True)
             if not k.lower().startswith("utm_") and k.lower() not in TRACKING]
    return urlunsplit((parts.scheme, parts.netloc.lower(), parts.path, urlencode(pairs), ""))


def fetch(url):
    for attempt in range(2):
        try:
            request = Request(url, headers={"User-Agent": "RegionalNewsMonitor/0.1", "Accept-Encoding": "gzip"})
            with urlopen(request, timeout=12) as response:
                stream = gzip.GzipFile(fileobj=response) if response.headers.get("Content-Encoding") == "gzip" else response
                return stream.read(4_000_000)
        except OSError as error:
            if attempt or (getattr(error, "code", 500) < 500):
                raise


def date_value(value):
    for parse in (parsedate_to_datetime, datetime.fromisoformat):
        try:
            date = parse(value)
            if date.tzinfo and date <= NOW + timedelta(hours=1):
                return date.astimezone(timezone.utc).isoformat()
        except (ValueError, TypeError, OverflowError):
            continue
    return ""


def read_feed(url):
    root = ET.fromstring(fetch(url))
    if root.tag.rsplit("}", 1)[-1] not in {"rss", "feed", "RDF"}:
        raise ValueError("Expected RSS or Atom")
    articles = []
    for item in root.iter():
        if item.tag.rsplit("}", 1)[-1] not in {"item", "entry"}:
            continue
        def fields(name):
            return item.findall(f"{{*}}{name}")

        def value(*names):
            return next((node.text for name in names for node in fields(name) if node.text), "")

        links = [node.get("href") or node.text or "" for node in fields("link")
                 if node.get("rel", "alternate") == "alternate"]
        link = next((canonical(x) for x in links if canonical(x)), "")
        title = plain(value("title"))
        date = date_value(value("pubDate", "published", "date", "updated"))
        section = " ".join(node.get("term") or node.text or "" for node in fields("category"))
        scope = f"{urlsplit(link).path} {section}"
        if link and title and date and not EXCLUDED.search(scope):
            articles.append({"url": link, "title": title, "date": date, "scope": scope,
                             "description": plain(value("description", "summary"))[:280]})
    return articles


def collect(source):
    if not source["candidate"]:
        return [], "Collection route pending"
    try:
        items = read_feed(source["candidate"])
        return items, "Available" if items else "No eligible articles returned"
    except (OSError, ET.ParseError, ValueError) as error:
        return [], f"Collection failed ({type(error).__name__})"


def french_translator():
    try:
        from argostranslate.translate import get_translation_from_codes
        return get_translation_from_codes("fr", "en").translate
    except (ImportError, AttributeError, ValueError, StopIteration):
        return None


def eligible_for_daily(article):
    return not OPINION.search(article["scope"])


def homepage_lead(source, articles):
    # The audited Middle East Eye homepage exposes its lead as a linked H2.
    if source["name"] != "Middle East Eye":
        return None
    from urllib.parse import urljoin
    from bs4 import BeautifulSoup
    page = BeautifulSoup(fetch(source["home"]), "html.parser")
    lead = next((link for link in page.select("h2 a[href]")
                 if urlsplit(urljoin(source["home"], link["href"])).path.startswith("/news/")), None)
    if lead:
        url = canonical(urljoin(source["home"], lead["href"]))
        return next((item for item in articles if item["url"] == url and eligible_for_daily(item)), None)
    return None


def select_daily(source, articles):
    try:
        lead = homepage_lead(source, articles)
    except (OSError, ImportError, ValueError):
        lead = None
    if lead:
        return dict(lead, method="Homepage lead")
    if source.get("top"):
        try:
            top = sorted(read_feed(source["top"]), key=lambda a: a["date"], reverse=True)
            lead = next((row for row in top if eligible_for_daily(row)), None)
            if lead:
                return dict(lead, method="Official top stories")
        except (OSError, ET.ParseError, ValueError):
            pass
    lead = next((row for row in articles if eligible_for_daily(row)), None)
    return dict(lead, method="Latest RSS article") if lead else None


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value, encoding="utf-8")


def rss(path, base, title, entries):
    root = ET.Element("rss", version="2.0")
    channel = ET.SubElement(root, "channel")
    for tag, value in {"title": title, "description": title, "link": base, "language": "en"}.items():
        ET.SubElement(channel, tag).text = value
    for entry in entries:
        node = ET.SubElement(channel, "item")
        for tag, value in {"title": entry["title"], "link": entry["url"],
                           "description": entry.get("description", ""),
                           "pubDate": format_datetime(datetime.fromisoformat(entry["date"]), usegmt=True)}.items():
            ET.SubElement(node, tag).text = value
        ET.SubElement(node, "guid", isPermaLink="false").text = entry.get("id", entry["url"])
        if entry.get("source"):
            ET.SubElement(node, "source", url=entry.get("feed") or base).text = entry["source"]
    path.write_bytes(ET.tostring(root, encoding="utf-8", xml_declaration=True))


def page(title, content, prefix=""):
    return f"""<!doctype html><html lang="en"><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{escape(title)} | Regional News Monitor</title>
<link rel="alternate" type="application/rss+xml" title="Latest news" href="{prefix}feed.xml">
<link rel="alternate" type="application/rss+xml" title="Daily review" href="{prefix}daily.xml">
<link rel="stylesheet" href="{prefix}style.css?v=cyprus-review">
<header><a class="masthead" href="{prefix}index.html">Regional News Monitor</a>
<nav aria-label="Main"><a href="{prefix}index.html">Latest news</a>
<a href="{prefix}archive/">Press review</a><a href="{prefix}sources/">Sources</a>
<a href="{prefix}feed.xml">News RSS</a><a href="{prefix}daily.xml">Daily RSS</a></nav></header>
<main><h1>{escape(title)}</h1>{content}</main></html>"""


def cyprus_time(value):
    local = datetime.fromisoformat(value).astimezone(CLOCK)
    return local.strftime("%Y-%m-%d %H:%M") + " Cyprus time"


def region_heading(label):
    return f'<section class="region-section"><div class="region-heading"><h2>{label}</h2></div>'


def update_archived_layout(path):
    original = path.read_text(encoding="utf-8")
    updated = original.replace('style.css?v=regional-preview', 'style.css?v=cyprus-review')
    if 'class="region-section"' not in updated:
        for index, region in enumerate(dict.fromkeys(source["region"] for source in SOURCES)):
            label = escape(region)
            heading = f"<h2>{label}</h2>"
            if heading in updated:
                prefix = "</section>" if index else ""
                updated = updated.replace(heading, prefix + region_heading(label), 1)
        if updated != original and 'class="region-section"' in updated:
            updated = updated.replace("</main>", "</section></main>", 1)
    updated = re.sub(
        r'(<time datetime="([^"]+)">)[^<]* UTC</time>',
        lambda match: match[1] + cyprus_time(match[2]) + "</time>",
        updated,
    )
    if updated != original:
        write(path, updated)


def card(row):
    return (f'<article data-source="{escape(row["source"])}" data-region="{escape(row["region"])}">'
            f'<p class="meta">{escape(row["source"])} · <time datetime="{row["date"]}">{cyprus_time(row["date"])}</time>'
            f'{(" · " + escape(row["method"])) if row.get("method") else ""}</p>'
            f'<h2><a href="{escape(row["url"])}">{escape(row["title"])}</a></h2>'
            f'<p>{escape(row["description"])}</p></article>')


def options(values):
    return "".join(f'<option>{escape(value)}</option>' for value in sorted(set(values)))


def build(output, base, edition):
    output.mkdir(parents=True, exist_ok=True)
    state = output / "state.json"
    previous = json.loads(state.read_text()) if state.exists() else {"articles": [], "successful": None}
    cutoff = (NOW - timedelta(days=7)).isoformat()
    merged = {(item["source"], item["url"]): item for item in previous["articles"] if item["date"] >= cutoff}
    status = {}
    per_source = {}
    translator = french_translator()
    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(collect, SOURCES))
    for source, (articles, status_text) in zip(SOURCES, results):
        name = source["name"]
        if source["language"] == "fr" and articles:
            if translator is None:
                articles, status_text = [], "Waiting for French translation model"
            else:
                try:
                    articles = [dict(row, title=translator(row["title"]),
                                     description=translator(row["description"]) if row["description"] else "")
                                for row in articles]
                except (RuntimeError, ValueError):
                    articles, status_text = [], "Translation failed"
        articles = [dict(row, source=name, region=source["region"], feed=source["candidate"],
                         id=f'{name}::{row["url"]}') for row in articles]
        per_source[name] = sorted(articles, key=lambda row: row["date"], reverse=True)
        status[name] = status_text
        for row in articles:
            if row["date"] >= cutoff:
                merged[name, row["url"]] = row
    latest = sorted(merged.values(), key=lambda row: row["date"], reverse=True)
    successful = NOW.isoformat() if any(per_source.values()) else previous["successful"]
    write(state, json.dumps({"articles": latest, "successful": successful}, ensure_ascii=False))
    rss(output / "feed.xml", base, "Regional News Monitor — Latest news", latest)
    stamp = escape(cyprus_time(successful) if successful else "Pending")
    filters = f"""<p class="meta">Last successful collection <time>{stamp}</time></p>
<div class="filters"><label>Region <select id="region"><option value="">All regions</option>{options(s["region"] for s in SOURCES)}</select></label>
<label>Publication <select id="source"><option value="">All publications</option>{options(s["name"] for s in SOURCES)}</select></label></div>
<p id="empty" hidden>No articles match these filters.</p><script defer src="filters.js?v=regional-preview"></script>"""
    write(output / "index.html", page("Latest news", filters + "".join(map(card, latest))))
    source_html = "".join(f'<li><a href="{escape(s["home"])}">{escape(s["name"])}</a> · {escape(s["region"])} · '
                          f'{escape(status[s["name"]])}</li>' for s in SOURCES)
    write(output / "sources/index.html", page("Monitored publications", f"<ul>{source_html}</ul>", "../"))
    archive = output / "archive"
    archive.mkdir(exist_ok=True)
    edition_file = archive / f"{TODAY}.html"
    if edition and not edition_file.exists():
        blocks = []
        lines = [f"Regional News Monitor — {TODAY}"]
        for region in dict.fromkeys(s["region"] for s in SOURCES):
            blocks.append(region_heading(escape(region)))
            lines.append(f"\n{region}")
            for source in (s for s in SOURCES if s["region"] == region):
                name = source["name"]
                lead = select_daily(source, per_source[name])
                if lead:
                    lead = dict(lead, source=name, region=region)
                    blocks.append(card(lead))
                    lines.append(f'{name} ({lead["method"]})\n{lead["title"]}\n{lead["description"]}\n{lead["url"]}')
                else:
                    message = f"{name} — leading story could not be retrieved."
                    blocks.append(f'<p class="region-unavailable">{escape(message)}</p>')
                    lines.append(message)
            blocks.append("</section>")
        write(archive / f"{TODAY}.txt", "\n\n".join(lines) + "\n")
        write(edition_file, page(f"Press review · {TODAY}", "".join(blocks), "../"))
    editions = sorted(archive.glob("????-??-??.html"), reverse=True)
    for saved in editions:
        update_archived_layout(saved)
    links = "".join(f'<li><a href="{f.name}">{f.stem}</a></li>' for f in editions)
    write(archive / "index.html", page("Daily press review", f"<ul>{links}</ul>" if links else "<p>The first edition is pending.</p>", "../"))
    daily = [{"title": f"Regional press review · {f.stem}", "url": f"{base}archive/{f.name}",
              "date": datetime.fromisoformat(f"{f.stem}T07:00").replace(tzinfo=CLOCK).astimezone(timezone.utc).isoformat()}
             for f in editions[:90]]
    rss(output / "daily.xml", base, "Regional News Monitor — Daily press review", daily)
    for asset in ("style.css", "filters.js"):
        write(output / asset, (ROOT / asset).read_text())


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("public"))
    parser.add_argument("--base", required=True)
    parser.add_argument("--edition", action="store_true")
    args = parser.parse_args()
    build(args.output, args.base.rstrip("/") + "/", args.edition)
