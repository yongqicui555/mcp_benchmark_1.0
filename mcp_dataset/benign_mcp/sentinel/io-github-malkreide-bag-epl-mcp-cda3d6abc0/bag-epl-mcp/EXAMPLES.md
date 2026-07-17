# Use Cases & Examples — bag-epl-mcp

Real-world queries by audience. Indicate per example whether an API key is required.

## 🏫 Bildung & Schule
Lehrpersonen, Schulbehörden, Fachreferent:innen

### Abklärung von Hilfsmitteln für den Schulalltag
«Zahlt die Krankenkasse das Hörgerät für einen Schüler oder müssen das die Eltern übernehmen?»

→ epl_migel_suche(suchbegriff="Hoergeraet")
→ epl_rechtskontext(frage="Zahlt die Grundversicherung Hörgeräte für Kinder?")
Warum nützlich: Hilft Lehrpersonen und Heilpädagog:innen schnell zu klären, welche Unterstützungsmöglichkeiten für Inklusionsmaterialien über die Grundversicherung bestehen. (Kein API-Key erforderlich)

### Medikamentengabe bei chronischen Erkrankungen im Schullager
«Wird Ritalin (Methylphenidat) von der Grundversicherung bezahlt und welche Regeln gelten?»

→ epl_sl_suche(suchbegriff="Methylphenidat")
→ epl_rechtskontext(frage="WZW Kriterien für ADHS Medikamente")
Warum nützlich: Unterstützt Schulleitungen und Lagerleitende dabei, den gesetzlichen und finanziellen Rahmen von häufigen Dauermedikationen bei Schulkindern zu verstehen. (Kein API-Key erforderlich)

## 👨👩👧 Eltern & Schulgemeinde
Elternräte, interessierte Erziehungsberechtigte

### Übernahme bei Geburtsgebrechen
«Mein Kind hat Zystische Fibrose (Geburtsgebrechen 404). Werden die speziellen Medikamente von der IV bezahlt?»

→ epl_ggsl_abfrage(geburtsgebrechen_nr="404")
→ epl_rechtskontext(frage="Medikamente bei Geburtsgebrechen IVG")
Warum nützlich: Gibt betroffenen Eltern konkrete Anhaltspunkte, ob wichtige, dauerhafte Medikationen von der IV über die GGSL übernommen werden. (Kein API-Key erforderlich)

### Kosten für Hilfsmittel
«Wird eine Gehhilfe oder ein Rollstuhl für mein Kind von der Krankenkasse übernommen?»

→ epl_migel_suche(suchbegriff="Rollstuhl")
Warum nützlich: Erleichtert Eltern den Zugang zu Informationen, welche medizinischen Hilfsmittel in der MiGeL gelistet und somit kassenpflichtig sind. (Kein API-Key erforderlich)

## 🗳️ Bevölkerung & öffentliches Interesse
Allgemeine Öffentlichkeit, politisch und gesellschaftlich Interessierte

### Transparenz bei neuen Medikamenten
«Welche neuen Medikamente sind aktuell zur Aufnahme in die Spezialitätenliste beantragt?»

→ epl_gesuchseingaenge()
Warum nützlich: Bietet der Öffentlichkeit und Medienschaffenden Transparenz darüber, welche neuen Therapien auf Zulassung zur Kassenpflicht warten. (Kein API-Key erforderlich)

### Verständnis der Kassenpflicht (WZW)
«Nach welchen Kriterien entscheidet das BAG eigentlich, ob ein neues Medikament von allen Prämienzahlern bezahlt wird?»

→ epl_rechtskontext(frage="Nach welchen Kriterien wird über die Aufnahme in die Spezialitätenliste entschieden?")
Warum nützlich: Fördert das demokratische Verständnis für gesundheitspolitische Entscheide und die Beurteilung nach Wirksamkeit, Zweckmässigkeit und Wirtschaftlichkeit. (Kein API-Key erforderlich)

## 🤖 KI-Interessierte & Entwickler:innen
MCP-Enthusiast:innen, Forscher:innen, Prompt Engineers, öffentliche Verwaltung

### Integration von Bundesrecht und Gesundheitsdaten
«Zeige mir die Medikamente in der Spezialitätenliste für Diabetes und gib mir direkt den genauen Fedlex-Link zum Krankenversicherungsgesetz (KVG) betreffend Leistungen.»

→ epl_sl_suche(suchbegriff="Insulin")
→ fedlex_suche(suchbegriff="Krankenversicherungsgesetz KVG Leistungen") (via https://github.com/malkreide/fedlex-mcp)
Warum nützlich: Demonstriert eindrücklich, wie fachspezifische Gesundheitsdaten automatisiert mit der primären Rechtsquelle (Fedlex) aus dem Swiss Public Data Portfolio verknüpft werden können. (Kein API-Key erforderlich)

### Automatisierter Kassenpflicht-Check
«Erstelle mir eine Übersicht der rechtlichen Grundlagen zur MiGeL und suche nach Inkontinenzhilfen.»

→ epl_rechtskontext(frage="Rechtliche Grundlagen MiGeL")
→ epl_migel_suche(suchbegriff="Inkontinenz")
Warum nützlich: Erlaubt Entwickler:innen den Bau von automatisierten Systemen für Patientenanfragen, um Kassenpflicht und Gesetze direkt abzugleichen. (Kein API-Key erforderlich)

---

## 🔧 Technische Referenz: Tool-Auswahl nach Anwendungsfall

| Ich möchte… | Tool(s) | Auth nötig? |
|---|---|---|
| prüfen, ob ein Medikament kassenpflichtig ist | `epl_sl_suche` | Nein |
| schauen, ob die IV Medikamente für ein Geburtsgebrechen zahlt | `epl_ggsl_abfrage` | Nein |
| die Kassenpflicht für Hilfsmittel (z.B. Rollstuhl) klären | `epl_migel_suche` | Nein |
| wissen, welche Medikamente auf die SL-Zulassung warten | `epl_gesuchseingaenge` | Nein |
| die rechtlichen Kriterien (z.B. WZW, KVG) verstehen | `epl_rechtskontext` | Nein |
| den Server-Status und geplante ePL-Phasen abfragen | `epl_server_info` | Nein |
