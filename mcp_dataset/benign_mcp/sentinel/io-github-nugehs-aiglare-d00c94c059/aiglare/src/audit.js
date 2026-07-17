import fs from 'node:fs';
import path from 'node:path';
import { walkFiles, analyzeFile, scoreSeverity } from './discovery/native-scanner.js';
import { findRepoctxIndex, loadRepoctxHints, refineWithHints } from './discovery/repoctx-adapter.js';
import { buildSummary } from './report/reporter.js';
import { mapViolations, buildComplianceSummary } from './compliance/mapper.js';

// Core audit. Pure: returns the report object, never touches the console or
// process exit code. Shared by the CLI and the MCP server so both surface
// identical results.
//
// options: { path, paths?: string[], sinks?: string[], severity?: 'red'|'amber',
//            ci?: boolean, compliance?: string[] }
export function runAudit(options = {}) {
  // Multi-path: scan each root and prefix file paths with the repo name.
  const roots = options.paths?.length
    ? options.paths.map(p => path.resolve(p))
    : [path.resolve(options.path ?? process.cwd())];

  for (const root of roots) {
    if (!fs.existsSync(root)) throw new Error(`Path not found: ${root}`);
  }

  const multiRepo = roots.length > 1;
  const repoName = multiRepo
    ? roots.map(r => path.basename(r)).join(', ')
    : path.basename(roots[0]);

  let surfaces = [];
  let acceleratedBy = null;

  for (const root of roots) {
    const repoLabel = path.basename(root);

    // Optional repoctx acceleration.
    const idxPath = findRepoctxIndex(root);
    const rc = idxPath ? loadRepoctxHints(idxPath, root) : null;
    if (rc) acceleratedBy = `repoctx index (${rc.fileCount} files)`;

    const allFiles = walkFiles(root);
    const ordered = rc?.candidates
      ? [...allFiles].sort((a, b) => (rc.candidates.has(b) ? 1 : 0) - (rc.candidates.has(a) ? 1 : 0))
      : allFiles;

    for (const f of ordered) {
      const r = analyzeFile(f);
      if (r) {
        const refined = refineWithHints(r, rc?.hints);
        refined.severity = scoreSeverity(refined.sink, refined.guardrails);
        delete refined.file_abs;
        delete refined._humanInLoopSignal;
        // Prefix with repo name when scanning multiple roots
        const rel = path.relative(root, refined.file ?? f);
        refined.file = multiRepo ? `${repoLabel}/${rel}` : rel;
        surfaces.push(refined);
      }
    }
  }

  // filters
  if (options.sinks) surfaces = surfaces.filter(s => options.sinks.includes(s.sink));
  if (options.severity === 'red') surfaces = surfaces.filter(s => s.severity === 'red');
  else if (options.severity === 'amber') surfaces = surfaces.filter(s => s.severity !== 'green');

  // Compliance mapping — attach violations[] to each surface when requested.
  const frameworks = options.compliance ?? [];
  if (frameworks.length) {
    surfaces = surfaces.map(s => ({ ...s, violations: mapViolations(s, frameworks) }));
  }

  const summary = buildSummary(surfaces);
  const blocking = surfaces.filter(s => s.severity === 'red' && s.sink === 'side-effectful').length;

  return {
    ok: true,
    repo: repoName,
    acceleratedBy,
    surfaceCount: surfaces.length,
    summary,
    compliance: frameworks.length
      ? { frameworks, violations: buildComplianceSummary(surfaces, frameworks) }
      : null,
    surfaces,
    gate: options.ci ? { passed: blocking === 0, blocking } : null,
  };
}
