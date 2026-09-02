# Deep-research triage

Source: a Google deep-research report, "Strategic Growth Levers for Claude Console:
Activation, Ecosystem, and Enterprise Expansion." Nine proposed initiatives, sized
Small / Medium / Large.

Triaged 2 September 2026 against primary `platform.claude.com` documentation.

## Verdict on the source

Useful as an idea checklist. Unusable as evidence.

- **The citations are mostly content farms.** `aipricing.guru`, `metacto.com`,
  `checkthat.ai`, `aitoolsofthetrade.com`, `digitalapplied.com`, `saashero.net`,
  `youngcopy.com`. Citation 9, supporting a claim about URL schemas for deep links,
  is an MDN page titled "Test your skills: HTML images."
- **The model references are stale and internally inconsistent.** One document names
  "Claude 3.5 Sonnet", "Sonnet 4.6", "Opus 4.7", and "Opus 4.8". The current family is
  Opus 5 / Sonnet 5 / Haiku 4.5 / Fable 5.1. Its "$3.00 per million" input figure is
  Sonnet 4.6's price; Sonnet 5 is $2.00.
- **Every benchmark figure traces to a marketing blog**, not primary research: TTFAC
  under 90 seconds, 80–95% abandonment past 10 minutes of setup, 68% citing setup time,
  K-factor 0.3–0.7, PQL conversion 25–30%. None of them enter this repo.
- **It does not check whether the things it proposes already exist.** Two of the nine
  are already shipped, in one case as the exact feature described.

What it did supply: the pointer to prompt caching as a growth surface, and one usable
citation — a Reddit thread titled "Spent a week assuming my prompt caching was working."
That thread is the only lead in 45 citations that survived, and it pointed at a real
failure with a real corpus behind it.

## The nine

| # | Size | Idea | Verdict |
|---|---|---|---|
| 1 | S | "Open in Playground" deep links + GitHub badges | **Not pursued.** Could not confirm either way whether Console deep links exist; the pattern ships for Claude Code (`code.claude.com/docs/en/deep-links`) and Claude Desktop. Theme collides with the M's acquisition hypothesis, and `01-dev-to-production` ranks activation as the tail of the revenue chain, not the head |
| 2 | S | Automated cache-miss diagnostics and nudges | **Taken, reshaped.** See below |
| 3 | S | Ephemeral "Hello World" sandbox pre-fills | **Not pursued.** Already a dead end in `01-dev-to-production`. The doc does route around one objection — the key *is* visible at creation, so the modal is the one place a prefilled snippet works — but the reason it died was the weak revenue chain, which the doc does not address |
| 4 | M | Shareable prompt evaluation workspaces | **Not pursued.** The viral-loop case rests entirely on K-factor benchmarks sourced to marketing blogs. Might be a real idea; nothing here establishes it |
| 5 | M | OpenAI-to-Claude migration adapter | **Already built here,** independently, as `02-openai-migration`. Mild validation that the idea is findable. Changes nothing: the doc's version stops at prompt and schema translation, both of which already ship (the Workbench prompt improver, the OpenAI SDK compatibility layer). The parity gate is the differentiator and the doc does not have it |
| 6 | M | Workspace PQL scoring engine | **Not pursued.** Internal sales tooling, not a platform surface. Nothing about it is checkable from outside, so it cannot be held to this repo's standard |
| 7 | L | Native MCP server directory + 1-click deploy | **Not pursued.** Its adoption statistics come from `nordicapis.com` and `digitalapplied.com`. MCP tunnels, which it treats as a component to build, already ship |
| 8 | L | Claude Code CLI / Console telemetry unification | **Not pursued as an idea; one lead extracted.** Overlaps both `bonus-billing-attribution` and the L. The useful part is the evidence lead it cites — `anthropics/claude-code#67083` on Console credit-balance confusion — which belongs in the bonus item's corpus, not in a new slate entry |
| 9 | L | Zero-setup hosted evaluation datasets | **Not pursued.** Plausible and expensive. No verification attempted; recorded so it is not re-derived |

## What happened to #2

The doc proposes building cache-miss diagnosis from scratch: detect a zero-hit
workload, then "analyze the last several payload hashes, visually highlighting the
exact token difference."

That feature exists. **Cache diagnostics** (beta header `cache-diagnosis-2026-04-07`)
compares consecutive requests server-side and returns a typed `cache_miss_reason` —
`model_changed`, `system_changed`, `tools_changed`, `messages_changed` — with a
`cache_missed_input_tokens` estimate. It has shipped since April 2026.

The detection data exists too. The Usage Report API already returns
`cache_creation.ephemeral_5m_input_tokens`, `cache_creation.ephemeral_1h_input_tokens`,
`cache_read_input_tokens` and `uncached_input_tokens`, grouped by `api_key_id`,
`workspace_id` and `model`, in buckets as fine as `1m`.

So the proposal as written is redundant. What is left after removing the parts that
already ship is smaller, cheaper, and a better idea: **both halves exist and nothing
connects them.** Detection is data nobody is looking at. Diagnosis is opt-in, requires
the beta header on every request, and therefore only answers developers who already
suspected the question.

That gap is `03-cache-breakeven`.
