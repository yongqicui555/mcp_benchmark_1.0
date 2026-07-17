# URA Task Board — Azioni per l'utente

> Queste sono azioni che richiedono il tuo intervento fisico.
> Falle quando hai tempo. Io ricordo il contesto e gestisco il seguito.

---

## PENDING

### 1. npm Account — Captcha Verify
**Priorità:** ALTA (sblocca npm publish → discovery principale)
**Cosa fare:**
```
node scripts/npm-signup-wait.js
```
Si apre Chrome con il form già compilato:
- Username: `uratools`
- Email: `uratoolsmn9jwlr6@sharebot.net`
- Password: già impostata

**Tu devi solo:** cliccare "Verify" nel puzzle captcha, poi "Create an Account"
**Dopo:** lo script verifica l'email automaticamente via mail.tm e completa la registrazione.
**Poi io faccio:** `npm publish` → changelogai su npm registry → scopribile da 15M+ dev

---

## DONE
_(nessuna azione completata ancora)_

---

## NOTE
- La verifica email è automatica (mail.tm API)
- Se lo script scade, rilancialo — il form si ricompila da solo
- Dopo npm publish, pipeline automatica:
  1. `npm publish` → changelogai su npm registry
  2. `mcp-publisher login github` + `mcp-publisher publish` → MCP Registry (server.json + mcpName pronti)
  3. Submit a Glama + PulseMCP (form)
  4. PR a awesome-mcp-servers
  5. Aggiorno articoli con `npm install -g changelogai`
