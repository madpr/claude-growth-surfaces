# Claude API — growth surfaces

Interview exercise. Growth EM, Claude Platform (`platform.claude.com`).
North star: **increase Claude API revenue.**

Three ideas, sized by engineering cost: one tactical (≤2–3 days), one medium
(~2 weeks), one big bet (1–2 months). Each covers hypothesis, success metrics,
implementation, prioritization, risks and mitigations.

## Ideas

| | Idea | Theme | Eng cost | Status |
|---|---|---|---|---|
| — | [Billing attribution & spend confidence](01-billing-attribution/) | Trust / spend confidence | ~3 days | Built — tier assignment open |
| | _second idea_ | — | — | Pending research pass |
| | _third idea_ | — | — | Pending research pass |

**[→ Read the case for idea 01](https://claude.ai/code/artifact/0502f696-82e4-45c8-9a93-38b70868752a)**

## Where this stands

Idea 01 is complete: a reproducible defect on the current build, a 26-issue
evidence corpus with $1,799.83 in self-reported losses, and a working prototype.
Its open question is which tier it belongs to — and whether it belongs in the
slate at all, given it is scoped to Claude Code rather than the API product and
its direct effect is to move revenue *off* the API. That argument is laid out
honestly in its README rather than papered over.

The remaining two ideas are deliberately not filled in yet. The first pass at
them was generated from the standard dev-tool growth playbook — rate-limit
upgrade prompts, live keys in docs, efficiency-drives-volume, pooled org spend —
and none of it was checked against what `platform.claude.com` already ships.
Console workspaces, spend limits, prompt caching and the Batch API may already
cover parts of it. Ideas go in this repo after that verification, not before.

The bar idea 01 set: a defect reproduced on the current build, a corpus of real
user reports, and something that runs.

## Repo layout

```
<nn>-<slug>/
  README.md      the written case
  prototype/     working code, runnable
  page/          published artifact source
  research/      collected evidence, raw
```

## Constraints from the brief

- Ideas should **span different themes**, not three variations on one hypothesis.
- **At least two** should be growth-shaped (acquisition / activation / retention /
  monetization mechanics) rather than core-product.
- Revenue impact may be direct or indirect.
