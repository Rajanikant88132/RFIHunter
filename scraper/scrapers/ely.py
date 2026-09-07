"""
Scraper: ELY-Centre / KEHA-Centre — Regional economic and transport agency tenders.

ELY-centres (Centre for Economic Development, Transport and the Environment) and
KEHA-centre (Centre for Economic Development, Transport and the Environment) publish
regional procurement notices across Finland.
URLs:
  https://www.ely-keskus.fi/en/web/ely-en/procurement
  https://www.keha-keskus.fi/hankinnat/
"""
import hashlib
import logging
from typing import Iterator

from bs4 import BeautifulSoup

from scrapers.base import BaseScraper, parse_date, safe_text
from classifier import classify_industry, classify_location, classify_company_size, extract_keywords

logger = logging.getLogger(__name__)

PAGES = [
    # ely-keskus has been renamed to elinvoimakeskus in 2025
    ("https://www.elinvoimakeskus.fi/en/procurement",                   "ELY-Centre"),
    ("https://www.elinvoimakeskus.fi/fi/hankinnat",                     "ELY-Centre"),
    # KEHA is now under VM (Ministry of Finance)
    ("https://vm.fi/kilpailutukset",                                    "KEHA-Centre"),
    ("https://www.suomi.fi/palvelut/organisaatiolle/hankinnat",         "Suomi.fi"),
    # fallback to Hilma's contracting authority listing
    ("https://hilma.fi/organisation",                                   "HILMA-Orgs"),
]


class ELYScraper(BaseScraper):
    SOURCE_NAME  = "ELY-KEHA"
    POLITE_DELAY = 1.5

    def scrape(self) -> Iterator[dict]:
        seen = set()
        for url, authority_name in PAGES:
            try:
                resp = self._get(url)
                soup = BeautifulSoup(resp.text, "lxml")
            except Exception as exc:
                logger.warning("ELY %s: %s", url, exc)
                continue

            items = (
                soup.select("article, li.procurement, div.procurement-item")
                or soup.select("table tbody tr")
                or soup.select(".portlet-body li, .entry-content li")
                or [
                    a.find_parent(["li", "div", "tr"]) or a
                    for a in soup.find_all("a", href=True)
                    if any(
                        kw in (a.get_text() + a["href"]).lower()
                        for kw in ("hankinta", "procurement", "kilpailutus", "tender")
                    )
                ]
            )

            logger.info("ELY %s: %d items", url, len(items))
            for item in items:
                try:
                    rec = self._parse(item, url, authority_name)
                    if rec and rec["external_id"] not in seen:
                        seen.add(rec["external_id"])
                        yield rec
                except Exception as exc:
                    logger.warning("ELY item: %s", exc)

    def _parse(self, item, page_url: str, authority_name: str) -> dict | None:
        title_el = item.select_one("h1,h2,h3,h4,.title,[class*='title'],a")
        title    = safe_text(title_el) or safe_text(item)[:120]
        if not title or len(title) < 5:
            return None

        link_el = item.select_one("a[href]")
        if link_el:
            href = link_el["href"]
            url  = href if href.startswith("http") else "https://www.ely-keskus.fi" + href
        else:
            url  = page_url

        desc_el  = item.select_one("p, .description, .summary")
        desc     = safe_text(desc_el)

        date_el  = item.select_one("time, .date, [class*='date']")
        date_str = (date_el.get("datetime") or safe_text(date_el)) if date_el else ""

        uid = hashlib.md5((title + url).encode()).hexdigest()[:20]
        full_text = f"{title} {desc} Finland regional"

        rec = self._base_record()
        rec.update({
            "external_id":           uid,
            "type":                  "RFP",
            "status":                "OPEN",
            "title":                 title[:1000],
            "description":           desc,
            "contracting_authority": authority_name,
            "company_size":          classify_company_size(full_text),
            "published_date":        parse_date(date_str),
            "source_url":            url,
            "keywords":              extract_keywords(full_text),
            "raw_data":              {"text": item.get_text(separator=" ", strip=True)[:1200]},
        })
        rec["industry_area_id"] = self._industry_id(classify_industry(full_text))
        rec["location_id"]      = self._location_id(classify_location(authority_name + " Finland"))
        return rec
