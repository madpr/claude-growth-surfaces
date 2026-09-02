// Seeded migration scenario. One screen reads from this, so the numbers on the
// page and the numbers in the detail tables cannot drift apart.
//
// Rule content is transcribed from primary Anthropic documentation, fetched
// 1 September 2026.

export const project = {
  name: 'support-triage',
  repo: 'acme/support-triage',
  files: 11,
  source: 'openai-python',
  target: 'claude-sonnet-5',
  scannedAt: '3h ago',
}

// What the migration rewrites without asking. Grouped for reading, not for
// completeness -- the full list expands under "the 39 call sites".
export const automatic = [
  { what: 'client = OpenAI(…) → Anthropic(…)', sites: 6 },
  { what: 'tools[].function.parameters → input_schema', sites: 7 },
  { what: 'system messages hoisted into the system field', sites: 3 },
  { what: 'temperature and top_p removed (400 on current models)', sites: 3 },
  { what: 'seed, frequency_penalty dropped (no equivalent)', sites: 4 },
  { what: 'stop → stop_sequences', sites: 2 },
  { what: 'reasoning_effort → output_config.effort', sites: 1 },
  { what: 'strict: true carried over where the schema allows', sites: 5 },
  { what: 'cache_control added after the stable prefix', sites: 2 },
]

export const autoSites = automatic.reduce((n, a) => n + a.sites, 0)

// What a person has to settle. The target is not a superset of the source, so
// these cannot be resolved mechanically.
export const decisions = [
  {
    id: 'D1',
    title: 'Schema bounds native structured outputs cannot express',
    sites: 3,
    detail:
      'Your triage schema uses minimum, maxLength and maxItems. Native structured outputs reject all three, so the bounds stop being enforced. Three eval cases depend on them.',
    docs: 'https://platform.claude.com/docs/en/build-with-claude/structured-outputs',
    options: [
      { id: 'validate', label: 'Validate after parsing', effect: 'Keeps enforcement, in your code instead of the schema. Clears all three cases.', fixesParity: true },
      { id: 'drop', label: 'Drop the bounds', effect: 'Less code, but those three cases keep failing.', fixesParity: false },
    ],
  },
  {
    id: 'D2',
    title: 'Assistant prefill',
    sites: 2,
    detail:
      'Two call sites end on an assistant turn to force a JSON opening brace. That returns 400 on claude-sonnet-5. The compatibility layer accepts it, so this only surfaces once you leave it.',
    docs: 'https://platform.claude.com/docs/en/build-with-claude/structured-outputs',
    options: [
      { id: 'format', label: 'Use output_config.format', effect: 'The model is constrained to the schema directly.', fixesParity: true },
      { id: 'instruct', label: 'Instruct in the system prompt', effect: 'No schema guarantee, but no schema to write either.', fixesParity: true },
    ],
  },
]

export const decisionSites = decisions.reduce((n, d) => n + d.sites, 0)
export const totalSites = autoSites + decisionSites

// The gate. A compiler cannot tell you whether a prompt still works, so the
// merge waits on the repo's own tests.
export const tests = { total: 12, baseline: 10, regressed: 3, recovered: 2 }

export function testsAfter(choices) {
  const fixed = decisions.every((d) => {
    const picked = d.options.find((o) => o.id === choices[d.id])
    return picked ? picked.fixesParity : false
  })
  return fixed ? tests.total : tests.total - tests.regressed
}

// Public list prices per million tokens, 1 September 2026.
export const cost = (() => {
  const reqPerDay = 12400
  const stable = 2600, variable = 600, out = 180
  const M = 1e6
  const gpt = (((stable + variable) * 2.5) + out * 10) / M
  const hit = (stable * 0.2 + variable * 2 + out * 10) / M
  const miss = (stable * 2.5 + variable * 2 + out * 10) / M
  const claude = hit * 0.71 + miss * 0.29
  return {
    sourceMonth: gpt * reqPerDay * 30,
    targetMonth: claude * reqPerDay * 30,
    deltaPct: Math.round(((claude - gpt) / gpt) * 100),
  }
})()

// Progressive detail: shown only when someone asks for it.
export const callSites = [
  ['src/triage/client.py', 14, 'client = OpenAI(…)', 'auto'],
  ['src/triage/client.py', 31, 'stable system + tools prefix', 'auto'],
  ['src/triage/client.py', 48, 'temperature', 'auto'],
  ['src/triage/client.py', 52, 'top_p', 'auto'],
  ['src/triage/client.py', 55, 'seed', 'auto'],
  ['src/triage/classify.py', 27, 'system messages', 'auto'],
  ['src/triage/classify.py', 41, 'response_format.json_schema', 'D1'],
  ['src/triage/classify.py', 63, 'tools[].function.parameters', 'auto'],
  ['src/triage/classify.py', 71, 'tools[].strict', 'auto'],
  ['src/triage/classify.py', 88, 'stop', 'auto'],
  ['src/triage/escalate.py', 19, 'tools[].function.parameters', 'auto'],
  ['src/triage/escalate.py', 26, 'tools[].strict', 'auto'],
  ['src/triage/escalate.py', 44, 'system messages', 'auto'],
  ['src/triage/schemas.py', 12, 'response_format.json_schema', 'D1'],
  ['src/triage/tools.py', 22, 'tools[].function.parameters', 'auto'],
  ['src/triage/tools.py', 29, 'tools[].strict', 'auto'],
  ['src/ingest/webhook.py', 38, 'client = OpenAI(…)', 'auto'],
  ['src/ingest/webhook.py', 66, 'temperature', 'auto'],
  ['src/ingest/webhook.py', 91, 'frequency_penalty', 'auto'],
  ['src/agents/router.py', 33, 'reasoning_effort', 'auto'],
  ['src/agents/router.py', 72, 'assistant prefill', 'D2'],
  ['src/agents/summarize.py', 29, 'assistant prefill', 'D2'],
  ['src/agents/summarize.py', 41, 'frequency_penalty', 'auto'],
  ['tests/test_classify.py', 21, 'response_format.json_schema', 'D1'],
]
