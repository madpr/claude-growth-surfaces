// Seeded migration scenario. Everything on screen derives from this module, so
// the headline metrics and the tables cannot disagree.
//
// The scenario is a support-triage service running on the OpenAI Chat
// Completions API. Rule content is transcribed from primary Anthropic
// documentation (fetched 1 September 2026) -- see `docs` on each rule.

export const project = {
  name: 'support-triage',
  repo: 'acme/support-triage',
  language: 'Python',
  source: 'openai-python 1.54',
  target: 'claude-sonnet-5',
  branch: 'migrate/claude',
  scannedAt: '3h ago',
  files: 11,
}

// ---------------------------------------------------------------- rulebook
//
// `mode` is the migration decision. 'auto' means the rewrite is mechanical.
// 'decide' means a human has to choose, because the target is not a superset
// of the source. Toggling a rule reclassifies every call site bound to it.

export const rules = [
  {
    id: 'R1',
    construct: 'Multiple system / developer messages',
    equivalent: 'Hoisted into the single `system` field',
    mode: 'auto',
    note: 'The compatibility layer already concatenates these with newlines. Native keeps position via mid-conversation system messages.',
    docs: 'https://platform.claude.com/docs/en/cli-sdks-libraries/libraries/openai-sdk',
  },
  {
    id: 'R2',
    construct: 'tools[].function.parameters',
    equivalent: 'tools[].input_schema',
    mode: 'auto',
    note: 'Field rename only. Name and description carry over unchanged.',
    docs: 'https://platform.claude.com/docs/en/build-with-claude/structured-outputs',
  },
  {
    id: 'R3',
    construct: 'tools[].strict',
    equivalent: 'strict: true — only if the schema is expressible',
    mode: 'auto',
    choice: {
      label: 'Where the schema is not expressible',
      options: ['Drop strict', 'Relax the schema'],
      value: 'Drop strict',
    },
    note: 'Silently ignored by the compatibility layer, so tool arguments stop being schema-guaranteed with no error. Native supports it, but not for schemas using numeric bounds or string lengths.',
    docs: 'https://platform.claude.com/docs/en/build-with-claude/structured-outputs',
  },
  {
    id: 'R4',
    construct: 'response_format.json_schema',
    equivalent: 'output_config.format',
    mode: 'decide',
    note: 'Ignored by the compatibility layer. Native structured outputs reject minimum, maximum, maxLength, maxItems and uniqueItems — constraints have to move into your own validation.',
    docs: 'https://platform.claude.com/docs/en/build-with-claude/structured-outputs',
  },
  {
    id: 'R5',
    construct: 'temperature',
    equivalent: 'Removed — use output_config.effort',
    mode: 'auto',
    choice: {
      label: 'Effort level to substitute',
      options: ['low', 'medium', 'high'],
      value: 'low',
    },
    note: 'Accepted by the compatibility layer (values above 1 are capped) but returns 400 on current models. Pick an effort level per call site.',
    docs: 'https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices',
  },
  {
    id: 'R6',
    construct: 'top_p',
    equivalent: 'Removed',
    mode: 'auto',
    note: 'Sampling parameters were removed on the current generation. Drop it.',
    docs: 'https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices',
  },
  {
    id: 'R7',
    construct: 'Assistant prefill (trailing assistant turn)',
    equivalent: 'output_config.format, or a system instruction',
    mode: 'decide',
    note: 'Returns 400 on current models. The compatibility layer accepts it, so this failure only appears after you migrate off it.',
    docs: 'https://platform.claude.com/docs/en/build-with-claude/structured-outputs',
  },
  {
    id: 'R8',
    construct: 'seed',
    equivalent: 'Removed',
    mode: 'auto',
    note: 'No equivalent. Reproducibility comes from a fixed prompt and a fixed effort level.',
    docs: 'https://platform.claude.com/docs/en/cli-sdks-libraries/libraries/openai-sdk',
  },
  {
    id: 'R9',
    construct: 'frequency_penalty / presence_penalty',
    equivalent: 'A system-prompt instruction',
    mode: 'auto',
    choice: {
      label: 'Replacement',
      options: ['Add an anti-repetition instruction', 'Drop entirely'],
      value: 'Add an anti-repetition instruction',
    },
    note: 'Ignored by the compatibility layer, so repetition tuning silently stops applying. Needs a prompt-level replacement you write.',
    docs: 'https://platform.claude.com/docs/en/cli-sdks-libraries/libraries/openai-sdk',
  },
  {
    id: 'R10',
    construct: 'reasoning_effort',
    equivalent: 'output_config.effort',
    mode: 'auto',
    note: 'Direct mapping: minimal and low to low, medium to medium, high to high.',
    docs: 'https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices',
  },
  {
    id: 'R11',
    construct: 'Stable system + tools prefix',
    equivalent: 'cache_control breakpoint',
    mode: 'auto',
    gain: true,
    note: 'Prompt caching is unavailable through the compatibility layer, so it never shows up in a like-for-like cost comparison. This is where the migration pays for itself.',
    docs: 'https://platform.claude.com/docs/en/build-with-claude/prompt-caching',
  },
  {
    id: 'R12',
    construct: 'stop',
    equivalent: 'stop_sequences',
    mode: 'auto',
    note: 'Carries over. Whitespace-only sequences do not take effect and are dropped.',
    docs: 'https://platform.claude.com/docs/en/cli-sdks-libraries/libraries/openai-sdk',
  },
  {
    id: 'R13',
    construct: 'client = OpenAI(...)',
    equivalent: 'client = Anthropic(...)',
    mode: 'auto',
    note: 'Constructor and call-site rename, including max_completion_tokens to max_tokens.',
    docs: 'https://platform.claude.com/docs/en/api/overview',
  },
]

