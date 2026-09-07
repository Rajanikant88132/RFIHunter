#!/usr/bin/env python3
"""
Seed script — inserts 50 realistic Finnish RFI/RFP notices with
buyer_email, buyer_phone, and pdf_urls populated for dashboard demo.

Run: python3 seed_demo.py
"""
import json
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from db import upsert_tender, init_schema, resolve_industry_id, resolve_location_id

init_schema()

NOTICES = [
    # ─── IT & Software ───────────────────────────────────────────────────────
    dict(
        external_id="DEMO-IT-001", source="HILMA", type="RFI", status="OPEN",
        title="Tietopyyntö: Sosiaali- ja terveydenhuollon potilastietojärjestelmä",
        description="Keski-Uudenmaan hyvinvointialue pyytää tietoja markkinoilla olevista sähköisistä "
                    "potilastietojärjestelmäratkaisuista. Tietopyyntö ei ole hankintamenettely eikä sido "
                    "hankintayksikköä hankintaan. Vastaukset käytetään hankinnan suunnittelun tueksi.",
        contracting_authority="Keski-Uudenmaan hyvinvointialue",
        company_size="ANY", published_date="2026-08-15", deadline_date="2026-10-31",
        estimated_value=None, currency="EUR",
        source_url="https://www.hankintailmoitukset.fi/fi/notice/2026-DEMO001",
        cpv_codes=json.dumps(["72000000", "48000000"]),
        keywords=json.dumps(["patient records", "EHR", "healthcare IT", "integration", "cloud"]),
        buyer_email="hankinnat@keusote.fi",
        buyer_phone="+358 9 8734 1000",
        pdf_urls=json.dumps([
            {"name": "Procurement Documents", "url": "https://tarjouspalvelu.fi/keusote?id=455573"},
            {"name": "HILMA Notice", "url": "https://www.hankintailmoitukset.fi/fi/notice/2026-DEMO001"},
            {"name": "RFI Technical Specifications (PDF)", "url": "https://www.hankintailmoitukset.fi/fi/public/procurement/100900/notice/147427"},
        ]),
        opportunity_score=88, raw_data=json.dumps({"source": "demo_seed"}),
    ),
    dict(
        external_id="DEMO-IT-002", source="HILMA", type="RFP", status="OPEN",
        title="Tarjouspyyntö: Pilvi-infrastruktuuripalvelut ja DevOps-ympäristö",
        description="Suomen Valtiokonttori kilpailuttaa pilvi-infrastruktuuripalvelut ja DevOps-ympäristön "
                    "valtionhallinnon IT-palveluille. Hankinta kattaa IaaS/PaaS-palvelut, CI/CD-putket "
                    "ja tietoturvavaatimukset. Sopimuskausi 3 + 1 + 1 vuotta.",
        contracting_authority="Valtiokonttori",
        company_size="LARGE", published_date="2026-08-20", deadline_date="2026-10-15",
        estimated_value=4500000, currency="EUR",
        source_url="https://www.hankintailmoitukset.fi/fi/notice/2026-DEMO002",
        cpv_codes=json.dumps(["72000000", "72200000", "72600000"]),
        keywords=json.dumps(["cloud", "AWS", "Azure", "DevOps", "infrastructure", "IaaS", "PaaS"]),
        buyer_email="kilpailutukset@valtiokonttori.fi",
        buyer_phone="+358 295 502 000",
        pdf_urls=json.dumps([
            {"name": "Tarjouspyyntö (PDF)", "url": "https://ted.europa.eu/fi/notice/2026-DEMO002/pdf"},
            {"name": "Tekniset vaatimukset (PDF)", "url": "https://www.hankintailmoitukset.fi/fi/notice/2026-DEMO002"},
            {"name": "Sopimusluonnos (PDF)", "url": "https://tarjouspalvelu.fi/valtiokonttori?id=600001"},
        ]),
        opportunity_score=82, raw_data=json.dumps({"source": "demo_seed"}),
    ),
    dict(
        external_id="DEMO-IT-003", source="TED", type="RFP", status="OPEN",
        title="Framework Agreement for AI and Machine Learning Services",
        description="The Finnish Government is establishing a framework agreement for Artificial Intelligence "
                    "and Machine Learning services to be used across multiple government agencies. "
                    "The framework covers model development, MLOps infrastructure and advisory services. "
                    "Total estimated value EUR 12M over 4 years.",
        contracting_authority="Hansel Oy (on behalf of Finnish Government)",
        company_size="LARGE", published_date="2026-09-01", deadline_date="2026-11-30",
        estimated_value=12000000, currency="EUR",
        source_url="https://ted.europa.eu/en/notice/-/detail/2026-DEMO003",
        cpv_codes=json.dumps(["72000000", "72212000", "72300000"]),
        keywords=json.dumps(["AI", "machine learning", "MLOps", "artificial intelligence", "data science"]),
        buyer_email="procurement@hansel.fi",
        buyer_phone="+358 29 444 4000",
        pdf_urls=json.dumps([
            {"name": "Official Notice PDF (ENG)", "url": "https://ted.europa.eu/en/notice/2026-DEMO003/pdf"},
            {"name": "Official Notice PDF (Finnish)", "url": "https://ted.europa.eu/fi/notice/2026-DEMO003/pdf"},
            {"name": "TED Notice (HTML)", "url": "https://ted.europa.eu/en/notice/-/detail/2026-DEMO003"},
        ]),
        opportunity_score=91, raw_data=json.dumps({"source": "demo_seed"}),
    ),
    dict(
        external_id="DEMO-IT-004", source="HILMA", type="RFI", status="OPEN",
        title="Markkinavuoropuhelu: Kyberturvallisuuspalvelut 2027",
        description="Puolustusministeriö käynnistää markkinavuoropuhelun kyberturvallisuuspalveluihin "
                    "liittyen. Tarkoituksena on kartoittaa markkinoiden tilannetta tunkeutumistestauksen, "
                    "SOC-palveluiden, haavoittuvuuksien hallinnan ja tietoturva-auditointien osalta. "
                    "Hankintamenettely käynnistyy arviolta Q1/2027.",
        contracting_authority="Puolustusministeriö",
        company_size="ANY", published_date="2026-08-10", deadline_date="2026-11-15",
        estimated_value=None, currency="EUR",
        source_url="https://www.hankintailmoitukset.fi/fi/notice/2026-DEMO004",
        cpv_codes=json.dumps(["72000000", "72200000"]),
        keywords=json.dumps(["cybersecurity", "penetration testing", "SOC", "audit", "tietoturva"]),
        buyer_email="hankinta@defmin.fi",
        buyer_phone="+358 295 160 001",
        pdf_urls=json.dumps([
            {"name": "Markkinavuoropuhelu - Kutsu (PDF)", "url": "https://www.hankintailmoitukset.fi/fi/notice/2026-DEMO004"},
            {"name": "Procurement Documents", "url": "https://tarjouspalvelu.fi/defmin?id=600004"},
        ]),
        opportunity_score=79, raw_data=json.dumps({"source": "demo_seed"}),
    ),
    dict(
        external_id="DEMO-IT-005", source="Hansel", type="RFP", status="OPEN",
        title="Dynamic Purchasing System: SaaS Software Products for Government",
        description="Hansel Oy is establishing a Dynamic Purchasing System (DPS) for SaaS software products "
                    "for the Finnish central government and municipalities. The DPS covers ERP, HR, CRM, "
                    "project management and collaboration tools. Suppliers can apply to join the DPS at any time.",
        contracting_authority="Hansel Oy",
        company_size="SME", published_date="2026-07-01", deadline_date="2027-06-30",
        estimated_value=8000000, currency="EUR",
        source_url="https://www.hansel.fi/en/procurement/dps-saas-2026",
        cpv_codes=json.dumps(["72000000", "48000000"]),
        keywords=json.dumps(["SaaS", "ERP", "CRM", "DPS", "framework agreement", "cloud software"]),
        buyer_email="dps@hansel.fi",
        buyer_phone="+358 29 444 4100",
        pdf_urls=json.dumps([
            {"name": "DPS Notice PDF", "url": "https://hansel.fi/docs/dps-saas-2026.pdf"},
            {"name": "Supplier Guide PDF", "url": "https://hansel.fi/docs/dps-guide-2026.pdf"},
            {"name": "Framework Terms PDF", "url": "https://hansel.fi/docs/dps-terms-2026.pdf"},
        ]),
        opportunity_score=85, raw_data=json.dumps({"source": "demo_seed"}),
    ),
    # ─── Healthcare ─────────────────────────────────────────────────────────────
    dict(
        external_id="DEMO-HC-001", source="HILMA", type="RFP", status="OPEN",
        title="Tarjouspyyntö: Terveydenhuollon digitaaliset etäpalvelut ja videovastaanotot",
        description="Pirkanmaan hyvinvointialue kilpailuttaa terveydenhuollon digitaaliset etäpalvelut. "
                    "Hankinta sisältää videovastaanottoalustan, ajanvarausjärjestelmän ja integraatiot "
                    "olemassa oleviin potilastietojärjestelmiin. Sopimuskausi 2 + 1 + 1 vuotta.",
        contracting_authority="Pirkanmaan hyvinvointialue",
        company_size="SME", published_date="2026-08-25", deadline_date="2026-10-20",
        estimated_value=750000, currency="EUR",
        source_url="https://www.hankintailmoitukset.fi/fi/notice/2026-DEMO-HC1",
        cpv_codes=json.dumps(["72000000", "85000000"]),
        keywords=json.dumps(["telemedicine", "video consultation", "digital health", "remote care"]),
        buyer_email="hankinnat@pirha.fi",
        buyer_phone="+358 3 311 69611",
        pdf_urls=json.dumps([
            {"name": "Tarjouspyyntö (PDF)", "url": "https://tarjouspalvelu.fi/pirha?id=600100"},
            {"name": "HILMA Notice", "url": "https://www.hankintailmoitukset.fi/fi/notice/2026-DEMO-HC1"},
            {"name": "Tekninen liite (PDF)", "url": "https://tarjouspalvelu.fi/pirha?id=600100&att=tech"},
        ]),
        opportunity_score=74, raw_data=json.dumps({"source": "demo_seed"}),
    ),
    dict(
        external_id="DEMO-HC-002", source="TED", type="RFI", status="OPEN",
        title="Prior Information Notice: National Electronic Prescription System Renewal",
        description="Kela (Social Insurance Institution of Finland) announces a Prior Information Notice "
                    "for the renewal of the national electronic prescription system. The project involves "
                    "modernising the Kanta.fi services infrastructure, FHIR R4 API implementation and "
                    "cloud migration. Estimated budget EUR 35M over 6 years.",
        contracting_authority="Kela – Social Insurance Institution",
        company_size="LARGE", published_date="2026-09-03", deadline_date="2026-12-15",
        estimated_value=35000000, currency="EUR",
        source_url="https://ted.europa.eu/en/notice/-/detail/2026-DEMO-HC2",
        cpv_codes=json.dumps(["72000000", "85000000", "48000000"]),
        keywords=json.dumps(["Kanta", "ePrescription", "FHIR", "healthcare IT", "cloud migration"]),
        buyer_email="kilpailutukset@kela.fi",
        buyer_phone="+358 20 634 1415",
        pdf_urls=json.dumps([
            {"name": "PIN Notice PDF (English)", "url": "https://ted.europa.eu/en/notice/2026-DEMO-HC2/pdf"},
            {"name": "PIN Notice PDF (Finnish)", "url": "https://ted.europa.eu/fi/notice/2026-DEMO-HC2/pdf"},
            {"name": "Market Consultation Brief", "url": "https://ted.europa.eu/en/notice/-/detail/2026-DEMO-HC2"},
        ]),
        opportunity_score=92, raw_data=json.dumps({"source": "demo_seed"}),
    ),
    # ─── Construction & Real Estate ─────────────────────────────────────────────
    dict(
        external_id="DEMO-CONST-001", source="HILMA", type="RFP", status="OPEN",
        title="Tarjouspyyntö: Espoon kaupungintalon peruskorjaus",
        description="Espoon kaupunki kilpailuttaa kaupungintalon peruskorjauksen. Hanke sisältää "
                    "talotekniikan uusimisen, esteettömyysparannukset ja energiatehokkuuskorjaukset. "
                    "Aloitus 03/2027, arvioitu kesto 24 kuukautta.",
        contracting_authority="Espoon kaupunki / Tilakeskus",
        company_size="LARGE", published_date="2026-08-01", deadline_date="2026-09-30",
        estimated_value=12000000, currency="EUR",
        source_url="https://www.hankintailmoitukset.fi/fi/notice/2026-DEMO-C1",
        cpv_codes=json.dumps(["45000000", "45300000"]),
        keywords=json.dumps(["construction", "renovation", "building", "energy efficiency"]),
        buyer_email="tilakeskus.kilpailutukset@espoo.fi",
        buyer_phone="+358 9 816 21000",
        pdf_urls=json.dumps([
            {"name": "Tarjouspyyntö (PDF)", "url": "https://tarjouspalvelu.fi/espoo?id=600200"},
            {"name": "Hankesuunnitelma (PDF)", "url": "https://tarjouspalvelu.fi/espoo?id=600200&att=plan"},
            {"name": "HILMA Notice", "url": "https://www.hankintailmoitukset.fi/fi/notice/2026-DEMO-C1"},
        ]),
        opportunity_score=60, raw_data=json.dumps({"source": "demo_seed"}),
    ),
    # ─── Transport & Logistics ──────────────────────────────────────────────────
    dict(
        external_id="DEMO-TRANS-001", source="TED", type="RFP", status="OPEN",
        title="Public Transport Ticketing and Journey Planner Platform — Helsinki Region",
        description="HSL (Helsinki Region Transport Authority) is procuring a new integrated public "
                    "transport ticketing and journey planning platform. The system must support MaaS "
                    "integration, open GTFS-RT data feeds and account-based ticketing. "
                    "Contract value estimated EUR 18M, duration 5 years.",
        contracting_authority="HSL – Helsinki Region Transport",
        company_size="LARGE", published_date="2026-09-02", deadline_date="2026-11-14",
        estimated_value=18000000, currency="EUR",
        source_url="https://ted.europa.eu/en/notice/-/detail/2026-DEMO-T1",
        cpv_codes=json.dumps(["72000000", "60000000"]),
        keywords=json.dumps(["MaaS", "ticketing", "public transport", "GTFS", "journey planning"]),
        buyer_email="procurement@hsl.fi",
        buyer_phone="+358 9 4766 4000",
        pdf_urls=json.dumps([
            {"name": "Contract Notice PDF (ENG)", "url": "https://ted.europa.eu/en/notice/2026-DEMO-T1/pdf"},
            {"name": "Contract Notice PDF (Finnish)", "url": "https://ted.europa.eu/fi/notice/2026-DEMO-T1/pdf"},
            {"name": "Technical Requirements v1.2 (PDF)", "url": "https://ted.europa.eu/en/notice/-/detail/2026-DEMO-T1"},
        ]),
        opportunity_score=87, raw_data=json.dumps({"source": "demo_seed"}),
    ),
    dict(
        external_id="DEMO-TRANS-002", source="HILMA", type="RFI", status="OPEN",
        title="Tietopyyntö: Autonomisten ajoneuvojen pilottihanke Tampereella",
        description="Tampereen kaupunki pyytää tietoja autonomisten ajoneuvojen toimittajilta kaupunki- "
                    "ympäristössä toteutettavaa pilottihanketta varten. Pilotti toteutetaan Ratinan "
                    "kaupunginosassa keväällä 2027. Vastaajia pyydetään esittämään tekniset ratkaisunsa "
                    "ja viitteet aiemmista kaupunkiympäristöpiloteista.",
        contracting_authority="Tampereen kaupunki",
        company_size="SME", published_date="2026-08-28", deadline_date="2026-10-28",
        estimated_value=None, currency="EUR",
        source_url="https://www.hankintailmoitukset.fi/fi/notice/2026-DEMO-T2",
        cpv_codes=json.dumps(["60000000", "34000000"]),
        keywords=json.dumps(["autonomous vehicles", "self-driving", "pilot", "urban mobility"]),
        buyer_email="liikenne.hankinnat@tampere.fi",
        buyer_phone="+358 3 565 611",
        pdf_urls=json.dumps([
            {"name": "Tietopyyntö (PDF)", "url": "https://tarjouspalvelu.fi/tampere?id=600300"},
            {"name": "HILMA Notice", "url": "https://www.hankintailmoitukset.fi/fi/notice/2026-DEMO-T2"},
        ]),
        opportunity_score=71, raw_data=json.dumps({"source": "demo_seed"}),
    ),
    # ─── Energy & Environment ────────────────────────────────────────────────────
    dict(
        external_id="DEMO-ENERGY-001", source="TED", type="RFP", status="OPEN",
        title="Smart Grid Management System and IoT Sensor Network for Helsinki",
        description="Helen Oy (Helsinki Energy) is procuring a smart grid management system integrated "
                    "with an IoT sensor network for real-time monitoring of the city's district heating "
                    "and electricity distribution networks. System must support predictive maintenance "
                    "and demand-response automation. Estimated EUR 7.5M.",
        contracting_authority="Helen Oy",
        company_size="LARGE", published_date="2026-08-18", deadline_date="2026-10-25",
        estimated_value=7500000, currency="EUR",
        source_url="https://ted.europa.eu/en/notice/-/detail/2026-DEMO-E1",
        cpv_codes=json.dumps(["38000000", "72000000"]),
        keywords=json.dumps(["smart grid", "IoT", "district heating", "energy", "predictive maintenance"]),
        buyer_email="procurement@helen.fi",
        buyer_phone="+358 9 6171",
        pdf_urls=json.dumps([
            {"name": "Contract Notice PDF (ENG)", "url": "https://ted.europa.eu/en/notice/2026-DEMO-E1/pdf"},
            {"name": "Contract Notice PDF (Finnish)", "url": "https://ted.europa.eu/fi/notice/2026-DEMO-E1/pdf"},
            {"name": "IoT Technical Specification (PDF)", "url": "https://ted.europa.eu/en/notice/-/detail/2026-DEMO-E1"},
        ]),
        opportunity_score=83, raw_data=json.dumps({"source": "demo_seed"}),
    ),
    dict(
        external_id="DEMO-ENERGY-002", source="HILMA", type="RFI", status="OPEN",
        title="Markkinavuoropuhelu: Vihreän vedyn tuotanto ja varastointi",
        description="Fortum pyytää markkinainformaatiota vihreän vedyn tuotantoteknologioista, "
                    "varastointiratkaisuista ja jakelujärjestelmistä Pohjois-Suomessa sijaitsevaa "
                    "pilottiprojektia varten. Hankkeen kokonaisbudjetti 50–100 M€. Vastausaika 8 viikkoa.",
        contracting_authority="Fortum Oyj",
        company_size="LARGE", published_date="2026-07-15", deadline_date="2026-09-15",
        estimated_value=None, currency="EUR",
        source_url="https://www.hankintailmoitukset.fi/fi/notice/2026-DEMO-E2",
        cpv_codes=json.dumps(["09000000", "38000000"]),
        keywords=json.dumps(["hydrogen", "green energy", "storage", "electrolysis", "renewable"]),
        buyer_email="hankinnat@fortum.com",
        buyer_phone="+358 10 4511",
        pdf_urls=json.dumps([
            {"name": "Markkinavuoropuhelu (PDF)", "url": "https://tarjouspalvelu.fi/fortum?id=600400"},
            {"name": "HILMA Notice", "url": "https://www.hankintailmoitukset.fi/fi/notice/2026-DEMO-E2"},
        ]),
        opportunity_score=76, raw_data=json.dumps({"source": "demo_seed"}),
    ),
    # ─── Education & Research ────────────────────────────────────────────────────
    dict(
        external_id="DEMO-EDU-001", source="HILMA", type="RFP", status="OPEN",
        title="Tarjouspyyntö: Oppimisanalytiikka-alusta korkea-asteelle",
        description="Jyväskylän yliopisto kilpailuttaa oppimisanalytiikka-alustan, joka integroituu "
                    "Moodle-oppimisympäristöön ja tuottaa reaaliaikaisia oppijakohtaisia analyysejä. "
                    "Hankinta kattaa alustan, integraatiotyön ja 3 vuoden ylläpidon.",
        contracting_authority="Jyväskylän yliopisto",
        company_size="SME", published_date="2026-08-22", deadline_date="2026-10-10",
        estimated_value=380000, currency="EUR",
        source_url="https://www.hankintailmoitukset.fi/fi/notice/2026-DEMO-EDU1",
        cpv_codes=json.dumps(["72000000", "80000000"]),
        keywords=json.dumps(["learning analytics", "Moodle", "education technology", "LMS", "university"]),
        buyer_email="hankinnat@jyu.fi",
        buyer_phone="+358 14 260 1211",
        pdf_urls=json.dumps([
            {"name": "Tarjouspyyntö (PDF)", "url": "https://tarjouspalvelu.fi/jyu?id=600500"},
            {"name": "Tekniset vaatimukset (PDF)", "url": "https://tarjouspalvelu.fi/jyu?id=600500&att=tech"},
            {"name": "HILMA Notice", "url": "https://www.hankintailmoitukset.fi/fi/notice/2026-DEMO-EDU1"},
        ]),
        opportunity_score=72, raw_data=json.dumps({"source": "demo_seed"}),
    ),
    dict(
        external_id="DEMO-EDU-002", source="TED", type="RFI", status="OPEN",
        title="Prior Information Notice: National Research Computing Infrastructure 2027",
        description="CSC – IT Center for Science announces a Prior Information Notice for the next "
                    "generation national research computing infrastructure. The procurement will cover "
                    "HPC cluster hardware, GPU compute capacity, petascale storage and interconnect. "
                    "Estimated total value EUR 120M over 7 years.",
        contracting_authority="CSC – IT Center for Science",
        company_size="LARGE", published_date="2026-09-04", deadline_date="2026-12-01",
        estimated_value=120000000, currency="EUR",
        source_url="https://ted.europa.eu/en/notice/-/detail/2026-DEMO-EDU2",
        cpv_codes=json.dumps(["72000000", "30000000"]),
        keywords=json.dumps(["HPC", "supercomputer", "research computing", "GPU", "data center"]),
        buyer_email="hankinta@csc.fi",
        buyer_phone="+358 9 457 2001",
        pdf_urls=json.dumps([
            {"name": "PIN Notice PDF (ENG)", "url": "https://ted.europa.eu/en/notice/2026-DEMO-EDU2/pdf"},
            {"name": "PIN Notice PDF (Finnish)", "url": "https://ted.europa.eu/fi/notice/2026-DEMO-EDU2/pdf"},
            {"name": "Technical Consultation Document", "url": "https://ted.europa.eu/en/notice/-/detail/2026-DEMO-EDU2"},
        ]),
        opportunity_score=90, raw_data=json.dumps({"source": "demo_seed"}),
    ),
    # ─── Finance & Insurance ────────────────────────────────────────────────────
    dict(
        external_id="DEMO-FIN-001", source="HILMA", type="RFP", status="OPEN",
        title="Tarjouspyyntö: Taloushallinnon SaaS-järjestelmä kunnille",
        description="Tampereen kaupunki johtavana hankintayksikkönä kilpailuttaa taloushallinnon "
                    "SaaS-järjestelmän 12 kunnalle. Hankinta kattaa kirjanpidon, laskutuksen, "
                    "budjetoinnin ja raportoinnin. Arvioitu kokonaisarvo 2 M€ / 4 vuotta.",
        contracting_authority="Tampereen kaupunki (yhteiShankinta)",
        company_size="SME", published_date="2026-07-28", deadline_date="2026-09-25",
        estimated_value=2000000, currency="EUR",
        source_url="https://www.hankintailmoitukset.fi/fi/notice/2026-DEMO-FIN1",
        cpv_codes=json.dumps(["72000000", "66000000"]),
        keywords=json.dumps(["ERP", "financial management", "SaaS", "accounting", "municipal"]),
        buyer_email="yhteiShankinnat@tampere.fi",
        buyer_phone="+358 3 5656 0000",
        pdf_urls=json.dumps([
            {"name": "Tarjouspyyntö (PDF)", "url": "https://tarjouspalvelu.fi/tampere?id=600600"},
            {"name": "Liite 1 – Vaatimusmäärittely (PDF)", "url": "https://tarjouspalvelu.fi/tampere?id=600600&att=req"},
            {"name": "Liite 2 – Sopimusluonnos (PDF)", "url": "https://tarjouspalvelu.fi/tampere?id=600600&att=contract"},
            {"name": "HILMA Notice", "url": "https://www.hankintailmoitukset.fi/fi/notice/2026-DEMO-FIN1"},
        ]),
        opportunity_score=78, raw_data=json.dumps({"source": "demo_seed"}),
    ),
    # ─── Defence & Security ──────────────────────────────────────────────────────
    dict(
        external_id="DEMO-DEF-001", source="TED", type="RFP", status="OPEN",
        title="Drone Detection and Counter-UAS System for Border Guard",
        description="The Finnish Border Guard is procuring a drone detection and counter-UAS system "
                    "for deployment along the eastern border. The system must integrate with existing "
                    "surveillance infrastructure, support multi-sensor fusion and AI-based classification. "
                    "Security-cleared suppliers only. Estimated EUR 9M.",
        contracting_authority="Finnish Border Guard (Rajavartiolaitos)",
        company_size="LARGE", published_date="2026-08-30", deadline_date="2026-11-07",
        estimated_value=9000000, currency="EUR",
        source_url="https://ted.europa.eu/en/notice/-/detail/2026-DEMO-DEF1",
        cpv_codes=json.dumps(["38000000", "72000000"]),
        keywords=json.dumps(["drone detection", "counter-UAS", "border security", "AI surveillance"]),
        buyer_email="hankinta@raja.fi",
        buyer_phone="+358 295 421 000",
        pdf_urls=json.dumps([
            {"name": "Contract Notice PDF (ENG)", "url": "https://ted.europa.eu/en/notice/2026-DEMO-DEF1/pdf"},
            {"name": "Contract Notice PDF (Finnish)", "url": "https://ted.europa.eu/fi/notice/2026-DEMO-DEF1/pdf"},
            {"name": "Security Requirements Document", "url": "https://ted.europa.eu/en/notice/-/detail/2026-DEMO-DEF1"},
        ]),
        opportunity_score=80, raw_data=json.dumps({"source": "demo_seed"}),
    ),
    # ─── Additional cities ────────────────────────────────────────────────────────
    dict(
        external_id="DEMO-OULU-001", source="FinnishCities", type="RFP", status="OPEN",
        title="Oulun älykaupunki: IoT-sensorit ja datanhallinnan alusta",
        description="Oulun kaupunki kilpailuttaa IoT-sensoreiden laajennuksen ja datanhallinnan alustan "
                    "älykaupunkistrategian toteuttamiseksi. Hankinta sisältää 2000 uutta ilmanlaatu-, "
                    "liikenteen ja energiamittaria sekä pilvi-alustan datan käsittelyyn.",
        contracting_authority="Oulun kaupunki / Yhdyskunta- ja ympäristöpalvelut",
        company_size="SME", published_date="2026-08-05", deadline_date="2026-10-05",
        estimated_value=1200000, currency="EUR",
        source_url="https://www.ouka.fi/hankintailmoitukset/2026-DEMO-OULU1",
        cpv_codes=json.dumps(["38000000", "72000000"]),
        keywords=json.dumps(["IoT", "smart city", "sensors", "data platform", "air quality"]),
        buyer_email="hankinnat@ouka.fi",
        buyer_phone="+358 8 558 410 00",
        pdf_urls=json.dumps([
            {"name": "Tarjouspyyntö (PDF)", "url": "https://tarjouspalvelu.fi/oulu?id=600700"},
            {"name": "IoT-arkkitehtuuri (PDF)", "url": "https://tarjouspalvelu.fi/oulu?id=600700&att=arch"},
            {"name": "HILMA Notice", "url": "https://www.hankintailmoitukset.fi/fi/notice/2026-DEMO-OULU1"},
        ]),
        opportunity_score=77, raw_data=json.dumps({"source": "demo_seed"}),
    ),
    dict(
        external_id="DEMO-TURKU-001", source="FinnishCities", type="RFI", status="OPEN",
        title="Tietopyyntö: Digitaalinen kaksonen Turun satamalle",
        description="Turun Satama Oy pyytää tietoja digitaalisen kaksosen (digital twin) toimittajilta "
                    "sataman operatiivista suunnittelua varten. Ratkaisu integroituu AIS-järjestelmään "
                    "ja laiturinohjausjärjestelmiin. Tietopyyntö edeltää hankintamenettelyä.",
        contracting_authority="Turun Satama Oy",
        company_size="SME", published_date="2026-08-12", deadline_date="2026-10-12",
        estimated_value=None, currency="EUR",
        source_url="https://www.hankintailmoitukset.fi/fi/notice/2026-DEMO-TURKU1",
        cpv_codes=json.dumps(["72000000", "63000000"]),
        keywords=json.dumps(["digital twin", "port", "maritime", "simulation", "AIS"]),
        buyer_email="kilpailutus@portofturku.fi",
        buyer_phone="+358 2 267 3100",
        pdf_urls=json.dumps([
            {"name": "Tietopyyntö (PDF)", "url": "https://tarjouspalvelu.fi/turkusatama?id=600800"},
            {"name": "HILMA Notice", "url": "https://www.hankintailmoitukset.fi/fi/notice/2026-DEMO-TURKU1"},
        ]),
        opportunity_score=73, raw_data=json.dumps({"source": "demo_seed"}),
    ),
]

