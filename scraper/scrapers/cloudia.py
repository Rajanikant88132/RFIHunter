"""
Scraper: Cloudia Tarjouspalvelu — Finland's major private e-tendering platform.

Source: https://tarjouspalvelu.fi  (public tender search, no login required)
Also:   https://www.cloudia.net/fi/

Cloudia/Tarjouspalvelu is the most widely used private procurement portal in Finland.
Many municipalities, hospitals, and companies publish tenders here that don't
appear in HILMA (private sector + some public that prefer Cloudia UI).

Public search URL: https://tarjouspalvelu.fi/tarjouspalvelu?lang=en
API-like JSON endpoint for listing open tenders.
"""
import hashlib
import logging
from typing import Iterator

from bs4 import BeautifulSoup

from scrapers.base import BaseScraper, parse_date, safe_text
from classifier import classify_industry, classify_location, classify_company_size, extract_keywords

logger = logging.getLogger(__name__)

BASE      = "https://tarjouspalvelu.fi"
SEARCH_FI = f"{BASE}/tarjouspalvelu"
SEARCH_EN = f"{BASE}/tarjouspalvelu?lang=fi"  # main listing page

# Tarjouspalvelu also has a JSON listing endpoint
JSON_API  = f"{BASE}/api/notices"

TENDER_KW_FI = {
    "tarjouspyyntö", "tarjouspyynto", "hankinta", "kilpailutus",
    "tietopyyntö", "tietopyynto", "markkinakartoitus",
}


class CloudiaScraper(BaseScraper):
    SOURCE_NAME  = "Cloudia"
    BASE_URL     = BASE
    POLITE_DELAY = 1.5

    def scrape(self) -> Iterator[dict]:
        # Try JSON API first, fall back to HTML
        try:
            yield from self._scrape_json()
            return
        except Exception as exc:
            logger.warning("Cloudia JSON API: %s — trying HTML", exc)
        yield from self._scrape_html()

    def _scrape_json(self) -> Iterator[dict]:
        page = 1
        while True:
            resp = self._get(JSON_API, params={"page": page, "limit": 50, "status": "open"})
            data = resp.json()
            items = data.get("notices") or data.get("results") or data.get("data") or []
            if not items:
                break
            for item in items:
                try:
                    yield self._parse_json(item)
                except Exception as exc:
                    logger.warning("Cloudia JSON parse: %s", exc)
            total = data.get("total") or 0
            if not total or page * 50 >= int(total):
                break
            page += 1

    def _parse_json(self, item: dict) -> dict:
        rec = self._base_record()
        title     = item.get("title") or item.get("subject") or ""
        authority = item.get("buyer") or item.get("organization") or item.get("authority") or ""
        desc      = item.get("description") or item.get("summary") or ""
        notice_id = str(item.get("id") or item.get("noticeId") or hashlib.md5((title+str(item)).encode()).hexdigest()[:16])
        dead_str  = str(item.get("deadline") or item.get("submissionDeadline") or "")
        pub_str   = str(item.get("publishedDate") or item.get("publicationDate") or "")
        url       = item.get("url") or item.get("link") or f"{BASE}/notice/{notice_id}"
        full_text = f"{title} {authority} {desc}"
        rec.update({
            "external_id":           notice_id,
            "type":                  "RFP",
            "status":                "OPEN",
            "title":                 safe_text(title)[:1000],
            "description":           safe_text(desc),
            "contracting_authority": safe_text(authority)[:500],
            "company_size":          classify_company_size(full_text),
            "published_date":        parse_date(pub_str),
            "deadline_date":         parse_date(dead_str),
            "source_url":            url,
            "keywords":              extract_keywords(full_text),
            "opportunity_score":     self._score(full_text),
            "raw_data":              item,
        })
        rec["industry_area_id"] = self._industry_id(classify_industry(full_text))
        rec["location_id"]      = self._location_id(classify_location(authority + " " + full_text))
        return rec

    def _scrape_html(self) -> Iterator[dict]:
        seen = set()
        for url in (SEARCH_EN, SEARCH_FI):
            try:
                resp = self._get(url)
                soup = BeautifulSoup(resp.text, "lxml")
            except Exception as exc:
                logger.warning("Cloudia HTML %s: %s", url, exc)
                continue

            rows = (
                soup.select("table.tenders tbody tr, .tender-row, .notice-row")
                or soup.select("div.tender-item, li.tender, article.tender")
                or [
                    a.find_parent(["li", "div", "tr", "article"]) or a
                    for a in soup.find_all("a", href=True)
                    if "/tarjouspyynto/" in a["href"] or "/notice/" in a["href"]
                ]
            )
            logger.info("Cloudia HTML %s: %d rows", url, len(rows))
            for row in rows:
                try:
                    rec = self._parse_html_row(row)
                    if rec and rec["external_id"] not in seen:
                        seen.add(rec["external_id"])
                        yield rec
                except Exception as exc:
                    logger.warning("Cloudia HTML row: %s", exc)

    def _parse_html_row(self, row) -> dict | None:
        title_el  = row.select_one("a.tender-title, a.notice-link, td.title a, h3 a, h4 a, a[href]")
        title     = safe_text(title_el) or safe_text(row)[:120]
        if not title or len(title) < 5:
            return None

        link_el = row.select_one("a[href]")
        if link_el:
            href = link_el["href"]
            url  = href if href.startswith("http") else BASE + href
        else:
            url = SEARCH_EN

        auth_el   = row.select_one(".buyer, .authority, td:nth-child(2), .organization")
        authority = safe_text(auth_el)
        date_el   = row.select_one("time, .deadline, .date, td.date")
        date_str  = (date_el.get("datetime") or safe_text(date_el)) if date_el else ""

        uid = hashlib.md5((title + url).encode()).hexdigest()[:20]
        full_text = f"{title} {authority}"

        rec = self._base_record()
        rec.update({
            "external_id":           uid,
            "type":                  "RFP",
            "status":                "OPEN",
            "title":                 title[:1000],
            "description":           title,
            "contracting_authority": authority[:500],
            "company_size":          classify_company_size(full_text),
            "deadline_date":         parse_date(date_str),
            "source_url":            url,
            "keywords":              extract_keywords(full_text),
            "opportunity_score":     self._score(full_text),
            "raw_data":              {"text": row.get_text(separator=" ", strip=True)[:800]},
        })
        rec["industry_area_id"] = self._industry_id(classify_industry(full_text))
        rec["location_id"]      = self._location_id(classify_location(authority + " Finland"))
        return rec

    @staticmethod
    def _score(full_text: str) -> int:
        score = 45
        text = full_text.lower()
        kws = ["software", "cloud", "ai", "data", "it ", "digital", "platform"]
        score += min(sum(1 for kw in kws if kw in text) * 5, 25)
        return min(score, 100)
