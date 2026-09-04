# Developer platform entry point

claude.ai already links to the Claude Platform twice, and both links behave the same
way: they sit behind a menu that only a visitor who already wants them will open, and
they land on the API keys page, which issues a credential rather than showing the
product. Neither link appears on the left rail, the one surface a subscriber sees every
session. This proposes a sixth rail row, after **Customize**, pointing at the platform
dashboard and shown to subscribers who declare engineering work. Both existing links already have
tracking tags on them, so these clicks are counted today and a placement test starts
with a number to beat rather than with no measurement at all.

**Status:** designed, working prototype · **Engineering cost:** ≤ 2–3 days ·
**Theme:** activation · **Revenue path:** direct

## Problem

Anthropic sells two products to overlapping people, and the paid subscriber who could
also be a platform customer has to go looking.

- **Both entry points require intent.** One sits in the account menu, below Claude
  Academy. The other sits in a settings section titled **Platform** that holds exactly
  one row. A subscriber who has not already decided to build never passes either.
- **Both land on a credential.** The API keys page hands over a secret and assumes the
  visitor knows what to do with it. The dashboard, on the same account, shows credits,
  spend against the monthly limit, prompt-caching hit rate, token volume, the model
  lineup, Managed Agents, and Claude Code usage.
- **The one high-intent moment is already answered, in the other direction.** The usage
  page mentions the API but never names the Claude Platform. What it offers at the plan
  limit is usage credits, which keep metered spend on the subscription.
- **The left rail says nothing.** New, Projects, Artifacts, Scheduled, and Customize.
  The header holds a single control, which makes it an action strip rather than a list
  of destinations.

## Goals

- Establish whether placement, rather than messaging, is what gates subscriber
  activation on the platform.
- Land arrivals on a page that shows the product, and reserve the credential for people
  who ask for one.
- Target on a signal claude.ai already collects, so the test ships in days.

## Non-goals

- Building new signal collection or a propensity model.
- Changing the plan-limit experience, which already has an answer.
- Changing pricing, packaging, or the platform dashboard itself.
- Removing the existing entry points. They stay, as the control.

## Proposed experience

- A sixth row in the left rail, directly after **Customize**, separated from the rows
  above it.
- The label names the destination rather than the credential.
- The row navigates in place, as every row above it does. Both existing entry points
  open a new tab, which is part of what makes them read as exits rather than as part
  of the product.
- The row carries the same tracking tags the two existing links already use, so the
  three placements are comparable.
- Shown only to subscribers whose profile declares engineering work. Everyone else sees
  today's rail.

## Success metrics

| | Measure |
|---|---|
| **Primary** | Click-through on the rail row, against the instrumented account-menu and settings links |
| **Secondary** | Organizations created, first successful API call within 7 days, still calling at day 30 |
| **Guardrail** | No fall in subscription retention, and no fall in claude.ai session volume |

The secondary chain is what separates a curiosity click from activation. A rail row that
wins clicks and produces no first call has found a worse answer than the buried menu.

## First cheap milestone

Run the placement test on the rail row alone, against today's experience.

At a 0.50% baseline and a 25% relative lift, at 5% significance and 80% power, the test
needs **56,193 impressions per arm**, or 112,386 in total. Time to a decision depends on
how many eligible sessions per day exist, which is not knowable from outside Anthropic,
so the prototype sweeps it:

| Eligible sessions/day | Time to decision |
|---|---|
| 5,000 | 22.5 days |
| 25,000 | 4.5 days |
| 100,000 | 1.1 days |
| 500,000 | 5.4 hours |

The 25% design point is deliberately conservative for a move from a buried menu to a
persistent rail. If the effect is a doubling, the same test needs 4,673 impressions per
arm and settles in hours at any of these traffic levels.

Once the row ships to everyone eligible, impressions recur every session. At 25,000
eligible sessions per day and $100 per month of spend per converted caller, the
prototype puts the incremental run rate at **$646,734 a year**; at 100,000 sessions per
day, **$2,586,937**. Both axes are swept because both are unknown from outside.

## Risks

- **Cannibalization.** A heavy subscriber who moves work onto metered billing may spend
  less in total than the flat fee they were paying. The bonus item in this repo argues
  the reverse trade deliberately, which means the two are in tension and the guardrail
  metric above is the thing that settles it.
- **The direction is contested inside the product.** Cowork keeps unattended work on the
  subscription, and usage credits keep limit-exhaustion spend there too. Two shipped
  surfaces choose the subscription over the platform for an existing audience. If that
  is deliberate policy rather than sequencing, this row argues against it and the case
  is a policy argument, not a growth test.
- **Rail real estate is the scarcest surface in the product.** A sixth row costs
  attention on every session for every targeted user. Targeting on the declared
  engineering signal is what keeps that cost proportionate, and a targeting signal that
  turns out to be rare or badly correlated makes the row noise.

## Open questions

- **What a subscriber with no organization sees at the dashboard.** If it is empty, the
  keys page may be the better landing after all, and the retarget is wrong. An outsider
  settles this with a second account.
- **Whether arriving from claude.ai provisions a second organization.** The account
  observed here already has one, so it cannot show the cold path. This repo separately
  records that the two surfaces resolve to different organizations on one account, which
  would mean the rail row promises continuity it does not deliver.
- **Current click-through on the two instrumented links.** Needs someone inside. It sets
  the baseline the sizing above assumes.
- **The share of subscribers who declare engineering work.** Needs someone inside. It
  sets eligible traffic, the single largest unknown in the sizing.
- **Whether keeping work on the subscription is deliberate.** Needs someone inside. It
  decides whether this is a test or a disagreement.

## Evidence

- [`research/entry-points.md`](research/entry-points.md) — the two entry points, their
  targets, the rail inventory, and the usage-page finding, observed on the live product
  on 3 September 2026.
- [`research/entry-point-audit.js`](research/entry-point-audit.js) — reproduces the
  entry-point table in a browser console. Prints link paths and the names of the tracking
  tags, never their values, so the finding reproduces without publishing an account.
- [`prototype/size_experiment.py`](prototype/size_experiment.py) — prints every figure
  on this page. Reads a seeded fixture, reads no account, makes no API calls.
- [`prototype/test_size_experiment.py`](prototype/test_size_experiment.py) — 15
  invariants, including that the swept inputs stay swept and the fixture carries no
  account data.

```
cd prototype && ./size_experiment.py && python3 test_size_experiment.py
```
