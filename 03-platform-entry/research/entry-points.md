# What claude.ai already links to on the platform

Observed on the live product, 3 September 2026, signed in on a consumer Max plan.
Reproduce with `entry-point-audit.js`, which prints the same table and no identifiers.

## Two entry points exist. Both are already instrumented

| # | Location | Link text | Target | Opens |
|---|---|---|---|---|
| 1 | Account menu, below **Claude Academy** and **Learn more** | "Get API keys / on Claude Platform" | `platform.claude.com/settings/keys` | New tab |
| 2 | Settings, in a section titled **Platform** | "API keys" | `platform.claude.com/settings/keys` | New tab |

Both links have tracking tags appended to the URL — the four standard UTM parameters,
`utm_source`, `utm_medium`, `utm_campaign`, and `utm_content`. These tell the
destination which link a visitor arrived from, which means these clicks are already
being counted. Values are omitted here on purpose; the presence of the tags is the
finding.

Two consequences:

- **A baseline exists.** Click-through on these links is already attributed, so a
  placement test starts with a number to beat instead of spending its first days
  building measurement.
- **Someone owns this funnel.** The idea is not "add a link." It is "move and retarget
  a link that is already measured."

## Both point at a credential, not at the product

`/settings/keys` issues a secret. It assumes the visitor already knows what to build.
`/dashboard`, on the same account, shows organization credits, spend against the monthly
limit, prompt-caching hit rate, token volume, the model lineup, Managed Agents, and a
section for Claude Code usage. Card names are recorded here; values are not.

## The left rail has no platform entry

Sidebar, top to bottom: **New**, **Projects**, **Artifacts**, **Scheduled**,
**Customize**. Then user projects, then chats. Nothing addresses the platform.

The header holds one control, **Use incognito**. It is an action strip, not a
destination list.

## The plan-limit moment is already monetized, in the other direction

The Settings **Usage** page shows session and weekly limits, and offers **usage
credits**: "Turn on usage credits to keep using Claude if you hit a plan limit."

- The page mentions "API" but never mentions "Claude Platform."
- Its only platform link is the same `/settings/keys` row from the settings nav.

So the exhaustion moment already has an answer, and that answer keeps metered spend on
the subscription. A placement test cannot claim the limit wall. It has to claim the
persistent nav.

This matches what the handoff records for Cowork: where Anthropic has shipped a choice
between subscription and platform for an existing audience, it has so far chosen the
subscription. Two surfaces now show the same pattern.

## The dashboard cannot be embedded in claude.ai

Tested 3 September 2026, because an embedded panel would be a better experience than
either a new tab or a full navigation. It is not available. Two independent blocks:

| Block | Evidence |
|---|---|
| The platform refuses third-party framing | `content-security-policy: frame-ancestors 'self'`, and `x-frame-options: SAMEORIGIN` |
| The session would not travel into a frame anyway | Session cookies are `SameSite=lax`, so a cross-site frame sends none of them and the visitor renders signed out |

Reproduce the first by pointing an iframe at `platform.claude.com/dashboard` from any
other origin. The browser renders its broken-frame placeholder rather than the page.

`frame-ancestors 'self'` is the modern header and supersedes `x-frame-options`, so
relaxing framing means changing a deliberate clickjacking defense on a page that carries
billing controls and API keys. That is the right default and should not be traded for a
placement test.

Consequence for the design: the row opens the dashboard rather than embedding it. An
embedded view is not a variant of this idea. It would mean claude.ai rendering platform
data from its own origin, which is a different and much larger project.

## A developer signal is already collected

Settings, Profile: **"What best describes your work?"** — a select, set to
**Engineering** on the account observed. Self-declared, already stored, usable for
targeting without building new collection. That is most of what keeps this idea small.

## Observed once, on one account

- The platform organization contains more than one workspace, one of them named for
  Claude Code. Whether that workspace is created by default is not established here.
- The workspace switcher says **"All workspaces — no combined view for this page"** on
  the dashboard.
- This account already has a provisioned organization with spend, so it cannot show what
  a subscriber with no organization sees at `/dashboard`. That is the open question a
  second account settles, and an outsider can settle it.

## What an outsider can settle, and what needs someone inside

| Question | Who can answer |
|---|---|
| What a subscriber with no organization sees at `/dashboard` | Outsider, second account |
| Whether the Claude Code workspace is created by default | Outsider, second account |
| Whether clicking through provisions a second organization | Outsider, second account |
| Current click-through on the two instrumented links | Inside |
| Share of claude.ai subscribers who declare Engineering | Inside |
| Share of subscribers who already have a platform organization | Inside |
