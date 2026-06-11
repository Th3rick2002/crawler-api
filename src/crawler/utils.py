import time
import random
from urllib.parse import urlparse, urlunparse

# List of typical User-Agents to rotate
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/115.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
]

# File extensions to ignore when scraping HTML content
IGNORED_EXTENSIONS = (
    ".pdf", ".docx", ".doc", ".xls", ".xlsx", ".ppt", ".pptx", ".zip", ".rar", ".tar", ".gz",
    ".png", ".jpg", ".jpeg", ".gif", ".svg", ".bmp", ".ico", ".mp4", ".mp3", ".avi", ".mov",
    ".css", ".js", ".json", ".xml", ".csv"
)

def get_random_user_agent() -> str:
    """Returns a random User-Agent string from the list."""
    return random.choice(USER_AGENTS)

def polite_delay() -> None:
    """Introduces a randomized delay between 1.5 and 3.5 seconds to respect the web server."""
    delay = random.uniform(1.5, 3.5)
    time.sleep(delay)

def get_domain(url: str) -> str:
    """Extracts the main domain or subdomain from a URL."""
    try:
        parsed = urlparse(url)
        return parsed.netloc.lower()
    except Exception:
        return ""

def clean_url(url: str) -> str:
    """Cleans a URL by removing fragments and query parameters to avoid duplicate crawling."""
    try:
        parsed = urlparse(url)
        # We preserve the scheme, netloc, and path, but drop params, query, and fragment.
        # This keeps URLs uniform (e.g. /carrera?id=1 vs /carrera?id=1#details)
        # Note: sometimes query params are important (e.g., career pages with query parameters).
        # Let's keep query params but strip fragments.
        return urlunparse((parsed.scheme, parsed.netloc, parsed.path, parsed.params, parsed.query, ""))
    except Exception:
        return url

def is_valid_internal_url(url: str, base_domains) -> bool:
    """
    Validates if a URL has an http/https scheme, belongs to the target domain(s) (or subdomains),
    and does not point to a binary file extension.
    """
    try:
        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https"):
            return False
        
        url_domain = parsed.netloc.lower()
        
        # Standardize base_domains to a set of lowercase strings
        if isinstance(base_domains, str):
            domains = {base_domains.lower()}
        else:
            domains = {d.lower() for d in base_domains if d}
            
        # Check if the domain matches or is a subdomain of any allowed domain
        matched = False
        for domain in domains:
            if url_domain == domain or url_domain.endswith("." + domain):
                matched = True
                break
                
        if not matched:
            return False
        
        # Check file extension
        path = parsed.path.lower()
        if path.endswith(IGNORED_EXTENSIONS):
            return False
            
        return True
    except Exception:
        return False
