# Two surfaces, one vocabulary

Probed 2 September 2026 against both binaries on macOS: Claude Code `2.1.259` and
`ant` `1.29.0`. Reproduce with [`probe.sh`](probe.sh) — it reads no account, makes no
API calls, and requires no login.

## The idea that did not survive first contact

The starting claim was "hosting autonomous agents is not available through the CLI."
It is. `ant` describes itself as **"CLI for the Claude Developer Platform"** and
exposes the entire Managed Agents control plane as first-class commands:

```
beta:agents        create  retrieve  update  list  archive
beta:environments  create  retrieve  update  list  archive
beta:deployments   create  retrieve  update  list  archive  pause  unpause  run
beta:sessions      + :events  :resources  :threads
beta:vaults        beta:memory-stores  beta:skills  beta:organization  …
```

Fifty-plus resources. The platform documentation does not merely permit this flow, it
**recommends** it over the SDK for control-plane work:

> the CLI owns the control plane (creating and updating agents), your code owns the
> data plane.

So "build a CLI" is already built. This is the fifth surface probed and found mature,
after billing, caching, key lifecycle and rate limits. What survives is narrower and,
unlike a missing feature, is visible from outside: there are **two** CLIs, they divide
one account, and they collide on the exact words a user would search.

**`ant` was not installed on the machine of a daily Claude Code user, and
`~/.config/anthropic` did not exist.** That is the finding, observed rather than argued.

## The collision table

Every row is printed by `probe.sh` from the installed binaries.

| Word | In Claude Code (`claude`) | On the platform (`ant`) |
|---|---|---|
| **agents** | `claude agents` — "Manage **background agents**": local sessions on your laptop, opened with `claude attach` | `beta:agents create` — a persisted, versioned, hosted agent |
| **environment** | `--environment <id>` — "self-hosted environment (`ccpool_...`)" for a cloud session | `env_...` — the Managed Agents container spec |
| **session** | a local conversation, resumable with `--resume` | a hosted run billing runtime on top of model tokens |
| **budget** | `--max-budget-usd` — API-call ceiling, **`--print` mode only** | session budget — dollar-denominated, enforced between model requests, **create-only** |
| **auth** | `login \| logout \| status` | `login \| logout \| status` |

The last row is the sharpest, and testing it produced something other than what was
predicted.

### The predicted conflict did not reproduce

The documentation warns:

> **The #1 auth trap:** … The same shadowing applies in reverse to Claude Code: after
> `ant auth login`, Claude Code may warn about an auth conflict between the profile
> and its own `/login` credential — keep one.

`ant auth login` was run on 3 September 2026 on a machine already logged into Claude
Code. **No conflict warning appeared**, from either binary. The login completed
cleanly and Claude Code continued working. Recorded as a failed prediction, not a
finding.

### What the test found instead: one person, two organizations

Comparing the two authenticated states afterwards:

| | organization | name it reports | method |
|---|---|---|---|
| `ant auth status` | org **A** | "&lt;account&gt;'s Individual Org" | platform OAuth, scopes `user:developer user:inference user:profile` |
| `claude auth status` | org **B** | "&lt;account&gt;'s Organization" | `claude.ai`, subscription `pro` |

Identifiers are redacted throughout; what matters is that A ≠ B, and both were
reported for one signed-in account. Same email address, **two different organization
IDs.** Claude Code authenticates through claude.ai against a subscription; `ant`
authenticates through the developer platform against a separate org.

Reproduce it on your own account with `probe.sh --identity`, which prints whether the
two agree without printing either value.

The two do not conflict because they never meet. They are not two credentials
competing for one account — they are two accounts.

And the platform org contains a workspace named, exactly, **`"Claude Code"`**,
selected as the login default. The platform already models Claude Code as a
first-class billing destination. The Claude Code CLI is not authenticated to it.

### The anecdote, made an account-level fact

```
$ ant beta:agents list          # (exit 0, empty)
$ ant beta:deployments list     # (exit 0, empty)
```

A developer who uses Claude Code every day has **zero hosted agents and zero
deployments**, on an account whose platform org already carries a workspace named
after the tool they use.

### What this costs the idea

This complicates the promotion path rather than supporting it. The six-of-seven field
mapping still holds for the *content* of an agent, but the *destination* is not the
org the user is logged into. A `claude`→hosted-agent path crosses an identity
boundary, not just a binary boundary. That is real work, and it is work the field
mapping does not cover.

