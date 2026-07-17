// Tool definitions for the ScreenshotInk MCP server (stdio package).
// Every tool calls the ScreenshotInk REST API with your own key — quota,
// 24h caching and rate limits are enforced there. Pure-JS dependencies only
// (no native modules), so `npx @screenshotink/mcp` works everywhere.

'use strict';

const { McpServer } = require('@modelcontextprotocol/sdk/server/mcp.js');
const { z } = require('zod');
const pixelmatch = require('pixelmatch');
const { PNG } = require('pngjs');

const SITE = (process.env.SCREENSHOTINK_API_BASE || 'https://screenshotink.com').replace(/\/$/, '');

/* ---------------------------------------------------------------- helpers */

class ApiError extends Error {}

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

/**
 * POST /v1/capture. Per-key rate limits (free plan = 1 req/s) are retried
 * politely so parallel fan-out degrades to sequential, not to errors.
 */
async function siteCapture(key, params) {
  for (let attempt = 1; ; attempt++) {
    const res = await fetch(SITE + '/v1/capture', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Authorization: 'Bearer ' + key },
      body: JSON.stringify(params),
      signal: AbortSignal.timeout(120_000),
    });
    const data = await res.json().catch(() => null);
    // Retry only transient per-second rate limits; a quota_exceeded 429 won't
    // clear by retrying, so fail fast instead of eating 6 round-trips.
    if (res.status === 429 && data?.error?.code === 'rate_limited' && attempt < 6) {
      const retryAfter = Number(res.headers.get('retry-after')) || 1;
      await sleep(retryAfter * 1000 + 150 + Math.floor(Math.random() * 250));
      continue;
    }
    if (!res.ok || !data || data.error) {
      const e = (data && data.error) || { code: 'http_' + res.status, message: 'Capture API returned HTTP ' + res.status + '.' };
      throw new ApiError(`${e.code}: ${e.message}`);
    }
    return data; // { image_url, width, height, format, bytes, render_ms, cached, expires_at }
  }
}

async function siteGet(key, path, params) {
  const qs = new URLSearchParams(params).toString();
  const res = await fetch(`${SITE}${path}?${qs}`, {
    headers: { Authorization: 'Bearer ' + key },
    signal: AbortSignal.timeout(120_000),
  });
  const data = await res.json().catch(() => null);
  if (!res.ok || !data || data.error) {
    const e = (data && data.error) || { code: 'http_' + res.status, message: `API returned HTTP ${res.status}.` };
    throw new ApiError(`${e.code}: ${e.message}`);
  }
  return data;
}

async function fetchBytes(url, cap = 40 * 1024 * 1024) {
  const res = await fetch(url, { signal: AbortSignal.timeout(60_000) });
  if (!res.ok) throw new ApiError(`Could not fetch stored capture (HTTP ${res.status}).`);
  const buf = Buffer.from(await res.arrayBuffer());
  if (buf.length > cap) throw new ApiError('Stored capture is too large to process.');
  return buf;
}

/**
 * Inline image content block when the file is small enough to embed sanely;
 * otherwise null (the hosted URL in the text block is always the source of
 * truth). No native image libs here, so no downscaling — the hosted API
 * `width`/`scaled_width` params control output size instead.
 */
function inlineIfSmall(buf, format, maxBytes) {
  if (buf.length > maxBytes) return null;
  return {
    type: 'image',
    data: buf.toString('base64'),
    mimeType: format === 'jpeg' ? 'image/jpeg' : 'image/png',
  };
}

/** Tiny promise pool — keeps us politely under per-key rate limits. */
async function mapPool(items, n, fn) {
  const out = new Array(items.length);
  let next = 0;
  await Promise.all(Array.from({ length: Math.min(n, items.length) }, async () => {
    while (next < items.length) {
      const i = next++;
      out[i] = await fn(items[i], i).then(value => ({ ok: true, value }), err => ({ ok: false, error: err.message }));
    }
  }));
  return out;
}

function err(message) {
  return { content: [{ type: 'text', text: message }], isError: true };
}

const fmt = z.enum(['png', 'jpeg', 'pdf']).optional().describe('Output format (default png)');
const INLINE_MAX = 800 * 1024;  // single screenshot embed cap
const THUMB_MAX = 350 * 1024;   // per-thumbnail embed cap in multi-capture tools

