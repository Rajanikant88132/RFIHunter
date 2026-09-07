"""
Scraper: Hankintailmoitukset.fi — Finnish procurement notices (HTML).

The site lists public procurement notices from Finnish contracting authorities.
URL: https://www.hankintailmoitukset.fi/fi/notice/list

Robustness improvements:
  - Multiple CSS selector fallbacks for each field
  - Hash-based deduplication when no id attribute is present
  - Deadline-date detection from multiple table columns
"""
import hashlib
import logging
from typing import Iterator

from bs4 import BeautifulSoup

from scrapers.base import BaseScraper, parse_date, safe_text
from classifier import classify_industry, classify_location, classify_company_size, extract_keywords

logger = logging.getLogger(__name__)

BASE   = "https://www.hankintailmoitukset.fi"
LIST   = f"{BASE}/fi/notice/list"


class HankintaScraper(BaseScraper):
    SOURCE_NAME  = "Hankintailmoitukset"
    BASE_URL     = BASE
    POLITE_DELAY = 1.5

    def scrape(self) -> Iterator[dict]:
        page = 1
        max_empty = 3
        empty_streak = 0

        while True:
            try:
                resp = self._get(LIST, params={"page": page, "limit": 25})
                soup = BeautifulSoup(resp.text, "lxml")
            except Exception as exc:
                logger.error("Hankinta page %d: %s", page, exc)
                break

            rows = (
                soup.select("table.notice-list tbody tr")
                or soup.select("tr[data-id]")
                or soup.select("div[data-notice-id]")
                or soup.select("li.notice-row")
                or soup.select("article.notice")
                # last-resort: any table row with a link
                or [
                    tr for tr in soup.select("tbody tr")
                    if tr.find("a", href=True)
                ]
            )

            if not rows:
                empty_streak += 1
                logger.info("Hankinta: no rows page %d (streak %d)", page, empty_streak)
                if empty_streak >= max_empty:
                    break
                page += 1
                continue

            empty_streak = 0
            for row in rows:
                try:
                    rec = self._parse_row(row)
                    if rec:
                        yield rec
                except Exception as exc:
                    logger.warning("Hankinta row parse: %s", exc)

            # next page
            next_btn = soup.select_one(
                "a[aria-label='Next'], a[rel='next'], "
                "li.next a, a.pagination-next, .next-page a"
            )
            if not next_btn:
                break
            page += 1

    def _parse_row(self, row) -> dict | None:
        tds = row.select("td")

        # --- title + link ---
        title_el = (
            row.select_one("td.title a, .notice-title a, a.notice-link")
            or row.select_one("a[href]")
        )
        title = safe_text(title_el) if title_el else safe_text(row)[:120]
        if not title:
            return None

        url = ""
        if title_el and title_el.get("href"):
            href = title_el["href"]
            url  = href if href.startswith("http") else BASE + href

        # --- authority ---
        auth_el = row.select_one(
            "td.authority, .contracting-authority, .buyer-name, td:nth-child(2)"
        )
        authority = safe_text(auth_el)

        # --- notice type ---
        type_el  = row.select_one("td.type, .notice-type, .badge, td:nth-child(3)")
        type_str = safe_text(type_el).upper()

        # --- dates (look for anything that looks like a date in tds) ---
        pub_date  = None
        dead_date = None
        for td in tds:
            txt = safe_text(td)
            d   = parse_date(txt)
            if d:
                if pub_date is None:
                    pub_date = d
                else:
                    dead_date = d
                    break

        # --- unique id ---
        raw_id = row.get("data-id") or row.get("data-notice-id") or ""
        uid = str(raw_id) if raw_id else hashlib.md5((title + url).encode()).hexdigest()[:20]

        full_text = f"{title} {authority}"

        rec = self._base_record()
        rec.update({
            "external_id":           uid,
            "type": (
                "RFI" if any(k in type_str for k in ("PRIOR", "RFI", "ENNAKKOILMOITUS"))
                else "RFP" if any(k in type_str for k in ("CONTRACT", "RFP", "HANKINTA"))
                else "OTHER"
            ),
            "status":                "OPEN",
            "title":                 title[:1000],
            "description":           title,
            "contracting_authority": authority[:500],
            "company_size":          classify_company_size(full_text),
            "published_date":        pub_date,
            "deadline_date":         dead_date,
            "source_url":            url or LIST,
            "keywords":              extract_keywords(full_text),
            "raw_data":              {"row_text": row.get_text(separator=" ", strip=True)[:1000]},
        })
        rec["industry_area_id"] = self._industry_id(classify_industry(full_text))
        rec["location_id"]      = self._location_id(classify_location(full_text))
        return rec
