# Move OpenAI workloads to Claude

Point Claude Code at a repository that uses the OpenAI SDK. It rewrites every call
site it can, stops to ask about the ones it can't, and then blocks the pull request
until the repository's own tests pass against Claude.

The rewrite is the easy part. Where I've watched this stall is the pull request
afterward: the code is translated, the tests are green on OpenAI, and nobody in review
can say whether they'd still be green on Claude, so the pull request waits and the
workload stays where it is. The check that answers that question is the part worth
building.

**Status:** Designed, working prototype.
**Cost:** About 2 weeks.
**Theme:** acquisition.

[Open the terminal demo](https://madpr.github.io/claude-growth-surfaces/migrate.html).
It's one session. The skill scans a seeded repository with 38 call sites, rewrites 33
of them without asking, stops on two decisions covering five call sites, runs the
repository's own tests against Claude, and ends on the pull request check that decides
whether the merge goes through.

## Problem

A team evaluating Claude can translate their code in an afternoon. What they can't do
is show their reviewer that the translation didn't change behavior. When a codebase
moves from one language to another, the compiler is the reviewer's evidence; if it
builds, the program still has the shape it had. There is no compiler for a prompt.
Nothing tells you the model still returns the JSON your parser expects, and a reviewer
who can't get that answer does the sensible thing and doesn't approve.

### What already ships

Before proposing anything I went looking for what Anthropic had already built, and
most of what an outsider would suggest is there.

The OpenAI SDK compatibility layer is an endpoint on Anthropic's API. You point the
OpenAI SDK at it with a Claude key and a Claude model name, and your Chat Completions
requests get translated on the server, tool definitions and tool calls included.
Anthropic is careful about what it's for. The documentation describes it as a way
"to test and compare model capabilities" and says it is
"not considered a long-term or production-ready solution".

The Claude GitHub App already has access to the repository, because the team granted
it for code review.

One thing I expected to find was gone. The Console used to have a prompt improver, and
it handled the prose half of a migration, the part where a prompt written for OpenAI
gets reworked for Claude. There's no Workbench in the Console navigation now, and the
improver's documentation page redirects to the general prompting guide.

### What's missing

Nothing tells you what broke. The compatibility layer ignores most fields it doesn't
support, silently, and two of those fields are the ones your parser depends on: the
structured-output format and strict tool schemas. So a team that evaluates Claude
through the layer Anthropic recommends for evaluation loses schema enforcement without
being told, gets free-form text back where it asked for JSON, and concludes that's the
best the model can do. It isn't.

The cost case is invisible from the one place you'd measure it. Prompt caching isn't
supported through the compatibility layer either. On the seeded workload the prototype
prints a 46% saving, and most of that comes from caching; run the same evaluation
through the layer and you see none of it.

Prompt tuning is nobody's job. Anthropic's own prompting documentation warns that a
prompt "well-tuned to OpenAI specifically" degrades on Claude, and the tool that used
to fix that has been retired.

## Goals

Let a team prove a migration didn't regress, using evidence their reviewer already
trusts, and move that decision out of the review thread and into a check that runs on
every push. Evaluation traffic then has a way to become production traffic.

## Non-goals

- Rewriting prompts silently. An unreviewable prose change is the last thing anyone
  wants in a migration pull request.
- Covering every language and endpoint. The first version handles Python and Chat
  Completions.
- Replacing the compatibility layer. It's the right way to try Claude from code you
  already have; it just isn't where an evaluation should run.

## Proposed experience

A developer points the tool at their repository and gets three things back.

1. **The rewrite.** Every call site that translates cleanly, translated.
2. **The decisions.** Anything a person has to judge gets put in front of them:
   prompts that look tuned for OpenAI, and fields whose behavior changes on Claude.
3. **The gate.** The repository's test suite already passes against OpenAI, and that's
   the baseline. The pull request stays blocked until it passes against Claude too.

I put each of the three where I did on purpose. The rewrite and the decisions happen in
Claude Code, because that's where the code is, and they arrive in the pull request as
ordinary diffs. The gate runs in the repository's own continuous integration on every
push and posts a status check, because a reviewer already trusts a red check from their
own CI and would not extend that trust to a report from a vendor. The Console does
nothing but show the record, which decisions were made, in which pull request, and
whether the check passed, so there's no second tool to open.

Scanning and rewriting already work. Proving behavior held is the part nobody has
built, and it's the reason Anthropic's published migration kit doesn't apply unchanged.
The kit assumes a new target language, a compiler that tells you when you're done, and
a rewrite done all at once. None of that is true here.

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

Milestone 1 runs locally, needs no account, and is a complete product on its own.
Milestone 2 adds the measurement: every metric in the table above is collected there.
The demo shows the developer's session, and the check it ends on is milestone 2
behavior as the developer would see it.

## What the first milestone settles

Whether switching cost is really the barrier. Milestone 1's report gives me a
scan-to-merge rate, which is whether teams who see the diff and the test results go on
to merge.

Whether anyone trusts the gate. From the first merged migration on, I can count
production regressions after a passing check. I don't know this yet; only merged
migrations will tell me.

Who to offer it to. Milestone 2 adds an endpoint dimension to usage reporting, so I can
offer the skill to organizations that already send Chat Completions traffic, without
waiting for them to go looking.

## Evidence

Platform behavior comes from the [OpenAI SDK compatibility
page](https://platform.claude.com/docs/en/cli-sdks-libraries/libraries/openai-sdk)
and the prompting documentation, which I fetched on September 1 and 3, 2026. The
layer's stated purpose, the list of fields it ignores, the retired prompt improver, and
the prompt-tuning warning are all quoted from those pages.

For precedent, AWS Transform and Moderne run this pattern at enterprise scale for
language migrations. No provider ships it for moving between providers; each one ships
a compatibility shim.

The linter, [`prototype/migration_lint.py`](prototype/migration_lint.py), classifies
every field the compatibility layer ignores. On the seeded payload it prints
7 breaks contract, 2 native rejects, 4 changes result, 3 inert. The seven contract
breaks are structured output and strict tool schemas. Its `scan` subcommand prints every figure
the demo shows: 38 call sites, 33 rewritten, two decisions covering five call sites,
and the test count and check result for each choice. The tests pin all of them.

The 46% comes from the same prototype's `cost` subcommand, run on public list prices as
of September 1, 2026, against a seeded workload of 12,400 requests a day at a 71% cache
hit rate. It's an illustration of what the compatibility layer hides. Nothing in it was
measured.

The prototype and the demo run on seeded data. They read no repository and run no
inference.

```
cd prototype && python3 migration_lint.py fixtures/support-triage.json && python3 migration_lint.py scan && python3 migration_lint.py cost && python3 test_migration_lint.py
```
