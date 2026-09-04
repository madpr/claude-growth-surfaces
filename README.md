# Claude API — growth surfaces

**North star:** increase Claude API revenue · **Sizing:** one tactical, one medium, one
big bet · **Evidence:** primary sources and running prototypes only

## Problem

The platform is mature wherever you would reach first. Billing, spend controls, prompt
caching, key lifecycle, and rate limits are all built, and the control plane already has
a recommended command line. An idea aimed at one of them proposes rebuilding something
that already works.

What is not built sits **between** products, where a customer does the work by hand:

| Seam | What the customer does today |
|---|---|
| claude.ai and the platform | Goes looking for the platform, and lands on a credential |
| Another vendor and Claude | Translates the code, then cannot prove behavior held |
| Claude Code and hosted agents | Rebuilds the limits that kept the work safe on a laptop |

Each idea below closes one seam. None of them proposes rebuilding something that ships.

## Goals

- Move revenue by removing a manual step between two products, not by adding a feature
  inside one.
- Prove each idea against the live product before designing it, and keep the disproof
  when it kills an idea.
- Keep every number in a case traceable to code that runs.

## Non-goals

- Rebuilding detection, diagnosis, spend caps, or control planes that already ship.
- Ideas that need internal data to be stated at all. Where internal data would sharpen
  a case, the case names the question and marks who can answer it.
- Three variations on one hypothesis. The slate spans different themes by construction.

## The slate

| | Idea | Theme | Engineering cost | Status |
|---|---|---|---|---|
| **S** | [Developer platform entry point](03-platform-entry/) | Activation | ≤ 2–3 days | Designed, working prototype |
| **M** | [OpenAI → Claude migration](02-openai-migration/) | Acquisition | ~2 weeks | Designed, working prototype |
| **L** | [Dev → production](01-dev-to-production/) | Expansion | 1–2 months | Case written, working prototype |

At least two are growth-shaped rather than core-product. Revenue impact is direct for
S and M, and direct but slower for L.

### S — Developer platform entry point

[Read the case](03-platform-entry/) ·
[Open the mock](https://madpr.github.io/claude-growth-surfaces/platform-entry.html)

claude.ai links to the Claude Platform twice. Both links sit behind a menu, and both
land on the API keys page, which issues a credential rather than showing the product.
Neither reaches the left rail, the one surface a subscriber sees every session. Add a
row there, point it at the dashboard, and show it to subscribers who declare
engineering work.

Two findings set the size and the risk:

- **The clicks are already counted.** Both existing links carry tracking tags, so a
  placement test starts with a number to beat rather than building measurement first.
- **The obvious moment is taken.** At the plan limit, claude.ai offers usage credits,
  which keep metered spend on the subscription. Cowork and the referral reward do the
  same. Three shipped surfaces route an existing user's value to the subscription rather
  than the platform, so this case argues against a pattern and says so under Risks.

### M — OpenAI → Claude migration

[Read the case](02-openai-migration/) ·
[Open the prototype](https://madpr.github.io/claude-growth-surfaces/migrations/)

Scans a repository for OpenAI SDK call sites, applies a rulebook, and blocks the pull
request until your eval cases pass. A language migration gates on a compiler, and no
compiler tells you whether a prompt still works, so the merge gates on the repository's
own tests instead.

Prompt rewriting, tool translation, and repository access all already ship. The
remaining work is the parity gate, which is narrower than the whole migration.

### L — Dev → production

[Read the case](01-dev-to-production/) ·
[Terminal demo](https://madpr.github.io/claude-growth-surfaces/promote-cli.html) ·
[Browser demo](https://madpr.github.io/claude-growth-surfaces/promote-to-agent.html)

A workload a developer supervises is bounded by that attention. Running unattended, it
is bounded only by the limits it was given, and Managed Agents is where those limits
live. Claude Code and the platform are two command lines that divide one
account, collide on every word you would search — `agents` means background sessions on
your laptop — and, on the account tested, resolve to two different organizations.

The prototype reads a Claude Code project, emits the agent the platform would run, and
names what cannot cross. Three fields transfer intact, three degrade, and two have no
hosted equivalent. Fourteen reproduced issues reach the same conclusion from the other
direction.

## Bonus

**[Billing attribution and spend confidence](bonus-billing-attribution/)** ·
[Drive the mock](https://madpr.github.io/claude-growth-surfaces/who-is-paying.html)

Outside the slate because it is scoped to Claude Code rather than the API product, and
because its revenue path runs the other way: it moves spend off metered billing and onto
a subscription the customer has already bought. What that protects is subscription
retention, where a $1,200–$2,400 annual plan outweighs the few hundred dollars of
one-off metered spend at stake. Its own README argues that trade.

Behind it: a defect reproduced on the current build, 26 public issues carrying
$1,799.83 in self-reported losses, and a working prototype.

The mock is that prototype made drivable. Export the API key most machines already
carry, start a session, and watch a subscription stop paying without saying so. Two
controls change the answer: whether the machine has a subscription, and whether the
precedence order is the one that ships or the one proposed.

## What was ruled out

Five surfaces were probed and found mature: billing and spend controls, prompt caching,
API key lifecycle, rate limits, and the Managed Agents control plane. Five candidate
ideas died with them.

An earlier pass, before that checking, produced generic growth-playbook material:
rate-limit upgrade prompts, live keys in documentation, efficiency-drives-volume, and
pooled organization spend. Every one of them described something the platform already
does.

Embedding the platform dashboard inside claude.ai was also tested and refused: the
platform sets `frame-ancestors 'self'`, and its session cookies would not travel into a
cross-site frame in any case.

Probing an obvious surface and finding it already built is a result. It is most of the
work behind these three.

## Evidence standards

- Primary documentation, installed binaries, and reproduced defects. No SEO citations,
  no deep-research numbers, and no third-party benchmarks at face value.
- Every issue in a corpus is opened and read, not matched on title.
- Prototypes run on seeded fixtures. They read no account and make no API calls.
- Every figure in a case is printed by the prototype behind it. This checks provenance,
  not worth: a figure computed from invented inputs passes it, so cases state no number
  that would need data an outsider does not have.
- Findings that cannot be reproduced without exposing an account ship as scripts that
  print the finding and none of the values.

## Open questions

These cut across the slate rather than belonging to one case.

- **Does Anthropic intend the subscription or the platform to carry an existing
  customer's incremental work?** Three shipped surfaces choose the subscription. S argues
  against that, the bonus leans into it, and L's revenue framing depends on the answer.
- **Is the subscription and platform organization split deliberate?** If it is, unifying
  the two is a policy argument rather than a growth feature, and L's estimate is wrong.
  Observed on one account; a second account settles whether it generalizes.
- **What a subscriber with no organization sees on the platform dashboard.** If that page
  is empty, S should keep pointing at the API keys page.

## Repo layout

```
<nn>-<slug>/       the three ideas, S is 03
bonus-<slug>/      supporting work, outside the slate
  README.md        the written case
  prototype/       working code, runnable, with tests
  page/            source for the published page
  research/        collected evidence, raw
```

The published site is <https://madpr.github.io/claude-growth-surfaces/>.
