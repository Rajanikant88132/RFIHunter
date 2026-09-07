"""
RFI Hunter — Base scraper class.
All source scrapers extend this.

Improvements over v1:
  - Safe UA fallback (fake-useragent can fail on first boot)
  - Per-domain polite delay config
  - Separate _post() helper with same retry logic
  - _safe_text() helper to strip excess whitespace from HTML elements
  - parse_date() promoted to base so every subclass can use it
"""
import logging
import re
import time
from abc import ABC, abstractmethod
from datetime import date
from typing import Iterator, Optional

import requests
from tenacity import retry, stop_after_attempt, wait_exponential, before_sleep_log

logger = logging.getLogger(__name__)

# UA pool – always use these directly to avoid fake-useragent network calls at runtime
_FALLBACK_UAS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 "
    "(KHTML, like Gecko) Version/17.4.1 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64; rv:125.0) Gecko/20100101 Firefox/125.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:126.0) Gecko/20100101 Firefox/126.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_5) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
]
_ua_index = 0


def _next_ua() -> str:
    """Return the next UA from the pool — no external network calls."""
    global _ua_index
    ua = _FALLBACK_UAS[_ua_index % len(_FALLBACK_UAS)]
    _ua_index += 1
    return ua


_DATE_FMTS = (
    "%Y-%m-%dT%H:%M:%S",
    "%Y-%m-%dT%H:%M",
    "%Y-%m-%d",
    "%d.%m.%Y",
    "%d/%m/%Y",
    "%Y/%m/%d",
)


def parse_date(s) -> Optional[date]:
    """Parse any common date string to a date object, or return None."""
    if not s:
        return None
    s = str(s).strip()
    for fmt in _DATE_FMTS:
        try:
            return __import__("datetime").datetime.strptime(s[: len(fmt)], fmt).date()
        except (ValueError, TypeError):
            continue
    return None


def safe_text(el, default: str = "") -> str:
    """Get clean text from a BeautifulSoup element (or plain string)."""
    if el is None:
        return default
    if isinstance(el, str):
        return re.sub(r"\s+", " ", el).strip()
    return re.sub(r"\s+", " ", el.get_text(separator=" ")).strip()


class BaseScraper(ABC):
    SOURCE_NAME: str = "base"
    BASE_URL: str = ""
    POLITE_DELAY: float = 1.2   # seconds between requests; override per scraper

    def __init__(self, session: requests.Session = None):
        self.session = session or self._make_session()

    # ── session ──────────────────────────────────────────────────────────────

    @staticmethod
    def _make_session() -> requests.Session:
        s = requests.Session()
        s.headers.update({
            "Accept":          "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9,fi;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection":      "keep-alive",
        })
        return s

    def _set_ua(self):
        self.session.headers["User-Agent"] = _next_ua()

    # ── HTTP helpers ──────────────────────────────────────────────────────────

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        reraise=True,
    )
    def _get(self, url: str, **kwargs) -> requests.Response:
        self._set_ua()
        resp = self.session.get(url, timeout=20, **kwargs)
        resp.raise_for_status()
        time.sleep(self.POLITE_DELAY)
        return resp

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        reraise=True,
    )
    def _post(self, url: str, **kwargs) -> requests.Response:
        self._set_ua()
        resp = self.session.post(url, timeout=20, **kwargs)
        resp.raise_for_status()
        time.sleep(self.POLITE_DELAY)
        return resp

    # ── abstract interface ────────────────────────────────────────────────────

    @abstractmethod
    def scrape(self) -> Iterator[dict]:
        """Yield normalised tender dicts ready for db.upsert_tender()."""
        ...

    # ── helpers shared by all subclasses ─────────────────────────────────────

    def _base_record(self) -> dict:
        return {
            "external_id":           None,
            "source":                self.SOURCE_NAME,
            "type":                  "OTHER",
            "status":                "UNKNOWN",
            "title":                 "",
            "description":           "",
            "contracting_authority": None,
            "company_size":          "ANY",
            "industry_area_id":      None,
            "location_id":           None,
            "published_date":        None,
            "deadline_date":         None,
            "estimated_value":       None,
            "currency":              "EUR",
            "source_url":            "",
            "cpv_codes":             None,
            "keywords":              None,
            # buyer contact info
            "buyer_email":           None,
            "buyer_phone":           None,
            # PDF / document attachments: list of {"name": str, "url": str}
            "pdf_urls":              None,
            "opportunity_score":     0,
            "raw_data":              None,
        }

    @staticmethod
    def _resolve(name: str, kind: str):
        from db import resolve_industry_id, resolve_location_id
        return resolve_industry_id(name) if kind == "industry" else resolve_location_id(name)

    # convenience wrappers
    def _industry_id(self, name: str): return self._resolve(name, "industry")
    def _location_id(self, name: str): return self._resolve(name, "location")

    @staticmethod
    def _parse_date(s) -> Optional[date]:
        return parse_date(s)
