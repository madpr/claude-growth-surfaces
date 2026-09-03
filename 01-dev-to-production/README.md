# Move unattended work to Managed Agents

Claude Code runs agents that you supervise. Managed Agents runs agents that you don't.
The unattended workload is worth far more per customer, and almost nobody crosses from
one to the other.

This proposal adds the crossing: a path from a working Claude Code project to a hosted
agent that runs on a schedule, inside limits you set before it runs.

**Status:** case written, prototype running, design unfinished.
**Cost:** 1–2 months.
**Theme:** expansion.

## Problem

A supervised workload is a $10-per-month prototype. The same workload running
unattended is a $1,000-per-month production workload. Managed Agents is where the
unattended version gets its limits: spend caps, quality rubrics, and credentials the
agent never sees.

Three things stop developers from getting there:

- **They can't find it.** Anthropic ships two command-line tools that split one account.
  `claude` is where developers work. `ant` owns the hosted-agent surface, and the
  platform docs recommend it. The two collide on every word someone would search.
- **Neither tool points at the other.** `claude import` reads configuration from
  *competing* agents. It has no outbound equivalent, and the platform tool has no
  awareness of Claude Code at all.
- **They're different accounts.** Claude Code signs in against a subscription. The
  platform signs in against a developer organization. On the account tested, those were
  two different organizations for one email address.

### The vocabulary collision

Search for the hosted product from inside Claude Code and every term answers locally:

| A developer types | They get | The hosted product means |
| --- | --- | --- |
| `agents` | Background sessions on their laptop | A stored, versioned hosted agent |
| `environment` | A pool for cloud sessions | The sandbox an agent runs in |
| `session` | A local conversation they can resume | A hosted run that bills runtime |
| `budget` | A flag that works in one mode | An enforced spend cap |
| `auth` | Sign in to Claude Code | Sign in to the platform |

Four of the five return a plausible local answer. Nothing signals a larger surface
exists, so the search ends.

### Why the account split matters

- Promotion crosses an identity boundary, not a tooling gap. Whatever transfers lands
  in an organization the developer isn't signed in to.
- That boundary is the revenue event. Subscription work is flat-fee. Hosted agents bill
  usage plus runtime. Moving a workload across converts it.
- It explains the timeline. Renaming a command takes days. Reconciling two identities
  doesn't, and that's the honest reason this costs 1–2 months.

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

From a working project, one command creates the hosted agent, the sandbox it runs in,
and the schedule it runs on.

Most of what the agent needs already exists on disk — the model, the instructions, the
tools, the skills, the connected services. The developer doesn't re-enter any of it.

Two things don't come along, and both shape the product:

- **The limits don't transfer.** The rules a developer set locally have no hosted
  equivalent. The flow has to make them set those limits again on the sandbox, and
  that's the moment worth designing well: it's the last point before the agent runs
  without anyone watching.
- **The sandbox can't be inferred.** A laptop has no container image, network policy,
  or credential store to hand over. Creating one is a required step, not a default.

Building the prototype changed this section twice. An early version assumed nearly
everything carried over; measuring it showed that three fields transfer intact, three
arrive degraded, and two kinds of working configuration have no destination at all.
The gap is the product.

## Why the destination is worth reaching

Hosted agents are the same model with an orchestrator above it. The limits belong to
that orchestrator:

| Limit | Building it yourself | Hosted |
| --- | --- | --- |
| Cost | Track usage and stop your own loop | A dollar cap enforced between model requests |
| Quality | Call a second model against a rubric | A required rubric, graded in a separate context |
| Authority | A container with scoped credentials | A per-session sandbox where secrets are substituted at egress and never visible inside |

A competent team can build the first two. The third is different in kind: the secret
never enters the sandbox, so the agent never holds the credential material.

That answers the sharpest report in the corpus. An agent hit a permissions error,
searched for a way through, found an admin secret in a sibling project, and minted
itself a token. Scoping the credential wouldn't have stopped it. Not holding it would.

## Success metrics

| Metric | What it tests |
| --- | --- |
| Workloads that move to unattended operation, against their own supervised baseline | The core claim |
| Spend 90 days after the move | The revenue claim. It lags. |
| Share of runs that set a spend cap and a rubric | Whether limits were the reason people came |

**Guardrail:** incidents on unattended runs. If promotion moves the failure instead of
containing it, this proposal is wrong.

**Leading indicators**, all watchable today: growth in traffic that runs on a schedule,
growth in hosted-agent sessions, and the share of those that set a cap or a rubric.

