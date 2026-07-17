import fs from 'node:fs';
import path from 'node:path';

/**
 * Universal server adapter: ingest any OpenAPI 2/3 document and emit the same
 * Route[] shape as a native parser. One adapter covers every backend that can
 * produce a spec — Express+swagger-jsdoc, NestJS, FastAPI, Spring springdoc,
 * .NET Swashbuckle, hand-written specs, etc.
 *
 * Config (server block):
 *   {
 *     "adapter": "openapi",
 *     "repo": "../my-api",
 *     "spec": "openapi.json" | "http://localhost:9999/doc-json",
 *     "stripPrefix": "api/v1"   // optional; removed from every path
 *   }
 */
const VERBS = ['get', 'post', 'put', 'patch', 'delete', 'options', 'head'];

export async function extractOpenapi(cfg) {
  const { spec, source } = await loadSpec(cfg);

  // OpenAPI 3 server path, or Swagger 2 basePath, may carry a prefix too.
  const serverPrefix = serverBasePath(spec);
  const strip = trim(cfg.stripPrefix || cfg.globalPrefix || '');

  const routes = [];
  const paths = spec.paths || {};
  for (const [rawPath, item] of Object.entries(paths)) {
    if (!item || typeof item !== 'object') continue;
    for (const verb of VERBS) {
      const op = item[verb];
      if (!op) continue;
      routes.push({
        side: 'server',
        method: verb.toUpperCase(),
        rawPath: stripPrefixes(rawPath, [strip, serverPrefix]),
        operationId: op.operationId,
        file: source,
        line: 0,
      });
    }
  }
  return routes;
}

function stripPrefixes(p, prefixes) {
  let out = trim(p);
  for (const pre of prefixes) {
    const t = trim(pre);
    if (t && (out === t || out.startsWith(t + '/'))) {
      out = trim(out.slice(t.length));
    }
  }
  return out;
}

const trim = (s) => String(s ?? '').replace(/^\/+/, '').replace(/\/+$/, '');

// Derive a path prefix from servers[].url (OpenAPI 3) or basePath (Swagger 2).
function serverBasePath(spec) {
  if (typeof spec.basePath === 'string') return spec.basePath; // Swagger 2
  const url = spec.servers && spec.servers[0] && spec.servers[0].url;
  if (!url) return '';
  try {
    // Relative server url ("/api/v1") or absolute ("http://host/api/v1").
    return /^https?:\/\//.test(url) ? new URL(url).pathname : url;
  } catch {
    return '';
  }
}

async function loadSpec(cfg) {
  const src = cfg.spec;
  if (!src) throw new Error("openapi adapter requires server.spec (file path or url)");

  let text;
  let source;
  if (/^https?:\/\//.test(src)) {
    const res = await fetch(src);
    if (!res.ok) throw new Error(`failed to fetch spec (${res.status}): ${src}`);
    text = await res.text();
    source = src;
  } else {
    source = path.isAbsolute(src) ? src : path.resolve(cfg.repoRoot, src);
    text = fs.readFileSync(source, 'utf8');
  }
  return { spec: await parseSpec(text, source), source };
}

async function parseSpec(text, source) {
  if (text.trimStart().startsWith('{')) return JSON.parse(text);
  // YAML: best-effort via a parser installed in the host project.
  for (const mod of ['yaml', 'js-yaml']) {
    try {
      const y = await import(mod);
      const fn = y.parse || y.load || (y.default && (y.default.parse || y.default.load));
      if (fn) return fn(text);
    } catch {
      /* try next */
    }
  }
  throw new Error(
    `spec at ${source} appears to be YAML. Install 'yaml' or 'js-yaml', or point tieline at a JSON spec.`,
  );
}
