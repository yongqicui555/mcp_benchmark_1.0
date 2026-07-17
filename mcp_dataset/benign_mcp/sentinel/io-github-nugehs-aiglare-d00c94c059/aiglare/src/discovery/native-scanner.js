import ts from 'typescript';
import fs from 'node:fs';
import path from 'node:path';
import { findProviderByPackage, findProviderByHost, INFERENCE_CALL_HINTS } from '../providers.js';

const SOURCE_EXT = new Set(['.ts', '.tsx', '.js', '.jsx', '.mjs', '.cjs']);
const IGNORE_DIRS = new Set(['node_modules', '.git', 'dist', 'build', '.next', 'coverage', '.dev-context', 'out', '__tests__', '__mocks__']);

// Test, story, and type-declaration files are not production AI surfaces: a
// spec that imports a provider and mentions "payment" is not a governance risk.
const NON_SOURCE_FILE_RX = /\.(spec|test|stories)\.[cm]?[jt]sx?$|\.d\.ts$/i;

export function walkFiles(root) {
  const out = [];
  (function rec(dir) {
    let entries;
    try { entries = fs.readdirSync(dir, { withFileTypes: true }); } catch { return; }
    for (const e of entries) {
      if (e.isDirectory()) {
        if (!IGNORE_DIRS.has(e.name) && !e.name.startsWith('.')) rec(path.join(dir, e.name));
      } else if (SOURCE_EXT.has(path.extname(e.name)) && !NON_SOURCE_FILE_RX.test(e.name)) {
        out.push(path.join(dir, e.name));
      }
    }
  })(root);
  return out;
}

