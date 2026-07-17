#!/usr/bin/env python3
"""Local Canvas MCP server. Reads token from ~/.canvas.env. Stdio transport."""
from __future__ import annotations
import os
from pathlib import Path
from typing import Any
import httpx
from mcp.server.fastmcp import FastMCP

ENV_FILE = Path.home() / ".canvas.env"
BASE = ""
HEAD: dict[str, str] = {}

mcp = FastMCP("canvas-local")

def _load_env() -> None:
    global BASE, HEAD
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text().splitlines():
            if "=" in line and not line.startswith("#"):
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())
    try:
        BASE = os.environ["CANVAS_BASE_URL"].rstrip("/")
        token = os.environ["CANVAS_TOKEN"]
    except KeyError as e:
        raise SystemExit(f"canvas-mcp: missing {e.args[0]}. Create ~/.canvas.env from .canvas.env.example (see README).")
    HEAD = {"Authorization": f"Bearer {token}"}

def _get(path: str, **params) -> Any:
    params.setdefault("per_page", 100)
    url = f"{BASE}{path}"
    out = []
    with httpx.Client(headers=HEAD, timeout=30) as c:
        while url:
            r = c.get(url, params=params)
            r.raise_for_status()
            data = r.json()
            if isinstance(data, list):
                out.extend(data)
            else:
                return data
            url = None
            params = {}
            link = r.headers.get("Link", "")
            for part in link.split(","):
                if 'rel="next"' in part:
                    url = part[part.find("<")+1:part.find(">")]
    return out

@mcp.tool()
def list_courses(active_only: bool = True) -> list[dict]:
    """List enrolled courses. Returns id, name, course_code, term."""
    p = "/api/v1/courses"
    params = {"enrollment_state": "active"} if active_only else {}
    cs = _get(p, **params)
    return [{"id": c["id"], "name": c.get("name"), "course_code": c.get("course_code")} for c in cs]

@mcp.tool()
def list_assignments(course_id: int, include_submissions: bool = False) -> list[dict]:
    """List assignments in a course. Includes due_at, points, submission status."""
    params = {}
    if include_submissions:
        params["include[]"] = "submission"
    asg = _get(f"/api/v1/courses/{course_id}/assignments", **params)
    out = []
    for a in asg:
        item = {
            "id": a["id"],
            "name": a.get("name"),
            "due_at": a.get("due_at"),
            "points_possible": a.get("points_possible"),
            "html_url": a.get("html_url"),
            "submission_types": a.get("submission_types"),
        }
        if include_submissions and a.get("submission"):
            s = a["submission"]
            item["submission"] = {"score": s.get("score"), "submitted_at": s.get("submitted_at"), "workflow_state": s.get("workflow_state")}
        out.append(item)
    return out

@mcp.tool()
def upcoming_events() -> list[dict]:
    """Upcoming planner items (assignments, calendar events) across all courses. Canvas returns roughly the next two weeks."""
    return _get("/api/v1/users/self/upcoming_events")

@mcp.tool()
def planner_items(start_date: str | None = None, end_date: str | None = None) -> list[dict]:
    """Planner items for the user. ISO dates (YYYY-MM-DD)."""
    p = {}
    if start_date: p["start_date"] = start_date
    if end_date: p["end_date"] = end_date
    return _get("/api/v1/planner/items", **p)

@mcp.tool()
def list_announcements(course_id: int) -> list[dict]:
    """Course announcements."""
    return _get(f"/api/v1/courses/{course_id}/discussion_topics", only_announcements=True)

@mcp.tool()
def list_modules(course_id: int, with_items: bool = True) -> list[dict]:
    """Course modules with items."""
    params = {}
    if with_items:
        params["include[]"] = "items"
    return _get(f"/api/v1/courses/{course_id}/modules", **params)

@mcp.tool()
def get_file_info(course_id: int, file_id: int) -> dict:
    """Get file metadata including download url."""
    return _get(f"/api/v1/courses/{course_id}/files/{file_id}")

@mcp.tool()
def get_grades(course_id: int | None = None) -> list[dict]:
    """Current grades. Per-course if course_id provided, otherwise all enrollments."""
    if course_id:
        en = _get(f"/api/v1/courses/{course_id}/enrollments", user_id="self")
    else:
        en = _get("/api/v1/users/self/enrollments", **{"state[]": "active"})
    return [{"course_id": e.get("course_id"), "grade": e.get("grades"), "type": e.get("type")} for e in en]

@mcp.tool()
def get_page(course_id: int, page_url: str) -> dict:
    """Fetch a course wiki page by its url slug."""
    return _get(f"/api/v1/courses/{course_id}/pages/{page_url}")

@mcp.tool()
def todo() -> list[dict]:
    """User's TODO list (ungraded assignments to look at)."""
    return _get("/api/v1/users/self/todo")

def main() -> None:
    _load_env()
    mcp.run()

if __name__ == "__main__":
    main()
