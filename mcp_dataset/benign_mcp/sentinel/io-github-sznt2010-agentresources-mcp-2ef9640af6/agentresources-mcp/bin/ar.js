#!/usr/bin/env node
// `ar` CLI shim. Forwards to the compiled CLI entrypoint so that this file
// can be published verbatim and resolved by Node 20+.
require("../dist/cli/index.js")
  .runCli(process.argv.slice(2))
  .catch((err) => {
    // eslint-disable-next-line no-console
    console.error(err && err.stack ? err.stack : err);
    process.exit(1);
  });
