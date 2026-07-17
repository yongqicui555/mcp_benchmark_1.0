'use strict';
const http = require('node:http');
const cache = require('../src/cache.js');
const PLUGIN_MANIFEST = require('../.claude-plugin/plugin.json');

const PAGE_SIZE = 100;

function escapeHtml(s) {
  return String(s).replace(/[&<>"']/g, (c) => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;',
  }[c]));
}

function fmtBytes(n) {
  if (n == null) return '—';
  if (n < 1024) return `${n} B`;
  if (n < 1024 * 1024) return `${(n / 1024).toFixed(1)} KB`;
  if (n < 1024 * 1024 * 1024) return `${(n / 1024 / 1024).toFixed(1)} MB`;
  return `${(n / 1024 / 1024 / 1024).toFixed(2)} GB`;
}

function fmtAge(ts) {
  if (!ts) return '—';
  const d = Date.now() - ts;
  if (d < 60_000) return `${Math.round(d / 1000)}s ago`;
  if (d < 3_600_000) return `${Math.round(d / 60_000)}m ago`;
  if (d < 86_400_000) return `${Math.round(d / 3_600_000)}h ago`;
  return `${Math.round(d / 86_400_000)}d ago`;
}

function domainOf(url) {
  try { return new URL(url).hostname; } catch { return '—'; }
}