// -------------------------------------------------------------- call sites
//
// Each site is bound to a rule. Its status is derived from that rule's mode,
// so changing a decision in the Rulebook tab reclassifies sites here.

export const callSites = [
  { file: 'src/triage/client.py', line: 14, symbol: 'build_client', rule: 'R13' },
  { file: 'src/triage/client.py', line: 31, symbol: 'build_client', rule: 'R11' },
  { file: 'src/triage/client.py', line: 48, symbol: '_defaults', rule: 'R5' },
  { file: 'src/triage/client.py', line: 52, symbol: '_defaults', rule: 'R6' },
  { file: 'src/triage/client.py', line: 55, symbol: '_defaults', rule: 'R8' },
  { file: 'src/triage/classify.py', line: 27, symbol: 'classify_ticket', rule: 'R1' },
  { file: 'src/triage/classify.py', line: 41, symbol: 'classify_ticket', rule: 'R4' },
  { file: 'src/triage/classify.py', line: 63, symbol: 'classify_ticket', rule: 'R2' },
  { file: 'src/triage/classify.py', line: 71, symbol: 'classify_ticket', rule: 'R3' },
  { file: 'src/triage/classify.py', line: 88, symbol: 'classify_ticket', rule: 'R12' },
  { file: 'src/triage/classify.py', line: 104, symbol: 'retry_classify', rule: 'R13' },
  { file: 'src/triage/escalate.py', line: 19, symbol: 'escalate', rule: 'R2' },
  { file: 'src/triage/escalate.py', line: 26, symbol: 'escalate', rule: 'R3' },
  { file: 'src/triage/escalate.py', line: 44, symbol: 'escalate', rule: 'R1' },
  { file: 'src/triage/escalate.py', line: 58, symbol: 'escalate', rule: 'R13' },
  { file: 'src/triage/schemas.py', line: 12, symbol: 'TriageResult', rule: 'R4' },
  { file: 'src/triage/schemas.py', line: 34, symbol: 'AccountLookup', rule: 'R2' },
  { file: 'src/triage/tools.py', line: 22, symbol: 'lookup_account', rule: 'R2' },
  { file: 'src/triage/tools.py', line: 29, symbol: 'lookup_account', rule: 'R3' },
  { file: 'src/triage/tools.py', line: 47, symbol: 'escalate_tool', rule: 'R2' },
  { file: 'src/triage/tools.py', line: 54, symbol: 'escalate_tool', rule: 'R3' },
  { file: 'src/ingest/webhook.py', line: 38, symbol: 'handle_event', rule: 'R13' },
  { file: 'src/ingest/webhook.py', line: 52, symbol: 'handle_event', rule: 'R1' },
  { file: 'src/ingest/webhook.py', line: 66, symbol: 'handle_event', rule: 'R5' },
  { file: 'src/ingest/webhook.py', line: 91, symbol: 'summarise', rule: 'R9' },
  { file: 'src/ingest/backfill.py', line: 24, symbol: 'replay_batch', rule: 'R13' },
  { file: 'src/ingest/backfill.py', line: 40, symbol: 'replay_batch', rule: 'R11' },
  { file: 'src/ingest/backfill.py', line: 57, symbol: 'replay_batch', rule: 'R8' },
  { file: 'src/agents/router.py', line: 33, symbol: 'route', rule: 'R10' },
  { file: 'src/agents/router.py', line: 45, symbol: 'route', rule: 'R2' },
  { file: 'src/agents/router.py', line: 72, symbol: 'route', rule: 'R7' },
  { file: 'src/agents/summarize.py', line: 18, symbol: 'summarize_thread', rule: 'R13' },
  { file: 'src/agents/summarize.py', line: 29, symbol: 'summarize_thread', rule: 'R7' },
  { file: 'src/agents/summarize.py', line: 41, symbol: 'summarize_thread', rule: 'R9' },
  { file: 'src/agents/summarize.py', line: 60, symbol: 'summarize_thread', rule: 'R12' },
  { file: 'tests/test_classify.py', line: 21, symbol: 'test_billing_case', rule: 'R4' },
  { file: 'tests/test_classify.py', line: 48, symbol: 'test_outage_case', rule: 'R13' },
  { file: 'tests/test_tools.py', line: 16, symbol: 'test_lookup_schema', rule: 'R3' },
  { file: 'tests/test_tools.py', line: 39, symbol: 'test_escalate_schema', rule: 'R2' },
]

