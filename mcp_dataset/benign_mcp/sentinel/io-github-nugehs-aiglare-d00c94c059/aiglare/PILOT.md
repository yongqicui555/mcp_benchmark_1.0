# Pilot runbook

A one-week evaluation plan: install aiglare, audit a real backend and a real
frontend repo, read the report, tune the flags, and decide whether the CI gate
earns a place in your pipeline. Examples below use `./my-api` (backend) and
`./my-app` (frontend) — substitute your own paths.

## 1. Install and sanity-check

```bash
npm install -g @nugehs/aiglare   # or: npx @nugehs/aiglare
aiglare --help
```

## 2. First real run — backend AI domain

If the repo has a [repoctx](https://github.com/nugehs/repoctx) index, the
adapter engages automatically and you'll see "accelerated by repoctx index" in
the header.

```bash
# whole backend, human-readable
aiglare ./my-api

# zoom in on the AI surfaces only
aiglare ./my-api --severity amber

# only the dangerous class: AI output -> irreversible side-effect
aiglare ./my-api --sinks side-effectful
```

Eyeball the surfaces it reports: provider config files, AI service wrappers,
and any domain where model output feeds a payment, booking, email, or write.

## 3. Frontend run

```bash
aiglare ./my-app --sinks user-facing
```

Watch whether your disclaimer/guardrail components are credited. In v1 a
guardrail is only credited when it sits in the same file as the AI call —
cross-file crediting (a disclaimer imported into a chat component) is the
first v2 item.

## 4. Try the CI gate

```bash
aiglare ./my-api/src --ci; echo "exit: $?"
```

Exit 1 = a red side-effectful surface exists. Wire it into your CI workflow
against a real source path once you're happy with the signal-to-noise.

## 5. Calibrate

Expect some false positives and negatives on the first run — note which, then
tune the heuristics in `src/discovery/native-scanner.js` (see CONTRIBUTING.md)
or open an issue with a minimal repro.

## What's proven vs. what's pending

Proven by the test suite: provider detection, sink classification, guardrail
scoring, the CI gate, and — most importantly — that the repoctx index flips a
false-negative `internal` classification into a correct `user-facing` RED (see
the `fixtures-rc` test). Pending: cross-file guardrail crediting (needs the
call graph), and calibration against real code, which is what this pilot
produces.
