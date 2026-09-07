"""
Scraper: Traficom — Finnish Transport and Communications Agency.

Traficom (traficom.fi) publishes procurement and tender notices.
URL: https://www.traficom.fi/en/about-us/procurement-and-tenders
"""
import hashlib
import logging
from typing import Iterator

from bs4 import BeautifulSoup

from scrapers.base import BaseScraper, parse_date, safe_text
from classifier import classify_industry, classify_location, classify_company_size, extract_keywords

logger = logging.getLogger(__name__)

BASE  = "https://www.traficom.fi"
PAGES = [
    f"{BASE}/en/about-traficom/procurement",
    f"{BASE}/fi/traficomista/hankinnat",
    f"{BASE}/en/about-traficom/open-calls-and-tenders",
]

TENDER_KW = {
    "tender", "procurement", "rfp", "rfq", "request", "hankinta",
    "kilpailutus", "tarjouspyynto", "tarjouspyyntö",
}


class TraficomScraper(BaseScraper):
    SOURCE_NAME  = "Traficom"
    BASE_URL     = BASE
    POLITE_DELAY = 1.5

    def scrape(self) -> Iterator[dict]:
        seen = set()
        for url in PAGES:
            try:
                resp = self._get(url)
                soup = BeautifulSoup(resp.text, "lxml")
            except Exception as exc:
                logger.warning("Traficom %s: %s", url, exc)
                continue

            items = (
                soup.select("article, li.procurement-item, div.tender-item")
                or soup.select("table.procurement-table tbody tr, .views-row")
                or [
                    a.find_parent(["li", "div", "tr", "article"]) or a
                    for a in soup.find_all("a", href=True)
                    if any(kw in (a.get_text() + a["href"]).lower() for kw in TENDER_KW)
                ]
            )

            logger.info("Traficom %s: %d items", url, len(items))
            for item in items:
                try:
                    rec = self._parse(item, url)
                    if rec and rec["external_id"] not in seen:
                        seen.add(rec["external_id"])
                        yield rec
                except Exception as exc:
                    logger.warning("Traficom item parse: %s", exc)

    def _parse(self, item, page_url: str) -> dict | None:
        title_el = item.select_one(
            "h1, h2, h3, h4, a.title, td.title, .field-title, [class*='title']"
        )
        title = safe_text(title_el) or safe_text(item)[:120]
        if not title:
            return None

        link_el = item.select_one("a[href]")
        if link_el:
            href = link_el["href"]
            url  = href if href.startswith("http") else BASE + href
        else:
            url = page_url

        desc_el = item.select_one("p, .description, .field-body, td.description")
        desc    = safe_text(desc_el)

        date_el  = item.select_one("time, .date, .field-date, td.date")
        date_str = (date_el.get("datetime") or safe_text(date_el)) if date_el else ""

        uid = hashlib.md5((title + url).encode()).hexdigest()[:20]
        full_text = f"{title} {desc} transport Finland"

        rec = self._base_record()
        rec.update({
            "external_id":  uid,
            "type":         "RFP",
            "status":       "OPEN",
            "title":        title[:1000],
            "description":  desc,
            "source_url":   url,
            "company_size": classify_company_size(full_text),
            "published_date": parse_date(date_str),
            "keywords":     extract_keywords(full_text),
            "raw_data":     {"text": item.get_text(separator=" ", strip=True)[:1500]},
        })
        rec["industry_area_id"] = self._industry_id(classify_industry("Transport " + full_text))
        rec["location_id"]      = self._location_id(classify_location("Finland Helsinki " + full_text))
        return rec
