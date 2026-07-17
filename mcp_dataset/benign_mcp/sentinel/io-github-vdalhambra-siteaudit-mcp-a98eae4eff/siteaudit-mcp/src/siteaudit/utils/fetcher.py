"""URL fetcher with caching, error handling, and proper user-agent."""

import time
import requests
from bs4 import BeautifulSoup
from fastmcp.exceptions import ToolError
from urllib.parse import urlparse

SESSION = requests.Session()
SESSION.headers.update({
    "User-Agent": "SiteAudit-MCP/1.0 (Web Audit Tool; +https://github.com/vdalhambra/siteaudit-mcp)",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
})

# Simple TTL cache
_cache: dict[str, tuple[any, float]] = {}
CACHE_TTL = 300  # 5 minutes


def _normalize_url(url: str) -> str:
    """Ensure URL has a scheme."""
    url = url.strip()
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    return url


def fetch_page(url: str) -> tuple[requests.Response, BeautifulSoup]:
    """Fetch a URL and return the response + parsed HTML."""
    url = _normalize_url(url)

    cache_key = f"page:{url}"
    if cache_key in _cache:
        val, exp = _cache[cache_key]
        if time.time() < exp:
            return val

    try:
        resp = SESSION.get(url, timeout=15, allow_redirects=True)
        resp.raise_for_status()
    except requests.exceptions.ConnectionError:
        raise ToolError(f"Could not connect to '{url}'. Check the URL is correct and the site is up.")
    except requests.exceptions.Timeout:
        raise ToolError(f"Timeout fetching '{url}'. The site took too long to respond.")
    except requests.exceptions.HTTPError as e:
        raise ToolError(f"HTTP error {e.response.status_code} for '{url}'.")
    except requests.RequestException as e:
        raise ToolError(f"Error fetching '{url}': {str(e)}")

    soup = BeautifulSoup(resp.text, "lxml")
    result = (resp, soup)
    _cache[cache_key] = (result, time.time() + CACHE_TTL)
    return result


def fetch_url(url: str) -> requests.Response:
    """Fetch a URL and return raw response (for robots.txt, sitemap, etc.)."""
    url = _normalize_url(url)
    try:
        resp = SESSION.get(url, timeout=10, allow_redirects=True)
        return resp
    except requests.RequestException:
        return None


def get_domain(url: str) -> str:
    """Extract domain from URL."""
    url = _normalize_url(url)
    parsed = urlparse(url)
    return parsed.netloc or parsed.path.split("/")[0]
