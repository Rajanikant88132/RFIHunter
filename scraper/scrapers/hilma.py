"""
Scraper: HILMA — Finland's official public procurement notice service.

Source: https://www.hankintailmoitukset.fi/
Search APIs (public, no auth required):
  - /search/notices      — legacy notices (pre-eForms)
  - /search/eformnotices — newer eForms-based notices (richer data)

Both endpoints discovered from the app config embed at /fi/notice/list.

mainType values:
  PriorInformationNotices    → RFI (ennakkoilmoitus / tietopyyntö)
  ContractNotices            → RFP (tarjouspyyntö / hankintailmoitus)
  ContractAwardNotices       → Awarded (stored as OTHER)
  DesignContestNotices       → RFP
  SocialContractNotices      → RFP

PDF / document links:
  - eFormnotices: procurementDocumentsUrl (link to procurement portal)
  - legacy notices: no direct PDF field — source URL used instead

Buyer contact:
  - eFormnotices: scraped from contactPointEmail / contactPersonName fields
  - TED XML: touchpoint-email-buyer (fetched by TED scraper)
"""
import hashlib
import logging
from typing import Iterator, Optional

from scrapers.base import BaseScraper, parse_date, safe_text
from classifier import classify_industry, classify_location, classify_company_size, extract_keywords

logger = logging.getLogger(__name__)

HILMA_NOTICES  = "https://www.hankintailmoitukset.fi/search/notices"
HILMA_EFORMS   = "https://www.hankintailmoitukset.fi/search/eformnotices"
HILMA_NOTICE   = "https://www.hankintailmoitukset.fi/fi/notice/{}"

# mainType → tender type
_RFI_TYPES = {"PriorInformationNotices", "PriorInformation"}
_RFP_TYPES = {
    "ContractNotices", "ContractNotice",
    "DesignContestNotices", "DesignContest",
    "SocialContractNotices",
}

# NUTS code prefix → city
_NUTS_MAP = {
    "FI1C1": "Helsinki", "FI1C2": "Espoo",  "FI1C3": "Vantaa",
    "FI1D1": "Tampere",  "FI1D2": "Lahti",  "FI1B1": "Turku",
    "FI1A1": "Oulu",     "FI193": "Jyväskylä", "FI1E1": "Kuopio",
    "FI1F1": "Joensuu",  "FI200": "Rovaniemi",
    "FI1D3": "Tampere",  "FI1D4": "Tampere",
    "FI1D8": "Tampere",
}


