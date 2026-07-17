import fs from 'node:fs';
import path from 'node:path';

const SKIP = new Set(['node_modules', 'dist', '.git', '.next', 'coverage', '.worktrees', '.yarn']);

/**
 * Recursively collect files under `dir` whose basename passes `filter`.
 * Returns absolute paths. Missing directories are skipped silently.
 */
export function walk(dir, filter = () => true) {
  const out = [];
  let entries;
  try {
    entries = fs.readdirSync(dir, { withFileTypes: true });
  } catch {
    return out;
  }
  for (const entry of entries) {
    if (entry.name.startsWith('.') && entry.name !== '.') continue;
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      if (SKIP.has(entry.name)) continue;
      out.push(...walk(full, filter));
    } else if (entry.isFile() && filter(entry.name)) {
      out.push(full);
    }
  }
  return out;
}

/** Line number (1-based) of a character offset within text. */
export function lineAt(text, offset) {
  let line = 1;
  for (let i = 0; i < offset && i < text.length; i++) {
    if (text[i] === '\n') line++;
  }
  return line;
}
