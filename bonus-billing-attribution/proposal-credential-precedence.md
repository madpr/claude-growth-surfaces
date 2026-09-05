# Separate the Claude Code billing credential from the SDK credential

## Overview

Claude Code reads `ANTHROPIC_API_KEY` and bills the associated Claude Console
account, even when you have an active Pro, Max, Team, or Enterprise
subscription. The variable is usually set for an application you're building
and says nothing about how your editor should be billed.

This proposal adds `CLAUDE_CODE_API_KEY`, which states billing intent
explicitly, and moves `ANTHROPIC_API_KEY` below your subscription in the
credential precedence order.

## Background

When several credentials are present, Claude Code selects one using a documented
seven-level precedence order:

| Level | Credential |
|---|---|
| 1 | Cloud provider credentials (`CLAUDE_CODE_USE_BEDROCK`, `CLAUDE_CODE_USE_VERTEX`, `CLAUDE_CODE_USE_FOUNDRY`) |
| 2 | `ANTHROPIC_AUTH_TOKEN` |
| 3 | `ANTHROPIC_API_KEY` |
| 4 | `apiKeyHelper` script output |
| 5 | `CLAUDE_CODE_OAUTH_TOKEN` |
| 6 | Anthropic profile and federation credentials |
| 7 | Subscription OAuth credentials from `/login` |

Your subscription ranks last. Claude Code asks you to approve
`ANTHROPIC_API_KEY` the first time it appears in an interactive session and
remembers the answer; in non-interactive mode (`claude -p`) it uses the key
without asking.

## Problem

`ANTHROPIC_API_KEY` is the credential the Anthropic SDKs read. Exporting it in
`~/.zshrc`, committing it to a project `.env` file, or baking it into a
container image configures an application; Claude Code reads the same variable
as a billing instruction.

The approval prompt appears once, in interactive mode, and the answer persists
to scheduled runs, cron jobs, continuous integration, and Routines, which never
prompt and which nobody watches, so an unintended charge accrues until someone
checks the Console.

Checking won't tell you either. With `ANTHROPIC_API_KEY` set,
`claude auth status --json` still reports `"authMethod": "claude.ai"` and
`"apiProvider": "firstParty"`; only `subscriptionType` changes, from your plan
name to `null`.

For the reproduction, the 26 public issues in this class, and the $1,799.83 that
four users report losing to it, see [README.md](README.md).

## Precedent

