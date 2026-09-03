# Move unattended work to Managed Agents

Claude Code runs agents that you supervise. Managed Agents runs agents that you don't.
The unattended workload is worth far more per customer, and almost nobody crosses from
one to the other.

This proposal adds the missing path: a command in `claude` that turns a working project
into a hosted agent, and tells you what it can't carry across.

**Status:** case written, prototype running, product design unfinished.
**Cost:** 1–2 months.
**Theme:** expansion.

## Problem

A supervised workload is a $10-per-month prototype. The same workload running
unattended is a $1,000-per-month production workload. Managed Agents is where the
unattended version gets its limits: session budgets, outcome rubrics, and vault
credentials that the agent never sees.

Three things stop developers from getting there:

- **You can't find it.** Anthropic ships two command-line tools that split one account.
  `claude` is where you work. `ant` owns the hosted-agent control plane, and the
  platform docs recommend it over the SDK. The two collide on every word you would
  search.
- **Neither tool points at the other.** `claude import` reads configuration from
  *competing* agents, and has no outbound equivalent. `ant` has no reference to Claude
  Code anywhere in its agent, environment, or deployment commands.
- **They're different accounts.** `claude` signs in through claude.ai against a
  subscription. `ant` signs in against a developer organization. On the account tested,
  those were two different organizations for one email address, and the developer
  organization already held a workspace named `Claude Code` that the Claude Code CLI
  wasn't signed in to.

### The vocabulary collision

| Word | In `claude` | In `ant` |
| --- | --- | --- |
| `agents` | Background sessions on your laptop | A stored, versioned hosted agent |
| `environment` | A `ccpool_` pool for cloud sessions | An `env_` container spec |
| `session` | A local conversation you can resume | A hosted run that bills container runtime |
| `budget` | `--max-budget-usd`, `--print` mode only | An enforced, create-only session budget |
| `auth` | `login`, `logout`, `status` | `login`, `logout`, `status` |

Four of the five terms return a plausible local answer. Nothing tells you a larger
surface exists, so you stop searching.

### Why the account split matters

- Promotion crosses an identity boundary, not just a tooling gap. Whatever the mapping
  carries, it lands in an organization you aren't signed in to.
- That boundary is also the revenue event. Subscription work is flat-fee. Managed Agents
  bills tokens plus container runtime. Moving a workload across converts it.
- It explains the timeline. Renaming a command takes days. Reconciling a subscription
  identity with a platform organization doesn't, and that's the honest reason this costs
  1–2 months.

## Solution

Add a promotion path to `claude`. It reads the project you already have and creates the
three objects Managed Agents needs: an agent, an environment, and a deployment.

Run the prototype:

```
cd 01-dev-to-production/prototype
./promote.py map fixtures/sample-project
```

It reads a project directory, writes the `agent.yaml` that `ant beta:agents create`
accepts, and reports every field that doesn't survive:

```
resolved 3   lossy 3   human 1   blocked 2   underivable 1
```

### What transfers

| Field | Source | Notes |
| --- | --- | --- |
| `name` | Directory name | |
| `model` | `.claude/settings.json` | Resolves the alias. `sonnet` becomes `claude-sonnet-5`. |
| `system` | `CLAUDE.md` | |
| `tools` | `settings.json` permissions | Whole-tool enable and disable only. |
| `skills` | `.claude/skills` | Names carry. You must upload each skill to the Skills API. |
| `mcp_servers` | `.mcp.json` | URL-based servers only. |
| `description` | None | The one field a person writes. |

### What doesn't transfer

Counting fields overstates what survives. Two kinds of working configuration have no
destination field at all:

| What | Why it can't cross |
| --- | --- |
| Command-pattern permissions, such as `Bash(rm *)` and `Write(ledger/**)` | The hosted toolset enables or disables a whole tool. Finer control belongs to the environment, through the sandbox and vault egress. |
| Stdio MCP servers | Managed Agents connects to servers of `type: "url"` over Streamable HTTP. Publish the server as an endpoint first. |
| The environment | A container image, a network policy, and credential vaults. A laptop has none of them to hand over. |

You set these limits again on the environment. That's why the promotion path has to
create one rather than copy it, and it's the step a developer can't skip.

## Why the destination is worth reaching

Managed Agents is the same inference with an orchestrator above it. The limits belong to
that orchestrator, not to the endpoint:

| Limit | Your own harness | Managed Agents |
| --- | --- | --- |
| Cost | Track `usage` and stop the loop | A dollar-denominated session budget, enforced between model requests |
| Quality | Call a second model against a rubric | `user.define_outcome`, graded in a separate context window |
| Authority | A container with scoped credentials | A per-session sandbox, with vault credentials substituted at egress |

A competent team can build the first two. The third is different in kind. Egress
substitution means the secret never enters the sandbox, so the agent never holds the
credential material.

That answers the sharpest issue in the corpus: an agent hit a 403, searched for a way
through, found an admin secret in a sibling project's `.env`, and minted itself a token.
Scoping the credential wouldn't have stopped it. Not holding it would have.

## Evidence from user reports

Fourteen issues in `anthropics/claude-code`, each opened and read. See
[`research/issues.tsv`](research/issues.tsv). Eleven show the agent acting outside its
mandate rather than producing bad work.

