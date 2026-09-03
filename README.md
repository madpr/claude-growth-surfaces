# Claude API — growth surfaces

North star: **increase Claude API revenue.**

Three ideas, sized by engineering cost: one tactical (≤2–3 days), one medium
(~2 weeks), one big bet (1–2 months). Each covers hypothesis, success metrics,
implementation, prioritization, risks and mitigations.

Each one was checked against what the platform already ships before it was written
up, and the checking is the load-bearing part: five surfaces were probed and found
already built, killing five candidate ideas. What survives is what survived that.

## The three ideas

| | Idea | Theme | Eng cost | Status |
|---|---|---|---|---|
| **S** | [Cache break-even](03-cache-breakeven/) | Monetization | ≤ 2–3 days | **Designed, working prototype** |
| **M** | [OpenAI → Claude migration](02-openai-migration/) | Acquisition | ~2 weeks | **Designed, working prototype** |
| **L** | [Dev → production](01-dev-to-production/) | Expansion | 1–2 months | **Case written, working prototype** |

[`02-openai-migration/`](02-openai-migration/) — [open the prototype →](https://claude.ai/code/artifact/13a609b1-6d14-49ac-99fe-644f4e0b29c9)

Scans a repo for OpenAI SDK call sites, applies a rulebook, and blocks the pull
request until your eval cases pass. The parity gate is the point: a language
migration gates on a compiler, and no compiler tells you whether a prompt still works.

Verification cut the scope twice. Prompt rewriting, tool translation, and repo access
all already ship, so the remaining work is narrower than it looked.

[`03-cache-breakeven/`](03-cache-breakeven/) — [open the prototype →](https://claude.ai/code/artifact/2b514045-cf23-496e-a97f-0fd5ffbd13bc)

The Console's Caching page already charts write amortization — tokens read back per
token written — and captions it "higher means better." There is an exact number where
better becomes worse: **0.28× on the 5-minute TTL, 1.11× on the 1-hour**. Below it,
caching bills more than switching it off. The chart's axis starts at 0.50×, so the
whole 5-minute danger zone sits below the visible range.

Draw the line. That is the change — a threshold on a chart that already exists.
Checking the live Console cut this idea twice: detection and diagnosis are both built,
and an earlier draft that proposed selling managed caching did not survive seeing the
page.

A response header naming the fields the compatibility layer drops was the other
candidate for this slot. It is a clean two-day item, but it shares a hypothesis with
the M and would strain the span-different-themes constraint.

[`01-dev-to-production/`](01-dev-to-production/) — run the prototype:
`cd 01-dev-to-production/prototype && ./promote.py map fixtures/ledger-reconcile`

A supervised workload is a $10/month prototype; unattended it is a $1,000/month
production workload. Managed Agents is where the unattended version is bounded. The
gap is that Claude Code and the platform are two CLIs that divide one account, collide
on every word you would search — `agents` means background sessions on your laptop —
and, on the account tested, resolve to two different organizations.

The prototype is the missing verb: it reads a Claude Code project and emits the agent
the platform would run, then names what cannot cross. Its own count corrected this
case's first draft. The skeleton transfers; the containment does not, which is the
same conclusion fourteen reproduced issues reach from the other direction.

It carries the verified platform facts and the dead ends already ruled out, so it is
the file to start with.

The surfaces probed and found mature: billing and spend controls, prompt caching, API
key lifecycle, rate limits, and the Managed Agents control plane — which already has a
CLI, and a recommended one. A first pass, before any of that checking, produced generic
growth-playbook material (rate-limit upgrade prompts, live keys in docs,
efficiency-drives-volume, pooled org spend). None of it survived contact with the
product. Probing an obvious surface and finding it already built is a result, not a
dead end, and it is most of the work behind these three.

## Bonus

**[Billing attribution & spend confidence](bonus-billing-attribution/)** —
[read the case →](https://claude.ai/code/artifact/0502f696-82e4-45c8-9a93-38b70868752a)

Included as a bonus rather than as one of the three. It came from a real painpoint
and it set the evidentiary bar the rest of the repo is held to: a defect reproduced
on the current build, 26 public issues with $1,799.83 in self-reported losses, and a
working prototype.

It sits outside the slate because it is scoped to Claude Code rather than the
API product. Its revenue path is also indirect — it moves spend off metered
billing and onto a subscription the user has already bought — though what that
protects is subscription retention, where a $1,200–$2,400/year plan outweighs the
few hundred dollars of one-off metered spend at stake. Argued in its README
rather than papered over.

It is here because it set that standard first, and because the standard held: every
number on a page in this repo is printed by the prototype behind it, so a page and
its code cannot disagree. Twice that rule has forced a written claim to be corrected
rather than the number to be rounded.

## Repo layout

```
<nn>-<slug>/       the three ideas
bonus-<slug>/      supporting work, outside the slate
  README.md        the written case
  prototype/       working code, runnable
  page/            published artifact source
  research/        collected evidence, raw
```

## Constraints

- Ideas should **span different themes**, not three variations on one hypothesis.
- **At least two** should be growth-shaped (acquisition / activation / retention /
  monetization mechanics) rather than core-product.
- Revenue impact may be direct or indirect.
