# Developer platform entry point

We propose a sixth rail row, after **Customize**, that opens the platform dashboard and
shows only to subscribers whose profile says they do engineering work. The dashboard
shows what the platform is; the keys page hands you a secret.

**Status:** Designed, working prototype · **Engineering cost:** 2 to 3 days ·
**Theme:** activation · **Revenue path:** direct

## Idea

claude.ai links to the Claude Platform twice, from the account menu and from a settings
page, and both open the API keys page in a new tab. Neither is in the left rail,
the only part of claude.ai a subscriber sees every session. Both carry tracking tags, so
the clicks are already counted.

The left rail is New, Projects, Artifacts, Scheduled, Customize, then projects, then
chats. It has no platform row. This is prime real estate on a high traffic page that can drive discovery and hence, API revenue in the longer run.


### Proposed experience

- A sixth rail row directly after **Customize**, with a separator above it.
- Labeled **Developer platform**, the product's name. A second arm tests
  **Build with the API**.
- The **New** pill the product already uses, expiring after the first click or after
  14 days, whichever comes first.
- Opens a new tab, like both existing links.
- Shown only to subscribers whose profile says Engineering.

## Success metrics

| | Measure |
|---|---|
| **Primary** | Click-through on the rail row, against the instrumented account-menu and settings links |
| **Secondary** | Organizations created, first successful API call within 7 days, still calling at day 30 |
| **Guardrail** | No fall in subscription retention, and no fall in claude.ai session volume |