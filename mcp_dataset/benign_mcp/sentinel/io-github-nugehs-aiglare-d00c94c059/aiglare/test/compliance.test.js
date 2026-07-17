import { test } from 'node:test';
import assert from 'node:assert';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { mapViolations, parseFrameworks, buildComplianceSummary } from '../src/compliance/mapper.js';
import { FRAMEWORK_IDS } from '../src/compliance/controls.js';
import { renderLint } from '../src/report/lint-reporter.js';
import { renderMarkdown } from '../src/report/markdown-reporter.js';
import { runAudit } from '../src/audit.js';

const here = path.dirname(fileURLToPath(import.meta.url));
const fx = (p) => path.join(here, 'fixtures', p);

// Minimal surface stubs
const redSideEffectful = {
  file: 'src/booking.ts',
  sink: 'side-effectful',
  sideEffects: ['payment', 'db_write'],
  severity: 'red',
  provider: 'openai',
  providerLabel: 'OpenAI',
  guardrails: { confidence: false, fallback: false, validation: false, humanInLoop: false, errorIsolation: false, disclaimer: false },
  evidence: ['src/booking.ts:42 autoBook'],
};

const amberUserFacing = {
  file: 'src/chat.ts',
  sink: 'user-facing',
  sideEffects: [],
  severity: 'amber',
  provider: 'anthropic',
  providerLabel: 'Anthropic',
  guardrails: { confidence: false, fallback: true, validation: false, humanInLoop: 'n/a', errorIsolation: true, disclaimer: false },
  evidence: ['src/chat.ts:18 getReply'],
};

const greenInternal = {
  file: 'src/logger.ts',
  sink: 'internal',
  sideEffects: [],
  severity: 'green',
  provider: 'openai',
  providerLabel: 'OpenAI',
  guardrails: { confidence: true, fallback: true, validation: true, humanInLoop: 'n/a', errorIsolation: true, disclaimer: false },
  evidence: [],
};

// --- parseFrameworks ---

test('parseFrameworks: "all" returns all framework IDs', () => {
  assert.deepEqual(parseFrameworks('all'), FRAMEWORK_IDS);
});

test('parseFrameworks: comma-separated values are parsed correctly', () => {
  assert.deepEqual(parseFrameworks('soc2,nist'), ['soc2', 'nist']);
});

test('parseFrameworks: throws on unknown framework', () => {
  assert.throws(() => parseFrameworks('soc2,badfw'), /Unknown compliance framework/);
});

test('parseFrameworks: returns empty array for falsy input', () => {
  assert.deepEqual(parseFrameworks(null), []);
  assert.deepEqual(parseFrameworks(''), []);
});

// --- mapViolations ---

test('mapViolations: red side-effectful triggers HITL errors in all frameworks', () => {
  const v = mapViolations(redSideEffectful, FRAMEWORK_IDS);
  const hitlErrors = v.filter(x => x.level === 'error');
  // SOC2 CC9.1, EU Art.14, NIST MANAGE-2.2, OWASP LLM08 — all should fire
  const frameworks = new Set(hitlErrors.map(x => x.framework));
  assert.ok(frameworks.has('soc2'), 'soc2 CC9.1 should fire');
  assert.ok(frameworks.has('eu-ai-act'), 'eu-ai-act Art.14 should fire');
  assert.ok(frameworks.has('nist'), 'nist MANAGE-2.2 should fire');
  assert.ok(frameworks.has('owasp'), 'owasp LLM08 should fire');
});

test('mapViolations: red side-effectful triggers validation errors', () => {
  const v = mapViolations(redSideEffectful, ['soc2', 'owasp']);
  const ids = v.map(x => x.id);
  assert.ok(ids.includes('PI1.2'), 'SOC2 PI1.2 (validation) should fire');
  assert.ok(ids.includes('LLM02'), 'OWASP LLM02 (insecure output) should fire');
});

test('mapViolations: internal sink produces no violations', () => {
  const v = mapViolations(greenInternal, FRAMEWORK_IDS);
  assert.equal(v.length, 0);
});

test('mapViolations: amber user-facing with partial guardrails produces warnings', () => {
  const v = mapViolations(amberUserFacing, ['soc2', 'nist']);
  assert.ok(v.length > 0, 'should have some violations');
  // humanInLoop is n/a so HITL controls should NOT fire
  const hitlViolations = v.filter(x => ['CC9.1', 'MANAGE-2.2'].includes(x.id));
  assert.equal(hitlViolations.length, 0, 'HITL controls should not fire for user-facing sink');
});

