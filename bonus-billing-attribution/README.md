# Billing attribution

I set an API key in my shell for an unrelated project and Claude Code quietly
started billing my Console account instead of the subscription I pay for. The
diagnostic said nothing had changed.

I was not the first. There are 26 public issues describing the same
misattribution, and the four that put a dollar figure on it add up to
$1,799.83.

**Status:** Defect reproduced, proposal written, drivable mock ·
**Cost:** three releases (announce, warn, switch) · **Theme:** retention

## Why this is outside the slate

It is scoped to Claude Code rather than the platform, and its direct effect
moves spend from metered billing to a subscription the customer has already
paid for. Under the decision rule the top README states (work stays on the
subscription while it is one person's, and moves to the platform when it bills
an organization rather than a person), this item is the guarantee that one
person's interactive session is never billed to an organization without saying
so. The API-layer version of the same work, per-team spend attribution and
budgets that pause instead of terminating, belongs on the platform and I left
it out.

## Findings

I first saw this on Claude Code v2.1.252 on 31 August 2026 and reproduced it
on v2.1.260 on 3 September 2026.

The diagnostic gives the same answer in both states. I ran
`claude auth status --json` with my Pro subscription signed in, then ran it
again with `ANTHROPIC_API_KEY` exported. `authMethod` said `"claude.ai"` both
times, `apiProvider` said `"firstParty"` both times, and the only field that
moved was `subscriptionType`, which went from `"pro"` to null.

```
$ claude auth status --json | jq -c '{authMethod,apiProvider,subscriptionType}'
{"authMethod":"claude.ai","apiProvider":"firstParty","subscriptionType":"pro"}

$ ANTHROPIC_API_KEY=sk-ant-… claude auth status --json | jq -c '…'
{"authMethod":"claude.ai","apiProvider":"firstParty","subscriptionType":null}
```

Reproduced 3/3. I tried the neighboring variables too. `ANTHROPIC_AUTH_TOKEN`
at least relabels itself to `oauth_token`, and an empty-string key is ignored,
which is right. `ANTHROPIC_API_KEY` is the one credential that displaces the
subscription and says nothing.

This is documented behavior, and the support guidance is to keep
`ANTHROPIC_API_KEY` unset. What I'm arguing is that the default is wrong.

## Evidence

There are 26 public issues on silent billing misattribution, September 2025
to August 2026, 20 still open. I read every one of them. The filing rate was
one or two a month through spring, then 5, 8, and 6 across June, July, and
August.

