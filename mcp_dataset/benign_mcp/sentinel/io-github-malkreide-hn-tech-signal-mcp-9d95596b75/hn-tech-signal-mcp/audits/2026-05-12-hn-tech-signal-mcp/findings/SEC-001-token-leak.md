# Finding: SEC-001 — GITHUB_TOKEN wird an Drittanbieter geleakt

| Feld | Wert |
|---|---|
| **Severity** | **critical** |
| **Status** | closed (re-audit 2026-05-12) |
| **Server** | `hn-tech-signal-mcp` |
| **Check-Reference** | `SEC-001` (Secret Handling / Outbound Auth Scoping) |
| **Audit-Datum** | 2026-05-12 |
| **Auditor** | Claude (mcp-audit-skill) |

### Observed Behavior

`_build_headers()` in `src/hn_tech_signal_mcp/server.py:92-97` hängt den
`Authorization: Bearer <GITHUB_TOKEN>`-Header bedingungslos an, sobald die
Env-Var gesetzt ist. Dieser Header wird durch `_get` (Zeile 100-104) und
`_get_text` (Zeile 107-111) auf **alle** ausgehenden Requests gesetzt —
nicht nur auf `api.github.com`, sondern auch auf:

- `https://hacker-news.firebaseio.com/v0/...`
- `https://hn.algolia.com/api/v1/search`
- `https://export.arxiv.org/api/query`
- `https://lobste.rs/hottest.json`

```python
# src/hn_tech_signal_mcp/server.py:92
def _build_headers() -> dict[str, str]:
    headers = {"Accept": "application/json", "User-Agent": "hn-tech-signal-mcp/0.1.0"}
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers
```

### Expected Behavior

Outbound Credentials werden ausschliesslich an den Host gesendet, für den sie
ausgestellt wurden. Pro Upstream-Aufrufer eigener Header-Builder, oder
hostbasierter Switch in `_get`/`_get_text`.

### Evidence

- `src/hn_tech_signal_mcp/server.py:92-97` — Header-Builder unkonditioniert
- `src/hn_tech_signal_mcp/server.py:102` — `_get` ruft `_build_headers()` ohne
  Host-Kontext
- `src/hn_tech_signal_mcp/server.py:109` — `_get_text` identisch
- Aufrufer: HN (`server.py:140, 145`), arXiv (`server.py:199, 667`),
  Lobsters (`server.py:531, 667`) — alle erhalten den Bearer-Token

### Risk Description

- GitHub Personal Access Tokens haben oft breite Scopes (`repo`, `read:org`,
  `gist`, …). Jeder Drittanbieter-Operator (HN-Firebase, Algolia, arXiv,
  Lobsters) sieht den Klartext-Token in seinen TLS-Terminator-Logs.
- Ein kompromittierter oder neugieriger Upstream kann den Token gegen die
  GitHub-API replayen.
- Token-Rotation wird wahrscheinlich nicht bemerkt — Benutzer sind sich nicht
  bewusst, dass HN/arXiv/Lobsters den Token überhaupt erhalten haben.
- Für den `mcp` einer Public-Data-Server-Familie ein erheblicher
  Vertrauensbruch — Nutzer erwarten, dass *No Auth Required* auch wirklich
  ohne Outbound-Auth-Headers funktioniert.

### Remediation

```diff
- def _build_headers() -> dict[str, str]:
-     headers = {"Accept": "application/json", "User-Agent": "hn-tech-signal-mcp/0.1.0"}
-     token = os.environ.get("GITHUB_TOKEN")
-     if token:
-         headers["Authorization"] = f"Bearer {token}"
-     return headers
+ _BASE_HEADERS = {
+     "Accept": "application/json",
+     "User-Agent": "hn-tech-signal-mcp/0.1.0",
+ }
+
+ def _headers_for(url: str) -> dict[str, str]:
+     headers = dict(_BASE_HEADERS)
+     if url.startswith(GITHUB_BASE_URL):
+         token = os.environ.get("GITHUB_TOKEN")
+         if token:
+             headers["Authorization"] = f"Bearer {token}"
+     return headers
```

Anpassung `_get`/`_get_text` auf `headers=_headers_for(url)`.

Zusätzlich Pytest-Regression:

```python
def test_github_token_only_sent_to_github(monkeypatch):
    monkeypatch.setenv("GITHUB_TOKEN", "ghp_secret")
    assert "Authorization" not in _headers_for("https://hacker-news.firebaseio.com/v0/topstories.json")
    assert "Authorization" not in _headers_for("https://export.arxiv.org/api/query")
    assert _headers_for("https://api.github.com/search/repositories")["Authorization"] == "Bearer ghp_secret"
```

### Effort Estimate

**S** — ~30 Minuten, einzelne Datei, +1 Regressionstest.

### Verification After Fix

- Pytest-Regression oben grün
- `grep -n _build_headers src/` liefert keine Treffer mehr
- Manueller Run mit `GITHUB_TOKEN=test` + `httpx`-Mock zeigt Header nur für `api.github.com`
