import fs from 'node:fs';
import path from 'node:path';

const C = {
  reset: '\x1b[0m',
  bold: '\x1b[1m',
  dim: '\x1b[2m',
  green: '\x1b[32m',
  yellow: '\x1b[33m',
  cyan: '\x1b[36m',
};
const on = process.stdout.isTTY && !process.env.NO_COLOR;
const c = (k, s) => (on ? C[k] + s + C.reset : s);

// Dir-name biases: a dir called "web" is probably the client, "api" the server.
const CLIENT_NAMES = /(web|frontend|front-end|client|ui|www|dashboard|admin)/i;
const SERVER_NAMES = /(api|server|backend|back-end|service|svc|gateway)/i;

/**
 * Generate a tieline.config.json by sniffing nearby repos.
 *
 * Scans cwd, its children, and its siblings for known stacks (package.json
 * deps, requirements.txt / pyproject.toml, pom.xml / build.gradle, OpenAPI
 * docs), picks the best client + server, and writes a ready-to-run config.
 * Always overwrites an existing config.
 */
export function runInit({ cwd = process.cwd(), out = 'tieline.config.json', quiet = false } = {}) {
  const target = path.resolve(cwd, out);
  const existed = fs.existsSync(target);

  const { client, server } = detect(cwd);
  const config = buildConfig(cwd, client, server);

  fs.writeFileSync(target, JSON.stringify(config, null, 2) + '\n');

  // `quiet` keeps stdout clean for the MCP server's JSON-RPC stream.
  if (!quiet) print(cwd, client, server, target, existed);
  return { config, client, server, path: target, existed };
}

/** Find the best client + server candidate among nearby directories. */
export function detect(cwd) {
  const matches = [];
  for (const { dir, proximity } of candidateDirs(cwd)) {
    for (const m of classify(dir)) {
      matches.push({ ...m, dir, proximity, score: score(m, dir, proximity) });
    }
  }
  const best = (side) =>
    matches
      .filter((m) => m.side === side)
      .sort((a, b) => b.score - a.score || a.dir.localeCompare(b.dir))[0] || null;

  return { client: best('client'), server: best('server') };
}

// cwd, then its children, then its siblings (children of the parent). Deduped
// by resolved path; proximity ranks closer dirs higher when names tie.
function candidateDirs(cwd) {
  const seen = new Set();
  const out = [];
  const add = (dir, proximity) => {
    let real;
    try {
      real = fs.realpathSync(dir);
    } catch {
      return;
    }
    if (seen.has(real)) return;
    seen.add(real);
    out.push({ dir, proximity });
  };

  add(cwd, 2);
  for (const child of subdirs(cwd)) add(child, 2);
  const parent = path.dirname(cwd);
  if (parent !== cwd) for (const sib of subdirs(parent)) add(sib, 1);
  return out;
}

function subdirs(dir) {
  try {
    return fs
      .readdirSync(dir, { withFileTypes: true })
      .filter((e) => e.isDirectory() && !e.name.startsWith('.') && e.name !== 'node_modules')
      .map((e) => path.join(dir, e.name));
  } catch {
    return [];
  }
}

// A directory may yield both a client and a server match (e.g. a full-stack
// Next app). Returns [{ side, adapter }, …].
function classify(dir) {
  const out = [];
  const pkg = readJson(path.join(dir, 'package.json'));
  if (pkg) {
    const deps = { ...pkg.dependencies, ...pkg.devDependencies, ...pkg.peerDependencies };
    const has = (n) => deps[n] != null;

    if (has('@nestjs/core')) out.push({ side: 'server', adapter: 'nestjs' });
    else if (has('fastify')) out.push({ side: 'server', adapter: 'fastify' });
    else if (has('express')) out.push({ side: 'server', adapter: 'express' });
    if (has('next') && !out.some((m) => m.side === 'server')) out.push({ side: 'server', adapter: 'next' });

    if (has('@reduxjs/toolkit')) out.push({ side: 'client', adapter: 'rtk-query' });
    else if (has('@angular/common') || has('@angular/core')) out.push({ side: 'client', adapter: 'angular-http' });
    else if (has('axios') || has('@tanstack/react-query') || has('swr')) out.push({ side: 'client', adapter: 'axios-fetch' });
  }

  // Python: requirements.txt / pyproject.toml mentions.
  const py = readText(path.join(dir, 'requirements.txt')) + readText(path.join(dir, 'pyproject.toml'));
  if (/\bfastapi\b/i.test(py)) out.push({ side: 'server', adapter: 'fastapi' });
  else if (/\bflask\b/i.test(py)) out.push({ side: 'server', adapter: 'flask' });

  // JVM: Spring on the classpath.
  const jvm = readText(path.join(dir, 'pom.xml')) + readText(path.join(dir, 'build.gradle')) + readText(path.join(dir, 'build.gradle.kts'));
  if (/springframework|spring-boot/i.test(jvm)) out.push({ side: 'server', adapter: 'spring' });

  // OpenAPI doc — only a fallback server when nothing native was found.
  if (!out.some((m) => m.side === 'server')) {
    const spec = ['openapi.json', 'openapi.yaml', 'openapi.yml', 'swagger.json', 'swagger.yaml'].find((f) =>
      fs.existsSync(path.join(dir, f)),
    );
    if (spec) out.push({ side: 'server', adapter: 'openapi', spec });
  }

  return out;
}

