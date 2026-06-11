import os
import re
import string
import sqlite3
import pandas as pd
from bs4 import BeautifulSoup
from datetime import datetime
from typing import Set

from src.analyzer.dynamic_filters import infer_categories
from src.analyzer.database import (
    init_db as init_silver_db,
    clear_silver_db,
    save_processed_page,
    save_word_frequencies,
    save_degree_counts,
    save_area_counts
)
import src.crawler.database as bronze_db

# Load Silver and Gold database paths
GOLD_DB_PATH = "data/3_gold_delivery.db"

# A comprehensive list of Spanish stopwords + common academic filler words
SPANISH_STOPWORDS: Set[str] = {
    # Pronouns, prepositions, conjunctions, articles
    "de", "la", "que", "el", "en", "y", "a", "los", "del", "se", "las", "un", "para", "con", "no", 
    "una", "su", "al", "lo", "como", "más", "pero", "sus", "les", "este", "o", "donde", "cuando", 
    "nos", "esta", "eso", "entre", "sobre", "también", "desde", "hasta", "mi", "mis", "tu", "tus", 
    "ti", "sí", "si", "por", "otro", "otros", "otra", "otras", "estos", "estas", "ese", "esa", 
    "esos", "esas", "aquel", "aquella", "todo", "todos", "toda", "todas", "cada", "uno", "dos", 
    "tres", "muy", "bien", "así", "asi", "entonces", "luego", "ya", "aún", "aun", "hoy", "aquí", 
    "aqui", "allí", "alli", "cómo", "dónde", "quién", "qué", "segun", "según", "sin", "bajo", 
    "tras", "para", "por", "hacia", "contra",
    # Basic verbs (ser, estar, haber, tener)
    "es", "son", "fue", "fueron", "era", "eran", "ha", "han", "he", "hemos", "había", "habían", 
    "está", "están", "estuvo", "estuvieron", "estaba", "estaban", "tiene", "tienen", "tenía", 
    "tenían", "hace", "hacen", "hacía", "hacían", "puede", "pueden", "ser", "estar", "haber", 
    "tener", "hacer", "para", "sino", "e", "u",
    # Academic noise/filler words that are not useful for analytics
    "carrera", "carreras", "programa", "programas", "universidad", "estudio", "estudios", 
    "estudiante", "estudiantes", "formación", "formacion", "egresado", "egresados", 
    "profesional", "profesionales", "semestre", "semestres", "plan", "asignatura", 
    "asignaturas", "materia", "materias", "año", "años", "curso", "cursos", "perfil", 
    "campo", "laboral", "duración", "duracion", "requisitos", "ingresar", "créditos", "creditos",
    "clases", "aula", "título", "titulo", "grado", "grados", "modalidad", "virtual", 
    "presencial", "académico", "academico", "académica", "academica", "pensum"
}

def clean_text_for_nlp(text: str) -> str:
    """Cleans a string by lowercasing and stripping punctuation for NLP processing."""
    text = text.lower()
    # Remove punctuation
    translator = str.maketrans("", "", string.punctuation + "¡!¿?«»“”‘’")
    text = text.translate(translator)
    # Remove digits/numbers
    text = re.sub(r"\d+", "", text)
    return text

def extract_metadata_from_html(html_content: str, url: str) -> tuple[str, str]:
    """Extracts a clean title and semantic text description from raw HTML."""
    soup = BeautifulSoup(html_content, "html.parser")
    
    # Extract Title
    title = ""
    # Try <h1> first (usually contains the career name)
    h1_tag = soup.find("h1")
    if h1_tag:
        title = h1_tag.get_text(strip=True)
    
    # Fallback to <title>
    if not title:
        title_tag = soup.find("title")
        if title_tag:
            title = title_tag.get_text(strip=True)
            # Remove site name suffix if common (e.g. "Software Engineering | University of...")
            if " | " in title:
                title = title.split(" | ")[0]
            elif " - " in title:
                title = title.split(" - ")[0]
                
    # Final fallback to URL path
    if not title:
        path_parts = [p for p in url.split("/") if p]
        if path_parts:
            title = path_parts[-1].replace("-", " ").replace("_", " ").title()
        else:
            title = "Página sin título"
            
    # Extract description text (cleaned of tags)
    description = soup.get_text(separator=" ", strip=True)
    # Compress multiple spaces
    description = re.sub(r"\s+", " ", description)
    
    return title, description

