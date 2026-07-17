// Control catalog: maps guardrail failures → specific compliance controls.
// Each entry: { id, title, description, level: 'error'|'warning', when(surface) → bool }

export const FRAMEWORKS = {
  'soc2':       'SOC 2 (Trust Services Criteria)',
  'eu-ai-act':  'EU AI Act',
  'nist':       'NIST AI RMF',
  'owasp':      'OWASP LLM Top 10',
};

export const FRAMEWORK_IDS = Object.keys(FRAMEWORKS);

// Controls are grouped by framework. `when` receives the full surface object.
export const CONTROLS = {
  'soc2': [
    {
      id: 'CC9.1',
      title: 'Risk Mitigation — Side-effectful AI without human review gate',
      description:
        'A side-effectful AI output (payment, booking, email, db write, shell) reaches an ' +
        'irreversible action with no human-in-the-loop confirmation, violating SOC 2 CC9.1 ' +
        '(risk mitigation through vendor/partner commitments and internal controls).',
      level: 'error',
      when: s => s.sink === 'side-effectful' && s.guardrails.humanInLoop !== true,
    },
    {
      id: 'PI1.2',
      title: 'Processing Integrity — AI output reaches users without validation',
      description:
        'Model output flows to a user or action without schema validation, allow-list, or ' +
        'structured parsing, violating SOC 2 PI1.2 (inputs are complete, accurate, and authorized).',
      level: 'error',
      when: s => s.sink !== 'internal' && !s.guardrails.validation,
    },
    {
      id: 'PI1.3',
      title: 'Processing Integrity — No confidence threshold on model output',
      description:
        'Model output is acted on with no confidence or probability threshold check, violating ' +
        'SOC 2 PI1.3 (processing results are complete, accurate, timely, and authorized).',
      level: 'warning',
      when: s => s.sink !== 'internal' && !s.guardrails.confidence,
    },
    {
      id: 'CC7.2',
      title: 'System Operations — No monitoring signal for anomalous AI output',
      description:
        'No confidence gating or output validation means anomalous model outputs cannot be ' +
        'detected, violating SOC 2 CC7.2 (monitor system components and controls for anomalies).',
      level: 'warning',
      when: s => s.sink !== 'internal' && !s.guardrails.confidence && !s.guardrails.validation,
    },
    {
      id: 'CC7.4',
      title: 'Incident Response — AI call not wrapped in error isolation',
      description:
        'The AI call has no error isolation (try-catch or equivalent), meaning failures propagate ' +
        'uncontrolled, violating SOC 2 CC7.4 (respond to identified security incidents).',
      level: 'warning',
      when: s => s.sink !== 'internal' && !s.guardrails.errorIsolation,
    },
    {
      id: 'A1.2',
      title: 'Availability — No fallback for degraded or uncertain AI output',
      description:
        'No fallback path exists when the model returns low-confidence or uncertain output, ' +
        'violating SOC 2 A1.2 (recovery processes maintain system availability).',
      level: 'warning',
      when: s => s.sink !== 'internal' && !s.guardrails.fallback,
    },
  ],

  'eu-ai-act': [
    {
      id: 'Art.14',
      title: 'Human Oversight — Consequential AI action without human control',
      description:
        'A consequential or irreversible AI-driven action occurs with no human oversight ' +
        'mechanism (confirm, approve, review), violating EU AI Act Article 14 which mandates ' +
        'effective human oversight for high-risk AI systems.',
      level: 'error',
      when: s => s.sink === 'side-effectful' && s.guardrails.humanInLoop !== true,
    },
    {
      id: 'Art.9',
      title: 'Risk Management — No output validation in risk management system',
      description:
        'Absence of output validation means the risk management system cannot verify model ' +
        'accuracy, violating EU AI Act Article 9 (risk management system throughout lifecycle).',
      level: 'error',
      when: s => s.sink !== 'internal' && !s.guardrails.validation,
    },
    {
      id: 'Art.13',
      title: 'Transparency — No confidence or uncertainty disclosure to users',
      description:
        'Model output reaches users without communicating confidence level or uncertainty, ' +
        'violating EU AI Act Article 13 (transparency and provision of information to deployers).',
      level: 'warning',
      when: s => s.sink === 'user-facing' && !s.guardrails.confidence && !s.guardrails.disclaimer,
    },
    {
      id: 'Art.17',
      title: 'Quality Management — No validation in quality management system',
      description:
        'No output validation exists to ensure model results meet quality standards, ' +
        'violating EU AI Act Article 17 (quality management system requirements).',
      level: 'warning',
      when: s => s.sink !== 'internal' && !s.guardrails.validation,
    },
    {
      id: 'Art.9-fallback',
      title: 'Risk Management — No degraded-mode fallback',
      description:
        'No fallback path for low-confidence or failed model output, violating EU AI Act ' +
        'Article 9 requirement to identify and implement risk mitigation measures.',
      level: 'warning',
      when: s => s.sink !== 'internal' && !s.guardrails.fallback,
    },
  ],

  'nist': [
    {
      id: 'MANAGE-2.2',
      title: 'MANAGE 2.2 — No human override mechanism for AI-driven action',
      description:
        'An AI-driven side-effect executes with no human override or confirmation step, ' +
        'violating NIST AI RMF MANAGE 2.2 (mechanisms for AI risk response including human override).',
      level: 'error',
      when: s => s.sink === 'side-effectful' && s.guardrails.humanInLoop !== true,
    },
    {
      id: 'MEASURE-2.5',
      title: 'MEASURE 2.5 — AI output not validated before use',
      description:
        'Model output flows to a user or action without validation, violating NIST AI RMF ' +
        'MEASURE 2.5 (AI system outputs are evaluated for accuracy, reliability, and validity).',
      level: 'error',
      when: s => s.sink !== 'internal' && !s.guardrails.validation,
    },
    {
      id: 'MEASURE-2.6',
      title: 'MEASURE 2.6 — No confidence threshold on model output',
      description:
        'No confidence or probability threshold check on model output, violating NIST AI RMF ' +
        'MEASURE 2.6 (AI system performance is monitored for trustworthiness).',
      level: 'warning',
      when: s => s.sink !== 'internal' && !s.guardrails.confidence,
    },
    {
      id: 'MANAGE-1.3',
      title: 'MANAGE 1.3 — No incident response path for AI failures',
      description:
        'No error isolation or fallback exists for AI call failures, violating NIST AI RMF ' +
        'MANAGE 1.3 (responses to identified AI risks are communicated and prioritized).',
      level: 'warning',
      when: s => s.sink !== 'internal' && !s.guardrails.errorIsolation && !s.guardrails.fallback,
    },
    {
      id: 'GOVERN-1.2',
      title: 'GOVERN 1.2 — Red AI surface violates organizational risk tolerance',
      description:
        'A red-severity AI surface (unguarded output to user or irreversible action) indicates ' +
        'AI risk exceeds acceptable tolerance, violating NIST AI RMF GOVERN 1.2 (risk tolerance ' +
        'policies are established and communicated).',
      level: 'error',
      when: s => s.severity === 'red',
    },
    {
      id: 'MAP-2.3',
      title: 'MAP 2.3 — AI-generated content lacks disclosure to end users',
      description:
        'User-facing AI output has no disclaimer, violating NIST AI RMF MAP 2.3 (scientific ' +
        'findings and organizational considerations are used to contextualize AI risk).',
      level: 'warning',
      when: s => s.sink === 'user-facing' && !s.guardrails.disclaimer,
    },
  ],

  'owasp': [
    {
      id: 'LLM08',
      title: 'LLM08: Excessive Agency — AI triggers irreversible action autonomously',
      description:
        'An LLM-driven side-effect (payment, booking, email, db/file write, shell) executes ' +
        'without human confirmation, a classic Excessive Agency failure per OWASP LLM Top 10 LLM08.',
      level: 'error',
      when: s => s.sink === 'side-effectful' && s.guardrails.humanInLoop !== true,
    },
    {
      id: 'LLM02',
      title: 'LLM02: Insecure Output Handling — Model output used without validation',
      description:
        'Model output is passed downstream (to a user, DB, shell, etc.) without validation or ' +
        'sanitization, per OWASP LLM Top 10 LLM02 (Insecure Output Handling).',
      level: 'error',
      when: s => s.sink !== 'internal' && !s.guardrails.validation,
    },
    {
      id: 'LLM09',
      title: 'LLM09: Overreliance — No confidence check or disclaimer on AI output',
      description:
        'User-facing AI output has no confidence threshold or disclaimer, risking overreliance ' +
        'on potentially incorrect model output, per OWASP LLM Top 10 LLM09 (Overreliance).',
      level: 'warning',
      when: s => s.sink === 'user-facing' && !s.guardrails.confidence && !s.guardrails.disclaimer,
    },
    {
      id: 'LLM04',
      title: 'LLM04: Model DoS — No fallback or error isolation for AI failures',
      description:
        'No fallback path or error isolation exists for AI call failures, making the system ' +
        'vulnerable to availability loss per OWASP LLM Top 10 LLM04 (Model Denial of Service).',
      level: 'warning',
      when: s => s.sink !== 'internal' && !s.guardrails.fallback && !s.guardrails.errorIsolation,
    },
  ],
};
