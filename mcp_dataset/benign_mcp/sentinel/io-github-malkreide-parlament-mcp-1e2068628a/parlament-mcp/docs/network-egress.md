# Network Egress Policy (SEC-021)

Der Server darf ausschliesslich seine eine Datenquelle kontaktieren. Das wird in
zwei Layern durchgesetzt.

## Erlaubte Hosts

| Host | Zweck | Code-Layer | Network-Layer |
|---|---|---|---|
| `ws.parlament.ch` | Curia Vista OData API | `ALLOWED_HOSTS` (frozenset) | NetworkPolicy egress (443) |

## Code-Layer

`src/parlament_mcp/security.py`:

```python
ALLOWED_HOSTS = frozenset({"ws.parlament.ch"})
assert_host_allowed(url)  # vor jedem ausgehenden Request
```

Die Allow-List ist ein `frozenset` — nicht zur Laufzeit über ENV/Config
mutierbar (bewusst, damit ein Operator-Fehler oder eine Kompromittierung den
Schutz nicht still aushebelt).

## Network-Layer

`deploy/k8s/networkpolicy.yaml`: Egress nur auf TCP/443 ins öffentliche Internet
(interne Ranges ausgenommen) + DNS. Ein kompromittiertes Image kann damit selbst
bei umgangenem Code-Check keine internen Dienste oder Cloud-Metadata-Endpunkte
erreichen.

## Update-Verfahren

Eine neue Allow-List-Domain erfordert:

1. Änderung in `src/parlament_mcp/security.py` (`ALLOWED_HOSTS`)
2. Änderung in `deploy/k8s/networkpolicy.yaml` (falls IP-spezifisch)
3. PR-Review mit Begründung
4. CHANGELOG-Eintrag
