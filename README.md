# Claude API — growth surfaces

This is a set of three product ideas for growing Claude API revenue, one small, one
medium, one big. I started by checking the places a growth team would look first,
billing, spend limits, caching, keys, rate limits, the agent control plane, and found
every one of them already built. So none of these ideas add a feature inside a
product. Each one takes a step a customer does by hand today, somewhere between two
Anthropic products, and removes it.

The small one puts the developer platform in claude.ai's left rail, where a subscriber
who wants to build will actually see it. The medium one gives a team moving code off
the OpenAI SDK a merge gate that proves the migration held. The big one takes a Claude
Code project that ought to be running unattended and promotes it to a hosted agent,
with the limits set before the first run.

**North star:** increase Claude API revenue · **Sizing:** one tactical, one medium, one
big bet · **Evidence:** primary sources and running prototypes only

## Problem

I wrote down what the customer does today at each of the three places these ideas
touch. All three are steps done by hand.

| Between | What the customer does today |
|---|---|
| claude.ai and the platform | Goes looking for the platform, and lands on a credential |
| Another vendor and Claude | Translates the code, then cannot prove behavior held |
| Claude Code and hosted agents | Rebuilds the limits that kept the work safe on a laptop |

One idea per row. Each removes that step.

## Which surface carries the work

I needed a rule for when work belongs on the claude.ai subscription and when it belongs
on the platform, because the ideas kept pulling in different directions. S sends a
subscriber toward the platform, L moves a whole workload there, and the bonus sends
spend back the other way, onto a subscription. For a while I couldn't say why all
three were right at once. This is the rule that made them agree.

> Work stays on the subscription while it is one person's: run interactively, or on
> their own account. It moves to the platform when it runs unattended against
> infrastructure a team owns, needs limits someone other than the operator sets, or
> bills an organization rather than a person.

S is the entry point a subscriber uses when they start building for others. M never
meets the rule at all, since that customer is on the platform from the first day. L is
the point where a workload stops being watched and moves. The bonus is the guarantee
that nothing moves silently.

## Goals

- Grow revenue by removing a manual step between two products.
- Check each idea against the live product before designing it, and keep the disproof
  when it kills one.
- Keep every number in a case traceable to code that runs.

## Non-goals

- Rebuilding detection, diagnosis, spend caps, or control planes. All of those ship
  today.
- Ideas I can't state without internal data.
- Three variations on one hypothesis. Each idea has its own theme on purpose.

## The slate

| | Idea | Theme | Engineering cost | Status |
|---|---|---|---|---|
| **S** | [Developer platform entry point](03-platform-entry/) | Activation | 2 to 3 days | Designed, working prototype |
| **M** | [OpenAI → Claude migration](02-openai-migration/) | Acquisition | About 2 weeks | Designed, working prototype |
| **L** | [Dev → production](01-dev-to-production/) | Expansion | 1 to 2 months | Case written, prototype running, two drivable demos |

S and M have a direct revenue path. L's is direct too, but it shows up about a quarter
after the workload moves.

### S — Developer platform entry point

