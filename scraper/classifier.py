"""
RFI Hunter — Classification utilities.
Maps scraped text → industry area, location, company size.
Includes full Finnish terminology from RFI_RFP_website.md.
"""
import re
from typing import Optional

# ── Finnish RFI term detection ────────────────────────────────────────────────
# From RFI_RFP_website.md section on Finnish terminology
RFI_TERMS_FI = {
    "tietopyyntö", "tietopyynto",
    "markkinakartoitus",
    "markkinavuoropuhelu",
    "tekninen vuoropuhelu",
    "ennakkoilmoitus",
    "tekninen dialogi",
    "market consultation",
    "prior information notice",
    "rfi",
}

RFP_TERMS_FI = {
    "tarjouspyyntö", "tarjouspyynto",
    "hankintailmoitus",
    "kilpailutus",
    "osallistumispyyntö", "osallistumispyynto",
    "puitejärjestely", "puitejärjestely",
    "dynaaminen hankintajärjestelmä",
    "dps",
    "contract notice",
    "rfp",
    "rfq",
}

FUTURE_TERMS_FI = {
    "tuleva hankinta",
    "hankintasuunnitelma",
    "kilpailutussuunnitelma",
    "hankintakalenteri",
    "tulevat hankinnat",
    "procurement plan",
    "upcoming procurement",
}


def detect_tender_type(text: str) -> str:
    """Detect RFI/RFP from Finnish or English text. Returns 'RFI', 'RFP', or 'OTHER'."""
    lower = text.lower()
    if any(term in lower for term in RFI_TERMS_FI):
        return "RFI"
    if any(term in lower for term in RFP_TERMS_FI):
        return "RFP"
    if any(term in lower for term in FUTURE_TERMS_FI):
        return "RFI"  # future procurement = market consultation stage
    return "OTHER"


# ── Industry area keyword mapping ─────────────────────────────────────────────
INDUSTRY_KEYWORDS: dict[str, list[str]] = {
    "IT & Software": [
        "software", "ohjelmisto", "it ", "ict", "digital", "cloud",
        "saas", "platform", "tietojärjestelmä", "tietotekniikka", "cyber",
        "application", "system", "network", "database", "ai ", "machine learning",
        "data analytics", "api", "integration", "erp", "crm", "kubernetes",
        "devops", "microservice", "blockchain", "tekoäly", "pilvi",
    ],
    "Construction & Real Estate": [
        "construction", "rakennus", "building", "infrastructure", "infra",
        "kiinteistö", "renovation", "bridge", "road", "silta", "tie ",
        "maintenance", "facility", "toimitila", "saneer", "rakentaminen",
    ],
    "Healthcare & Social Services": [
        "health", "terveys", "hospital", "sairaala", "medical", "lääke",
        "welfare", "hyvinvointi", "social service", "sosiaali", "care",
        "pharmacy", "diagnostic", "laboratory", "patient", "potilas",
        "nursing", "hoiva", "wellbeing", "hyvinvointialue",
    ],
    "Transport & Logistics": [
        "transport", "liikenne", "logistics", "railway", "rautatie",
        "aviation", "ilmailu", "shipping", "port", "satama", "bus",
        "fleet", "vehicle", "ajoneuvo", "väylä", "traffic",
    ],
    "Energy & Environment": [
        "energy", "energia", "renewable", "uusiutuva", "electricity", "sähkö",
        "solar", "wind", "biogas", "environment", "ympäristö", "waste",
        "jäte", "water", "vesi ", "heating", "lämpö", "fingrid", "gasgrid",
    ],
    "Education & Research": [
        "education", "koulutus", "training", "university", "yliopisto",
        "school", "koulu", "research", "tutkimus", "library", "kirjasto",
        "e-learning", "learning management", "opetus", "akademi",
    ],
    "Defence & Security": [
        "defence", "puolustus", "security", "turvallisuus", "police",
        "poliisi", "fire", "palo", "border", "military", "armeija",
        "surveillance", "emergency", "pelastus",
    ],
    "Finance & Insurance": [
        "finance", "rahoitus", "banking", "pankki", "insurance", "vakuutus",
        "payment", "maksu", "audit", "tarkastus", "accounting", "vero",
        "tax", "kela", "finnvera",
    ],
    "Food & Agriculture": [
        "food", "ruoka", "agriculture", "maatalous", "farming", "catering",
        "restaurant", "ravinto", "elintarvike", "ruokavirasto",
    ],
}

