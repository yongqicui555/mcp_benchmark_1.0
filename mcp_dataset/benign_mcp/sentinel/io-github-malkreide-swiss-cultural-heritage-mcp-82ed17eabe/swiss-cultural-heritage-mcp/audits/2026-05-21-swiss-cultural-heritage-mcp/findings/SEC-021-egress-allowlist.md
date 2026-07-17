# Finding — SEC-021 / Egress allow-list

**Check:** SEC-021 — Egress allow-list (code + network)
**Status:** FAIL
**Severity:** high
**File:** `src/swiss_cultural_heritage_mcp/server.py:30-34, 54-57`

## Evidence

Endpoint constants are hardcoded (`SIK_ISEA_API`, `CKAN_API`, `NB_OAI_PMH`), which is good. However:

- `_http_get(url, ...)` accepts an arbitrary URL — there is no `ALLOWED_HOSTS = frozenset(...)` and no pre-flight host validation.
- `follow_redirects=True` (line 56) lets the three upstreams transparently redirect the client to any host. A compromise or misconfiguration at `nb.admin.ch` or `opendata.swiss` could redirect to an attacker-controlled host and the server would happily fetch it.
- No infrastructure-layer egress policy is documented (Render deployment instructions in README do not mention egress restrictions).

## Impact

- Defense-in-depth gap. Per SEC-021: "Neither layer alone suffices." Currently neither layer is present.
- Path-based data exfiltration vector via redirect chains is open.
- A future refactor that derives part of the URL from a tool parameter (e.g., an OAI `identifier`) would silently become an SSRF.

## Remediation

```python
from typing import Final
ALLOWED_HOSTS: Final[frozenset[str]] = frozenset({
    "api.sik-isea.ch",
    "opendata.swiss",
    "www.nb.admin.ch",
})

def _assert_allowed(url: str) -> None:
    host = httpx.URL(url).host
    if host not in ALLOWED_HOSTS:
        raise ValueError(f"Host not in allow-list: {host}")
```

1. Call `_assert_allowed(url)` at the top of `_http_get`.
2. Set `follow_redirects=False`; if a redirect is observed, re-validate the target host explicitly.
3. Add `docs/network-egress.md` listing the three hosts and the update procedure.
4. For HTTP-mode deployments (Render), document the recommended platform egress rule.

**Effort:** S (≤ 1 day)
