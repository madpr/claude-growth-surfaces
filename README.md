# Claude API — growth surfaces

Three ideas for growing Claude API revenue, sized as one tactical, one medium, and one
big bet. None of them adds a feature inside a product, because the surfaces a growth
team would reach for first are already built: billing, spend controls, caching, key
lifecycle, rate limits, and the agent control plane. Each idea removes a manual step
between two products instead.

- **S.** A claude.ai subscriber who wants to build finds the platform in the left rail,
  not in a settings menu.
- **M.** A team moving code off the OpenAI SDK gets a merge gate that proves the
  migration held.
- **L.** A developer whose Claude Code project should run unattended promotes it to a
  hosted agent, with limits set before the first run.

**North star:** increase Claude API revenue · **Sizing:** one tactical, one medium, one
big bet · **Evidence:** primary sources and running prototypes only

## Problem

At each of the three places, the customer does the work by hand today:

| Between | What the customer does today |
|---|---|
| claude.ai and the platform | Goes looking for the platform, and lands on a credential |
| Another vendor and Claude | Translates the code, then cannot prove behavior held |
| Claude Code and hosted agents | Rebuilds the limits that kept the work safe on a laptop |

Each idea below removes one of those steps.

## Which surface carries the work

One rule decides whether work belongs on the subscription or on the platform:

> Work stays on the subscription while it is one person's: run interactively, or on
> their own account. It moves to the platform when it runs unattended against
> infrastructure a team owns, needs limits someone other than the operator sets, or
> bills an organization rather than a person.

Under that rule:

- **S** is the entry point a subscriber uses when they start building for others.
- **M** is unaffected by the rule, because the customer starts on the platform.
- **L** is the moment a workload stops being watched and moves.
- **The bonus** is the guarantee that nothing moves silently.

## Goals

- Move revenue by removing a manual step between two products, not by adding a feature
  inside one.
- Prove each idea against the live product before designing it, and keep the disproof
  when it kills an idea.
- Keep every number in a case traceable to code that runs.

## Non-goals

- Rebuilding detection, diagnosis, spend caps, or control planes that already ship.
- Ideas that need internal data to be stated at all.
- Three variations on one hypothesis. The slate spans different themes by construction.

## The slate

| | Idea | Theme | Engineering cost | Status |
|---|---|---|---|---|
| **S** | [Developer platform entry point](03-platform-entry/) | Activation | 2 to 3 days | Designed, working prototype |
| **M** | [OpenAI → Claude migration](02-openai-migration/) | Acquisition | About 2 weeks | Designed, working prototype |
| **L** | [Dev → production](01-dev-to-production/) | Expansion | 1 to 2 months | Case written, prototype running, two drivable demos |

S and M carry a direct revenue path, and L carries one that is direct but lagging.

### S — Developer platform entry point

[Read the case](03-platform-entry/) ·
[Open the mock](https://madpr.github.io/claude-growth-surfaces/platform-entry.html)

claude.ai links to the Claude Platform twice. Both links sit behind a menu, and both
land on the API keys page, which issues a credential rather than showing the product.
Neither reaches the left rail, the one surface a subscriber sees every session. Add a
row there, point it at the dashboard, and show it to subscribers who declare
engineering work.

Two findings set the size and the scope:

- **The clicks are already counted.** Both existing links carry tracking tags, so a
  placement test starts with a number to beat rather than building measurement first.
- **The obvious moment is taken.** At the plan limit, claude.ai offers usage credits,
  which keep metered spend on the subscription, and Cowork keeps scheduled work there
  too. Two shipped surfaces keep one person's work on their own account, which is what
  the rule above says they should do. The rail row is the entry point the decision rule
  describes, for a subscriber who starts building for others, and it leaves the
  plan-limit moment alone.

### M — OpenAI → Claude migration

[Read the case](02-openai-migration/) ·
[Open the prototype](https://madpr.github.io/claude-growth-surfaces/migrations/)

Scans a repository for OpenAI SDK call sites, applies a rulebook, and blocks the pull
request until the repository's own tests pass against Claude. A language migration
gates on a compiler, and no compiler tells you whether a prompt still works, so the
merge gates on those tests instead.

Prompt rewriting, tool translation, and repository access all already ship. The
remaining work is the parity gate, which is narrower than the whole migration.

### L — Dev → production

[Read the case](01-dev-to-production/) ·
[Terminal demo](https://madpr.github.io/claude-growth-surfaces/promote-cli.html) ·
[Browser demo](https://madpr.github.io/claude-growth-surfaces/promote-to-agent.html)

A workload a developer supervises is bounded by that attention. Running unattended, it
is bounded only by the limits it was given, and Managed Agents is where those limits
live. Claude Code and the platform are two command lines that divide one account. They
collide on every word you would search, so that inside Claude Code "agents" means
background sessions on your laptop, and on the account tested they resolve to two
different organizations.

The prototype reads a Claude Code project, emits the agent the platform would run, and
names what does not transfer. Three fields transfer intact, three degrade, and two have
no hosted equivalent. Fourteen issues, each opened and read, reach the same conclusion
from the other direction.

## Bonus

**[Billing attribution](bonus-billing-attribution/)** ·
[Drive the mock](https://madpr.github.io/claude-growth-surfaces/who-is-paying.html)

Outside the slate because it is scoped to Claude Code rather than the API product, and
because its revenue path runs the other way: it moves spend off metered billing and onto
a subscription the customer has already bought. What that protects is subscription
retention: the loss in those reports is trust in a plan already paid for, not the
refund.

Under the rule above, the bonus is the guarantee that a person's interactive session is
never billed to an organization without saying so. Behind it are a defect reproduced on
the current build, a written proposal, a working prototype, and 26 public issues
carrying $1,799.83 in self-reported losses.

The mock is that prototype made drivable. Export the API key most machines already
carry, start a session, and watch a subscription stop paying without saying so. Two
controls change the answer: whether the machine has a subscription, and whether the
precedence order is the one that ships or the one proposed.

## What was ruled out

Each idea was checked against what the platform ships before it was designed. Five
surfaces were probed and found mature: billing and spend controls, prompt caching, API
key lifecycle, rate limits, and the Managed Agents control plane. Five candidate ideas
died with them.

Embedding the platform dashboard inside claude.ai was also tested and refused: the
platform sets `frame-ancestors 'self'`, and its session cookies do not reach a
cross-site frame in any case.

## Evidence standards

- Primary documentation, installed binaries, and reproduced defects. No SEO citations,
  no deep-research numbers, and no third-party benchmarks at face value.
- Every issue in a corpus is opened and read, not matched on title.
- Prototypes run on seeded fixtures. They read no account and make no API calls.
- Every figure in a case is printed by the prototype behind it, so a case and its code
  cannot disagree. Where an input is not public, the prototype sweeps it and the case
  reads the table.
- Findings that cannot be reproduced without exposing an account ship as scripts that
  print the finding and none of the values.

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
