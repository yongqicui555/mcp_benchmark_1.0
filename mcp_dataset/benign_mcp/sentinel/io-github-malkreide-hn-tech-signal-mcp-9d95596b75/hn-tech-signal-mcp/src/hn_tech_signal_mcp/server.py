"""HN Tech Signal MCP Server – 7 Tools for Tech & AI Intelligence.

Aggregates signals from four complementary sources:
  - HackerNews  (community discourse, broad tech)
  - arXiv       (AI/ML research frontier: cs.AI / cs.LG / cs.CL)
  - Lobste.rs   (curated tech signal, higher quality filter)
  - GitHub      (what is actually being built)

No API key required for any source.
Optional: GITHUB_TOKEN for higher GitHub rate limits (5,000 req/h vs 60).

Architecture:
  FRONTIER  →  arXiv API          (cs.AI / cs.LG / cs.CL / cs.CV / stat.ML)
  DISCOURSE →  HackerNews API     (top / best / new stories)
               Lobste.rs JSON API (curated tech community)
  PRACTICE  →  GitHub Search API  (trending repos by topic)
  AGGREGATE →  tech_signal_digest (all sources, one call)
"""

import asyncio
import json
import logging
import os
import time
from collections import OrderedDict
from datetime import datetime, timezone
from typing import Any, Optional
from xml.etree.ElementTree import Element as _XmlElement

import httpx
from defusedxml import ElementTree as _DefusedET
from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, ConfigDict, Field, field_validator

logger = logging.getLogger("hn-tech-signal-mcp")


