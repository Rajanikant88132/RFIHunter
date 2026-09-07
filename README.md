# RFI Hunter — Finland RFI/RFP Aggregator

A full-stack application that scrapes publicly available RFI (Request for Information) and RFP (Request for Proposals) published in Finland, stores them in MySQL, and serves a searchable dashboard.

## Architecture

```
┌─────────────────┐     ┌───────────────┐     ┌────────────────────┐
│  Python Scraper │────▶│  MySQL 8      │◀────│  Node.js/Express   │
│  (scraper/)     │     │  (rfihunter)  │     │  REST API          │
└─────────────────┘     └───────────────┘     └────────┬───────────┘
                                                         │
                                                ┌────────▼───────────┐
                                                │  React Dashboard   │
                                                │  (dashboard/)      │
                                                └────────────────────┘
```

## Sources Scraped

| Source | URL | Type |
|--------|-----|------|
| HILMA (Finland national procurement portal) | hilma.fi | RFI/RFP |
| TED (EU Tenders Electronic Daily) | ted.europa.eu | RFI/RFP |
| Hankintailmoitukset.fi | hankintailmoitukset.fi | RFI/RFP |
| Business Finland | businessfinland.fi | RFI |
| Traficom | traficom.fi | RFP |

## Quick Start (Docker)

```bash
docker-compose up --build
```

- **Dashboard**: http://localhost:3000
- **API**:       http://localhost:4000/api
- **Scraper** runs on schedule (every 6 hours) or manually:

```bash
docker-compose run --rm scraper python main.py --run-now
```

## Manual Setup

### 1. MySQL

```sql
CREATE DATABASE rfihunter CHARACTER SET utf8mb4;
CREATE USER 'rfihunter'@'%' IDENTIFIED BY 'rfihunter_pass';
GRANT ALL ON rfihunter.* TO 'rfihunter'@'%';
```

### 2. Scraper

```bash
cd scraper
pip install -r requirements.txt
cp .env.example .env   # fill in DB credentials
python main.py --run-now
```

### 3. API

```bash
cd api
npm install
cp .env.example .env   # fill in DB credentials
npm start
```

### 4. Dashboard

```bash
cd dashboard
npm install
npm start
```

## Search & Filter Criteria

| Filter | Values |
|--------|--------|
| Industry Area | IT & Software, Construction, Healthcare, Transport, Energy, Education, Defence, Other |
| Location | Helsinki, Espoo, Tampere, Turku, Oulu, Nationwide, Other |
| Company Size | SME, Large, Any |
| Problem Area | Free-text keyword search across title + description |
| Type | RFI, RFP, Both |
| Status | Open, Closed, All |
| Deadline | Date range picker |

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| DB_HOST | localhost | MySQL host |
| DB_PORT | 3306 | MySQL port |
| DB_NAME | rfihunter | Database name |
| DB_USER | rfihunter | DB username |
| DB_PASS | rfihunter_pass | DB password |
| API_PORT | 4000 | API server port |
| SCRAPE_INTERVAL_HOURS | 6 | How often to re-scrape |
# RFIHunter
