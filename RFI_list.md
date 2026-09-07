# Finland RFI/RFP Procurement Sources

## Overview

For a Python-based RFI/RFP opportunity crawler in Finland, prioritize **HILMA + TED + Cloudia/Tarjouspalvelu**, then add major Finnish public buyers and procurement calendars.

In Finland, RFI is often described as:

- Tietopyyntö
- Markkinakartoitus
- Markkinavuoropuhelu
- Tekninen vuoropuhelu
- Ennakkoilmoitus
- Tietopyyntö / markkinakartoitus

RFP-related terms include:

- Tarjouspyyntö
- Hankintailmoitus
- Kilpailutus
- Osallistumispyyntö
- Puitejärjestely
- Dynaaminen hankintajärjestelmä
- DPS

Future-opportunity terms include:

- Tuleva hankinta
- Hankintasuunnitelma
- Kilpailutussuunnitelma
- Hankintakalenteri
- Tulevat hankinnat

## 1. Highest-priority sources

| Priority | Source | Type | RFI/RFP | API | Python crawling | Recommendation |
|---:|---|---|---|---|---|---|
| 1 | HILMA | Finland national procurement | Yes | Official API | Yes | Must have |
| 2 | TED | EU procurement | Yes | Official API | Yes | Must have |
| 3 | Cloudia Tarjouspalvelu | Finnish e-tendering | Yes | Limited/public interfaces | Possible | Must have |
| 4 | Hansel | State framework/DPS | Yes | Limited | Public pages | Very high |
| 5 | Hanki | State procurement | Yes | Limited | Possible | Very high |
| 6 | Finnish cities | Local procurement | Yes | Usually no | Yes | High |
| 7 | Wellbeing counties | Healthcare/social procurement | Yes | Usually no | Yes | High |
| 8 | Universities | Research/IT/services | Yes | Usually no | Yes | High |
| 9 | State-owned companies | Infrastructure/IT | Yes | Usually no | Yes | High |
| 10 | Commercial aggregators | Aggregated tenders | Yes | Depends | Possible | Secondary |

## 2. Official / trusted sources

### HILMA

HILMA is the official Finnish public procurement notice service and should be the foundation of the crawler.

Official links:

- https://www.hankintailmoitukset.fi/
- https://hns-hilma-prod-apim.developer.azure-api.net/
- https://github.com/Hankintailmoitukset/hilma-api

The HILMA AVP-Read API is intended for retrieving open procurement data. The API documentation indicates that commercial use is permitted subject to applicable API limits.

### TED

TED is the EU-wide procurement platform and should be the second core source.

Official API documentation:

- https://docs.ted.europa.eu/api/latest/search.html

TED supports procurement notice search, expert queries, bulk XML downloads and programmatic retrieval.

Useful filters include:

- Country = Finland
- NUTS = FI
- CPV 72000000 — IT services
- CPV 48000000 — Software packages and information systems
- CPV 72200000 — Software programming and consultancy services
- CPV 72300000 — Data services
- CPV 72400000 — Internet services

## 3. Top 100 sources

### National / EU procurement

1. HILMA
2. TED
3. Cloudia Tarjouspalvelu
4. Hansel
5. Hanki
6. Valtiokonttori
7. Hankinta-Suomi
8. Suomi.fi procurement
9. Ministry of Finance
10. Ministry of Economic Affairs and Employment

### Major Finnish cities

11. City of Helsinki
12. City of Espoo
13. City of Tampere
14. City of Vantaa
15. City of Turku
16. City of Oulu
17. City of Jyväskylä
18. City of Lahti
19. City of Kuopio
20. City of Pori
21. City of Kouvola
22. City of Joensuu
23. City of Lappeenranta
24. City of Hämeenlinna
25. City of Vaasa
26. City of Seinäjoki
27. City of Rovaniemi
28. City of Mikkeli
29. City of Kotka
30. City of Salo

