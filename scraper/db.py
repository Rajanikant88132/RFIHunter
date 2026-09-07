"""
RFI Hunter — Database helper
Handles connections, upserts, and run-logging against MySQL.
"""
import json
import logging
from contextlib import contextmanager
from datetime import datetime
from typing import Optional

import mysql.connector
from mysql.connector import pooling

from config import DB_CONFIG

logger = logging.getLogger(__name__)

# ── connection pool ────────────────────────────────────────────────────────────
_pool: Optional[pooling.MySQLConnectionPool] = None


def get_pool() -> pooling.MySQLConnectionPool:
    global _pool
    if _pool is None:
        _pool = pooling.MySQLConnectionPool(
            pool_name="rfihunter",
            pool_size=5,
            **DB_CONFIG,
        )
    return _pool


@contextmanager
def get_conn():
    conn = get_pool().get_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


# ── schema bootstrap ───────────────────────────────────────────────────────────
def init_schema(schema_path: str = None) -> None:
    """Run schema.sql on first startup (idempotent CREATE IF NOT EXISTS).
    Searches /app/db/schema.sql (Docker mount) then ../db/schema.sql (local dev)."""
    import os
    if schema_path is None:
        candidates = [
            "/app/db/schema.sql",
            os.path.join(os.path.dirname(__file__), "../db/schema.sql"),
            os.path.join(os.path.dirname(__file__), "schema.sql"),
        ]
        schema_path = next((p for p in candidates if os.path.exists(p)), None)
    if not schema_path:
        logger.warning("schema.sql not found in any known location, skipping init")
        return
    with open(schema_path, "r", encoding="utf-8") as fh:
        raw = fh.read()

    # split on ';' and run statement by statement
    statements = [s.strip() for s in raw.split(";") if s.strip()]
    with get_conn() as conn:
        cur = conn.cursor()
        for stmt in statements:
            try:
                cur.execute(stmt)
            except mysql.connector.Error as exc:
                logger.debug("Schema stmt skipped (%s): %.80s", exc.errno, stmt)
        cur.close()
    logger.info("Schema initialised.")


# ── lookup helpers ─────────────────────────────────────────────────────────────
def resolve_industry_id(name: str) -> Optional[int]:
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("SELECT id FROM industry_areas WHERE name = %s", (name,))
        row = cur.fetchone()
        cur.close()
    return row[0] if row else None


def resolve_location_id(name: str) -> Optional[int]:
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("SELECT id FROM locations WHERE name = %s", (name,))
        row = cur.fetchone()
        cur.close()
    return row[0] if row else None


# ── upsert ─────────────────────────────────────────────────────────────────────
UPSERT_SQL = """
INSERT INTO tenders (
    external_id, source, type, status, title, description,
    contracting_authority, company_size, industry_area_id, location_id,
    published_date, deadline_date, estimated_value, currency,
    source_url, cpv_codes, keywords,
    buyer_email, buyer_phone, pdf_urls,
    opportunity_score, raw_data
) VALUES (
    %(external_id)s, %(source)s, %(type)s, %(status)s, %(title)s, %(description)s,
    %(contracting_authority)s, %(company_size)s, %(industry_area_id)s, %(location_id)s,
    %(published_date)s, %(deadline_date)s, %(estimated_value)s, %(currency)s,
    %(source_url)s, %(cpv_codes)s, %(keywords)s,
    %(buyer_email)s, %(buyer_phone)s, %(pdf_urls)s,
    %(opportunity_score)s, %(raw_data)s
)
ON DUPLICATE KEY UPDATE
    status                = VALUES(status),
    title                 = VALUES(title),
    description           = VALUES(description),
    contracting_authority = VALUES(contracting_authority),
    company_size          = VALUES(company_size),
    industry_area_id      = VALUES(industry_area_id),
    location_id           = VALUES(location_id),
    deadline_date         = VALUES(deadline_date),
    estimated_value       = VALUES(estimated_value),
    cpv_codes             = VALUES(cpv_codes),
    keywords              = VALUES(keywords),
    buyer_email           = VALUES(buyer_email),
    buyer_phone           = VALUES(buyer_phone),
    pdf_urls              = VALUES(pdf_urls),
    opportunity_score     = VALUES(opportunity_score),
    raw_data              = VALUES(raw_data),
    updated_at            = CURRENT_TIMESTAMP
"""


def upsert_tender(record: dict) -> str:
    """
    Insert or update a tender record.
    Returns 'inserted' or 'updated'.
    """
    # serialise JSON fields
    for field in ("cpv_codes", "keywords", "raw_data", "pdf_urls"):
        if record.get(field) is not None and not isinstance(record[field], str):
            record[field] = json.dumps(record[field], ensure_ascii=False)

    # ensure new nullable fields have a default
    record.setdefault("buyer_email", None)
    record.setdefault("buyer_phone", None)
    record.setdefault("pdf_urls", None)

    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(UPSERT_SQL, record)
        affected = cur.rowcount
        cur.close()

    # MySQL: 1 = inserted, 2 = updated
    return "inserted" if affected == 1 else "updated"


# ── scrape run log ─────────────────────────────────────────────────────────────
def start_run(source: str) -> int:
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO scrape_runs (source, status) VALUES (%s, 'RUNNING')",
            (source,),
        )
        run_id = cur.lastrowid
        cur.close()
    return run_id


def finish_run(run_id: int, new: int, upd: int, err: int, error_msg: str = None) -> None:
    status = "FAILED" if error_msg else "SUCCESS"
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            """UPDATE scrape_runs
               SET finished_at=%s, records_new=%s, records_upd=%s,
                   records_err=%s, error_msg=%s, status=%s
               WHERE id=%s""",
            (datetime.utcnow(), new, upd, err, error_msg, status, run_id),
        )
        cur.close()