def init_gold_db() -> None:
    """Initializes the Gold database schemas."""
    os.makedirs(os.path.dirname(GOLD_DB_PATH), exist_ok=True)
    conn = sqlite3.connect(GOLD_DB_PATH)
    cursor = conn.cursor()
    
    # Normalized careers table for delivery
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS careers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT UNIQUE NOT NULL,
            title TEXT NOT NULL,
            degree_type TEXT NOT NULL,
            academic_area TEXT NOT NULL,
            description TEXT NOT NULL,
            extracted_at TEXT NOT NULL
        )
    """)
    
    # Table for summary metrics
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS metrics (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

def run_analytics_pipeline() -> None:
    """
    Pandas Ingestion & NLP mining:
    1. Reads raw data from Bronze (1_bronze_raw.db).
    2. Performs text extraction, category inference, and stores cleaned data in Silver.
    3. Runs Pandas value_counts to aggregate degree and area distributions, and counts word frequencies.
    4. Populates Gold (3_gold_delivery.db) with structured metrics and careers list.
    """
    print("[ANALYTICS] Starting analytics mining pipeline...")
    
    # 1. Read raw crawled pages from Bronze
    raw_pages = bronze_db.get_all_raw_pages()
    if not raw_pages:
        print("[ANALYTICS] No raw pages found in Bronze database. Aborting pipeline.")
        return
        
    # Initialize Silver and Gold databases
    init_silver_db()
    clear_silver_db()
    init_gold_db()
    
    # Load into Pandas DataFrame
    df_raw = pd.DataFrame(raw_pages)
    
    processed_records = []
    all_words = []
    
    # 2. Extract title, clean description, and infer filters for each page
    for idx, row in df_raw.iterrows():
        url = row["url"]
        html_content = row["html_content"]
        
        # Extract metadata
        title, description = extract_metadata_from_html(html_content, url)
        
        # Skip pages that are too short or don't look like content pages (e.g. index directories)
        if len(description) < 150:
            continue
            
        # Infer categories using rule engine
        degree_type, academic_area = infer_categories(title, description)
        
        # Save to Silver database (clean processed text)
        save_processed_page(url, title, description)
        
        # Track record
        processed_records.append({
            "url": url,
            "title": title,
            "degree_type": degree_type,
            "academic_area": academic_area,
            "description": description,
            "extracted_at": datetime.utcnow().isoformat()
        })
        
        # NLP Tokenization & Cleaning for Word Frequency
        clean_text = clean_text_for_nlp(title + " " + description)
        words = [w for w in clean_text.split() if w not in SPANISH_STOPWORDS and len(w) >= 3]
        all_words.extend(words)

    if not processed_records:
        print("[ANALYTICS] No career profiles could be extracted from pages. Aborting.")
        return
        
    # Convert processed records to Pandas DataFrame
    df_processed = pd.DataFrame(processed_records)
    
    # 3. Calculate metrics using Pandas value_counts()
    degree_counts = df_processed["degree_type"].value_counts().to_dict()
    area_counts = df_processed["academic_area"].value_counts().to_dict()
    
    # Calculate word frequency counts
    word_series = pd.Series(all_words)
    word_freqs = word_series.value_counts().head(100).to_dict()  # top 100 words
    
    # Save computed metrics to Silver DB
    save_degree_counts(degree_counts)
    save_area_counts(area_counts)
    save_word_frequencies(word_freqs)
    
    # 4. Populate Gold DB (3_gold_delivery.db)
    # Clear Gold careers first and repopulate
    conn_gold = sqlite3.connect(GOLD_DB_PATH)
    cursor_gold = conn_gold.cursor()
    cursor_gold.execute("DELETE FROM careers")
    
    # Batch insert to Gold
    careers_data = df_processed[["url", "title", "degree_type", "academic_area", "description", "extracted_at"]].values.tolist()
    cursor_gold.executemany("""
        INSERT OR REPLACE INTO careers (url, title, degree_type, academic_area, description, extracted_at)
        VALUES (?, ?, ?, ?, ?, ?)
    """, careers_data)
    
    # Calculate Summary Metrics
    total_pages_crawled, errors_intercepted = bronze_db.get_crawling_stats()
    careers_found = len(df_processed)
    
    metrics = {
        "total_pages_crawled": str(total_pages_crawled),
        "careers_found": str(careers_found),
        "errors_intercepted": str(errors_intercepted),
        "last_processed_at": datetime.utcnow().isoformat()
    }
    
    # Write summary metrics to Gold DB
    cursor_gold.execute("DELETE FROM metrics")
    cursor_gold.executemany("""
        INSERT OR REPLACE INTO metrics (key, value)
        VALUES (?, ?)
    """, list(metrics.items()))
    
    conn_gold.commit()
    conn_gold.close()
    
    print(f"[ANALYTICS] Pipeline complete. Careers extracted: {careers_found}. Frequencies computed.")

if __name__ == "__main__":
    # Test runner
    run_analytics_pipeline()
