"""
Scraper: Finnish Universities — procurement and research call pages.

Source list from RFI_RFP_website.md (items 86-95):
  University of Helsinki, Aalto University, University of Turku,
  Tampere University, University of Oulu, University of Jyväskylä,
  University of Eastern Finland, Åbo Akademi, LUT University,
  University of Vaasa.

Universities publish both procurement notices (HILMA-compliant) and
research calls/open tenders on their own websites.
"""
import hashlib
import logging
from typing import Iterator

from bs4 import BeautifulSoup

from scrapers.base import BaseScraper, parse_date, safe_text
from classifier import classify_industry, classify_company_size, extract_keywords

logger = logging.getLogger(__name__)

UNIVERSITY_SOURCES = [
    ("University of Helsinki",       "Helsinki",    [
        "https://www.helsinki.fi/en/university/procurement",
        "https://www.helsinki.fi/fi/yliopisto/hankinnat",
    ]),
    ("Aalto University",             "Espoo",       [
        "https://www.aalto.fi/en/aalto-university/procurement",
        "https://www.aalto.fi/fi/aalto-yliopisto/hankinnat",
    ]),
    ("University of Turku",          "Turku",       [
        "https://www.utu.fi/fi/yliopisto/hankinnat",
        "https://www.utu.fi/en/university/procurement",
    ]),
    ("Tampere University",           "Tampere",     [
        "https://www.tuni.fi/fi/tietoa-meista/hankinnat",
        "https://www.tuni.fi/en/about-us/procurement",
    ]),
    ("University of Oulu",           "Oulu",        [
        "https://www.oulu.fi/fi/yliopisto/hankinnat",
        "https://www.oulu.fi/en/university/procurement",
    ]),
    ("University of Jyväskylä",      "Jyväskylä",   [
        "https://www.jyu.fi/fi/yliopisto/hankinnat",
        "https://www.jyu.fi/en/university/procurement",
    ]),
    ("LUT University",               "Lappeenranta",[
        "https://www.lut.fi/fi/yliopisto/hankinnat",
        "https://www.lut.fi/en/university/procurement",
    ]),
    ("University of Eastern Finland","Other",       [
        "https://www.uef.fi/fi/yliopisto/hankinnat",
    ]),
    ("Åbo Akademi University",       "Turku",       [
        "https://www.abo.fi/en/procurement",
    ]),
    ("University of Vaasa",          "Other",       [
        "https://www.uwasa.fi/fi/yliopisto/hankinnat",
    ]),
]

PROCUREMENT_KW = {
    "hankinta", "kilpailutus", "tarjouspyynto", "tarjouspyyntö",
    "procurement", "tender", "rfp", "open call", "research call",
    "tietopyynto", "tietopyyntö",
}


class UniversitiesScraper(BaseScraper):
    SOURCE_NAME  = "Universities"
    POLITE_DELAY = 2.0

    def scrape(self) -> Iterator[dict]:
        seen = set()
        for uni_name, location, urls in UNIVERSITY_SOURCES:
            for url in urls:
                try:
                    yield from self._scrape_page(url, uni_name, location, seen)
                except Exception as exc:
                    logger.warning("Uni %s %s: %s", uni_name, url, exc)

    def _scrape_page(self, url: str, uni_name: str, location: str, seen: set) -> Iterator[dict]:
        try:
            resp = self._get(url)
            soup = BeautifulSoup(resp.text, "lxml")
        except Exception as exc:
            logger.warning("Uni %s: %s", url, exc)
            return

        items = (
            soup.select("article, li.procurement-item, div.procurement")
            or soup.select("table tbody tr")
            or soup.select(".views-row, ul.listing li, div.list-item")
            or [
                a.find_parent(["li", "div", "tr", "article"]) or a
                for a in soup.find_all("a", href=True)
                if any(kw in (a.get_text() + a["href"]).lower() for kw in PROCUREMENT_KW)
            ]
        )

        logger.info("Uni %s (%s): %d items", uni_name, url, len(items))
        for item in items:
            try:
                rec = self._parse(item, url, uni_name, location)
                if rec and rec["external_id"] not in seen:
                    seen.add(rec["external_id"])
                    yield rec
            except Exception as exc:
                logger.warning("Uni item: %s", exc)

    def _parse(self, item, page_url: str, uni_name: str, location: str) -> dict | None:
        title_el = item.select_one("h1,h2,h3,h4,.title,[class*='title'],a")
        title    = safe_text(title_el) or safe_text(item)[:120]
        if not title or len(title) < 5:
            return None

        link_el = item.select_one("a[href]")
        if link_el:
            href = link_el["href"]
            base = "/".join(page_url.split("/")[:3])
            url  = href if href.startswith("http") else base + href
        else:
            url = page_url

        desc_el  = item.select_one("p, .description, .summary")
        desc     = safe_text(desc_el)
        date_el  = item.select_one("time, .deadline, .date, [class*='date']")
        date_str = (date_el.get("datetime") or safe_text(date_el)) if date_el else ""

        is_rfi = any(kw in title.lower() or kw in desc.lower()
                     for kw in ("tietopyynto", "tietopyyntö", "markkinakartoitus",
                                "prior information", "open call", "research call"))

        uid = hashlib.md5((uni_name + title + url).encode()).hexdigest()[:20]
        full_text = f"{title} {desc} {uni_name} research Finland"

        rec = self._base_record()
        rec.update({
            "external_id":           uid,
            "type":                  "RFI" if is_rfi else "RFP",
            "status":                "OPEN",
            "title":                 title[:1000],
            "description":           desc,
            "contracting_authority": uni_name,
            "company_size":          classify_company_size(full_text),
            "deadline_date":         parse_date(date_str),
            "source_url":            url,
            "keywords":              extract_keywords(full_text),
            "opportunity_score":     self._score(full_text),
            "raw_data":              {"text": item.get_text(separator=" ", strip=True)[:1200]},
        })
        rec["industry_area_id"] = self._industry_id(classify_industry("Education " + full_text))
        rec["location_id"]      = self._location_id(location)
        return rec

    @staticmethod
    def _score(full_text: str) -> int:
        score = 42
        text = full_text.lower()
        kws = ["software", "cloud", "ai", "data", "it ", "digital", "research", "innovation"]
        score += min(sum(1 for kw in kws if kw in text) * 4, 22)
        return min(score, 100)
