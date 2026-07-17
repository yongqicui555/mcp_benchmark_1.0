# claude-webcache — Diagnosis 2026-05-20

> Companion doc для `[[rd275]]` (Cards/rd275 claude-webcache investigate — diagnosis 2026-05-15.md). Картировка root cause + follow-up actions.

---

## TL;DR

- **Root cause confirmed:** `${CLAUDE_PLUGIN_ROOT}` в `hooks.json` не разрешался в Claude Code 2.1.x → PostToolUse hook silent-failed → cache.db stale c 2026-04-30 (rows write) / 2026-05-14 (file mtime, последний successful открытие/touch).
- **Fix #1 confirmed applied:** commit `2bd5855` (2026-05-15) — `plugin/hooks/hooks.json` теперь использует `node ./scripts/hook-stats.cjs` и `node ./scripts/hook-webfetch-cache.cjs` (relative paths).
- **Hook firing now:** **unknown** — local v0.4.0 fix живёт только в `D:/Yahia/active/claude-webcache/plugin/`, плагин в `~/.claude/plugins/cache/theyahia/claude-webcache/0.1.5/` всё ещё broken-версия. Без v0.4.0 publish + reinstall hook не fires.

---

## Verification log (2026-05-20)

### Fix #1: hooks.json relative paths

`D:/Yahia/active/claude-webcache/plugin/hooks/hooks.json` (current):

```json
{
  "hooks": {
    "SessionStart": [{ "matcher": "startup|clear|compact", "hooks": [
      { "type": "command", "command": "node ./scripts/hook-stats.cjs" }
    ]}],
    "PostToolUse": [{ "matcher": "WebFetch", "hooks": [
      { "type": "command", "command": "node ./scripts/hook-webfetch-cache.cjs" }
    ]}]
  }
}
```

✅ Корректно — relative `./scripts/`. Per CLAUDE.md правило (секция «Пути внутри плагина»): `${CLAUDE_PLUGIN_ROOT}` для hooks shell команд **избегать**.

### Cache.db state

| Metric | Value |
|---|---|
| Path | `C:/Users/romim/.webcache/cache.db` |
| File mtime | 2026-05-14 14:24 |
| Row count | **7** |
| MAX(cached_at) raw | `1777554491186` |
| MAX(cached_at) human | **2026-04-30 16:08:11** |
| MAX(last_hit_at) human | 2026-04-30 11:50:48 |

⛔ Ни одного нового row с 2026-04-30. Hook не fires (или fires но не пишет). Hook log файла (`~/.webcache/hook.log`) **нет** → hook никогда не запускался.

### npm registry state

```
$ npm view @theyahia/claude-webcache versions
['0.1.0', '0.1.1', '0.1.2', '0.1.3', '0.1.4', '0.1.5']
```

❌ v0.4.0 ещё не опубликован. Local `package.json` уже на 0.4.0.

### Installed plugin

`C:/Users/romim/.claude/plugins/cache/theyahia/claude-webcache/0.1.5/` — **v0.1.5 (broken)** активна (29 `.in_use/` PID lockfiles → активно загружается в sessions).

---

## Root cause (confirmed)

**Гипотеза 1 из rd275 подтверждена:**

`${CLAUDE_PLUGIN_ROOT}` в hooks.json **silent-fails** в Claude Code 2.1.x:
- Не резолвится в реальный path
- Не выдаёт error
- Hook просто не запускается
- Cache.db остаётся stale, log не пишется

**Эмпирический proof:** обе hooks (SessionStart `hook-stats.cjs` и PostToolUse `hook-webfetch-cache.cjs`) используют `${CLAUDE_PLUGIN_ROOT}` в v0.1.5 и обе не fires. Если бы проблема была в matcher syntax — SessionStart всё равно бы запускался.

**Гипотезы 2 (matcher `WebFetch`) и 3 (`node:sqlite` import error) исключены** — SessionStart тоже мёртв, log отсутствует → import даже не достигается.

---

## Follow-up actions (USER-required, не агентом)

### rd973 — v0.4.0 npm publish

**Where:** terminal на этой машине (не Claude Code Bash — npm login требует interactive browser flow).

**Commands:**

```powershell
# Шаг 1 — login (если ещё не залогинен или session expired):
#   ОТДЕЛЬНЫЙ терминал, не Claude Code (Claude Code Bash = non-interactive)
npm whoami                              # проверить — залогинен ли
npm login                               # если нет — browser-based login flow

# Шаг 2 — sanity check package
cd D:/Yahia/active/claude-webcache
npm view @theyahia/claude-webcache version   # должно показать 0.1.5 (текущий публичный)
cat package.json | grep version              # должно показать "0.4.0"

# Шаг 3 — publish с OTP (2FA)
#   Получить OTP из Authenticator app
npm publish --otp=XXXXXX                # XXXXXX = 6-digit код из Authenticator

# Шаг 4 — verify
npm view @theyahia/claude-webcache version   # должно теперь показать 0.4.0
```