### Wellbeing services counties

31. Vantaa-Kerava wellbeing services county
32. Western Uusimaa wellbeing services county
33. Central Uusimaa wellbeing services county
34. Eastern Uusimaa wellbeing services county
35. Southwest Finland wellbeing services county
36. Satakunta wellbeing services county
37. Kanta-Häme wellbeing services county
38. Pirkanmaa wellbeing services county
39. Päijät-Häme wellbeing services county
40. Kymenlaakso wellbeing services county
41. South Karelia wellbeing services county
42. South Savo wellbeing services county
43. North Savo wellbeing services county
44. North Karelia wellbeing services county
45. Central Finland wellbeing services county
46. South Ostrobothnia wellbeing services county
47. Ostrobothnia wellbeing services county
48. Central Ostrobothnia wellbeing services county
49. North Ostrobothnia wellbeing services county
50. Kainuu wellbeing services county
51. Lapland wellbeing services county

### Finnish government / state organizations

52. Kela
53. Finnish Tax Administration (Vero)
54. Digital and Population Data Services Agency (DVV)
55. Valtiokonttori
56. Finnish Transport Infrastructure Agency (Väylävirasto)
57. Traficom
58. Business Finland
59. Finnish Patent and Registration Office (PRH)
60. Statistics Finland
61. Finnish Meteorological Institute
62. Finnish Environment Institute (Syke)
63. Finnish Food Authority
64. Finnish Medicines Agency (Fimea)
65. Finnish Institute for Health and Welfare (THL)
66. Finnish Institute of Occupational Health
67. Finnish Immigration Service
68. National Archives of Finland
69. Finnish National Agency for Education
70. Other central government agencies published through HILMA/Hansel

### State-owned / strategic companies

71. Finavia
72. Fintraffic
73. Fingrid
74. Posti
75. VR Group
76. Gasgrid Finland
77. Fortum
78. Helen
79. VTT Technical Research Centre of Finland
80. CSC – IT Center for Science
81. Finnish Meteorological Institute
82. Senaatti-kiinteistöt
83. Motiva
84. Finnvera
85. Solidium

### Universities

86. University of Helsinki
87. Aalto University
88. University of Turku
89. Tampere University
90. University of Oulu
91. University of Jyväskylä
92. University of Eastern Finland
93. Åbo Akademi University
94. LUT University
95. University of Vaasa

### Other procurement / opportunity sources

96. Mercell
97. Tarjouspalvelu
98. Procurement.fi / Hankinnat.fi
99. Yrittäjät procurement services
100. Regional procurement calendars

## 4. Recommended crawler architecture

Do not create 100 independent crawlers. Build a small number of source connectors.

```text
                       FINLAND PROCUREMENT SOURCES

                         +----------------+
                         |     HILMA      |
                         | Official API   |
                         +-------+--------+
                                 |
                         +-------v--------+
                         |      TED       |
                         | Official API   |
                         +-------+--------+
                                 |
                  +--------------v---------------+
                  |    Cloudia/Tarjouspalvelu    |
                  |          Web crawler         |
                  +--------------+---------------+
                                 |
                  +--------------v---------------+
                  |       Python ingestion       |
                  |                              |
                  | httpx / requests / Scrapy    |
                  | Playwright where required    |
                  +--------------+---------------+
                                 |
                         +-------v--------+
                         |  Normalization |
                         |                |
                         | title          |
                         | buyer          |
                         | CPV            |
                         | deadline       |
                         | value          |
                         | RFI/RFP        |
                         | URL            |
                         | language       |
                         +-------+--------+
                                 |
                         +-------v--------+
                         | AI Classifier   |
                         |                |
                         | RFI/RFP        |
                         | AI             |
                         | Cloud          |
                         | Data           |
                         | Cybersecurity  |
                         +-------+--------+
                                 |
                         +-------v--------+
                         | PostgreSQL     |
                         | + pgvector     |
                         +-------+--------+
                                 |
                 +---------------+---------------+
                 |               |               |
              Dashboard        Email           Teams
```

