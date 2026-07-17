## Finding: SEC-004 — SSRF-Prevention: HTTPS-Enforcement + IP-Blocklisting

**Severity:** critical
**Status:** open
**Server:** lobbywatch-mcp
**Check-Reference:** SEC-004
**PDF-Reference:** Sec 4.x / Anhang B

### Observed Behavior

`API_BASE` is hardcoded https → host is not user-controlled. However user-supplied `id_or_name` is interpolated raw into the URL path:

```python
# client.py:216
search = await self.api_get(f"search/default/{id_or_name}", params={"limit": 5})
```

`httpx.AsyncClient(follow_redirects=True)` (client.py:61) blindly follows 30x. No IP-blocklist, no link-local / metadata-IP guard, no allow-list of expected paths.

### Expected Behavior

- URL-encode user-supplied path segments (`urllib.parse.quote`)
- Validate `id_or_name` length / character set before interpolation
- Disable redirects or restrict to same-origin
- Add an httpx event hook that rejects responses from RFC1918 / link-local / 169.254.0.0/16 if the host ever resolves there

### Evidence

- `src/lobbywatch_mcp/client.py:216` — raw f-string interpolation of `id_or_name`
- `src/lobbywatch_mcp/client.py:61` — `follow_redirects=True`
- `src/lobbywatch_mcp/client.py:212` — numeric path uses `int(id_or_name)` (good — already coerced)

### Risk Description

Mostly mitigated by hardcoded host. Worst case: malformed `id_or_name="../../../admin/dump"` reaches an unintended cms.lobbywatch.ch endpoint. Risk escalates if `API_BASE` is ever made configurable or upstream introduces a redirect chain to a third-party CDN.

### Remediation

```diff
-        search = await self.api_get(f"search/default/{id_or_name}", params={"limit": 5})
+        from urllib.parse import quote
+        search = await self.api_get(f"search/default/{quote(str(id_or_name), safe='')}", params={"limit": 5})
```

Plus: turn off `follow_redirects` for `api_get` or whitelist hosts on redirect.

### Effort Estimate

S (< 1d)
