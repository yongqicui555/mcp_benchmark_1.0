#!/usr/bin/env node
import { run } from '../src/cli.mjs';

run(process.argv.slice(2)).catch((err) => {
  console.error('tieline: ' + (err && err.message ? err.message : String(err)));
  process.exitCode = 2;
});