**Verify success:**
- `npm view @theyahia/claude-webcache version` → `0.4.0`
- `npm view @theyahia/claude-webcache versions` → массив содержит `'0.4.0'`

**Pre-flight check:**
- `package.json` version = `0.4.0` ✅
- `plugin/.claude-plugin/plugin.json` version = `0.4.0` (verify before publish)
- `.claude-plugin/marketplace.json` plugins[0].version = `0.4.0` (verify before publish)

---

### rd974 — v0.4.0 MCP Registry republish

**Where:** terminal на этой машине.

**Commands:**

```powershell
cd D:/Yahia/active/claude-webcache

# Шаг 1 — sanity check server.json
cat server.json                         # должен содержать version: 0.4.0

# Шаг 2 — token (если истёк)
#   Path к token: .mcpregistry_registry_token (gitignored)
ls .mcpregistry_registry_token          # должен существовать

# Шаг 3 — publish
mcp-publisher.exe publish

# Шаг 4 — verify
#   Открыть https://registry.mcp.dev/api/v0/servers/io.github.theYahia/claude-webcache
#   В JSON ответе version_detail.version = "0.4.0"
```

**Verify success:**
- MCP Registry API возвращает `version_detail.version = "0.4.0"`
- Listing на https://registry.mcp.dev обновлён

---

### rd975 — v0.4.0 local verify after restart

**Where:** Claude Code session (новый restart обязателен — plugin marketplace cache читается только при старте).

**Commands:**

```
# В Claude Code (после v0.4.0 npm publish + MCP Registry publish):

# Шаг 1 — remove + add cycle (нужен полный refresh)
/plugin marketplace remove theyahia
/plugin marketplace add theYahia/claude-webcache
/plugin install claude-webcache@theyahia

# Шаг 2 — restart Claude Code session (.mcp.json + hooks читаются только при старте)

# Шаг 3 — 5 smoke checks (после restart):
```

**5 smoke checks:**

1. **Plugin version installed**
   ```powershell
   ls C:/Users/romim/.claude/plugins/cache/theyahia/claude-webcache/
   ```
   Должна появиться папка `0.4.0/`.

2. **hooks.json содержит relative paths**
   ```powershell
   cat C:/Users/romim/.claude/plugins/cache/theyahia/claude-webcache/0.4.0/hooks/hooks.json
   ```
   `command` поля должны быть `node ./scripts/hook-*.cjs` (не `${CLAUDE_PLUGIN_ROOT}`).

3. **SessionStart hook fired** — сразу после restart Claude Code session:
   ```powershell
   ls C:/Users/romim/.webcache/hook.log
   ```
   Файл должен существовать (создаётся при first hook run). Должны быть строки про SessionStart.

4. **PostToolUse hook fires на WebFetch** — в Claude Code сделать тест:
   ```
   WebFetch https://example.com summary
   ```
   Затем:
   ```powershell
   python -c "import sqlite3; c=sqlite3.connect('C:/Users/romim/.webcache/cache.db'); print(list(c.execute('SELECT COUNT(*) FROM cache')))"
   ```
   Counter должен увеличиться с 7 → 8. Также `hook.log` должен иметь новую строку про PostToolUse.

5. **`cached_fetch` MCP tool работает** — в Claude Code:
   ```
   cached_fetch(url="https://example.com", prompt="summary")
   ```
   На second call (после теста #4) должен вернуть cached text (cache HIT), не `[CACHE_MISS]`.

**Definition of done для rd975:**
- Все 5 smoke checks PASS
- cache.db rows растут на каждый WebFetch
- hook.log existed and growing
- rd275 / rd973 / rd974 / rd975 закрыты в Board

---

## Why this exit path

- **Fix #1 (local edit)** = agent-doable, done.
- **rd973 (npm publish)** = blocking on user OTP, нельзя automate.
- **rd974 (MCP Registry)** = depends on rd973 publish first.
- **rd975 (verify)** = blocks on rd973 + rd974 + Claude Code restart.

Текущий agent делает diagnosis-doc + закрывает rd275. Остальные карточки — user-action queue.

---

## Backlinks

- Card: `[[rd275]]` — `Cards/rd275 claude-webcache investigate — diagnosis 2026-05-15.md`
- Follow-ups: `[[rd973]]`, `[[rd974]]`, `[[rd975]]`
- Reference: CLAUDE.md «Claude Code plugins — marketplace.json и публикация»
