# Separate the Claude Code billing credential from the SDK credential

## Overview

Claude Code reads `ANTHROPIC_API_KEY` and bills the associated Claude Console
account, even when you have an active Pro, Max, Team, or Enterprise
subscription. In most environments, `ANTHROPIC_API_KEY` is set for an
application that you're building, not to choose how your editor is billed.

This proposal adds a `CLAUDE_CODE_API_KEY` environment variable that states your
billing intent explicitly, and moves `ANTHROPIC_API_KEY` below your subscription
in the credential precedence order.

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

Your subscription ranks last. Every environment credential outranks it.

Claude Code prompts you to approve `ANTHROPIC_API_KEY` the first time it appears
in an interactive session, and remembers your answer. In non-interactive mode
(`claude -p`), Claude Code uses the key whenever it's present and doesn't prompt.

## Problem

Three properties combine to produce charges that you don't intend and can't see.

**The variable is ambiguous.** `ANTHROPIC_API_KEY` is the credential that the
Anthropic SDKs read. When you export it in `~/.zshrc`, commit it to a project
`.env` file, or set it in a container image, you're configuring an application.
Claude Code interprets the same variable as an instruction about billing.

**Consent doesn't cover the unattended case.** The approval prompt appears once,
in interactive mode, and your answer persists to every later session. Scheduled
runs, cron jobs, continuous integration, and Routines never prompt. These are the
sessions you don't watch, so an unintended charge accrues until you check the
Console.

**The active credential isn't reported accurately.** Setting `ANTHROPIC_API_KEY`
displaces your subscription, but `claude auth status --json` continues to report
`"authMethod": "claude.ai"` and `"apiProvider": "firstParty"`. Only
`subscriptionType` changes, from your plan name to `null`. If you check which
credential is paying, the answer looks unchanged.

For the reproduction, the 26 public issues in this class, and the $1,799.83 that
four users report losing to it, see [README.md](README.md).

## Precedent

