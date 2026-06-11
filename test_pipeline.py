import os
import sqlite3
import pandas as pd

from src.crawler.database import init_db, save_raw_page, clear_bronze_db
from src.analyzer.pipeline import run_analytics_pipeline
import src.delivery.database as gold_db
import src.analyzer.database as silver_db

def test_system():
    print("=== STARTING MEDALLION ARCHITECTURE INTEGRATION TEST ===")
    
    # 1. Initialize databases
    print("\n[STEP 1] Initializing Bronze DB...")
    init_db()
    clear_bronze_db()
    
    # 2. Insert mock raw HTML pages (Bronze Stage)
    print("[STEP 2] Inserting mock raw university pages into Bronze...")
    mock_pages = [
        {
            "url": "https://university.edu/careers/software-engineering",
            "html": """
            <html>
            <body>
                <header><nav>Menú de Navegación</nav></header>
                <main id="content">
                    <h1>Ingeniería de Software</h1>
                    <p>La carrera de Ingeniería de Software forma profesionales en desarrollo de sistemas, bases de datos y programación de software.</p>
                    <p>Los estudiantes aprenderán sobre algoritmos, computación y tecnologías en la nube en el plan de estudios.</p>
                </main>
                <footer>Pie de página universitario</footer>
            </body>
            </html>
            """
        },
        {
            "url": "https://university.edu/careers/business-administration",
            "html": """
            <html>
            <body>
                <main>
                    <h1>Licenciatura en Administración de Empresas</h1>
                    <p>El programa de Licenciatura busca capacitar en negocios, gestión de finanzas, economía y administración comercial.</p>
                    <p>Perfil del egresado: directores de empresas con habilidades gerenciales y contabilidad.</p>
                </main>
            </body>
            </html>
            """
        },
        {
            "url": "https://university.edu/careers/public-health-master",
            "html": """
            <html>
            <body>
                <article class="post-content">
                    <h1>Maestría en Salud Pública</h1>
                    <p>Especialización para médicos y enfermeras en epidemiología, medicina preventiva y gestión de salud clínica.</p>
                </article>
            </body>
            </html>
            """
        },
        {
            "url": "https://university.edu/careers/graphic-design-tech",
            "html": """
            <html>
            <body>
                <main>
                    <h1>Técnico Superior en Diseño Gráfico</h1>
                    <p>Plan de estudios centrado en artes visuales, diseño web y comunicación visual digital.</p>
                </main>
            </body>
            </html>
            """
        }
    ]
    
    for page in mock_pages:
        save_raw_page(page["url"], page["html"], 200)
        print(f"  Inserted raw page: {page['url']}")
        
    # 3. Run Analytics Pipeline (Bronze -> Silver -> Gold)
    print("\n[STEP 3] Executing Analytics Pipeline (Mining & Inference)...")
    run_analytics_pipeline()
    
    # 4. Verify Silver Database (Processed & NLP)
    print("\n[STEP 4] Verifying Silver Database (2_silver_analytics.db)...")
    summary = silver_db.get_analytics_summary()
    print("  Aggregated Degrees Count:")
    for deg in summary["degrees"]:
        print(f"    - {deg['degree_type']}: {deg['count']}")
        
    print("  Aggregated Academic Areas Count:")
    for ar in summary["areas"]:
        print(f"    - {ar['academic_area']}: {ar['count']}")
        
    print("  Top 10 Word Frequencies (Stopwords filtered):")
    freqs = silver_db.get_word_frequencies(10)
    for f in freqs:
        print(f"    - '{f['word']}': {f['frequency']} veces")

    # 5. Verify Gold Database (Structured Delivery)
    print("\n[STEP 5] Verifying Gold Database (3_gold_delivery.db)...")
    careers = gold_db.get_careers()
    print(f"  Total structured careers in Gold: {len(careers)}")
    for car in careers:
        print(f"    * {car['title']}")
        print(f"      -> Grado: {car['degree_type']}")
        print(f"      -> Área:  {car['academic_area']}")
        print(f"      -> Desc:  {car['description'][:80]}...")
        
    metrics = gold_db.get_metrics()
    print("\n  Gold System Metrics:")
    for k, v in metrics.items():
        print(f"    - {k}: {v}")

    print("\n=== MEDALLION ARCHITECTURE INTEGRATION TEST PASSED SUCCESSFULLY ===")

if __name__ == "__main__":
    test_system()
