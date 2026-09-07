"""
Scraper: TED (Tenders Electronic Daily) — EU procurement, Finland filter.

Source: https://docs.ted.europa.eu/api/latest/search.html

TED API v3 uses POST with a JSON body containing:
  - query:    expert-search query string
  - fields:   list of fields to return
  - page:     1-based page number
  - pageSize: results per page

Correct expert-query syntax for Finland:
  ND=[FI*]   — notice ID starting with FI (country prefix)
  PC=[72*]   — CPV codes starting with 72 (IT services)

Fields documentation:
  ND  = Notice number
  TI  = Title
  CA  = Contracting authority
  TD  = Document type (notice type)
  DD  = Deadline for submission
  DT  = Date of dispatch
  PC  = CPV codes
  OJ_S = OJ supplement reference (publication date)
  IA  = Information about lots
  AU  = Additional description
"""
import logging
from typing import Iterator

from scrapers.base import BaseScraper, parse_date, safe_text
from classifier import classify_industry, classify_location, classify_company_size, extract_keywords

logger = logging.getLogger(__name__)

TED_SEARCH = "https://api.ted.europa.eu/v3/notices/search"
TED_DETAIL = "https://ted.europa.eu/en/notice/-/detail/{}"

# notice-type values → tender type
# pin-rtl / pin-only = Prior Information Notice (RFI)
# cn-standard / cn-social / cn-defen-serv / subco = Contract Notice (RFP)
_RFI_NOTICE_TYPES = {"pin-rtl", "pin-only", "pin-buyer", "pin-cfc-social", "pin-cfc-standard"}
_RFP_NOTICE_TYPES = {
    "cn-standard", "cn-social", "cn-defen-serv", "subco",
    "cn-utilities", "cn-op-def", "cn-oth-def",
}

# Fields supported by TED v3 API (confirmed from error response)
# "links" contains pdf/html/xml URLs for the notice in all EU languages
# "buyer-email" and "touchpoint-email-buyer" carry the contact email
_FIELDS = [
    "ND", "notice-title", "notice-type", "buyer-name", "deadline",
    "publication-date", "classification-cpv", "description-lot",
    "description-part", "buyer-country", "organisation-country-buyer",
    "buyer-city", "links", "buyer-email", "touchpoint-email-buyer",
    "buyer-touchpoint-email",
]


