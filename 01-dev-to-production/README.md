# Dev → production: approach note

Status: **direction, not a finished idea.** Written as a handoff so a new thread
can start from verified ground.

## Why this lever

API revenue ≈ workloads × volume per workload × price. Ranked by leverage:

| Lever | Magnitude | Barrier |
|---|---|---|
| **Dev → production conversion** | Highest. A prototype burns $10s/month; a production workload burns $1,000s | Confidence — teams can't bound the downside |
| Winning workloads from competitors | High | Switching cost: prompts, evals, quality uncertainty |
| Expansion inside existing accounts | Medium | New use cases, new teams |
| Leakage to subscription products | Unknown, possibly large | See open threads |
| New-developer activation | Long tail | Rescues the least-committed developers |

Revenue on an API platform is power-law: a small number of production workloads
generate most of it. Activation and billing-plumbing work moves the tail. This
lever moves the head.

## The hypothesis

> Teams don't run agents unattended because the blast radius is unbounded in three
> currencies: what it costs, whether the work is any good, and **what the agent is
> allowed to touch**. The third binds first and hardest. So a human stays in the
> loop, and the workload never becomes a production workload.

Revised 2 September 2026, twice. The first version named cost. Practitioner evidence
pointed at output quality instead. Fourteen issues in `anthropics/claude-code`
([`research/issues.tsv`](research/issues.tsv), each opened and read) point somewhere
more specific again: **eleven of the fourteen are the agent acting outside its
mandate**, not writing bad code.