class HilmaScraper(BaseScraper):
    SOURCE_NAME  = "HILMA"
    BASE_URL     = "https://www.hankintailmoitukset.fi"
    POLITE_DELAY = 0.8

    def scrape(self) -> Iterator[dict]:
        """
        Scrape both legacy notices and eForms notices.
        eForms endpoint is scraped first (richer data: PDFs, contact info).
        """
        logger.info("HILMA: scraping eForms notices (richer data)")
        yield from self._paginate(HILMA_EFORMS, is_eforms=True)

        logger.info("HILMA: scraping legacy notices")
        yield from self._paginate(HILMA_NOTICES, is_eforms=False)

    def _paginate(self, endpoint: str, is_eforms: bool) -> Iterator[dict]:
        page, page_size = 1, 50
        seen: set = set()
        empty_streak = 0

        while True:
            params = {"pageSize": page_size, "page": page}
            try:
                resp = self._get(endpoint, params=params)
                data = resp.json()
            except Exception as exc:
                logger.error("HILMA %s page %d: %s", endpoint, page, exc)
                break

            notices = data.get("value") or []
            if not notices:
                empty_streak += 1
                if empty_streak >= 2:
                    logger.info("HILMA %s: no more results after page %d", endpoint, page)
                    break
                page += 1
                continue

            empty_streak = 0
            for n in notices:
                uid = str(n.get("noticeNumber") or n.get("id") or
                          hashlib.md5(str(n).encode()).hexdigest()[:16])
                if uid in seen:
                    continue
                seen.add(uid)
                try:
                    yield self._parse(n, is_eforms=is_eforms)
                except Exception as exc:
                    logger.warning("HILMA parse (%s): %s | %.80s",
                                   "eform" if is_eforms else "legacy", exc, str(n)[:80])

            if len(notices) < page_size:
                break
            page += 1

    def _parse(self, n: dict, is_eforms: bool = False) -> dict:
        rec = self._base_record()

        notice_id = str(n.get("noticeNumber") or n.get("id") or
                        hashlib.md5(str(n).encode()).hexdigest()[:16])

        # ─ Type ─
        main_type = str(n.get("mainType") or "")
        tender_type = (
            "RFI" if main_type in _RFI_TYPES else
            "RFP" if main_type in _RFP_TYPES else "OTHER"
        )

        # ─ Title (eforms has fi/sv/en variants) ─
        if is_eforms:
            title = safe_text(
                n.get("titleFi") or n.get("titleEn") or n.get("titleSv") or ""
            )
            desc = safe_text(
                n.get("descriptionFi") or n.get("descriptionEn") or n.get("descriptionSv") or ""
            )
            authority = safe_text(
                n.get("organisationNameFi") or n.get("organisationNameEn") or
                n.get("organisationNameSv") or ""
            )
        else:
            title     = safe_text(n.get("projectTitle") or n.get("projectTitleNormalized") or "")
            desc      = safe_text(n.get("projectShortDescription") or n.get("objectDescriptions") or "")
            authority = safe_text(n.get("organisationName") or "")

        # ─ CPV ─
        cpv_raw  = n.get("cpvCodes") or ""
        cpv_list = []
        for part in str(cpv_raw).split():
            code = part.strip()
            if code and code[:2].isdigit() and len(code) >= 8:
                cpv_list.append(code[:8])

        # ─ Dates ─
        pub_str  = str(n.get("datePublished") or "")[:10]
        dead_str = str(
            n.get("deadline") or
            n.get("tendersOrRequestsToParticipateDueDateTime") or
            n.get("expirationDate") or ""
        )[:10]

        # ─ Location ─
        nuts_raw = str(n.get("nutsCodes") or n.get("organisationNutsCode") or "").strip()
        city = ""
        for code in nuts_raw.split():
            city = _NUTS_MAP.get(code[:5], "")
            if city:
                break
        loc_hint = city or authority

        # ─ Status ─
        cancelled = n.get("isCancelled", False)
        deadline  = parse_date(dead_str)
        from datetime import date as _date
        if cancelled:
            status = "CLOSED"
        elif deadline and deadline < _date.today():
            status = "CLOSED"
        else:
            status = "OPEN"

        # ─ Estimated value ─
        est_val  = n.get("estimatedValue") or 0.0
        currency = n.get("currency") or "EUR"

        # ─ PDF / document links ─
        pdf_list = self._extract_pdfs(n, notice_id, is_eforms)

        # ─ Buyer contact ─
        buyer_email, buyer_phone = self._extract_contact(n, is_eforms)

        full_text = f"{title} {desc} {authority} {loc_hint} Finland"
        opp_score = self._score(full_text, cpv_list, dead_str)

        rec.update({
            "external_id":           notice_id,
            "type":                  tender_type,
            "status":                status,
            "title":                 title[:1000] or "Untitled",
            "description":           desc,
            "contracting_authority": authority[:500],
            "company_size":          classify_company_size(full_text),
            "published_date":        parse_date(pub_str),
            "deadline_date":         deadline,
            "estimated_value":       float(est_val) if est_val else None,
            "currency":              currency,
            "source_url":            HILMA_NOTICE.format(notice_id),
            "cpv_codes":             cpv_list or None,
            "keywords":              extract_keywords(full_text),
            "buyer_email":           buyer_email,
            "buyer_phone":           buyer_phone,
            "pdf_urls":              pdf_list or None,
            "opportunity_score":     opp_score,
            "raw_data":              n,
        })
        rec["industry_area_id"] = self._industry_id(classify_industry(full_text))
        rec["location_id"]      = self._location_id(classify_location(loc_hint or "Finland"))
        return rec

    # ── helpers ───────────────────────────────────────────────────────────────

    @staticmethod
    def _extract_pdfs(n: dict, notice_id: str, is_eforms: bool) -> list:
        """
        Build a list of {"name": str, "url": str} PDF/document entries.

        eForms: procurementDocumentsUrl = link to procurement portal (Tarjouspalvelu, etc.)
        Legacy: use the HILMA notice page URL as the canonical link.
        """
        pdfs = []

        if is_eforms:
            doc_url = n.get("procurementDocumentsUrl") or ""
            if doc_url and doc_url.startswith("http"):
                pdfs.append({"name": "Procurement Documents", "url": doc_url})

        # Always add HILMA notice page as a viewable entry
        hilma_url = HILMA_NOTICE.format(notice_id)
        pdfs.append({"name": "HILMA Notice", "url": hilma_url})

        # eForm linked notices (corrigenda, award notices, etc.)
        linked = n.get("linkedNotices") or []
        if isinstance(linked, list):
            for lnk in linked[:3]:
                if isinstance(lnk, dict):
                    lnk_id  = lnk.get("noticeNumber") or lnk.get("id") or ""
                    lnk_type = lnk.get("mainType") or "Notice"
                    if lnk_id:
                        pdfs.append({
                            "name": f"Linked: {lnk_type}",
                            "url":  HILMA_NOTICE.format(lnk_id),
                        })

        return pdfs

    @staticmethod
    def _extract_contact(n: dict, is_eforms: bool) -> tuple:
        """Return (email, phone) for the contracting authority contact point."""
        email = None
        phone = None

        if is_eforms:
            # eForms notices store contact in lots[].contactPoint or top-level fields
            lots = n.get("lots") or []
            if isinstance(lots, list) and lots:
                lot = lots[0] if isinstance(lots[0], dict) else {}
                email = lot.get("contactPointEmail") or lot.get("contactEmail")
                phone = lot.get("contactPointPhone") or lot.get("contactPhone")

            # Fall back to top-level contact fields
            if not email:
                email = (n.get("contactPointEmail") or n.get("contactEmail") or
                         n.get("buyerEmail") or None)
            if not phone:
                phone = (n.get("contactPointPhone") or n.get("contactPhone") or
                         n.get("buyerPhone") or None)

        return (email, phone)

    @staticmethod
    def _score(full_text: str, cpv_list: list, deadline_str: str) -> int:
        score = 40
        text = full_text.lower()
        tech_kw = ["software", "cloud", "ai ", "data", "it ", "ict", "digital",
                   "platform", "cyber", "api", "integration", "erp", "saas"]
        score += min(sum(1 for kw in tech_kw if kw in text) * 5, 30)
        if any(str(c)[:2] in {"72", "48", "73", "38"} for c in (cpv_list or [])):
            score += 15
        deadline = parse_date(deadline_str)
        if deadline:
            from datetime import date as _date
            days = (deadline - _date.today()).days
            score += 10 if days > 14 else (5 if days > 0 else 0)
        if any(kw in text for kw in ["rfi", "tietopyynto", "markkinakartoitus",
                                      "market consultation", "prior information",
                                      "ennakkoilmoitus"]):
            score += 5
        return min(score, 100)
