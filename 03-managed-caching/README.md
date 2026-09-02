# Managed prompt caching

Prompt caching bills a premium up front and refunds it only when the cache is read
back. When the cache never reads, you pay 1.25 to 2 times what the same traffic costs
with caching switched off. The platform can already detect this and can already
diagnose it, but it does neither unless you ask.

This proposes two things: a free card that tells you when you're paying the surcharge,
and a paid service that places and maintains your cache breakpoints so you stop.

| Component | Effort | Revenue |
|---|---|---|
| Surcharge card (free, always on) | 2 to 3 days | Indirect. It's the acquisition wedge |
| Managed caching (paid) | Larger. Not sized here | Direct |

The card qualifies the accounts the paid service is for. Ship it first, and let the
population it surfaces tell you whether the service is worth building.

[Open the prototype](https://claude.ai/code/artifact/2b514045-cf23-496e-a97f-0fd5ffbd13bc) — the Console surface, on Analytics › Caching, which is a
nav entry that already exists.

## How prompt caching is priced

From the prompt caching documentation:

> * 5-minute cache write tokens are **1.25 times** the base input tokens price
> * 1-hour cache write tokens are **2 times** the base input tokens price
> * Cache read tokens are **0.1 times** the base input token price

Cache reads on Claude Fable 5.1 and Claude Mythos 5.1 are 0.025 times base input
instead.

You buy caching up front and collect on it later. If you never collect, you're worse
off than if you'd never bought it. That inversion is the defect. A missed discount is
an optimization you skipped; a premium charged for nothing is a billing problem.

It also creates an incentive nobody designed. As priced today, a workload whose cache
fails bills more than the same workload whose cache works. Nothing in the product
corrects for that, and no signal reaches the customer.

## What already ships

Three of the four pieces exist. They aren't connected to each other, and each one is
inert alone.

| Piece | Status | Why it isn't enough |
|---|---|---|
| Automatic breakpoint placement | Ships. A top-level `cache_control` field places one breakpoint on the last cacheable block and moves it forward as the conversation grows | It places **exactly one** breakpoint out of four available slots, so prompts with several stability boundaries need manual markers. The docs also record its own failure mode: when a prompt ends in per-request content, the automatic breakpoint lands after it and "every request pays the write premium on bytes that are never read back — a pure surcharge" |
| Detection data | Ships. The Usage Report API returns `cache_creation.ephemeral_5m_input_tokens`, `cache_creation.ephemeral_1h_input_tokens`, `cache_read_input_tokens`, and `uncached_input_tokens`, grouped by `api_key_id`, `workspace_id`, and `model`, in buckets as fine as `1m` | No Console surface reads these fields. To find the problem you have to already suspect it, find the Admin API, and write a query |
| Diagnosis | Ships. Cache diagnostics (beta header `cache-diagnosis-2026-04-07`) compares consecutive requests and returns a typed `cache_miss_reason`: `model_changed`, `system_changed`, `tools_changed`, or `messages_changed` | Opt-in, and the header must be on **every** request. Retrofitting fails with `previous_message_not_found`, so you can't turn it on after you notice. You have to turn it on before there's anything to notice |
| Measurement and correction | Missing | Nothing checks whether your caching works, and nothing adjusts when it stops |

No response header carries cache state either. The documented response headers are
`request-id`, `anthropic-organization-id`, `anthropic-workspace-id`, and the rate-limit
family. That's the same asymmetry [`01-dev-to-production`](../01-dev-to-production/)
records for spend: twelve or more rate-limit headers, none for budget.

## Evidence

The corpus holds 16 public reports, in [`research/issues.tsv`](research/issues.tsv).
Each one was opened and read rather than matched on title. They divide into four
groups, and the division is the finding.

| Group | Count | What happened |
|---|---|---|
| The prefix broke | 6 | Caching was configured correctly and stopped working |
| Caching never engaged | 3 | `cache_control` was never sent. A hard-coded model allowlist, a policy that does nothing on one provider, a harness that didn't implement it |
| Accounting was wrong | 4 | Cache tokens were dropped or double-counted downstream, so the bill couldn't be reconciled |
| Not the Claude API | 3 | Compatibility endpoints and routers that accept `cache_control` and ignore it |

Nine of the 16 are breakpoint management failures. That's the population the paid
service is for.

The clearest reports, with figures as their authors gave them:

| Report | Measured |
|---|---|
| [openclaw#19534](https://github.com/openclaw/openclaw/issues/19534) | 170,602 tokens rewritten on every request with cache reads at 0. "$35 today instead of expected $9." A timestamp in the system prompt |
| [signalbox#611](https://github.com/KeenWill/signalbox/issues/611) | 98 calls, about 7.1M input tokens, 0 cache-read tokens. One session re-sent the same prefix 45 times. "~$22; with standard prompt caching… a few dollars" |
| [bifrost#6591](https://github.com/maximhq/bifrost/issues/6591) | Non-deterministic tool serialization gave 1 cache hit in 5 through the proxy against 5 in 5 direct. The third regression of the same bug, after #1742, #2347, and #3362 |
| [pi-mono#520](https://github.com/lue-labs/pi-mono/issues/520) | 177k of 279k session write tokens traced to three miss events, including a full miss 7 seconds after a 96.3% hit |
| [theia#17986](https://github.com/eclipse-theia/theia/issues/17986) | Editor state resolved into the system prompt, billing "at cache-write rates (1.25×) instead of cache-read rates (0.1×)" |

bifrost#6591 is the strongest single argument for measurement. A team that knows about
this bug and has fixed it three times can't keep it fixed, because nothing tells them
when it returns.

Two limits on this evidence. Most of these authors run agent harnesses, IDE
extensions, and proxies rather than direct API integrations, which gives them the same
standing the Claude Code issues have in `01`: directionally relevant, not proof. And
the figures are rates and ratios at different scales, so unlike
[`bonus-billing-attribution`](../bonus-billing-attribution/) they aren't summed into a
headline number. A total would be arithmetic on incompatible units.

## Free tier: the surcharge card

One card on the Console usage view, always on, for every account.

1. Detect keys with sustained cache writes and almost no reads.
2. Price the surcharge in dollars: what you paid, against what the same traffic costs
   with caching off.
3. Offer two exits. Fix it yourself with a prefilled cache diagnostics snippet, or
   turn on managed caching.

Two to three days of work, because steps 1 and 3 are a query and a link. The estimate
covers the card only.

This part stays free. Charging an account to discover that it's being surcharged for a
mechanism that silently failed would be indefensible, and a panel would say so.

### Trigger rules

Evaluate daily, on `1h` buckets, across a trailing 7 days. Flag a key when all four
hold:

- Three or more consecutive buckets where cache writes exceed the model's minimum
  cacheable prefix, which runs from 512 to 4,096 tokens depending on model.
- Cache reads under 2% of writes across that run.
- A surcharge above a materiality floor. Around $5 over the window keeps the card off
  accounts where it's noise.
- No documented reason for the miss. A prefix under the minimum cacheable length is
  expected behavior and never a defect.

An hour is fine enough that a bursty workload doesn't average out to healthy, and
coarse enough that a low-volume key doesn't trip on three minutes of traffic. Three
consecutive hours of writing without reading is unambiguous: the first write in any
conversation has nothing to read, so three hours of them means every conversation is a
first.

Evaluate daily rather than in real time. The fix is a code change and a redeploy, so a
faster alert repeats itself while someone schedules the work.

### Placement

Placement is the weakest part of this design, and it's worth saying so directly.

| Surface | Role |
|---|---|
| Usage page | The detail view: which key, which model, the priced surcharge, the exits |
| Console home | A dismissible banner at next sign-in, for members who can see billing |
| Spend-threshold email | The surface that actually reaches someone who isn't looking |

The Usage page is the natural home for the detail, but a page you visit deliberately
only helps people who already suspect something. That's the same failure that makes
cache diagnostics inert. The email is the surface that solves it, and `01` records
that threshold alerts are automatic for Enterprise and opt-in for Console. So the
customers least likely to be watching their cache are also least likely to have
enabled the channel that would tell them. Changing that is more than 2 to 3 days, and
folding it in silently would break the estimate.

## Premium tier: managed caching

You stop placing breakpoints. The platform observes which parts of your prompt are
actually stable across your own traffic, places up to four breakpoints at the real
stability boundaries, and moves them when your traffic changes.

What makes this a product rather than a feature request:

- **Automatic placement puts one breakpoint where the conversation grows.** Managed
  placement uses all four slots, at boundaries measured from your requests: tools that
  never change, context that changes daily, conversation that changes per turn.
- **It closes the loop.** Placement is checked against realized hit rates and adjusts.
  Nothing in the product does this today, which is why bifrost fixed the same bug
  three times.
- **It fixes the incentive.** Priced as a share of realized savings, Anthropic earns
  when your cache works. Today the platform earns more when it fails.

### Pricing

Two models, and the choice is a real one.

**Bundle it into the Scale tier.** Simplest to build, uses billing that exists, and
converts self-serve accounts to contracted ones, which is the growth motion. `01`
records the tier structure: Start at $500 monthly, Build at $1,000, Scale at $200,000.
Recommended, because it ships.

**Charge a share of realized savings.** Bill a percentage of the measured difference
between what the workload cost and what it would have cost uncached. Harder to
meter and to explain on an invoice, but it's the only version where the vendor's
incentive and the customer's point the same way. Worth costing before defaulting to
the tier bundle.

## Success metrics

Track the free card first. It sizes the paid product, and if the population is small
the paid product shouldn't be built.

| Metric | What it tells you | Target |
|---|---|---|
| High-volume keys in the surcharge state | The size of the problem, and whether any of this was worth building | Primary |
| Keys that leave the state within 30 days of first seeing the card | Whether telling people is enough on its own | Above 50% |
| Conversion from card to managed caching | Whether the paid product answers the problem the card surfaces | Primary, paid |
| Realized hit rate under managed caching, against the account's own baseline | Whether the service delivers | Above 80% |
| Diagnostics opt-in rate from the self-serve exit | Whether the free path is sufficient for most accounts | Above 25% |
| Keys that recover and then regress | Whether this needs to be a standing check rather than a one-time card | Watch |

Two guardrails decide whether the card stays switched on:

| Guardrail | Why it matters | Limit |
|---|---|---|
| False positive rate | A workload with no stable prefix is correctly not caching. Flagging it trains people to dismiss a billing warning | Under 5% |
| Prefixes below the minimum cacheable length | Documented behavior, never a defect, and never a valid flag | 0 |

Measure the first metric before building anything. It's one query against data
Anthropic already holds.

## Risks

| Risk | What kills the idea |
|---|---|
| The population is small | Few keys are in this state, and the corpus is loud rather than large. Check first |
| Managed caching can't beat manual | If measured placement doesn't outperform a competent engineer with four markers, there's nothing to sell |
| Charging for caching reads badly | "Pay us to stop overcharging you" is the obvious attack. The free card is the answer, and it has to stay free and stay first |
| Telling people isn't enough | Teams see the card, understand it, and still don't act, because the cause sits in a vendored dependency. That's true for a third of the corpus |
| It's a documentation problem | If most causes are the same three mistakes, a better troubleshooting page costs a day and no engineering |
| The self-serve exit cannibalizes the paid one | If the diagnostics snippet fixes most accounts for free, managed caching has a small market. That's a good outcome for customers and a bad one for this pitch |

## Run the prototype

```
cd prototype
python3 cache_lint.py detect  fixtures/usage-report.json
python3 cache_lint.py explain fixtures/payload-log.json
python3 test_cache_lint.py
```

| Path | Contents |
|---|---|
| `prototype/cache_lint.py` | Both halves. `detect` reads a usage report and prices the surcharge. `explain` reads a payload log and locates the invalidator |
| `prototype/test_cache_lint.py` | 44 invariants |
| `prototype/fixtures/` | A usage report with one surcharged key, one healthy key, one below the cacheable floor, and one that never caches. A six-request payload log seeding one failure of each class |
| `page/managed-caching.html` | The Console mockup. Four tabs, every figure read out of the linter's output |
| `research/issues.tsv` | The corpus. 16 rows, each one read |
| `research/deep-research-triage.md` | The nine ideas this came from, and what happened to the other eight |

`explain` classifies into the same discriminated union the API returns, so the local
answer and the server answer use one vocabulary. When a local diff can't see the
cause, it reports `unavailable` rather than guessing. That covers a prompt-affecting
parameter outside the prefix, and a turn that appends past the 20-position lookback
window, where the payloads are byte-identical and the cache still misses. Promising a
diagnosis the data can't support would reproduce the defect this idea is about.

The moving `cache_control` breakpoint is stripped before diffing. It differs between
every adjacent pair and isn't an invalidator, so a diff that leaves it in reports the
marker every time and buries the real cause.

The trigger rules above are enforced in `detect`, including the materiality floor.
The floor applies only where the model is priceable: an unrecognized model prices at
zero, and suppressing it would hide a large finding behind a missing price rather than
behind a small surcharge.

## Sources

Documentation quotations come from `platform.claude.com`, fetched 2 September 2026,
and are linked from each claim. Issue numbers are real, and each was opened and read.

The prototype runs on seeded fixtures. It reads no account and makes no API calls.

One question decides whether any of this is worth building, and it's inside Anthropic:
**how many API organizations are in the surcharge state, and what do they spend?** One
query against the Usage Report API answers it.
