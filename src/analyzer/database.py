import os
import sqlite3
from datetime import datetime
from typing import Dict, List, Tuple

DB_PATH = os.path.join("data", "2_silver_analytics.db")

def get_db_connection() -> sqlite3.Connection:
    """Establishes and returns a connection to the Silver database."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db() -> None:
    """Initializes the Silver database by creating tables if they do not exist."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Processed content table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS processed_pages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT UNIQUE NOT NULL,
                title TEXT,
                cleaned_text TEXT NOT NULL,
                processed_at TEXT NOT NULL
            )
        """)
        
        # Word frequency metrics
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS word_frequencies (
                word TEXT PRIMARY KEY,
                frequency INTEGER NOT NULL
            )
        """)
        
        # Dynamic filter counts
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS degree_counts (
                degree_type TEXT PRIMARY KEY,
                count INTEGER NOT NULL
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS area_counts (
                academic_area TEXT PRIMARY KEY,
                count INTEGER NOT NULL
            )
        """)
        
        conn.commit()

def clear_silver_db() -> None:
    """Clears all Silver database metrics tables."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM processed_pages")
        cursor.execute("DELETE FROM word_frequencies")
        cursor.execute("DELETE FROM degree_counts")
        cursor.execute("DELETE FROM area_counts")
        conn.commit()

def save_processed_page(url: str, title: str, cleaned_text: str) -> None:
    """Saves a processed and cleaned career page."""
    now = datetime.utcnow().isoformat()
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO processed_pages (url, title, cleaned_text, processed_at)
            VALUES (?, ?, ?, ?)
        """, (url, title, cleaned_text, now))
        conn.commit()

def save_word_frequencies(frequencies: Dict[str, int]) -> None:
    """Saves word frequencies (replaces existing content)."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM word_frequencies")
        cursor.executemany("""
            INSERT INTO word_frequencies (word, frequency)
            VALUES (?, ?)
        """, list(frequencies.items()))
        conn.commit()

def save_degree_counts(counts: Dict[str, int]) -> None:
    """Saves academic degree counts."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM degree_counts")
        cursor.executemany("""
            INSERT INTO degree_counts (degree_type, count)
            VALUES (?, ?)
        """, list(counts.items()))
        conn.commit()

def save_area_counts(counts: Dict[str, int]) -> None:
    """Saves academic area/faculty counts."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM area_counts")
        cursor.executemany("""
            INSERT INTO area_counts (academic_area, count)
            VALUES (?, ?)
        """, list(counts.items()))
        conn.commit()

def get_word_frequencies(limit: int = 50) -> List[Dict]:
    """Retrieves top N most common words from the Silver database."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT word, frequency FROM word_frequencies ORDER BY frequency DESC LIMIT ?", (limit,))
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

def get_analytics_summary() -> Dict:
    """Retrieves computed counts for UI charts."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        cursor.execute("SELECT degree_type, count FROM degree_counts ORDER BY count DESC")
        degrees = [dict(row) for row in cursor.fetchall()]
        
        cursor.execute("SELECT academic_area, count FROM area_counts ORDER BY count DESC")
        areas = [dict(row) for row in cursor.fetchall()]
        
        return {
            "degrees": degrees,
            "areas": areas
        }
