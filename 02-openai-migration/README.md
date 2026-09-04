# Move OpenAI workloads to Claude

Point Claude Code at a repository that uses the OpenAI SDK. It rewrites every call
site it can, stops to ask about the ones it can't, and then blocks the pull request
until the repository's own tests pass against Claude.

**Status:** Designed, working prototype.
**Cost:** About 2 weeks.
**Theme:** acquisition.

[Open the terminal demo](https://madpr.github.io/claude-growth-surfaces/migrate.html).
It scans a seeded repository with 38 call sites, rewrites 33 without asking, stops on
two decisions covering five call sites, runs the repository's tests against Claude,
and ends on the pull request check.

## Problem

The rewrite is the easy part. A team can translate their code in an afternoon but
can't show their reviewer that behavior held, because there is no compiler for a
prompt. So the workload stays where it is.

### What already ships

The OpenAI SDK compatibility layer is an endpoint on Anthropic's API. You point the
OpenAI SDK at it with a Claude key and a Claude model name, and requests are
translated on the server, tools included. The documentation describes it as a way
"to test and compare model capabilities" and says it is
"not considered a long-term or production-ready solution".

The Claude GitHub App already has repository access, granted for code review.

### What's missing

Nothing tells you what broke. The compatibility layer silently ignores most fields it
doesn't support, including the structured-output format and strict tool schemas, so a
team evaluating through it gets free-form text where it asked for JSON and no warning.

Prompt caching isn't supported through the layer either, so the 46% saving the
prototype prints on the seeded workload, most of it from caching, is invisible there.

Anthropic's prompting documentation warns that a prompt "well-tuned to OpenAI specifically"
degrades on Claude. The Console's prompt improver used to fix that; it has been
retired and its documentation page now redirects.

## Goals

Let a team prove a migration didn't regress, with evidence their reviewer already
trusts, in a check that runs on every push.

## Non-goals

- Rewriting prompts silently.
- Every language and endpoint. The first version handles Python and Chat Completions.
- Replacing the compatibility layer.

## Proposed experience

A developer gets three things back.

1. The rewrite: every call site that translates cleanly.
2. The decisions: prompts that look tuned for OpenAI, and fields whose behavior
   changes on Claude.
3. The gate: the pull request stays blocked until the tests pass against Claude.

The rewrite and the decisions happen in Claude Code, where the code is, and arrive in
the pull request as ordinary diffs. The gate runs in the repository's own CI on every
push and posts a status check, because a reviewer trusts a red check from their own
CI and would not extend that trust to a vendor's report. The Console only shows the
record: which decisions were made, in which pull request, whether the check passed.

## Success metrics

| Metric | What it tests |
| --- | --- |
| Merged migrations per quarter | Whether workloads actually move |
| Metered spend 90 days after merge, against the account's pre-migration baseline | The revenue claim |
| Scan to merged pull request | Where the funnel leaks. Below 40% means the report isn't enough. |

Guardrail: production regressions after a passing gate. The target is zero.

## Ship the skill first

| Milestone | Ships | Reuses |
| --- | --- | --- |
| 1. A skill — 2–3 days | Rulebook, scan, rewrite, tests-green gate, HTML report | The migration kit's templates and queue runner |
| 2. Console — the rest | Decisions that persist, organization view, pull request status check, funnel metrics | Console components, the Claude GitHub App, the repository's own CI |

Milestone 1 runs locally and needs no account. Milestone 2 collects every metric
above; the check the demo ends on is milestone 2 behavior.

## What the first milestone settles

- Whether switching cost is the barrier: the scan-to-merge rate from milestone 1's
  report.
- Whether anyone trusts the gate: production regressions after a passing check.
- Who to offer it to: organizations already sending Chat Completions traffic, from
  milestone 2's endpoint dimension in usage reporting.

## Evidence

The quotations and the list of ignored fields come from the [OpenAI SDK compatibility
page](https://platform.claude.com/docs/en/cli-sdks-libraries/libraries/openai-sdk)
and the prompting documentation, fetched September 1 and 3, 2026.

The linter, [`prototype/migration_lint.py`](prototype/migration_lint.py), classifies
every field the compatibility layer ignores. On the seeded payload it prints
7 breaks contract, 2 native rejects, 4 changes result, 3 inert. Its `scan` subcommand
prints every figure the demo shows, and the tests pin them.

The 46% comes from the `cost` subcommand, run on public list prices as of
September 1, 2026, against a seeded workload of 12,400 requests a day at a 71% cache
hit rate. Nothing in it was measured; the prototype and the demo run on seeded data,
read no repository, and run no inference.

```
cd prototype && python3 migration_lint.py fixtures/support-triage.json && python3 migration_lint.py scan && python3 migration_lint.py cost && python3 test_migration_lint.py
```
