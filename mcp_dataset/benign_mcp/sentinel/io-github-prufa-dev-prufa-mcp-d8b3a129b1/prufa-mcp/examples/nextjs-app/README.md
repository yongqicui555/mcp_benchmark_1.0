# Example: audit a Next.js app with prufa-mcp

This example shows a one-call audit of a deployed Next.js app. It assumes
you have `prufa-mcp` installed and `PRUFA_API_TOKEN` set.

## Run

```bash
pip install prufa-mcp
export PRUFA_API_TOKEN=...
python audit.py https://your-nextjs-app.com
```

## Expected output

```json
{
  "report_id": "rep_abc123",
  "url": "https://your-nextjs-app.com",
  "findings": [
    {"severity": "critical", "kind": "tracking", "detail": "GA4 event `purchase` not firing on /checkout/success"},
    {"severity": "warning", "kind": "consent", "detail": "Meta pixel fires before consent signal"},
    {"severity": "info", "kind": "console", "detail": "1 uncaught console error on initial load"}
  ]
}
```
