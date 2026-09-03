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

Managed Agents already bounds this. `/v1/messages` does not. The lever is routing
unattended work onto the surface where the bounds exist, which also happens to bill
session runtime at $0.08/hour on top of model tokens.

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

What is missing is any bound on a single unattended run. On `/v1/messages` there is no
grader, no sandbox, and `task_budget` is documented as "a soft hint, not a hard cap" —
advisory, token-denominated, and re-derived from the conversation you resend, so the
server admits it loses track after compaction. A cumulative cap cannot be enforced from
a position that cannot know the cumulative total.

Managed Agents bounds all three currencies, and the third structurally rather than by
asking the model nicely:

| Bound | `/v1/messages` | Managed Agents |
|---|---|---|
| Cost | `task_budget`, advisory | Session budget: dollar-denominated, enforced between model requests |
| Quality | Nothing | `user.define_outcome`: a required rubric graded in a **separate context window**, iterating until satisfied |
| Authority | Nothing | Per-session sandbox; vault credentials substituted at egress and never visible inside it |

There is no sibling project's `.env` in a sandbox and no `C:\` to wipe. #85919 and
#86667 are impossible there — not less likely, impossible.

## Cost to build

One to two months, and the design isn't done. Two candidate shapes, in increasing cost:

- **A path from a loop to an agent.** Scan an existing agentic loop, emit the agent and
  environment config, set a budget and a rubric, run it in the sandbox. Closest to a
  product, and closest to the M — which is the problem.
- **Promotion as a surface.** Budget, rubric, sandbox scope and kill switch presented as
  the thing you configure before an agent runs unattended. Packaging as much as
  engineering.

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

## Evidence

Platform quotations come from Anthropic documentation fetched 2 September 2026. Issue
numbers are real and each was opened and read.

Two numbers decide this and both are internal: what fraction of API organizations run
anything unattended, and how many have a single-day spend spike over 5× their trailing
average.
