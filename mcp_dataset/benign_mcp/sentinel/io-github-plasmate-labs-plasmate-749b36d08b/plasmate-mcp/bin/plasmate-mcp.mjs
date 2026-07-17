#!/usr/bin/env node
/**
 * Plasmate MCP Server
 * Wraps the `plasmate mcp` command for use with Claude Code, Claude Desktop, Cursor, etc.
 */
import { spawn } from 'child_process';
import { existsSync } from 'fs';
import { execSync } from 'child_process';

// Find plasmate binary
function findPlasmate() {
  // Check if plasmate is in PATH
  try {
    const path = execSync('which plasmate', { encoding: 'utf-8' }).trim();
    if (path) return path;
  } catch {}
  
  // Check common pip install locations
  const candidates = [
    `${process.env.HOME}/.local/bin/plasmate`,
    `${process.env.HOME}/.cargo/bin/plasmate`,
    '/usr/local/bin/plasmate',
  ];
  
  for (const c of candidates) {
    if (existsSync(c)) return c;
  }
  
  return null;
}

const binary = findPlasmate();

if (!binary) {
  process.stderr.write(
    'Error: plasmate binary not found.\n' +
    'Install with one of:\n' +
    '  pip install plasmate\n' +
    '  cargo install plasmate\n' +
    '  brew tap plasmate-labs/plasmate && brew install plasmate\n'
  );
  process.exit(1);
}

// Spawn plasmate mcp and pipe stdio
const child = spawn(binary, ['mcp'], {
  stdio: ['inherit', 'inherit', 'inherit'],
});

child.on('exit', (code) => process.exit(code ?? 0));
process.on('SIGINT', () => child.kill('SIGINT'));
process.on('SIGTERM', () => child.kill('SIGTERM'));
