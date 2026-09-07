"""
Scraper: Finland RSS/Atom procurement feeds — generic feed reader.

Several Finnish contracting authorities publish Atom/RSS feeds for their
procurement notices. This scraper reads multiple feed URLs and normalises
each entry into a standard tender record.

Sources:
  - HILMA RSS feed
  - Hankintailmoitukset RSS
  - Finnish state procurement (valtiokonttori / hansel)
  - Hansel Oy (Finland's central procurement unit)
"""
import hashlib
import logging
from typing import Iterator
from xml.etree import ElementTree as ET

from scrapers.base import BaseScraper, parse_date, safe_text
from classifier import classify_industry, classify_location, classify_company_size, extract_keywords

logger = logging.getLogger(__name__)

# (feed_url, source_label, default_type)
# Verified live RSS/Atom feeds for Finnish procurement
FEEDS = [
    ("https://www.hansel.fi/en/feed/",                   "Hansel",     "RFP"),
    ("https://www.hansel.fi/feed/",                      "Hansel",     "RFP"),
    ("https://tukes.fi/fi/ajankohtaista/feed/",          "Tukes",      "RFP"),
    ("https://www.motiva.fi/rss.xml",                    "Motiva",     "RFI"),
    ("https://vm.fi/feed/",                              "MinFinance", "RFP"),
    ("https://www.businessfinland.fi/feed/",             "BizFinland", "RFI"),
]

# XML namespace helpers
NS = {
    "atom": "http://www.w3.org/2005/Atom",
    "dc":   "http://purl.org/dc/elements/1.1/",
}


def _txt(el, tag: str, ns: str = "") -> str:
    """Get text of first matching child tag, or ''."""
    if el is None:
        return ""
    child = el.find(f"{ns}{tag}") if not ns else el.find(f"{{{NS.get(ns,'')}}}{tag}")
    if child is None:
        child = el.find(tag)
    return (child.text or "").strip() if child is not None else ""


class RSSFeedScraper(BaseScraper):
    SOURCE_NAME  = "RSS-Feeds"
    POLITE_DELAY = 1.0

    def scrape(self) -> Iterator[dict]:
        seen = set()
        for feed_url, label, default_type in FEEDS:
            try:
                resp = self._get(feed_url)
                yield from self._parse_feed(resp.text, feed_url, label, default_type, seen)
            except Exception as exc:
                logger.warning("RSS feed %s: %s", feed_url, exc)

    def _parse_feed(
        self, xml_text: str, feed_url: str, label: str, default_type: str, seen: set
    ) -> Iterator[dict]:
        try:
            root = ET.fromstring(xml_text)
        except ET.ParseError as exc:
            logger.warning("RSS parse error %s: %s", feed_url, exc)
            return

        # RSS 2.0
        items = root.findall(".//item")
        # Atom
        if not items:
            items = root.findall(".//{http://www.w3.org/2005/Atom}entry")

        for item in items:
            try:
                rec = self._parse_item(item, label, default_type, feed_url)
                if rec and rec["external_id"] not in seen:
                    seen.add(rec["external_id"])
                    yield rec
            except Exception as exc:
                logger.warning("RSS item parse %s: %s", label, exc)

    def _parse_item(self, item, label: str, default_type: str, feed_url: str) -> dict | None:
        # RSS 2.0 tags
        title = (
            _txt(item, "title")
            or _txt(item, "{http://www.w3.org/2005/Atom}title")
        )
        if not title:
            return None

        link = (
            _txt(item, "link")
            or _txt(item, "{http://www.w3.org/2005/Atom}id")
            or feed_url
        )
        # Atom <link href="...">
        if not link or link == feed_url:
            link_el = item.find("{http://www.w3.org/2005/Atom}link")
            if link_el is not None:
                link = link_el.get("href", feed_url)

        desc = (
            _txt(item, "description")
            or _txt(item, "summary")
            or _txt(item, "{http://www.w3.org/2005/Atom}summary")
            or _txt(item, "{http://www.w3.org/2005/Atom}content")
        )
        # strip HTML tags from desc
        if desc and "<" in desc:
            try:
                from bs4 import BeautifulSoup
                desc = BeautifulSoup(desc, "lxml").get_text(separator=" ")
            except Exception:
                pass

        pub_str = (
            _txt(item, "pubDate")
            or _txt(item, "published")
            or _txt(item, "{http://www.w3.org/2005/Atom}published")
            or _txt(item, "{http://www.w3.org/2005/Atom}updated")
        )

        uid = hashlib.md5((title + link).encode()).hexdigest()[:20]
        full_text = f"{title} {desc}"

        rec = self._base_record()
        rec.update({
            "external_id":  uid,
            "source":       label,
            "type":         default_type,
            "status":       "OPEN",
            "title":        safe_text(title)[:1000],
            "description":  safe_text(desc),
            "published_date": parse_date(pub_str),
            "source_url":   link,
            "company_size": classify_company_size(full_text),
            "keywords":     extract_keywords(full_text),
            "raw_data":     {"feed": feed_url, "title": title},
        })
        rec["industry_area_id"] = self._industry_id(classify_industry(full_text))
        rec["location_id"]      = self._location_id(classify_location("Finland " + full_text))
        return rec
