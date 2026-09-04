# Developer platform entry point

I signed into claude.ai on my Max plan and went looking for the Claude Platform. It is
linked twice, once from the account menu and once from a settings page, and both links
open the API keys page in a new tab. Neither is in the left rail, which is the only part
of claude.ai a subscriber sees every session. Both links already have tracking tags on
the URL, so somebody is counting these clicks today.

I propose a sixth rail row, after **Customize**, that opens the platform dashboard and
shows only to subscribers who say on their profile that they do engineering work. The
dashboard shows what the platform is; the keys page hands you a secret. And because the
two existing links are already counted, the test starts with a number to beat.

**Status:** Designed, working prototype · **Engineering cost:** 2 to 3 days ·
**Theme:** activation · **Revenue path:** direct

The estimate covers the row, its link, and its tracking tags. Setting up the experiment,
targeting it, and reading it out happen in the experiment tooling claude.ai already has,
and I haven't counted them.

## Problem

Anthropic sells two products to a lot of the same people, and a paid subscriber who could
also be a platform customer has to go find the second one.

I started in the account menu. Below Claude Academy and Learn more there is a link that
reads "Get API keys / on Claude Platform", and it opens
`platform.claude.com/settings/keys` in a new tab. You only open that menu if you already
want something in it.

Settings has a section titled **Platform** with exactly one row in it, "API keys", and
that row opens the same keys page. So both of the links claude.ai has hand you a secret
and assume you know what to do with it. The dashboard on the same account is the page I
would want a curious subscriber to see. It shows credits, spend against the monthly
limit, the prompt-caching hit rate, token volume, the model lineup, Managed Agents, and a
section for Claude Code usage, which is to say it shows what the platform is. Nothing in
claude.ai links to it.

Then I opened the usage page, which is where you end up when you hit a plan limit. It
shows the session and weekly limits and offers usage credits: "Turn on usage credits to
keep using Claude if you hit a plan limit." It mentions "API" but never says "Claude
Platform", and its only platform link is the same API keys row from the settings nav. So
when you hit your limit, claude.ai offers to sell you more of the subscription and never
names the platform. A placement test can't claim the limit wall. It has to claim the nav.

Last, the left rail. Top to bottom it is New, Projects, Artifacts, Scheduled, Customize,
then your projects, then your chats. The header has one control, Use incognito, so it
isn't a place to put a destination either. The platform is in none of it.

## Goals

- Find out whether placement, rather than messaging, is what keeps subscribers off the
  platform.
- Send arrivals to a page that shows the product, and give out the credential only to
  people who ask for one.
- Target on a signal claude.ai already collects, so the test ships in days.

Under [the decision rule this repo states](../README.md), this row is the entry point a
subscriber uses when they start building for others, and it moves no interactive
personal work anywhere, because that work stays on the subscription while it is one
person's.

## Non-goals

- Building new signal collection or a propensity model. The profile question "What best
  describes your work?" is already there and already stored.
- Changing the plan-limit experience, which already has an answer.
- Changing pricing, packaging, or the platform dashboard itself.
- Removing the existing entry points. They stay, as the control.
- Embedding the dashboard inside claude.ai. I tried. The platform sends
  `frame-ancestors 'self'`, and its session cookies would not travel into a cross-site
  frame anyway, so a visitor would render signed out. A same-origin version is a
  different and much larger project than this one.

## Proposed experience

- A sixth row in the left rail, directly after **Customize**, with a separator above it.
- I labeled it **Developer platform** because that is the product's name, and the two
  links that exist today are named for the credential. A second arm tests
  **Build with the API** as the label, since a subscriber who hasn't built anything yet
  may not know what a developer platform is.
- The row gets the **New** pill the product already uses for new navigation. I set it to
  expire after the subscriber's first click or after 14 days, whichever comes first. A
  New pill that never goes away stops meaning anything.
- The row opens a new tab, the same as both existing links, so nobody loses the
  conversation they were in.
- It has the same tracking tags the two existing links already have, so all three
  placements show up on the same report.
- Only subscribers whose profile says Engineering see it. Everyone else sees today's
  rail.

## Success metrics

| | Measure |
|---|---|
| **Primary** | Click-through on the rail row, against the instrumented account-menu and settings links |
| **Secondary** | Organizations created, first successful API call within 7 days, still calling at day 30 |
| **Guardrail** | No fall in subscription retention, and no fall in claude.ai session volume |

A click on its own could be curiosity. The secondary row is where I would see
activation.

## What the placement test settles

- The baseline. Click-through on the two tagged links is already counted, so I read it
  before the test starts and that is the number to beat.
- What a subscriber with no organization sees at the dashboard. I don't know yet; my
  account already has a provisioned organization with spend on it, so a second account
  would tell me. The mock shows what my account saw.
- Whether the row pulls anything off the subscription. The retention and session-volume
  guardrails answer that while the test runs.

## Evidence

- [`research/entry-points.md`](research/entry-points.md): what I found on the live
  product on 3 September 2026. The two entry points and where they go, the rail, and the
  usage page.
- [`research/entry-point-audit.js`](research/entry-point-audit.js): paste it into a
  browser console on claude.ai and it prints the same table. It prints link paths and
  the names of the tracking tags, never their values, so you can reproduce the finding
  without publishing your account.
- [`prototype/size_experiment.py`](prototype/size_experiment.py): sizes the test. Given
  a baseline click-through and eligible traffic, it prints impressions per arm and days
  to a decision. It reads a seeded fixture, reads no account, and makes no API calls.
- [`prototype/test_size_experiment.py`](prototype/test_size_experiment.py): checks the
  sizing, including that the swept inputs stay swept and that the fixture holds no
  account data.

```
cd prototype && ./size_experiment.py && python3 test_size_experiment.py
```
