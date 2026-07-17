# Secret Management

**Datenklasse: Public Open Data.** Dieser Server benötigt **keine** Secrets.

## Status (Audit SEC-013)

- Die BISTA-API (`www.bista.zh.ch`) ist vollständig öffentlich — **kein**
  API-Key, Token oder Connection-String.
- Es gibt keine Secrets im Code, in ENV-Vars oder im Container-Image.
- `.gitignore` enthält `.env` / `.env.*` (Schutz für den Fall, dass künftig
  doch lokale Config-Secrets dazukommen).

Damit ist „Stufe 1" (keine / einfache ENV-Konfiguration) gemäss SEC-013 für die
Datenklasse *Public Open Data* ausreichend und dokumentiert.

## Falls künftig Secrets nötig werden

Sollte eine zukünftige Datenquelle Authentifizierung verlangen:

1. Secret **nie** im Code oder Image-Layer — nur via Secret Manager / Plattform-Secrets.
2. In-Memory als `pydantic.SecretStr`, nicht als `str`.
3. Region Schweiz/EU (DSG), Rotation ohne Code-Änderung.
4. CI-Secret-Scan (Gitleaks/Trufflehog) aktivieren.
