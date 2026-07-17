# Finding — SEC / Unsafe XML parser

**Check:** SEC (defense-in-depth, cross-references SEC-018/023)
**Status:** FAIL
**Severity:** high
**File:** `src/swiss_cultural_heritage_mcp/server.py:19, 94, 130, 782`

## Evidence

```python
import xml.etree.ElementTree as ET
...
root = ET.fromstring(xml_text)
```

`xml.etree.ElementTree` from the Python standard library is documented as vulnerable to several XML attack classes (billion-laughs / entity expansion). Python's docs explicitly recommend `defusedxml` for any XML coming from outside the application's trust boundary.

The OAI-PMH responses come from `www.nb.admin.ch` (currently trusted) but:
- No integrity/authenticity is enforced beyond TLS
- A future deployment, an upstream compromise, or a man-in-the-middle on a misconfigured network could deliver a malicious payload
- This is exactly the defense-in-depth scenario the audit framework's SOLID-principle catalog highlights

## Impact

- Potential DoS via entity expansion on a single malformed OAI response
- Inconsistent with the rest of the security posture (Pydantic `extra="forbid"`, input length caps) which is otherwise solid

## Remediation

1. Add `defusedxml` to dependencies in `pyproject.toml`.
2. Replace the import:
   ```python
   from defusedxml import ElementTree as ET
   ```
3. No call-site changes needed; the API is drop-in compatible for `fromstring` and `find/findall`.

**Effort:** XS (< 1 hour)