/* ----------------------------------------------------------------- server */

function buildServer(key) {
  const server = new McpServer({ name: 'screenshotink', version: '1.0.3' });

  /* ---------- take_screenshot ---------- */
  server.registerTool('take_screenshot', {
    title: 'Take screenshot',
    annotations: { readOnlyHint: true, openWorldHint: true },
    description: 'Capture a full-page or above-the-fold screenshot of any public URL as PNG, JPEG or PDF. Use it to verify a deploy, inspect a layout, read a page you otherwise cannot see, or grab visual evidence. Returns the image inline (when small enough to embed) so you can reason about the rendered pixels in the same turn, plus a hosted full-resolution link. Counts 1 capture against your plan quota; identical requests within 24h are cached free.',
    inputSchema: {
      url: z.string().url().describe('Absolute http(s) URL to capture'),
      width: z.number().int().min(320).max(3840).optional().describe('Viewport width in px (default 1440)'),
      full_size: z.boolean().optional().describe('Capture the full scrollable page, not just the viewport'),
      format: fmt,
      no_ads: z.boolean().optional().describe('Block ads'),
      no_cookie_banners: z.boolean().optional().describe('Auto-dismiss cookie consent banners'),
      lazy_load: z.boolean().optional().describe('Scroll the page first so lazy-loaded content renders'),
      dark_mode: z.boolean().optional().describe('Emulate prefers-color-scheme: dark'),
      delay_ms: z.number().int().min(0).max(10000).optional().describe('Extra wait after load, in ms'),
      fresh: z.boolean().optional().describe('Bypass the 24h cache and force a new capture'),
    },
  }, async (a) => {
    try {
      const cap = await siteCapture(key, {
        url: a.url, width: a.width, full_size: a.full_size, format: a.format,
        no_ads: a.no_ads, no_cookie_banners: a.no_cookie_banners, lazy_load: a.lazy_load,
        dark_mode: a.dark_mode, sleep_time: a.delay_ms, nocache: a.fresh,
        // keep embeds context-friendly without native downscaling
        scaled_width: a.full_size && !a.format ? Math.min(a.width || 1440, 1024) : undefined,
      });
      const meta = `Captured ${a.url}\n` +
        `Image: ${cap.image_url}\n` +
        (cap.format === 'pdf' ? `Format: pdf · ${cap.bytes} bytes` :
          `Size: ${cap.width}×${cap.height} ${cap.format} · ${cap.bytes} bytes`) +
        ` · render ${cap.render_ms}ms${cap.cached ? ' · served from 24h cache (free)' : ''}` +
        (cap.expires_at ? `\nStored until ${cap.expires_at}` : '');
      if (cap.format === 'pdf') return { content: [{ type: 'text', text: meta }] };
      const img = inlineIfSmall(await fetchBytes(cap.image_url), cap.format, INLINE_MAX);
      return { content: img
        ? [img, { type: 'text', text: meta }]
        : [{ type: 'text', text: meta + '\n(image too large to embed inline — open the URL above)' }] };
    } catch (e) { return err(e.message); }
  });

  /* ---------- bulk_screenshots ---------- */
  server.registerTool('bulk_screenshots', {
    title: 'Bulk screenshots',
    annotations: { readOnlyHint: true, openWorldHint: true },
    description: 'Screenshot up to 20 URLs in a single call. Use it to audit a whole funnel, a set of landing pages, or a competitor set at once instead of looping take_screenshot. Returns a hosted link for every page plus inline thumbnails so you can scan them in the same turn. Each capture counts 1 against your quota (24h cache hits are free).',
    inputSchema: {
      urls: z.array(z.string().url()).min(1).max(20).describe('Up to 20 absolute http(s) URLs'),
      width: z.number().int().min(320).max(3840).optional(),
      full_size: z.boolean().optional(),
      format: fmt,
    },
  }, async (a) => {
    const results = await mapPool(a.urls, 2, (url) =>
      siteCapture(key, { url, width: a.width, full_size: a.full_size, format: a.format }));
    const lines = results.map((r, i) => r.ok
      ? `✓ ${a.urls[i]}\n   ${r.value.image_url} (${r.value.format}${r.value.cached ? ', cached' : ''}, ${r.value.render_ms}ms)`
      : `✕ ${a.urls[i]}\n   failed: ${r.error}`);
    const okCount = results.filter(r => r.ok).length;

    const content = [];
    let thumbs = 0;
    for (let i = 0; i < results.length && thumbs < 4; i++) {
      if (!results[i].ok || results[i].value.format === 'pdf') continue;
      try {
        const img = inlineIfSmall(await fetchBytes(results[i].value.image_url), results[i].value.format, THUMB_MAX);
        if (img) { content.push(img); thumbs++; }
      } catch { /* best-effort */ }
    }
    content.push({ type: 'text', text: `${okCount}/${a.urls.length} captured.\n\n${lines.join('\n')}` +
      (thumbs ? `\n\n(first ${thumbs} embedded inline — full set at the URLs)` : '') });
    return { content, isError: okCount === 0 };
  });

  /* ---------- compare_screenshots ---------- */
  server.registerTool('compare_screenshots', {
    title: 'Compare screenshots',
    annotations: { readOnlyHint: true, openWorldHint: true },
    description: 'Pixel-diff two URLs (or fresh captures of them) and report exactly what changed — ideal for staging vs production, or before vs after a change. Returns the percentage of pixels that differ plus a diff image with the changed regions highlighted in orange, inline, so you can judge the change immediately. Bills 2 captures; pages are captured fresh by default so the comparison reflects the live pages.',
    inputSchema: {
      url_a: z.string().url().describe('First URL (e.g. production)'),
      url_b: z.string().url().describe('Second URL (e.g. staging)'),
      threshold: z.number().min(0).max(1).optional().describe('Per-pixel color tolerance 0–1 (default 0.1; higher = less sensitive)'),
      width: z.number().int().min(320).max(1920).optional().describe('Viewport width for both captures (default 1280)'),
      full_size: z.boolean().optional().describe('Compare full pages instead of viewports'),
      fresh: z.boolean().optional().describe('Bypass the 24h cache (default true for comparisons)'),
    },
  }, async (a) => {
    try {
      const width = a.width || 1280;
      const params = { width, full_size: a.full_size, format: 'png', nocache: a.fresh !== false };
      const [capA, capB] = await Promise.all([
        siteCapture(key, { url: a.url_a, ...params }),
        siteCapture(key, { url: a.url_b, ...params }),
      ]);
      const [pngA, pngB] = await Promise.all([
        fetchBytes(capA.image_url).then(b => PNG.sync.read(b)),
        fetchBytes(capB.image_url).then(b => PNG.sync.read(b)),
      ]);

      // Same width param → same pixel width; pad the shorter page with the
      // brand background so added/removed content reads as a difference.
      const W = Math.min(pngA.width, pngB.width);
      const MAXH = 8000;
      const H = Math.min(MAXH, Math.max(pngA.height, pngB.height));
      const pad = (png) => {
        const out = Buffer.alloc(W * H * 4);
        for (let i = 0; i < out.length; i += 4) { out[i] = 13; out[i + 1] = 13; out[i + 2] = 22; out[i + 3] = 255; } // #0D0D16
        const rows = Math.min(png.height, H);
        for (let y = 0; y < rows; y++) {
          png.data.copy(out, y * W * 4, y * png.width * 4, y * png.width * 4 + W * 4);
        }
        return out;
      };
      const [rawA, rawB] = [pad(pngA), pad(pngB)];

      const diff = new PNG({ width: W, height: H });
      const changed = pixelmatch(rawA, rawB, diff.data, W, H, {
        threshold: a.threshold ?? 0.1,
        diffColor: [255, 178, 36],
        diffColorAlt: [255, 120, 36],
        alpha: 0.25,
      });
      const pct = (changed / (W * H)) * 100;
      const diffBuf = PNG.sync.write(diff);
      const img = inlineIfSmall(diffBuf, 'png', 2 * INLINE_MAX);

      const truncated = pngA.height > MAXH || pngB.height > MAXH;
      const text =
        `Diff: ${pct.toFixed(2)}% of pixels differ (${changed.toLocaleString()} px, threshold ${a.threshold ?? 0.1})\n` +
        `A: ${a.url_a}\n   ${capA.image_url}\n` +
        `B: ${a.url_b}\n   ${capB.image_url}\n` +
        `Changed regions are highlighted in warm orange${img ? ' in the diff image above' : ''}.` +
        (truncated ? '\nNote: pages compared down to the first 8000px.' : '') +
        (img ? '' : '\n(diff image too large to embed — compare the two URLs above)');
      return { content: img ? [img, { type: 'text', text }] : [{ type: 'text', text }] };
    } catch (e) { return err(e.message); }
  });

  /* ---------- run_lighthouse ---------- */
  server.registerTool('run_lighthouse', {
    title: 'Run Lighthouse',
    annotations: { readOnlyHint: true, openWorldHint: true },
    description: 'Run a Google Lighthouse audit on a URL and get performance, accessibility, best-practices and SEO scores plus Core Web Vitals. Use it when you need real scores AND the rendered page to explain why a page is slow or failing, not just a number. Returns the scores alongside a screenshot of the audited page. Counts 1 capture against your quota.',
    inputSchema: {
      url: z.string().url().describe('Absolute http(s) URL to audit'),
      strategy: z.enum(['desktop', 'mobile']).optional().describe('Audit profile (default desktop)'),
    },
  }, async (a) => {
    try {
      const r = await siteGet(key, '/v1/lighthouse', { url: a.url, strategy: a.strategy || 'desktop' });
      const s = r.scores || {};
      const m = r.metrics || {};
      const line = (label, v) => `${label}: ${v === null || v === undefined ? '—' : v}`;
      const text =
        `Lighthouse (${a.strategy || 'desktop'}) — ${a.url}\n\n` +
        `Scores (0–100):\n` +
        `  ${line('Performance     ', s.performance)}\n` +
        `  ${line('Accessibility   ', s.accessibility)}\n` +
        `  ${line('Best practices  ', s.best_practices)}\n` +
        `  ${line('SEO             ', s.seo)}\n` +
        (Object.keys(m).length ? `\nCore metrics:\n` +
          Object.entries(m).map(([k, v]) => `  ${k.toUpperCase()}: ${v}`).join('\n') : '');
      return { content: [{ type: 'text', text }] };
    } catch (e) { return err(e.message); }
  });

  /* ---------- capture_sitemap ---------- */
  server.registerTool('capture_sitemap', {
    title: 'Capture sitemap',
    annotations: { readOnlyHint: true, openWorldHint: true },
    description: 'Read a sitemap.xml and screenshot every page it lists (up to the limit). Use it to inventory, archive, or visually QA a whole site in one pass instead of capturing pages one by one. Returns a hosted capture for each page plus inline thumbnails. Each page counts 1 against your quota.',
    inputSchema: {
      sitemap_url: z.string().url().describe('URL of the sitemap.xml (sitemap indexes are followed one level)'),
      limit: z.number().int().min(1).max(25).optional().describe('Max pages to capture (default 10, max 25)'),
      width: z.number().int().min(320).max(3840).optional(),
      format: fmt,
    },
  }, async (a) => {
    try {
      const limit = a.limit ?? 10;
      const sm = await siteGet(key, '/v1/sitemap', { url: a.sitemap_url, limit });
      const urls = sm.urls || [];
      if (!urls.length) return err('No URLs found in that sitemap.');

      const results = await mapPool(urls, 2, (url) =>
        siteCapture(key, { url, width: a.width, format: a.format }));
      const lines = results.map((r, i) => r.ok
        ? `✓ ${urls[i]}\n   ${r.value.image_url}${r.value.cached ? ' (cached)' : ''}`
        : `✕ ${urls[i]}\n   failed: ${r.error}`);
      const okCount = results.filter(r => r.ok).length;

      const content = [];
      let thumbs = 0;
      for (let i = 0; i < results.length && thumbs < 4; i++) {
        if (!results[i].ok || results[i].value.format === 'pdf') continue;
        try {
          const img = inlineIfSmall(await fetchBytes(results[i].value.image_url), results[i].value.format, THUMB_MAX);
          if (img) { content.push(img); thumbs++; }
        } catch { /* best-effort */ }
      }
      content.push({ type: 'text', text:
        `Sitemap listed ${sm.count ?? urls.length} URL(s); captured ${okCount}/${urls.length} (limit ${limit}).\n\n${lines.join('\n')}` +
        (thumbs ? `\n\n(first ${thumbs} embedded inline — full set at the URLs)` : '') });
      return { content, isError: okCount === 0 };
    } catch (e) { return err(e.message); }
  });

  return server;
}

module.exports = { buildServer };
