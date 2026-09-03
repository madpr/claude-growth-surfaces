# OpenAI → Claude migration

Point Claude Code at a repo that uses the OpenAI SDK. It rewrites every call site,
then blocks the pull request until your tests still pass.

The rewrite is what blocks migration, not model quality. Remove it and workloads move,
which adds metered revenue. A narrower claim is cheaper to test: the parity gate alone
unblocks the decision. If teams migrate once they can prove no regression, build the
gate and skip the rewriter.

[Open the prototype](https://madpr.github.io/claude-growth-surfaces/) — one screen: 33
call sites rewritten for you, 5 decisions only you can make, and whether your tests
still pass. Settle both decisions and the merge unblocks.

## Why this isn't solved already

Most of it already ships. The OpenAI SDK compatibility layer translates `tools` and
`tool_calls` server-side. The Claude GitHub App already has repo access, granted for
Code Review. The Console's prompt improver handles the prose half, and is marketed for
"prompts originally written for other AI models."[^1]

What's missing is telling you what broke. The compatibility layer "silently ignores"
most unsupported fields, and two of them carry your output contract: `response_format`
and `tools[].strict`. Evaluate Claude through the layer Anthropic recommends for
evaluation and you lose schema enforcement, then read the unenforced result as the
model's ceiling. Prompt caching is unsupported there too, so the cost saving that
justifies migrating — 46% on the seeded workload, most of it from caching — is
invisible from the place you'd measure it.

## The parity gate

A language migration gates on a compiler. No compiler tells you whether a prompt still
works, so the merge gates on the repo's own test suite instead: it already passes on
OpenAI, so that's the baseline, and it has to still pass on Claude.

This is why Anthropic's published migration kit doesn't apply unchanged — it assumes a
new target language, a compiler, and a non-incremental rewrite. None hold here.

## Cost to build

| Milestone | Ships | Reuses |
|---|---|---|
| 1. Skill — 2–3 days | `/migrate-from-openai`: rulebook, scan, rewrite, tests-green gate, HTML report | The migration kit's templates and queue runner |
| 2. Console — the rest | Decisions that persist, org view, PR status check, funnel metrics | Console components, the Claude GitHub App, the repo's own CI |

About two weeks total, Python and Chat Completions only. Ship milestone 1 first: it
runs locally, needs no account, and is a complete product. Milestone 2 buys
measurement — every metric below is uncollectible from a local skill that prints HTML.

## Success metrics

- **Merged migrations per quarter.** Whether workloads actually move.
- **Metered spend 90 days after merge**, against the account's pre-migration baseline.
- **Scan → merged PR.** Where the funnel leaks. Below 40% means the report isn't enough.

One guardrail can kill the product: **production regressions after a passing gate**
should be ~0. A gate that passes bad migrations is worse than no gate.

## Risks

- Most OpenAI workloads are small enough to port in an afternoon, so switching cost
  isn't the barrier and the premise is wrong.
- The gate can't be trusted, and this reduces to a codemod.
- Targeting isn't possible. The Usage and Cost APIs group by `model`, `workspace_id`,
  `api_key_id` and similar — no endpoint dimension — so nothing public separates
  `/v1/chat/completions` from `/v1/messages`. Without it, milestone 2 loses its
  strongest justification and the skill has to be found rather than offered.

AWS Transform and Moderne prove the pattern works at enterprise scale. Neither exists
for LLM provider migration; every provider ships a compatibility shim instead.

## Evidence

Quotations come from Anthropic documentation fetched on 1 September 2026.

The prototype runs on seeded data. It reads no repository and runs no inference.

No user report backs the claim that developers reach the wrong conclusion from a
compatibility-layer evaluation. It follows from documented behaviour. Close that gap
first.

[^1]: Verify before submitting. The dedicated docs page for the Console prompting
tools now redirects to the general prompting guide, and the Console's Build section
lists Playground, Files, Skills and Batches — no Workbench, which is where the
improver used to live. If it has been retired, the gap this idea addresses is larger,
not smaller.