function buildHtml({ query, offset, scopeAll }) {
  const scopeOpts = { global: scopeAll };
  const s = cache.stats(scopeOpts);
  const allRows = cache.list(PAGE_SIZE * 10, 0, scopeOpts); // up to 1000 for search context
  const filtered = query
    ? allRows.filter((r) => r.url.toLowerCase().includes(query.toLowerCase()) || domainOf(r.url).toLowerCase().includes(query.toLowerCase()))
    : allRows;
  const pageStart = Math.max(0, offset);
  const recent = filtered.slice(pageStart, pageStart + PAGE_SIZE);
  const hasMore = filtered.length > pageStart + PAGE_SIZE;
  const hasPrev = pageStart > 0;

  const domains = cache.statsByDomain(15, scopeOpts);
  const namespaces = cache.listNamespaces();

  const rowHtml = (r) => `
    <tr>
      <td><span class="dom">${escapeHtml(domainOf(r.url))}</span></td>
      <td><a href="${escapeHtml(r.url)}" target="_blank" rel="noopener">${escapeHtml(r.url.length > 80 ? r.url.slice(0, 80) + '…' : r.url)}</a></td>
      ${scopeAll ? `<td><span class="ns">${escapeHtml(r.namespace || '(default)')}</span></td>` : ''}
      <td class="num">${r.hit_count}</td>
      <td class="num">${fmtAge(r.cached_at)}</td>
      <td class="num">${fmtAge(r.last_hit_at)}</td>
      <td class="actions">
        <button class="refresh" data-url="${escapeHtml(r.url)}" title="Refresh (invalidate)">↻</button>
        <button class="invalidate" data-url="${escapeHtml(r.url)}" title="Drop all entries for this URL">×</button>
      </td>
    </tr>`;

  const qStr = query ? `&q=${encodeURIComponent(query)}` : '';
  const scopeStr = scopeAll ? '&all=1' : '';
  const prevHref = hasPrev ? `?offset=${Math.max(0, pageStart - PAGE_SIZE)}${qStr}${scopeStr}` : '#';
  const nextHref = hasMore ? `?offset=${pageStart + PAGE_SIZE}${qStr}${scopeStr}` : '#';

  const errSummary = s.last_hook_error_at
    ? `<div class="err">⚠ last hook error: ${fmtAge(s.last_hook_error_at)}${s.last_hook_error_msg ? ` — <code>${escapeHtml(s.last_hook_error_msg)}</code>` : ''} (log: <code>${escapeHtml(s.hook_log_path || '')}</code>)</div>`
    : '';

  const oversizeBadge = s.oversize_skipped > 0
    ? `<div class="warn">⚠ ${s.oversize_skipped} oversize payloads skipped${s.last_oversize_url ? ` — last: <code>${escapeHtml(s.last_oversize_url)}</code>` : ''}</div>`
    : '';

  const nsSection = namespaces.length > 1
    ? `<div class="ns-bar">Namespaces in DB: ${namespaces.map((n) => `<code>${escapeHtml(n || '(default)')}</code>`).join(' · ')} — switch via <code>WEBCACHE_NAMESPACE=...</code> env, or view all: <a href="?all=1">all namespaces</a> · <a href="/">scoped</a></div>`
    : '';

  return `<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>claude-webcache dashboard</title>
<style>
  :root { color-scheme: light dark; }
  body { font: 14px/1.5 -apple-system, system-ui, sans-serif; max-width: 1200px; margin: 2rem auto; padding: 0 1rem; }
  h1 { margin: 0 0 .5rem; font-size: 1.4rem; }
  h2 { font-size: 1rem; margin: 1.5rem 0 .5rem; }
  .sub { color: #888; margin-bottom: 1.5rem; }
  .stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: .75rem; margin-bottom: 1.5rem; }
  .stat { padding: .75rem 1rem; background: rgba(127,127,127,.1); border-radius: 6px; }
  .stat .v { font-size: 1.4rem; font-weight: 600; }
  .stat .l { font-size: .75rem; color: #888; text-transform: uppercase; letter-spacing: .04em; }
  .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 2rem; margin-bottom: 1.5rem; }
  @media (max-width: 720px) { .grid { grid-template-columns: 1fr; } }
  table { width: 100%; border-collapse: collapse; font-size: 13px; }
  th, td { text-align: left; padding: .4rem .6rem; border-bottom: 1px solid rgba(127,127,127,.2); }
  th { font-weight: 600; color: #888; font-size: .75rem; text-transform: uppercase; letter-spacing: .04em; }
  td.num { text-align: right; white-space: nowrap; color: #888; font-variant-numeric: tabular-nums; }
  td.actions { white-space: nowrap; }
  .dom, .ns { display: inline-block; padding: 1px 6px; background: rgba(127,127,127,.15); border-radius: 3px; font-size: 11px; }
  .ns { background: rgba(80,160,220,.18); }
  a { color: inherit; }
  input[type=search] { width: 100%; padding: .5rem .75rem; font: inherit; border: 1px solid rgba(127,127,127,.3); border-radius: 4px; background: transparent; color: inherit; margin-bottom: 1rem; }
  button.invalidate, button.refresh { background: transparent; border: 1px solid rgba(127,127,127,.3); border-radius: 3px; cursor: pointer; padding: 0 6px; font-size: 14px; line-height: 1.4; color: inherit; margin-right: 2px; }
  button.invalidate:hover { background: rgba(220,50,50,.15); border-color: rgba(220,50,50,.5); }
  button.refresh:hover { background: rgba(50,160,220,.15); border-color: rgba(50,160,220,.5); }
  .empty { color: #888; padding: 1rem; text-align: center; }
  .err { padding: .5rem .75rem; background: rgba(220,50,50,.12); border-left: 3px solid rgba(220,50,50,.6); border-radius: 3px; margin-bottom: 1rem; font-size: 13px; }
  .warn { padding: .4rem .6rem; background: rgba(220,160,50,.12); border-left: 3px solid rgba(220,160,50,.6); border-radius: 3px; margin-bottom: 1rem; font-size: 13px; }
  .ns-bar { padding: .4rem .6rem; background: rgba(80,160,220,.08); border-radius: 4px; margin-bottom: 1rem; font-size: 12px; color: #666; }
  .pager { display: flex; gap: .5rem; margin-top: 1rem; }
  .pager a { padding: .25rem .75rem; border: 1px solid rgba(127,127,127,.3); border-radius: 3px; text-decoration: none; }
  .pager a.disabled { opacity: .3; pointer-events: none; }
  code { font-size: 12px; background: rgba(127,127,127,.12); padding: 1px 4px; border-radius: 2px; }
</style>
</head>
<body>
  <h1>claude-webcache <span class="sub">v${escapeHtml(PLUGIN_MANIFEST.version)} · ns: <code>${escapeHtml(scopeAll ? '* (all)' : (s.namespace || '(default)'))}</code></span></h1>
  <div class="sub">DB: <code>${escapeHtml(cache.DB_PATH)}</code></div>
  ${errSummary}
  ${oversizeBadge}
  ${nsSection}

  <div class="stats">
    <div class="stat"><div class="v">${s.total}</div><div class="l">entries</div></div>
    <div class="stat"><div class="v">${s.hits}</div><div class="l">hits</div></div>
    <div class="stat"><div class="v">${s.misses}</div><div class="l">misses (global)</div></div>
    <div class="stat"><div class="v">${(s.hit_rate * 100).toFixed(1)}%</div><div class="l">hit rate</div></div>
    <div class="stat"><div class="v">${fmtBytes(s.db_size_bytes)}</div><div class="l">db size</div></div>
    ${s.compressed_rows != null ? `<div class="stat"><div class="v">${s.compressed_rows}</div><div class="l">gz rows</div></div>` : ''}
    <div class="stat"><div class="v">${s.evicted}</div><div class="l">evicted</div></div>
    <div class="stat"><div class="v">${fmtAge(s.last)}</div><div class="l">last write</div></div>
  </div>

  <div class="grid">
    <div>
      <h2 style="margin-top:0">Top URLs by hits</h2>
      <table>
        <thead><tr><th>URL</th><th>hits</th></tr></thead>
        <tbody>
          ${s.top_urls.length === 0
    ? '<tr><td colspan="2" class="empty">No hits yet</td></tr>'
    : s.top_urls.map((r) => `<tr><td>${escapeHtml(r.url)}</td><td class="num">${r.hit_count}</td></tr>`).join('')}
        </tbody>
      </table>
    </div>
    <div>
      <h2 style="margin-top:0">Top domains</h2>
      <table>
        <thead><tr><th>Domain</th><th>entries</th><th>hits</th><th>avg</th><th>last</th></tr></thead>
        <tbody>
          ${domains.length === 0
    ? '<tr><td colspan="5" class="empty">Empty</td></tr>'
    : domains.map((d) => `<tr><td>${escapeHtml(d.domain)}</td><td class="num">${d.entries}</td><td class="num">${d.total_hits}</td><td class="num">${d.avg_hits_per_entry}</td><td class="num">${fmtAge(d.last_fetched_at)}</td></tr>`).join('')}
        </tbody>
      </table>
    </div>
  </div>

  <h2>Recent (${recent.length} shown, page offset ${pageStart}${query ? `, filtered from ${allRows.length}` : ''})</h2>
  <form method="get" action="/">
    <input type="search" name="q" value="${escapeHtml(query || '')}" placeholder="Filter by URL or domain substring…" autofocus>
    ${scopeAll ? '<input type="hidden" name="all" value="1">' : ''}
  </form>
  <table>
    <thead>
      <tr><th>Domain</th><th>URL</th>${scopeAll ? '<th>ns</th>' : ''}<th>hits</th><th>cached</th><th>last hit</th><th></th></tr>
    </thead>
    <tbody>
      ${recent.length === 0
    ? `<tr><td colspan="${scopeAll ? 7 : 6}" class="empty">No entries match</td></tr>`
    : recent.map(rowHtml).join('')}
    </tbody>
  </table>
  <div class="pager">
    <a href="${escapeHtml(prevHref)}" class="${hasPrev ? '' : 'disabled'}">← Prev</a>
    <a href="${escapeHtml(nextHref)}" class="${hasMore ? '' : 'disabled'}">Next →</a>
  </div>

<script>
async function post(path, payload) {
  return fetch(path, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
}
document.querySelectorAll('button.invalidate').forEach((btn) => {
  btn.addEventListener('click', async () => {
    const url = btn.dataset.url;
    if (!confirm('Invalidate all entries for:\\n' + url + '?')) return;
    const r = await post('/api/invalidate', { url });
    if (r.ok) location.reload();
    else alert('Failed: ' + await r.text());
  });
});
document.querySelectorAll('button.refresh').forEach((btn) => {
  btn.addEventListener('click', async () => {
    const url = btn.dataset.url;
    if (!confirm('Mark for refresh (drop from cache):\\n' + url + '\\n\\nNext WebFetch will re-cache.')) return;
    const r = await post('/api/refresh', { url });
    if (r.ok) location.reload();
    else alert('Failed: ' + await r.text());
  });
});
</script>
</body>
</html>`;
}

