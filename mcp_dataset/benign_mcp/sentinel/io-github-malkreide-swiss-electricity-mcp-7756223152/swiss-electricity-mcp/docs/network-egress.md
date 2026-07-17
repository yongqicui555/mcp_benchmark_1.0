# Network egress allow-list

`swiss-electricity-mcp` only ever talks to a fixed set of official Swiss
open-data endpoints. Outbound access is restricted at two layers.

## Code layer (enforced in this repo)

`assert_url_allowed()` in `src/swiss_electricity_mcp/api_client.py` gates **every**
outbound request. It requires HTTPS and rejects any host outside the
`ALLOWED_HOSTS` frozenset:

| Host | Purpose |
|---|---|
| `www.energiedashboard.admin.ch` | BFE Energie-Dashboard (production/consumption/prices) |
| `lindas.admin.ch` | ElCom tariff cubes via SPARQL |
| `opendata.swiss` | CKAN dataset discovery (BFE datasets) |
| `data.stadt-zuerich.ch` | Stadt Zürich OGD dataset discovery |

The list is a `frozenset` constant — it cannot be mutated at runtime or via
configuration. Non-HTTPS schemes (`http://`, `file://`, `gopher://`, …) and
cloud-metadata IPs (`169.254.169.254`) are rejected by construction.

## Network layer (deployment responsibility)

As defense-in-depth, restrict egress at the infrastructure layer so a code bug
cannot reach anything else:

- **Kubernetes:** a `NetworkPolicy` allowing egress only to TCP/443 and the DNS
  resolver.
- **Render / Railway / Fly.io:** platform egress rules where available.
- **Docker / self-hosted:** firewall rules or an egress proxy (e.g. Stripe
  Smokescreen) allowing only the four hosts above.

## Updating the allow-list

Adding an upstream is a deliberate, reviewed change:

1. Add the host to `ALLOWED_HOSTS` in `api_client.py`.
2. Add a row to the table above with its purpose.
3. Update the network-layer rules in the deployment config.
4. Note the change in `CHANGELOG.md`.