function score(m, dir, proximity) {
  const base = dir.endsWith(path.sep + 'node_modules') ? -100 : 1;
  const name = path.basename(dir);
  const wanted = m.side === 'client' ? CLIENT_NAMES : SERVER_NAMES;
  const other = m.side === 'client' ? SERVER_NAMES : CLIENT_NAMES;
  let bias = 0;
  if (wanted.test(name)) bias += 3;
  if (other.test(name)) bias -= 2;
  return base + bias + proximity;
}

function buildConfig(cwd, client, server) {
  const clientBlock = client
    ? { adapter: client.adapter, repo: relRepo(cwd, client.dir), roots: clientRoots(client.dir, client.adapter), basePath: '' }
    : { adapter: 'rtk-query', repo: '../web', roots: ['src/redux/apis'], basePath: '/api/v1' };

  const serverBlock = server
    ? { adapter: server.adapter, repo: relRepo(cwd, server.dir), roots: serverRoots(server.dir, server.adapter), globalPrefix: '' }
    : { adapter: 'nestjs', repo: '../api', roots: ['src'], globalPrefix: 'api/v1' };

  if (server?.spec) serverBlock.spec = server.spec;

  return { client: clientBlock, server: serverBlock, ignore: [], failOn: ['drift'] };
}

// Path from the config dir to the repo, in forward slashes. cwd itself → ".".
function relRepo(cwd, dir) {
  const rel = path.relative(cwd, dir).split(path.sep).join('/');
  return rel === '' ? '.' : rel;
}

function clientRoots(dir, adapter) {
  const candidates =
    adapter === 'rtk-query'
      ? ['src/redux/apis', 'redux/apis', 'src/store', 'src/services', 'src']
      : adapter === 'angular-http'
        ? ['src/app', 'src']
        : ['src'];
  return [firstExisting(dir, candidates) || 'src'];
}

function serverRoots(dir, adapter) {
  switch (adapter) {
    case 'spring':
      return [firstExisting(dir, ['src/main/java', 'src']) || 'src/main/java'];
    case 'fastapi':
    case 'flask':
      return [firstExisting(dir, ['app', 'src']) || '.'];
    case 'next':
      return [firstExisting(dir, ['src/app', 'app', 'src/pages', 'pages', 'src']) || 'src'];
    case 'openapi':
      return ['.'];
    default:
      return [firstExisting(dir, ['src']) || 'src'];
  }
}

function firstExisting(dir, candidates) {
  return candidates.find((r) => fs.existsSync(path.join(dir, r)));
}

function readJson(file) {
  try {
    return JSON.parse(fs.readFileSync(file, 'utf8'));
  } catch {
    return null;
  }
}

function readText(file) {
  try {
    return fs.readFileSync(file, 'utf8');
  } catch {
    return '';
  }
}

function print(cwd, client, server, target, existed) {
  const rel = path.relative(cwd, target).split(path.sep).join('/') || path.basename(target);
  console.log('');
  console.log(c('bold', '  tieline · init'));
  console.log('');
  console.log(c('dim', `  scanning ${shorten(cwd)} for repos…`));

  line(cwd, 'client', client);
  line(cwd, 'server', server);

  console.log('');
  console.log(`  📝 wrote ${c('bold', rel)}${existed ? c('dim', ' (overwritten)') : ''}`);
  if (!client || !server) {
    console.log(c('yellow', `  ⚠️  ${[!client && 'client', !server && 'server'].filter(Boolean).join(' and ')} not detected — placeholder written, edit repo/roots by hand`));
  }
  console.log(c('dim', '  then run `tieline check`'));
  console.log('');
}

function line(cwd, side, m) {
  if (!m) {
    console.log(`  ${c('yellow', '?')} ${side}: ${c('dim', 'not detected (placeholder)')}`);
    return;
  }
  const repo = relRepo(cwd, m.dir);
  const roots = side === 'client' ? clientRoots(m.dir, m.adapter) : serverRoots(m.dir, m.adapter);
  console.log(
    `  ${c('green', '✔')} ${side}: ${c('cyan', m.adapter.padEnd(13))} → ${c('bold', repo)}   ${c('dim', `(roots: ${roots.join(', ')})`)}`,
  );
}

function shorten(dir) {
  const home = process.env.HOME || '';
  return home && dir.startsWith(home) ? '~' + dir.slice(home.length) : dir;
}
