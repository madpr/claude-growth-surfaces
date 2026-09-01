# Claude API — growth surfaces

Interview exercise. Growth EM, Claude Platform (`platform.claude.com`).
North star: **increase Claude API revenue.**

Three ideas, sized by engineering cost: one tactical (≤2–3 days), one medium
(~2 weeks), one big bet (1–2 months). Each covers hypothesis, success metrics,
implementation, prioritization, risks and mitigations.

## The three ideas

| | Idea | Theme | Eng cost | Status |
|---|---|---|---|---|
| **S** | _tbd_ | — | ≤ 2–3 days | Pending research pass |
| **M** | _tbd_ | — | ~2 weeks | Pending research pass |
| **L** | _tbd_ | — | 1–2 months | Pending research pass |

Ideas go here after they are checked against what `platform.claude.com` already
ships — pricing tiers and how limits are communicated, what Console workspaces
and spend limits already cover, how prompt caching and the Batch API are
surfaced, and what the signup-to-first-call path costs. A first pass produced
generic growth-playbook material (rate-limit upgrade prompts, live keys in docs,
efficiency-drives-volume, pooled org spend) that had not been verified against
any of it. That verification comes first.

## Bonus

**[Billing attribution & spend confidence](bonus-billing-attribution/)** —
[read the case →](https://claude.ai/code/artifact/0502f696-82e4-45c8-9a93-38b70868752a)

Included as a bonus rather than as one of the three. It came from a real
painpoint, and it is the only item here that survived verification: a defect
reproduced on the current build, 26 public issues with $1,799.83 in self-reported
losses, and a working prototype.

It sits outside the slate for two honest reasons. It is scoped to Claude Code
rather than the API product, and its direct effect is to move revenue *off* the
API and onto subscriptions — the trust and churn argument for it is real but
second-order. Both are argued in its README rather than papered over.

It is here because it shows the standard the three ideas should meet: a defect
reproduced on the current build, a corpus of real user reports, and something
that runs.

## Repo layout

```
<nn>-<slug>/       the three ideas
bonus-<slug>/      supporting work, outside the slate
  README.md        the written case
  prototype/       working code, runnable
  page/            published artifact source
  research/        collected evidence, raw
```

## Constraints from the brief

- Ideas should **span different themes**, not three variations on one hypothesis.
- **At least two** should be growth-shaped (acquisition / activation / retention /
  monetization mechanics) rather than core-product.
- Revenue impact may be direct or indirect.
