import fs from 'node:fs';
import path from 'node:path';
import { findProviderByPackage } from '../providers.js';

// Optional accelerator. Reads a real repoctx index (.dev-context/index.json),
// whose per-file records look like:
//   { path, kind, domain, domains[], httpMethods[], imports[], exports[], symbols[] }
// We use this to (a) find AI surfaces directly from imports[] without parsing,
// (b) classify sinks more reliably (httpMethods[] => user-facing; kind/domains),
// and (c) prioritize files for the native deep-scan that adds guardrail signals.

const AI_DOMAIN_RX = /^(ai|llm|genai|open-?ai|anthropic|cloudflare-ai|recommendations?|mascot|generate|conversational)$/i;
const USER_FACING_KINDS = new Set(['controller', 'route', 'apiRoute', 'component']);
const SIDE_EFFECT_DOMAINS = new Set(['payment', 'paystack', 'booking', 'vendor-booking', 'service-booking', 'email', 'sms', 'notifications']);

export function findRepoctxIndex(root) {
  const p = path.join(root, '.dev-context', 'index.json');
  return fs.existsSync(p) ? p : null;
}

export function loadRepoctxHints(indexPath, root) {
  let idx;
  try { idx = JSON.parse(fs.readFileSync(indexPath, 'utf8')); } catch { return null; }

  // The index stores files under a `files` array. Current repoctx nests the
  // catalog under `map.files`; older/defensive shapes use top-level `files` or
  // `entries`.
  const files =
    idx.files || idx.entries || (idx.map && idx.map.files) || [];
  const hints = new Map();      // absPath -> hint record
  const candidates = new Set(); // absPath of likely AI surfaces

  for (const f of files) {
    const rel = f.path || f.file || f.relPath;
    if (!rel) continue;
    const abs = path.isAbsolute(rel) ? rel : path.join(root, rel);
    const domains = f.domains || (f.domain ? [f.domain] : []);
    const imports = f.imports || [];
    const httpMethods = f.httpMethods || [];

    // provider detection straight from the index imports[]
    const importedProvider = imports.map(findProviderByPackage).find(Boolean) || null;
    const aiCandidate =
      Boolean(importedProvider) ||
      domains.some(d => AI_DOMAIN_RX.test(d)) ||
      AI_DOMAIN_RX.test(path.basename(path.dirname(abs)));

    hints.set(abs, {
      kind: f.kind || null,
      domains,
      httpMethods,
      imports,
      exports: f.exports || [],
      provider: importedProvider,
      hasDisclaimerExport: (f.exports || []).some(e => /disclaimer/i.test(e)),
      aiCandidate,
    });
    if (aiCandidate) candidates.add(abs);
  }
  return { hints, candidates, version: idx.version ?? 'unknown', fileCount: files.length };
}

// Sharpen a native-scanner result using index facts the single-file scan can't see.
export function refineWithHints(result, hints) {
  if (!hints) return result;
  const h = hints.get(result.file_abs || result.file);
  if (!h) return result;

  let sink = result.sink;
  let refinedBy = null;

  // httpMethods[] is repoctx telling us this is an HTTP surface => user-facing
  if (h.httpMethods.length && sink === 'internal') { sink = 'user-facing'; refinedBy = 'repoctx-httpMethods'; }
  // a controller/route/component kind => user-facing
  else if (sink === 'internal' && h.kind && USER_FACING_KINDS.has(h.kind)) { sink = 'user-facing'; refinedBy = 'repoctx-kind'; }
  // membership in a side-effect domain promotes internal -> side-effectful
  if (sink !== 'side-effectful' && h.domains.some(d => SIDE_EFFECT_DOMAINS.has(d))) {
    sink = 'side-effectful'; refinedBy = 'repoctx-domain';
  }

  let guardrails = result.guardrails;
  // If the index promoted this to a side-effect, the human-in-loop guardrail
  // (which the native scan skips as 'n/a' for non-side-effect sinks) now
  // applies — re-apply the raw signal so a genuinely-guarded surface isn't
  // falsely scored red on the repoctx-accelerated path.
  if (sink === 'side-effectful' && guardrails.humanInLoop === 'n/a') {
    guardrails = { ...guardrails, humanInLoop: result._humanInLoopSignal === true };
  }
  // credit an existing disclaimer control surfaced by the index
  if (h.hasDisclaimerExport) guardrails = { ...guardrails, disclaimer: true };

  const out = { ...result, sink, guardrails };
  if (refinedBy) out._refinedBy = refinedBy;
  // prefer the index's provider label if the scanner came up unknown
  if (result.provider === 'unknown' && h.provider) {
    out.provider = h.provider.id; out.providerLabel = h.provider.label;
  }
  return out;
}
