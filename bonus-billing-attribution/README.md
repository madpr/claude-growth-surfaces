# Billing attribution

An API key left in the environment for another application silently displaces an
active Claude subscription in Claude Code, and the session bills the Console
account instead. The diagnostic that reports which credential is active gives
the same answer in both states. 26 public issues describe this misattribution,
and the four that carry a figure report losses totaling $1,799.83.

**Status:** Defect reproduced, proposal written, drivable mock ·
**Cost:** three releases (announce, warn, switch) · **Theme:** retention

## Why this is outside the slate

It is scoped to Claude Code rather than the platform. Its direct effect moves
spend from metered billing to a subscription the customer has already paid for.

Under the decision rule the top README states (work stays on the subscription
while it is one person's, and moves to the platform when it bills an
organization rather than a person), this item is the guarantee that one person's
interactive session is never billed to an organization without saying so. An
API-layer version of the same work, per-team spend attribution and budgets that
pause rather than terminate, is a platform item and is out of scope here.

## Findings

Verified on Claude Code v2.1.252, 31 August 2026, and reproduced on v2.1.260,
3 September 2026.

**The diagnostic surface reports the same answer in both states.** Setting
`ANTHROPIC_API_KEY` displaces an active subscription while `authMethod` continues
to report `"claude.ai"` and `apiProvider` continues to report `"firstParty"`. The
only signal is `subscriptionType` going null.

```
$ claude auth status --json | jq -c '{authMethod,apiProvider,subscriptionType}'
{"authMethod":"claude.ai","apiProvider":"firstParty","subscriptionType":"pro"}

$ ANTHROPIC_API_KEY=sk-ant-… claude auth status --json | jq -c '…'
{"authMethod":"claude.ai","apiProvider":"firstParty","subscriptionType":null}
```

Reproduced 3/3. `ANTHROPIC_AUTH_TOKEN` relabels to `oauth_token`, and an
empty-string key is correctly ignored. `ANTHROPIC_API_KEY` is the one credential
that displaces silently.

**The behavior is documented as intended.** Support guidance is to keep
`ANTHROPIC_API_KEY` unset. The argument is that a default is wrong, not that a
bug exists.

## Evidence

26 public issues on silent billing misattribution, September 2025 to August 2026,
20 still open. Filing rate: one or two a month through spring, then 5, 8, and 6
across June, July, and August.

