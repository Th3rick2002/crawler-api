import os
import sqlite3
from fastapi import APIRouter, Request, BackgroundTasks, Query, Response, HTTPException
from fastapi.responses import HTMLResponse, StreamingResponse, FileResponse
from fastapi.templating import Jinja2Templates
from typing import Optional

import src.delivery.database as gold_db
import src.delivery.reporting as reporting
import src.crawler.database as bronze_db
import src.analyzer.database as silver_db
from src.crawler.engine import crawl_website, status_tracker
from src.analyzer.pipeline import run_analytics_pipeline

router = APIRouter()

# Resolve templates directory relative to this file
TEMPLATES_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "templates")
templates = Jinja2Templates(directory=TEMPLATES_DIR)

# --- WEB PAGE ROUTES ---

@router.get("/", response_class=HTMLResponse)
async def get_dashboard(request: Request):
    """Renders the main dashboard page with key metrics and charts."""
    metrics = gold_db.get_metrics()
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"metrics": metrics, "crawler_status": status_tracker}
    )

@router.get("/explore", response_class=HTMLResponse)
async def explore_data(
    request: Request,
    degree_type: Optional[str] = Query("", description="Filter by academic degree"),
    academic_area: Optional[str] = Query("", description="Filter by field of study"),
    search: Optional[str] = Query("", description="Keyword search in title/details")
):
    """Renders the data table explorer page with active search and filtering."""
    careers = gold_db.get_careers(degree_type, academic_area, search)
    degree_options, area_options = gold_db.get_filter_options()
    metrics = gold_db.get_metrics()
    
    return templates.TemplateResponse(
        request=request,
        name="explore.html",
        context={
            "careers": careers,
            "degree_options": degree_options,
            "area_options": area_options,
            "selected_degree": degree_type,
            "selected_area": academic_area,
            "search_query": search,
            "metrics": metrics
        }
    )

# --- API ENDPOINTS FOR INTERACTIVE UI & CHARTS ---

@router.get("/api/metrics")
async def get_live_metrics():
    """Returns JSON representation of Gold DB summary metrics."""
    return gold_db.get_metrics()

@router.get("/api/charts")
async def get_chart_data():
    """Returns Silver DB processed counts for academic area and degree types, plus top word frequency."""
    silver_summary = silver_db.get_analytics_summary()
    word_freqs = silver_db.get_word_frequencies(30) # Top 30 words
    
    return {
        "degrees": silver_summary["degrees"],
        "areas": silver_summary["areas"],
        "word_frequencies": word_freqs
    }

@router.get("/api/errors")
async def get_crawler_errors():
    """Returns list of crawler failure logs stored in Bronze database."""
    return bronze_db.get_failed_urls()

@router.get("/api/crawler/status")
async def get_crawler_status():
    """Retrieves current background crawler status."""
    return {
        "is_running": status_tracker.is_running,
        "pages_crawled": status_tracker.pages_crawled,
        "pages_failed": status_tracker.pages_failed,
        "current_url": status_tracker.current_url,
        "start_time": status_tracker.start_time,
        "end_time": status_tracker.end_time,
        "seed_url": status_tracker.seed_url,
        "message": status_tracker.message
    }

@router.post("/api/crawler/start")
async def start_crawler_task(
    background_tasks: BackgroundTasks,
    seed_url: str = Query(..., description="The university base URL to start crawling from"),
    max_pages: int = Query(50, description="Max pages to crawl"),
    max_depth: int = Query(3, description="BFS depth limit")
):
    """Triggers the BFS crawler background task which runs asynchronously."""
    if status_tracker.is_running:
        return {"status": "error", "message": "Crawler is already running."}
        
    # Clear old Bronze & Silver & Gold records before a fresh manual start if requested,
    # or keep incremental. Let's clear to prevent dirty mixes of different universities.
    bronze_db.clear_bronze_db()
    
    # Add BFS crawl loop to background tasks with analytics post-crawl callback
    background_tasks.add_task(
        crawl_website,
        seed_url=seed_url,
        max_pages=max_pages,
        max_depth=max_depth,
        on_complete_callback=run_analytics_pipeline
    )
    
    return {"status": "success", "message": "Crawler started in background."}

@router.post("/api/crawler/stop")
async def stop_crawler_task():
    """Instructs the crawler to stop execution safely on its next iteration."""
    if not status_tracker.is_running:
        return {"status": "error", "message": "Crawler is not running."}
        
    status_tracker.is_running = False
    status_tracker.message = "Stopping requested..."
    return {"status": "success", "message": "Stop command sent to crawler."}

@router.post("/api/pipeline/run")
async def trigger_analytics_pipeline():
    """Manually triggers the analytics pipeline using currently saved Bronze raw data."""
    try:
        run_analytics_pipeline()
        return {"status": "success", "message": "Analytics pipeline executed successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Pipeline error: {str(e)}")

@router.post("/api/data/clear")
async def clear_all_data():
    """Clears all records from Bronze, Silver, and Gold databases."""
    try:
        bronze_db.clear_bronze_db()
        silver_db.clear_silver_db()
        gold_db.clear_gold_db()
        return {"status": "success", "message": "All database stages cleared successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database clearing failed: {str(e)}")


# --- DATA EXPORT DOWNLOADS ---

@router.get("/export/excel")
async def download_excel_export(
    degree_type: Optional[str] = "",
    academic_area: Optional[str] = "",
    search: Optional[str] = ""
):
    """Streams the filtered academic careers in Excel format."""
    try:
        buffer = reporting.generate_excel_report(degree_type, academic_area, search)
        filename = f"oferta_academica_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        return StreamingResponse(
            buffer,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate Excel report: {str(e)}")

@router.get("/export/pdf")
async def download_pdf_export(
    degree_type: Optional[str] = "",
    academic_area: Optional[str] = "",
    search: Optional[str] = ""
):
    """Streams the filtered academic careers in PDF format."""
    try:
        pdf_bytes = reporting.generate_pdf_report(degree_type, academic_area, search)
        filename = f"oferta_academica_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate PDF report: {str(e)}")

@router.get("/export/db")
async def download_gold_database():
    """Provides direct download of the clean Gold Delivery SQLite database file."""
    if not os.path.exists(reporting.GOLD_DB_FILE):
        raise HTTPException(status_code=404, detail="Gold database has not been populated yet.")
        
    filename = "3_gold_delivery.db"
    return FileResponse(
        path=reporting.GOLD_DB_FILE,
        filename=filename,
        media_type="application/octet-stream"
    )
