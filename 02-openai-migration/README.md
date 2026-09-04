# Move OpenAI workloads to Claude

Point Claude Code at a repository that uses the OpenAI SDK. It rewrites every call
site, then blocks the pull request until the repository's own tests still pass.

The rewrite isn't what stops teams from switching, and neither is model quality. What
stops them is that nobody can prove the switch is safe, so the parity gate is the part
worth building.

**Status:** designed, working prototype.
**Cost:** ~2 weeks.
**Theme:** acquisition.

[Open the prototype](https://madpr.github.io/claude-growth-surfaces/migrations/) — one screen: 33
call sites rewritten, 5 decisions only a person can make, and whether the tests still
pass. Settle both decisions and the merge unblocks.

## Problem

A team evaluating Claude can translate their code in an afternoon. What they can't do
is show their reviewer that the translation didn't change behavior. A language
migration gates on a compiler. No compiler tells you whether a prompt still works, so
the decision stalls in review and the workload stays where it is.

### What already ships

Most of what an outsider would propose building is already there:

- The OpenAI SDK compatibility layer translates tool definitions and tool calls
  server-side.
- The Claude GitHub App already has repository access, granted for code review.

One thing that used to exist is gone. The Console's prompt improver handled the prose
half of a migration. It's been retired: no Workbench in the navigation, and its
documentation page now redirects to the general prompting guide.

### What's missing

**Nothing tells you what broke.** The compatibility layer silently ignores most
unsupported fields, and two of them carry the output contract: the structured-output
format and strict tool schemas. A team that evaluates Claude through the layer
Anthropic recommends for evaluation loses schema enforcement, then reads the
unenforced result as the model's ceiling.

**The cost case is invisible from the place you'd measure it.** Prompt caching isn't
supported through the compatibility layer either. On the seeded workload, most of a 46%
saving comes from caching — none of which shows up in an evaluation run through the
layer.

**Prompt tuning is nobody's job.** Anthropic's own documentation warns that a prompt
"well-tuned to OpenAI specifically" degrades on Claude, and the tool that fixed that has
been retired.

## Goals

- Let a team prove a migration didn't regress, using evidence their reviewer already
  trusts.
- Move the decision out of review and into a check.
- Convert evaluation traffic into production traffic.

## Non-goals

- Rewriting prompts silently. An unreviewable prose change is the last thing anyone
  wants in a migration pull request.
- Covering every language and endpoint. The first version is Python and Chat
  Completions.
- Replacing the compatibility layer. It's the right on-ramp; it's the wrong place to
  evaluate from.

## Proposed experience

A developer points the tool at their repository. It produces three things:

1. **The mechanical rewrite.** Every call site that translates cleanly, translated.
2. **The decisions.** Anything a person has to judge, surfaced rather than guessed —
   prompts that look OpenAI-tuned, and fields whose behavior changes.
3. **The gate.** The repository's own test suite already passes against OpenAI. That's
   the baseline. The pull request stays blocked until it passes against Claude too.

The gate is the part worth building. Scanning and rewriting already work; proving
behavior held does not.

This is why Anthropic's published migration kit doesn't apply unchanged. It assumes a
new target language, a compiler, and a non-incremental rewrite. None of those hold here.

## Success metrics

| Metric | What it tests |
| --- | --- |
| Merged migrations per quarter | Whether workloads actually move |
| Metered spend 90 days after merge, against the account's pre-migration baseline | The revenue claim |
| Scan to merged pull request | Where the funnel leaks. Below 40% means the report isn't enough. |

**Guardrail:** production regressions after a passing gate should be about zero. A gate
that passes bad migrations is worse than no gate, and it's the one failure that kills
the product outright.

## Ship the skill first

| Milestone | Ships | Reuses |
| --- | --- | --- |
| 1. A skill — 2–3 days | Rulebook, scan, rewrite, tests-green gate, HTML report | The migration kit's templates and queue runner |
| 2. Console — the rest | Decisions that persist, organization view, pull request status check, funnel metrics | Console components, the Claude GitHub App, the repository's own CI |

Milestone 1 runs locally, needs no account, and is a complete product on its own.
Milestone 2 buys measurement: every metric above is uncollectible from a local tool that
prints a report.

## Risks

- **If most OpenAI workloads port in an afternoon, the premise fails.** Switching cost
  wouldn't be the barrier, and none of this matters.
- **The gate has to be trusted.** If it isn't, this reduces to a codemod.
- **Targeting isn't possible today.** The Usage and Cost APIs group by model, workspace,
  and key. There's no endpoint dimension, so nothing public separates Chat Completions
  traffic from Messages traffic. Without it, milestone 2 loses its strongest
  justification and the skill has to be found rather than offered.

AWS Transform and Moderne prove the pattern works at enterprise scale. Neither exists
for provider migration; every provider ships a compatibility shim instead.

## Open questions

**No user report backs the central claim.** That developers reach the wrong conclusion
from a compatibility-layer evaluation follows from documented behavior, not from anyone
saying it happened to them. Close that gap before milestone 2.

## Evidence

Platform quotations come from Anthropic documentation fetched September 1, 2026.

Both prototypes run on seeded data. They read no repository and run no inference.

The 46% saving is computed in the published prototype from public list prices as of
September 1, 2026, on a workload of 12,400 requests per day with a 71% cache hit rate.
It's an illustration of the gap the compatibility layer hides, not a measurement of any
real account.

The linter behind the decisions runs locally:

```
cd prototype
python3 migration_lint.py fixtures/support-triage.json
python3 test_migration_lint.py
```

It classifies each ignored field by whether it breaks the output contract, gets rejected
natively, changes the result, or drops input — because "20 fields are ignored" isn't a
finding, and four of them are.
