"""
Scraper: Business Finland — open calls, RFI and funding opportunities.

Business Finland (businessfinland.fi) publishes open calls for research funding,
startup programmes and procurement requests. We scrape the open calls listing page.
URL: https://www.businessfinland.fi/en/do-business-with-finland/find-funding-and-services
     https://www.businessfinland.fi/en/for-finnish-companies/funding/all-funding
"""
import hashlib
import logging
from typing import Iterator

from bs4 import BeautifulSoup

from scrapers.base import BaseScraper, parse_date, safe_text
from classifier import classify_industry, classify_location, classify_company_size, extract_keywords

logger = logging.getLogger(__name__)

BASE = "https://www.businessfinland.fi"

PAGES = [
    f"{BASE}/en/programmes-and-services",
    f"{BASE}/en/for-finnish-companies/funding",
    f"{BASE}/en/for-companies/funding-and-services",
    f"{BASE}/globalassets/julkaisut/open-calls",
]

RFI_KEYWORDS = {"rfi", "request for information", "open call", "expression of interest", "haku"}


class BusinessFinlandScraper(BaseScraper):
    SOURCE_NAME  = "BusinessFinland"
    BASE_URL     = BASE
    POLITE_DELAY = 1.5

    def scrape(self) -> Iterator[dict]:
        seen = set()
        for url in PAGES:
            try:
                resp = self._get(url)
                soup = BeautifulSoup(resp.text, "lxml")
            except Exception as exc:
                logger.warning("BusinessFinland fetch %s: %s", url, exc)
                continue

            cards = (
                soup.select("article.card, article.funding-card")
                or soup.select("div.listing-item, div.card-item, div.funding-item")
                or soup.select("li.service-item, li.funding-item")
                or soup.select("[class*='card'], [class*='item'], [class*='funding']")
            )

            # fallback: anchors whose text looks like a call
            if not cards:
                cards = [
                    a.find_parent(["li", "div", "article"]) or a
                    for a in soup.find_all("a", href=True)
                    if any(kw in (a.get_text() + a["href"]).lower() for kw in RFI_KEYWORDS)
                ]

            logger.info("BusinessFinland %s: %d items", url, len(cards))
            for card in cards:
                try:
                    rec = self._parse_card(card, url)
                    if rec and rec["external_id"] not in seen:
                        seen.add(rec["external_id"])
                        yield rec
                except Exception as exc:
                    logger.warning("BusinessFinland card parse: %s", exc)

    def _parse_card(self, card, page_url: str) -> dict | None:
        title_el = card.select_one(
            "h1, h2, h3, h4, .card-title, .title, .heading, [class*='title']"
        )
        title = safe_text(title_el) or safe_text(card)[:120]
        if not title:
            return None

        desc_el  = card.select_one("p, .description, .card-body, .summary, .lead")
        desc     = safe_text(desc_el)

        link_el  = card.select_one("a[href]")
        if link_el:
            href = link_el["href"]
            url  = href if href.startswith("http") else BASE + href
        else:
            url = page_url

        date_el  = card.select_one("time, .date, .deadline, [class*='date']")
        dead_str = date_el.get("datetime") or safe_text(date_el) if date_el else ""

        uid = hashlib.md5((title + url).encode()).hexdigest()[:20]
        full_text = f"{title} {desc} Finland"

        rec = self._base_record()
        rec.update({
            "external_id":  uid,
            "type":         "RFI",
            "status":       "OPEN",
            "title":        title[:1000],
            "description":  desc,
            "source_url":   url,
            "company_size": classify_company_size(full_text),
            "deadline_date": parse_date(dead_str),
            "keywords":     extract_keywords(full_text),
            "raw_data":     {"text": card.get_text(separator=" ", strip=True)[:1500]},
        })
        rec["industry_area_id"] = self._industry_id(classify_industry(full_text))
        rec["location_id"]      = self._location_id(classify_location("Finland " + full_text))
        return rec
