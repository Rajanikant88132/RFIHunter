"""
Scrapers package — all source scrapers ordered by priority.
Priority order from RFI_RFP_website.md:
  1. HILMA (official Finnish API)
  2. TED (EU API)
  3. Cloudia/Tarjouspalvelu (private e-tendering)
  4. Hansel + Hanki (state framework)
  5. Finnish cities (top 20)
  6. Wellbeing counties (21 counties)
  7. State organisations (agencies + state companies)
  8. Universities (top 10)
  9. RSS feeds (supplementary)
"""
from .hilma          import HilmaScraper
from .ted            import TEDScraper
from .cloudia        import CloudiaScraper
from .hansel         import HanselScraper
from .cities         import FinnishCitiesScraper
from .wellbeing      import WellbeingCountiesScraper
from .state_orgs     import StateOrgsScraper
from .universities   import UniversitiesScraper
from .rss_feeds      import RSSFeedScraper

ALL_SCRAPERS = [
    HilmaScraper,             # 1. HILMA — official Finnish procurement API
    TEDScraper,               # 2. TED   — EU procurement API, Finland filter
    CloudiaScraper,           # 3. Cloudia/Tarjouspalvelu — e-tendering platform
    HanselScraper,            # 4. Hansel + Hanki — state framework agreements
    FinnishCitiesScraper,     # 5. Top 20 Finnish cities
    WellbeingCountiesScraper, # 6. 21 wellbeing services counties
    StateOrgsScraper,         # 7. State agencies + state-owned companies
    UniversitiesScraper,      # 8. Top 10 Finnish universities
    RSSFeedScraper,           # 9. RSS/Atom feeds (Hansel, Tukes, Motiva etc.)
]
