# Network Egress Allow-List

This server uses a defense-in-depth approach to outbound traffic: a code-level allow-list backed by an optional network-level policy. See audit finding [`SEC-021`](../audits/2026-05-21-swiss-cultural-heritage-mcp/findings/SEC-021-egress-allowlist.md).

## Allowed hosts

The list is declared as an immutable `frozenset` in `src/swiss_cultural_heritage_mcp/server.py`:

```python
ALLOWED_HOSTS: Final[frozenset[str]] = frozenset({
    "ckan.opendata.swiss",     # CKAN API — SIKART artist data + Nationalmuseum datasets
    "helveticat.nb.admin.ch",  # OAI-PMH provider — Nationalbibliothek (Helveticat)
})
```

Every HTTP request passes through `_assert_allowed(url)` in `_http_get`. Any other host raises `ValueError` *before* the request leaves the process. The shared `httpx.AsyncClient` keeps `follow_redirects=False`; redirects are followed manually in `_http_get` and **every hop is re-checked** against the allow-list, so an upstream cannot redirect us off-list.

## How to update the allow-list

Adding or removing a host is a security-relevant change. The procedure:

1. Open a PR that edits `ALLOWED_HOSTS` and this document in the same commit.
2. Justify the new host in the PR description (which upstream, why now, what data is fetched).
3. Add at least one unit test that hits the new host through `_http_get` (using `respx` mocks).
4. Reviewers verify the host's published privacy / terms-of-use; document any restrictions.

A change here is also an implicit change to the network-layer policy below — keep both in sync.

## Network-layer policy (operators)

The code allow-list is the inner layer; the platform should enforce the outer layer.

### Kubernetes

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: swiss-cultural-heritage-mcp-egress
spec:
  podSelector:
    matchLabels:
      app: swiss-cultural-heritage-mcp
  policyTypes: ["Egress"]
  egress:
    # DNS
    - to:
        - namespaceSelector: {}
          podSelector:
            matchLabels:
              k8s-app: kube-dns
      ports:
        - protocol: UDP
          port: 53
    # HTTPS to allow-listed upstreams (resolve in your platform)
    - to:
        - ipBlock:
            cidr: 0.0.0.0/0
      ports:
        - protocol: TCP
          port: 443
```

For stricter control, pair with an egress proxy (e.g. Cloudflare WARP, AWS NAT + Security Group, GCP Cloud NAT + Firewall) and limit destinations to the two FQDNs.

### Cloudflare Zero Trust

Create a Gateway HTTP policy allowing only `ckan.opendata.swiss`, `helveticat.nb.admin.ch` and blocking the catch-all for the workload identity.

### Render / Railway / Fly.io

These platforms do not currently expose fine-grained egress controls. The code-level allow-list remains the operative control. Document the residual risk if your deployment policy requires it.