export const ruleById = Object.fromEntries(rules.map((r) => [r.id, r]))

// A call site needs a human decision when the rule it is bound to does.
export function siteStatus(site, modes) {
  return modes[site.rule] === 'decide' ? 'decide' : 'auto'
}

// Which of the three rulebook classes a rule currently falls in. This is
// derived from the live decision, not stored, so holding a rule reclassifies
// every site bound to it.
export function classOf(rule, modes) {
  if (modes[rule.id] === 'decide') return 'blocking'
  return rule.choice ? 'choice' : 'mechanical'
}

// Call sites grouped by class -- the composition behind the headline count.
export function composition(modes) {
  const out = { mechanical: 0, choice: 0, blocking: 0 }
  for (const site of callSites) out[classOf(ruleById[site.rule], modes)] += 1
  return out
}

// Open decisions broken down by the rule holding them up.
export function openDecisions(modes) {
  return rules
    .filter((r) => modes[r.id] === 'decide')
    .map((r) => ({ id: r.id, sites: callSites.filter((c) => c.rule === r.id).length }))
}

export function summarise(modes) {
  const total = callSites.length
  const decide = callSites.filter((s) => siteStatus(s, modes) === 'decide').length
  return {
    total,
    decide,
    auto: total - decide,
    autoPct: Math.round(((total - decide) / total) * 100),
  }
}

// ------------------------------------------------------------------- cost
//
// Public list prices per million tokens, 1 September 2026.

