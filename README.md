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
| **S** | [Developer platform entry point](03-platform-entry/) | Activation | ≤ 2–3 days | **Designed, working prototype** |
| **M** | [OpenAI → Claude migration](02-openai-migration/) | Acquisition | ~2 weeks | **Designed, working prototype** |
| **L** | [Dev → production](01-dev-to-production/) | Expansion | 1–2 months | **Case written, working prototype** |

[`02-openai-migration/`](02-openai-migration/) — [open the prototype →](https://madpr.github.io/claude-growth-surfaces/migrations/)

Scans a repo for OpenAI SDK call sites, applies a rulebook, and blocks the pull
request until your eval cases pass. The parity gate is the point: a language
migration gates on a compiler, and no compiler tells you whether a prompt still works.

Verification cut the scope twice. Prompt rewriting, tool translation, and repo access
all already ship, so the remaining work is narrower than it looked.

[`03-platform-entry/`](03-platform-entry/) — drive the mock:
[`page/platform-entry.html`](03-platform-entry/page/platform-entry.html)

claude.ai links to the Claude Platform twice. Both links sit behind a menu, and both
land on the API keys page, which issues a credential rather than showing the product.
Neither reaches the left rail, the one surface a subscriber sees every session. Add a
row there, point it at the dashboard, and show it to subscribers who declare
engineering work.

Probing the live product is what shaped this. Both existing links already carry
campaign parameters, so the test measures lift against an instrumented control instead
of standing up tracking, which is most of what keeps the idea inside two days. The
obvious moment to sell the platform turned out to be taken: at the plan limit claude.ai
offers usage credits, which keep metered spend on the subscription. Cowork and the
referral reward do the same. **Three shipped surfaces route an existing user's value to
the subscription rather than the platform**, so this case argues against a pattern, and
says so under Risks rather than working around it.

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
