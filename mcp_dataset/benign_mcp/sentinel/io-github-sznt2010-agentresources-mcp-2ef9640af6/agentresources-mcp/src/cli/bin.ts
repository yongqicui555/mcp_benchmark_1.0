#!/usr/bin/env node
import { runCli } from "./index.js";

runCli(process.argv.slice(2)).catch((err) => {
  // eslint-disable-next-line no-console
  console.error(err instanceof Error ? err.message : err);
  process.exit(1);
});