| Issue | Filed | Self-reported | Mechanism |
|---|---|---|---|
| [#86723](https://github.com/anthropics/claude-code/issues/86723) | 2026-08 | $1,122.83 | env var in Routines cloud environment |
| [#62338](https://github.com/anthropics/claude-code/issues/62338) | 2026-05 | $447.00 | billed to API instead of Max |
| [#39903](https://github.com/anthropics/claude-code/issues/39903) | 2026-03 | $152.00 | subagent dispatch used the API key |
| [#78491](https://github.com/anthropics/claude-code/issues/78491) | 2026-07 | $78.00 | shell profile export, 17 days unnoticed |
| | | **$1,799.83** | four issues; twenty-two carry no figure |

Each of the four filers with a figure had an active subscription that the
session never used, and reading their threads, the refund is the smaller part
of what they lost. They had paid for a plan and stopped believing it was the
thing being used.

[#78491](https://github.com/anthropics/claude-code/issues/78491) asks for this
exact fix in its title: *"request louder consent + persistent indicator."*

Prior art exists. `/cost`, `/usage`, `/stats`, and `/status` all ship, but you
have to go and run them, which means you have to be suspicious already. Even
then they can be wrong.
[#74217](https://github.com/anthropics/claude-code/issues/74217) reports `/status`
showing one account while billing another, and
[#84015](https://github.com/anthropics/claude-code/issues/84015) reports a Max
session mislabeled as "Claude API account."

## Proposed fix

Full design: **[proposal-credential-precedence.md](proposal-credential-precedence.md)**

Add a `CLAUDE_CODE_API_KEY` variable that says what you mean about billing, and
move `ANTHROPIC_API_KEY` below subscription credentials in the precedence order.

| Level | Current | Proposed |
|---|---|---|
| 3 | `ANTHROPIC_API_KEY` | **`CLAUDE_CODE_API_KEY`** |
| 7 | Subscription (`/login`) | Subscription (`/login`) |
| 8 | — | **`ANTHROPIC_API_KEY`** |

Adding the variable on its own fixes nothing, because the unintended charges
come through `ANTHROPIC_API_KEY`. The demotion is the change that matters, and
the new variable is what makes it safe to do.

This is a smaller ask than it looks. Claude Code on the Web already behaves
this way; per the docs, environment API keys in the web sandbox
"don't override your subscription credentials," so the proposal brings the CLI
in line with a decision that already shipped. The name is familiar too. Claude
Code keeps its own configuration under `CLAUDE_CODE_*`, and
`CLAUDE_CODE_OAUTH_TOKEN` is the exact parallel, the namespaced way to hand the
tool a *subscription* credential where browser login is not available. There
has never been an equivalent for an API credential.

It ships in three releases. The first announces the variable, the second warns
when the key displaces a subscription, and the third switches the order. The
warning release also adds a rebill key, so when the warning fires in an
interactive session, one keystroke bills the rest of that session to the
subscription and prints the permanent fix.

Nearly nothing breaks. CI and container environments usually have no
subscription on the machine, so the key falls through to level 8 and keeps
working. The only people whose behavior changes without them doing anything are
the ones with both a subscription and an ambient `ANTHROPIC_API_KEY` on the
same machine, and those are the people filing the issues.

## Prototype

`prototype/statusline-billing.sh` is the stage 2 warning from the proposal,
built and running. Since `authMethod` is the same in both states, checking that
field tells you nothing, so the script probes `claude auth status` twice, once
as the environment stands and once with the credential variables stripped, and
compares:

```bash
resolved=$(claude auth status --json)
latent=$(env -u ANTHROPIC_API_KEY -u ANTHROPIC_AUTH_TOKEN claude auth status --json)
[ -z "$resolved_sub" ] && [ -n "$latent_sub" ] && state=CONFLICT
```

Three states, and the third matters as much as the others. An API key with no
subscription behind it is correct billing and gets no warning:

```
◆ PRO SUB · Opus                       subscription pays
████░░░░░░ 41% · 5h 62% · caps in ~23min

▲ API KEY ····4f2a · Opus              displaced an entitlement
ANTHROPIC_API_KEY displaced your pro subscription
  ↳ press ⌥B to bill the subscription instead

◇ API KEY ····test · Opus              correct, and silent
████░░░░░░ 41% · $2.14
```

The continuity projection (`caps in ~23min`) is real arithmetic on
`rate_limits.five_hour` from the status-line payload.

### Run it

```bash
# against the captured session fixture
./prototype/statusline-billing.sh < prototype/mock-session.json

# force the displaced state
ANTHROPIC_API_KEY=sk-ant-test0000000000000000000000004f2a \
  ./prototype/statusline-billing.sh < prototype/mock-session.json
```

The capture's five-hour window has since reset, so a raw replay prints
`finishes`. Re-clock the window to get the projection shown above:

```bash
jq '.rate_limits.five_hour.resets_at = (now + 2100 | floor)' \
  prototype/mock-session.json | ./prototype/statusline-billing.sh
```

To use it for real, set it as the status line command in your Claude Code
settings. The auth probe costs ~210 ms and is cached for 30 s, keyed on a
fingerprint of the credential env vars so changing one invalidates it
immediately. Render is 68 ms.

## Mock

`page/who-is-paying.html`: drive the precedence order at
<https://madpr.github.io/claude-growth-surfaces/who-is-paying.html>

It's a terminal you type into. Export the key most machines already have,
start a session, and watch which credential pays. You can change the machine
(a laptop with a subscription, or a build box without one) and the precedence
order (the one that ships today, or the one proposed here). Either change ends
the running session and keeps your environment, so the next `claude` shows what
the new setting does.

The custom API key dialog, the fields `claude auth status --json` reports, and
the `/cost` layout are copied from Claude Code v2.1.260. Everything the proposal
adds (the billing badge in the status line, the displacement note, and the
rebill key) is marked in the transcript. The figures come from the fixture
through the same arithmetic as the status line script, so the page and the code
can't disagree.