class TEDScraper(BaseScraper):
    SOURCE_NAME  = "TED"
    BASE_URL     = "https://ted.europa.eu"
    POLITE_DELAY = 0.8

    def scrape(self) -> Iterator[dict]:
        """
        TED v3 API: POST JSON body.
        Correct query for Finland: buyer-country=FIN
        (verified working — returns Finnish notices including CPV, title, deadline)
        """
        page = 1
        page_size = 50

        while True:
            body = {
                "query":  "buyer-country=FIN",
                "fields": _FIELDS,
                "page":   page,
                "limit":  page_size,
            }
            try:
                resp = self._post(TED_SEARCH, json=body)
                data = resp.json()
            except Exception as exc:
                logger.error("TED page %d: %s", page, exc)
                break

            notices = data.get("notices") or data.get("results") or []
            if not notices:
                logger.info("TED: no more results at page %d", page)
                break

            for n in notices:
                try:
                    yield self._parse(n)
                except Exception as exc:
                    logger.warning("TED parse: %s | %.80s", exc, str(n)[:80])

            total = (
                data.get("totalNoticeCount") or data.get("total")
                or data.get("totalElements") or 0
            )
            if not total or page * page_size >= int(total):
                break
            page += 1

    def _parse(self, n: dict) -> dict:
        rec = self._base_record()

        notice_id    = str(n.get("ND") or n.get("publication-number") or "")
        notice_type  = str(n.get("notice-type") or "")

        # Title: {"eng": ["..."]} or {"fin": ["..."]}
        title     = self._pick_lang(n.get("notice-title") or {})
        desc      = self._pick_lang(n.get("description-lot") or n.get("description-part") or {})
        authority = self._pick_lang(n.get("buyer-name") or {})
        city      = self._pick_lang(n.get("buyer-city") or {})

        # CPV: list of "45000000" strings
        cpv_raw  = n.get("classification-cpv") or []
        cpv_list = list(cpv_raw) if isinstance(cpv_raw, list) else [str(cpv_raw)] if cpv_raw else []

        pub_str  = str(n.get("publication-date") or "")[:10]
        dead_str = str(n.get("deadline") or "")[:10]

        # ─ PDF links ─ (links.pdf contains per-language PDF URLs)
        pdf_list = self._extract_pdfs(n, notice_id)

        # ─ Buyer contact ─
        buyer_email = self._extract_email(n)

        full_text = f"{title} {desc} {authority} {city} Finland"

        rec.update({
            "external_id":           notice_id,
            "type":                  ("RFI" if notice_type in _RFI_NOTICE_TYPES
                                      else "RFP" if notice_type in _RFP_NOTICE_TYPES
                                      else "OTHER"),
            "status":                "OPEN",
            "title":                 safe_text(title)[:1000] or notice_id,
            "description":           safe_text(desc),
            "contracting_authority": safe_text(authority)[:500],
            "company_size":          classify_company_size(full_text),
            "published_date":        parse_date(pub_str),
            "deadline_date":         parse_date(dead_str),
            "source_url":            TED_DETAIL.format(notice_id),
            "cpv_codes":             cpv_list or None,
            "keywords":              extract_keywords(full_text),
            "buyer_email":           buyer_email,
            "buyer_phone":           None,   # TED API does not expose phone number
            "pdf_urls":              pdf_list or None,
            "opportunity_score":     self._score(full_text, cpv_list),
            "raw_data":              n,
        })
        rec["industry_area_id"] = self._industry_id(classify_industry(full_text))
        rec["location_id"]      = self._location_id(classify_location(city or "Finland"))
        return rec

    @staticmethod
    def _extract_pdfs(n: dict, notice_id: str) -> list:
        """
        Build PDF entries from TED notice links.
        links.pdf = {"ENG": "https://...", "FIN": "https://...", ...}
        We prefer English, then Finnish, then first available.
        Also add the HTML notice page link.
        """
        pdfs = []
        links = n.get("links") or {}
        pdf_langs = links.get("pdf") or {}

        if isinstance(pdf_langs, dict):
            # Prefer English, then Finnish
            for lang in ("ENG", "FIN", "FRA", "DEU"):
                url = pdf_langs.get(lang) or pdf_langs.get(lang.lower())
                if url:
                    pdfs.append({"name": f"Official Notice PDF ({lang})", "url": url})
                    break
            # Also add Finnish version if available and not already added
            if pdf_langs.get("FIN") and (not pdfs or pdfs[0]["url"] != pdf_langs["FIN"]):
                pdfs.append({"name": "Official Notice PDF (Finnish)", "url": pdf_langs["FIN"]})

        # HTML notice page
        html_langs = links.get("html") or {}
        if isinstance(html_langs, dict):
            html_url = (html_langs.get("ENG") or html_langs.get("FIN") or
                        next(iter(html_langs.values()), None))
            if html_url:
                pdfs.append({"name": "TED Notice (HTML)", "url": html_url})
        else:
            pdfs.append({"name": "TED Notice", "url": TED_DETAIL.format(notice_id)})

        return pdfs

    @staticmethod
    def _extract_email(n: dict) -> str:
        """Extract buyer contact email from various TED field names."""
        for field in ("buyer-email", "touchpoint-email-buyer", "buyer-touchpoint-email"):
            val = n.get(field)
            if not val:
                continue
            # Field may be a string, list, or dict
            if isinstance(val, str) and "@" in val:
                return val
            if isinstance(val, list):
                for v in val:
                    if isinstance(v, str) and "@" in v:
                        return v
            if isinstance(val, dict):
                for v in val.values():
                    if isinstance(v, str) and "@" in v:
                        return v
        return None

    @staticmethod
    def _pick_lang(obj) -> str:
        """Extract English or Finnish text from TED multilingual dicts like {"eng": ["text"]}."""
        if not obj:
            return ""
        if isinstance(obj, dict):
            for lang in ("ENG", "FIN", "eng", "fin", "EN", "FI", "en", "fi"):
                val = obj.get(lang)
                if val:
                    if isinstance(val, list):
                        return " ".join(str(v) for v in val if v)
                    return str(val)
            # fallback: first value
            first = next(iter(obj.values()), "")
            if isinstance(first, list):
                return " ".join(str(v) for v in first if v)
            return str(first) if first else ""
        if isinstance(obj, list):
            return " ".join(str(v) for v in obj if v)
        return str(obj)

    @staticmethod
    def _score(full_text: str, cpv_list: list) -> int:
        score = 45
        text = full_text.lower()
        tech_kw = ["software", "cloud", "ai ", "data", "it ", "ict", "digital", "platform"]
        score += min(sum(1 for kw in tech_kw if kw in text) * 5, 25)
        if any(str(c)[:2] in {"72", "48", "73"} for c in (cpv_list or [])):
            score += 15
        return min(score, 100)
