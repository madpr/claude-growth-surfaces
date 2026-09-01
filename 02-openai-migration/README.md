# OpenAI → Claude migration

Point Claude Code at a repo running on OpenAI. It rewrites every call site against a
rulebook, and holds the pull request until the team's own evals pass.

Medium-sized: roughly two weeks scoped to Python and the Chat Completions surface,
reusing Anthropic's existing migration kit and GitHub App. A multi-language,
multi-surface version is not two weeks.

**The bet** is that what keeps an OpenAI workload from moving is the codebase
rewrite, not model quality — remove the rewrite and workloads convert, which is new
metered revenue. There is a narrower claim underneath it worth testing on its own,
because it is much cheaper to build: that the *parity gate* is what actually unblocks
the decision. If teams migrate once they can prove no regression on their own cases,
the rewriting matters less than the proof, and the proof is a smaller product.

## Why this isn't already solved

Two of the three obvious mechanisms already ship. The Workbench prompt improver
rewrites prompts and is marketed for "prompts originally written for other AI
models." The OpenAI SDK compatibility layer already translates `tools` and
`tool_calls` server-side.

What neither does is say what was dropped. The compatibility layer's documented
behaviour is that "most unsupported fields are silently ignored rather than producing
errors" — and two of the silent ones, `response_format` and `tools[].strict`, carry
the output contract. A team evaluating Claude through the layer Anthropic recommends
for evaluation gets its schema enforcement removed, then reads the unenforced result
as the model's ceiling.

## The rulebook

Every construct that differs between the two APIs falls into one of three classes.
This taxonomy is the product: it separates what can be automated from what genuinely
needs a person, so the migration can run unattended right up to the point where it
can't.

| Class | Handling | Why |
|---|---|---|
| mechanical | applied automatically | renames and hoists the compatibility layer already performs |
| choice | pick a default, change it later | the target accepts it but someone must choose — which effort level replaces `temperature`, what happens where `strict` can't hold |
| blocking | held for review | the target cannot express it at all — schema bounds, assistant prefill |

Thirteen rules, each carrying its source link. Content is transcribed from primary
Anthropic docs, fetched 1 September 2026.

## The parity gate

This is the load-bearing part, and the reason the existing migration kit doesn't
simply apply. A language migration gates on a compiler. There is no compiler for
"does this prompt still work," so the merge gates on the project's own eval cases
instead — baseline run against migrated run, same cases, same judge.

In the seeded scan three cases regress, all from one root cause, and the pull-request
button reads *Blocked by parity* until the remedy lands. Two other cases recover,
which is why the surface reports regressed and recovered separately rather than a net
score that would hide both.

Alongside it, a cost model with editable workload assumptions. Prompt caching is
unavailable through the compatibility layer, so a like-for-like evaluation there
never surfaces it — which is why the seeded workload moves from −18% to −46% once
caching is on. That delta is the argument for migrating rather than staying on the
shim indefinitely.

## What's in here

**`app/`** — the Console surface, live at
[this link](https://claude.ai/code/artifact/13a609b1-6d14-49ac-99fe-644f4e0b29c9),
sitting under Build → Migrations next to Playground.

`src/data.js` holds the seeded scan and the rulebook, deliberately separate from the
components so the model is readable without reading UI code. Every metric on screen
is derived from it, so the tabs cannot disagree — holding rule R3 moves
auto-migratable from 87% to 74%, promotes it into blocking decisions, and re-filters
the call-sites table. `src/App.jsx` lifts that state to the root and routes on the
hash so deep links survive static hosting. `src/views/` is one file per tab.

**`prototype/migration_lint.py`** — the static analyser the rulebook came from, and
the "gap inventory" step of Anthropic's published migration methodology. It reads an
OpenAI payload and classifies every field against the compatibility layer's
documented handling, ranked by whether it changes the *result* rather than by whether
it was dropped — twenty-three ignored fields is not a finding, four that alter output
is. It then emits the native `/v1/messages` equivalent, and withholds `strict: true`
and `output_config.format` unless the schema is genuinely expressible under native
structured outputs. Promising enforcement the API can't deliver would reproduce the
exact defect this idea is about. `test_migration_lint.py` runs 28 invariants over it.

## Why this is buildable, not speculative

Anthropic already publishes a six-step methodology for large-scale code migration
with Claude Code, plus a starter kit, reporting 1M lines migrated Zig→Rust in under
two weeks with every test passing. That machinery has never been aimed at the
migration that grows API revenue.

Repo access is already solved too: the Claude GitHub App is "shared by every Claude
feature that integrates with GitHub," so this reuses the access teams already grant
for Code Review and opens a pull request the way the Action does today. No new trust
ask, no new ingestion path.

That also settles how a migration is started. The scan runs in Claude Code, not in
the Console — source never leaves the machine or the CI runner, and the Console holds
the rulebook, the decisions and the parity history:

```
$ claude /migrate-from-openai --to claude-sonnet-5

  scanning 11 files… 39 call sites
  rulebook: 34 automatic, 5 held
  → pushed to Console · Build › Migrations
```

or in CI, through the action teams already run:

```yaml
- uses: anthropics/claude-code-action@v1
  with:
    prompt: /migrate-from-openai --to claude-sonnet-5
```

The slash command is proposed, not shipped. Everything it would be built on —
the Action, the App, the migration kit — exists.

What has to change from the existing kit is the gate. It assumes a new target
language, a compiler, and a non-incremental rewrite — none of which hold here.

## Prior art

The pattern is proven, which de-risks the design and is also the sharpest objection
to it. **AWS Transform / Amazon Q Developer** ships first-party agentic migration
onto AWS. **Moderne** ships a dashboard tracking modernization campaigns that open
reviewable PRs across many repos.

Neither exists for LLM provider migration. Every provider's answer is a compatibility
shim — Anthropic's, Google's, Groq's — and the shim is the thing that fails silently.

## What would kill it

- If most OpenAI workloads are small enough that the rewrite is an afternoon, the
  switching cost isn't the barrier and the premise is wrong.
- If the parity gate can't be made trustworthy — a judge that disagrees with the
  team's own judgement — the merge gate is theatre and this is just a codemod.
- If teams won't grant repo access for this despite already granting it for Code
  Review, the distribution assumption fails.

## Evidence quality

Quotations are from primary Anthropic documentation fetched 1 September 2026 and are
reproducible from the links in the rulebook. **The prototype runs entirely on seeded
data — no repository is read and no inference is run.** The claim that developers
reach the wrong conclusion about Claude from a compatibility-layer evaluation follows
from documented behaviour but has no user report behind it. That is the first gap to
close.
