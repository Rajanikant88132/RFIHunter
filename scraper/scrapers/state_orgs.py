"""
Scraper: Finnish State Organisations — procurement pages.

Source list from RFI_RFP_website.md (items 52-70):
  Kela, Vero, DVV, Valtiokonttori, Väylävirasto, Traficom,
  Business Finland, PRH, Statistics Finland, FMI, Syke,
  Finnish Food Authority, Fimea, THL, TTHL, Immigration Service,
  National Archives, OPH, and others.

Also covers State-Owned Companies (items 71-85):
  Finavia, Fintraffic, Fingrid, Posti, VR Group, Gasgrid,
  Fortum, Helen, CSC, Senaatti, Motiva, Finnvera.
"""
import hashlib
import logging
from typing import Iterator

from bs4 import BeautifulSoup

from scrapers.base import BaseScraper, parse_date, safe_text
from classifier import classify_industry, classify_company_size, extract_keywords

logger = logging.getLogger(__name__)

STATE_SOURCES = [
    # Finnish state agencies (items 52-70)
    ("Kela",                             "Nationwide", "https://www.kela.fi/fi/hankintailmoitukset"),
    ("Finnish Tax Administration",       "Nationwide", "https://www.vero.fi/tietoa-verohallinnosta/tietoa_verohallinnosta/hankinnat/"),
    ("DVV",                              "Nationwide", "https://dvv.fi/fi/dvv/hankinnat"),
    ("Valtiokonttori",                   "Helsinki",   "https://www.valtiokonttori.fi/palvelut/hankinnat/"),
    ("Väylävirasto",                     "Nationwide", "https://vayla.fi/fi/hankinnat"),
    ("Traficom",                         "Nationwide", "https://www.traficom.fi/en/about-traficom/procurement"),
    ("Business Finland",                 "Helsinki",   "https://www.businessfinland.fi/en/for-finnish-companies/services"),
    ("PRH",                              "Helsinki",   "https://www.prh.fi/fi/prhsta/hankinnat.html"),
    ("Statistics Finland",               "Helsinki",   "https://stat.fi/org/hankinnat/index.html"),
    ("Finnish Meteorological Institute", "Helsinki",   "https://www.ilmatieteenlaitos.fi/hankinnat"),
    ("Syke",                             "Helsinki",   "https://www.syke.fi/fi-FI/Toimintamahdollisuudet/Hankinnat"),
    ("THL",                              "Helsinki",   "https://thl.fi/fi/thl/hankinnat"),
    ("Finnish Immigration Service",      "Helsinki",   "https://migri.fi/fi/hankinnat"),
    ("OPH",                              "Helsinki",   "https://www.oph.fi/fi/opetushallitus/hankinnat"),
    # State-owned companies (items 71-85)
    ("Finavia",                          "Helsinki",   "https://www.finavia.fi/fi/finavia-yrityksena/hankinnat"),
    ("Fintraffic",                       "Nationwide", "https://www.fintraffic.fi/fi/fintraffic/hankinnat"),
    ("Fingrid",                          "Nationwide", "https://www.fingrid.fi/fi/fingrid/hankinnat/"),
    ("VR Group",                         "Helsinki",   "https://www.vr.fi/fi/vr-group/hankinnat"),
    ("Posti",                            "Nationwide", "https://www.posti.com/fi/posti-group/hankinnat"),
    ("CSC",                              "Espoo",      "https://csc.fi/fi/csc/hankinnat"),
    ("Senaatti-kiinteistot",             "Nationwide", "https://www.senaatti.fi/fi/hankinnat"),
    ("Motiva",                           "Helsinki",   "https://www.motiva.fi/fi/hankinnat"),
    ("Finnvera",                         "Nationwide", "https://www.finnvera.fi/finnvera/hankinnat"),
]

PROCUREMENT_KW = {
    "hankinta", "kilpailutus", "tarjouspyynto", "tarjouspyyntö",
    "procurement", "tender", "rfp", "tietopyynto", "tietopyyntö",
}


class StateOrgsScraper(BaseScraper):
    SOURCE_NAME  = "StateOrgs"
    POLITE_DELAY = 2.0

    def scrape(self) -> Iterator[dict]:
        seen = set()
        for authority_name, location, url in STATE_SOURCES:
            try:
                yield from self._scrape_page(url, authority_name, location, seen)
            except Exception as exc:
                logger.warning("StateOrg %s: %s", authority_name, exc)

    def _scrape_page(self, url: str, authority_name: str, location: str, seen: set) -> Iterator[dict]:
        try:
            resp = self._get(url)
            soup = BeautifulSoup(resp.text, "lxml")
        except Exception as exc:
            logger.warning("StateOrg %s: %s", url, exc)
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

        logger.info("StateOrg %s: %d items", authority_name, len(items))
        for item in items:
            try:
                rec = self._parse(item, url, authority_name, location)
                if rec and rec["external_id"] not in seen:
                    seen.add(rec["external_id"])
                    yield rec
            except Exception as exc:
                logger.warning("StateOrg item: %s", exc)

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

        is_rfi = any(kw in title.lower() or kw in desc.lower()
                     for kw in ("tietopyynto", "tietopyyntö", "markkinakartoitus",
                                "prior information", "ennakkoilmoitus"))

        uid = hashlib.md5((authority_name + title + url).encode()).hexdigest()[:20]
        full_text = f"{title} {desc} {authority_name} Finland"

        rec = self._base_record()
        rec.update({
            "external_id":           uid,
            "type":                  "RFI" if is_rfi else "RFP",
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
        rec["location_id"]      = self._location_id(location)
        return rec

    @staticmethod
    def _score(full_text: str) -> int:
        score = 48
        text = full_text.lower()
        kws = ["software", "cloud", "ai", "data", "it ", "digital", "platform", "system"]
        score += min(sum(1 for kw in kws if kw in text) * 4, 20)
        return min(score, 100)
