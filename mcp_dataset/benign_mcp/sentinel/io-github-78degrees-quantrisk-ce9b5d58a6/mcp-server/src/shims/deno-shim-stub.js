// Stub for @deno/shim-deno on Cloudflare Workers.
//
// yahoo-finance2 imports `Deno` from this package and uses two surfaces:
//   1. runtime-detect.js checks for `Deno.version.deno` and `Deno.build.os`
//      to decide whether we're on Deno; without those we correctly fall
//      through to the Cloudflare branch.
//   2. createYahooFinance.js calls `Deno.stdout.isTerminal()` to pick a
//      logger format. Stub it to return false so logs render as JSON.
export const Deno = {
  stdout: {
    isTerminal: () => false,
  },
};
export default { Deno };