**Limit: n = 1, and on a Pro subscription.** The claude.ai-subscription org versus
platform org split may be specific to consumer-subscription users; an organization on
a Console/API plan may well resolve to a single org. This must be checked on a second
account before any claim generalizes.

## Discovery is blocked at exactly the words a user would try

`claude agents` is the command an avid Claude Code user types to learn whether Claude
Code can run agents for them. It answers, authoritatively, with local background
sessions. The hosted product is not mentioned, and the term is now spent — having been
answered once, it does not get typed again.

`environment` resolves to a `ccpool_` pool. `session` and `budget` resolve to local
equivalents with different semantics. Four of five terms return a *plausible local
answer*, so nothing signals a second, larger surface exists. This is not an absent
feature. It is a **namespace that shadows the thing it should point to.**

## Neither direction exists

```
  import [options] [source]   Import config from another AI coding agent into Claude Code
  outbound commands in claude: 0

  beta:agents create          0 references to Claude Code
  beta:environments create    0 references to Claude Code
  beta:deployments create     0 references to Claude Code
```

Claude Code ships an `import` that acquires configuration **from competitors** and
nothing that moves configuration **outward**. `ant` cannot read a Claude Code
configuration either. The verb that would route a working local setup onto hosted
infrastructure — where budgets, rubrics and vaults live — exists in neither binary,
in neither direction.

There is already a thread between the surfaces: `claude --cloud` creates a hosted
session and `--environment ccpool_...` runs it on self-hosted infrastructure. The
machinery for "run this somewhere other than my laptop" is shipping in the CLI. It
terminates in Claude Code's own cloud, not on the agent platform.

## Why the bridge is cheap: the fields already exist

`ant beta:agents create` takes seven meaningful fields. Six have a direct source in a
working Claude Code configuration:

| `ant beta:agents create` | Already present locally |
|---|---|
| `--model` | `--model` / the `model` setting |
| `--system` | `CLAUDE.md`, `--system-prompt`, `--append-system-prompt` |
| `--tool` | `--tools` (the built-in set) |
| `--skill` | skills (`/skill-name`, `.claude/skills`) |
| `--mcp-server` | `.mcp.json` / `--mcp-config` |
| `--name` | `--name`, or the repo name |
| `--description` | *no local source — human-supplied* |

### The mapping, counted

Working the mapping through against an example project gives a less flattering
count than the table above, and it is the number to quote:

```
resolved 3   lossy 3   human 1   blocked 2   underivable 1
```

Six fields do have a local source. Only **three survive intact** — name, model and
system. Three more map with loss: tools drop command-pattern granularity, skills
carry names but must be re-uploaded to the Skills API, and MCP servers translate only
when they are URL-based.

More importantly, counting *fields* undercounted the problem, because two categories
of working local configuration have no destination field at all:

- **Command-pattern permissions** (`Bash(rm *)`, `Write(ledger/**)`). The hosted
  toolset enables or disables a whole tool. Containment at finer grain is an
  environment property on the target — sandbox and vault egress — not an agent
  property, so it cannot ride along on the agent.
- **stdio MCP servers.** Managed Agents MCP servers are `type: "url"` over Streamable
  HTTP. A server Claude Code launches as a local subprocess has no representation on
  a hosted agent and must be published as an endpoint first.

So "a six-sevenths complete field mapping" is true of fields and false of fidelity.
The honest claim is that the *skeleton* transfers and the *containment* does not —
which is the same conclusion the L item reached from the opposite direction, and it
is the reason the environment is underivable rather than merely unset.

## What this does not claim

- Not that the capability is missing. It ships, it is documented, and `ant` is the
  recommended way to drive it.
- Not that it is hidden. The platform docs are clear once you are reading platform
  docs. The failure is that nothing in the tool a developer already lives in routes
  them there.
- Not, yet, that this costs revenue. One user's experience is an anecdote. The
  collision table reproduces on any machine; the size of the affected population is
  internal data.

## Sources

- Claude Code `2.1.259` — `claude --help`, `claude agents --help`, `claude auth --help`.
- `ant` `1.29.0` — `ant --help`, `ant auth status`, `ant beta:{agents,environments,deployments} --help`.
- Both captured by `probe.sh` on 2 September 2026.
- Bundled `claude-api` skill, `shared/anthropic-cli.md` — the control-plane/data-plane
  split and the auth trap (the only claims here not taken from a binary).
