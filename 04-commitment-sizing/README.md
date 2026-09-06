# Size a commitment from agent run cost

Committed-spend discounts turn metered revenue into contracted revenue, and self-serve
they stall on one question: how much to commit to. A team asked to forecast a year of
usage guesses, guesses low, and stays on pay-as-you-go. An agent workload takes the guess
out. The Console already knows what a run costs and how many runs a month there are, so
it can do the arithmetic, offer the largest tier that is still consumed in a bad month,
and show the loss on every tier above it.

**Status:** Designed · **Cost:** About 2 weeks · **Theme:** monetization ·
**Revenue path:** direct

[Open the mock](https://madpr.github.io/claude-growth-surfaces/size-commitment.html)

## Problem

Discounts are negotiated. The pricing documentation says volume discounts "are
negotiated on a case-by-case basis", tells high-volume agent applications to "contact
the enterprise sales team for custom pricing arrangements", and bills everyone else on
"actual monthly usage". The accounts best placed to commit, the ones running an agent at
a known cost per run, are sent to a sales conversation most mid-sized accounts never
start.

The Cost page already holds every input. I opened it on my own account on September 6,
2026: it filters by workspace, shows total cost next to "List price before discount",
and splits token cost from session runtime cost. It stops one step short of an offer.

Sizing is the hard part, and it is lopsided. Prepaying C at a discount d buys credits
worth C / (1 − d) at list price; unused credits expire, and usage past them bills at
list. Breakeven utilization is therefore 1 − d whatever the tier, so a 13% discount is a
bet that you consume 87% of what you bought. Size at expected spend and roughly half of
all months land below that line. An account that underuses once feels cheated and does
not renew.

## Proposed experience

A Commitment panel on the Cost page, under the daily chart, sized for the selected
workspace:

- The cost of a batch you name, with an 80% band. Single runs are heavy-tailed, batch
  totals are not, so in the seeded production workload the band on 1,000 runs is 7.7%
  of the estimate while the p95 run is nearly four times the median.
- Projected monthly spend at list price, with the p10 month next to it.
- The full tier ladder: breakeven utilization, saving per year, and the share of months
  that would fall below breakeven, losses included.
- The offer. The largest tier still consumed in a p10 month is recommended; the seeded
  production workload gets Growth at 9%, $11,868 a year. One tier up is shown as a
  stretch when fewer than a quarter of months would miss breakeven, with the share
  stated: Scale saves $53,793 a year and misses in 12% of months. The pilot workload,
  three months old and volatile, gets no recommendation, only the closest tier and its
  risk.

The ladder in the mock is illustrative; thresholds and discounts come from finance.
Prepaid credits already exist in the Console, so the two weeks cover the sizing and the
panel.

## Success metrics

| Metric | What it tests |
| --- | --- |
| Commitments accepted from the panel, and contracted share of API revenue | Primary. Whether a sized offer converts where a blank forecast does not |
| Utilization at term end, and renewal | Whether the p10 rule sizes honestly. Commitments finishing below breakeven mean the sizing is too aggressive, a term before the renewal number says so |

Guardrail: revenue per contracted account against matched uncontracted accounts. A
discount on spend that was coming anyway is margin given away.

## Evidence

The pricing documentation, read September 6, 2026
([Pricing](https://platform.claude.com/docs/en/about-claude/pricing)): "Volume discounts
may be available for high-volume users. These are negotiated on a case-by-case basis";
"For high-volume agent applications, contact the enterprise sales team for custom pricing
arrangements"; "Billing is based on actual monthly usage". Managed Agents sessions bill
tokens at model rates plus $0.08 per session-hour, so a run has a price.

The Cost page on my account, September 6, 2026, recorded in
[`research/cost-page.md`](research/cost-page.md) with values left out: filters for
workspace, API key, model, range, and grouping; five cards, one of them "List price
before discount"; a daily token cost chart. The Usage and Cost Admin API
([documentation](https://platform.claude.com/docs/en/manage-claude/usage-cost-api))
returns the same data grouped by workspace and day, so a workload in its own workspace
already has a monthly cost and, from its sessions, a run count.

The mock runs on three seeded workspaces and an illustrative tier ladder. It reads no
account and calls no API.
