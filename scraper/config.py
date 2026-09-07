"""
RFI Hunter — Shared configuration loaded from .env
"""
import os
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    "host":     os.getenv("DB_HOST", "localhost"),
    "port":     int(os.getenv("DB_PORT", "3306")),
    "database": os.getenv("DB_NAME", "rfihunter"),
    "user":     os.getenv("DB_USER", "rfihunter"),
    "password": os.getenv("DB_PASS", "rfihunter_pass"),
    "charset":  "utf8mb4",
    "use_unicode": True,
    "autocommit": False,
}

SCRAPE_INTERVAL_HOURS = int(os.getenv("SCRAPE_INTERVAL_HOURS", "6"))
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
