import os
import sqlite3
from datetime import datetime
from typing import Dict, List, Tuple

DB_PATH = os.path.join("data", "1_bronze_raw.db")

def get_db_connection() -> sqlite3.Connection:
    """Establishes and returns a connection to the Bronze database."""
    # Ensure data directory exists
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db() -> None:
    """Initializes the Bronze database by creating tables if they do not exist."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Table for successfully crawled pages
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS raw_pages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT UNIQUE NOT NULL,
                html_content TEXT NOT NULL,
                crawled_at TEXT NOT NULL,
                status_code INTEGER NOT NULL
            )
        """)
        
        # Table for tracking failures (404, 500, timeouts, etc.)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS failed_urls (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT NOT NULL,
                error_message TEXT NOT NULL,
                attempted_at TEXT NOT NULL
            )
        """)
        conn.commit()

def clear_bronze_db() -> None:
    """Clears both raw pages and failed logs for starting a fresh crawl."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM raw_pages")
        cursor.execute("DELETE FROM failed_urls")
        conn.commit()

def save_raw_page(url: str, html_content: str, status_code: int) -> None:
    """Saves or updates a successfully crawled raw page."""
    now = datetime.utcnow().isoformat()
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO raw_pages (url, html_content, crawled_at, status_code)
            VALUES (?, ?, ?, ?)
        """, (url, html_content, now, status_code))
        conn.commit()

def save_failed_url(url: str, error_message: str) -> None:
    """Logs a crawler failure in the failed_urls table."""
    now = datetime.utcnow().isoformat()
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO failed_urls (url, error_message, attempted_at)
            VALUES (?, ?, ?)
        """, (url, error_message, now))
        conn.commit()

def get_all_raw_pages() -> List[Dict]:
    """Retrieves all raw pages from the Bronze database."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, url, html_content, crawled_at, status_code FROM raw_pages")
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

def get_failed_urls() -> List[Dict]:
    """Retrieves all logged failures from the Bronze database."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, url, error_message, attempted_at FROM failed_urls ORDER BY attempted_at DESC")
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

def get_crawling_stats() -> Tuple[int, int]:
    """Returns the total number of successfully crawled pages and error entries."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM raw_pages")
        raw_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM failed_urls")
        failed_count = cursor.fetchone()[0]
        
        return raw_count, failed_count
