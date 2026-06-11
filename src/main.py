import uvicorn
from fastapi import FastAPI

import src.crawler.database as bronze_db
import src.analyzer.database as silver_db
import src.analyzer.pipeline as gold_pipeline
from src.delivery.routes import router as delivery_router

app = FastAPI(
    title="University Career Web Crawler & Analytics System",
    description="A multi-stage SQLite (Medallion) web crawler and career parser built with FastAPI, Jinja2, and Pandas.",
    version="1.0.0"
)

# Initialize all database schemas on server startup
@app.on_event("startup")
def startup_event():
    print("[SYSTEM] Initializing Medallion databases...")
    try:
        bronze_db.init_db()
        print("[SYSTEM] Bronze DB initialized successfully.")
    except Exception as e:
        print(f"[SYSTEM] ERROR initializing Bronze DB: {e}")
        
    try:
        silver_db.init_db()
        print("[SYSTEM] Silver DB initialized successfully.")
    except Exception as e:
        print(f"[SYSTEM] ERROR initializing Silver DB: {e}")
        
    try:
        gold_pipeline.init_gold_db()
        print("[SYSTEM] Gold DB initialized successfully.")
    except Exception as e:
        print(f"[SYSTEM] ERROR initializing Gold DB: {e}")

# Include Presentation, API, and Download routes
app.include_router(delivery_router)

if __name__ == "__main__":
    uvicorn.run("src.main:app", host="127.0.0.1", port=8000, reload=True)