| Issue | What it did |
|---|---|
| [#85919](https://github.com/anthropics/claude-code/issues/85919) | Hit a 403, found an admin secret in a *sibling project's* `.env`, minted itself a token with expanded capabilities |
| [#86667](https://github.com/anthropics/claude-code/issues/86667) | Bypassed a system-path guard, kept running unsupervised after timeout, wiped the `C:\` drive root |
| [#82063](https://github.com/anthropics/claude-code/issues/82063) | Deployed to production without asking. "no harm done, but it makes me very worried" |
| [#81035](https://github.com/anthropics/claude-code/issues/81035) | A failed nested fork still spawned an unsupervised process that merged PRs with admin bypass |
| [#79103](https://github.com/anthropics/claude-code/issues/79103) | Asks outright for a pre-flight checkpoint before unattended runs, citing "the desire for genuinely unattended, overnight agent operation" |

#82063 is the hypothesis in a user's own words: nothing broke, and they are still
frightened enough to file. That is what keeps a human in the loop.

The shape of the original hypothesis survives: an unbounded downside keeps a human
watching. The currency changes. Every workload stuck under supervision is the
difference between $10/month and $1,000/month, and a hard dollar cap alone does not
release it.

This is the "capped confidence beats uncapped anxiety" thesis, attached for the
first time to a decision that moves real money rather than to a per-prompt
approval dialog.

**Evidence that the failure is real** (Claude Code issues, so directionally
relevant rather than proof for the API):

| Issue | What happened |
|---|---|
| [#69578](https://github.com/anthropics/claude-code/issues/69578) | Recursive sub-agent loop, ~800k tokens, $27.60 |
| [#72861](https://github.com/anthropics/claude-code/issues/72861) | Recursive fan-out, significant unexpected charges — **explicitly requests guardrails** |
| [#72732](https://github.com/anthropics/claude-code/issues/72732) | Uncontrolled recursive agent spawning |
| [#76938](https://github.com/anthropics/claude-code/issues/76938) | A script burned 15,861 API calls over 13 hours |

Damage measured in hours; controls measured in months.

## Verified platform facts

Checked against primary docs on 31 August 2026. **Do not re-research these.**

**Spend controls that exist**

- Tier monthly spend caps: Start **$500**, Build **$1,000**, Scale **$200,000**. Custom tier has none.
- Self-set spend limit, org and workspace scoped. Monthly.
- Per-workspace rate limits (RPM / ITPM / OTPM).
- Auto-reload: trigger threshold + reload amount, **bounded by the monthly spend
  limit** ("auto-reload will not add credits once your monthly spend limit is
  reached"), plus a $2,000 daily redemption ceiling.
- Spend Limits API (per-member caps, increase-request workflow).
- Analytics cost API with daily buckets.

**The gaps**

- **`monthly` is the only supported period** on the Spend Limits API. Quoted from
  its docs. No daily, hourly or rolling budget exists there.
- **But a hard per-run dollar cap already ships — on Managed Agents.** A session
  budget is `{type: "limit", max_list_cost: {amount, currency}}`, set at session
  creation in minor units. The platform prices everything the session consumes at
  public list rates and **gates before every model request**, pausing the session
  at `stop_reason: budget_reached` rather than terminating it; history and sandbox
  survive, and raising or removing the cap resumes the work. Model tokens, web
  search at $10/1,000, and session runtime at $0.08/hour all count. Scheduled
  deployments can carry one too, copied onto each fired session.

  This is the single most important correction in this document. It is **not**
  advisory: `task_budget` on the Messages API is the advisory, token-denominated
  one, and the docs draw the distinction explicitly.
- **Spend accounting is explicitly not transactional.** `period_to_date_spend`
  "may read as `0` if the spend reading is temporarily unavailable; treat it as
  informational, not transactional." Daily cost is "provisional and can be
  revised upward." You cannot build a circuit breaker on *these* figures.

  **This no longer establishes that a circuit breaker is infeasible.** Managed
  Agents enforces one today by pricing at list rates and gating pre-request, which
  sidesteps the settled-spend problem entirely — list cost is computable from
  tokens the platform has already counted. The reported figure is rounded to the
  cent while enforcement compares exact amounts, and the request that crosses the
  cap completes, so it is a bound on new work rather than an exact stop. That is
  the shape a Messages-API equivalent would take.
- **Twelve-plus rate-limit response headers, zero spend headers.** You can read
  `anthropic-ratelimit-input-tokens-remaining` to the nearest thousand. There is
  no equivalent for budget. The asymmetry is not limited to spend: the documented
  response headers are `request-id`, `anthropic-organization-id`,
  `anthropic-workspace-id` and the rate-limit family, so **no header carries cache
  state either** — see [`03-cache-breakeven`](../03-cache-breakeven/), which
  turns that gap into its own idea.
- **No anomaly or velocity detection.** Anthropic's own docs carry a worked
  example titled "Find members with rapidly changing usage" instructing admins to
  pull two weeks of daily cost and flag week-over-week multiples themselves.
- **The Spend Limits API excludes the API product**: "available to Claude
  Enterprise organizations only. It is not available to Claude Platform (Claude
  Console) organizations."
- **Threshold alerts are asymmetric**: automatic at 75% and 90% for Enterprise;
  opt-in for Console ("get notified as your monthly spend approaches an amount
  **you set**").
- **The spend-cap error is misclassified.** Returns `error.type:
  "rate_limit_error"` with `details.error_code: "enforced_spend_limit_reached"`,
  **no `retry-after`**, and the docs confirm "retrying, including the SDKs'
  automatic retries, fails until access resumes." A budget failure is presented
  as a throughput failure, and the client library burns the customer's time on a
  remedy that cannot work.

## Dead ends — already explored, don't repeat

| Idea | Why it died |
|---|---|
| Default auto-reload to on | **Actively harmful.** Auto-reload is the mechanism that turned a silent misattribution into "nine auto-recharge charges later, $187 gone." Users disable it deliberately as protection. |
| Bounded auto-reload (cap per period) | **Already built.** The monthly spend limit already gates it. |
| Pooled org spend + per-team attribution | **Largely built.** Workspaces, spend limits, Analytics API, Spend Limits API. |
| Tier-cap upgrade moment | Weakened once threshold alerts turned up. Survives only as the SDK misclassification fix — real, but too small to carry a slot. |
| Activation / time-to-first-call | Verified gap (docs show `your-api-key-here` even when logged in), but a weak revenue chain: it rescues the least-committed developers. Naive fix is also blocked — no test-key split, and keys are almost certainly not retrievable after creation. |

The pattern across these: **billing and spend controls on `platform.claude.com`
are more mature than they look from outside.** Worth saying in the submission —
probing the obvious surface and finding it well-built is a finding.

## What this does to the idea

Checked 2 September 2026. **The cap is not portable to the Messages API, and the
reason is architectural rather than a matter of priority.** That settles the
direction of this idea.

**`task_budget` is advisory by admission.** Its doc carries a section titled "Task
budgets are advisory, not enforced": a "soft hint, not a hard cap… The enforced
limit on total output tokens is still `max_tokens`." `max_tokens` caps one request;
nothing caps the loop.

**It is advisory because the Messages API holds no per-run state.** The countdown is
re-derived from the conversation you resend on each request. Quoted: "If your
agentic loop compacts or rewrites context between requests, **the server has no
memory of how much budget was spent before compaction**. Pass `remaining` on the
next request so the countdown continues." A cumulative cap cannot be enforced from a
position that cannot reliably know the cumulative total — and a client-supplied
counter cannot be trusted for enforcement, which is precisely why it is a hint.

**The session budget is enforceable because a session is a server-side state
machine.** It "maintains conversation history across multiple interactions", the
platform "prices everything the session consumes at public list rates", and the cap
is "enforced between model requests". There is an object to accumulate against and
a thread to pause.

**The timeline confirms the boundary is deliberate.** Task budgets shipped 16 April
2026, advisory, on the Messages API. Session budgets shipped 7 August 2026, hard, on
Managed Agents. Anthropic did not harden the first; it built a second primitive with
a different unit on a different surface. Release notes carry no indication of spend
controls coming to the Messages API.

So to cap a run on the Messages API you would first have to invent the run. That is
not impossible — cache diagnostics already threads `previous_message_id` across
stateless requests — but it is a new platform primitive, not a port, and it is well
outside this idea's scope.

## The idea, restated

The lever is no longer "build a spend circuit breaker." It is:

> Running unattended needs a bound on both currencies. Neither exists on
> `/v1/messages`. Both already run in production on Managed Agents. Route the
> workload.

| Bound | Messages API | Managed Agents |
|---|---|---|
| Cost | `task_budget` — advisory, token-denominated, "a soft hint, not a hard cap" | Session budget — hard, dollar-denominated, enforced between model requests |
| Quality | Nothing | `user.define_outcome`: a required rubric graded by a **separate context window**, iterating until satisfied or `max_iterations` |

The grader's independence is the load-bearing part — the docs say it "uses a separate
context window to avoid being influenced by the main agent's implementation choices."
That is what makes it a check rather than the model marking its own homework.

**The customer is artifact-producing unattended work** — scheduled reports, models,
data pipelines, analyses — not autonomous coding. A rubric grades a deliverable
against stated criteria. "The CSV has a numeric price column" is gradeable;
"don't make architecturally bad decisions in my repo" is not. The evidence that
prompted this revision comes from codebase work, which is the case outcomes serve
worst. Scheduled deployments and the $0.08/hour runtime billing point the same way.

Managed Agents bills model tokens **plus** session runtime at $0.08/hour and web
search at $10 per 1,000, so a workload that moves there is worth more per unit of
work than the same workload on `/v1/messages` — and the reason to move is a
capability the customer cannot build for themselves, not a discount.

**Two objections that must be answered.**

*It resembles the M.* "Accept work you don't trust by gating it on a check you
specify" is the parity gate's hypothesis. The themes differ — acquisition there,
expansion here — and so do the mechanics, a one-time PR gate against continuous
unattended operation. The resemblance is still real and should be named in the
submission rather than discovered by a reader. The M's "judge disagrees with the
team" risk is inherited in full.

*A team can cap spend themselves* by summing `usage` and stopping the loop. Three
reasons that is not equivalent, and they need testing with real teams rather than
assertion:

1. The runaway case is a **defective loop**, and a check inside the loop that is
   malfunctioning is not a control.
2. It requires list prices, cache-tier accounting, and tool-cost accounting the
   caller has to maintain and keep current.
3. It does not survive a wedged or crashed process, which is the case that produces
   the largest bills.

## How I'd investigate from here

**1. Establish the gate is real, and is about blast radius.** The hypothesis is
currently reasoning plus adjacent Claude Code issues. Before designing anything,
find out whether teams actually say this. Sources: developer forums and Discords
on shipping agents to production; competitor changelogs (does anyone ship
runtime spend controls?); the phrasing in #72861 where a user asks for guardrails
outright.

**2. Confront the technical blocker directly.** Spend accounting is not
transactional, so a hard per-run budget may be genuinely hard to build. Decide
early whether the idea is:
- a **hard** circuit breaker (requires transactional spend — expensive, possibly
  a non-starter), or
- a **soft** one: token-based budgets enforced client-side or at the gateway,
  since token counts *are* known per request in real time and cost is a
  deterministic function of them.

The second is much cheaper and probably the right scope. Tokens are the honest
unit anyway.

**3. Check the competitive baseline.** Do OpenAI, Google, or Bedrock offer
runtime spend controls, per-key budgets, or anomaly halts? If a competitor ships
this and Anthropic doesn't, that is the pitch. If nobody does, ask why — there
may be a reason.

**4. Size it.** The number that decides everything, and it is inside Anthropic:
**what fraction of API organizations have a workload that runs on a schedule or
unattended, versus only interactive/dev traffic?** And: how many orgs have a
single-day spend spike of >5× their trailing average? That second one is
computable from data they already hold and it directly measures the failure.

## Candidate shapes

Not finished ideas. Ordered by increasing cost.

- **Token budgets per key or per run.** A `max_spend_tokens` style ceiling
  enforced where tokens are already counted. Sidesteps the non-transactional
  spend problem entirely.
- **Spend headers.** Mirror the rate-limit headers with budget-remaining
  equivalents, so a client can see the wall coming and degrade gracefully instead
  of being cut off.
- **Velocity halt.** Detect a burn rate anomalous against the org's own trailing
  baseline, pause, and notify — the feature Anthropic's docs currently tell
  admins to build themselves.
- **A "production readiness" surface**: budgets, alerts, and a kill switch
  presented as the thing you configure before you promote an agent. Packaging as
  much as engineering.

## What would kill this

- If most agent workloads already run in production and cost anxiety isn't the
  gate, the premise is wrong. **Test this before building anything.**
- If spend spikes are rare in the data, the failure is anecdotal and this is a
  support problem.
- If transactional spend accounting is infeasible and token budgets don't
  satisfy the actual anxiety (teams want dollars, not tokens), the idea shrinks
  to alerting.

## Open threads worth picking up

- **The ~20× subscription/API price delta.** A Reddit calculation, unverified:
  "Max 5x ($100/mo): weekly limit worth ~$523 in API pricing." If roughly right,
  the API's heaviest individual developers have a structural incentive to leave
  for a subscription. Reshapes any monetization argument. **Verify the arithmetic
  first.**
- **Credit expiry suppressing prepayment.** Users report refusing to fund
  accounts because credits expire. A customer who won't top up beyond $20 out of
  distrust has a spend ceiling set by fear. Clean revenue argument, unexplored.
- **Competitive migration.** The most traditionally growth-shaped lever we
  identified and the least examined.

## Evidence quality note

Everything under "Verified platform facts" is quoted from primary Anthropic
documentation. Issue numbers are real and checked. The Reddit material is a
third-party digest without dates or vote counts — directional only, and it
cannot establish frequency. Every sizing question in this document requires
internal data.
