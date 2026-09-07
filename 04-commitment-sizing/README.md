# Size a commitment from agent run cost

Committed-spend discounts turn metered revenue into contracted revenue. In self-serve,
they stall on one question: how much to commit to. An agent workload takes the guess out
and makes the yearly forecast clear.

**Cost:** About 2 weeks · **Theme:** monetization

[Open the mock](https://madpr.github.io/claude-growth-surfaces/size-commitment.html)

## Problem

Discounts are negotiated and have a human in the loop today. The pricing documentation
says volume discounts "are negotiated on a case-by-case basis", tells high-volume agent
applications to "contact the enterprise sales team for custom pricing arrangements", and
bills everyone else on "actual monthly usage".

The Cost page already has enough inputs to price a credit purchase at a discounted rate
that commits the account to future spend.

## Proposed experience

A Commitment panel sits on the Cost page, under the daily chart, sized for the selected
workspace. It recommends the largest tier consumed in a slow month and states the
breakeven utilization next to it; the mock shows the arithmetic behind every number.

Two weeks is the engineering estimate to build the product. Its definition, the tiers,
the terms, and how the revenue is recognized, is a cross-functional decision with
finance, sales, and legal.

The offer comes in a workload's first 90 days, as soon as there are enough runs to price
one. Not every workspace gets an offer; the panel appears once the workload has run a
certain number of times.

## Success metrics

| Metric | What it tests |
| --- | --- |
| Revenue per contracted account at 90 days, against matched uncontracted accounts | Primary. Whether the commitment grows spend or discounts spend that was coming anyway |
| Commitments accepted inside a workload's first 90 days, and contracted share of API revenue | Leading. Whether a sized offer converts, and converts early |
| Utilization at term end, and renewal | Whether sizing to a slow month is honest. Commitments finishing below breakeven mean the sizing is too aggressive, a term before the renewal number says so |

Guardrail: spend from accounts that saw the panel and declined, against matched accounts
that never saw it.

## Evidence

The discount terms quoted above are from the
[pricing documentation](https://platform.claude.com/docs/en/about-claude/pricing).

The mock runs on three seeded workspaces and an illustrative tier ladder. It reads no
account and calls no API.
