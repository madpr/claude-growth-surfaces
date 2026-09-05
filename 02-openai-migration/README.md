# Move OpenAI workloads to Claude

Point Claude Code at a repository that uses the OpenAI SDK. It rewrites every call
site it can, stops to ask about the ones it can't, and then blocks the pull request
until the repository's own tests pass against Claude.

**Status:** Designed · **Cost:** About 2 weeks · **Theme:** acquisition

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

Prompt caching isn't supported through the layer either, so a cost comparison run
through it bills every request at uncached prices and overstates what the same
workload costs on the native API.

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

The compatibility layer's own documentation, read September 1, 2026
([OpenAI SDK compatibility](https://platform.claude.com/docs/en/cli-sdks-libraries/libraries/openai-sdk)):
it is "primarily intended to test and compare model capabilities, and is not considered
a long-term or production-ready solution"; `strict` and `response_format` are ignored;
prompt caching is not supported; and "most unsupported fields are silently ignored
rather than producing errors."

The terminal demo runs on a seeded repository. It reads no repository and calls no API.
