# Move unattended work to Managed Agents

Claude Code runs agents while a developer watches. Managed Agents runs agents nobody
watches, inside a spend cap, a quality rubric, and a sandbox where the agent never sees
its own credentials. There is no command that moves a project from the first to the
second. I use Claude Code every day, and when I went looking for that command I found
that I had zero hosted agents and that the platform, once I signed in, put me in a
different organization than Claude Code did. This proposal builds the path: a working
project becomes a hosted agent on a schedule, with its limits set before the first run.

**Status:** Case written, prototype running, two drivable demos.
**Cost:** 1 to 2 months.
**Theme:** expansion.

## Problem

I wanted one of my Claude Code projects to run on a schedule without me at the
keyboard, so I typed the words you would type. `claude agents` answered with background
sessions on my laptop. `environment` turned out to be a pool for cloud sessions,
`session` a local conversation I could resume, `budget` a flag that only works in one
mode. Every answer was plausible and every one was local, so for a while I concluded
that what I wanted did not exist.

It does. Anthropic ships a second command-line tool for the developer platform, and it
exposes the whole Managed Agents control plane as ordinary commands. It was not on my
machine. I installed it, signed in, and ran the status command in each tool. Claude
Code reported one organization for my email address and the platform CLI reported
another. Same email, two organization IDs. I did not expect that. The platform
organization already contained a workspace named, exactly, "Claude Code", and the tool
I use every day is not signed in to it. My hosted agent list was empty. So was my
deployment list.

Then I wrote a script that takes a real project and maps it onto the fields a hosted
agent needs, and counted what survives. Three fields transfer intact. Three arrive
degraded. Two kinds of working configuration, the permission rules and the locally
launched MCP servers, have no hosted field at all.

So the hard part is identity. Claude Code signs in through claude.ai against a
subscription; the platform signs in against a developer organization. On my account
those are two different organizations, so anything a promotion command emits would go
to an organization I am not signed in to from Claude Code. That boundary is also where
the money changes hands: subscription work is a flat fee, a hosted agent bills usage
plus runtime, and promoting a workload converts one into the other. And it is why the
estimate is months rather than days. Renaming a command takes days. Reconciling two
identities is the rest of the 1 to 2 months.

### The vocabulary collision

The two tools never mention each other, and they collide on every word someone would
search.

| A developer types | They get | The hosted product means |
| --- | --- | --- |
| `agents` | Background sessions on their laptop | A stored, versioned hosted agent |
| `environment` | A pool for cloud sessions | The sandbox an agent runs in |
| `session` | A local conversation they can resume | A hosted run that bills runtime |
| `budget` | A flag that works in one mode | An enforced spend cap |
| `auth` | Sign in to Claude Code | Sign in to the platform |

Four of the five return a plausible local answer, so nothing tells you a larger product
exists and the search ends there. Claude Code has an `import` command that pulls
configuration in from competing coding agents and nothing that pushes configuration
out, and the platform tool cannot read a Claude Code project either.

## Goals

- Put a supervised workload onto hosted infrastructure at the point where someone
  decides to stop watching it.
- Make the spend cap and the rubric something the developer sets in that same step,
  before the first unattended run.
- Convert flat-fee subscription work into metered platform usage.

## Non-goals

- Building spend caps, rubrics, or credential isolation. All three already ship.
- A general migration tool. This is one path, from Claude Code to a hosted agent.
- Changing how Claude Code runs locally.

## Proposed experience

One command turns a working project into a hosted agent, the sandbox it runs in, and
the schedule it runs on. The model, the instructions, the tools, the skills, and the
connected services already exist on disk, and the developer re-enters none of them.

The three fields that transfer intact are the name, the model, and the system prompt,
which is CLAUDE.md. The three that arrive degraded are tools, which lose their
command-pattern granularity, skills, which keep their names but have to be uploaded to
the Skills API, and MCP servers, which translate only when they are URL-based. The two
kinds of configuration with no hosted field at all are what shape the product.

The permission rules do not transfer. A hosted toolset turns a whole tool on or off
and has no equivalent of `Bash(rm *)` or `Write(ledger/**)`. Containment at that grain
is a property of the environment, the sandbox and the vault, so the command has to
make the developer set limits again on the sandbox. That is the last point before the
agent runs with nobody watching, and it is the step worth designing well.

And the sandbox cannot be inferred. A laptop has no container image, network policy,
or credential store to hand over. Creating one is a required step in the flow, with
nothing defaulted.

## First cheap milestone

Before building the promotion path, test whether discovery is the gate. Disambiguate
the `agents` command in Claude Code so it names the hosted product, name Managed
Agents in Claude Code where someone searching would look, and watch hosted-agent
creation for 30 days. That is days of work, and creation over those 30 days tells you
whether people were only failing to find it.

The test replaces the arithmetic I would otherwise be tempted to do about what one
promoted workload bills. I had the prototype print that arithmetic anyway, at list
price and tokens only, for the model the fixture pins, Claude Sonnet 5: $2 per million
input tokens and $10 per million output tokens, uncached, from the platform pricing
page retrieved September 3, 2026. I do not know how many input tokens a run takes or
how many runs a night a workload does, so the table sweeps both.

| Input tokens per run | 1 run/night | 3 runs/night | 10 runs/night |
| --- | --- | --- | --- |
| 200,000 | $18.00 | $54.00 | $180.00 |
| 1,000,000 | $90.00 | $270.00 | $900.00 |
| 5,000,000 | $450.00 | $1,350.00 | $4,500.00 |

