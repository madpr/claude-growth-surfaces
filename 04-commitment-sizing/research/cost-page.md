# The Console's Cost page, as observed

Observed on the live product, September 6, 2026, signed in as an organization admin.
Values are left out on purpose; the layout is the finding.

## Where it sits

Sidebar, top to bottom: **Dashboard**, **API keys**, then **Build** (Playground, marked
New; Files; Skills; Batches), **Managed Agents** (Quickstart, Agents, Sessions,
Deployments, Environments, Credential vaults, Memory stores), **Analytics** (Usage,
Caching, Rate limits, Cost, Logs), **Claude Code** (Usage, Settings), and **Manage**
(Rate limits, Spend limits, Service accounts, App Integrations, marked Beta; Security).
Below the nav: Notifications, Documentation, Credits with the balance, and the signed-in
user with their role.

Above the nav: the workspace switcher, reading "All workspaces", and Search Console.

## What the Cost page shows

- Title **Cost**. Subtitle: "Cost of your organization's usage over time. All dates are
  in UTC."
- An information bar: "Costs from your service accounts are only shown when grouping by
  service account", with a **Group by service account** button.
- Filters, left to right: **Workspace**, **API key**, **Model**, **Range** (default Last
  30 days), then **Group by** (default Model). A download control on the right.
- Five cards: **Total cost**; **Total token cost**, with a second line "List price
  before discount"; **Total web search cost**; **Total code execution cost**; **Total
  session runtime cost**.
- One chart, **Daily token cost**, subtitled "Includes token usage from both API and
  Console", one series per model, plus a "List price (before discount)" series in the
  legend.
- Nothing below the chart.

## What the Usage page shows

Title **Usage**, subtitle "Token usage across your organization over time. All dates are
in UTC." Filters: Workspace, Range, API key, Account, Model, Group by. Three cards: Total
tokens in, Total tokens out, Total web searches. One chart, **Token usage**. Tokens, no
dollars. That is why the panel goes on Cost.

## Two consequences

- The page already compares what was paid with list price. A commitment is priced
  against exactly that comparison, so the panel adds a third number to a pair the page
  already shows.
- The Workspace filter is the unit of sizing. A workload that lives in its own workspace
  has a monthly cost on this page and a run count under Sessions.

## What the documentation says about discounts

[Pricing](https://platform.claude.com/docs/en/about-claude/pricing), read the same day:

- "Volume discounts may be available for high-volume users. These are negotiated on a
  case-by-case basis."
- "For high-volume agent applications, contact the enterprise sales team for custom
  pricing arrangements."
- "Billing is based on actual monthly usage"
- Managed Agents: "Session runtime · $0.08 per session-hour", accruing only while the
  session's status is `running`. Tokens bill at model rates.

[Usage and Cost API](https://platform.claude.com/docs/en/manage-claude/usage-cost-api),
read the same day:

- "This data is similar to the information available in the Usage and Cost pages of the
  Claude Console."
- The cost report groups "by workspace or description"; daily granularity only.
- The usage report filters and groups by API key, workspace, model, and service tier.
