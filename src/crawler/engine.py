import logging
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from typing import Set, List, Dict, Optional, Callable
from datetime import datetime

from src.crawler.utils import (
    get_random_user_agent,
    polite_delay,
    get_domain,
    clean_url,
    is_valid_internal_url
)
from src.crawler.database import init_db, save_raw_page, save_failed_url

# Configure console logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("CrawlerEngine")

class CrawlerStatus:
    def __init__(self):
        self.is_running: bool = False
        self.pages_crawled: int = 0
        self.pages_failed: int = 0
        self.current_url: str = ""
        self.start_time: Optional[str] = None
        self.end_time: Optional[str] = None
        self.seed_url: str = ""
        self.message: str = "Idle"

# Global crawler status tracker
status_tracker = CrawlerStatus()

def crawl_website(
    seed_url: str,
    max_pages: int = 50,
    max_depth: int = 3,
    on_complete_callback: Optional[Callable[[], None]] = None
) -> None:
    """
    Executes a BFS crawling loop starting from the seed_url up to max_pages and max_depth.
    Runs in a background thread/task.
    """
    global status_tracker
    
    # Initialize state
    status_tracker.is_running = True
    status_tracker.pages_crawled = 0
    status_tracker.pages_failed = 0
    status_tracker.current_url = seed_url
    status_tracker.start_time = datetime.utcnow().isoformat()
    status_tracker.end_time = None
    status_tracker.seed_url = seed_url
    status_tracker.message = "Starting crawl..."
    
    logger.info(f"Starting BFS crawl from seed: {seed_url} (max_pages={max_pages}, max_depth={max_depth})")
    
    # Initialize DB
    init_db()
    
    # Split seed_url by commas, semicolons, or newlines to support lists of URLs
    raw_urls = []
    for line in seed_url.replace("\r", "").split("\n"):
        for part in line.split(","):
            for subpart in part.split(";"):
                url = subpart.strip()
                if url:
                    raw_urls.append(url)

    # Setup BFS structures
    urls = []
    allowed_domains = set()
    for url in raw_urls:
        domain = get_domain(url)
        if domain:
            urls.append(clean_url(url))
            allowed_domains.add(domain)
            
    if not urls:
        error_msg = f"No valid seed URLs parsed from: {seed_url}"
        logger.error(error_msg)
        save_failed_url(seed_url, error_msg)
        status_tracker.is_running = False
        status_tracker.pages_failed += 1
        status_tracker.end_time = datetime.utcnow().isoformat()
        status_tracker.message = f"Failed: {error_msg}"
        return

    visited_urls: Set[str] = set(urls)
    url_queue: List[tuple] = [(url, 0) for url in urls]  # Queue of (url, current_depth)
    
    session = requests.Session()
    
    while url_queue and status_tracker.pages_crawled < max_pages:
        # Check if crawler was stopped or if something went wrong
        if not status_tracker.is_running:
            logger.info("Crawler stopped by user request.")
            status_tracker.message = "Stopped by user"
            break
            
        current_url, depth = url_queue.pop(0)
        status_tracker.current_url = current_url
        status_tracker.message = f"Crawling page {status_tracker.pages_crawled + 1}: {current_url}"
        
        if depth > max_depth:
            continue
            
        # Web politeness delay
        polite_delay()
        
        headers = {"User-Agent": get_random_user_agent()}
        
        try:
            logger.info(f"Visiting page: {current_url} (depth={depth})")
            response = session.get(current_url, headers=headers, timeout=10)
            
            if response.status_code != 200:
                error_msg = f"HTTP {response.status_code} - {response.reason}"
                logger.warning(f"[ERROR] Failed to fetch: {current_url} ({error_msg})")
                save_failed_url(current_url, error_msg)
                status_tracker.pages_failed += 1
                continue
                
            content_type = response.headers.get("Content-Type", "")
            if "text/html" not in content_type:
                logger.info(f"Skipping non-HTML page: {current_url} ({content_type})")
                continue
                
            # Parse html content
            html_text = response.text
            soup = BeautifulSoup(html_text, "html.parser")
            
            # Find the main semantic content
            main_element = None
            for selector in ("main", "article", "#content", ".content", "#main", ".main"):
                main_element = soup.find(selector)
                if main_element:
                    break
            
            if not main_element:
                main_element = soup.find("body")
                
            if not main_element:
                main_element = soup  # Fallback to full document if no body is found
                
            # Create a clone/copy or clean in place the main content to avoid header/footer/sidebars
            # We remove elements that are noisy
            for noise_tag in ("header", "footer", "nav", "aside", "script", "style", "form", "iframe"):
                for element in main_element.find_all(noise_tag):
                    element.decompose()
            
            # Clean semantic content HTML representation
            semantic_html = str(main_element)
            
            # Save raw semantic HTML in Bronze database
            save_raw_page(current_url, semantic_html, response.status_code)
            status_tracker.pages_crawled += 1
            logger.info(f"[OK] Visiting page: {current_url}")
            
            # Extract internal links from the main content (or full soup to find all structural links)
            internal_links_count = 0
            for link_tag in soup.find_all("a", href=True):
                raw_href = link_tag.get("href")
                # Resolve relative URL
                full_link = urljoin(current_url, raw_href)
                cleaned_link = clean_url(full_link)
                
                if is_valid_internal_url(cleaned_link, allowed_domains):
                    if cleaned_link not in visited_urls:
                        visited_urls.add(cleaned_link)
                        url_queue.append((cleaned_link, depth + 1))
                        internal_links_count += 1
                        
            logger.info(f"[OK] Internal links found: {internal_links_count}")
            
        except requests.exceptions.RequestException as e:
            error_msg = str(e)
            logger.warning(f"[ERROR] Exception requesting {current_url}: {error_msg}")
            save_failed_url(current_url, error_msg)
            status_tracker.pages_failed += 1
            
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            logger.error(f"[ERROR] processing {current_url}: {error_msg}")
            save_failed_url(current_url, error_msg)
            status_tracker.pages_failed += 1

    status_tracker.is_running = False
    status_tracker.end_time = datetime.utcnow().isoformat()
    status_tracker.message = f"Completed. Crawled {status_tracker.pages_crawled} pages. Failed {status_tracker.pages_failed} pages."
    logger.info(f"Crawl completed. {status_tracker.message}")
    
    # Trigger post-crawl analytics pipeline if callback is registered
    if on_complete_callback:
        logger.info("Triggering post-crawl analytics pipeline...")
        try:
            on_complete_callback()
        except Exception as e:
            logger.error(f"Error during post-crawl callback: {str(e)}")
