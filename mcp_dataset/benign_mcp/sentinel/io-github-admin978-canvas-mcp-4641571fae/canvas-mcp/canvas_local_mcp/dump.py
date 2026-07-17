#!/usr/bin/env python3
"""Bulk-download Canvas content: files, modules, assignments, pages, announcements."""
from __future__ import annotations
import json, os, re, sys
from pathlib import Path
import urllib.request, urllib.error

ENV_FILE = Path.home() / ".canvas.env"
BASE = ""
HEAD: dict[str, str] = {}
OUT = Path()
SAFE = re.compile(r"[^\w\-. áéíóúñÁÉÍÓÚÑ()]+")

def _load_env() -> None:
    global BASE, HEAD, OUT
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
    OUT = Path(os.environ.get("CANVAS_DUMP_DIR", "canvas-dump")).resolve()
    OUT.mkdir(parents=True, exist_ok=True)

def slug(s: str, n: int = 120) -> str:
    return SAFE.sub("_", (s or "untitled")).strip("._ ")[:n] or "untitled"

def req(url: str):
    r = urllib.request.Request(url, headers=HEAD)
    return urllib.request.urlopen(r, timeout=60)

def paged(url: str):
    if "?" not in url:
        url += "?per_page=100"
    elif "per_page" not in url:
        url += "&per_page=100"
    while url:
        with req(url) as resp:
            data = json.loads(resp.read())
            yield from data if isinstance(data, list) else [data]
            link = resp.headers.get("Link", "")
            nxt = None
            for part in link.split(","):
                if 'rel="next"' in part:
                    nxt = part[part.find("<")+1:part.find(">")]
            url = nxt

def download(url: str, dest: Path):
    if dest.exists() and dest.stat().st_size > 0:
        return "skip"
    dest.parent.mkdir(parents=True, exist_ok=True)
    try:
        with req(url) as resp, open(dest, "wb") as f:
            while chunk := resp.read(65536):
                f.write(chunk)
        return "ok"
    except urllib.error.HTTPError as e:
        return f"err {e.code}"

def dump_course(c: dict):
    cid = c["id"]
    name = slug(c.get("name") or c.get("course_code") or str(cid))
    root = OUT / f"{cid}_{name}"
    print(f"\n=== {cid} {name} ===")

    # modules with items (primary content source — /files index is often 403)
    mods = []
    try:
        mods = list(paged(f"{BASE}/api/v1/courses/{cid}/modules?include[]=items&include[]=content_details"))
        root.mkdir(parents=True, exist_ok=True)
        (root / "_modules.json").write_text(json.dumps(mods, ensure_ascii=False, indent=2))
    except Exception as e:
        print(f"  modules: {e}")

    # files via module items
    for m in mods:
        mname = slug(m.get("name", "mod"))
        for it in m.get("items", []):
            t = it.get("type")
            title = slug(it.get("title", str(it.get("id"))))
            if t == "File" and it.get("url"):
                try:
                    with req(it["url"]) as r:
                        meta = json.loads(r.read())
                    durl = meta.get("url")
                    fname = slug(meta.get("display_name") or meta.get("filename") or title)
                    if durl:
                        dest = root / "files" / mname / fname
                        print(f"  file [{mname}] {fname} -> {download(durl, dest)}")
                except Exception as e:
                    print(f"  file {title}: {e}")
            elif t == "Page" and it.get("url"):
                try:
                    with req(it["url"]) as r:
                        p = json.loads(r.read())
                    body = p.get("body") or ""
                    dest = root / "pages" / mname / f"{title}.html"
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    dest.write_text(body)
                    print(f"  page [{mname}] {title} -> ok")
                except Exception as e:
                    print(f"  page {title}: {e}")

    # assignments
    try:
        asg = list(paged(f"{BASE}/api/v1/courses/{cid}/assignments"))
        (root / "_assignments.json").write_text(json.dumps(asg, ensure_ascii=False, indent=2))
        for a in asg:
            html = a.get("description") or ""
            if html:
                (root / "assignments" / f"{slug(a['name'])}.html").parent.mkdir(parents=True, exist_ok=True)
                (root / "assignments" / f"{slug(a['name'])}.html").write_text(html)
    except Exception as e:
        print(f"  assignments: {e}")

    # pages
    try:
        for p in paged(f"{BASE}/api/v1/courses/{cid}/pages"):
            url_slug = p.get("url")
            if not url_slug:
                continue
            with req(f"{BASE}/api/v1/courses/{cid}/pages/{url_slug}") as r:
                full = json.loads(r.read())
            body = full.get("body") or ""
            (root / "pages" / f"{slug(full.get('title', url_slug))}.html").parent.mkdir(parents=True, exist_ok=True)
            (root / "pages" / f"{slug(full.get('title', url_slug))}.html").write_text(body)
    except Exception as e:
        print(f"  pages: {e}")

    # announcements
    try:
        ann = list(paged(f"{BASE}/api/v1/courses/{cid}/discussion_topics?only_announcements=true"))
        (root / "_announcements.json").write_text(json.dumps(ann, ensure_ascii=False, indent=2))
    except Exception as e:
        print(f"  announcements: {e}")

def main():
    _load_env()
    only = set(sys.argv[1:])
    courses = list(paged(f"{BASE}/api/v1/courses?enrollment_state=active"))
    for c in courses:
        if only and str(c["id"]) not in only:
            continue
        dump_course(c)

if __name__ == "__main__":
    main()