test('mapViolations: only requested frameworks appear in violations', () => {
  const v = mapViolations(redSideEffectful, ['soc2']);
  const fw = new Set(v.map(x => x.framework));
  assert.deepEqual([...fw], ['soc2']);
});

test('mapViolations: GOVERN-1.2 fires only for red severity', () => {
  const red = mapViolations(redSideEffectful, ['nist']);
  const amber = mapViolations(amberUserFacing, ['nist']);
  assert.ok(red.some(v => v.id === 'GOVERN-1.2'), 'should fire for red');
  assert.ok(!amber.some(v => v.id === 'GOVERN-1.2'), 'should not fire for amber');
});

// --- buildComplianceSummary ---

test('buildComplianceSummary: counts errors and warnings per framework', () => {
  const violations = mapViolations(redSideEffectful, ['soc2', 'owasp']);
  const surface = { ...redSideEffectful, violations };
  const summary = buildComplianceSummary([surface], ['soc2', 'owasp']);
  assert.ok(summary.soc2.error > 0, 'soc2 should have errors');
  assert.ok(summary.owasp.error > 0, 'owasp should have errors');
});

// --- runAudit integration ---

test('runAudit: compliance option attaches violations to surfaces', () => {
  const report = runAudit({ path: fx('bad'), compliance: ['soc2', 'owasp'] });
  assert.ok(report.compliance, 'should have compliance object');
  assert.deepEqual(report.compliance.frameworks, ['soc2', 'owasp']);
  for (const s of report.surfaces) {
    assert.ok(Array.isArray(s.violations), 'each surface should have violations[]');
  }
});

test('runAudit: no compliance option — violations not attached', () => {
  const report = runAudit({ path: fx('bad') });
  assert.equal(report.compliance, null);
  for (const s of report.surfaces) {
    assert.equal(s.violations, undefined, 'violations should be absent without --compliance');
  }
});

test('runAudit: red side-effectful fixture has HITL violations across all frameworks', () => {
  const report = runAudit({ path: fx('bad'), compliance: FRAMEWORK_IDS });
  const sideEffectSurface = report.surfaces.find(s => s.sink === 'side-effectful');
  assert.ok(sideEffectSurface, 'should find a side-effectful surface');
  assert.ok(sideEffectSurface.violations.length > 0, 'should have violations');
  const hitlErrors = sideEffectSurface.violations.filter(v => v.level === 'error');
  assert.ok(hitlErrors.length >= 4, 'should have at least 4 error-level HITL violations (one per framework)');
});

// --- renderLint ---

test('renderLint: produces ESLint-style output with file names and rule IDs', () => {
  const report = runAudit({ path: fx('bad'), compliance: ['soc2'] });
  const out = renderLint(report, { color: false });
  assert.ok(out.includes('soc2/'), 'should include framework/control rule IDs');
  assert.ok(out.includes('error'), 'should include error severity');
  assert.ok(out.match(/\d+:\d+/), 'should include line:col format');
});

test('renderLint: summary line shows file count, errors, warnings', () => {
  const report = runAudit({ path: fx('bad'), compliance: ['soc2'] });
  const out = renderLint(report, { color: false });
  const lastLine = out.trim().split('\n').pop();
  assert.ok(lastLine.includes('file'), 'summary should mention files');
  assert.ok(lastLine.includes('error'), 'summary should mention errors');
  assert.ok(lastLine.includes('warning'), 'summary should mention warnings');
});

test('renderLint: works without compliance (guardrail mode)', () => {
  const report = runAudit({ path: fx('bad') });
  const out = renderLint(report, { color: false });
  assert.ok(out.includes('guardrail/'), 'should use guardrail/ rule IDs without compliance');
});

// --- renderMarkdown ---

test('renderMarkdown: produces markdown with framework sections when compliance set', () => {
  const report = runAudit({ path: fx('bad'), compliance: ['soc2', 'eu-ai-act'] });
  const out = renderMarkdown(report);
  assert.ok(out.includes('# AI Governance Audit Report'), 'should have title');
  assert.ok(out.includes('SOC 2'), 'should include SOC 2 section');
  assert.ok(out.includes('EU AI Act'), 'should include EU AI Act section');
  assert.ok(out.includes('CC9.1'), 'should include control IDs');
});

test('renderMarkdown: includes all-surfaces table', () => {
  const report = runAudit({ path: fx('bad'), compliance: ['nist'] });
  const out = renderMarkdown(report);
  assert.ok(out.includes('## All AI Surfaces'), 'should have surfaces table');
});
