# Cache break-even

The Console's Caching page charts write amortization &mdash; tokens read back per token
written &mdash; and captions it "higher means better cache reuse." There is an exact
number where better becomes worse, and the page never draws it.

**Draw the line.** That is the whole proposal.

[Open the prototype](https://claude.ai/code/artifact/2b514045-cf23-496e-a97f-0fd5ffbd13bc) &mdash;
a replica of Analytics › Caching with the one addition, and a switch to see the page
without it.

## The line

A 5-minute cache write bills 1.25× base input, a 1-hour write bills 2×, and a read
bills 0.1×. Write W tokens once and read them back A times: caching bills
`W(write + read·A)`, and not caching bills `W(1 + A)`, because those tokens are
processed at full rate each time they appear. Setting them equal:

```
A = (write_multiplier - 1) / (1 - read_multiplier)
```

| TTL | Break-even amortization |
|---|---|
| 5 minutes | **0.28×** |
| 1 hour | **1.11×** |

Below that, caching costs more than switching it off. The amortization chart's y-axis
starts at 0.50×, so the entire 5-minute danger zone sits below the visible range.

`breakeven_amortization()` in the prototype computes it, with invariants covering both
TTLs and the discounted read rate on Fable 5.1 and Mythos 5.1.

## What already ships

Checked against the live Console on 2 September 2026, not inferred from docs. The
page is good, and most of what an outsider would propose is already built:

- **Cache read ratio**, as a headline tile and its own chart.
- **Write amortization**, as a table column and its own chart with a 24-hour window.
- **Input token composition** over time, split into read, write (5m), write (1h), and
  uncached.
- **A Cache diagnostics panel**, with an empty state inviting you to enable it.
- Filters for workspace, model, and range; hourly refresh.

Probing the obvious surface and finding it well-built is a finding, and it cut this
idea down twice. An earlier draft proposed building detection and diagnosis from
scratch. Both exist.

## What is missing

| Gap | Consequence |
|---|---|
| **No threshold on write amortization** | The page shows the metric and never says where it turns negative. "Higher is better" is true and useless at 0.02× |
| No dollars | Everything is tokens and ratios. Cost lives on a different page, so the surcharge is never named as money |
| Group by is model or workspace only | The Usage Report API supports `api_key_id`. You can see that something is wrong, not which key is doing it |

The first one is the idea. The other two are what make it actionable.

## The change

On the write amortization chart: extend the axis below 0.50×, draw the break-even at
0.28×, shade beneath it, and label it. In the breakdown table: a status against that
line rather than a bare multiple. When a model or workspace sits below break-even for
a sustained window, name the surcharge in dollars.

Two to three days. It is a threshold, an axis change, and a subtraction of two numbers
already on the page.

## Evidence

Sixteen public reports in [`research/issues.tsv`](research/issues.tsv), each opened and
read. Six are prefixes that broke, three never engaged caching at all, four are
downstream accounting, and three are not the Claude API. The sharpest:

| Report | Measured |
|---|---|
| [openclaw#19534](https://github.com/openclaw/openclaw/issues/19534) | 170,602 tokens rewritten every request, reads at 0. "$35 today instead of expected $9." A timestamp in the system prompt |
| [signalbox#611](https://github.com/KeenWill/signalbox/issues/611) | 98 calls, ~7.1M input tokens, 0 cache reads. "~$22; with standard prompt caching… a few dollars" |
| [bifrost#6591](https://github.com/maximhq/bifrost/issues/6591) | Non-deterministic tool serialization: 1 hit in 5 through the proxy against 5 in 5 direct. The third regression of the same bug |

Every one of these workloads had an amortization the platform could see. None of them
were told what it meant.

Two limits. Most authors run harnesses, IDE extensions, and proxies rather than direct
API integrations, which gives them the standing the Claude Code issues have in `01`:
directionally relevant, not proof. And the figures are rates at different scales, so
they are not summed into a headline number.

## Success metrics

| Metric | Target |
|---|---|
| Workspaces below break-even on material volume | Primary. Sizes the problem, and one query answers it |
| Share that cross above break-even within 30 days of first seeing the line | Above 50% |
| False positives &mdash; workloads correctly not caching, or under the minimum cacheable prefix | Under 5% |

Measure the first before building. If the population is small this was a support
problem, not a product one.

## Risks

| Risk | What kills it |
|---|---|
| The population is small | The corpus is loud rather than large |
| A line is not enough | People see it, understand it, and still do not act &mdash; the cause is in a vendored dependency for a third of the corpus |
| It is a docs problem | If the same three mistakes cause most of it, a better troubleshooting page costs a day |
| Revenue runs the wrong way | Fixing this lowers the customer's bill. The brief permits indirect impact, and this is the same trade `bonus-billing-attribution` makes: protect trust, lose a little metered spend. Said plainly rather than dressed up |

An earlier draft proposed selling managed breakpoint placement as a paid tier. It does
not survive seeing the page: the observation layer is already strong, so "buy a better
dashboard" has nothing to sell, and charging to fix a surcharge reads badly. If a paid
product belongs anywhere here it is placement that measures its own hit rate and
adapts, which is a separate idea and a much larger one.

## Run the prototype

```
cd prototype
python3 cache_lint.py detect  fixtures/usage-report.json
python3 cache_lint.py explain fixtures/payload-log.json
python3 test_cache_lint.py
```

| Path | Contents |
|---|---|
| `prototype/cache_lint.py` | `breakeven_amortization()` for the line; `detect` prices the surcharge from a usage report; `explain` locates the invalidator in a payload log |
| `prototype/test_cache_lint.py` | 52 invariants |
| `prototype/fixtures/` | A usage report with one surcharged key, one healthy, one under the cacheable floor, one that never caches; a six-request payload log seeding one failure of each class |
| `page/managed-caching.html` | The page replica and the proposed addition |
| `research/issues.tsv` | The corpus, 16 rows |
| `research/deep-research-triage.md` | The nine ideas this came from, and what happened to the other eight |

`explain` classifies into the same union the cache diagnostics beta returns, and reports
`unavailable` rather than guessing when a local diff cannot see the cause. Promising a
diagnosis the data cannot support would reproduce the defect this is about.

## Sources

Pricing multipliers are quoted from the prompt caching documentation, fetched
2 September 2026. The Caching page inventory comes from the live Console on the same
date. Issue numbers are real and each was opened and read.

One question decides whether this is worth building, and it is inside Anthropic: **how
many workspaces sit below break-even on material volume, and what do they spend?**
