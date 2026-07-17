# Use Cases & Beispiele — parlament-mcp

Hier finden Sie praxisnahe Anwendungsfälle für verschiedene Zielgruppen. Jeder Fall zeigt, wie die spezifischen Tools des Servers genutzt werden können, um relevante Informationen aus den Daten des Schweizer Parlaments abzurufen.

Da dieser Server auf die öffentliche Curia Vista API zugreift, wird für keines der Tools ein API-Key benötigt.

---

## 🏫 Bildung & Schule
Lehrpersonen, Schulbehörden, Fachreferent:innen

**Aktuelle Bildungsgeschäfte finden**
«Zeige mir alle hängigen parlamentarischen Vorstösse zum Thema Digitalisierung in der Schule.»
→ `parlament_search_business(keyword="Digitalisierung", keyword2="Schule", status="Eingereicht")`

Warum nützlich: Erlaubt Lehrpersonen und Schulleitungen, sich über anstehende politische Entscheide zu informieren, die den Unterrichtsalltag oder die Schulentwicklung direkt betreffen könnten.

**Debatten zur Schulpolitik analysieren**
«Was hat Nationalrätin Wasserfallen in der letzten Session zum Thema Bildung gesagt?»
→ `parlament_get_transcripts(speaker_name="Wasserfallen", keyword="Bildung")`

Warum nützlich: Eignet sich für den Staatskundeunterricht, um Schülern an konkreten Voten aufzuzeigen, wie im Parlament über aktuelle Schulthemen debattiert wird.

---

## 👨‍👩‍👧 Eltern & Schulgemeinde
Elternräte, interessierte Erziehungsberechtigte

**Familienpolitische Vorstösse verfolgen**
«Welche Motionen oder Postulate zur familienexternen Kinderbetreuung wurden in den letzten zwei Jahren eingereicht?»
→ `parlament_search_business(keyword="Kinderbetreuung", submitted_after="2022-01-01")`

Warum nützlich: Hilft Elternräten und Familien, politische Initiativen zu finden, die finanzielle Entlastungen oder bessere Betreuungsangebote fordern.

**Abstimmungsverhalten bei Familienthemen prüfen**
«Wie hat der Nationalrat kürzlich über Vorlagen zum Thema Elternurlaub abgestimmt?»
→ `parlament_get_votes(keyword="Elternurlaub")`

Warum nützlich: Macht für interessierte Eltern transparent, wie das Parlament bei für Familien entscheidenden Fragen gestimmt hat.

---

## 🗳️ Bevölkerung & öffentliches Interesse
Allgemeine Öffentlichkeit, politisch und gesellschaftlich Interessierte

**Details zu einem bekannten Geschäft abrufen**
«Wie lautet der genaue Text des Vorstosses mit der ID 20243000 und wie hat der Bundesrat darauf geantwortet?»
→ `parlament_get_business(business_id=20243000)`

Warum nützlich: Bietet Bürgern direkten, ungefilterten Zugang zu den Originaltexten von Vorstössen und den offiziellen Stellungnahmen der Regierung, ohne auf Medienzusammenfassungen angewiesen zu sein.

**Regionale Vertretung prüfen**
«Wer sind die aktiven National- und Ständeräte aus dem Kanton Graubünden?»
→ `parlament_search_members(canton="GR", active_only=True)`

Warum nützlich: Zeigt Bürgern schnell, wer ihren Heimatkanton im Bundeshaus vertritt, um diese bei regionalen Anliegen kontaktieren zu können.

**Transparenz bei Parlamentsentscheiden**
«Wann findet die nächste Session statt und welche Abstimmungen gab es zum Thema Umweltschutz in der letzten?»
→ `parlament_get_sessions(limit=5)`
→ `parlament_get_votes(keyword="Umweltschutz", session_id=...[von get_sessions])`

Warum nützlich: Stärkt das demokratische Engagement, da Wähler das Abstimmungsverhalten und die Traktanden direkt nachvollziehen können.

---

## 🤖 KI-Interessierte & Entwickler:innen
MCP-Enthusiast:innen, Forscher:innen, Prompt Engineers, öffentliche Verwaltung

**Analyse von Redeverhalten (Text Mining)**
«Suche alle Transkripte von Ständeräten der letzten Session zum Thema 'Künstliche Intelligenz'.»
→ `parlament_get_sessions(limit=1)`
→ `parlament_get_transcripts(keyword="Künstliche Intelligenz", council="SR", session_id=...[von get_sessions])`

Warum nützlich: Ideal für Forscher oder NLP-Entwickler, die parlamentarische Debatten automatisiert auf bestimmte Themen oder Stimmungen hin auswerten möchten.

**Gesetze und Debatten verknüpfen (Multi-Server-Szenario)**
«Finde das Bundesgesetz über den Datenschutz im fedlex-mcp und zeige mir gleichzeitig die parlamentarischen Debatten aus dem Parlament, in denen vor der Verabschiedung über Datenschutz diskutiert wurde.»
→ `fedlex_search_enactment(query="Datenschutz", sort="dateDesc")`
→ `parlament_get_transcripts(keyword="Datenschutz")`

Warum nützlich: Kombiniert die rechtskräftigen Gesetzestexte von [fedlex-mcp](https://github.com/malkreide/fedlex-mcp) mit der parlamentarischen Entstehungsgeschichte, um die Absicht des Gesetzgebers (historische Auslegung) umfassend zu analysieren.

---

## 🔧 Technische Referenz: Tool-Auswahl nach Anwendungsfall

| Ich möchte… | Tool(s) | Auth nötig? |
|-------------|---------|-------------|
| **hängige oder erledigte Vorstösse finden** | `parlament_search_business` | Nein |
| **den vollen Text und die Antwort des Bundesrats lesen** | `parlament_get_business` | Nein |
| **Parlamentarier meines Kantons oder meiner Partei suchen** | `parlament_search_members` | Nein |
| **die Resultate von Ratsabstimmungen einsehen** | `parlament_get_votes` | Nein |
| **die Daten der laufenden oder kommenden Sessionen abfragen** | `parlament_get_sessions` | Nein |
| **nachlesen, wer was im Rat gesagt hat (Wortprotokoll)** | `parlament_get_transcripts` | Nein |
