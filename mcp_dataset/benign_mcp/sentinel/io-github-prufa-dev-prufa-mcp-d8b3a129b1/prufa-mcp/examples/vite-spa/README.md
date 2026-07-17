# Example: audit a Vite SPA with prufa-mcp

This example shows a one-call audit of a deployed Vite SPA. It assumes
you have `prufa-mcp` installed and `PRUFA_API_TOKEN` set.

Vite SPAs are interesting because they load via client-side routing —
the audit walks the routes the same way an agent would.

## Run

```bash
pip install prufa-mcp
export PRUFA_API_TOKEN=...
python audit.py https://your-vite-app.com
```

## Expected output

```json
{
  "report_id": "rep_def456",
  "url": "https://your-vite-app.com",
  "findings": [
    {"severity": "critical", "kind": "tracking", "detail": "GTM dataLayer `page_view` not pushed on client-side route change"},
    {"severity": "warning", "kind": "console", "detail": "Uncaught TypeError on /settings route load"},
    {"severity": "info", "kind": "seo", "detail": "Missing <link rel=\"canonical\"> on /about"}
  ]
}
```
