# Accepted Risks

Findings aus dem MCP-Audit, die für diesen Server bewusst **nicht** im Code
behoben werden, weil sie auf eine andere Architektur-Ebene gehören. Sie sind
hier dokumentiert statt stillschweigend ignoriert (Audit-Anti-Pattern #4).

## SEC-014 — Tool-Allow-Listing via MCP-Gateway

**Status:** accepted-risk (Portfolio-/Gateway-Ebene)

Tool-Allow-Listing pro Team/Rolle (default-deny) ist ein **Gateway**-Pattern.
`zh-education-mcp` ist ein eigenständiger, read-only Single-Purpose-Server mit
8 öffentlichen Tools ohne Auth — es gibt keine Rollen-/Team-Differenzierung auf
Server-Ebene. Lateral Movement zwischen Teams ist nicht möglich, da alle Tools
dieselben öffentlichen Daten lesen.

**Wenn der Server in eine Enterprise-/Stadt-Zürich-Umgebung mit Gateway
eingebunden wird**, ist das Allow-Listing dort zu konfigurieren (nicht im
Server). Server-seitige Defense-in-Depth ist mangels Auth nicht anwendbar.

## SEC-015 — Pre-Flight Tool-Poisoning Detection

**Status:** accepted-risk (Gateway-Ebene)

Tool-Poisoning-Detection (System-Prompt-/Override-/Homoglyph-Erkennung in
Tool-Definitionen) schützt einen **MCP-Client/Gateway** vor bösartigen Servern.
Für einen vertrauenswürdigen First-Party-Server mit statischen, im Repo
versionierten Tool-Definitionen ist der Detection-Layer am Gateway zu
implementieren, nicht im Server selbst.

Die Tool-Definitionen sind im Code versioniert; Änderungen durchlaufen Review +
CHANGELOG (siehe SEC-022). Ein „Rug Pull" wäre damit im Git-Verlauf sichtbar.

## SEC-005 — DNS-Pinning (Teil-Restrisiko)

**Status:** accepted-risk (gering), Folge-Härtung möglich

Vollständiges DNS-IP-Pinning gegen TOCTOU ist nicht implementiert. Das
Restrisiko ist gering, weil die Egress-Allow-List nur **einen** vertrauens-
würdigen Host (`www.bista.zh.ch`) zulässt (siehe `network-egress.md`).
