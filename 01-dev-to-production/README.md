# Move unattended work to Managed Agents

Claude Code runs agents while a developer watches. Managed Agents runs them unwatched,
inside a spend cap, a quality rubric, and a sandbox that never shows the agent its own
credentials. Nothing moves a project from one to the other; this proposal builds that
path, with the limits set before the first unattended run.

**Status:** Case written, prototype running, two drivable demos · **Cost:** 1 to 2 months ·
**Theme:** expansion

Two drivable demos: [terminal](https://madpr.github.io/claude-growth-surfaces/promote-cli.html) and
[browser](https://madpr.github.io/claude-growth-surfaces/promote-to-agent.html).

## Problem

The obvious words typed into Claude Code (`claude agents`, `environment`, `session`,
`budget`) all return local answers, so the search ends there. The platform CLI reported
a different organization ID than Claude Code for the same email; that organization
already held a workspace named, exactly, "Claude Code", and my hosted agent list was
empty. That boundary is the revenue event, a flat subscription fee becoming metered
usage plus runtime.

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

## Proposed experience

One command turns a working project into a hosted agent, the sandbox it runs in, and the
schedule it runs on. The command makes the developer create the sandbox, set its limits,
and fill in the gaps, with nothing defaulted.

## Success metrics

| Metric | What it tests |
| --- | --- |
| Workloads that move to unattended operation, against their supervised baseline | The core claim |
| Spend 90 days after the move | Lagging. The revenue claim |

Guardrail: incidents on unattended runs, against the supervised baseline.

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
