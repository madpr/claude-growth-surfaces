# Claude API — growth surfaces

Interview exercise. Growth EM, Claude Platform (`platform.claude.com`).
North star: **increase Claude API revenue.**

Three ideas, sized by engineering cost: one tactical (≤2–3 days), one medium
(~2 weeks), one big bet (1–2 months). Each covers hypothesis, success metrics,
implementation, prioritization, risks and mitigations.

## The three ideas

| | Idea | Theme | Eng cost | Status |
|---|---|---|---|---|
| **S** | _tbd_ | — | ≤ 2–3 days | Open |
| **M** | [OpenAI → Claude migration](02-openai-migration/) | Acquisition | ~2 weeks | **Designed, working prototype** |
| **L** | [Dev → production](01-dev-to-production/) | Expansion | 1–2 months | **Direction chosen, not designed** |

[`02-openai-migration/`](02-openai-migration/) — [open the prototype →](https://claude.ai/code/artifact/13a609b1-6d14-49ac-99fe-644f4e0b29c9)

A Migrations surface for the Console, under Build next to Playground. It scans a repo
for OpenAI SDK call sites, applies a rulebook that separates the mechanical from the
genuinely undecidable, and holds the pull request until the team's own eval cases
pass. The parity gate is the part that matters: a language migration gates on a
compiler, and there is no compiler for whether a prompt still works.

Verification reshaped this one twice. Prompt rewriting and tool translation both
turned out to already ship, and the repo connection is already solved by the Claude
GitHub App — so the remaining work is narrower and more buildable than it first
looked.

The **S** slot is still open. A response header on the compatibility endpoint naming
the fields it silently drops is a clean ≤2–3 day item, but it comes from the same
hypothesis as the M and would strain the brief's "span different themes" constraint.
Left unassigned rather than used to fill the slot quietly.

Start with [`01-dev-to-production/README.md`](01-dev-to-production/README.md).
It carries the verified platform facts, the dead ends already ruled out, and the
open questions — enough to resume without re-researching.

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

It sits outside the slate because it is scoped to Claude Code rather than the
API product. Its revenue path is also indirect — it moves spend off metered
billing and onto a subscription the user has already bought — though what that
protects is subscription retention, where a $1,200–$2,400/year plan outweighs the
few hundred dollars of one-off metered spend at stake. Argued in its README
rather than papered over.

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
