import { test } from 'node:test';
import assert from 'node:assert';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { analyzeFile, walkFiles } from '../src/discovery/native-scanner.js';

const here = path.dirname(fileURLToPath(import.meta.url));
const fx = (p) => path.join(here, 'fixtures', p);
const run = (p) => analyzeFile(fx(p));

test('detects a provider import as an AI surface', () => {
  const r = run('bad/mascot-reply.tsx');
  assert.equal(r.provider, 'anthropic');
});

test('non-AI files are ignored', () => {
  assert.equal(run('good/utils.ts'), null);
});

test('auto-booking is RED side-effectful with no human-in-loop', () => {
  const r = run('bad/auto-booking.service.ts');
  assert.equal(r.sink, 'side-effectful');
  assert.equal(r.severity, 'red');
  assert.equal(r.guardrails.humanInLoop, false);
  assert.ok(r.sideEffects.includes('payment'));
});

test('user-facing reply with no guardrails is RED', () => {
  const r = run('bad/mascot-reply.tsx');
  assert.equal(r.sink, 'user-facing');
  assert.equal(r.severity, 'red');
});

test('SDK .create() does not falsely trigger db_write', () => {
  // bird-id calls completions.create() but writes nothing — must not be flagged side-effectful
  const r = run('good/bird-id.service.ts');
  assert.notEqual(r.sink, 'side-effectful');
});

test('deferred email draft (human-in-loop) is not RED', () => {
  const r = run('good/draft-email.service.ts');
  assert.equal(r.sink, 'side-effectful');
  assert.equal(r.guardrails.humanInLoop, true);
  assert.notEqual(r.severity, 'red');
});

test('fully-guarded identification scores all guardrails present', () => {
  const r = run('good/bird-id.service.ts');
  assert.ok(r.guardrails.confidence && r.guardrails.fallback && r.guardrails.validation && r.guardrails.errorIsolation);
});

test('side-effect keywords in a prompt/comment do not create a side-effect sink', () => {
  // payment/charge/refund/booking appear ONLY in a comment and a prompt string;
  // the file takes no such action, so it must not be classified side-effectful.
  const r = run('good/prompt-only-payment.service.ts');
  assert.notEqual(r.sink, 'side-effectful');
  assert.deepEqual(r.sideEffects, []);
  assert.notEqual(r.severity, 'red');
});

test('importing a provider without calling the model is not a surface', () => {
  // DI wiring: imports OpenAI, constructs it in a factory, never invokes it.
  assert.equal(run('good/ai-wiring.module.ts'), null);
});

test('side-effect-named fields/identifiers do not create a side-effect sink', () => {
  // isStripeConnected / bookingsAsVendor / email are read as data, not actions.
  const r = run('good/reads-payment-fields.service.ts');
  assert.deepEqual(r.sideEffects, []);
  assert.notEqual(r.sink, 'side-effectful');
  assert.notEqual(r.severity, 'red');
});

test('walkFiles excludes spec/test/stories/d.ts files', () => {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'aiglare-walk-'));
  for (const name of [
    'service.ts',
    'legacy.cjs',
    'service.spec.ts',
    'service.test.tsx',
    'worker.test.cjs',
    'button.stories.tsx',
    'types.d.ts',
  ]) {
    fs.writeFileSync(path.join(root, name), 'export const x = 1;');
  }
  fs.mkdirSync(path.join(root, '__tests__'));
  fs.writeFileSync(path.join(root, '__tests__', 'extra.ts'), 'export const y = 1;');

  const found = walkFiles(root).map((p) => path.basename(p));
  assert.deepEqual(found.sort(), ['legacy.cjs', 'service.ts']);
});

// ---- CommonJS / dynamic import detection ----
import { findProviderByPackage } from '../src/providers.js';

test('CJS: plain require of a provider is an AI surface', () => {
  const r = run('cjs/openai-plain-require.js');
  assert.equal(r.provider, 'openai');
  assert.ok(r.evidence.some((e) => e.includes('require OpenAI')));
});

test('CJS: destructured require is detected', () => {
  const r = run('cjs/anthropic-destructured-require.js');
  assert.equal(r.provider, 'anthropic');
});

test('CJS: member-access require is detected', () => {
  const r = run('cjs/openai-member-require.js');
  assert.equal(r.provider, 'openai');
});

test('dynamic import() of a provider is detected', () => {
  const r = run('cjs/openai-dynamic-import.js');
  assert.equal(r.provider, 'openai');
  assert.ok(r.evidence.some((e) => e.includes('import() OpenAI')));
});

