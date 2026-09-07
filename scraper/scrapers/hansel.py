"""
Scraper: Hansel Oy — Finland's central government procurement unit.

Source: https://www.hansel.fi/en/procurement/

Hansel manages framework agreements and DPS (Dynamic Purchasing Systems)
on behalf of the Finnish state. All calls are public.

Also scrapes Hanki (hanki.fi) — the state procurement service portal
run by the State Treasury (Valtiokonttori).
Source: https://hanki.fi  (redirects to state procurement services)
"""
import hashlib
import logging
from typing import Iterator

from bs4 import BeautifulSoup

from scrapers.base import BaseScraper, parse_date, safe_text
from classifier import classify_industry, classify_company_size, extract_keywords

logger = logging.getLogger(__name__)

HANSEL_PAGES = [
    "https://www.hansel.fi/en/procurement/",
    "https://www.hansel.fi/fi/kilpailutukset/",
    "https://www.hansel.fi/en/",
    "https://www.hansel.fi/fi/",
]

HANKI_PAGES = [
    "https://hanki.fi/",
    "https://www.valtiokonttori.fi/palvelut/hankinnat/",
]


class HanselScraper(BaseScraper):
    SOURCE_NAME  = "Hansel"
    BASE_URL     = "https://www.hansel.fi"
    POLITE_DELAY = 1.5

    def scrape(self) -> Iterator[dict]:
        seen = set()
        for url in HANSEL_PAGES:
            yield from self._scrape_page(url, "Hansel Oy", seen)
        for url in HANKI_PAGES:
            yield from self._scrape_page(url, "Hanki / Valtiokonttori", seen)

    def _scrape_page(self, url: str, authority_name: str, seen: set) -> Iterator[dict]:
        try:
            resp = self._get(url)
            soup = BeautifulSoup(resp.text, "lxml")
        except Exception as exc:
            logger.warning("Hansel %s: %s", url, exc)
            return

        items = (
            soup.select("article, li.competition-item, div.competition")
            or soup.select("table tbody tr")
            or soup.select(".views-row, .field-items .field-item")
            or [
                a.find_parent(["li", "div", "article", "tr"]) or a
                for a in soup.find_all("a", href=True)
                if any(kw in (a.get_text() + a["href"]).lower()
                       for kw in ("competition", "kilpailutus", "framework",
                                  "puitesopimus", "tender", "hankinta", "dps"))
            ]
        )

        logger.info("Hansel %s: %d items", url, len(items))
        for item in items:
            try:
                rec = self._parse(item, url, authority_name)
                if rec and rec["external_id"] not in seen:
                    seen.add(rec["external_id"])
                    yield rec
            except Exception as exc:
                logger.warning("Hansel item: %s", exc)

    def _parse(self, item, page_url: str, authority_name: str) -> dict | None:
        title_el = item.select_one("h1,h2,h3,h4,.title,[class*='title'],a")
        title    = safe_text(title_el) or safe_text(item)[:120]
        if not title or len(title) < 5:
            return None

        link_el = item.select_one("a[href]")
        if link_el:
            href = link_el["href"]
            url  = href if href.startswith("http") else self.BASE_URL + href
        else:
            url = page_url

        desc_el  = item.select_one("p, .description, .summary, .lead")
        desc     = safe_text(desc_el)

        date_el  = item.select_one("time, .deadline, .date, [class*='date']")
        date_str = (date_el.get("datetime") or safe_text(date_el)) if date_el else ""

        uid = hashlib.md5((title + url).encode()).hexdigest()[:20]
        full_text = f"{title} {desc} Finland government procurement"

        # Determine if it's a framework agreement (DPS) or direct RFP
        is_framework = any(kw in title.lower() or kw in url.lower()
                           for kw in ("framework", "puitesopimus", "dps", "dynamic"))
        tender_type = "RFP" if not is_framework else "RFP"

        rec = self._base_record()
        rec.update({
            "external_id":           uid,
            "type":                  tender_type,
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
        rec["industry_area_id"] = self._industry_id(classify_industry(full_text))
        rec["location_id"]      = self._location_id("Nationwide")
        return rec

    @staticmethod
    def _score(full_text: str) -> int:
        score = 50  # state procurement — high baseline
        text = full_text.lower()
        kws = ["software", "cloud", "ai", "data", "it ", "digital"]
        score += min(sum(1 for kw in kws if kw in text) * 5, 20)
        return min(score, 100)
