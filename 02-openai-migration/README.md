# Move OpenAI workloads to Claude

Point Claude Code at a repository that uses the OpenAI SDK. It rewrites every call
site, then blocks the pull request until the repository's own tests still pass.

The rewrite isn't what stops teams from switching, and neither is model quality. What
stops them is that nobody can prove the switch is safe, so the parity gate is the part
worth building.

**Status:** Designed, working prototype.
**Cost:** About 2 weeks.
**Theme:** acquisition.

[Open the prototype](https://madpr.github.io/claude-growth-surfaces/migrations/). One
screen: 33 call sites rewritten, two decisions covering five call sites that only a
person can make, and whether the tests still pass. Settle both decisions and the merge
unblocks.

## Problem

A team evaluating Claude can translate their code in an afternoon. What they can't do
is show their reviewer that the translation didn't change behavior. A language
migration gates on a compiler. No compiler tells you whether a prompt still works, so
the decision stalls in review and the workload stays where it is.

### What already ships

Most of what an outsider would propose building is already there:

- The OpenAI SDK compatibility layer, an endpoint on Anthropic's API. Point the
  OpenAI SDK at it with a Claude key and a Claude model name, and Chat Completions
  requests are translated server-side, tool definitions and tool calls included.
  Anthropic documents it as a way "to test and compare model capabilities", and "not
  considered a long-term or production-ready solution".
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
saving comes from caching, and none of it shows up in an evaluation run through the
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
- Replacing the compatibility layer. It's the right way to try Claude from existing
  code, and the wrong place to run an evaluation.

## Proposed experience

A developer points the tool at their repository. It produces three things:

1. **The mechanical rewrite.** Every call site that translates cleanly, translated.
2. **The decisions.** Anything a person has to judge, surfaced rather than guessed:
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

**Guardrail:** Production regressions after a passing gate, target zero.

## Ship the skill first

| Milestone | Ships | Reuses |
| --- | --- | --- |
| 1. A skill — 2–3 days | Rulebook, scan, rewrite, tests-green gate, HTML report | The migration kit's templates and queue runner |
| 2. Console — the rest | Decisions that persist, organization view, pull request status check, funnel metrics | Console components, the Claude GitHub App, the repository's own CI |

Milestone 1 runs locally, needs no account, and is a complete product on its own.
Milestone 2 adds measurement: the success metrics above are collected there. The
published prototype shows the milestone 2 screen because that is where the gate state
and the funnel metrics become visible; milestone 1 prints the same three sections as a
static report.

## What the first milestone settles

- **Whether switching cost is the barrier:** the scan-to-merge rate from milestone 1's
  report.
- **Whether the gate is trusted:** production regressions after a passing gate, tracked
  from the first merged migration.
- **Who to offer it to:** milestone 2 adds an endpoint dimension to usage reporting, so
  the skill is offered to organizations with Chat Completions traffic rather than found.

## Evidence

- **Platform behavior:** the [OpenAI SDK compatibility
  page](https://platform.claude.com/docs/en/cli-sdks-libraries/libraries/openai-sdk)
  and the prompting documentation, fetched September 1 and 3, 2026. The layer's stated
  purpose, its ignored fields, the retired prompt improver, and the prompt-tuning
  warning are quoted from them.
- **Precedent:** AWS Transform and Moderne run this pattern at enterprise scale for
  language migrations. No provider ships it for provider migration; each ships a
  compatibility shim instead.
- **The linter:** [`prototype/migration_lint.py`](prototype/migration_lint.py)
  classifies every field the compatibility layer ignores. On the seeded payload it
  prints 7 breaks contract, 2 native rejects, 4 changes result, 3 inert. The seven
  contract breaks are structured output and strict tool schemas. Tests pin the counts.
- **The 46%:** computed in the published prototype from public list prices as of
  September 1, 2026, on a seeded workload of 12,400 requests a day at a 71% cache hit
  rate. An illustration of what the compatibility layer hides, not a measurement.
- Both prototypes run on seeded data, read no repository, and run no inference.

```
cd prototype && python3 migration_lint.py fixtures/support-triage.json && python3 test_migration_lint.py
```
