# Move OpenAI workloads to Claude

Point Claude Code at a repository that uses the OpenAI SDK. It rewrites every call
site it can, stops to ask about the ones it can't, and then blocks the pull request
until the repository's own tests pass against Claude.

**Status:** Designed, working prototype · **Cost:** About 2 weeks · **Theme:** acquisition

[Terminal demo](https://madpr.github.io/claude-growth-surfaces/migrate.html)

## Problem

The OpenAI SDK compatibility layer is an endpoint on Anthropic's API. You point the
OpenAI SDK at it with a Claude key and a Claude model name, and requests are
translated on the server, tools included. The documentation describes it as a way
"to test and compare model capabilities" and says it is
"not considered a long-term or production-ready solution".

Nothing tells you what broke. The compatibility layer silently ignores most fields it
doesn't support, including the structured-output format and strict tool schemas, so a
team evaluating through it gets free-form text where it asked for JSON and no warning.

Prompt caching isn't supported through the layer either, so the 46% saving the
prototype prints on the seeded workload, most of it from caching, is invisible there.

## Proposed experience

Clean translations, prompts that look tuned for OpenAI, and fields whose behavior
changes on Claude all arrive in the pull request as ordinary diffs the team can review.

## Success metrics

| Metric | What it tests |
| --- | --- |
| Merged migrations per quarter | Whether workloads actually move |
| Metered spend 90 days after merge, against the account's pre-migration baseline | The revenue claim |

Guardrail: production regressions after a passing gate. The target is zero.

## Evidence

```
cd prototype && python3 migration_lint.py fixtures/support-triage.json && python3 migration_lint.py scan && python3 migration_lint.py cost && python3 test_migration_lint.py
```
