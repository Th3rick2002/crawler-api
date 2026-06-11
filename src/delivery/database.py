import os
import sqlite3
from typing import Dict, List, Tuple

DB_PATH = os.path.join("data", "3_gold_delivery.db")

def get_db_connection() -> sqlite3.Connection:
    """Establishes and returns a connection to the Gold database."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def get_metrics() -> Dict[str, str]:
    """Retrieves all stored metrics as a dictionary."""
    metrics = {
        "total_pages_crawled": "0",
        "careers_found": "0",
        "errors_intercepted": "0",
        "last_processed_at": "Never"
    }
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT key, value FROM metrics")
            rows = cursor.fetchall()
            for row in rows:
                metrics[row["key"]] = row["value"]
    except sqlite3.OperationalError:
        # DB or table might not exist yet
        pass
    return metrics

def get_careers(
    degree_type: str = "",
    academic_area: str = "",
    search_query: str = ""
) -> List[Dict]:
    """Retrieves filtered list of careers from the Gold database."""
    careers = []
    query = "SELECT id, url, title, degree_type, academic_area, description, extracted_at FROM careers WHERE 1=1"
    params = []
    
    if degree_type:
        query += " AND degree_type = ?"
        params.append(degree_type)
        
    if academic_area:
        query += " AND academic_area = ?"
        params.append(academic_area)
        
    if search_query:
        query += " AND (title LIKE ? OR description LIKE ?)"
        params.append(f"%{search_query}%")
        params.append(f"%{search_query}%")
        
    query += " ORDER BY title ASC"
    
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()
            careers = [dict(row) for row in rows]
    except sqlite3.OperationalError:
        pass
    return careers

def get_filter_options() -> Tuple[List[str], List[str]]:
    """Retrieves distinct values for degree types and academic areas to populate filters."""
    degree_types = []
    academic_areas = []
    
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("SELECT DISTINCT degree_type FROM careers WHERE degree_type IS NOT NULL ORDER BY degree_type ASC")
            degree_types = [row["degree_type"] for row in cursor.fetchall() if row["degree_type"]]
            
            cursor.execute("SELECT DISTINCT academic_area FROM careers WHERE academic_area IS NOT NULL ORDER BY academic_area ASC")
            academic_areas = [row["academic_area"] for row in cursor.fetchall() if row["academic_area"]]
    except sqlite3.OperationalError:
        pass
        
    return degree_types, academic_areas

def clear_gold_db() -> None:
    """Clears all records from the Gold database."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM careers")
            cursor.execute("DELETE FROM metrics")
            conn.commit()
    except sqlite3.OperationalError:
        pass