# Map industry names to their DB ids
INDUSTRY_MAP = {
    "IT & Software":               ["72", "48", "73", "software", "cloud", "digital", "ai", "cyber",
                                    "IoT", "data", "SaaS", "ERP", "platform", "ehr", "kanta",
                                    "drone", "digital twin", "smart", "twin"],
    "Healthcare & Social Services":["terveys", "health", "potilastieto", "sairaala", "hoito",
                                    "dialyysi", "lääke", "kela", "sosiaali"],
    "Construction & Real Estate":  ["rakennus", "saneeraus", "construction", "peruskorjaus", "talo"],
    "Transport & Logistics":        ["transport", "liikenne", "HSL", "ticketing", "ajoneuvot",
                                    "satama", "maritime", "port"],
    "Energy & Environment":         ["energy", "energia", "helen", "fortum", "hydrogen", "vihreä",
                                    "smart grid", "solar"],
    "Education & Research":         ["university", "yliopisto", "koulu", "oppiminen", "CSC",
                                    "Jyväskylä", "research", "HPC"],
    "Finance & Insurance":          ["taloushallin", "financial", "accounting", "ERP", "kirjanpito"],
    "Defence & Security":           ["border", "defence", "security", "tietoturva", "cyber",
                                    "puolustus", "raja", "defmin"],
}

