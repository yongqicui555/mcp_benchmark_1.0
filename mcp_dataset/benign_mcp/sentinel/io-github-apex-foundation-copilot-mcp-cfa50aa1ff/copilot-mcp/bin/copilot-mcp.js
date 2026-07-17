#!/usr/bin/env node
import { dispatch } from '../dist/cli.js'

dispatch(process.argv.slice(2)).catch((err) => {
  process.stderr.write(`copilot-mcp fatal: ${err?.message ?? err}\n`)
  process.exit(1)
})
