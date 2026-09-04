# Developer platform entry point

claude.ai links to the Claude Platform twice, and neither link appears on the left
rail, the one surface a subscriber sees every session. This proposes a sixth rail row,
after **Customize**, pointing at the platform dashboard and shown to subscribers who
declare engineering work.

- **Both existing links are already tracked.** Each carries tracking tags, so these
  clicks are counted today and the test starts with a measured baseline.
- **Both land on a credential, not the product.** Each opens the API keys page, which
  issues a secret rather than showing the product. The row points at the dashboard,
  which shows the product.

**Status:** Designed, working prototype · **Engineering cost:** 2 to 3 days ·
**Theme:** activation · **Revenue path:** direct

Engineering covers the row, its link, and its tracking tags. Experiment setup,
targeting, and the readout are separate and use claude.ai's existing experiment
tooling.

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
  The header holds a single control, which makes it an action strip rather than a
  navigation list.

## Goals

- Establish whether placement, rather than messaging, is what gates subscriber
  activation on the platform.
- Land arrivals on a page that shows the product, and reserve the credential for people
  who ask for one.
- Target on a signal claude.ai already collects, so the test ships in days.

Under [the decision rule this repo states](../README.md), this row is the entry point a
subscriber uses when they start building for others, and it moves no interactive
personal work anywhere, because that work stays on the subscription while it is one
person's.

## Non-goals

- Building new signal collection or a propensity model.
- Changing the plan-limit experience, which already has an answer.
- Changing pricing, packaging, or the platform dashboard itself.
- Removing the existing entry points. They stay, as the control.
- Embedding the dashboard inside claude.ai. The platform refuses third-party framing,
  and a same-origin version is a different and much larger project than this one.

## Proposed experience

- A sixth row in the left rail, directly after **Customize**, separated from the rows
  above it.
- The row label is **Developer platform**, which names the product, not the credential.
  A second arm tests **Build with the API** as the label, because a subscriber who has
  not built anything does not know what a developer platform is.
- The row carries the **New** pill the product already uses for new navigation. The pill
  expires after the subscriber's first click or after 14 days, whichever comes first,
  because a permanent New pill stops meaning anything.
- The row opens a new tab, matching both existing entry points, so a subscriber never
  loses the conversation they were in.
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

The secondary chain is what separates a curiosity click from activation.

## What the placement test settles

- **The baseline:** click-through on the two tagged links, read before the test starts.
- **The landing for a subscriber with no organization:** a second account, checked
  before launch. The mock shows the observed landing.
- **Cannibalization:** the subscription-retention and session-volume guardrails, read
  during the test.

## Evidence

- [`research/entry-points.md`](research/entry-points.md): the two entry points, their
  targets, the rail inventory, and the usage-page finding, observed on the live product
  on 3 September 2026.
- [`research/entry-point-audit.js`](research/entry-point-audit.js): reproduces the
  entry-point table in a browser console. Prints link paths and the names of the tracking
  tags, never their values, so the finding reproduces without publishing an account.
- [`prototype/size_experiment.py`](prototype/size_experiment.py): sizes the placement
  test, impressions per arm and time to a decision, by baseline click-through and
  eligible traffic. Reads a seeded fixture, reads no account, makes no API calls.
- [`prototype/test_size_experiment.py`](prototype/test_size_experiment.py): invariants
  on the sizing, including that the swept inputs stay swept and the fixture carries no
  account data.

```
cd prototype && ./size_experiment.py && python3 test_size_experiment.py
```