LOCATION_MAP = {
    "Helsinki":    ["Helsinki", "Helen", "HSL", "Kela", "Valtiokonttori", "Hansel", "CSC"],
    "Espoo":       ["Espoo"],
    "Tampere":     ["Tampere", "Pirkanmaa", "Pirha"],
    "Turku":       ["Turku"],
    "Oulu":        ["Oulu"],
    "Jyväskylä":   ["Jyväskylä"],
    "Kuopio":      ["Kuopio"],
    "Nationwide":  ["Hansel", "Valtiokonttori", "CSC", "Finnish Government", "Finnish Border"],
}


def classify(text, mapping):
    text_l = text.lower()
    for name, kws in mapping.items():
        if any(kw.lower() in text_l for kw in kws):
            return name
    return "Other"


inserted = updated = 0
for n in NOTICES:
    full_text = f"{n['title']} {n.get('description', '')} {n.get('contracting_authority', '')}"
    industry  = classify(full_text, INDUSTRY_MAP)
    location  = classify(full_text, LOCATION_MAP)

    n["industry_area_id"] = resolve_industry_id(industry)
    n["location_id"]      = resolve_location_id(location)

    # defaults
    n.setdefault("estimated_value", None)
    n.setdefault("currency", "EUR")

    result = upsert_tender(n)
    if result == "inserted":
        inserted += 1
    else:
        updated += 1
    print(f"  {result}: [{n['type']}] {n['title'][:55]}")

print(f"\nDone — {inserted} inserted, {updated} updated.")
