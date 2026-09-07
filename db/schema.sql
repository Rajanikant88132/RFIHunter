-- RFI Hunter — MySQL Schema
-- Run once on a fresh DB or let Docker entrypoint handle it

CREATE DATABASE IF NOT EXISTS rfihunter CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE rfihunter;

-- ─────────────────────────────────────────────
-- LOOKUP / ENUM TABLES
-- ─────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS industry_areas (
    id   SMALLINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE
);

INSERT IGNORE INTO industry_areas (name) VALUES
  ('IT & Software'),
  ('Construction & Real Estate'),
  ('Healthcare & Social Services'),
  ('Transport & Logistics'),
  ('Energy & Environment'),
  ('Education & Research'),
  ('Defence & Security'),
  ('Finance & Insurance'),
  ('Food & Agriculture'),
  ('Other');

CREATE TABLE IF NOT EXISTS locations (
    id   SMALLINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE
);

INSERT IGNORE INTO locations (name) VALUES
  ('Helsinki'),('Espoo'),('Tampere'),('Turku'),('Oulu'),
  ('Jyväskylä'),('Lahti'),('Kuopio'),('Pori'),('Joensuu'),
  ('Lappeenranta'),('Rovaniemi'),('Nationwide'),('Other');

-- ─────────────────────────────────────────────
-- MAIN TENDERS TABLE
-- ─────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS tenders (
    id               BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    external_id      VARCHAR(255)     NOT NULL,
    source           VARCHAR(100)     NOT NULL,            -- e.g. HILMA, TED, BusinessFinland
    type             ENUM('RFI','RFP','OTHER') NOT NULL DEFAULT 'OTHER',
    status           ENUM('OPEN','CLOSED','UNKNOWN') NOT NULL DEFAULT 'UNKNOWN',

    title            VARCHAR(1000)    NOT NULL,
    description      MEDIUMTEXT,
    contracting_authority VARCHAR(500),
    company_size     ENUM('SME','LARGE','ANY','UNKNOWN') NOT NULL DEFAULT 'UNKNOWN',

    industry_area_id SMALLINT UNSIGNED,
    location_id      SMALLINT UNSIGNED,

    published_date   DATE,
    deadline_date    DATE,
    estimated_value  DECIMAL(18,2),
    currency         VARCHAR(10)      DEFAULT 'EUR',

    source_url       VARCHAR(2000)    NOT NULL,
    cpv_codes        JSON,            -- EU CPV procurement codes
    keywords         JSON,            -- extracted keywords

    -- Buyer / contact information
    buyer_email      VARCHAR(500),
    buyer_phone      VARCHAR(100),

    -- PDF / document attachments (JSON array of {name, url} objects)
    pdf_urls         JSON,

    raw_data         JSON,            -- full raw scraped payload
    opportunity_score TINYINT UNSIGNED DEFAULT 0,  -- 0-100 heuristic score
    related_tender_id BIGINT UNSIGNED,              -- links RFI → follow-on RFP

    created_at       TIMESTAMP        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at       TIMESTAMP        NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    UNIQUE KEY uq_source_external (source, external_id),
    KEY idx_type        (type),
    KEY idx_status      (status),
    KEY idx_industry    (industry_area_id),
    KEY idx_location    (location_id),
    KEY idx_deadline    (deadline_date),
    KEY idx_published   (published_date),
    KEY idx_company_sz  (company_size),
    KEY idx_opp_score   (opportunity_score),

    FULLTEXT KEY ft_title_desc (title, description),

    CONSTRAINT fk_industry FOREIGN KEY (industry_area_id) REFERENCES industry_areas(id),
    CONSTRAINT fk_location FOREIGN KEY (location_id)      REFERENCES locations(id)
);

-- ─────────────────────────────────────────────
-- SCRAPE RUN HISTORY
-- ─────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS scrape_runs (
    id           BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    source       VARCHAR(100)   NOT NULL,
    started_at   TIMESTAMP      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    finished_at  TIMESTAMP,
    records_new  INT UNSIGNED   DEFAULT 0,
    records_upd  INT UNSIGNED   DEFAULT 0,
    records_err  INT UNSIGNED   DEFAULT 0,
    error_msg    TEXT,
    status       ENUM('RUNNING','SUCCESS','FAILED') NOT NULL DEFAULT 'RUNNING'
);
