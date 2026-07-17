#!/usr/bin/env node
// Replace `workspace:*` deps in the mirrored package.json with the published
// version of each AR package. Without this, `npm install` against the mirror
// alone would fail because pnpm workspaces don't exist outside the monorepo.

import { readFileSync, writeFileSync } from "node:fs";
import { resolve } from "node:path";

const target = process.argv[2];
if (!target) {
  console.error("usage: normalise-package-json.mjs <path-to-package.json>");
  process.exit(2);
}

const path = resolve(target);
const pkg = JSON.parse(readFileSync(path, "utf8"));

// Pin AR workspace deps to the same version as the package being published.
// Pre-1.0 caret-major would still be reasonable; using exact for safety.
const arVersion = pkg.version;

for (const section of ["dependencies", "devDependencies", "peerDependencies"]) {
  const deps = pkg[section];
  if (!deps) continue;
  for (const name of Object.keys(deps)) {
    if (deps[name] === "workspace:*" || deps[name] === "workspace:^") {
      if (name.startsWith("@agentresources/")) {
        deps[name] = `^${arVersion}`;
      } else if (name.startsWith("@ar/")) {
        // Internal-only packages should never be a runtime dep of a public mirror.
        delete deps[name];
        console.warn(`[normalise] dropped internal workspace dep ${name}`);
      } else {
        // Unknown workspace dep — fail loudly so we don't ship a broken package.json.
        console.error(`[normalise] unknown workspace:* dep ${name}; refusing to publish`);
        process.exit(1);
      }
    }
  }
}

// Strip monorepo-only scripts.
if (pkg.scripts) {
  delete pkg.scripts.dev;
}

writeFileSync(path, JSON.stringify(pkg, null, 2) + "\n", "utf8");
console.log(`[normalise] rewrote ${path}`);
