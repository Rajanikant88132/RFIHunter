"""
Scraper: Top 20 Finnish Cities — procurement pages.

Source list from RFI_RFP_website.md (items 11-30):
  Helsinki, Espoo, Tampere, Vantaa, Turku, Oulu, Jyväskylä, Lahti,
  Kuopio, Pori, Kouvola, Joensuu, Lappeenranta, Hämeenlinna,
  Vaasa, Seinäjoki, Rovaniemi, Mikkeli, Kotka, Salo

Each city uses HILMA for mandatory notices — this scraper targets
city-specific procurement calendars and supplementary pages that
may not appear in the national portal.
"""
import hashlib
import logging
from typing import Iterator

from bs4 import BeautifulSoup

from scrapers.base import BaseScraper, parse_date, safe_text
from classifier import classify_industry, classify_company_size, extract_keywords

logger = logging.getLogger(__name__)

# (city_name, location_name, [urls...])
CITY_SOURCES = [
    ("City of Helsinki", "Helsinki", [
        "https://www.hel.fi/en/city-and-administration/strategy-and-economy/procurement",
        "https://www.hel.fi/fi/kaupunki-ja-hallinto/strategia-ja-talous/hankinnat",
    ]),
    ("City of Espoo", "Espoo", [
        "https://www.espoo.fi/en/city-espoo/procurement",
        "https://www.espoo.fi/fi/espoon-kaupunki/hankinnat",
    ]),
    ("City of Tampere", "Tampere", [
        "https://www.tampere.fi/tampere-info/hankinnat.html",
        "https://www.tampere.fi/en/city-tampere/procurement.html",
    ]),
    ("City of Vantaa", "Other", [
        "https://www.vantaa.fi/fi/kaupunki-ja-paatoksenteko/hankinnat",
        "https://www.vantaa.fi/en/city-and-decision-making/procurement",
    ]),
    ("City of Turku", "Turku", [
        "https://www.turku.fi/en/procurement",
        "https://www.turku.fi/fi/kaupunki-ja-paatoksenteko/hankinnat",
    ]),
    ("City of Oulu", "Oulu", [
        "https://www.oulu.fi/fi/hankinnat",
        "https://www.oulu.fi/en/procurement",
    ]),
    ("City of Jyväskylä", "Jyväskylä", [
        "https://www.jyvaskyla.fi/en/city-information/procurement",
        "https://www.jyvaskyla.fi/fi/kaupunki/hankinnat",
    ]),
    ("City of Lahti", "Lahti", [
        "https://www.lahti.fi/fi/kaupunki-ja-hallinto/hankinnat",
    ]),
    ("City of Kuopio", "Kuopio", [
        "https://www.kuopio.fi/fi/kaupunki-ja-hallinto/hankinnat",
        "https://www.kuopio.fi/en/procurement",
    ]),
    ("City of Tampere – Wellbeing", "Tampere", [
        "https://pirha.fi/hankinnat",
    ]),
    ("City of Kouvola", "Other", [
        "https://www.kouvola.fi/fi/kaupunki-ja-paatoksenteko/hankinnat/",
    ]),
    ("City of Joensuu", "Joensuu", [
        "https://www.joensuu.fi/fi/kaupunki-ja-paatoksenteko/hankinnat",
    ]),
    ("City of Rovaniemi", "Rovaniemi", [
        "https://www.rovaniemi.fi/fi/palvelut/hankinnat",
    ]),
    ("City of Vaasa", "Other", [
        "https://www.vaasa.fi/fi/kaupunki-ja-hallinto/hankinnat",
    ]),
]

PROCUREMENT_KW = {
    "hankinta", "kilpailutus", "tarjouspyynto", "tarjouspyyntö",
    "procurement", "tender", "rfp", "rfq",
    "tietopyynto", "tietopyyntö", "markkinakartoitus",
}


class FinnishCitiesScraper(BaseScraper):
    SOURCE_NAME  = "FinnishCities"
    POLITE_DELAY = 2.0  # be polite to city websites

    def scrape(self) -> Iterator[dict]:
        seen = set()
        for city_name, location, urls in CITY_SOURCES:
            for url in urls:
                try:
                    yield from self._scrape_city(url, city_name, location, seen)
                except Exception as exc:
                    logger.warning("City %s %s: %s", city_name, url, exc)

    def _scrape_city(self, url: str, city_name: str, location: str, seen: set) -> Iterator[dict]:
        try:
            resp = self._get(url)
            soup = BeautifulSoup(resp.text, "lxml")
        except Exception as exc:
            logger.warning("City %s: %s", url, exc)
            return

        items = (
            soup.select("article, li.procurement-item, div.procurement")
            or soup.select("table.procurement tbody tr, .views-row")
            or soup.select("ul.list li, ol.list li, div.listing-item")
            or [
                a.find_parent(["li", "div", "tr", "article"]) or a
                for a in soup.find_all("a", href=True)
                if any(kw in (a.get_text() + a["href"]).lower() for kw in PROCUREMENT_KW)
            ]
        )

        logger.info("City %s (%s): %d items", city_name, url, len(items))
        for item in items:
            try:
                rec = self._parse(item, url, city_name, location)
                if rec and rec["external_id"] not in seen:
                    seen.add(rec["external_id"])
                    yield rec
            except Exception as exc:
                logger.warning("City %s item: %s", city_name, exc)

    def _parse(self, item, page_url: str, city_name: str, location: str) -> dict | None:
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

        uid = hashlib.md5((city_name + title + url).encode()).hexdigest()[:20]
        full_text = f"{title} {desc} {city_name} Finland"

        # Detect RFI keywords in Finnish
        is_rfi = any(kw in title.lower() or kw in desc.lower()
                     for kw in ("tietopyynto", "tietopyyntö", "markkinakartoitus",
                                "market consultation", "prior information", "ennakkoilmoitus"))

        rec = self._base_record()
        rec.update({
            "external_id":           uid,
            "type":                  "RFI" if is_rfi else "RFP",
            "status":                "OPEN",
            "title":                 title[:1000],
            "description":           desc,
            "contracting_authority": city_name,
            "company_size":          classify_company_size(full_text),
            "deadline_date":         parse_date(date_str),
            "source_url":            url,
            "keywords":              extract_keywords(full_text),
            "opportunity_score":     self._score(full_text),
            "raw_data":              {"text": item.get_text(separator=" ", strip=True)[:1200]},
        })
        rec["industry_area_id"] = self._industry_id(classify_industry(full_text))
        rec["location_id"]      = self._location_id(location)
        return rec

    @staticmethod
    def _score(full_text: str) -> int:
        score = 42
        text = full_text.lower()
        kws = ["software", "cloud", "ai", "data", "it ", "digital", "platform"]
        score += min(sum(1 for kw in kws if kw in text) * 5, 25)
        return min(score, 100)
