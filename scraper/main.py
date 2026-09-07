"""
RFI Hunter — Scraper entry point.

Usage:
  python main.py               # start scheduled mode (every N hours)
  python main.py --run-now     # single immediate run then exit
  python main.py --source HILMA --run-now
"""
import argparse
import logging
import sys
import time

import schedule

from config import SCRAPE_INTERVAL_HOURS, LOG_LEVEL, DB_CONFIG
from db import init_schema, upsert_tender, start_run, finish_run
from scrapers import ALL_SCRAPERS

logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("main")


def wait_for_db(retries: int = 15, delay: int = 5) -> None:
    import mysql.connector
    for i in range(retries):
        try:
            conn = mysql.connector.connect(**DB_CONFIG)
            conn.close()
            logger.info("Database is reachable.")
            return
        except mysql.connector.Error as exc:
            logger.warning("DB not ready (%d/%d): %s", i + 1, retries, exc)
            time.sleep(delay)
    raise RuntimeError("Database did not become available in time.")


def run_scraper(scraper_cls, dry_run: bool = False) -> None:
    name = scraper_cls.SOURCE_NAME
    logger.info("▶ Starting scrape: %s", name)
    run_id = start_run(name)

    new_count = upd_count = err_count = 0
    error_msg = None

    try:
        scraper = scraper_cls()
        for record in scraper.scrape():
            try:
                if dry_run:
                    logger.debug("DRY RUN — would upsert: %s", record.get("title", "")[:80])
                    continue
                result = upsert_tender(record)
                if result == "inserted":
                    new_count += 1
                else:
                    upd_count += 1
            except Exception as exc:
                err_count += 1
                logger.error("Upsert failed (%s): %s", record.get("external_id"), exc)
    except Exception as exc:
        error_msg = str(exc)
        logger.exception("Scraper %s crashed: %s", name, exc)

    finish_run(run_id, new_count, upd_count, err_count, error_msg)
    logger.info(
        "✔ %s finished — new=%d updated=%d errors=%d",
        name, new_count, upd_count, err_count,
    )


def run_all(source_filter: str = None, dry_run: bool = False) -> None:
    scrapers = [
        cls for cls in ALL_SCRAPERS
        if source_filter is None or cls.SOURCE_NAME.upper() == source_filter.upper()
    ]
    if not scrapers:
        logger.error("No scraper matched source filter '%s'", source_filter)
        return
    for cls in scrapers:
        run_scraper(cls, dry_run=dry_run)


def main() -> None:
    parser = argparse.ArgumentParser(description="RFI Hunter Scraper")
    parser.add_argument("--run-now",  action="store_true", help="Run once immediately then exit")
    parser.add_argument("--source",   default=None,        help="Restrict to one source (e.g. HILMA)")
    parser.add_argument("--dry-run",  action="store_true", help="Scrape but do not write to DB")
    args = parser.parse_args()

    wait_for_db()
    init_schema()

    if args.run_now or args.dry_run:
        run_all(args.source, dry_run=args.dry_run)
        return

    # Scheduled mode
    logger.info("Scheduler started — will run every %d hours.", SCRAPE_INTERVAL_HOURS)
    run_all(args.source)     # immediate first run
    schedule.every(SCRAPE_INTERVAL_HOURS).hours.do(run_all, source_filter=args.source)

    while True:
        schedule.run_pending()
        time.sleep(60)


if __name__ == "__main__":
    main()