| Issue | What the agent did |
| --- | --- |
| [#85919](https://github.com/anthropics/claude-code/issues/85919) | Found an admin secret in a sibling project's `.env` and minted a token with expanded capabilities |
| [#86667](https://github.com/anthropics/claude-code/issues/86667) | Bypassed a system-path guard, kept running after timeout, and wiped the `C:\` drive root |
| [#82063](https://github.com/anthropics/claude-code/issues/82063) | Deployed to production without asking |
| [#81035](https://github.com/anthropics/claude-code/issues/81035) | Spawned a live process from a failed fork that merged pull requests with admin bypass |
| [#79103](https://github.com/anthropics/claude-code/issues/79103) | Asked for a preflight checkpoint before unattended runs |

Issue #82063 states the problem in a user's own words: "no harm done, but it makes me
very worried." Nothing broke, and they filed anyway.

These are Claude Code issues, not API issues. They show the behavior at laptop scale.
They don't prove it happens against shared infrastructure.

## Competitive pressure

[`antigravity-for-claude-code`](https://github.com/yuting0624/antigravity-for-claude-code)
is an unaffiliated Claude Code plugin with 303 stars. It routes token-heavy work out of
Claude Code to Gemini through Google's `agy` CLI. A `SessionStart` hook injects a
cost-aware routing policy, so after you install it, offloading is the default.

Routing to Gemini needs no identity work: different vendor, separate credentials, nobody
expects one account. Routing to Managed Agents needs it precisely because it's the same
company. The exit is cheaper to build than the entrance.

This proposal doesn't cite the plugin's benchmark. Its cost figures rest on one task, a
three-case quality evaluation, character-count estimates for the Gemini side, and rates
in a user-editable `prices.json` that the author tells you to replace before quoting any
figure. The citable fact is that the plugin exists and what it claims.

It also names a failure mode the rest of the slate misses: **within-session spend
routing**. The customer never churns. The seat, the organization, and the subscription
all persist. Only per-session token volume falls, so account-level retention dashboards
read it as healthy.

## Success metrics

| Metric | What it tests |
| --- | --- |
| Workloads that move to unattended operation, against their own supervised baseline | The core claim |
| Spend 90 days after the move | The revenue claim. It lags. |
| Share of sessions that set a budget and a rubric | Whether limits were the reason people came |

**Guardrail:** incidents on unattended runs. If promotion moves the failure instead of
containing it, this proposal is wrong.

**Leading indicators**, all watchable today: growth in traffic that runs on a schedule,
growth in Managed Agents sessions, and the share of those sessions that set a budget or
a rubric.

## Ship the pointer first

Test discovery before building the promotion path:

1. Disambiguate `claude agents`.
2. Name the hosted destination in the CLI.
3. Watch hosted-agent creation for 30 days.

This takes days. If creation doesn't move, discovery isn't the gate and this proposal
is wrong.

## Risks

- **The identity finding rests on one account, on a Pro subscription.** If a Console
  organization resolves to a single organization, the identity section describes a
  segment rather than the platform. Check a second account first.
- **"Identity reconciliation is hard" is inferred, not verified.** Two findings would
  invalidate the estimate: existing organization-linking already solves it, or the split
  is deliberate because subscriptions and metered billing are different business models.
  If it's deliberate, unifying them is a policy argument, not a growth feature.
- **Timing.** If unattended fleets are three years out rather than one, this is a
  correct proposal built two years early, and the engineering ages badly before anyone
  needs it.
- **Rubrics fit artifact work**, such as reports and pipelines. They fit open-ended
  codebase maintenance badly, which is where the corpus came from.
- **This resembles the migration proposal.** Gating untrusted work on a check you
  specify is that proposal's hypothesis too.
- **The grader is Claude judging Claude.**
- **Some teams won't accept a hosted sandbox** for work that touches their own
  infrastructure, which is the work with the largest blast radius.
- **A team that already built its own metering and containment** gains only the egress
  row, and pays a migration to get it.

## Reproduce these results

Run both from this directory. Neither reads an account or calls an API:

```
./research/probe.sh
./prototype/promote.py map prototype/fixtures/sample-project
```

`probe.sh` prints the collision table from the two installed binaries. `promote.py`
exits `1` when it finds fields that can't cross, which is the expected result for the
sample project.

One command needs credentials. It reports only whether the two organizations agree, and
prints no identifier, workspace, email, or name:

```
./research/probe.sh --identity
```

## Sources and limits

Platform quotations come from Anthropic documentation retrieved September 2, 2026.
Binary behavior comes from Claude Code 2.1.259 and `ant` 1.29.0, captured September 2–3,
2026. Every count in [What transfers](#what-transfers) is printed by `promote.py`, so
this document and the code can't disagree.

One documented behavior doesn't reproduce. The platform docs warn that signing in to
`ant` triggers a credential conflict with Claude Code. On the account tested, it didn't:
the two tools never contend, because they resolve to different organizations.

Four numbers decide this proposal, and all of them are internal:

- What fraction of API organizations run anything unattended.
- How many have a single-day spend spike over five times their trailing average.
- What share of Claude Code users have ever created a Managed Agent, and what share of
  Managed Agents were created by someone who already had Claude Code installed.
- What share of Claude Code sessions delegate work to a non-Anthropic model.
