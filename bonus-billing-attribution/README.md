# Billing attribution

I set an API key in my shell for an unrelated project and Claude Code quietly
started billing my Console account instead of the subscription I pay for, and
the diagnostic said nothing had changed. There are 26 public issues describing
the same misattribution, and the four that put a dollar figure on it add up to
$1,799.83.

**Status:** Defect reproduced, proposal written, drivable mock ·
**Cost:** three releases (announce, warn, switch) · **Theme:** retention

## Why this is outside the slate

Under the decision rule the top README states (work stays on the subscription
while it is one person's, and moves to the platform when it bills an
organization rather than a person), this item is the guarantee that one
person's interactive session is never billed to an organization without saying
so.

## Findings

I first saw this on Claude Code v2.1.252 on 31 August 2026 and reproduced it
on v2.1.260 on 3 September 2026.

```
$ claude auth status --json | jq -c '{authMethod,apiProvider,subscriptionType}'
{"authMethod":"claude.ai","apiProvider":"firstParty","subscriptionType":"pro"}

$ ANTHROPIC_API_KEY=sk-ant-… claude auth status --json | jq -c '…'
{"authMethod":"claude.ai","apiProvider":"firstParty","subscriptionType":null}
```

Reproduced 3/3. Only `subscriptionType` moves, from `"pro"` to null.
`ANTHROPIC_AUTH_TOKEN` at least relabels itself to `oauth_token`, and an
empty-string key is ignored; `ANTHROPIC_API_KEY` alone displaces the
subscription and says nothing. This is documented behavior. The default is
wrong.

## Evidence

There are 26 public issues on silent billing misattribution, September 2025
to August 2026, 20 still open, and the filing rate was one or two a month
through spring, then 5, 8, and 6 across June, July, and August.

| Issue | Filed | Self-reported | Mechanism |
|---|---|---|---|
| [#86723](https://github.com/anthropics/claude-code/issues/86723) | 2026-08 | $1,122.83 | env var in Routines cloud environment |
| [#62338](https://github.com/anthropics/claude-code/issues/62338) | 2026-05 | $447.00 | billed to API instead of Max |
| [#39903](https://github.com/anthropics/claude-code/issues/39903) | 2026-03 | $152.00 | subagent dispatch used the API key |
| [#78491](https://github.com/anthropics/claude-code/issues/78491) | 2026-07 | $78.00 | shell profile export, 17 days unnoticed |
| | | **$1,799.83** | four issues; twenty-two carry no figure |

[#78491](https://github.com/anthropics/claude-code/issues/78491) asks for this
exact fix in its title: *"request louder consent + persistent indicator."*

The existing diagnostics can also be wrong:
[#74217](https://github.com/anthropics/claude-code/issues/74217) reports `/status`
showing one account while billing another, and
[#84015](https://github.com/anthropics/claude-code/issues/84015) a Max session
labeled "Claude API account."

## Proposed fix

Full design: **[proposal-credential-precedence.md](proposal-credential-precedence.md)**

Add `CLAUDE_CODE_API_KEY` for stated billing intent and demote
`ANTHROPIC_API_KEY` below the subscription.

| Level | Current | Proposed |
|---|---|---|
| 3 | `ANTHROPIC_API_KEY` | **`CLAUDE_CODE_API_KEY`** |
| 7 | Subscription (`/login`) | Subscription (`/login`) |
| 8 | — | **`ANTHROPIC_API_KEY`** |

The demotion is the change that matters; the new variable makes it safe. On
the web, environment API keys already "don't override your subscription
credentials," per the docs, and this brings the CLI in line. Three releases:
announce the variable, warn when the key
displaces a subscription (plus a rebill key for interactive sessions), then
switch the order. A machine with no subscription falls through to level 8
unchanged; behavior changes only for people with both a subscription and an
ambient `ANTHROPIC_API_KEY`, the people filing the issues.

## Prototype

`prototype/statusline-billing.sh` is the stage 2 warning. Since `authMethod`
is the same in both states, it probes `claude auth status` twice, with and
without the credential variables, and compares:

```bash
resolved=$(claude auth status --json)
latent=$(env -u ANTHROPIC_API_KEY -u ANTHROPIC_AUTH_TOKEN claude auth status --json)
[ -z "$resolved_sub" ] && [ -n "$latent_sub" ] && state=CONFLICT
```

Three states; a key with no subscription behind it is correct billing and gets
no warning:

```
◆ PRO SUB · Opus                       subscription pays
████░░░░░░ 41% · 5h 62% · caps in ~23min

▲ API KEY ····4f2a · Opus              displaced an entitlement
ANTHROPIC_API_KEY displaced your pro subscription
  ↳ press ⌥B to bill the subscription instead

◇ API KEY ····test · Opus              correct, and silent
████░░░░░░ 41% · $2.14
```

`caps in ~23min` is arithmetic on `rate_limits.five_hour` from the payload.

### Run it

```bash
# against the captured session fixture
./prototype/statusline-billing.sh < prototype/mock-session.json

# force the displaced state
ANTHROPIC_API_KEY=sk-ant-test0000000000000000000000004f2a \
  ./prototype/statusline-billing.sh < prototype/mock-session.json
```

The capture's window has since reset, so a raw replay prints `finishes`;
re-clock it for the projection above:

```bash
jq '.rate_limits.five_hour.resets_at = (now + 2100 | floor)' \
  prototype/mock-session.json | ./prototype/statusline-billing.sh
```

As a status line command, the auth probe costs ~210 ms and is cached for 30 s,
keyed on a fingerprint of the credential env vars; render is 68 ms.

## Mock

`page/who-is-paying.html`: drive the precedence order at
<https://madpr.github.io/claude-growth-surfaces/who-is-paying.html>

A terminal you type into: export the key, start a session, and watch which
credential pays, on a laptop with a subscription or a build box without one,
under either precedence order. The dialog, auth status fields, and `/cost`
layout are copied from Claude Code v2.1.260; the proposal's additions are
marked in the transcript.