# ── Location keyword mapping ───────────────────────────────────────────────────
LOCATION_KEYWORDS: dict[str, list[str]] = {
    "Helsinki":      ["helsinki"],
    "Espoo":         ["espoo", "aalto"],
    "Tampere":       ["tampere", "pirkanmaa", "pirha"],
    "Turku":         ["turku", "varha", "satahyva"],
    "Oulu":          ["oulu", "pohde"],
    "Jyväskylä":     ["jyväskylä", "jyvaskyla", "hyvaks", "keski-suomi"],
    "Lahti":         ["lahti", "päijät-häme", "paijat"],
    "Kuopio":        ["kuopio", "pohjo-savo", "pohjois-savo"],
    "Pori":          ["pori", "satakunta"],
    "Joensuu":       ["joensuu", "pohjois-karjala"],
    "Lappeenranta":  ["lappeenranta", "etelä-karjala", "eksote", "lut"],
    "Rovaniemi":     ["rovaniemi", "lappi", "lapinhy"],
    "Nationwide":    [
        "nationwide", "finland", "suomi", "national", "kansallinen",
        "valtio", "state", "hansel", "hilma", "kela", "vero", "dvv",
    ],
}

# ── Company size hints ────────────────────────────────────────────────────────
SME_KEYWORDS = [
    "sme", "pk-yritys", "small", "medium", "startup",
    "microenterprise", "pienyrittäjä",
]
LARGE_KEYWORDS = [
    "large enterprise", "corporation", "conglomerate", "global", "kansainvälinen",
]


def classify_industry(text: str) -> str:
    lower = text.lower()
    scores: dict[str, int] = {}
    for industry, keywords in INDUSTRY_KEYWORDS.items():
        scores[industry] = sum(1 for kw in keywords if kw in lower)
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "Other"


def classify_location(text: str) -> str:
    lower = text.lower()
    for loc, keywords in LOCATION_KEYWORDS.items():
        if any(kw in lower for kw in keywords):
            return loc
    return "Other"


def classify_company_size(text: str) -> str:
    lower = text.lower()
    if any(kw in lower for kw in SME_KEYWORDS):
        return "SME"
    if any(kw in lower for kw in LARGE_KEYWORDS):
        return "LARGE"
    return "ANY"


def extract_keywords(text: str, max_words: int = 20) -> list[str]:
    """Lightweight keyword extraction — top non-stopword tokens."""
    STOP = {
        # English
        "the", "a", "an", "and", "or", "for", "of", "to", "in", "on",
        "at", "is", "are", "was", "be", "by", "with", "this", "that",
        "from", "as", "its", "it", "we", "our", "your", "will", "has",
        "have", "been", "not", "but", "if", "all", "any", "new", "can",
        # Finnish common words
        "ja", "tai", "on", "se", "ei", "en", "ole", "olla", "myös",
        "joka", "että", "kuin", "niin", "kun", "jos", "hän", "he",
        "sekä", "joko", "kaikki", "jokin", "jotkin", "tai", "vain",
    }
    tokens = re.findall(r"[a-zA-ZäöåÄÖÅ]{4,}", text.lower())
    seen: dict[str, int] = {}
    for t in tokens:
        if t not in STOP:
            seen[t] = seen.get(t, 0) + 1
    ranked = sorted(seen.items(), key=lambda x: -x[1])
    return [w for w, _ in ranked[:max_words]]


def opportunity_score(
    title: str,
    description: str,
    cpv_codes: list,
    deadline_str: str,
    tender_type: str,
) -> int:
    """
    Composite opportunity score 0–100 based on the model in RFI_RFP_website.md:
      30% Technology Match
      20% Customer Match (public sector = high)
      15% RFI/RFP Stage
      15% Contract Value (estimated from keywords)
      10% Deadline
      10% Strategic Match
    """
    from scrapers.base import parse_date
    from datetime import date

    text = f"{title} {description}".lower()
    score = 0

    # 30% Technology Match
    tech_kw = [
        "software", "cloud", "ai ", "data", "ict", "digital",
        "cyber", "platform", "api", "integration", "erp", "saas",
        "tekoäly", "pilvi", "tietojärjestelmä",
    ]
    tech_cpv = {"72", "48", "73", "38", "32"}
    tech_hits = sum(1 for kw in tech_kw if kw in text)
    tech_cpv_hits = sum(1 for c in (cpv_codes or []) if str(c)[:2] in tech_cpv)
    score += min((tech_hits * 3 + tech_cpv_hits * 5), 30)

    # 20% Customer Match (public sector always matches for Finland)
    score += 20  # all our sources are Finnish public sector

    # 15% RFI/RFP Stage (RFI = early, more time → higher score)
    if tender_type == "RFI":
        score += 15
    elif tender_type == "RFP":
        score += 10
    else:
        score += 5

    # 15% Contract Value (keywords hinting at large value)
    value_kw = ["million", "miljoona", "framework", "puitesopimus", "national", "kansallinen"]
    if any(kw in text for kw in value_kw):
        score += 15
    else:
        score += 7

    # 10% Deadline (more time = higher score)
    dead = parse_date(deadline_str)
    if dead and dead > date.today():
        from datetime import timedelta
        days_left = (dead - date.today()).days
        score += 10 if days_left > 30 else 7 if days_left > 14 else 3
    else:
        score += 3

    # 10% Strategic Match
    strategic_kw = ["ai", "cloud", "platform", "data", "automation", "modernization",
                    "digital transformation", "digimuutos"]
    if any(kw in text for kw in strategic_kw):
        score += 10
    else:
        score += 4

    return min(score, 100)