## Ship the pointer first

Test discovery before building the promotion path:

1. Disambiguate `claude agents`.
2. Name the hosted destination in the CLI.
3. Watch hosted-agent creation for 30 days.

This takes days. If creation doesn't move, discovery isn't the gate and this proposal
is wrong.

## Risks and open questions

- **The identity finding rests on one account, on a consumer subscription.** If a
  Console organization resolves to a single organization, that section describes a
  segment rather than the platform. Check a second account first.
- **"Identity reconciliation is hard" is inferred, not verified.** Two findings would
  invalidate the estimate: existing organization-linking already solves it, or the split
  is deliberate because subscriptions and metered billing are different business models.
  If it's deliberate, unifying them is a policy argument, not a growth feature.
- **Timing.** If unattended fleets are three years out rather than one, this is a
  correct proposal built two years early.
- **Rubrics fit artifact work**, such as reports and pipelines. They fit open-ended
  codebase maintenance badly, which is where the evidence came from.
- **This resembles the migration proposal.** Gating untrusted work on a check you
  specify is that proposal's hypothesis too.
- **The grader is Claude judging Claude.**
- **Some teams won't accept a hosted sandbox** for work that touches their own
  infrastructure, which is the work with the largest blast radius.
- **A team that already built its own metering and containment** gains only credential
  isolation, and pays a migration to get it.

Four numbers decide this, and all of them are internal:

- What fraction of API organizations run anything unattended.
- How many have a single-day spend spike over five times their trailing average.
- What share of Claude Code users have ever created a hosted agent, and what share of
  hosted agents were created by someone who already had Claude Code installed.
- What share of Claude Code sessions delegate work to a non-Anthropic model.

## Evidence

**User reports.** Fourteen issues in `anthropics/claude-code`, each opened and read
([`research/issues.tsv`](research/issues.tsv)). Eleven show the agent acting outside its
mandate rather than producing bad work.

| Issue | What the agent did |
| --- | --- |
| [#85919](https://github.com/anthropics/claude-code/issues/85919) | Found an admin secret in a sibling project and minted a token with expanded capabilities |
| [#86667](https://github.com/anthropics/claude-code/issues/86667) | Bypassed a system-path guard, kept running after timeout, and wiped a drive root |
| [#82063](https://github.com/anthropics/claude-code/issues/82063) | Deployed to production without asking |
| [#81035](https://github.com/anthropics/claude-code/issues/81035) | Spawned a live process from a failed fork that merged pull requests with admin bypass |
| [#79103](https://github.com/anthropics/claude-code/issues/79103) | Asked for a preflight checkpoint before unattended runs |

Issue #82063 states the problem in a user's own words: "no harm done, but it makes me
very worried." Nothing broke, and they filed anyway. These are Claude Code issues, not
API issues. They show the behavior at laptop scale. They don't prove it happens against
shared infrastructure.

**Competitive pressure.**
[`antigravity-for-claude-code`](https://github.com/yuting0624/antigravity-for-claude-code)
is an unaffiliated Claude Code plugin with 303 stars that routes token-heavy work out of
Claude Code to Gemini. It installs a hook that makes offloading the default.

Routing to a competitor needs no identity work: different vendor, separate credentials,
nobody expects one account. Routing to Anthropic's own hosted product needs it precisely
because it's the same company. The exit is cheaper to build than the entrance.

This proposal doesn't cite the plugin's cost benchmark, which rests on one task, a
three-case quality evaluation, and estimated rates the author tells you to replace. The
citable fact is that the plugin exists and what it claims.

It also names a failure mode the rest of the slate misses: **within-session spend
routing**. The customer never churns. The seat, the organization, and the subscription
all persist. Only per-session volume falls, so retention dashboards read it as healthy.

**Reproduce it.** Run these from this directory. Neither reads an account or calls an
API:

```
./research/probe.sh
./prototype/promote.py map prototype/fixtures/sample-project
```

One command needs credentials. It reports only whether the two organizations agree, and
prints no identifier, workspace, email, or name:

```
./research/probe.sh --identity
```

Platform behavior was captured September 2–3, 2026, from Claude Code 2.1.259 and the
platform CLI 1.29.0. Every count in this document is printed by the prototype, so the
case and the code can't disagree. One documented behavior doesn't reproduce: the docs
warn that signing in to the platform tool triggers a credential conflict with Claude
Code. It doesn't. The two never contend, because they resolve to different
organizations.