function readBody(req) {
  return new Promise((resolve, reject) => {
    let body = '';
    req.on('data', (c) => { body += c; });
    req.on('end', () => resolve(body));
    req.on('error', reject);
  });
}

function start(port) {
  const server = http.createServer(async (req, res) => {
    try {
      const url = new URL(req.url, `http://localhost:${port}`);

      if (req.method === 'GET' && (url.pathname === '/' || url.pathname === '/index.html')) {
        const q = url.searchParams.get('q') || '';
        const offset = Number(url.searchParams.get('offset')) || 0;
        const scopeAll = url.searchParams.get('all') === '1';
        res.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8' });
        res.end(buildHtml({ query: q, offset, scopeAll }));
        return;
      }

      if (req.method === 'GET' && url.pathname === '/api/stats') {
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify(cache.stats()));
        return;
      }

      if (req.method === 'GET' && url.pathname === '/api/domains') {
        const limit = Number(url.searchParams.get('limit')) || 20;
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify(cache.statsByDomain(limit)));
        return;
      }

      if (req.method === 'POST' && url.pathname === '/api/invalidate') {
        const body = await readBody(req);
        const { url: target } = JSON.parse(body || '{}');
        if (!target) { res.writeHead(400); res.end('url required'); return; }
        const deleted = cache.invalidate(target);
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ deleted }));
        return;
      }

      if (req.method === 'POST' && url.pathname === '/api/refresh') {
        const body = await readBody(req);
        const { url: target } = JSON.parse(body || '{}');
        if (!target) { res.writeHead(400); res.end('url required'); return; }
        const deleted = cache.invalidate(target);
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ refreshed: target, invalidated: deleted }));
        return;
      }

      res.writeHead(404); res.end('not found');
    } catch (e) {
      try { res.writeHead(500); res.end(e.message); } catch {}
    }
  });

  server.listen(port, '127.0.0.1', () => {
    process.stdout.write(`claude-webcache dashboard → http://localhost:${port}/\n`);
    process.stdout.write('Ctrl-C to stop.\n');
  });

  server.on('error', (err) => {
    process.stderr.write(`Failed to start dashboard: ${err.message}\n`);
    process.exit(1);
  });

  return server;
}

module.exports = { start };
