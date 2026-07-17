const C = {
  reset: '\x1b[0m',
  bold: '\x1b[1m',
  dim: '\x1b[2m',
  red: '\x1b[31m',
  green: '\x1b[32m',
  yellow: '\x1b[33m',
  cyan: '\x1b[36m',
};
const on = process.stdout.isTTY && !process.env.NO_COLOR;
const c = (k, s) => (on ? C[k] + s + C.reset : s);

const rel = (f) => String(f).replace(process.cwd() + '/', '');
const loc = (e) => c('dim', e.line ? `${rel(e.file)}:${e.line}` : rel(e.file));

export function reportHuman(result, { command = 'check' } = {}) {
  const { matched, drift, unverifiable, dead, totals } = result;

  if (command === 'orphans') {
    printDead(dead);
    return;
  }
  if (command === 'list') {
    printList(matched, drift, unverifiable);
    return;
  }

  console.log('');
  console.log(c('bold', '  tieline · contract check'));
  console.log('');

  if (drift.length) {
    console.log(c('red', c('bold', `  ❌  ${drift.length} drift`)) + c('dim', '  (FE calls a route the backend does not expose)'));
    for (const d of drift) {
      console.log(`     ${c('red', d.method.padEnd(6))} ${c('bold', '/' + d._np)}`);
      console.log(`            ${c('dim', d.name)}  ·  ${loc(d)}`);
      console.log(`            ${c('yellow', '→ ' + d.hint)}`);
    }
    console.log('');
  }

  if (unverifiable.length) {
    console.log(c('yellow', `  ⚠️   ${unverifiable.length} unverifiable`) + c('dim', '  (url built at runtime — cannot resolve statically)'));
    for (const u of unverifiable.slice(0, 12)) {
      console.log(`     ${c('dim', u.name.padEnd(28))} ${loc(u)}`);
    }
    if (unverifiable.length > 12) console.log(c('dim', `     … and ${unverifiable.length - 12} more`));
    console.log('');
  }

  console.log(
    '  ' +
      c('green', `✅ ${totals.matched} matched`) +
      '   ' +
      c('red', `❌ ${totals.drift} drift`) +
      '   ' +
      c('yellow', `⚠️  ${totals.unverifiable} unverifiable`) +
      '   ' +
      c('dim', `🟡 ${totals.dead} unused backend routes`),
  );
  console.log(c('dim', '  (run `tieline orphans` to list unused backend routes)'));
  console.log('');
}

function printDead(dead) {
  console.log('');
  console.log(c('bold', `  🟡  ${dead.length} backend routes no resolvable frontend call reaches`));
  console.log(c('dim', '  (may be intentional: webhooks, admin tools, internal, or other clients)'));
  console.log('');
  for (const r of dead) {
    console.log(`     ${c('cyan', r.method.padEnd(6))} ${'/' + r._np}   ${loc(r)}`);
  }
  console.log('');
}

export function reportDoctor(result, { codeAdapter, specSource } = {}) {
  const { undocumented, phantom, totals } = result;

  console.log('');
  console.log(c('bold', '  tieline · doctor') + c('dim', `   code (${codeAdapter})  ↔  spec (${rel(specSource)})`));
  console.log('');

  if (undocumented.length) {
    console.log(c('red', c('bold', `  ❌  ${undocumented.length} undocumented`)) + c('dim', '  (in code, missing from the published spec)'));
    for (const r of undocumented) {
      console.log(`     ${c('red', r.method.padEnd(6))} ${c('bold', '/' + r._np)}   ${loc(r)}`);
      if (r.hint) console.log(`            ${c('yellow', '→ ' + r.hint)}`);
    }
    console.log('');
  }

  if (phantom.length) {
    console.log(c('yellow', c('bold', `  👻  ${phantom.length} phantom`)) + c('dim', '  (in the spec, no matching route in code)'));
    for (const r of phantom.slice(0, 30)) {
      console.log(`     ${c('yellow', r.method.padEnd(6))} ${'/' + r._np}`);
      if (r.hint) console.log(`            ${c('dim', '→ ' + r.hint)}`);
    }
    if (phantom.length > 30) console.log(c('dim', `     … and ${phantom.length - 30} more`));
    console.log('');
  }

  if (!undocumented.length && !phantom.length) {
    console.log(c('green', '  ✅ code and spec agree on every route.'));
    console.log('');
  }

  console.log(
    '  ' +
      c('green', `✅ ${totals.matched} agree`) +
      '   ' +
      c('red', `❌ ${totals.undocumented} undocumented`) +
      '   ' +
      c('yellow', `👻 ${totals.phantom} phantom`) +
      c('dim', `   (${totals.code} code routes, ${totals.spec} spec routes)`),
  );
  console.log('');
}

function printList(matched, drift, unverifiable) {
  console.log('');
  const all = [
    ...matched.map((e) => ({ e, mark: c('green', '✅') })),
    ...drift.map((e) => ({ e, mark: c('red', '❌') })),
    ...unverifiable.map((e) => ({ e, mark: c('yellow', '⚠️ '), unresolved: true })),
  ].sort((a, b) => a.e.name.localeCompare(b.e.name));
  for (const { e, mark, unresolved } of all) {
    const p = unresolved ? c('dim', '(runtime url)') : c('bold', e.method + ' /' + e._np);
    console.log(`  ${mark} ${e.name.padEnd(34)} ${p}  ${loc(e)}`);
  }
  console.log('');
}