## 5. Recommended Python technology

### API sources

```text
Python
├── httpx
├── requests
├── Pydantic
└── asyncio
```

### Static websites

```text
BeautifulSoup
lxml
Scrapy
```

### JavaScript-heavy websites

```text
Playwright
```

Avoid Selenium unless a particular website requires it.

### Database

```text
PostgreSQL
+
pgvector
```

### Search

```text
OpenSearch / Elasticsearch
```

or PostgreSQL full-text search for the first version.

### AI classification

```text
LLM
  ↓
Finnish/Swedish → English
  ↓
RFI/RFP classification
  ↓
Technology classification
  ↓
Opportunity scoring
```

## 6. Opportunity scoring

A useful initial scoring model:

```text
Opportunity Score =
    30% Technology Match
  + 20% Customer Match
  + 15% RFI/RFP Stage
  + 15% Contract Value
  + 10% Deadline
  + 10% Strategic Match
```

Example normalized record:

```json
{
  "title": "AI platform development and maintenance",
  "buyer": "Finnish Government Agency",
  "country": "Finland",
  "type": "RFI",
  "language": "Finnish",
  "cpv": [
    "72000000",
    "72200000"
  ],
  "estimated_value": 5000000,
  "deadline": "2026-10-15",
  "technology": [
    "AI",
    "Cloud",
    "Data",
    "Kubernetes"
  ],
  "opportunity_score": 94
}
```

## 7. RFI → RFP tracking

A particularly valuable feature is tracking an RFI through to the eventual RFP.

```text
Nov 2026
    ↓
RFI: AI platform modernization
    ↓
Buyer asks vendors for input
    ↓
AI detects opportunity
    ↓
Save RFI
    ↓
Track buyer
    ↓
Track CPV
    ↓
Track keywords
    ↓
Jan 2027
    ↓
RFP published
    ↓
AI automatically links RFP
    ↓
Notify sales team
```

This is potentially more valuable than a generic tender crawler because early-stage market-dialogue/RFI notices can provide advance visibility before the actual competition.

## 8. Recommended implementation phases

### Phase 1 — highest value

Start with:

1. HILMA API
2. TED API
3. Cloudia/Tarjouspalvelu
4. Hansel
5. Hanki
6. Major Finnish cities
7. Wellbeing services counties

### Phase 2

Add:

8. Universities
9. State agencies
10. State-owned companies
11. Regional procurement calendars
12. Specialized procurement portals

### Phase 3

Add:

13. AI-powered matching
14. Finnish → English translation
15. RFI → predicted RFP detection
16. Opportunity scoring
17. Duplicate detection
18. Buyer intelligence
19. Historical winning-supplier analysis
20. CRM integration

## 9. Final recommendation

For a production-quality Finland RFI/RFP intelligence system:

**HILMA API + TED API should be the authoritative backbone.**

Use **Cloudia/Tarjouspalvelu** as the major tender-document layer, and then crawl the important Finnish buyers only where information is not already available through central systems.

This approach minimizes crawler maintenance, reduces duplicate data, and provides a strong foundation for AI-powered procurement intelligence.

## Trusted source references

- HILMA: https://www.hankintailmoitukset.fi/
- HILMA API Developer Portal: https://hns-hilma-prod-apim.developer.azure-api.net/
- HILMA API GitHub: https://github.com/Hankintailmoitukset/hilma-api
- TED API documentation: https://docs.ted.europa.eu/api/latest/search.html
- Suomi.fi public procurement guidance: https://www.suomi.fi/yritykselle/liiketoiminnan-kehittaminen/markkinointi-ja-myynti/opas/myynti/julkiset-hankinnat
- Mercell: https://info.mercell.com/fi-fi/login/
