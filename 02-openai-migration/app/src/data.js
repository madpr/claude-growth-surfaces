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
// completeness: the full list expands under "Every call site". `matches` names
// the call-site labels each group covers, so the two tables are checked
// against each other at load (see the guard below callSites).
export const automatic = [
  { what: 'client = OpenAI(…) → Anthropic(…)', sites: 6, matches: ['client = OpenAI(…)'] },
  { what: 'tools[].function.parameters → input_schema', sites: 7, matches: ['tools[].function.parameters'] },
  { what: 'system messages hoisted into the system field', sites: 3, matches: ['system messages'] },
  { what: 'temperature and top_p removed (400 on current models)', sites: 3, matches: ['temperature', 'top_p'] },
  { what: 'seed, frequency_penalty dropped (no equivalent)', sites: 4, matches: ['seed', 'frequency_penalty'] },
  { what: 'stop → stop_sequences', sites: 2, matches: ['stop'] },
  { what: 'reasoning_effort → output_config.effort', sites: 1, matches: ['reasoning_effort'] },
  { what: 'strict: true carried over where the schema allows', sites: 5, matches: ['tools[].strict'] },
  { what: 'cache_control added after the stable prefix', sites: 2, matches: ['stable system + tools prefix'] },
]

export const autoSites = automatic.reduce((n, a) => n + a.sites, 0)

// What a person has to settle. Every field here is data a scan can emit --
// a construct, a count, an enum reason, a list of offending values. The only
// prose in the UI is the field labels, which are fixed and explained once.
export const decisions = [
  {
    id: 'D1',
    construct: 'response_format.json_schema',
    sites: 3,
    reason: 'Not expressible natively',
    offending: ['minimum', 'maxLength', 'maxItems'],
    failingTests: ['tc_006', 'tc_007', 'tc_010'],
    options: [
      { id: 'validate', label: 'Validate after parsing', recovers: 3, effect: 'recovers 3 tests' },
      { id: 'drop', label: 'Drop the bounds', recovers: 0, effect: 'leaves 3 failing' },
    ],
  },
  {
    id: 'D2',
    construct: 'assistant prefill',
    sites: 2,
    reason: 'Rejected by target model',
    offending: ['400 on claude-sonnet-5'],
    failingTests: [],
    options: [
      { id: 'format', label: 'output_config.format', recovers: 0, effect: 'schema enforced' },
      { id: 'instruct', label: 'System instruction', recovers: 0, effect: 'no schema guarantee' },
    ],
  },
]

export const decisionSites = decisions.reduce((n, d) => n + d.sites, 0)

// The gate. A compiler cannot tell you whether a prompt still works, so the
// merge waits on the repo's own tests.
export const tests = { total: 12, baseline: 10, regressed: 3, recovered: 2 }

// Each option states how many failing tests it recovers, so the number on the
// page is summed from the choices rather than narrated.
export function testsAfter(choices) {
  const recovered = decisions.reduce((n, d) => {
    const picked = d.options.find((o) => o.id === choices[d.id])
    return n + (picked ? picked.recovers : 0)
  }, 0)
  return tests.total - tests.regressed + recovered
}

// Settled decisions whose chosen option leaves tests failing that another
// option of the same decision would recover. The status bar names them and
// the decision card marks them, both from this list rather than by construct.
export function blocking(choices) {
  return decisions.flatMap((d) => {
    const picked = d.options.find((o) => o.id === choices[d.id])
    if (!picked) return []
    const better = d.options.reduce((a, b) => (b.recovers > a.recovers ? b : a))
    if (better.recovers <= picked.recovers) return []
    return [{ decision: d, picked, better, left: d.failingTests.length - picked.recovers }]
  })
}

// Public list prices per million tokens, 1 September 2026. An illustration on
// the seeded workload, not a measurement of any account.
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

// Progressive detail: shown only when someone asks for it. Every call site the
// scan found, one row each. The header count is this table's length.
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
  ['src/triage/tools.py', 47, 'tools[].function.parameters', 'auto'],
  ['src/triage/tools.py', 54, 'tools[].strict', 'auto'],
  ['src/triage/tools.py', 68, 'tools[].function.parameters', 'auto'],
  ['src/ingest/webhook.py', 38, 'client = OpenAI(…)', 'auto'],
  ['src/ingest/webhook.py', 66, 'temperature', 'auto'],
  ['src/ingest/webhook.py', 91, 'frequency_penalty', 'auto'],
  ['src/ingest/backfill.py', 17, 'client = OpenAI(…)', 'auto'],
  ['src/ingest/backfill.py', 42, 'seed', 'auto'],
  ['src/agents/router.py', 12, 'client = OpenAI(…)', 'auto'],
  ['src/agents/router.py', 24, 'stable system + tools prefix', 'auto'],
  ['src/agents/router.py', 33, 'reasoning_effort', 'auto'],
  ['src/agents/router.py', 51, 'tools[].function.parameters', 'auto'],
  ['src/agents/router.py', 58, 'tools[].strict', 'auto'],
  ['src/agents/router.py', 72, 'assistant prefill', 'D2'],
  ['src/agents/summarize.py', 9, 'client = OpenAI(…)', 'auto'],
  ['src/agents/summarize.py', 18, 'system messages', 'auto'],
  ['src/agents/summarize.py', 29, 'assistant prefill', 'D2'],
  ['src/agents/summarize.py', 41, 'frequency_penalty', 'auto'],
  ['src/agents/summarize.py', 52, 'stop', 'auto'],
  ['tests/conftest.py', 8, 'client = OpenAI(…)', 'auto'],
  ['tests/conftest.py', 23, 'tools[].function.parameters', 'auto'],
  ['tests/test_classify.py', 21, 'response_format.json_schema', 'D1'],
]

// Guard. The summary counts and the call-site table are two views of one scan.
// If they disagree, throw at load rather than publish a page that says one
// number in the header and lists another in the table.
;(() => {
  const count = (pred) => callSites.filter(pred).length
  const problems = []
  for (const a of automatic) {
    const n = count(([, , what, owner]) => owner === 'auto' && a.matches.includes(what))
    if (n !== a.sites) problems.push(`"${a.what}": summary says ${a.sites}, table lists ${n}`)
  }
  for (const d of decisions) {
    const n = count(([, , , owner]) => owner === d.id)
    if (n !== d.sites) problems.push(`${d.id}: summary says ${d.sites}, table lists ${n}`)
  }
  const known = new Set(automatic.flatMap((a) => a.matches))
  for (const [file, line, what, owner] of callSites) {
    if (owner === 'auto' && !known.has(what)) problems.push(`${file}:${line} "${what}" matches no automatic rule`)
    if (owner !== 'auto' && !decisions.some((d) => d.id === owner)) problems.push(`${file}:${line} owner ${owner} is not a decision`)
  }
  const autoRows = count(([, , , owner]) => owner === 'auto')
  if (autoRows !== autoSites) problems.push(`automatic: summary says ${autoSites}, table lists ${autoRows}`)
  const files = new Set(callSites.map(([file]) => file)).size
  if (files !== project.files) problems.push(`files: project says ${project.files}, table spans ${files}`)
  if (problems.length) throw new Error(`data.js is inconsistent: ${problems.join('; ')}`)
})()

export const totalSites = callSites.length
