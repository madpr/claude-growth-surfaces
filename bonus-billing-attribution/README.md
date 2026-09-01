# Billing attribution & spend confidence

**Thesis.** Unpriced uncertainty suppresses usage. What is unpriced is not dollars
but *whether the run will be allowed to finish* — in three currencies: API spend,
subscription rate-limit windows, and org budget someone else owns.

## Why this is a bonus and not one of the three

Two reasons, both worth stating plainly.

1. **It is scoped to the wrong product.** The brief's north star is Claude API
   revenue on `platform.claude.com`. The defect documented here lives in Claude
   Code's credential precedence.
2. **Its direct effect is revenue-negative for that north star.** It tells users
   "you are paying API rates when your subscription already covers this."
   The defensible case is trust and churn prevention — surprise bills produce
   disputes, defensive spend caps and cancellations — but that is second-order,
   and a growth pitch that opens by helping users pay less deserves the pushback
   it will get.

There is an API-layer version that survives both objections: per-team spend
attribution, budgets that pause rather than terminate, forecasting. Budget
confidence unblocks org deployment, which is straightforwardly revenue-positive.
If that turns out to be the right big bet, the evidence below is its foundation.

Kept here because it is the only item in this repo that has been verified: a
defect reproduced on the current build, a corpus of real user reports, and a
prototype that runs. That is the bar the three ideas should meet.

## Findings

Verified on Claude Code v2.1.252, 31 August 2026.

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

Reproduced 3/3. `ANTHROPIC_AUTH_TOKEN` relabels to `oauth_token`; an empty-string
key is correctly ignored. `ANTHROPIC_API_KEY` is the one credential that displaces
silently.

**The behavior is documented as intended** — support guidance is "keep
`ANTHROPIC_API_KEY` unset." So the argument is that a default is wrong, not that
a bug exists.

## Evidence

26 public issues on silent billing misattribution, Sep 2025 – Aug 2026, 20 still
open. Filing rate: 1–2/month through spring, then 5, 8, 6 across June–August.

| Issue | Filed | Self-reported | Mechanism |
|---|---|---|---|
| [#86723](https://github.com/anthropics/claude-code/issues/86723) | 2026-08 | $1,122.83 | env var in Routines cloud environment |
| [#62338](https://github.com/anthropics/claude-code/issues/62338) | 2026-05 | $447.00 | billed to API instead of Max |
| [#39903](https://github.com/anthropics/claude-code/issues/39903) | 2026-03 | $152.00 | subagent dispatch used the API key |
| [#78491](https://github.com/anthropics/claude-code/issues/78491) | 2026-07 | $78.00 | `~/.zshrc` export, 17 days unnoticed |
| | | **$1,799.83** | four issues; twenty-two carry no figure |

[#78491](https://github.com/anthropics/claude-code/issues/78491) independently asks
for this exact fix: *"request louder consent + persistent indicator."*

Prior art to acknowledge, not ignore: `/cost`, `/usage`, `/stats` and `/status`
all ship. The argument is that they are **pull, not push** — reachable only by a
user who has already become suspicious. And they are not reliable:
[#74217](https://github.com/anthropics/claude-code/issues/74217) reports `/status`
showing one account while billing another;
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

Adding the variable alone fixes nothing — the unintended charges happen through
`ANTHROPIC_API_KEY`, so the demotion is the change that matters. The new variable
is what makes the demotion safe.

Two facts make this a smaller ask than it looks:

- **Claude Code on the Web already behaves this way.** Per the docs, environment
  API keys in the web sandbox "don't override your subscription credentials." The
  proposal makes the CLI consistent with a decision already shipped elsewhere.
- **The `CLAUDE_CODE_*` namespace is established**, and `CLAUDE_CODE_OAUTH_TOKEN`
  is the exact parallel: the namespaced way to supply a *subscription* credential
  where browser login isn't available. No equivalent exists for an API credential.

Nearly nothing breaks. CI and container environments usually have no subscription
on the machine, so the key falls through to level 8 and keeps working. The only
population whose behavior changes without action is machines with both a
subscription and an ambient `ANTHROPIC_API_KEY` — the population reporting the
charges.

## Prototype

`prototype/statusline-billing.sh` — the stage 2 migration signal from the
proposal, built and running. It detects *displacement* rather than reading the reported auth
method, which is necessary because `authMethod` returns the same value in both
states. It probes twice and compares:

```bash
resolved=$(claude auth status --json)
latent=$(env -u ANTHROPIC_API_KEY -u ANTHROPIC_AUTH_TOKEN claude auth status --json)
[ -z "$resolved_sub" ] && [ -n "$latent_sub" ] && state=CONFLICT
```

Three states, and the third matters as much as the others — an API key with no
subscription behind it is correct billing, and draws no warning:

```
◆ PRO SUB · Opus                       subscription pays
████░░░░░░ 41% · 5h 62% · caps in ~23min

▲ API KEY ····4f2a · Opus              displaced an entitlement
ANTHROPIC_API_KEY displaced your pro subscription

◇ API KEY ····test · Opus              correct, and silent
████░░░░░░ 41% · $2.14
```

The continuity projection (`caps in ~23min`) is computed from `rate_limits.five_hour`
in the status-line payload, not mocked — both currencies of the thesis are already
on the wire.

### Run it

```bash
# against the captured session fixture
./prototype/statusline-billing.sh < prototype/mock-session.json

# force the displaced state
ANTHROPIC_API_KEY=sk-ant-test0000000000000000000000004f2a \
  ./prototype/statusline-billing.sh < prototype/mock-session.json
```

Install by pointing `statusLine.command` in `~/.claude/settings.json` at it.
Auth probe costs ~210 ms, cached 30 s, keyed on a fingerprint of the credential
env vars so a change invalidates immediately. Render: 68 ms.

## Falsification

- If the share of subscription-entitled sessions running on API credentials is
  under ~1%, this is a support problem, not a growth surface. One query decides
  it; it cannot be run from outside.
- If Max session lengths match API session lengths after normalizing for task
  type, cost uncertainty is not the usage constraint and the thesis fails.
- If declined tool calls do not fall once headroom is visible, the hesitation was
  about blast radius rather than exhaustion — a different, larger problem.

## Published case

The written case, with the reproducible defect, the evidence corpus and the
prototype output rendered as a page:

<https://claude.ai/code/artifact/0502f696-82e4-45c8-9a93-38b70868752a>

`page/billing-attribution.html` is its source.
