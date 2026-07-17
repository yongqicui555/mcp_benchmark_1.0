import { CONTROLS, FRAMEWORK_IDS } from './controls.js';

// Returns violations[] for a single surface, filtered to the requested frameworks.
// Each violation: { framework, frameworkLabel, id, title, description, level }
export function mapViolations(surface, frameworks = FRAMEWORK_IDS) {
  const violations = [];
  for (const fw of frameworks) {
    const catalog = CONTROLS[fw];
    if (!catalog) continue;
    for (const control of catalog) {
      if (control.when(surface)) {
        violations.push({
          framework: fw,
          id: control.id,
          title: control.title,
          description: control.description,
          level: control.level,
        });
      }
    }
  }
  return violations;
}

// Parses a --compliance value: 'all', or comma-separated framework IDs.
// Returns validated array of framework IDs or throws with a helpful message.
export function parseFrameworks(value) {
  if (!value) return [];
  if (value === 'all') return [...FRAMEWORK_IDS];
  const ids = value.split(',').map(s => s.trim()).filter(Boolean);
  const invalid = ids.filter(id => !CONTROLS[id]);
  if (invalid.length) {
    throw new Error(
      `Unknown compliance framework(s): ${invalid.join(', ')}. ` +
      `Valid: ${FRAMEWORK_IDS.join(', ')}, all`
    );
  }
  return ids;
}

// Builds a per-framework violation summary: { soc2: { error: N, warning: N }, ... }
export function buildComplianceSummary(surfaces, frameworks) {
  const summary = {};
  for (const fw of frameworks) summary[fw] = { error: 0, warning: 0 };
  for (const s of surfaces) {
    for (const v of (s.violations ?? [])) {
      if (summary[v.framework]) summary[v.framework][v.level]++;
    }
  }
  return summary;
}
