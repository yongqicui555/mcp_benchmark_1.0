# Example: audit a Stripe-checkout page with prufa-mcp

This example shows a one-call audit of a deployed Stripe-checkout page.
The audit focuses on payment-flow verification: the success URL, the
cancel URL, the webhook reachability, and the consent signals on the
checkout page.

## Run

```bash
pip install prufa-mcp
export PRUFA_API_TOKEN=...
python audit.py https://your-site.com/checkout
```

## Expected output

```json
{
  "report_id": "rep_ghi789",
  "url": "https://your-site.com/checkout",
  "findings": [
    {"severity": "critical", "kind": "flow", "detail": "Stripe success URL returns 404 — purchase events will not be tracked"},
    {"severity": "warning", "kind": "consent", "detail": "Meta pixel fires before consent on the checkout page"},
    {"severity": "info", "kind": "flow", "detail": "Stripe webhook endpoint /api/stripe/webhook is not publicly reachable"}
  ]
}
```
