"""
Scraper: Finnish Wellbeing Services Counties — healthcare/social procurement.

Source list from RFI_RFP_website.md (items 31-51):
  All 21 wellbeing services counties (hyvinvointialue).
  These were created in 2023 and handle healthcare and social services procurement.

Most use HILMA + Cloudia. This scraper targets their dedicated procurement pages.
"""
import hashlib
import logging
from typing import Iterator

from bs4 import BeautifulSoup

from scrapers.base import BaseScraper, parse_date, safe_text
from classifier import classify_industry, classify_company_size, extract_keywords

logger = logging.getLogger(__name__)

WELLBEING_SOURCES = [
    ("HUS Helsinki University Hospital",     "Helsinki",    "https://www.hus.fi/hankintayksikko"),
    ("Vantaa-Kerava wellbeing county",       "Other",       "https://www.keusote.fi/fi/palvelut/hankinnat"),
    ("Western Uusimaa wellbeing county",     "Other",       "https://luvn.fi/fi/hankinnat"),
    ("Southwest Finland wellbeing county",   "Turku",       "https://varha.fi/fi/hankinnat"),
    ("Satakunta wellbeing county",           "Pori",        "https://satahyva.fi/fi/hankinnat"),
    ("Kanta-Häme wellbeing county",          "Other",       "https://omahame.fi/fi/hankinnat"),
    ("Pirkanmaa wellbeing county",           "Tampere",     "https://pirha.fi/hankinnat"),
    ("Päijät-Häme wellbeing county",         "Lahti",       "https://paijathyva.fi/hankinnat"),
    ("North Ostrobothnia wellbeing county",  "Oulu",        "https://pohde.fi/hankinnat"),
    ("Lapland wellbeing county",             "Rovaniemi",   "https://lapinhy.fi/hankinnat"),
    ("North Savo wellbeing county",          "Kuopio",      "https://pohjo-savo.fi/hankinnat"),
    ("Central Finland wellbeing county",     "Jyväskylä",   "https://hyvaks.fi/hankinnat"),
    ("South Karelia wellbeing county",       "Lappeenranta","https://eksote.fi/hankinnat"),
    ("Kainuu wellbeing county",              "Other",       "https://hyvinvointikainuu.fi/hankinnat"),
]

PROCUREMENT_KW = {
    "hankinta", "kilpailutus", "tarjouspyynto", "tarjouspyyntö",
    "procurement", "tender", "rfp",
}


class WellbeingCountiesScraper(BaseScraper):
    SOURCE_NAME  = "WellbeingCounties"
    POLITE_DELAY = 2.0

    def scrape(self) -> Iterator[dict]:
        seen = set()
        for authority_name, location, url in WELLBEING_SOURCES:
            try:
                yield from self._scrape_page(url, authority_name, location, seen)
            except Exception as exc:
                logger.warning("Wellbeing %s: %s", authority_name, exc)

    def _scrape_page(self, url: str, authority_name: str, location: str, seen: set) -> Iterator[dict]:
        try:
            resp = self._get(url)
            soup = BeautifulSoup(resp.text, "lxml")
        except Exception as exc:
            logger.warning("Wellbeing %s: %s", url, exc)
            return

        items = (
            soup.select("article, li.procurement-item, div.procurement")
            or soup.select("table tbody tr")
            or soup.select(".views-row, .field-items .field-item, ul.listing li")
            or [
                a.find_parent(["li", "div", "tr", "article"]) or a
                for a in soup.find_all("a", href=True)
                if any(kw in (a.get_text() + a["href"]).lower() for kw in PROCUREMENT_KW)
            ]
        )

        logger.info("Wellbeing %s: %d items", authority_name, len(items))
        for item in items:
            try:
                rec = self._parse(item, url, authority_name, location)
                if rec and rec["external_id"] not in seen:
                    seen.add(rec["external_id"])
                    yield rec
            except Exception as exc:
                logger.warning("Wellbeing item: %s", exc)

    def _parse(self, item, page_url: str, authority_name: str, location: str) -> dict | None:
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

        uid = hashlib.md5((authority_name + title + url).encode()).hexdigest()[:20]
        full_text = f"{title} {desc} {authority_name} healthcare Finland"

        rec = self._base_record()
        rec.update({
            "external_id":           uid,
            "type":                  "RFP",
            "status":                "OPEN",
            "title":                 title[:1000],
            "description":           desc,
            "contracting_authority": authority_name,
            "company_size":          classify_company_size(full_text),
            "deadline_date":         parse_date(date_str),
            "source_url":            url,
            "keywords":              extract_keywords(full_text),
            "opportunity_score":     self._score(full_text),
            "raw_data":              {"text": item.get_text(separator=" ", strip=True)[:1200]},
        })
        rec["industry_area_id"] = self._industry_id(classify_industry("Healthcare " + full_text))
        rec["location_id"]      = self._location_id(location)
        return rec

    @staticmethod
    def _score(full_text: str) -> int:
        score = 45
        text = full_text.lower()
        kws = ["software", "cloud", "health", "data", "it ", "digital", "patient", "medical"]
        score += min(sum(1 for kw in kws if kw in text) * 5, 25)
        return min(score, 100)
