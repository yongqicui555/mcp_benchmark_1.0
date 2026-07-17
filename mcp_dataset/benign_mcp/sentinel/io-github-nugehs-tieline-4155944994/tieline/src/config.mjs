import fs from 'node:fs';
import path from 'node:path';

const DEFAULTS = {
  client: { adapter: 'rtk-query', repo: '.', roots: ['redux/apis'], basePath: '' },
  server: { adapter: 'nestjs', repo: '.', roots: ['src'], globalPrefix: '' },
  ignore: [],
  failOn: ['drift'],
};

/** Load and resolve tieline.config.json. Repo paths are resolved relative to the config file. */
export function loadConfig(explicitPath) {
  const cfgPath = path.resolve(explicitPath || findConfig());
  const dir = path.dirname(cfgPath);
  const raw = JSON.parse(fs.readFileSync(cfgPath, 'utf8'));

  const cfg = {
    ...DEFAULTS,
    ...raw,
    client: { ...DEFAULTS.client, ...(raw.client || {}) },
    server: { ...DEFAULTS.server, ...(raw.server || {}) },
  };
  cfg.client.repoRoot = path.resolve(dir, cfg.client.repo);
  cfg.server.repoRoot = path.resolve(dir, cfg.server.repo);
  cfg._path = cfgPath;
  return cfg;
}

function findConfig() {
  let dir = process.cwd();
  for (;;) {
    const p = path.join(dir, 'tieline.config.json');
    if (fs.existsSync(p)) return p;
    const parent = path.dirname(dir);
    if (parent === dir) break;
    dir = parent;
  }
  throw new Error('No tieline.config.json found (searched up from cwd). Pass --config <path>.');
}