[Read the case](03-platform-entry/) ·
[Open the mock](https://madpr.github.io/claude-growth-surfaces/platform-entry.html)

I went looking for how a claude.ai subscriber gets to the Claude Platform and found two
links. One is in the account menu, below Claude Academy. The other is in a settings
section titled Platform that holds exactly one row. Both open the API keys page, so the
first thing a curious subscriber sees is a secret. Neither is in the left rail, the one
part of the product every subscriber looks at every session. The idea is a row there,
pointing at the dashboard, shown to subscribers who say they do engineering work.

Two things I found set the size of this. Both existing links already carry tracking
tags, so those clicks are counted today and a placement test starts with a number to
beat. And the plan limit, which I'd assumed was the obvious hook, is already spoken
for: when you hit it, claude.ai offers to sell you usage credits, and never mentions
the platform. Cowork keeps scheduled work on the subscription too. Both of those keep
one person's work on their own account, so the rail row leaves the plan limit alone and
only serves a subscriber who has started building for others.

### M — OpenAI → Claude migration

[Read the case](02-openai-migration/) ·
[Terminal demo](https://madpr.github.io/claude-growth-surfaces/migrate.html)

Point Claude Code at a repository that uses the OpenAI SDK. It scans for call sites,
applies a rulebook, asks the two questions only a person can answer, and then blocks
the pull request until the repository's own tests pass against Claude. A language
migration gates on a compiler. No compiler tells you whether a prompt still works, so
the merge gates on those tests instead.

What surprised me was how much of the migration already ships. Anthropic runs a
compatibility layer that translates OpenAI SDK calls server-side, tool calls included,
and the Claude GitHub App already has repository access. What neither does is tell you
what broke. On a seeded payload the linter found seven fields the layer silently
ignores that break the output contract, every one of them structured output or a
strict tool schema, so a team that evaluates Claude through the layer loses schema
enforcement and reads the unenforced result as the model's ceiling. The parity gate is
the only piece left to build, and it's far narrower than the whole migration.

### L — Dev → production

[Read the case](01-dev-to-production/) ·
[Terminal demo](https://madpr.github.io/claude-growth-surfaces/promote-cli.html) ·
[Browser demo](https://madpr.github.io/claude-growth-surfaces/promote-to-agent.html)

While I'm watching an agent, my attention is the limit on what it can spend or break.
The minute it runs on a schedule with nobody watching, the only limits are the ones
somebody set up front, and right now Managed Agents is the only place those limits
exist. Nothing takes a Claude Code project there. On my own account, which uses Claude
Code daily, there were zero hosted agents. Claude Code and the platform ship as two
command-line tools that split one account, and they collide on every word you'd
search; inside Claude Code, `agents` means background sessions on your laptop. When I
signed into both tools with the same email, they reported two different organization
IDs. I did not expect that.

The prototype reads a Claude Code project, writes out the agent the platform would run,
and names what doesn't survive the trip. Three fields transfer intact, three degrade,
and two have no hosted equivalent at all. Fourteen issues from the Claude Code tracker,
each of which I opened and read, get to the same place from the other direction: in
eleven of them the agent acted outside its mandate. One filer wrote "no harm done, but
it makes me very worried." Nothing broke, and they filed anyway.

## Bonus

**[Billing attribution](bonus-billing-attribution/)** ·
[Drive the mock](https://madpr.github.io/claude-growth-surfaces/who-is-paying.html)

I kept this out of the slate for two reasons. It's a Claude Code item, and the slate is
about the API product. And its revenue runs the other way: it moves spend off metered
billing and onto a subscription the customer has already bought. What it protects is
subscription retention. Each of the four filers who put a number on their loss had an
active subscription the session never used, and what they write about is trust in a
plan they'd already paid for.

Here's the defect. Leave an `ANTHROPIC_API_KEY` in your shell for some other
application, start Claude Code while signed into a subscription, and the session
quietly bills the Console account. The diagnostic that reports which credential is
active gives the same answer in both states. I reproduced that on the current build,
wrote a proposal, and built the warning. I also found 26 public issues describing it;
the four that carry a figure add up to $1,799.83 in self-reported losses. This is the
guarantee side of the rule: a person's interactive session is never billed to an
organization without saying so.

The mock is that prototype made drivable. Export the API key most machines already
carry, start a session, and watch a subscription stop paying without saying so. Two
controls change the answer: whether the machine has a subscription, and whether the
precedence order is the one that ships or the one I proposed.

## What was ruled out

Before I designed anything, I checked what the platform already ships. I probed five
surfaces and found them built: billing and spend controls, prompt caching, API key
lifecycle, rate limits, and the Managed Agents control plane. Five candidate ideas died
with them.

I also tried embedding the platform dashboard inside claude.ai, and the platform
refused. It sets `frame-ancestors 'self'`, and its session cookies wouldn't reach a
cross-site frame in any case.

## Evidence standards

Everything in these cases comes from primary documentation, binaries I installed, and
defects I reproduced myself. No SEO citations, no deep-research numbers, and no
third-party benchmarks taken at face value. A few rules I held to throughout:

- Every issue in a corpus, I opened and read.
- The prototypes run on seeded fixtures. They read no account and make no API calls.
- Every figure in a case is printed by the prototype behind it, so a case and its code
  can't disagree. Where an input isn't public, the prototype sweeps it and the case
  reads the table.
- Where I couldn't reproduce a finding without exposing my own account, it ships as a
  script that prints the finding and none of the values.

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