def _now_iso() -> str:
    """Timezone-aware UTC timestamp string."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

HN_BASE_URL = "https://hacker-news.firebaseio.com/v0"
HN_ALGOLIA_URL = "https://hn.algolia.com/api/v1"
ARXIV_BASE_URL = "https://export.arxiv.org/api/query"
LOBSTERS_BASE_URL = "https://lobste.rs"
GITHUB_BASE_URL = "https://api.github.com"

DEFAULT_TIMEOUT = 20.0
ARXIV_AI_CATEGORIES = ["cs.AI", "cs.LG", "cs.CL", "cs.CV", "cs.NE", "stat.ML"]

# In-memory TTL cache, LRU-bounded to prevent unbounded growth in long-running HTTP mode.
_CACHE_MAX_ENTRIES = 512
_cache: "OrderedDict[str, tuple[float, Any]]" = OrderedDict()
CACHE_TTL: dict[str, int] = {
    "hn_top": 600,
    "hn_search": 300,
    "arxiv": 1800,
    "lobsters": 900,
    "github": 1800,
    "digest": 600,
}


def _cache_get(key: str, ttl_type: str) -> Optional[Any]:
    if key not in _cache:
        return None
    ts, data = _cache[key]
    if time.time() - ts > CACHE_TTL.get(ttl_type, 600):
        del _cache[key]
        return None
    _cache.move_to_end(key)
    return data


def _cache_set(key: str, data: Any) -> None:
    if key in _cache:
        _cache.move_to_end(key)
    _cache[key] = (time.time(), data)
    while len(_cache) > _CACHE_MAX_ENTRIES:
        _cache.popitem(last=False)


# ---------------------------------------------------------------------------
# Server
# ---------------------------------------------------------------------------

server = FastMCP(
    "hn_tech_signal_mcp",
    instructions=(
        "Tech & AI intelligence server aggregating signals from HackerNews, arXiv, "
        "Lobste.rs and GitHub. No API keys required. "
        "Use tech_signal_digest for a full briefing in a single call."
    ),
)


# ---------------------------------------------------------------------------
# Shared HTTP helpers
# ---------------------------------------------------------------------------

_BASE_HEADERS = {
    "Accept": "application/json",
    "User-Agent": "hn-tech-signal-mcp/0.1.0",
}


def _headers_for(url: str) -> dict[str, str]:
    headers = dict(_BASE_HEADERS)
    if url.startswith(GITHUB_BASE_URL):
        token = os.environ.get("GITHUB_TOKEN")
        if token:
            headers["Authorization"] = f"Bearer {token}"
    return headers


async def _get(url: str, params: Optional[dict] = None) -> Any:
    async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
        r = await client.get(url, params=params, headers=_headers_for(url))
        r.raise_for_status()
        return r.json()


async def _get_text(url: str, params: Optional[dict] = None) -> str:
    async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
        r = await client.get(url, params=params, headers=_headers_for(url))
        r.raise_for_status()
        return r.text


def _handle_error(e: Exception, source: str = "") -> str:
    logger.warning(
        "Upstream error from %s: %s: %s",
        source or "unknown",
        type(e).__name__,
        str(e)[:200],
    )
    prefix = f"[{source}] " if source else ""
    if isinstance(e, httpx.HTTPStatusError):
        code = e.response.status_code
        if code == 429:
            return (
                f"{prefix}Error: Rate limit exceeded. "
                "For GitHub, set GITHUB_TOKEN for higher limits."
            )
        if code == 403:
            return f"{prefix}Error: Forbidden (HTTP 403). For GitHub, set GITHUB_TOKEN."
        return f"{prefix}Error: HTTP {code}"
    if isinstance(e, httpx.TimeoutException):
        return f"{prefix}Error: Request timed out. Try again in a moment."
    return f"{prefix}Error: {type(e).__name__}: {str(e)[:200]}"


def _ts_to_iso(ts: Optional[int]) -> str:
    if not ts:
        return "unknown"
    from datetime import timezone

    return datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%d %H:%M UTC")


# ---------------------------------------------------------------------------
# HackerNews helpers
# ---------------------------------------------------------------------------


async def _fetch_hn_stories(story_type: str, limit: int) -> list[dict]:
    ids: list[int] = await _get(f"{HN_BASE_URL}/{story_type}stories.json")
    ids = ids[: min(limit * 3, 120)]

    async def fetch_item(item_id: int) -> Optional[dict]:
        try:
            return await _get(f"{HN_BASE_URL}/item/{item_id}.json")
        except Exception as e:
            logger.debug("HN item %s fetch failed: %s", item_id, e)
            return None

    items = await asyncio.gather(*[fetch_item(i) for i in ids])
    stories = [i for i in items if i and i.get("type") == "story" and i.get("title")]
    return stories[:limit]


def _format_hn_story(s: dict) -> dict:
    return {
        "id": s.get("id"),
        "title": s.get("title", ""),
        "url": s.get("url", f"https://news.ycombinator.com/item?id={s.get('id')}"),
        "score": s.get("score", 0),
        "comments": s.get("descendants", 0),
        "by": s.get("by", ""),
        "posted": _ts_to_iso(s.get("time")),
        "hn_link": f"https://news.ycombinator.com/item?id={s.get('id')}",
    }


# ---------------------------------------------------------------------------
# arXiv helpers
# ---------------------------------------------------------------------------


def _parse_arxiv_entry(entry: _XmlElement, ns: str) -> dict:
    def t(tag: str) -> str:
        el = entry.find(f"{ns}{tag}")
        return el.text.strip() if el is not None and el.text else ""

    authors = [
        a.find(f"{ns}name").text.strip()
        for a in entry.findall(f"{ns}author")
        if a.find(f"{ns}name") is not None
    ][:5]

    link_el = entry.find(f"{ns}link[@rel='alternate']")
    pdf_el = entry.find(f"{ns}link[@title='pdf']")
    cat_el = entry.find("{http://arxiv.org/schemas/atom}primary_category")

    return {
        "id": t("id").split("/abs/")[-1],
        "title": t("title").replace("\n", " "),
        "abstract": t("summary").replace("\n", " ")[:400] + "…",
        "authors": authors,
        "published": t("published")[:10],
        "category": cat_el.get("term", "") if cat_el is not None else "",
        "url": link_el.get("href", t("id")) if link_el is not None else t("id"),
        "pdf": pdf_el.get("href", "") if pdf_el is not None else "",
    }


async def _fetch_arxiv(search_query: str, limit: int) -> list[dict]:
    xml_text = await _get_text(
        ARXIV_BASE_URL,
        {
            "search_query": search_query,
            "start": 0,
            "max_results": limit,
            "sortBy": "submittedDate",
            "sortOrder": "descending",
        },
    )
    root = _DefusedET.fromstring(xml_text)
    ns = "{http://www.w3.org/2005/Atom}"
    return [_parse_arxiv_entry(e, ns) for e in root.findall(f"{ns}entry")]


# ---------------------------------------------------------------------------
# Input models
# ---------------------------------------------------------------------------


class HnTopStoriesInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    feed: str = Field(
        default="top",
        description="Feed type: 'top' (frontpage), 'best' (highest voted), 'new' (latest)",
        pattern="^(top|best|new)$",
    )
    limit: int = Field(default=10, description="Number of stories to return (1–30)", ge=1, le=30)
    min_score: int = Field(default=0, description="Minimum score filter (0 = no filter)", ge=0)


class HnSearchInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    query: str = Field(
        ...,
        description="Search query (e.g. 'Claude MCP', 'LLM agents')",
        min_length=1,
        max_length=200,
    )
    limit: int = Field(default=10, description="Number of results (1–20)", ge=1, le=20)
    days_back: int = Field(default=7, description="Look back N days (1–365)", ge=1, le=365)
    tags: Optional[str] = Field(
        default=None,
        description="HN tag filter: 'story', 'ask_hn', 'show_hn'. Leave empty for all.",
    )


class ArxivLatestInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    categories: list[str] = Field(
        default_factory=lambda: ["cs.AI", "cs.LG"],
        description=(
            "arXiv categories. Options: cs.AI, cs.LG, cs.CL, cs.CV, cs.NE, stat.ML. "
            "Default: ['cs.AI', 'cs.LG']"
        ),
    )
    limit: int = Field(default=10, description="Papers per category (1–20)", ge=1, le=20)

    @field_validator("categories")
    @classmethod
    def validate_categories(cls, v: list[str]) -> list[str]:
        valid = set(ARXIV_AI_CATEGORIES)
        for cat in v:
            if cat not in valid:
                raise ValueError(f"Invalid category '{cat}'. Valid: {sorted(valid)}")
        if not v:
            raise ValueError("At least one category required.")
        return v


class ArxivSearchInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    query: str = Field(
        ...,
        description="Search terms (e.g. 'large language models agents')",
        min_length=1,
        max_length=300,
    )
    category: Optional[str] = Field(
        default=None, description="Restrict to category (e.g. 'cs.AI'). Empty = all."
    )
    limit: int = Field(default=10, description="Number of papers (1–20)", ge=1, le=20)

    @field_validator("category")
    @classmethod
    def validate_category(cls, v: Optional[str]) -> Optional[str]:
        if v is None or v == "":
            return None
        if v not in ARXIV_AI_CATEGORIES:
            raise ValueError(f"Invalid category '{v}'. Valid: {sorted(ARXIV_AI_CATEGORIES)}")
        return v


class LobstersHotInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    limit: int = Field(default=10, description="Number of stories (1–25)", ge=1, le=25)
    tag_filter: Optional[str] = Field(
        default=None,
        description="Filter by tag keyword (e.g. 'ai', 'ml', 'security'). Case-insensitive.",
    )


class GithubTrendingAiInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    topic: str = Field(
        default="llm",
        description="GitHub topic (e.g. 'llm', 'mcp', 'ai-agents', 'rag', 'openai', 'anthropic')",
        min_length=1,
        max_length=100,
    )
    limit: int = Field(default=10, description="Number of repos (1–15)", ge=1, le=15)
    min_stars: int = Field(default=100, description="Minimum star count", ge=0)
    sort: str = Field(
        default="stars",
        description="Sort by: 'stars' (total stars) or 'updated' (recently active)",
        pattern="^(stars|updated)$",
    )


class TechSignalDigestInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    focus: Optional[str] = Field(
        default=None,
        description="Topic focus (e.g. 'MCP', 'agents', 'open source'). Empty = broad overview.",
        max_length=100,
    )
    hn_limit: int = Field(
        default=5, description="HackerNews stories to include (1–10)", ge=1, le=10
    )
    arxiv_limit: int = Field(default=5, description="arXiv papers to include (1–10)", ge=1, le=10)
    lobsters_limit: int = Field(
        default=5, description="Lobste.rs stories to include (1–10)", ge=1, le=10
    )
    github_limit: int = Field(default=5, description="GitHub repos to include (1–10)", ge=1, le=10)


# ---------------------------------------------------------------------------
# Tool 1: hn_top_stories
# ---------------------------------------------------------------------------


@server.tool(
    name="hn_top_stories",
    annotations={
        "title": "HackerNews Top/Best/New Stories",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def hn_top_stories(params: HnTopStoriesInput) -> str:
    """Fetch top, best or new stories from HackerNews.

    Args:
        params (HnTopStoriesInput):
            - feed (str): 'top', 'best', or 'new'
            - limit (int): Stories to return (1–30)
            - min_score (int): Minimum score filter

    Returns:
        str: JSON with feed, count, stories[]. Each story: id, title, url,
             score, comments, by, posted, hn_link.
    """
    cache_key = f"hn_top|{params.feed}|{params.limit}|{params.min_score}"
    if cached := _cache_get(cache_key, "hn_top"):
        return cached
    try:
        stories = await _fetch_hn_stories(params.feed, params.limit * 2)
        if params.min_score > 0:
            stories = [s for s in stories if s.get("score", 0) >= params.min_score]
        stories = stories[: params.limit]
        result = json.dumps(
            {
                "feed": params.feed,
                "fetched_at": _now_iso(),
                "count": len(stories),
                "stories": [_format_hn_story(s) for s in stories],
            },
            indent=2,
            ensure_ascii=False,
        )
        _cache_set(cache_key, result)
        return result
    except Exception as e:
        return _handle_error(e, "HackerNews")


# ---------------------------------------------------------------------------
# Tool 2: hn_search
# ---------------------------------------------------------------------------


@server.tool(
    name="hn_search",
    annotations={
        "title": "HackerNews Full-Text Search (Algolia)",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def hn_search(params: HnSearchInput) -> str:
    """Search HackerNews by keyword using the Algolia search API.

    Covers all historical HN content. Find discussions on specific
    technologies, papers, companies, or events.

    Args:
        params (HnSearchInput):
            - query (str): Search terms
            - limit (int): Results (1–20)
            - days_back (int): Recency window in days
            - tags (Optional[str]): 'story', 'ask_hn', 'show_hn', or empty

    Returns:
        str: JSON with query, total_found, count, hits[]. Each hit: id, title,
             url, score, comments, author, posted, hn_link, excerpt.
    """
    cache_key = f"hn_search|{params.query}|{params.limit}|{params.days_back}|{params.tags}"
    if cached := _cache_get(cache_key, "hn_search"):
        return cached
    try:
        cutoff = int(time.time()) - params.days_back * 86400
        algolia_params: dict[str, Any] = {
            "query": params.query,
            "hitsPerPage": params.limit,
            "numericFilters": f"created_at_i>{cutoff}",
        }
        if params.tags:
            algolia_params["tags"] = params.tags
        data = await _get(f"{HN_ALGOLIA_URL}/search", algolia_params)
        hits = [
            {
                "id": h.get("objectID"),
                "title": h.get("title") or h.get("story_title", ""),
                "url": h.get("url") or f"https://news.ycombinator.com/item?id={h.get('objectID')}",
                "score": h.get("points", 0),
                "comments": h.get("num_comments", 0),
                "author": h.get("author", ""),
                "posted": h.get("created_at", ""),
                "hn_link": f"https://news.ycombinator.com/item?id={h.get('objectID')}",
                "excerpt": (h.get("story_text") or "")[:200],
            }
            for h in data.get("hits", [])
        ]
        result = json.dumps(
            {
                "query": params.query,
                "days_back": params.days_back,
                "total_found": data.get("nbHits", 0),
                "count": len(hits),
                "hits": hits,
            },
            indent=2,
            ensure_ascii=False,
        )
        _cache_set(cache_key, result)
        return result
    except Exception as e:
        return _handle_error(e, "HN Algolia")


# ---------------------------------------------------------------------------
# Tool 3: arxiv_latest
# ---------------------------------------------------------------------------


@server.tool(
    name="arxiv_latest",
    annotations={
        "title": "arXiv Latest AI/ML Papers by Category",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def arxiv_latest(params: ArxivLatestInput) -> str:
    """Fetch the most recently submitted papers from arXiv AI/ML categories.

    Papers appear hours before press coverage — the fastest signal of
    what is happening at the AI research frontier.

    Categories: cs.AI (Artificial Intelligence), cs.LG (Machine Learning),
    cs.CL (NLP), cs.CV (Computer Vision), cs.NE (Neural Computing), stat.ML.

    Args:
        params (ArxivLatestInput):
            - categories (List[str]): arXiv category codes
            - limit (int): Papers per category (1–20)

    Returns:
        str: JSON with categories, total_papers, by_category dict.
             Each paper: id, title, abstract (400 chars), authors, published, url, pdf.
    """
    cache_key = f"arxiv_latest|{'_'.join(sorted(params.categories))}|{params.limit}"
    if cached := _cache_get(cache_key, "arxiv"):
        return cached
    try:
        results_raw = await asyncio.gather(
            *[_fetch_arxiv(f"cat:{c}", params.limit) for c in params.categories]
        )
        by_category = {cat: papers for cat, papers in zip(params.categories, results_raw)}
        result = json.dumps(
            {
                "fetched_at": _now_iso(),
                "categories": params.categories,
                "total_papers": sum(len(p) for p in by_category.values()),
                "by_category": by_category,
            },
            indent=2,
            ensure_ascii=False,
        )
        _cache_set(cache_key, result)
        return result
    except Exception as e:
        return _handle_error(e, "arXiv")


# ---------------------------------------------------------------------------
# Tool 4: arxiv_search
# ---------------------------------------------------------------------------


@server.tool(
    name="arxiv_search",
    annotations={
        "title": "arXiv Full-Text Search",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def arxiv_search(params: ArxivSearchInput) -> str:
    """Search arXiv for papers matching a query, sorted by submission date.

    Searches title, abstract and author fields. Optionally restrict to a
    specific AI/ML category.

    Args:
        params (ArxivSearchInput):
            - query (str): Search terms (e.g. 'LLM agents tool use')
            - category (Optional[str]): arXiv category filter
            - limit (int): Papers to return (1–20)

    Returns:
        str: JSON with query, category, count, papers[].
             Each paper: id, title, abstract, authors, published, url, pdf.
    """
    cache_key = f"arxiv_search|{params.query}|{params.category}|{params.limit}"
    if cached := _cache_get(cache_key, "arxiv"):
        return cached
    try:
        if params.category:
            search_query = f"all:{params.query} AND cat:{params.category}"
        else:
            search_query = f"all:{params.query}"
        papers = await _fetch_arxiv(search_query, params.limit)
        result = json.dumps(
            {
                "query": params.query,
                "category": params.category,
                "fetched_at": _now_iso(),
                "count": len(papers),
                "papers": papers,
            },
            indent=2,
            ensure_ascii=False,
        )
        _cache_set(cache_key, result)
        return result
    except Exception as e:
        return _handle_error(e, "arXiv")


# ---------------------------------------------------------------------------
# Tool 5: lobsters_hot
# ---------------------------------------------------------------------------


@server.tool(
    name="lobsters_hot",
    annotations={
        "title": "Lobste.rs Hottest Tech Stories",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def lobsters_hot(params: LobstersHotInput) -> str:
    """Fetch the hottest stories from Lobste.rs, a curated tech community.

    Lobste.rs is smaller and more technically focused than HackerNews.
    Invitation-only membership ensures higher signal-to-noise ratio.

    Args:
        params (LobstersHotInput):
            - limit (int): Stories to return (1–25)
            - tag_filter (Optional[str]): Tag substring filter (e.g. 'ai', 'ml')

    Returns:
        str: JSON with count, stories[]. Each story: title, url, score,
             comments, tags, submitter, submitted_at, lobsters_url.
    """
    cache_key = f"lobsters|{params.limit}|{params.tag_filter}"
    if cached := _cache_get(cache_key, "lobsters"):
        return cached
    try:
        data: list[dict] = await _get(f"{LOBSTERS_BASE_URL}/hottest.json")
        stories = []
        for item in data:
            if params.tag_filter:
                tags = item.get("tags", [])
                if not any(params.tag_filter.lower() in t.lower() for t in tags):
                    continue
            stories.append(
                {
                    "title": item.get("title", ""),
                    "url": item.get("url") or item.get("comments_url", ""),
                    "score": item.get("score", 0),
                    "comments": item.get("comment_count", 0),
                    "tags": item.get("tags", []),
                    "submitter": item.get("submitter_user", {}).get("username", ""),
                    "submitted_at": (item.get("created_at", "")[:16] or "").replace("T", " ")
                    + " UTC",
                    "lobsters_url": item.get("comments_url", ""),
                }
            )
            if len(stories) >= params.limit:
                break
        result = json.dumps(
            {
                "tag_filter": params.tag_filter,
                "fetched_at": _now_iso(),
                "count": len(stories),
                "stories": stories,
            },
            indent=2,
            ensure_ascii=False,
        )
        _cache_set(cache_key, result)
        return result
    except Exception as e:
        return _handle_error(e, "Lobste.rs")


# ---------------------------------------------------------------------------
# Tool 6: github_trending_ai
# ---------------------------------------------------------------------------


@server.tool(
    name="github_trending_ai",
    annotations={
        "title": "GitHub Trending AI/Tech Repos",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def github_trending_ai(params: GithubTrendingAiInput) -> str:
    """Search GitHub for trending repositories by topic.

    A surge of starred repos on a topic is a strong adoption signal.
    No auth required (60 req/h). Set GITHUB_TOKEN for 5,000 req/h.

    Args:
        params (GithubTrendingAiInput):
            - topic (str): GitHub topic tag (e.g. 'llm', 'mcp', 'ai-agents')
            - limit (int): Repos to return (1–15)
            - min_stars (int): Minimum stars filter
            - sort (str): 'stars' or 'updated'

    Returns:
        str: JSON with topic, total_found, count, repos[].
             Each repo: name, description, stars, forks, language, topics, updated_at, url.
    """
    cache_key = f"github|{params.topic}|{params.sort}|{params.min_stars}|{params.limit}"
    if cached := _cache_get(cache_key, "github"):
        return cached
    try:
        query = f"topic:{params.topic}"
        if params.min_stars > 0:
            query += f" stars:>={params.min_stars}"
        data = await _get(
            f"{GITHUB_BASE_URL}/search/repositories",
            {"q": query, "sort": params.sort, "order": "desc", "per_page": params.limit},
        )
        repos = [
            {
                "name": r["full_name"],
                "description": r.get("description", ""),
                "stars": r.get("stargazers_count", 0),
                "forks": r.get("forks_count", 0),
                "language": r.get("language", ""),
                "topics": r.get("topics", [])[:8],
                "updated_at": r.get("updated_at", "")[:10],
                "url": r.get("html_url", ""),
            }
            for r in data.get("items", [])
        ]
        result = json.dumps(
            {
                "topic": params.topic,
                "sort": params.sort,
                "fetched_at": _now_iso(),
                "total_found": data.get("total_count", 0),
                "count": len(repos),
                "repos": repos,
            },
            indent=2,
            ensure_ascii=False,
        )
        _cache_set(cache_key, result)
        return result
    except Exception as e:
        return _handle_error(e, "GitHub")


# ---------------------------------------------------------------------------
# Tool 7: tech_signal_digest
# ---------------------------------------------------------------------------


@server.tool(
    name="tech_signal_digest",
    annotations={
        "title": "Aggregated Tech & AI Signal Digest",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def tech_signal_digest(params: TechSignalDigestInput) -> str:
    """Aggregate tech & AI signals from all four sources in one call.

    The primary tool for a comprehensive daily or weekly tech intelligence
    briefing. Combines HackerNews, arXiv, Lobste.rs and GitHub into one
    structured JSON digest. Use 'focus' to filter for a specific topic.

    Args:
        params (TechSignalDigestInput):
            - focus (Optional[str]): Topic filter (e.g. 'MCP', 'agents')
            - hn_limit (int): HN stories (1–10)
            - arxiv_limit (int): arXiv papers (1–10)
            - lobsters_limit (int): Lobste.rs stories (1–10)
            - github_limit (int): GitHub repos (1–10)

    Returns:
        str: JSON digest with generated_at, focus, sources{hn, arxiv, lobsters, github}.
             Each source has label, count, and its items list.
    """
    focus_lower = params.focus.lower() if params.focus else None
    cache_key = (
        f"digest|{params.focus}|{params.hn_limit}|{params.arxiv_limit}"
        f"|{params.lobsters_limit}|{params.github_limit}"
    )
    if cached := _cache_get(cache_key, "digest"):
        return cached

    def _matches_focus(items: list[dict], *fields: str) -> list[dict]:
        if not focus_lower:
            return items
        return [
            item
            for item in items
            if focus_lower in " ".join(str(item.get(f, "")) for f in fields).lower()
        ]

    try:
        hn_raw, arxiv_raw, lob_raw, gh_raw = await asyncio.gather(
            _fetch_hn_stories("top", params.hn_limit * 4),
            _fetch_arxiv("cat:cs.AI OR cat:cs.LG OR cat:cs.CL", params.arxiv_limit * 2),
            _get(f"{LOBSTERS_BASE_URL}/hottest.json"),
            _get(
                f"{GITHUB_BASE_URL}/search/repositories",
                {
                    "q": "topic:llm OR topic:ai-agents OR topic:mcp stars:>=100",
                    "sort": "updated",
                    "order": "desc",
                    "per_page": params.github_limit * 2,
                },
            ),
        )

        hn_stories = _matches_focus([_format_hn_story(s) for s in hn_raw], "title")[
            : params.hn_limit
        ]

        arxiv_papers = _matches_focus(arxiv_raw, "title", "abstract")[: params.arxiv_limit]

        lob_stories = _matches_focus(
            [
                {
                    "title": s.get("title", ""),
                    "url": s.get("url") or s.get("comments_url", ""),
                    "score": s.get("score", 0),
                    "tags": s.get("tags", []),
                    "lobsters_url": s.get("comments_url", ""),
                }
                for s in lob_raw
            ],
            "title",
            "tags",
        )[: params.lobsters_limit]

        gh_repos = _matches_focus(
            [
                {
                    "name": r["full_name"],
                    "description": r.get("description", ""),
                    "stars": r.get("stargazers_count", 0),
                    "language": r.get("language", ""),
                    "topics": r.get("topics", [])[:5],
                    "url": r.get("html_url", ""),
                }
                for r in gh_raw.get("items", [])
            ],
            "name",
            "description",
        )[: params.github_limit]

        digest = {
            "generated_at": _now_iso(),
            "focus": params.focus or "broad tech & AI",
            "sources": {
                "hn": {"label": "HackerNews", "count": len(hn_stories), "stories": hn_stories},
                "arxiv": {
                    "label": "arXiv (cs.AI/cs.LG/cs.CL)",
                    "count": len(arxiv_papers),
                    "papers": arxiv_papers,
                },
                "lobsters": {
                    "label": "Lobste.rs",
                    "count": len(lob_stories),
                    "stories": lob_stories,
                },
                "github": {"label": "GitHub Trending", "count": len(gh_repos), "repos": gh_repos},
            },
        }

        result = json.dumps(digest, indent=2, ensure_ascii=False)
        _cache_set(cache_key, result)
        return result
    except Exception as e:
        return _handle_error(e, "digest")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def _resolve_http_bind() -> tuple[str, int]:
    """Resolve MCP_HOST/MCP_PORT and refuse public bind without bearer token.

    Default bind is 127.0.0.1. Non-loopback binds require MCP_BEARER_TOKEN
    to prevent accidental public exposure of the server.
    """
    host = os.environ.get("MCP_HOST", "127.0.0.1")
    port = int(os.environ.get("MCP_PORT", "8000"))
    loopback = {"127.0.0.1", "localhost", "::1"}
    if host not in loopback and not os.environ.get("MCP_BEARER_TOKEN"):
        raise RuntimeError(
            f"Refusing to bind streamable_http to non-loopback host '{host}' "
            "without MCP_BEARER_TOKEN. Set MCP_BEARER_TOKEN, or bind to "
            "127.0.0.1 and place an authenticating reverse proxy in front."
        )
    return host, port


def main() -> None:
    logging.basicConfig(
        level=os.environ.get("LOG_LEVEL", "INFO").upper(),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    transport = os.environ.get("MCP_TRANSPORT", "stdio")
    logger.info("Starting hn-tech-signal-mcp transport=%s", transport)
    if transport == "streamable_http":
        host, port = _resolve_http_bind()
        server.settings.host = host
        server.settings.port = port
        server.run(transport="streamable_http")
    else:
        server.run()


if __name__ == "__main__":
    main()
