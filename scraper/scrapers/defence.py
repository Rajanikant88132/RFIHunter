"""
Scraper: Finnish Defence Forces — procurement and tenders (puolustusvoimat.fi).

The Finnish Defence Forces publish procurement notices at:
  https://www.puolustusvoimat.fi/en/industry-and-research/procurement
  https://www.puolustusvoimat.fi/fi/teollisuus-ja-tutkimus/hankinnat
"""
import hashlib
import logging
from typing import Iterator

from bs4 import BeautifulSoup

from scrapers.base import BaseScraper, parse_date, safe_text
from classifier import classify_industry, classify_company_size, extract_keywords

logger = logging.getLogger(__name__)

BASE  = "https://www.puolustusvoimat.fi"
PAGES = [
    f"{BASE}/en/industry-cooperation/procurement",
    f"{BASE}/fi/teollisuusyhteistyo/hankinnat",
    f"{BASE}/en/about/procurements",
]


class DefenceScraper(BaseScraper):
    SOURCE_NAME  = "FinnishDefence"
    BASE_URL     = BASE
    POLITE_DELAY = 2.0   # defence site — be extra polite

    def scrape(self) -> Iterator[dict]:
        seen = set()
        for url in PAGES:
            try:
                resp = self._get(url)
                soup = BeautifulSoup(resp.text, "lxml")
            except Exception as exc:
                logger.warning("Defence %s: %s", url, exc)
                continue

            items = (
                soup.select("article, li.procurement-item, div.procurement")
                or soup.select("table tbody tr")
                or soup.select(".field-items .field-item, .views-row")
                or [
                    a.find_parent(["li", "div", "tr", "article"]) or a
                    for a in soup.find_all("a", href=True)
                    if any(
                        kw in (a.get_text() + a["href"]).lower()
                        for kw in (
                            "hankinta", "procurement", "tender",
                            "rfp", "rfq", "kilpailutus", "tarjouspyynto"
                        )
                    )
                ]
            )

            logger.info("Defence %s: %d items", url, len(items))
            for item in items:
                try:
                    rec = self._parse(item, url)
                    if rec and rec["external_id"] not in seen:
                        seen.add(rec["external_id"])
                        yield rec
                except Exception as exc:
                    logger.warning("Defence item parse: %s", exc)

    def _parse(self, item, page_url: str) -> dict | None:
        title_el = item.select_one("h1,h2,h3,h4,.title,[class*='title'],a")
        title    = safe_text(title_el) or safe_text(item)[:120]
        if not title or len(title) < 5:
            return None

        link_el = item.select_one("a[href]")
        if link_el:
            href = link_el["href"]
            url  = href if href.startswith("http") else BASE + href
        else:
            url  = page_url

        desc_el  = item.select_one("p, .description, .summary")
        desc     = safe_text(desc_el)

        date_el  = item.select_one("time, .date, [class*='date']")
        date_str = (date_el.get("datetime") or safe_text(date_el)) if date_el else ""

        uid = hashlib.md5((title + url).encode()).hexdigest()[:20]
        full_text = f"{title} {desc} defence Finland military"

        rec = self._base_record()
        rec.update({
            "external_id":           uid,
            "type":                  "RFP",
            "status":                "OPEN",
            "title":                 title[:1000],
            "description":           desc,
            "contracting_authority": "Finnish Defence Forces",
            "company_size":          classify_company_size(full_text),
            "published_date":        parse_date(date_str),
            "source_url":            url,
            "keywords":              extract_keywords(full_text),
            "raw_data":              {"text": item.get_text(separator=" ", strip=True)[:1200]},
        })
        rec["industry_area_id"] = self._industry_id(classify_industry("Defence & Security " + full_text))
        rec["location_id"]      = self._location_id("Nationwide")
        return rec
