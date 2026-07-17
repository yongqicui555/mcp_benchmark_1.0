import { FRAMEWORKS } from '../compliance/controls.js';

const SEV_BG    = { red: '#fef2f2', amber: '#fffbeb', green: '#f0fdf4' };
const SEV_BADGE = { red: '🔴', amber: '🟡', green: '🟢' };
const FW_ACCENT = { 'soc2': '#6366f1', 'eu-ai-act': '#0ea5e9', 'nist': '#10b981', 'owasp': '#f97316' };
const FW_ICON   = { 'soc2': '🛡️', 'eu-ai-act': '🇪🇺', 'nist': '🏛️', 'owasp': '🔓' };

function esc(s) {
  return String(s ?? '')
    .replace(/&/g, '&amp;').replace(/</g, '&lt;')
    .replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

function tick(v) {
  if (v === true)    return '<span class="tick yes">✓</span>';
  if (v === 'n/a')   return '<span class="tick na">—</span>';
  return '<span class="tick no">✗</span>';
}

function sevPill(sev) {
  const cls = { red: 'pill-red', amber: 'pill-amber', green: 'pill-green' }[sev] ?? '';
  return `<span class="pill ${cls}">${SEV_BADGE[sev]} ${sev}</span>`;
}

function levelBadge(level) {
  return level === 'error'
    ? '<span class="lvl-badge lvl-error">error</span>'
    : '<span class="lvl-badge lvl-warn">warning</span>';
}

export function renderHtml(report) {
  const date = new Date().toISOString().slice(0, 10);
  const hasCompliance = !!(report.compliance?.frameworks?.length);
  const sm = report.summary;

  // ── gate banner ───────────────────────────────────────────────────────────
  const gateBanner = report.gate
    ? `<div class="gate-banner ${report.gate.passed ? 'gate-pass' : 'gate-fail'}">
        <span class="gate-icon">${report.gate.passed ? '✅' : '❌'}</span>
        <span>${report.gate.passed
          ? 'CI gate passed — no red side-effectful surfaces'
          : `CI gate failed — <strong>${report.gate.blocking}</strong> blocking surface(s)`}</span>
      </div>`
    : '';

  // ── compliance violation summary table ────────────────────────────────────
  let complianceSummarySection = '';
  let frameworkSections = '';

  if (hasCompliance) {
    const summaryRows = report.compliance.frameworks.map(fw => {
      const v = report.compliance.violations[fw] ?? { error: 0, warning: 0 };
      const accent = FW_ACCENT[fw] ?? '#6366f1';
      const icon = FW_ICON[fw] ?? '📋';
      const label = esc(FRAMEWORKS[fw] ?? fw);
      return `<div class="fw-summary-card" style="border-top:3px solid ${accent}">
        <div class="fw-summary-icon">${icon}</div>
        <div class="fw-summary-label">${label}</div>
        <div class="fw-summary-counts">
          <span class="fw-count err">${v.error} <small>error${v.error !== 1 ? 's' : ''}</small></span>
          <span class="fw-count warn">${v.warning} <small>warning${v.warning !== 1 ? 's' : ''}</small></span>
        </div>
      </div>`;
    }).join('');

    complianceSummarySection = `
    <section class="section">
      <h2 class="section-title">Compliance Overview</h2>
      <div class="fw-summary-grid">${summaryRows}</div>
    </section>`;

    // ── per-framework detail sections ──────────────────────────────────────
    for (const fw of report.compliance.frameworks) {
      const label = esc(FRAMEWORKS[fw] ?? fw);
      const accent = FW_ACCENT[fw] ?? '#6366f1';
      const icon = FW_ICON[fw] ?? '📋';

      const allViolations = [];
      for (const s of report.surfaces) {
        for (const v of (s.violations ?? [])) {
          if (v.framework === fw) allViolations.push({ surface: s, violation: v });
        }
      }

      let controlsHtml = '';
      if (!allViolations.length) {
        controlsHtml = '<p class="empty-state">✅ No violations found for this framework.</p>';
      } else {
        const byControl = new Map();
        for (const { surface, violation } of allViolations) {
          if (!byControl.has(violation.id)) byControl.set(violation.id, { violation, surfaces: [] });
          byControl.get(violation.id).surfaces.push(surface);
        }

        for (const [, { violation, surfaces }] of byControl) {
          const affectedRows = surfaces.map(s => {
            const se = s.sideEffects?.length ? `<span class="se-tags">${s.sideEffects.map(e => `<span class="se-tag">${esc(e)}</span>`).join('')}</span>` : '<span class="dim">—</span>';
            return `<tr>
              <td><code class="filepath">${esc(s.file)}</code></td>
              <td><span class="sink-badge sink-${s.sink.replace('-','')}">${esc(s.sink)}</span></td>
              <td>${se}</td>
              <td>${sevPill(s.severity)}</td>
            </tr>`;
          }).join('');

          controlsHtml += `
          <div class="control-card ${violation.level}">
            <div class="control-header">
              <div class="control-meta">
                ${levelBadge(violation.level)}
                <code class="control-id" style="color:${accent}">${esc(violation.id)}</code>
              </div>
              <h4 class="control-title">${esc(violation.title)}</h4>
              <p class="control-desc">${esc(violation.description)}</p>
            </div>
            <div class="control-body">
              <table class="inner-table">
                <thead><tr><th>File</th><th>Sink</th><th>Side Effects</th><th>Severity</th></tr></thead>
                <tbody>${affectedRows}</tbody>
              </table>
            </div>
          </div>`;
        }
      }

      const totalViolations = allViolations.length;
      frameworkSections += `
      <section class="section fw-section" id="fw-${esc(fw)}">
        <details open>
          <summary class="fw-summary-bar" style="--accent:${accent}">
            <span class="fw-summary-left">
              <span class="fw-icon">${icon}</span>
              <span class="fw-name">${label}</span>
              <span class="fw-count-pill">${totalViolations} violation${totalViolations !== 1 ? 's' : ''}</span>
            </span>
            <span class="fw-chevron">▾</span>
          </summary>
          <div class="fw-controls">${controlsHtml}</div>
        </details>
      </section>`;
    }
  }

  // ── all surfaces table ────────────────────────────────────────────────────
  const order = { red: 0, amber: 1, green: 2 };
  const sorted = [...report.surfaces].sort((a, b) => order[a.severity] - order[b.severity]);
  const surfaceRows = sorted.map(s => {
    const g = s.guardrails;
    const se = s.sideEffects?.length
      ? s.sideEffects.map(e => `<span class="se-tag">${esc(e)}</span>`).join('')
      : '<span class="dim">—</span>';
    return `<tr style="background:${SEV_BG[s.severity]}">
      <td>${sevPill(s.severity)}</td>
      <td><code class="filepath">${esc(s.file)}</code></td>
      <td><span class="provider-tag">${esc(s.providerLabel)}</span></td>
      <td><span class="sink-badge sink-${s.sink.replace('-','')}s">${esc(s.sink)}</span></td>
      <td><span class="se-tags">${se}</span></td>
      <td class="tc">${tick(g.confidence)}</td>
      <td class="tc">${tick(g.fallback)}</td>
      <td class="tc">${tick(g.validation)}</td>
      <td class="tc">${tick(g.humanInLoop)}</td>
      <td class="tc">${tick(g.errorIsolation)}</td>
    </tr>`;
  }).join('');

  const fwNav = hasCompliance
    ? report.compliance.frameworks.map(fw =>
        `<a href="#fw-${esc(fw)}" class="nav-link">${FW_ICON[fw] ?? ''} ${esc(FRAMEWORKS[fw] ?? fw)}</a>`
      ).join('')
    : '';

  return `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>aiglare — ${esc(report.repo)}</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
  <style>
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

    :root {
      --bg: #f8fafc;
      --surface: #ffffff;
      --border: #e2e8f0;
      --text: #0f172a;
      --muted: #64748b;
      --dim: #94a3b8;
      --red: #dc2626;
      --amber: #d97706;
      --green: #16a34a;
      --radius: 10px;
      --shadow: 0 1px 3px rgba(0,0,0,.07), 0 1px 2px rgba(0,0,0,.05);
      --shadow-md: 0 4px 6px -1px rgba(0,0,0,.07), 0 2px 4px -1px rgba(0,0,0,.05);
    }

    body {
      font-family: 'Inter', system-ui, sans-serif;
      font-size: 14px;
      color: var(--text);
      background: var(--bg);
      line-height: 1.6;
    }

    /* ── top bar ── */
    .topbar {
      background: #0f172a;
      color: #f8fafc;
      padding: 0 2rem;
      display: flex;
      align-items: center;
      justify-content: space-between;
      height: 56px;
      position: sticky;
      top: 0;
      z-index: 100;
      border-bottom: 1px solid #1e293b;
    }
    .topbar-brand {
      display: flex;
      align-items: center;
      gap: .5rem;
      font-weight: 700;
      font-size: 1rem;
      letter-spacing: -.01em;
    }
    .topbar-brand .logo { font-size: 1.2rem; }
    .topbar-brand .repo {
      font-weight: 400;
      color: #94a3b8;
      font-family: 'JetBrains Mono', monospace;
      font-size: .8rem;
      margin-left: .25rem;
    }
    .topbar-date { font-size: .75rem; color: #64748b; }
    .nav-links { display: flex; gap: .25rem; align-items: center; flex-wrap: wrap; }
    .nav-link {
      font-size: .75rem;
      color: #94a3b8;
      text-decoration: none;
      padding: .25rem .6rem;
      border-radius: 5px;
      transition: background .15s, color .15s;
    }
    .nav-link:hover { background: #1e293b; color: #f8fafc; }

    /* ── layout ── */
    .page { max-width: 1100px; margin: 0 auto; padding: 2rem 1.5rem 4rem; }

    /* ── hero ── */
    .hero {
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: var(--radius);
      padding: 2rem;
      margin-bottom: 1.5rem;
      box-shadow: var(--shadow);
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      flex-wrap: wrap;
      gap: 1.5rem;
    }
    .hero-left h1 { font-size: 1.4rem; font-weight: 700; letter-spacing: -.02em; margin-bottom: .25rem; }
    .hero-left p { color: var(--muted); font-size: .85rem; }
    .hero-meta { display: flex; flex-direction: column; gap: .35rem; }
    .hero-meta-row { display: flex; gap: .75rem; align-items: center; font-size: .82rem; }
    .hero-meta-row .key { color: var(--muted); min-width: 100px; }
    .hero-meta-row code { font-family: 'JetBrains Mono', monospace; font-size: .78rem; background: #f1f5f9; padding: .1rem .4rem; border-radius: 4px; }

    /* ── stat cards ── */
    .stat-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 1rem; margin-bottom: 1.5rem; }
    .stat-card {
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: var(--radius);
      padding: 1.25rem 1.5rem;
      box-shadow: var(--shadow);
      display: flex;
      align-items: center;
      gap: 1rem;
    }
    .stat-card.red   { border-left: 4px solid var(--red); }
    .stat-card.amber { border-left: 4px solid var(--amber); }
    .stat-card.green { border-left: 4px solid var(--green); }
    .stat-icon { font-size: 1.8rem; line-height: 1; }
    .stat-num  { font-size: 2rem; font-weight: 700; line-height: 1; }
    .stat-card.red   .stat-num { color: var(--red); }
    .stat-card.amber .stat-num { color: var(--amber); }
    .stat-card.green .stat-num { color: var(--green); }
    .stat-label { font-size: .78rem; color: var(--muted); margin-top: .2rem; }

    /* ── gate banner ── */
    .gate-banner {
      border-radius: var(--radius);
      padding: .9rem 1.25rem;
      margin-bottom: 1.5rem;
      display: flex;
      align-items: center;
      gap: .75rem;
      font-weight: 500;
      font-size: .9rem;
      box-shadow: var(--shadow);
    }
    .gate-pass { background: #f0fdf4; border: 1px solid #bbf7d0; color: #15803d; }
    .gate-fail { background: #fef2f2; border: 1px solid #fecaca; color: #b91c1c; }
    .gate-icon { font-size: 1.1rem; }

    /* ── sections ── */
    .section { margin-bottom: 1.5rem; }
    .section-title {
      font-size: .7rem;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: .08em;
      color: var(--muted);
      margin-bottom: .75rem;
    }

    /* ── fw summary cards ── */
    .fw-summary-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: .75rem; }
    .fw-summary-card {
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: var(--radius);
      padding: 1.1rem 1.25rem;
      box-shadow: var(--shadow);
    }
    .fw-summary-icon { font-size: 1.3rem; margin-bottom: .4rem; }
    .fw-summary-label { font-weight: 600; font-size: .85rem; margin-bottom: .5rem; }
    .fw-summary-counts { display: flex; gap: .75rem; }
    .fw-count { font-size: .82rem; font-weight: 600; }
    .fw-count.err  { color: var(--red); }
    .fw-count.warn { color: var(--amber); }
    .fw-count small { font-weight: 400; color: var(--muted); }

    /* ── framework detail sections ── */
    .fw-section {
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: var(--radius);
      box-shadow: var(--shadow);
      overflow: hidden;
    }
    details { width: 100%; }
    .fw-summary-bar {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 1rem 1.25rem;
      cursor: pointer;
      user-select: none;
      border-left: 4px solid var(--accent, #6366f1);
      list-style: none;
      transition: background .15s;
    }
    .fw-summary-bar:hover { background: #f8fafc; }
    .fw-summary-bar::-webkit-details-marker { display: none; }
    .fw-summary-left { display: flex; align-items: center; gap: .6rem; }
    .fw-icon { font-size: 1.1rem; }
    .fw-name { font-weight: 600; font-size: .95rem; }
    .fw-count-pill {
      font-size: .72rem;
      background: #f1f5f9;
      color: var(--muted);
      padding: .15rem .55rem;
      border-radius: 99px;
      font-weight: 500;
    }
    .fw-chevron { color: var(--dim); font-size: .85rem; transition: transform .2s; }
    details[open] .fw-chevron { transform: rotate(180deg); }
    .fw-controls { padding: 1rem 1.25rem; border-top: 1px solid var(--border); display: flex; flex-direction: column; gap: .75rem; }

    /* ── control cards ── */
    .control-card {
      border: 1px solid var(--border);
      border-radius: 8px;
      overflow: hidden;
    }
    .control-card.error  { border-left: 3px solid var(--red); }
    .control-card.warning { border-left: 3px solid var(--amber); }
    .control-header { padding: .9rem 1rem; background: #fafafa; }
    .control-meta { display: flex; align-items: center; gap: .5rem; margin-bottom: .4rem; }
    .control-id {
      font-family: 'JetBrains Mono', monospace;
      font-size: .78rem;
      font-weight: 600;
      background: #f1f5f9;
      padding: .15rem .45rem;
      border-radius: 4px;
    }
    .control-title { font-size: .88rem; font-weight: 600; margin-bottom: .3rem; }
    .control-desc { font-size: .8rem; color: var(--muted); line-height: 1.5; }
    .control-body { padding: .75rem 1rem; }

    /* ── level badges ── */
    .lvl-badge {
      font-size: .68rem;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: .05em;
      padding: .15rem .45rem;
      border-radius: 4px;
    }
    .lvl-error { background: #fef2f2; color: var(--red); }
    .lvl-warn  { background: #fffbeb; color: var(--amber); }

    /* ── severity pills ── */
    .pill {
      display: inline-flex; align-items: center; gap: .25rem;
      font-size: .75rem; font-weight: 600;
      padding: .2rem .6rem; border-radius: 99px;
    }
    .pill-red   { background: #fef2f2; color: var(--red); }
    .pill-amber { background: #fffbeb; color: var(--amber); }
    .pill-green { background: #f0fdf4; color: var(--green); }

    /* ── sink badges ── */
    .sink-badge {
      font-size: .72rem; font-weight: 500;
      padding: .15rem .5rem; border-radius: 5px;
      background: #f1f5f9; color: #475569;
      white-space: nowrap;
    }
    .sink-badge.sink-sideeffectfuls { background: #fff1f2; color: #be123c; }
    .sink-badge.sink-userfacings { background: #eff6ff; color: #1d4ed8; }

    /* ── tables ── */
    .inner-table, .surfaces-table {
      width: 100%;
      border-collapse: collapse;
      font-size: .8rem;
    }
    .inner-table th, .surfaces-table th {
      text-align: left;
      padding: .45rem .75rem;
      background: #f8fafc;
      border-bottom: 1px solid var(--border);
      font-weight: 600;
      font-size: .72rem;
      text-transform: uppercase;
      letter-spacing: .04em;
      color: var(--muted);
      white-space: nowrap;
    }
    .inner-table td, .surfaces-table td {
      padding: .5rem .75rem;
      border-bottom: 1px solid #f1f5f9;
      vertical-align: middle;
    }
    .inner-table tr:last-child td,
    .surfaces-table tr:last-child td { border-bottom: none; }

    /* ── code ── */
    .filepath {
      font-family: 'JetBrains Mono', monospace;
      font-size: .75rem;
      background: #f1f5f9;
      padding: .15rem .4rem;
      border-radius: 4px;
      color: #334155;
      word-break: break-all;
    }

    /* ── side effect tags ── */
    .se-tags { display: flex; flex-wrap: wrap; gap: .25rem; }
    .se-tag {
      font-size: .68rem; background: #fdf4ff; color: #7e22ce;
      padding: .1rem .4rem; border-radius: 4px; font-weight: 500;
    }

    /* ── provider tag ── */
    .provider-tag {
      font-size: .72rem; background: #f0fdf4; color: #15803d;
      padding: .1rem .4rem; border-radius: 4px; font-weight: 500;
    }

    /* ── tick marks ── */
    .tick { font-weight: 700; }
    .tick.yes { color: var(--green); }
    .tick.no  { color: var(--red); }
    .tick.na  { color: var(--dim); }
    .tc { text-align: center; }

    /* ── surfaces card ── */
    .surfaces-card {
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: var(--radius);
      box-shadow: var(--shadow);
      overflow: hidden;
    }
    .surfaces-card-header {
      padding: 1rem 1.25rem;
      border-bottom: 1px solid var(--border);
      display: flex;
      align-items: center;
      justify-content: space-between;
    }
    .surfaces-card-header h2 { font-size: .95rem; font-weight: 600; }
    .surfaces-wrap { overflow-x: auto; }

    /* ── empty state ── */
    .empty-state { color: var(--muted); font-size: .85rem; padding: .5rem 0; }

    /* ── misc ── */
    .dim { color: var(--dim); }
    .footer {
      text-align: center;
      margin-top: 2.5rem;
      font-size: .78rem;
      color: var(--dim);
    }
    .footer a { color: #6366f1; text-decoration: none; }
    .footer a:hover { text-decoration: underline; }

    @media (max-width: 700px) {
      .stat-grid { grid-template-columns: 1fr 1fr; }
      .hero { flex-direction: column; }
      .topbar { height: auto; flex-wrap: wrap; padding: .75rem 1rem; gap: .5rem; }
      .page { padding: 1rem .75rem 3rem; }
    }
  </style>
</head>
<body>

  <!-- top bar -->
  <header class="topbar">
    <div class="topbar-brand">
      <span class="logo">🔍</span>
      <span>aiglare</span>
      <span class="repo">${esc(report.repo)}</span>
    </div>
    <nav class="nav-links">
      ${fwNav}
      <a href="#all-surfaces" class="nav-link">📄 Surfaces</a>
    </nav>
    <span class="topbar-date">${date}</span>
  </header>

  <div class="page">

    <!-- hero -->
    <div class="hero">
      <div class="hero-left">
        <h1>AI Governance Audit Report</h1>
        <p>Surfaces where model output reaches users or side-effects without guardrails</p>
      </div>
      <div class="hero-meta">
        <div class="hero-meta-row"><span class="key">Repository</span><code>${esc(report.repo)}</code></div>
        <div class="hero-meta-row"><span class="key">Generated</span><span>${date}</span></div>
        <div class="hero-meta-row"><span class="key">AI surfaces</span><span>${report.surfaceCount}</span></div>
        ${report.acceleratedBy ? `<div class="hero-meta-row"><span class="key">Accelerated by</span><span>${esc(report.acceleratedBy)}</span></div>` : ''}
        ${hasCompliance ? `<div class="hero-meta-row"><span class="key">Frameworks</span><span>${report.compliance.frameworks.map(f => esc(FRAMEWORKS[f] ?? f)).join(', ')}</span></div>` : ''}
      </div>
    </div>

    <!-- gate banner -->
    ${gateBanner}

    <!-- stat cards -->
    <div class="stat-grid">
      <div class="stat-card red">
        <div class="stat-icon">🔴</div>
        <div><div class="stat-num">${sm.red}</div><div class="stat-label">Red — review now</div></div>
      </div>
      <div class="stat-card amber">
        <div class="stat-icon">🟡</div>
        <div><div class="stat-num">${sm.amber}</div><div class="stat-label">Amber — partial coverage</div></div>
      </div>
      <div class="stat-card green">
        <div class="stat-icon">🟢</div>
        <div><div class="stat-num">${sm.green}</div><div class="stat-label">Green — guardrails present</div></div>
      </div>
    </div>

    <!-- compliance overview -->
    ${complianceSummarySection}

    <!-- per-framework sections -->
    ${frameworkSections}

    <!-- all surfaces -->
    <section class="section" id="all-surfaces">
      <h2 class="section-title">All AI Surfaces</h2>
      <div class="surfaces-card">
        <div class="surfaces-card-header">
          <h2>Surfaces (${report.surfaceCount})</h2>
          <span style="font-size:.75rem;color:var(--muted)">Conf. = Confidence · Fall. = Fallback · Valid. = Validation · HITL = Human-in-loop · Err. = Error isolation</span>
        </div>
        <div class="surfaces-wrap">
          <table class="surfaces-table">
            <thead>
              <tr>
                <th>Severity</th><th>File</th><th>Provider</th><th>Sink</th><th>Side Effects</th>
                <th title="Confidence handling">Conf.</th>
                <th title="Fallback path">Fall.</th>
                <th title="Output validation">Valid.</th>
                <th title="Human-in-the-loop">HITL</th>
                <th title="Error isolation">Err.</th>
              </tr>
            </thead>
            <tbody>${surfaceRows}</tbody>
          </table>
        </div>
      </div>
    </section>

    <div class="footer">
      Generated by <a href="https://github.com/nugehs/aiglare">aiglare</a> · AI governance guardrail linter
    </div>

  </div>
</body>
</html>`;
}
