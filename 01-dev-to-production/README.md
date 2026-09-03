# Dev → production

Status: **direction chosen, shape chosen, prototype running.** The written case is
here; the design is not finished.

Teams run agents with a human watching. A supervised workload is a $10/month
prototype; the same workload unattended is a $1,000/month production workload.
Managed Agents is where the unattended version is bounded — session budgets, outcome
rubrics, and vault credentials substituted at egress. The lever is routing work
there.

The question this item used to get wrong was *why* teams don't go. The first answer
was cost, the second was quality, the third was authority. All three were guesses
about motive. The verified answer is simpler and sits one step earlier: **most Claude
Code users never learn the destination exists, and when they do, it turns out to be a
different account.**

## Three layers

| | | Evidence |
|---|---|---|
| **Symptom** | You cannot find it. Two CLIs divide one account and collide on every word you would search | [`research/surface-collision.md`](research/surface-collision.md), reproducible via [`research/probe.sh`](research/probe.sh) |
| **Mechanism** | It is a different organization. Promotion crosses an identity boundary, not just a tooling gap | `claude auth status` vs `ant auth status`, n=1 |
| **Prize** | Flat-fee work moves onto metered infrastructure | Claude Code Pro is a subscription; Managed Agents bills tokens plus container runtime |

Authority — the old headline — is now the mechanism underneath, and it is better
evidenced there than it ever was as a thesis. See [Containment is what does not
cross](#containment-is-what-does-not-cross).

## The symptom: two CLIs, one vocabulary

`ant` (1.29.0, "CLI for the Claude Developer Platform") ships the entire Managed
Agents control plane and the platform docs recommend it over the SDK for that work.
So hosted agents are not missing from *a* CLI. They are missing from **the** CLI, and
the two surfaces collide on exactly the words a developer would try:

| Word | `claude` | `ant` |
|---|---|---|
| **agents** | "Manage **background agents**" — sessions on your laptop | a persisted, versioned hosted agent |
| **environment** | `--environment ccpool_...` self-hosted pool | `env_...` container spec |
| **session** | a local conversation, `--resume`-able | a hosted run billing container runtime |
| **budget** | `--max-budget-usd`, `--print` mode only | session budget, enforced, create-only |
| **auth** | `login \| logout \| status` | `login \| logout \| status` |

Four of five terms return a plausible *local* answer, so nothing signals a larger
surface exists — the search term is spent, not retried. `probe.sh` prints every row
from the two installed binaries: no login, no network, no account read.

Neither binary has a verb pointing at the other. `claude import` acquires config from
*competing* agents; outbound verbs number zero, and `ant` has no reference to Claude
Code anywhere in its agent, environment or deployment surface.

## The mechanism: it is a different account

Running `ant auth login` on a machine already signed into Claude Code was expected to
trigger the documented credential conflict. **It did not.** What the comparison found
instead was better:

| | organization | method |
|---|---|---|
| `claude` | org **A** | claude.ai, subscription `pro` |
| `ant` | org **B** | platform OAuth |

One email address, two organization IDs. They do not contend because they never meet.
And the platform org already contains a workspace named exactly **"Claude Code"** —
the platform models the tool as a billing destination that the tool itself is not
signed into. On that account, `ant beta:agents list` and `beta:deployments list` both
return empty: a daily Claude Code user, zero hosted agents.

**This is n=1, on a Pro subscription.** A Console/API organization may well resolve to
a single org, in which case this is a consumer-subscription-segment problem rather
than a platform-architecture one. Checking a second account is the first open task,
and it is cheap. Nothing downstream should be read as settled until it is done.

It also explains the timeline. A naming fix is two days. Reconciling a subscription
identity with a platform organization is not, and it is the honest reason this item
costs one to two months rather than a week.

## Containment is what does not cross

[`prototype/promote.py`](prototype/promote.py) is the missing verb, run locally: it
reads a Claude Code project and emits the `agent.yaml` that `ant beta:agents create`
accepts, then names every field that does not survive.

```
$ ./promote.py map fixtures/sample-project
resolved 3   lossy 3   human 1   blocked 2   underivable 1
```

An earlier draft of this case claimed "six of the seven agent fields have a local
source." That is true of fields and false of fidelity, and **the prototype falsified
it.** Only name, model and system transfer intact. Tools lose command-pattern
granularity; skills carry names but must be re-uploaded to the Skills API; MCP servers
translate only when URL-based.

Counting fields also missed two categories of working local configuration that have
**no destination field at all**:

- **Command-pattern permissions** — `Bash(rm *)`, `Write(ledger/**)`. The hosted
  toolset enables or disables a whole tool. Containment at finer grain is an
  *environment* property on the target — sandbox and vault egress — not an agent
  property, so it cannot ride along on the agent.
- **stdio MCP servers** — Managed Agents MCP servers are `type: "url"` over Streamable
  HTTP. A server Claude Code launches as a subprocess has no representation on a
  hosted agent and must be published as an endpoint first.

**The skeleton transfers; the containment does not.** That is the old authority thesis,
re-derived by a mechanical route that knew nothing about it. It is also why the
environment is *underivable* rather than merely unset: a sandbox is the one thing a
developer machine cannot hand over, and it is the reason the destination is worth
reaching.

The prototype reads a directory, makes no API calls and touches no account. Its test
suite is mostly negative — that a stdio server never reaches the emitted body, that no
command pattern leaks in, that a missing `CLAUDE.md` yields "needs a human" rather than
an empty prompt. A promoter that emits a plausible-looking agent is worse than none,
because the fields it dropped are the ones keeping the work on the laptop.

## Why the destination is worth reaching

Managed Agents is the same inference with an orchestrator above it. The bounds are
properties of that orchestrator, not of the endpoint:

| Bound | Your own harness | Managed Agents |
|---|---|---|
| Cost | Accumulate `usage`, stop the loop | Session budget: dollar-denominated, enforced between model requests |
| Quality | Call a second model against a rubric | `user.define_outcome`: a required rubric graded in a **separate context window** |
| Authority | Container with scoped credentials | Per-session sandbox; **vault credentials substituted at egress, never visible inside it** |

**A competent team can build the first two.** Anthropic hosts them rather than
inventing them. One row is different in kind: egress substitution means the secret
never enters the sandbox, so the agent never holds the credential material at all. A
self-hosted container can scope credentials down; the process still has them.

That is the bound that answers the sharpest issue in the corpus below — an agent that
hit a 403, went looking, found an admin secret in a *sibling project's* `.env` and
minted itself a token. Scoping would not have stopped it. Not holding the secret would.

## The corpus, now supporting evidence rather than the argument

Fourteen issues in `anthropics/claude-code` ([`research/issues.tsv`](research/issues.tsv),
each opened and read). Eleven are the agent acting outside its mandate rather than
producing bad work.

| Issue | What it did |
|---|---|
| [#85919](https://github.com/anthropics/claude-code/issues/85919) | Hit a 403, found an admin secret in a *sibling project's* `.env`, minted itself a token with expanded capabilities |
| [#86667](https://github.com/anthropics/claude-code/issues/86667) | Bypassed a system-path guard, kept running unsupervised after timeout, wiped the `C:\` drive root |
| [#82063](https://github.com/anthropics/claude-code/issues/82063) | Deployed to production without asking |
| [#81035](https://github.com/anthropics/claude-code/issues/81035) | A *failed* nested fork still spawned a live process that merged PRs with admin bypass |
| [#79103](https://github.com/anthropics/claude-code/issues/79103) | Asks outright for a pre-flight checkpoint before unattended runs |

\#82063 is the point in a user's own words: *"no harm done, but it makes me very
worried."* Nothing broke and they filed anyway.

These are Claude Code issues, so they are directionally relevant rather than proof for
the API. Their job in this case has changed: they no longer carry the argument on
their own — `probe.sh` and `promote.py` do that, and reproduce anywhere — but they
show what the missing containment costs at the scale where it currently happens.

## Competitive pressure: the off-ramp shipped first

[`antigravity-for-claude-code`](https://github.com/yuting0624/antigravity-for-claude-code)
is a Claude Code plugin, 303 stars, MIT, unaffiliated. It routes token-heavy work out
of Claude Code to Gemini via Google's `agy` CLI. A **SessionStart hook auto-injects a
cost-aware routing policy**, so once installed the offloading is the default rather
than a deliberate act.

Its existence establishes the asymmetry this item is about. Routing Claude Code →
Gemini needs no identity reconciliation: different vendor, separate auth, nobody
expects one account. Routing Claude Code → Managed Agents needs it *precisely because
it is the same company*. Anthropic is penalised for owning both ends — the
competitor's off-ramp is architecturally cheaper to build than Anthropic's own
on-ramp, which is why it shipped first, from a stranger.

**Its benchmark is not cited here.** The −27% / −64% figures rest on n=1, a three-case
quality eval, Gemini-side cost estimated from character-count approximations, and
rates in a user-editable `prices.json` the author explicitly says to replace before
quoting. The citable fact is that the plugin exists and what it claims — not the
magnitude. 303 stars is a demand signal, not a measurement.

It also names a failure mode the rest of the slate does not cover: **within-session
spend routing.** The customer never churns. Seat, org and subscription persist; only
per-session token volume falls. Account-level retention dashboards read that as healthy.

## Why this isn't solved already

Spend controls are more mature than they look from outside — tier caps, self-set org
and workspace limits, bounded auto-reload, a Spend Limits API, an Analytics cost API.
Probing them killed four candidate ideas as already-built. Probing the `ant` CLI
killed a fifth: "hosted agents are not available from the command line" is false.

**Managed Agents has the bounds, and the scheduled path is already bounded.** A
deployment takes a required `environment_id`, the same `budget` object as a session,
a `user.define_outcome`, and vaults. Nothing there needs building. The gaps are
narrower: every bound is opt-in and set one object at a time, a session budget is
**create-only** so a session started without one can never be capped, and nothing on
an agent says whether any of its runs are bounded at all.

Anthropic's own hosting guidance points the same way for a different reason — the
Agent SDK hosting page tells self-hosters who don't need infrastructure control to
"consider Managed Agents instead." That is a hosting-convenience argument, and it is
corroboration that the destination is right. It is not a motion: nothing targets a
workload, measures a move, or routes anyone there.

## Cost to build

One to two months. Two shapes were open; the field mapping chose the first.

- **The promotion path** — read a working Claude Code configuration and emit the
  agent, environment and deployment together, so the bounds are set at the moment
  someone decides to stop watching. `prototype/promote.py` is the agent third of this,
  and it exists.
- The remaining work is not the mapping. It is the identity boundary, the environment
  (which the mapping cannot derive), and the surfacing — a developer has to learn the
  destination exists from inside `claude`.

## Success metrics

- **Workloads that move to unattended operation**, against their own prior supervised
  baseline. The thesis in one number.
- **Spend 90 days after the move.** The revenue claim, and it lags.
- **Sessions run with a budget and a rubric set.** If people route workloads but leave
  both unset, the bounds were not why they came.

Guardrail: **incidents on unattended runs**. If routing moves the failure rather than
containing it, the argument is wrong.

The falsifier is clean, and it is cheaper than the build: **ship the pointer first.**
Disambiguate `claude agents`, name the hosted destination, and watch hosted-agent
creation. If it does not move, discovery was never the gate.

## Risks

- **The identity finding is n=1, on a Pro subscription.** If Console orgs resolve to
  one org, the mechanism section is about a segment, not the platform. This is the
  first thing to check and it invalidates a load-bearing claim if it goes the other way.
- **"Identity reconciliation is hard" is inferred, not verified.** It may already be
  solvable with existing org-linking, or it may be deliberate — subscription and
  metered are different business models with different terms. If deliberate, unifying
  them is a policy argument, not a growth feature.
- **Timing.** For a bet on direction, early and wrong cost the same. If fleets of
  unattended agents are three years out, this is correct and built two years too soon.
- The rubric fits artifact work — reports, models, pipelines — and fits open-ended
  codebase maintenance badly, which is where the corpus came from.
- It resembles the M. Gating untrusted work on a check you specify is the parity gate's
  hypothesis. Different theme and different mechanics, but a reader will see it.
- The grader is Claude judging Claude. The M's "judge disagrees with the team" risk is
  inherited in full.
- Teams may not accept a hosted sandbox for work that touches their infrastructure —
  exactly the work with the largest blast radius.
- A team that has already built its own metering and containment gets only the egress
  row, and buys a migration to get it.

## Evidence

Platform quotations come from Anthropic documentation fetched 2 September 2026.
Binary behaviour was captured 2–3 September 2026 from Claude Code 2.1.259 and `ant`
1.29.0 and reproduces via `research/probe.sh`. Issue numbers are real and each was
opened and read. Every figure in [Containment is what does not
cross](#containment-is-what-does-not-cross) is printed by `prototype/promote.py`, so
this page and the code cannot disagree.

Four numbers decide this and all are internal:

- what fraction of API organizations run anything unattended;
- how many have a single-day spend spike over 5× their trailing average;
- what share of Claude Code users have ever created a Managed Agent, and what share of
  Managed Agents were created by someone who already had Claude Code installed;
- what share of Claude Code sessions delegate work to a non-Anthropic model.
