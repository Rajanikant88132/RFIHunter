"""
Scraper: Julkiset.fi — Finnish public-sector procurement portal.

Julkiset.fi is operated by the Finnish Government Shared Services Centre (Palkeet)
and lists procurement notices across all Finnish ministries and agencies.
URL: https://www.julkiset.fi/kilpailutukset/
"""
import hashlib
import logging
from typing import Iterator

from bs4 import BeautifulSoup

from scrapers.base import BaseScraper, parse_date, safe_text
from classifier import classify_industry, classify_location, classify_company_size, extract_keywords

logger = logging.getLogger(__name__)

BASE      = "https://www.julkiset.fi"
LIST_URL  = f"{BASE}/tarjouskilpailut/"       # current Finnish URL
LIST_EN   = f"{BASE}/en/tenders/"             # current English URL


class JulkisetScraper(BaseScraper):
    SOURCE_NAME  = "Julkiset"
    BASE_URL     = BASE
    POLITE_DELAY = 1.5

    def scrape(self) -> Iterator[dict]:
        seen = set()
        for start_url in (LIST_URL, LIST_EN):
            yield from self._scrape_listing(start_url, seen)

    def _scrape_listing(self, start_url: str, seen: set) -> Iterator[dict]:
        page = 1
        empty = 0

        while empty < 3:
            url = start_url if page == 1 else f"{start_url}?page={page}"
            try:
                resp = self._get(url)
                soup = BeautifulSoup(resp.text, "lxml")
            except Exception as exc:
                logger.warning("Julkiset %s page %d: %s", start_url, page, exc)
                break

            items = (
                soup.select("article.procurement, li.procurement-item, div.procurement-item")
                or soup.select("table.tenders tbody tr, .views-row")
                or soup.select("ul.listing li, ol.listing li")
                or [
                    a.find_parent(["li", "div", "tr", "article"]) or a
                    for a in soup.find_all("a", href=True)
                    if "/kilpailutukset/" in a["href"] or "/procurement/" in a["href"]
                ]
            )

            if not items:
                empty += 1
                page += 1
                continue

            empty = 0
            for item in items:
                try:
                    rec = self._parse(item)
                    if rec and rec["external_id"] not in seen:
                        seen.add(rec["external_id"])
                        yield rec
                except Exception as exc:
                    logger.warning("Julkiset parse: %s", exc)

            next_el = soup.select_one("a[rel='next'], a.next, li.pager-next a")
            if not next_el:
                break
            page += 1

    def _parse(self, item) -> dict | None:
        title_el = item.select_one("h1,h2,h3,h4,.title,[class*='title'],a")
        title    = safe_text(title_el) or safe_text(item)[:120]
        if not title or len(title) < 5:
            return None

        link_el = item.select_one("a[href]")
        if link_el:
            href = link_el["href"]
            url  = href if href.startswith("http") else BASE + href
        else:
            url  = LIST_URL

        auth_el    = item.select_one(".authority, .buyer, td:nth-child(2), [class*='auth']")
        authority  = safe_text(auth_el)

        desc_el    = item.select_one("p, .description, .summary")
        desc       = safe_text(desc_el)

        date_el    = item.select_one("time, .date, td.date, [class*='date']")
        date_str   = (date_el.get("datetime") or safe_text(date_el)) if date_el else ""

        uid = hashlib.md5((title + url).encode()).hexdigest()[:20]
        full_text = f"{title} {authority} {desc}"

        rec = self._base_record()
        rec.update({
            "external_id":           uid,
            "type":                  "RFP",
            "status":                "OPEN",
            "title":                 title[:1000],
            "description":           desc,
            "contracting_authority": authority[:500],
            "company_size":          classify_company_size(full_text),
            "published_date":        parse_date(date_str),
            "source_url":            url,
            "keywords":              extract_keywords(full_text),
            "raw_data":              {"text": item.get_text(separator=" ", strip=True)[:1200]},
        })
        rec["industry_area_id"] = self._industry_id(classify_industry(full_text))
        rec["location_id"]      = self._location_id(classify_location(authority + " " + full_text))
        return rec