Claude Code already does this on the web. From the
[authentication documentation](https://code.claude.com/docs/en/authentication):

> Claude Code on the Web always uses your subscription credentials. If you set
> `ANTHROPIC_API_KEY` or `ANTHROPIC_AUTH_TOKEN` in the sandbox environment, it
> doesn't override your subscription credentials.

The naming is also established. Claude Code namespaces its own configuration
under `CLAUDE_CODE_*`, and `CLAUDE_CODE_OAUTH_TOKEN` is the direct parallel:
the way to hand Claude Code a *subscription* credential where browser login
isn't available. There is no namespaced equivalent for an API credential.

## Proposal

Make two changes to the precedence order.

1. Add `CLAUDE_CODE_API_KEY` at level 3, where `ANTHROPIC_API_KEY` is today.
2. Move `ANTHROPIC_API_KEY` below subscription credentials, to level 8.

| Level | Current | Proposed |
|---|---|---|
| 1 | Cloud provider credentials | Cloud provider credentials |
| 2 | `ANTHROPIC_AUTH_TOKEN` | `ANTHROPIC_AUTH_TOKEN` |
| 3 | `ANTHROPIC_API_KEY` | **`CLAUDE_CODE_API_KEY`** |
| 4 | `apiKeyHelper` | `apiKeyHelper` |
| 5 | `CLAUDE_CODE_OAUTH_TOKEN` | `CLAUDE_CODE_OAUTH_TOKEN` |
| 6 | Profile and federation | Profile and federation |
| 7 | Subscription (`/login`) | Subscription (`/login`) |
| 8 | — | **`ANTHROPIC_API_KEY`** |

`CLAUDE_CODE_API_KEY` takes the same value as `ANTHROPIC_API_KEY` and is sent
the same way, as the `X-Api-Key` header; setting it tells Claude Code how to
bill this tool rather than telling an SDK how to reach the API.

The unintended charges come through `ANTHROPIC_API_KEY`, so the demotion is the
change that matters; the new variable makes it safe by giving you a way to keep
API billing deliberately.

### Scope

Change the precedence of `ANTHROPIC_API_KEY` only. `apiKeyHelper` lives in a
settings file, a deliberate act, and `ANTHROPIC_AUTH_TOKEN` routes through an
LLM gateway or proxy, also deliberate and usually environment-wide by design.
`ANTHROPIC_API_KEY` is the only credential in the list that developers commonly
set for reasons unrelated to Claude Code.

## Effect on existing configurations

| Your setup | Behavior today | Behavior after the change |
|---|---|---|
| `ANTHROPIC_API_KEY` set, no subscription on the machine (CI, containers, API-only developers) | API billing | API billing, unchanged. The key falls through to level 8. |
| `ANTHROPIC_API_KEY` set for an application, active subscription | API billing, usually unintended | Subscription billing |
| API billing wanted despite an active subscription | API billing | Set `CLAUDE_CODE_API_KEY` to keep API billing |
| Bedrock, Vertex, Foundry, or a gateway | Provider credential | Provider credential, unchanged |
| `apiKeyHelper` configured | Helper output | Helper output, unchanged |

Only the second row changes behavior without action, and that is the population
reporting unintended charges.

## Migration

To keep API billing on a machine with a subscription:

```bash
export CLAUDE_CODE_API_KEY="$ANTHROPIC_API_KEY"
```

The rollout has three stages.

1. **Announce.** Add `CLAUDE_CODE_API_KEY` at level 3 and document it.
   `ANTHROPIC_API_KEY` stays at level 3 too, with `CLAUDE_CODE_API_KEY` winning
   when both are set. No existing configuration changes behavior.
2. **Warn.** When `ANTHROPIC_API_KEY` selects API billing on a machine with an
   active subscription, say so at session start, in every session type
   including `claude -p`: name the variable, name the displaced subscription,
   and give the one-line migration command. Sessions with no subscription
   present produce no warning.
3. **Switch.** Move `ANTHROPIC_API_KEY` to level 8, after the warning has been
   live for a full release window.

**Caution:** Don't skip stage 2. Unattended sessions are where this costs money
and where a silent change of billing source is hardest to notice.

The stage 2 warning works by probing `claude auth status` with and without the
credential variables and comparing, since the reported auth method is the same
in both states.

### The rebill key

When the warning fires in an interactive session, one keystroke switches
billing for the rest of that session to your subscription. The proposal binds
it to Option+B and appends the hint to the warning:

```
ANTHROPIC_API_KEY displaced your pro subscription
  ↳ press ⌥B to bill the subscription instead
```

Pressing it prints what changed and the permanent fix, and the status line then
reports the subscription as paying:

```
Billing switched to your pro subscription for this session.
To make it permanent: unset ANTHROPIC_API_KEY
```

The change lasts for the current session only; the next session starts on
`ANTHROPIC_API_KEY` again until you apply the fix. Non-interactive sessions get
the warning and no key.

## Alternatives considered

**Warn but don't change precedence.** Keeps every existing configuration working
and needs no migration. Rejected as insufficient on its own: a warning that
appears in every session becomes background noise, and the problem persists for
anyone who dismisses it. That is why warning is stage 2 of the migration and
the switch is stage 3.

**Prompt in non-interactive mode.** A prompt requires someone to answer it.
Scheduled runs and continuous integration have no one at the terminal, so the
session either blocks or falls back to the current behavior.

**Ignore `ANTHROPIC_API_KEY` entirely.** Simpler to describe, but it breaks
continuous integration, containers, and API-only developers, none of whom are
affected by the problem. The demotion achieves the same outcome for the affected
population and leaves everyone else working.

**Report the active credential accurately and stop there.** Fixes the diagnostic
gap described in [Problem](#problem) and leaves the default alone. You'd still
have to check, and unattended sessions still have no one checking.

## Success metrics

| Metric | Direction | Reads as |
|---|---|---|
| Sessions billed to `ANTHROPIC_API_KEY` on machines with an active subscription | Down | The problem class shrinking |
| New issues filed in this class | Down | Users no longer encountering it |
| Sessions setting `CLAUDE_CODE_API_KEY` | Up, then flat | Deliberate API users migrating successfully |
| Support contacts about unexpected Console charges | Down | The outcome the change exists to produce |
| Stage 2 warnings shown per week | Down over the window | Migration progressing rather than stalling |