Claude Code already implements this proposal on another surface. From the
[authentication documentation](https://code.claude.com/docs/en/authentication):

> Claude Code on the Web always uses your subscription credentials. If you set
> `ANTHROPIC_API_KEY` or `ANTHROPIC_AUTH_TOKEN` in the sandbox environment, it
> doesn't override your subscription credentials.

The web surface treats an environment API key as unrelated to how Claude Code is
billed. The command-line interface doesn't. This proposal makes the two
consistent.

The naming is also established. Claude Code namespaces its own configuration
under `CLAUDE_CODE_*`, including `CLAUDE_CODE_USE_BEDROCK`,
`CLAUDE_CODE_API_KEY_HELPER_TTL_MS`, and `CLAUDE_CODE_OAUTH_TOKEN`. The last of
these is the direct parallel: it's how you hand Claude Code a *subscription*
credential in an environment where browser login isn't available. No namespaced
equivalent exists for an API credential.

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

`CLAUDE_CODE_API_KEY` accepts the same value as `ANTHROPIC_API_KEY` and is sent
the same way, as the `X-Api-Key` header. The only difference is what setting it
means: you're telling Claude Code how to bill this tool, rather than telling an
SDK how to reach the API.

Adding the variable without moving `ANTHROPIC_API_KEY` doesn't solve the problem.
The unintended charges happen through `ANTHROPIC_API_KEY`, so the demotion is the
change that matters. The new variable is what makes the demotion safe, because it
gives you a way to keep API billing deliberately.

### Scope

Change the precedence of `ANTHROPIC_API_KEY` only. Leave `ANTHROPIC_AUTH_TOKEN`
and `apiKeyHelper` where they are:

* You configure `apiKeyHelper` in a settings file, which is a deliberate act.
* You set `ANTHROPIC_AUTH_TOKEN` to route through an LLM gateway or proxy, which
  is also deliberate and usually environment-wide by design.

`ANTHROPIC_API_KEY` is the only credential in the list that developers commonly
set for a purpose unrelated to Claude Code. Limiting the change to that variable
keeps the proposal narrow enough to evaluate.

## Effect on existing configurations

| Your setup | Behavior today | Behavior after the change |
|---|---|---|
| `ANTHROPIC_API_KEY` set, no subscription on the machine (CI, containers, API-only developers) | API billing | API billing, unchanged. The key falls through to level 8. |
| `ANTHROPIC_API_KEY` set for an application, active subscription | API billing, usually unintended | Subscription billing |
| API billing wanted despite an active subscription | API billing | Set `CLAUDE_CODE_API_KEY` to keep API billing |
| Bedrock, Vertex, Foundry, or a gateway | Provider credential | Provider credential, unchanged |
| `apiKeyHelper` configured | Helper output | Helper output, unchanged |

Only one row changes behavior without action: a machine that has both a
subscription and an ambient `ANTHROPIC_API_KEY`. That's the population reporting
unintended charges.

**Note:** Most continuous integration environments have no subscription
credential on the machine, so the demotion is a no-op for them. The change
reaches only environments where a subscription is already signed in.

## Migration

To preserve API billing on a machine that has a subscription, set the new
variable:

```bash
export CLAUDE_CODE_API_KEY="$ANTHROPIC_API_KEY"
```

Roll the change out in three stages:

1. **Announce.** Add `CLAUDE_CODE_API_KEY` at level 3 and document it. Keep
   `ANTHROPIC_API_KEY` at level 3 as well, with `CLAUDE_CODE_API_KEY` winning
   when both are set. No existing configuration changes behavior.
2. **Warn.** When `ANTHROPIC_API_KEY` selects API billing on a machine that has
   an active subscription, report it at session start, in every session type
   including `claude -p`. Name the variable, name the displaced subscription, and
   give the one-line migration command. Sessions with no subscription present
   produce no warning, because their billing is already correct.
3. **Switch.** Move `ANTHROPIC_API_KEY` to level 8.

**Caution:** Don't skip stage 2. Unattended sessions are where the cost of this
behavior lands, and they're also where a silent change of billing source is
hardest to notice in either direction.

The status line in [prototype/statusline-billing.sh](prototype/statusline-billing.sh)
implements the stage 2 signal. It detects displacement rather than reading the
reported auth method, by probing `claude auth status` twice — once as the
environment stands, and once with the credential variables stripped — and
comparing the results.

## Alternatives considered

**Warn but don't change precedence.** Keeps every existing configuration working
and needs no migration. Rejected as insufficient on its own: a warning that
appears in every session becomes background noise, and the problem persists for
anyone who dismisses it. This is stage 2 of the migration, not a destination.

**Prompt in non-interactive mode.** A prompt requires someone to answer it.
Scheduled runs and continuous integration have no one at the terminal, so the
session either blocks or falls back to the current behavior.

**Ignore `ANTHROPIC_API_KEY` entirely.** Simpler to describe, but it breaks
continuous integration, containers, and API-only developers, none of whom are
affected by the problem. The demotion achieves the same outcome for the affected
population and leaves everyone else working.

**Report the active credential accurately and stop there.** Fixes the diagnostic
gap described in [Problem](#problem) but not the default. You'd still have to
check, and unattended sessions still have no one checking.

## Risks

**A developer misses the migration and their billing source changes.** Someone
who wants API billing, has a subscription, and ignores the stage 2 warning moves
onto subscription billing without acting. The consequence is bounded: their
subscription usage rises and their API spend falls, and no charge occurs that
they didn't already agree to. Mitigate with the warning window and by naming the
exact command in the message.

**Another variable becomes the ambiguous one.** If tooling starts setting
`CLAUDE_CODE_API_KEY` broadly, the problem returns under a new name. This is
unlikely, because the name has no meaning outside Claude Code — which is the
property the proposal depends on.

**Subscription rate limits become the constraint instead.** A developer moved
from API billing to subscription billing gains a rate-limit ceiling they didn't
have. Report remaining headroom in the same surface that reports the credential,
so the tradeoff is visible at the moment it applies.

## Success metrics

| Metric | Direction | Reads as |
|---|---|---|
| Sessions billed to `ANTHROPIC_API_KEY` on machines with an active subscription | Down | The problem class shrinking |
| New issues filed in this class | Down | Users no longer encountering it |
| Sessions setting `CLAUDE_CODE_API_KEY` | Up, then flat | Deliberate API users migrating successfully |
| Support contacts about unexpected Console charges | Down | The outcome the change exists to produce |
| Stage 2 warnings shown per week | Down over the window | Migration progressing rather than stalling |

If the first metric is near zero before the change ships, this is a support
problem rather than a product one, and the proposal doesn't justify the
migration cost. That query decides whether to build it.
