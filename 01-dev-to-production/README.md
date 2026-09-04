# Move unattended work to Managed Agents

Claude Code runs agents a developer supervises. Managed Agents runs agents nobody
watches, inside spend caps, quality rubrics, and credentials the agent never sees. No
command moves a project from one to the other, and on the account tested a daily Claude
Code user had zero hosted agents. This proposal adds that path: a working project
becomes a hosted agent on a schedule, inside limits set before it runs.

**Status:** Case written, prototype running, two drivable demos.
**Cost:** 1 to 2 months.
**Theme:** expansion.

## Problem

A supervised workload is bounded by the attention of whoever watches it. Unattended, it
is bounded only by the limits it was given, and Managed Agents is where those limits
live.

- **Promotion is an identity problem, not a tooling gap.** Claude Code signs in against
  a subscription; the platform signs in against a developer organization. On the
  account tested, those were two different organizations for one email address, so
  whatever transfers lands in an organization the developer is not signed in to.
- **That boundary is the revenue event.** Subscription work is flat-fee. Hosted agents
  bill usage plus runtime. Promoting a workload converts it.
- **It sets the timeline.** Renaming a command takes days. Reconciling two identities
  does not, and that is why this costs 1 to 2 months.

### The vocabulary collision

Anthropic ships two command-line tools that split one account: Claude Code, where
developers work, and the platform tool, which owns the hosted-agent surface. Neither
points at the other, and they collide on every word someone would search:

| A developer types | They get | The hosted product means |
| --- | --- | --- |
| `agents` | Background sessions on their laptop | A stored, versioned hosted agent |
| `environment` | A pool for cloud sessions | The sandbox an agent runs in |
| `session` | A local conversation they can resume | A hosted run that bills runtime |
| `budget` | A flag that works in one mode | An enforced spend cap |
| `auth` | Sign in to Claude Code | Sign in to the platform |

Four of the five return a plausible local answer, so nothing signals a larger surface
exists and the search ends. Claude Code imports configuration from competing agents and
exports nothing; the platform tool has no awareness of Claude Code.

## Goals

- Route supervised workloads onto hosted infrastructure at the moment someone decides
  to stop watching.
- Make the limits a deliberate choice at that moment, rather than an optional call
  afterward.
- Convert flat-fee subscription work into metered platform usage.

## Non-goals

- Building spend caps, rubrics, or credential isolation. All three already ship.
- A general migration tool. This is one path, from Claude Code to hosted agents.
- Changing how Claude Code runs locally.

## Proposed experience

One command turns a working project into the hosted agent, the sandbox it runs in, and
the schedule it runs on. The model, instructions, tools, skills, and connected services
already exist on disk; the developer re-enters none of them.

Measured against a real project, three fields transfer intact, three arrive degraded,
and two kinds of working configuration have no hosted equivalent. The last two shape
the product:

- **The limits do not transfer.** Local permission rules have no hosted equivalent, so
  the flow makes the developer set limits again on the sandbox. That is the last point
  before the agent runs with nobody watching, and the step worth designing well.
- **The sandbox cannot be inferred.** A laptop has no container image, network policy,
  or credential store to hand over. Creating one is a required step, not a default.

## First cheap milestone

Test discovery before building the promotion path:

1. Disambiguate the agents command in Claude Code so it names the hosted product.
2. Name Managed Agents in Claude Code, where someone searching would look.
3. Watch hosted-agent creation for 30 days.

This takes days, and creation over those 30 days reads whether discovery is the gate.

What one promoted workload bills is the arithmetic the test replaces. The prototype
prints it at list price, tokens only, for the model the fixture pins, Claude Sonnet 5:
$2 per million input tokens and $10 per million output tokens, uncached, from the
platform pricing page retrieved September 3, 2026. Input tokens per run and runs per
night both vary by workload, so both are swept.

| Input tokens per run | 1 run/night | 3 runs/night | 10 runs/night |
| --- | --- | --- | --- |
| 200,000 | $18.00 | $54.00 | $180.00 |
| 1,000,000 | $90.00 | $270.00 | $900.00 |
| 5,000,000 | $450.00 | $1,350.00 | $4,500.00 |

30 nights per month. Output is fixed at one tenth of input per run, one third of every
cell at these prices. Session runtime bills on top at $0.08 per session-hour and is not
priced here. The table is an illustration at list price, not a forecast. A subscription
seat bills the same flat fee whether the workload runs once a night or ten times; the
platform bills every run, and that difference is what promotion converts.

## What the first test settles

- **Whether discovery is the gate:** hosted-agent creation over the 30 days after the
  pointer ships.