test('CJS: require without an inference call is not a surface', () => {
  // same DI-wiring rule as ESM: loading the SDK is not using the model.
  assert.equal(run('cjs/wiring-only-require.js'), null);
});

test('require of @aws-sdk/client-bedrock-runtime matches bedrock by package, not host substring', () => {
  // the package name contains the "bedrock-runtime" host fragment; the match
  // must come from the package registry (evidence says "require"), not from
  // findProviderByHost accidentally substring-matching the require string.
  const r = run('cjs/bedrock-require.js');
  assert.equal(r.provider, 'bedrock');
  assert.ok(r.evidence.some((e) => e.includes('require AWS Bedrock')));
});

test('registry: groq-sdk, @google/genai, and official @ai-sdk/* packages resolve', () => {
  assert.equal(findProviderByPackage('groq-sdk').id, 'groq');
  assert.equal(findProviderByPackage('@google/genai').id, 'google-genai');
  for (const pkg of ['google', 'mistral', 'groq', 'xai', 'cohere', 'amazon-bedrock', 'azure', 'deepseek', 'perplexity']) {
    assert.equal(findProviderByPackage(`@ai-sdk/${pkg}`)?.id, 'vercel-ai', `@ai-sdk/${pkg}`);
  }
});

import { loadRepoctxHints, refineWithHints } from '../src/discovery/repoctx-adapter.js';
import { scoreSeverity } from '../src/discovery/native-scanner.js';

test('repoctx httpMethods refines internal -> user-facing (catches a false negative)', () => {
  const idxPath = fx('fixtures-rc/.dev-context/index.json');
  const root = fx('fixtures-rc');
  const rc = loadRepoctxHints(idxPath, root);
  const raw = analyzeFile(fx('fixtures-rc/src/ai/chat.service.ts'));
  assert.equal(raw.sink, 'internal'); // single-file scan can't see the route
  const refined = refineWithHints(raw, rc.hints);
  assert.equal(refined.sink, 'user-facing');
  assert.equal(refined._refinedBy, 'repoctx-httpMethods');
  assert.equal(scoreSeverity(refined.sink, refined.guardrails), 'red');
});

test('repoctx index detects provider from imports[] without parsing', () => {
  const root = fx('fixtures-rc');
  const rc = loadRepoctxHints(fx('fixtures-rc/.dev-context/index.json'), root);
  const h = rc.hints.get(fx('fixtures-rc/src/ai/chat.service.ts'));
  assert.equal(h.provider.id, 'openai');
  assert.ok(rc.candidates.has(fx('fixtures-rc/src/ai/chat.service.ts')));
});

test('side-effect domain promotion re-evaluates human-in-loop (not falsely RED)', () => {
  const root = fx('fixtures-rc');
  const rc = loadRepoctxHints(fx('fixtures-rc/.dev-context/index.json'), root);
  const raw = analyzeFile(fx('fixtures-rc/src/ai/trip-suggest.service.ts'));
  // native scan can't see the side-effect domain, so it reads as internal
  assert.equal(raw.sink, 'internal');
  assert.equal(raw.guardrails.humanInLoop, 'n/a');
  const refined = refineWithHints(raw, rc.hints);
  assert.equal(refined.sink, 'side-effectful');
  assert.equal(refined._refinedBy, 'repoctx-domain');
  // the human-in-loop signal ('pending_approval'/'requiresApproval') must be
  // re-applied after promotion, so the surface is amber — not falsely red.
  assert.equal(refined.guardrails.humanInLoop, true);
  assert.notEqual(scoreSeverity(refined.sink, refined.guardrails), 'red');
});

test('repoctx index nested under map.files is read (real repoctx shape)', () => {
  // Current repoctx writes the catalog under `map.files`, not a top-level
  // `files`. Regression: the adapter must read it, otherwise acceleration
  // silently loads 0 files and degrades to native-only.
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'aiglare-rc-'));
  const dir = path.join(root, '.dev-context');
  fs.mkdirSync(dir, { recursive: true });
  const idxPath = path.join(dir, 'index.json');
  fs.writeFileSync(
    idxPath,
    JSON.stringify({
      version: 1,
      map: {
        files: [
          {
            path: 'src/ai/chat.service.ts',
            kind: 'source',
            domain: 'ai',
            domains: ['ai'],
            httpMethods: [],
            imports: ['@nestjs/common', 'openai'],
            exports: [],
          },
        ],
      },
    }),
  );

  const rc = loadRepoctxHints(idxPath, root);
  assert.equal(rc.fileCount, 1);
  const abs = path.join(root, 'src/ai/chat.service.ts');
  assert.ok(rc.candidates.has(abs));
  assert.equal(rc.hints.get(abs).provider.id, 'openai');
});
