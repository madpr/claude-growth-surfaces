# Size a commitment from agent run cost

Committed-spend discounts turn metered revenue into contracted revenue. In self-serve,
they stall on one question: how much to commit to. An agent workload takes the guess out
and makes the yearly forecast clear.

**Cost:** About 2 weeks · **Theme:** monetization ·
**Revenue path:** direct

[Open the mock](https://madpr.github.io/claude-growth-surfaces/size-commitment.html)

## Problem

Discounts are negotiated and have a human in the loop today. The pricing documentation
says volume discounts "are negotiated on a case-by-case basis", tells high-volume agent
applications to "contact the enterprise sales team for custom pricing arrangements", and
bills everyone else on "actual monthly usage".

The Cost page already holds every input. Those inputs can price a credit purchase at a
discounted rate that commits the account to future spend.

## Proposed experience

A Commitment panel sits on the Cost page, under the daily chart, sized for the selected
workspace. It recommends the largest tier still consumed in a p10 month and states the
breakeven utilization next to it; the mock shows the arithmetic behind every number.

The offer comes in a workload's first 90 days, as soon as there are enough runs to price
one. Sizing needs runs, not months: a thousand runs settle the cost per run whether they
took three weeks or a year. A workload that has already run a year at list price is
spending anyway, and a discount then is margin given away. Early, the offer decides how
the spend gets bought.

Not every workspace gets an offer. The panel appears inside a workload's first 90 days,
once it has run a thousand times and a p10 month clears the smallest tier, and never for
a workspace already on a negotiated rate. Until then the Cost page is just the Cost page.

## Success metrics

| Metric | What it tests |
| --- | --- |
| Commitments accepted inside a workload's first 90 days, and contracted share of API revenue | Primary. Whether a sized offer converts where a blank forecast does not, and whether it converts early |
| Utilization at term end, and renewal | Whether the p10 rule sizes honestly. Commitments finishing below breakeven mean the sizing is too aggressive, a term before the renewal number says so |

Guardrail: revenue per contracted account against matched uncontracted accounts. A
discount on spend that was coming anyway is margin given away.

## Evidence

The pricing documentation
([Pricing](https://platform.claude.com/docs/en/about-claude/pricing)): "Volume discounts
may be available for high-volume users. These are negotiated on a case-by-case basis";
"For high-volume agent applications, contact the enterprise sales team for custom pricing
arrangements"; "Billing is based on actual monthly usage". Managed Agents sessions bill
tokens at model rates plus $0.08 per session-hour, so a run has a price.

The mock runs on three seeded workspaces and an illustrative tier ladder. It reads no
account and calls no API.