- **Whether the organization split generalizes beyond consumer subscriptions:** a
  second sign-in on a Console plan account, with the identity probe in the research
  directory, which reports agreement without printing identifiers.
- **Whether unattended workloads exist at scale on the platform today:** scheduled and
  hosted-session traffic, which the leading indicators under Success metrics already
  read.

## Why hosted rather than self-built

Hosted agents are the same model with an orchestrator above it, and the limits belong
to that orchestrator:

| Limit | Building it yourself | Hosted |
| --- | --- | --- |
| Cost | Track usage and stop your own loop | A dollar cap enforced between model requests |
| Quality | Call a second model against a rubric | A required rubric, graded in a separate context |
| Authority | A container with scoped credentials | A per-session sandbox where secrets are substituted at egress and never visible inside |

A competent team can build the first two; the third is different in kind, because the
secret never enters the sandbox. That answers the sharpest report in the corpus, an
agent that hit a permissions error, found an admin secret in a sibling project, and
minted itself a token: scoping the credential would not have stopped it, and not
holding it would.

## Where else this applies

Cowork is this argument already shipped, for people who never open a terminal: it runs
"the same agentic architecture that powers Claude Code" inside Claude Desktop and
schedules tasks that run unattended on Anthropic's servers. Its documentation states
that it "doesn't read the Claude Code CLI's `~/.claude` directory", so a developer who
configured Claude Code re-enters that work by hand, the same portability gap on a third
surface. Cowork ships on all paid plans, reads the claude.ai account, and keeps
unattended work on the subscription. Under [the decision rule this repo
states](../README.md), work stays on the subscription while it is one person's, run
interactively or on their own account, and moves to the platform when it runs
unattended against infrastructure a team owns, needs limits someone other than the
operator sets, or bills an organization rather than a person. Cowork's scheduled tasks
are one person's, on their own account, and stay on the subscription. This proposal
covers team-owned unattended work, which the rule places on the platform.

## Success metrics

Read the leading indicators first; spend lags them by a quarter and confirms them.

| Metric | What it reads |
| --- | --- |
| Traffic that runs on a schedule | Leading. Unattended work is growing |
| Hosted-agent sessions | Leading. That work runs on the platform |
| Share of runs that set a spend cap and a rubric | Leading. Limits are the reason people came |
| Workloads that move to unattended operation, against their supervised baseline | The core claim |
| Spend 90 days after the move | Lagging. The revenue claim |

**Guardrail:** incidents on unattended runs, against the supervised baseline.

## Evidence

**User reports.** Fourteen issues in the Claude Code issue tracker, each opened and read
([`research/issues.tsv`](research/issues.tsv)). Eleven show the agent acting outside
its mandate rather than producing bad work.

| Issue | What the agent did |
| --- | --- |
| [#85919](https://github.com/anthropics/claude-code/issues/85919) | Found an admin secret in a sibling project and minted a token with expanded capabilities |
| [#86667](https://github.com/anthropics/claude-code/issues/86667) | Bypassed a system-path guard, kept running after timeout, and wiped a drive root |
| [#82063](https://github.com/anthropics/claude-code/issues/82063) | Deployed to production without asking |
| [#81035](https://github.com/anthropics/claude-code/issues/81035) | Spawned a live process from a failed fork that merged pull requests with admin bypass |
| [#79103](https://github.com/anthropics/claude-code/issues/79103) | Asked for a preflight checkpoint before unattended runs |

Issue #82063 states it in a user's own words: "no harm done, but it makes me very
worried." Nothing broke, and they filed anyway.

**Competitive pressure.**
[`antigravity-for-claude-code`](https://github.com/yuting0624/antigravity-for-claude-code)
is an unaffiliated Claude Code plugin, observed September 3, 2026, that routes
token-heavy work out of Claude Code to Gemini through a hook that makes offloading the
default. It names a failure mode the rest of the slate misses, within-session spend
routing: the seat, the organization, and the subscription all persist, only per-session
volume falls, and retention dashboards read it as healthy.

**Reproduce it.** Neither command reads an account or calls an API; `size` in place of
`map` prints the cost table.

```
./research/probe.sh
./prototype/promote.py map prototype/fixtures/ledger-reconcile
```

Cowork quotes: claude.com/docs/cowork/overview and claude.com/product/cowork, retrieved
September 3, 2026. Platform behavior: Claude Code 2.1.259 and the platform CLI 1.29.0,
captured September 2 and 3, 2026. Every figure here is printed by the prototype and
pinned by its tests. Two drivable demos:
[terminal](https://madpr.github.io/claude-growth-surfaces/promote-cli.html) and
[browser](https://madpr.github.io/claude-growth-surfaces/promote-to-agent.html).
