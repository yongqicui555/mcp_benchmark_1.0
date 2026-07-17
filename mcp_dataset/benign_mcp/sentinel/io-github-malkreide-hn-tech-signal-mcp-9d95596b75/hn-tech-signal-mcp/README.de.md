> 🇨🇭 **Teil des [Swiss Public Data MCP Portfolios](https://github.com/malkreide)**

# 📡 hn-tech-signal-mcp

![Version](https://img.shields.io/badge/version-0.1.0-blue)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![MCP](https://img.shields.io/badge/MCP-Model%20Context%20Protocol-purple)](https://modelcontextprotocol.io/)
[![Kein API-Key erforderlich](https://img.shields.io/badge/auth-kein%20API--Key-brightgreen)](https://github.com/malkreide/hn-tech-signal-mcp)
![CI](https://github.com/malkreide/hn-tech-signal-mcp/actions/workflows/ci.yml/badge.svg)

> MCP-Server für globale Tech- und KI-Signalanalyse — aggregiert HackerNews, arXiv, Lobste.rs und GitHub zu einem strukturierten Briefing. Kein API-Key erforderlich.

[🇬🇧 English Version](README.md)

### Demo

![Demo: Claude nutzt tech_signal_digest über arXiv, HackerNews und GitHub](docs/assets/demo.svg)

---

## Übersicht

**hn-tech-signal-mcp** verwandelt jeden KI-Assistenten in einen proaktiven Tech-Intelligence-Analysten. Der Server aggregiert vier Signalschichten — Forschungsfront, Entwickler-Diskurs, kuratiertes Signal und Open-Source-Praxis — zu einem einzigen, strukturierten Briefing.

**Kein API-Key erforderlich.** Alle vier Datenquellen sind öffentliche APIs. Optional: `GITHUB_TOKEN` setzen für höhere GitHub-Rate-Limits (5'000 statt 60 Anfragen/Stunde).

**Anchor-Demo-Query:**
*«Gib mir ein Tech-Signal-Digest zu KI heute — was passiert in Forschung, Entwickler-Diskurs und Open Source?»*

---

## Signalarchitektur

```
FRONTIER    arXiv API      → Neueste KI/ML-Paper (cs.AI, cs.LG, cs.CL, cs.CV)
DISCOURSE   HackerNews     → Top/Best-Stories + Algolia-Volltextsuche
            Lobste.rs      → Kuratiertes, rauscharmes Tech-Signal
PRACTICE    GitHub-Suche   → Was Entwicklerinnen und Entwickler gerade bauen
```

Die vier Schichten funktionieren wie ein Radar: arXiv zeigt, was am Horizont erscheint; HN und Lobste.rs zeigen, was die Community diskutiert; GitHub zeigt, was tatsächlich gebaut wird.

---

## Tools

| # | Tool | Quelle | Beschreibung |
|---|---|---|---|
| 1 | `hn_top_stories` | HackerNews | Top/Best/New-Stories, optional KI-Filter |
| 2 | `hn_search` | HN Algolia | Volltextsuche in der gesamten HN-Historie |
| 3 | `arxiv_latest` | arXiv | Neueste Paper nach Kategorie (cs.AI etc.) |
| 4 | `arxiv_search` | arXiv | Suche nach Stichwort/Titel/Autorin |
| 5 | `lobsters_hot` | Lobste.rs | Kuratierte Tech-Stories, nach Tag filterbar |
| 6 | `github_trending_ai` | GitHub | Trending KI-Repos nach Topic und Sterne |
| 7 | `tech_signal_digest` | Alle Quellen | Aggregiertes Markdown-Briefing |

---

## Installation

```bash
# Empfohlen: uvx (kein Installationsschritt nötig)
uvx hn-tech-signal-mcp

# Alternativ: pip
pip install hn-tech-signal-mcp
```

---

## Schnellstart

```bash
# Server starten (stdio-Modus für Claude Desktop)
uvx hn-tech-signal-mcp

# Mit optionalem GitHub-Token für höhere Rate-Limits
GITHUB_TOKEN=ghp_yourtoken uvx hn-tech-signal-mcp
```

Sofort in Claude Desktop ausprobieren:
> *«Gib mir ein Tech-Signal-Digest zu KI heute»*
> *«Was sind die neuesten cs.AI-Paper der letzten 48 Stunden?»*
> *«Was diskutiert HackerNews diese Woche über MCP?»*
> *«Zeig mir Trending-GitHub-Repos zum Thema ai-agents»*

---

## Konfiguration

### Umgebungsvariablen

| Variable | Standard | Beschreibung |
|---|---|---|
| `GITHUB_TOKEN` | – | Optional. GitHub Personal Access Token. Ohne Token: 60 Anfragen/h. Mit Token: 5'000/h. |
| `MCP_TRANSPORT` | `stdio` | Transport: `stdio` oder `streamable_http` |
| `MCP_PORT` | `8000` | Port für HTTP-Transport |

### Claude Desktop Konfiguration

```json
{
  "mcpServers": {
    "hn-tech-signal": {
      "command": "uvx",
      "args": ["hn-tech-signal-mcp"],
      "env": {
        "GITHUB_TOKEN": "ghp_yourtoken_optional"
      }
    }
  }
}
```

**Konfigurationsdatei-Speicherorte:**
- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`

---

## Anwendungsbeispiele

### KI-Fachgruppe / Stadtverwaltung

```
«Gib mir ein Tech-Signal-Digest zu KI heute»
→ tech_signal_digest(focus="AI")

«Was sind die Top-5-arXiv-Paper zu LLM-Agenten diese Woche?»
→ arxiv_search(query="LLM agents", category_filter="cs.AI", limit=5)

«Was diskutiert HackerNews über das Model Context Protocol?»
→ hn_search(query="model context protocol", days_back=30)
```

### Forschungsmonitoring

```
«Zeig mir die neuesten NLP-Paper von arXiv»
→ arxiv_latest(category="cs.CL", limit=10)

«Suche arXiv-Paper zu Retrieval-Augmented Generation»
→ arxiv_search(query="retrieval augmented generation RAG", limit=10)

[→ Weitere Anwendungsbeispiele nach Zielgruppe →](EXAMPLES.md)
```

---

## Bekannte Einschränkungen

- **GitHub Rate-Limit**: 60 Anfragen/h ohne Token. `GITHUB_TOKEN` für den Produktiveinsatz setzen.
- **arXiv**: Neue Paper erscheinen mit bis zu 24 Stunden Verzögerung. An Wochenenden und Feiertagen verzögerte Batches.
- **HackerNews**: Top/Best-Listen aktualisieren sich alle paar Minuten. Sehr neue Stories haben noch geringe Scores.
- **Lobste.rs**: Kleinere Community als HN; tech-fokussiert, aber nicht alle KI-Themen abgedeckt.

---

## Sicherheit & Limiten

- **Read-only:** Alle Tools führen ausschliesslich HTTP-GET-Anfragen aus — keine Posts, Kommentare, Votes oder Schreibzugriffe nach oben.
- **Keine Personendaten:** Der Server fragt öffentliche Tech-Aggregatoren ab. Es werden keine Personendaten erhoben; Autor:innennamen aus öffentlichen Posts/Papers werden 1:1 von der Quelle zurückgegeben und nicht angereichert oder verknüpft.
- **Rate-Limits:** arXiv's Richtlinie von ≤3 Anfragen/Sekunde wird standardmässig respektiert; GitHub-Suche ist ohne `GITHUB_TOKEN` auf 60 Anfragen/Stunde limitiert. Pro Anfrage gilt ein Timeout.
- **Kein Bulk-Harvesting:** Der Server ist für interaktive, dialogische Nutzung gebaut — nicht für Scraping oder Mirroring. Nicht zum Umgehen von Pagination oder ToS einsetzen.
- **Nutzungsbedingungen:** Die Daten unterliegen den ToS der jeweiligen Quellen — [HackerNews](https://news.ycombinator.com/), [arXiv API](https://info.arxiv.org/help/api/tou.html), [Lobste.rs](https://lobste.rs/about), [GitHub](https://docs.github.com/en/site-policy/github-terms/github-terms-of-service).
- **Keine Garantien:** Community-Projekt, nicht affiliiert mit HackerNews / Y Combinator, arXiv / Cornell, Lobste.rs oder GitHub. Verfügbarkeit hängt von den vorgelagerten APIs ab.

---

## Changelog

Siehe [CHANGELOG.md](CHANGELOG.md)

---

## Lizenz

MIT-Lizenz — siehe [LICENSE](LICENSE)

---

## Autorin / Autor

Hayal Oezkan · [malkreide](https://github.com/malkreide)