| Issue | Filed | Self-reported | Mechanism |
|---|---|---|---|
| [#86723](https://github.com/anthropics/claude-code/issues/86723) | 2026-08 | $1,122.83 | env var in Routines cloud environment |
| [#62338](https://github.com/anthropics/claude-code/issues/62338) | 2026-05 | $447.00 | billed to API instead of Max |
| [#39903](https://github.com/anthropics/claude-code/issues/39903) | 2026-03 | $152.00 | subagent dispatch used the API key |
| [#78491](https://github.com/anthropics/claude-code/issues/78491) | 2026-07 | $78.00 | shell profile export, 17 days unnoticed |
| | | **$1,799.83** | four issues; twenty-two carry no figure |

The loss these four figures describe is trust in a plan already paid for, not
the refund. Each of the four filers had an active subscription that the session
did not use.

[#78491](https://github.com/anthropics/claude-code/issues/78491) independently asks
for this exact fix: *"request louder consent + persistent indicator."*

Prior art: `/cost`, `/usage`, `/stats`, and `/status` all ship. They are **pull,
not push**, reachable only by a user who has already become suspicious. Two
issues show the gap they leave even when pulled:
[#74217](https://github.com/anthropics/claude-code/issues/74217) reports `/status`
showing one account while billing another, and
[#84015](https://github.com/anthropics/claude-code/issues/84015) reports a Max
session mislabeled as "Claude API account."

## Proposed fix

Full design: **[proposal-credential-precedence.md](proposal-credential-precedence.md)**

Add a `CLAUDE_CODE_API_KEY` variable that states billing intent explicitly, and
move `ANTHROPIC_API_KEY` below subscription credentials in the precedence order.

| Level | Current | Proposed |
|---|---|---|
| 3 | `ANTHROPIC_API_KEY` | **`CLAUDE_CODE_API_KEY`** |
| 7 | Subscription (`/login`) | Subscription (`/login`) |
| 8 | — | **`ANTHROPIC_API_KEY`** |

Adding the variable alone fixes nothing. The unintended charges happen through
`ANTHROPIC_API_KEY`, so the demotion is the change that matters. The new variable
is what makes the demotion safe.

Two facts make this a smaller ask than it looks:

- **Claude Code on the Web already behaves this way.** Per the docs, environment
  API keys in the web sandbox "don't override your subscription credentials." The
  proposal makes the CLI consistent with a decision already shipped elsewhere.
- **The `CLAUDE_CODE_*` namespace is established**, and `CLAUDE_CODE_OAUTH_TOKEN`
  is the exact parallel: the namespaced way to supply a *subscription* credential
  where browser login is not available. No equivalent exists for an API credential.

The change ships in three releases: announce the variable, warn when the key
displaces a subscription, then switch the order. The warning release also adds a
rebill key. When the warning fires in an interactive session, one keystroke bills
the rest of that session to the subscription and prints the permanent fix.

Nearly nothing breaks. CI and container environments usually have no subscription
on the machine, so the key falls through to level 8 and keeps working. The only
population whose behavior changes without action is machines with both a
subscription and an ambient `ANTHROPIC_API_KEY`, which is the population
reporting the charges.

## Prototype

`prototype/statusline-billing.sh` is the stage 2 warning from the proposal, built
and running. It detects displacement rather than reading the reported auth
method, which is necessary because `authMethod` returns the same value in both
states. It probes twice and compares:

```bash
resolved=$(claude auth status --json)
latent=$(env -u ANTHROPIC_API_KEY -u ANTHROPIC_AUTH_TOKEN claude auth status --json)
[ -z "$resolved_sub" ] && [ -n "$latent_sub" ] && state=CONFLICT
```

Three states, and the third matters as much as the others. An API key with no
subscription behind it is correct billing, and draws no warning:

```
◆ PRO SUB · Opus                       subscription pays
████░░░░░░ 41% · 5h 62% · caps in ~23min

▲ API KEY ····4f2a · Opus              displaced an entitlement
ANTHROPIC_API_KEY displaced your pro subscription
  ↳ press ⌥B to bill the subscription instead

◇ API KEY ····test · Opus              correct, and silent
████░░░░░░ 41% · $2.14
```

The continuity projection (`caps in ~23min`) is computed from `rate_limits.five_hour`
in the status-line payload, not mocked.

### Run it

```bash
# against the captured session fixture
./prototype/statusline-billing.sh < prototype/mock-session.json

# force the displaced state
ANTHROPIC_API_KEY=sk-ant-test0000000000000000000000004f2a \
  ./prototype/statusline-billing.sh < prototype/mock-session.json
```

The capture's five-hour window has since reset, so the continuity projection
reads `finishes` on a raw replay. Re-clock the window to see the projection that
produced the output above:

```bash
jq '.rate_limits.five_hour.resets_at = (now + 2100 | floor)' \
  prototype/mock-session.json | ./prototype/statusline-billing.sh
```

Install it as the status line command in your Claude Code settings. The auth
probe costs ~210 ms, cached 30 s, keyed on a fingerprint of the credential env
vars so a change invalidates immediately. Render: 68 ms.

## Mock

`page/who-is-paying.html`: drive the precedence order at
<https://madpr.github.io/claude-growth-surfaces/who-is-paying.html>

A terminal you type into. Export the key most machines already carry, start a
session, and watch which credential pays. Two controls change the answer: the
machine (a laptop with a subscription, or a build box without one) and the
precedence order (the one that ships, or the one proposed here). Changing either
control ends a running session and keeps your environment, so the next `claude`
shows the new setting's effect.

The custom API key dialog, the fields `claude auth status --json` reports, and
the `/cost` layout are replicated from Claude Code v2.1.260. Everything the
proposal adds (the status line's billing badge, the displacement note, and the
rebill key) is marked in the transcript. Figures come from the fixture through
the arithmetic in the status line script, so the page and the code cannot
disagree.
