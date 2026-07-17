# Changelog

Tutte le modifiche significative a questo progetto vengono documentate in questo file.

Il formato segue [Keep a Changelog](https://keepachangelog.com/it/1.1.0/),
e questo progetto aderisce a [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.7] - 2026-05-04

### Changed
- `list_heu_documents`: chiarito nella description del tool e dei parametri che `created_from` e `created_to` devono essere passati **insieme**. Passare solo una delle due date può far sì che l'API HEU non restituisca tutti i documenti del periodo. Per "tutti i documenti senza limiti di data" basta omettere entrambe.

## [0.1.6] - 2026-05-04

### Added
- Nuovo tool `extract_heu_document_parties`: estrae i dati anagrafici delle parti da un documento HEU combinando metadati (firmatari, ruoli, stato firma) con dati estratti dal testo: codice fiscale, P.IVA, **codice univoco SDI**, email, PEC, luogo e data di nascita, indirizzi, CAP.
- Nuovo tool `extract_pdf_document_parties`: equivalente per i PDF caricati.
- Pattern regex ottimizzati per documenti italiani (CF 16 caratteri con omocodia, P.IVA 11 cifre, SDI 7 alfanumerici, varianti di etichetta come "Codice Univoco SDI", "Codice Destinatario", "C.U. Destinatario").
- Parametro opzionale `include_text` per includere il testo grezzo nel risultato.

## [0.1.5] - 2026-05-04

### Added
- Nuovo tool `read_heu_document`: legge il contenuto testuale di un documento HEU senza salvarlo in locale. Ritorna il testo direttamente nella risposta MCP, abilitando casi d'uso come riassunto, ricerca clausole, confronto contratti.
- Nuovo tool `read_pdf_document`: equivalente per i PDF caricati.
- Supporto al parametro `pages` con range arbitrari (`"1-3"`, `"5"`, `"1,3,5-7"`).
- Limite di sicurezza di 100 pagine quando non viene specificato il range, con notifica `truncated` nel payload.
- Nuova dipendenza: `pypdf>=5.0.0` per l'estrazione testo.

## [0.1.4] - 2026-05-04

### Fixed
- Corretto il case del namespace MCP Registry: `io.github.Lucav21/heu-mcp` (case-match con l'username GitHub canonical, richiesto dal registry).

## [0.1.3] - 2026-05-04

### Changed
- Aggiornato namespace MCP Registry e URL del repository al nuovo username GitHub `Lucav21`.

## [0.1.2] - 2026-05-04

### Added
- Marker `mcp-name` nel README per la verifica di ownership richiesta dal MCP Registry ufficiale.

## [0.1.1] - 2026-05-04

### Fixed
- Corretti gli URL del progetto (homepage, repository, issues) che puntavano a un username GitHub errato.

## [0.1.0] - 2026-05-04

### Added
- Prima release pubblica.
- 14 tool MCP che coprono interamente l'API HEU Legal v1:
  - Documenti nativi: list, get, list placeholders, create, prompt signature, download PDF.
  - PDF caricati: list, get, list signers, list signer placeholders, list placeholders, create, prompt signature.
  - Health check.
- Variabili d'ambiente: `HEU_API_KEY`, `HEU_BASE_URL`, `HEU_DOWNLOAD_DIR`.
- Compatibilità Python 3.10+.
- Documentazione README con esempi di configurazione per Claude Desktop e Claude Code.