export const pricing = {
  'gpt-4o': { input: 2.5, output: 10.0 },
  'claude-sonnet-5': { input: 2.0, output: 10.0, cacheWrite: 2.5, cacheRead: 0.2 },
}

export const workload = {
  requestsPerDay: 12400,
  stablePrefixTokens: 2600,
  variableInputTokens: 600,
  outputTokens: 180,
  cacheHitRate: 0.71,
}

export function costModel(w) {
  const o = pricing['gpt-4o']
  const c = pricing['claude-sonnet-5']
  const M = 1_000_000
  const totalIn = w.stablePrefixTokens + w.variableInputTokens

  const source = (totalIn * o.input + w.outputTokens * o.output) / M

  const hit =
    (w.stablePrefixTokens * c.cacheRead +
      w.variableInputTokens * c.input +
      w.outputTokens * c.output) / M
  const miss =
    (w.stablePrefixTokens * c.cacheWrite +
      w.variableInputTokens * c.input +
      w.outputTokens * c.output) / M

  const uncached = (totalIn * c.input + w.outputTokens * c.output) / M
  const target = hit * w.cacheHitRate + miss * (1 - w.cacheHitRate)

  return {
    source,
    uncached,
    target,
    deltaPct: Math.round(((target - source) / source) * 100),
    monthlySource: source * w.requestsPerDay * 30,
    monthlyTarget: target * w.requestsPerDay * 30,
  }
}

// ----------------------------------------------------------------- parity
//
// The eval gate. A compiler cannot tell you whether a prompt still works, so
// the migration is gated on the project's own cases instead.

export const parityCases = [
  { id: 'tc_001', name: 'Billing discrepancy, known account', before: 'pass', after: 'pass' },
  { id: 'tc_002', name: 'Outage report, data loss language', before: 'pass', after: 'pass' },
  { id: 'tc_003', name: 'Feature request, low severity', before: 'pass', after: 'pass' },
  { id: 'tc_004', name: 'Unknown account, escalation path', before: 'fail', after: 'pass' },
  { id: 'tc_005', name: 'Multi-tool: lookup then escalate', before: 'pass', after: 'pass' },
  { id: 'tc_006', fixedBy: 'R4', name: 'Severity clamp at schema bound', before: 'pass', after: 'fail' },
  { id: 'tc_007', fixedBy: 'R4', name: 'Summary exceeds 280 characters', before: 'pass', after: 'fail' },
  { id: 'tc_008', name: 'Empty ticket body', before: 'pass', after: 'pass' },
  { id: 'tc_009', name: 'Non-English ticket', before: 'fail', after: 'pass' },
  { id: 'tc_010', fixedBy: 'R4', name: 'Tag list exceeds five entries', before: 'pass', after: 'fail' },
  { id: 'tc_011', name: 'Prompt-injection attempt in body', before: 'pass', after: 'pass' },
  { id: 'tc_012', name: 'Duplicate webhook replay', before: 'pass', after: 'pass' },
]

export const parityNote =
  'All three regressions share one root cause: native structured outputs cannot express minimum, maxLength or maxItems, so the bounds silently stopped being enforced. Moving them into application validation clears all three.'

// Applying the R4 remedy — move the unexpressible constraints into your own
// validation — clears every case that regressed because of it.
export function parityResults(fixApplied) {
  return parityCases.map((c) => ({
    ...c,
    result: fixApplied && c.fixedBy === 'R4' ? 'pass' : c.after,
  }))
}

export function parityScore(fixApplied) {
  const rows = parityResults(fixApplied)
  return {
    before: parityCases.filter((c) => c.before === 'pass').length,
    after: rows.filter((c) => c.result === 'pass').length,
    total: parityCases.length,
    // Net movement hides the shape: cases can regress and recover at once.
    regressed: rows.filter((c) => c.before === 'pass' && c.result === 'fail').length,
    recovered: rows.filter((c) => c.before === 'fail' && c.result === 'pass').length,
  }
}

