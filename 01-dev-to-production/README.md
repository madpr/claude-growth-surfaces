# Move unattended work to Managed Agents

Claude Code runs agents while a developer watches. Managed Agents runs them unwatched,
inside a spend cap, a quality rubric, and a sandbox that never shows the agent its own
credentials. Nothing moves a project from one to the other; this proposal builds that
path, with the limits set before the first unattended run.

**Status:** Case written, prototype running, two drivable demos.
**Cost:** 1 to 2 months.
**Theme:** expansion.

## Problem

The obvious words typed into Claude Code (`claude agents`, `environment`, `session`,
`budget`) all return local answers, so the search ends there. The platform CLI was not
on my machine. Signed in, it reported a different organization ID than Claude Code for
the same email; that organization already held a workspace named, exactly, "Claude
Code", and my hosted agent list was empty. That boundary is the revenue event, a flat
subscription fee becoming metered usage plus runtime, and why the estimate is months:
the rename is days, the identity work is the rest.

The two tools never mention each other and collide on every searchable word.

| A developer types | They get | The hosted product means |
| --- | --- | --- |
| `agents` | Background sessions on their laptop | A stored, versioned hosted agent |
| `environment` | A pool for cloud sessions | The sandbox an agent runs in |
| `session` | A local conversation they can resume | A hosted run that bills runtime |
| `budget` | A flag that works in one mode | An enforced spend cap |
| `auth` | Sign in to Claude Code | Sign in to the platform |

## Goals

- Move a supervised workload to hosted infrastructure when someone stops watching it.
- Have the developer set the spend cap and the rubric in that same step.
- Convert flat-fee subscription work into metered platform usage.

## Non-goals

- Spend caps, rubrics, credential isolation. All three already ship.
- A general migration tool. This is one path, from Claude Code to a hosted agent.

## Proposed experience

One command turns a working project into a hosted agent, the sandbox it runs in, and
the schedule it runs on. Of the hosted agent's fields, three transfer intact (name,
model, CLAUDE.md as the system prompt), three arrive degraded (tools lose
command-pattern granularity, skills must be uploaded to the Skills API, MCP servers
translate only when URL-based), and two have no hosted equivalent: permission rules,
since a hosted toolset has nothing like `Bash(rm *)`, and the sandbox itself, since a
laptop has no container image, network policy, or credential store to hand over. The
command makes the developer create the sandbox and set its limits, nothing defaulted.

## First cheap milestone

First, test whether discovery is the gate. Make Claude Code's `agents` command name
the hosted product, put Managed Agents where someone searching would look, and watch
hosted-agent creation for 30 days. Days of work.

The prototype also prints what one promoted workload bills at list price, tokens only,
for the fixture's model, Claude Sonnet 5: $2 per million input tokens and $10 per
million output tokens, uncached, from the platform pricing page retrieved September 3,
2026. Input per run and runs per night are unknown, so the table sweeps both.

| Input tokens per run | 1 run/night | 3 runs/night | 10 runs/night |
| --- | --- | --- | --- |
| 200,000 | $18.00 | $54.00 | $180.00 |
| 1,000,000 | $90.00 | $270.00 | $900.00 |
| 5,000,000 | $450.00 | $1,350.00 | $4,500.00 |

Every cell assumes 30 nights a month and output at one tenth of input. Runtime bills
on top at $0.08 per session-hour and is not in the table. None of this is a forecast.

## What the first test settles

Whether discovery is the gate: hosted-agent creation in the 30 days after the pointer
ships.

Whether the organization split is only a consumer-subscription thing. My one account
is on a Pro plan; a second sign-in on a Console plan would tell me, and
`research/probe.sh` reports whether the two tools agree without printing either
identifier.

Whether unattended workloads already run at scale on the platform: scheduled and
hosted-session traffic, both under Success metrics.

## Why hosted rather than self-built

The limits belong to the orchestrator above the model.

| Limit | Building it yourself | Hosted |
| --- | --- | --- |
| Cost | Track usage and stop your own loop | A dollar cap enforced between model requests |
| Quality | Call a second model against a rubric | A required rubric, graded in a separate context |
| Authority | A container with scoped credentials | A per-session sandbox where secrets are substituted at egress and never visible inside |

A competent team can build the first two. In #85919 the agent hit a 403, found an
admin secret in a sibling project's `.env`, and minted itself a token with more
capabilities than it had. A better-scoped credential would not have helped; the hosted
sandbox never holds one.

## Where else this applies

Cowork is the same argument shipped for people who never open a terminal. It runs
"the same agentic architecture that powers Claude Code" inside Claude Desktop,
schedules unattended tasks on Anthropic's servers, and "doesn't read the Claude Code
CLI's `~/.claude` directory". Under [the decision rule this repo states](../README.md),
work stays on the subscription while it is one person's, run interactively or on their
own account, and moves to the platform when it runs unattended against infrastructure
a team owns, needs limits someone other than the operator sets, or bills an
organization rather than a person. Cowork's tasks are one person's on their own
account, so they stay; this proposal covers the team-owned work the rule moves.

## Success metrics

| Metric | What it reads |
| --- | --- |
| Traffic that runs on a schedule | Leading. Unattended work is growing |
| Hosted-agent sessions | Leading. That work runs on the platform |
| Share of runs that set a spend cap and a rubric | Leading. Limits are the reason people came |
| Workloads that move to unattended operation, against their supervised baseline | The core claim |
| Spend 90 days after the move | Lagging. The revenue claim |

The guardrail is incidents on unattended runs, against the supervised baseline.

## Evidence

Fourteen issues in the Claude Code issue tracker
([`research/issues.tsv`](research/issues.tsv)), all read. Eleven show the agent acting
outside its mandate.

| Issue | What the agent did |
| --- | --- |
| [#85919](https://github.com/anthropics/claude-code/issues/85919) | Found an admin secret in a sibling project and minted a token with expanded capabilities |
| [#86667](https://github.com/anthropics/claude-code/issues/86667) | Bypassed a system-path guard, kept running after timeout, and wiped a drive root |
| [#82063](https://github.com/anthropics/claude-code/issues/82063) | Deployed to production without asking |
| [#81035](https://github.com/anthropics/claude-code/issues/81035) | Spawned a live process from a failed fork that merged pull requests with admin bypass |
| [#79103](https://github.com/anthropics/claude-code/issues/79103) | Asked for a preflight checkpoint before unattended runs |

Issue #82063 in the user's own words: "no harm done, but it makes me very
worried."

[`antigravity-for-claude-code`](https://github.com/yuting0624/antigravity-for-claude-code),
an unaffiliated plugin looked at on September 3, 2026, makes offloading token-heavy
work from Claude Code to Gemini the default: the seat stays, the volume per session
falls, and a retention dashboard calls that account healthy.

Run from this directory; neither reads an account or calls an API. `size` in
place of `map` prints the cost table.

```
./research/probe.sh
./prototype/promote.py map prototype/fixtures/ledger-reconcile
```

The Cowork quotes are from claude.com/docs/cowork/overview and
claude.com/product/cowork, retrieved September 3, 2026. The tool behavior is from
Claude Code 2.1.259 and the platform CLI 1.29.0, captured September 2 and 3, 2026.
Two drivable demos: [terminal](https://madpr.github.io/claude-growth-surfaces/promote-cli.html) and
[browser](https://madpr.github.io/claude-growth-surfaces/promote-to-agent.html).