Every cell assumes 30 nights a month and fixes output at one tenth of input per run,
which at these prices is one third of the cell. Session runtime bills on top at $0.08
per session-hour and is not in the table, because run duration is a third thing I do
not know. None of this is a forecast. What the table shows is the shape of the
conversion: a subscription seat costs the same flat fee whether the workload runs once
a night or ten times, and the platform bills every run.

## What the first test settles

Whether discovery is the gate. Hosted-agent creation over the 30 days after the pointer
ships answers that directly.

Whether the organization split is only a consumer-subscription thing. I don't know this
yet; I have one account and it is on a Pro plan. A second sign-in on a Console plan
account would tell me, and the identity probe in the research directory reports whether
the two tools agree without printing either identifier.

Whether unattended workloads already exist at scale on the platform. Scheduled and
hosted-session traffic answer that, and both are already leading indicators under
Success metrics.

## Why hosted rather than self-built

A hosted agent is the same model with an orchestrator above it, and the limits belong
to the orchestrator.

| Limit | Building it yourself | Hosted |
| --- | --- | --- |
| Cost | Track usage and stop your own loop | A dollar cap enforced between model requests |
| Quality | Call a second model against a rubric | A required rubric, graded in a separate context |
| Authority | A container with scoped credentials | A per-session sandbox where secrets are substituted at egress and never visible inside |

A competent team can build the first two. The third is different in kind, because the
secret never enters the sandbox. The sharpest report I read in the issue tracker is
#85919. The agent hit a 403, went looking, found an admin secret in a sibling project's
`.env`, and used it to mint itself a new API token with more capabilities than the one
it had. It never asked. What struck me was that scoping the credential better would
not have helped, because the agent simply found a different credential. What would
have stopped it is never holding a secret at all, which is what the hosted sandbox
does.

## Where else this applies

Cowork is this argument already shipped, for people who never open a terminal. It runs
"the same agentic architecture that powers Claude Code" inside Claude Desktop, and it
schedules tasks that run unattended on Anthropic's servers. Its documentation says it
"doesn't read the Claude Code CLI's `~/.claude` directory", so a developer who has set
Claude Code up carefully does that work again by hand, the same portability gap on a
third product. Cowork ships on all paid plans, signs in with the claude.ai account, and
keeps unattended work on the subscription. Under [the decision rule this repo
states](../README.md), work stays on the subscription while it is one person's, run
interactively or on their own account, and moves to the platform when it runs
unattended against infrastructure a team owns, needs limits someone other than the
operator sets, or bills an organization rather than a person. Cowork's scheduled tasks
are one person's, on their own account, so they stay on the subscription. This
proposal is about the team-owned unattended work the rule puts on the platform.

## Success metrics

The leading indicators move first. Spend lags them by about a quarter and confirms
them.

| Metric | What it reads |
| --- | --- |
| Traffic that runs on a schedule | Leading. Unattended work is growing |
| Hosted-agent sessions | Leading. That work runs on the platform |
| Share of runs that set a spend cap and a rubric | Leading. Limits are the reason people came |
| Workloads that move to unattended operation, against their supervised baseline | The core claim |
| Spend 90 days after the move | Lagging. The revenue claim |

The guardrail is incidents on unattended runs, measured against the supervised
baseline.

## Evidence

Fourteen issues in the Claude Code issue tracker
([`research/issues.tsv`](research/issues.tsv)). I opened and read all fourteen. Eleven
show the agent acting outside its mandate; the work itself was usually fine. Five are
in the table.

| Issue | What the agent did |
| --- | --- |
| [#85919](https://github.com/anthropics/claude-code/issues/85919) | Found an admin secret in a sibling project and minted a token with expanded capabilities |
| [#86667](https://github.com/anthropics/claude-code/issues/86667) | Bypassed a system-path guard, kept running after timeout, and wiped a drive root |
| [#82063](https://github.com/anthropics/claude-code/issues/82063) | Deployed to production without asking |
| [#81035](https://github.com/anthropics/claude-code/issues/81035) | Spawned a live process from a failed fork that merged pull requests with admin bypass |
| [#79103](https://github.com/anthropics/claude-code/issues/79103) | Asked for a preflight checkpoint before unattended runs |

Issue #82063 says it in the user's own words: "no harm done, but it makes me very
worried." Nothing broke, and they filed anyway.

There is competitive pressure too.
[`antigravity-for-claude-code`](https://github.com/yuting0624/antigravity-for-claude-code)
is an unaffiliated Claude Code plugin I looked at on September 3, 2026. It routes
token-heavy work out of Claude Code to Gemini through a hook that makes offloading the
default. It names a failure the rest of this slate misses, spend routing inside a
session: the seat stays, the organization stays, the subscription stays, only the
volume per session falls, and a retention dashboard would call that account healthy.

To reproduce it, run these from this directory. Neither command reads an account or
calls an API, and `size` in place of `map` prints the cost table.

```
./research/probe.sh
./prototype/promote.py map prototype/fixtures/ledger-reconcile
```

The Cowork quotes are from claude.com/docs/cowork/overview and
claude.com/product/cowork, retrieved September 3, 2026. The tool behavior is from
Claude Code 2.1.259 and the platform CLI 1.29.0, captured September 2 and 3, 2026.
Every figure in the mapping and in the size table is printed by the prototype and
pinned by its tests. Two drivable demos: [terminal](https://madpr.github.io/claude-growth-surfaces/promote-cli.html) and
[browser](https://madpr.github.io/claude-growth-surfaces/promote-to-agent.html).
