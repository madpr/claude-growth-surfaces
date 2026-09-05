# Claude API — growth surfaces

This is a set of three product ideas for growing Claude API revenue, one small, one
medium, one big. Each one takes a step a customer does by hand today, somewhere between two
Anthropic products, and removes it.

The small one puts the developer platform in claude.ai's left rail, where a subscriber
who wants to build will actually see it. The medium one gives a team moving code off
the OpenAI SDK a merge gate that proves the migration is safe. The big one takes a Claude
Code project that ought to be running unattended and promotes it to a hosted agent,
with the limits set before the first run.

**North star:** increase Claude API revenue · **Sizing:** one tactical, one medium, one
big bet · **Evidence:** primary sources; every demo runs on a seeded scenario and reads no account

## Principle

> Two kinds of work: (1) subscription, where it's one person's and runs interactively;
> (2) platform, where it runs unattended against infrastructure the team owns and bills
> an organization rather than a person.

## Goals

- Grow Claude API revenue by removing a manual step between two products.

## The slate

| | Idea | Demo | Theme | Engineering cost | Status |
|---|---|---|---|---|---|
| **S** | [Developer platform entry point](03-platform-entry/) | [Open the mock](https://madpr.github.io/claude-growth-surfaces/platform-entry.html) | Activation | 2 to 3 days | Designed |
| **M** | [OpenAI → Claude migration](02-openai-migration/) | [Terminal demo](https://madpr.github.io/claude-growth-surfaces/migrate.html) | Acquisition | About 2 weeks | Designed |
| **L** | [Dev → production](01-dev-to-production/) | [Terminal demo](https://madpr.github.io/claude-growth-surfaces/promote-cli.html) · [Browser demo](https://madpr.github.io/claude-growth-surfaces/promote-to-agent.html) | Expansion | 1 to 2 months | Case written, two drivable demos |

### Bonus

**[Billing attribution](bonus-billing-attribution/)** ·
[Drive the mock](https://madpr.github.io/claude-growth-surfaces/who-is-paying.html)

## Repo layout

```
<nn>-<slug>/       the three ideas, S is 03
bonus-<slug>/      supporting work, outside the slate
  README.md        the written case
  page/            source for the published page
  research/        collected evidence, raw
```

The published site is <https://madpr.github.io/claude-growth-surfaces/>.