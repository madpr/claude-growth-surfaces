# Developer platform entry point

We propose a sixth rail row, labeled Developer platform, after Customize. It opens the
platform dashboard and shows only to subscribers whose profile says they do engineering
work. The dashboard shows what the platform is; the keys page hands you a secret.

**Cost:** 2 to 3 days · **Theme:** activation ·
**Revenue path:** direct

[Open the mock](https://madpr.github.io/claude-growth-surfaces/platform-entry.html)

## Problem

claude.ai links to the Claude Platform twice, from the account menu and from a settings
page, and both open the API keys page in a new tab. Neither is in the left rail, the only
part of claude.ai a subscriber sees every session. This is prime real estate on a
high-traffic page. It can drive discovery and, in the longer run, API revenue.

## Proposed experience

- A sixth rail row directly after Customize, with a separator above it.
- Labeled **Developer platform**, the product's name. A second arm tests
  **Build with the API**.
- The **New** pill the product already uses, expiring after the first click or after
  14 days, whichever comes first.
- Opens a new tab, like both existing links.
- Shown only to subscribers whose profile says Engineering and who have no platform
  organization yet.

## Success metrics

| Metric | What it tests |
| --- | --- |
| First successful API call within 7 days, against a control group that does not see the row | Primary. Whether the row creates platform customers |
| Organizations created, and accounts still calling at day 30 | Secondary. Whether the first call becomes repeat use |
| Click-through on the rail row, against the two existing links | Diagnostic. Whether placement is what gates the first call |

Guardrail: no fall in subscription retention, and no fall in claude.ai session volume.
