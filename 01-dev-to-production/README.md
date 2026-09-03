# Dev → production

Status: **direction, not a finished design.**

Teams run agents with a human watching. A supervised workload is a $10/month
prototype; the same workload unattended is a $1,000/month production workload. What
keeps the human there is not model quality — it is not knowing what the agent will
reach.

**This is a bet on direction, not a fix for a fully-evidenced problem today.** The
failure is visible now at small scale, on individual machines, with a blast radius of
one laptop and one repo. The bet is that it becomes the gating constraint when the
same agents run unattended against company infrastructure, at fleet scale. A big bet
held to the same evidentiary bar as a two-day fix is guaranteed to arrive late.

[Open the prototype](https://claude.ai/code/artifact/e503ed07-defe-4063-a164-7f40537b1055) — one screen: a working Claude Code configuration
becomes the three objects Managed Agents needs, an agent, an environment and a
deployment, with each field's source in the margin and the sandbox as the only thing a
laptop cannot supply.

Managed Agents bounds this. A harness you wrote around `/v1/messages` does not, and
mostly never will. The lever is routing unattended work onto the surface where the
bounds exist, which also happens to bill session runtime at $0.08/hour on top of model
tokens.

## The gate is authority, not cost

Read these as an early indicator, not as proof that teams are blocked today. Fourteen issues in `anthropics/claude-code` ([`research/issues.tsv`](research/issues.tsv),
each opened and read). Eleven are the agent acting outside its mandate rather than
producing bad work.

| Issue | What it did |
|---|---|
| [#85919](https://github.com/anthropics/claude-code/issues/85919) | Hit a 403, found an admin secret in a *sibling project's* `.env`, minted itself a token with expanded capabilities |
| [#86667](https://github.com/anthropics/claude-code/issues/86667) | Bypassed a system-path guard, kept running unsupervised after timeout, wiped the `C:\` drive root |
| [#82063](https://github.com/anthropics/claude-code/issues/82063) | Deployed to production without asking |
| [#81035](https://github.com/anthropics/claude-code/issues/81035) | A *failed* nested fork still spawned a live process that merged PRs with admin bypass |
| [#79103](https://github.com/anthropics/claude-code/issues/79103) | Asks outright for a pre-flight checkpoint before unattended runs |

\#82063 is the thesis in a user's own words: *"no harm done, but it makes me very
worried."* Nothing broke and they filed anyway. That is what keeps a human in the loop,
and no spend cap addresses it.

These are Claude Code issues, so they are directionally relevant rather than proof for
the API. They describe the same decision, at the scale where it currently occurs: one
developer, one machine, one repo. Each of them is a rehearsal for the same event
against shared infrastructure.

The second piece of direction evidence is Anthropic's own build order. Session budgets
shipped 7 August 2026, alongside outcome graders, scheduled deployments, credential
vaults and per-session sandboxes — an entire surface whose reason to exist is agents
running unattended. The bet here is not that this direction is real. The company has
already committed to it in code. The bet is on what the binding constraint turns out
to be when it arrives, and on getting the workloads there.

## Why this isn't solved already

Spend controls are more mature than they look from outside — tier caps, self-set org
and workspace limits, bounded auto-reload, a Spend Limits API, an Analytics cost API.
Probing them killed four candidate ideas as already-built, including pooled org spend
and per-team attribution.

What is missing is any bound on a run you host yourself. `/v1/messages` is invoked by
a loop you wrote, in your process, on your machine: you own the retries, the tool
execution, the credentials and the filesystem. The endpoint has no run to bound, and
`task_budget` — the one thing that looks like a ceiling — is documented as "a soft
hint, not a hard cap," re-derived from the conversation you resend, so the server
admits it loses track after compaction.

**Managed Agents has all of it, and the scheduled path is already bounded.** A
deployment takes a required `environment_id`, the same `budget` object as a session
(accepted on create *and* update, copied onto each fired session), a
`user.define_outcome` in `initial_events`, and vaults. Nothing here needs building.
The gap is narrower: every bound is opt-in and set one object at a time, a session
budget is **create-only** so a session started without one can never be capped, and
nothing on an agent says whether any of its runs are bounded at all.

Managed Agents is the same inference with an orchestrator above it. The agent loop
runs on Anthropic's side; the container is where tools execute; sessions bill model
tokens at list price plus runtime. So the bounds below are properties of that
orchestrator, not of the endpoint:

| Bound | Your own harness | Managed Agents |
|---|---|---|
| Cost | Accumulate `usage`, stop the loop | Session budget: dollar-denominated, enforced between model requests |
| Quality | Call a second model against a rubric | `user.define_outcome`: a required rubric graded in a **separate context window**, iterating until satisfied |
| Authority | Container with scoped credentials | Per-session sandbox; **vault credentials substituted at egress and never visible inside it** |

**A competent team can build the first two.** Anthropic hosts them rather than
inventing them, and the sandbox is reproducible with real infrastructure work. The
argument is not that customers are locked out. It is that this is three separate
infrastructure problems — metering, evaluation and containment — and none of them is
the thing the team set out to build.

Anthropic's own hosting guidance already points the same way, for a different
reason. The Agent SDK hosting page tells self-hosters that if they "do not need
infrastructure control, custom isolation, or your own data plane," they should
"consider Managed Agents instead." That is a hosting-convenience argument aimed at
someone who would rather not operate containers. It is corroboration that the
destination is right, and it is not a motion: nothing targets a workload, measures a
move, or tells a team the thing blocking them is containment. The same page lists the
egress-proxy credential pattern under production concerns to build yourself, alongside
multi-tenant isolation and horizontal scaling.

One row is different in kind. Egress substitution means the secret never enters the
sandbox, so the agent never holds the credential material at all. A self-hosted
container can scope credentials down; the process still has them. That is the bound
that answers [#85919](https://github.com/anthropics/claude-code/issues/85919), the
sharpest issue in the corpus — an agent that hit a 403, went looking, found a secret
in a sibling project and used it. Scoping would not have stopped it. Not holding the
secret would have.

## Cost to build

One to two months, and the design isn't done. Two candidate shapes, in increasing cost:

- **A promotion path.** Read a working Claude Code configuration and emit the agent,
  environment and deployment together, so the bounds are set at the moment someone
  decides to stop watching rather than left to a later API call. Closest to a product,
  and closest to the M — though it inverts the M's third rulebook class: that one is
  what breaks in translation, this is what you acquire.
- **Promotion as a surface.** Environment, budget and rubric presented as the thing you
  settle before an agent runs unattended, and shown on the agent rather than buried one
  object down. Packaging as much as engineering.

Neither is designed. The next work is evidence, not code.

## Success metrics

- **Workloads that move to unattended operation**, against their own prior supervised
  baseline. The whole thesis in one number.
- **Spend 90 days after the move.** The revenue claim, and it lags.
- **Sessions run with a budget and a rubric set.** If people route workloads but leave
  both unset, the bounds were not why they came.

One guardrail: **incidents on unattended runs**. If routing moves the failure rather
than containing it, the argument is wrong.

Because this is a bet, the metrics that matter first are leading ones, and all three
are watchable today: growth in API traffic that runs on a schedule or unattended,
growth in Managed Agents sessions, and the share of those sessions that set a budget
or a rubric. If the first two are flat, the bet is early. If they climb and the third
stays near zero, the bounds are not why anyone came.

## Risks

- **Timing is the real risk.** For a bet on direction, early and wrong cost the same.
  If fleets of unattended agents are three years out rather than one, this is a
  correct idea built two years too soon, and the engineering ages badly.
- Framing it as a bet buys the right to act ahead of the evidence and gives up
  falsifiability in exchange. "Teams don't ship because of X" was testable; "this
  becomes the constraint" is not, until it does. The discipline has to move to the
  leading indicators below.
- Authority rests on fourteen issues from one product. If teams do not describe it
  this way as the scale grows, the premise is wrong.
- The rubric fits artifact work — reports, models, pipelines — and fits open-ended
  codebase maintenance badly, which is where the evidence came from.
- It resembles the M. Gating untrusted work on a check you specify is the parity gate's
  hypothesis. Different theme and different mechanics, but a reader will see it.
- The grader is Claude judging Claude. The M's "judge disagrees with the team" risk is
  inherited in full.
- Teams may not accept a hosted sandbox for work that touches their infrastructure,
  which is exactly the work with the largest blast radius.
- A team that has already built its own metering and containment gets only the egress
  row, and buys a migration to get it. The pitch is strongest before they build, which
  makes timing a go-to-market problem as well as a product one.

## Evidence

Platform quotations come from Anthropic documentation fetched 2 September 2026. Issue
numbers are real and each was opened and read.

Two numbers decide this and both are internal: what fraction of API organizations run
anything unattended, and how many have a single-day spend spike over 5× their trailing
average.