// ---- Guardrail signal detectors (text + AST heuristics over a file) ----
const RX = {
  confidence: /\b(confidence|probability|score|threshold|certainty|logprob|topProb)\b/i,
  fallback: /\b(fallback|uncertain|notSure|not_sure|unknown|low[_-]?confidence|degraded|couldNotDetermine)\b/i,
  validation: /\b(zod|\.parse\(|\.safeParse\(|JSON\.parse|schema|validateSync|class-validator|ajv|allow[_-]?list|whitelist)\b/i,
  humanInLoop: /\b(confirm|review|approve|pending|awaitConfirmation|requireApproval|draft|needsReview)\b/i,
};

// Side-effect rules are call/method-shaped so a field or variable named like a
// side-effect (`email`, `bookingsAsVendor`, `isStripeConnected`) does not trip a
// sink — only an actual payment/booking/email operation does.
const SIDE_EFFECT_HINTS = {
  payment: /\b(stripe|paystack)\.[a-z_$]|\b(createCharge|chargeCard|processPayment|createPaymentIntent|capturePayment|issueRefund|createPayout)\s*\(|\.(charge|refund|payout|capture)\s*\(/i,
  booking: /\b(createBooking|confirmBooking|cancelBooking|makeBooking|reserve)\s*\(|\bbooking\.(create|update|delete|upsert|cancel|confirm)\b/i,
  email: /\b(sendMail|sendEmail|draftEmail|mailer|nodemailer|sendgrid|sgMail)\b|\.send(Mail|Email)\s*\(/i,
  db_write: /(prisma\.\w+\.(create|update|delete|upsert)|repository\.(save|insert|update|delete)|\.(save|insert)\(|knex\(|\.query\(['"`]\s*(INSERT|UPDATE|DELETE))/i,
  fs_write: /(writeFile|writeFileSync|fs\.write)/i,
  shell: /(execSync|child_process|\bspawn\()/i,
};

const USER_FACING_HINTS = {
  controller_route: /@(Get|Post|Put|Patch|Delete)\(|@Controller\(|export\s+(async\s+)?function\s+(GET|POST|PUT|PATCH|DELETE)\b/,
  http_response: /res\.(json|send)\(|NextResponse\.json\(|\.status\(\d+\)/,
  jsx_ext: /\.(t|j)sx$/,
};

// Blank out the given [start, end) spans (string/template literals) with spaces,
// preserving newlines and overall length so other offsets stay valid.
function blankRanges(text, ranges) {
  if (!ranges.length) return text;
  const chars = text.split('');
  for (const [s, e] of ranges) {
    for (let i = s; i < e && i < chars.length; i++) {
      if (chars[i] !== '\n') chars[i] = ' ';
    }
  }
  return chars.join('');
}

// Remove line and block comments. Run AFTER string literals are blanked so a
// "//" or "/*" inside a string can't be mistaken for a comment.
function stripComments(text) {
  return text
    .replace(/\/\*[\s\S]*?\*\//g, ' ')
    .replace(/(^|[^:/])\/\/[^\n]*/g, '$1 ');
}

export function analyzeFile(filePath) {
  let text;
  try { text = fs.readFileSync(filePath, 'utf8'); } catch { return null; }

  const sf = ts.createSourceFile(filePath, text, ts.ScriptTarget.Latest, true);
  const imports = [];
  const inferenceCalls = [];
  const fetchHostHits = [];
  const literalRanges = []; // string/template-literal spans, masked before side-effect scan
  let hasTryCatch = false;

  const lineOf = (node) => sf.getLineAndCharacterOfPosition(node.getStart(sf)).line + 1;

  function visit(node) {
    if (ts.isImportDeclaration(node) && node.moduleSpecifier) {
      const spec = node.moduleSpecifier.getText(sf);
      const prov = findProviderByPackage(spec);
      if (prov) imports.push({ provider: prov, line: lineOf(node), via: 'import' });
    }
    // Record string/template literal spans so prose inside prompts/messages
    // cannot drive side-effect classification.
    if (ts.isStringLiteralLike(node) || ts.isTemplateExpression(node)) {
      literalRanges.push([node.getStart(sf), node.getEnd()]);
    }
    if (ts.isCallExpression(node)) {
      // CommonJS `require('pkg')` and dynamic `import('pkg')` are module loads,
      // not network calls: the specifier goes through the same package registry
      // as an ESM import. Handling them here (instead of falling through to the
      // host matcher) also makes package/host disambiguation intentional — e.g.
      // require('@aws-sdk/client-bedrock-runtime') matches the bedrock provider
      // by PACKAGE, not because the "bedrock-runtime" host fragment happens to
      // appear inside the require string.
      const isRequire = ts.isIdentifier(node.expression) && node.expression.text === 'require';
      const isDynamicImport = node.expression.kind === ts.SyntaxKind.ImportKeyword;
      if (isRequire || isDynamicImport) {
        const spec = node.arguments && node.arguments[0];
        if (spec && ts.isStringLiteralLike(spec)) {
          const prov = findProviderByPackage(spec.text);
          if (prov) imports.push({ provider: prov, line: lineOf(node), via: isRequire ? 'require' : 'import()' });
        }
      } else {
        const callText = node.expression.getText(sf);
        if (INFERENCE_CALL_HINTS.some(h => callText.endsWith(h) || callText.includes(h))) {
          inferenceCalls.push({ text: callText, line: lineOf(node) });
        }
        // raw fetch/axios to a known host
        for (const arg of node.arguments || []) {
          if (ts.isStringLiteralLike(arg)) {
            const prov = findProviderByHost(arg.text);
            if (prov) fetchHostHits.push({ provider: prov, line: lineOf(node) });
          }
        }
      }
    }
    if (ts.isTryStatement(node)) hasTryCatch = true;
    ts.forEachChild(node, visit);
  }
  visit(sf);

  // A file is an AI surface if it imports a known provider SDK or calls a known
  // inference host directly (importedProvider already folds in fetchHostHits).
  // Inference method-name hints alone (.run()/.generate()/.invoke()) are too
  // weak to flag without a provider, so they only enrich evidence.
  const importedProvider = imports[0]?.provider || fetchHostHits[0]?.provider || null;
  if (!importedProvider) return null;
  // "imports a provider" is not "uses a model". DI wiring (e.g. a NestJS module
  // that constructs the client in a factory), config, and re-export files
  // import the SDK but never call it — they are not AI surfaces. Require an
  // actual inference call or a fetch to a known inference host.
  if (inferenceCalls.length === 0 && fetchHostHits.length === 0) return null;

  // sink classification — over CODE only, never prose.
  // (1) Mask string/template literals: a prompt that says "payment" or "booking"
  //     is not a payment or booking call.
  // (2) Strip comments: a keyword in a docstring or log line must not count.
  // (3) Neutralize the AI SDKs' own methods (.create()/.run()/.generate()) whose
  //     verbs collide with side-effect hints.
  let sideEffectText = stripComments(blankRanges(text, literalRanges));
  for (const c of inferenceCalls) {
    sideEffectText = sideEffectText.split(c.text).join(' /*inference*/ ');
  }

  const sideEffects = Object.entries(SIDE_EFFECT_HINTS).filter(([, rx]) => rx.test(sideEffectText)).map(([k]) => k);
  const userFacing = USER_FACING_HINTS.controller_route.test(text) ||
                     USER_FACING_HINTS.http_response.test(text) ||
                     USER_FACING_HINTS.jsx_ext.test(filePath);
  const sink = sideEffects.length ? 'side-effectful' : userFacing ? 'user-facing' : 'internal';

  // guardrail detection. human-in-loop only counts for side-effects, but we
  // compute the raw signal unconditionally so the repoctx adapter can re-apply
  // it if the index later promotes this surface to side-effectful.
  const humanInLoopSignal = RX.humanInLoop.test(text);
  const guardrails = {
    confidence: RX.confidence.test(text),
    fallback: RX.fallback.test(text),
    validation: RX.validation.test(text),
    humanInLoop: sink === 'side-effectful' ? humanInLoopSignal : 'n/a',
    errorIsolation: hasTryCatch,
    disclaimer: /\bdisclaimer\b/i.test(text),
  };

  const severity = scoreSeverity(sink, guardrails);

  return {
    file: filePath,
    file_abs: filePath,
    provider: importedProvider?.id || 'unknown',
    providerLabel: importedProvider?.label || 'Unknown',
    sink,
    sideEffects,
    guardrails,
    _humanInLoopSignal: humanInLoopSignal,
    severity,
    evidence: [
      ...imports.map(i => `${path.basename(filePath)}:${i.line} ${i.via} ${i.provider.label}`),
      ...inferenceCalls.slice(0, 3).map(c => `${path.basename(filePath)}:${c.line} ${c.text}()`),
    ],
  };
}

export function scoreSeverity(sink, g) {
  const present = [g.confidence, g.fallback, g.validation, g.errorIsolation, g.disclaimer, g.humanInLoop === true].filter(Boolean).length;
  if (sink === 'side-effectful') {
    if (g.humanInLoop !== true) return 'red';          // irreversible action with no confirm = headline risk
    return present >= 3 ? 'green' : 'amber';
  }
  if (sink === 'user-facing') {
    if (present === 0) return 'red';
    return present >= 2 ? 'green' : 'amber';
  }
  return 'green'; // internal-only
}
