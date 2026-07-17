# Contributing

## Adding an AI provider

The fastest, most valuable contribution. Edit `src/providers.js` and add an
entry to `PROVIDERS` with the npm package name(s) and/or API host(s):

```js
{ id: 'your-provider', label: 'Your Provider', packages: ['your-sdk'], hosts: ['api.yourprovider.com'] }
```

If the SDK's inference method name isn't already covered, add it to
`INFERENCE_CALL_HINTS`. Add a fixture under `test/fixtures/` and a case in
`test/scanner.test.js`.

## Tuning guardrail detection

Detection heuristics live in `src/discovery/native-scanner.js` (`RX`,
`SIDE_EFFECT_HINTS`, `USER_FACING_HINTS`, `scoreSeverity`). Keep changes
fixture-backed: every rule change should move a fixture's classification and
have a test asserting it.

## Philosophy

This is advisory static analysis — a linter, not a verifier. Prefer catching a
true risk with some false positives over staying quiet. The CI gate
(`--ci`) is deliberately narrow (red + side-effectful only) so teams can adopt
it without alert fatigue.
