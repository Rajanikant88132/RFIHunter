"""
Scraper: VTT Technical Research Centre of Finland — research & innovation calls.

VTT publishes open calls, collaboration requests and RFIs at:
  https://www.vttresearch.com/en/collaboration
  https://www.vttresearch.com/en/open-positions  (also lists open calls)
  https://www.vtt.fi/palvelut  (Finnish services)
"""
import hashlib
import logging
from typing import Iterator

from bs4 import BeautifulSoup

from scrapers.base import BaseScraper, parse_date, safe_text
from classifier import classify_industry, classify_company_size, extract_keywords

logger = logging.getLogger(__name__)

PAGES = [
    "https://www.vttresearch.com/en/collaboration-and-services",
    "https://www.vttresearch.com/en/media/news",
    "https://www.vttresearch.com/en/about-vtt/sustainability/open-science",
    "https://www.vtt.fi/en/about-vtt/open-calls",
]

CALL_KW = {
    "call", "rfi", "request", "open call", "collaboration",
    "haku", "kutsu", "yhteistyö", "tender",
}


class VTTScraper(BaseScraper):
    SOURCE_NAME  = "VTT"
    BASE_URL     = "https://www.vttresearch.com"
    POLITE_DELAY = 1.5

    def scrape(self) -> Iterator[dict]:
        seen = set()
        for url in PAGES:
            try:
                resp = self._get(url)
                soup = BeautifulSoup(resp.text, "lxml")
            except Exception as exc:
                logger.warning("VTT %s: %s", url, exc)
                continue

            items = (
                soup.select("article, div.card, li.item, div.listing-item")
                or soup.select("[class*='card'], [class*='item'], [class*='listing']")
                or [
                    a.find_parent(["li", "div", "article"]) or a
                    for a in soup.find_all("a", href=True)
                    if any(kw in (a.get_text() + a["href"]).lower() for kw in CALL_KW)
                ]
            )

            logger.info("VTT %s: %d items", url, len(items))
            for item in items:
                try:
                    rec = self._parse(item, url)
                    if rec and rec["external_id"] not in seen:
                        seen.add(rec["external_id"])
                        yield rec
                except Exception as exc:
                    logger.warning("VTT item: %s", exc)

    def _parse(self, item, page_url: str) -> dict | None:
        title_el = item.select_one("h1,h2,h3,h4,.title,[class*='title'],a")
        title    = safe_text(title_el) or safe_text(item)[:120]
        if not title or len(title) < 5:
            return None

        link_el = item.select_one("a[href]")
        if link_el:
            href = link_el["href"]
            url  = href if href.startswith("http") else self.BASE_URL + href
        else:
            url  = page_url

        desc_el  = item.select_one("p, .description, .summary, .teaser")
        desc     = safe_text(desc_el)

        date_el  = item.select_one("time, .date, [class*='date']")
        date_str = (date_el.get("datetime") or safe_text(date_el)) if date_el else ""

        uid = hashlib.md5((title + url).encode()).hexdigest()[:20]
        full_text = f"{title} {desc} research Finland technology"

        rec = self._base_record()
        rec.update({
            "external_id":           uid,
            "type":                  "RFI",
            "status":                "OPEN",
            "title":                 title[:1000],
            "description":           desc,
            "contracting_authority": "VTT Technical Research Centre",
            "company_size":          classify_company_size(full_text),
            "published_date":        parse_date(date_str),
            "source_url":            url,
            "keywords":              extract_keywords(full_text),
            "raw_data":              {"text": item.get_text(separator=" ", strip=True)[:1200]},
        })
        rec["industry_area_id"] = self._industry_id(classify_industry("Education & Research " + full_text))
        rec["location_id"]      = self._location_id("Espoo")   # VTT HQ is in Espoo
        return rec
