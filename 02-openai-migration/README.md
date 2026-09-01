# OpenAI → Claude migration

Point Claude Code at a repo that uses the OpenAI SDK. It rewrites every call site
against a rulebook, then blocks the pull request until your eval cases pass.

**Engineering cost to build:** about two weeks. That buys Python and Chat
Completions only, and reuses the existing Claude Code migration kit, the Claude
GitHub App, and the Workbench eval tooling. Each additional language or API surface
adds to it.

[Open the prototype](https://claude.ai/code/artifact/13a609b1-6d14-49ac-99fe-644f4e0b29c9)

## Hypothesis

The rewrite blocks migration, not model quality. Remove the rewrite and workloads
move, which adds metered revenue.

A narrower claim is cheaper to test: the parity gate alone unblocks the decision. If
teams migrate once they can prove no regression on their own cases, build the gate
and skip the rewriter.

## Why this isn't solved already

| Mechanism | Status |
|---|---|
| Prompt rewriting | Ships. The Workbench prompt improver is marketed for "prompts originally written for other AI models" |
| Tool schema translation | Ships. The OpenAI SDK compatibility layer translates `tools` and `tool_calls` server-side |
| Repo access | Ships. The Claude GitHub App is already installed for Code Review |
| Reporting what broke | Missing |

The compatibility layer "silently ignores" most unsupported fields. Two of them carry
your output contract: `response_format` and `tools[].strict`. You evaluate Claude
through the layer Anthropic recommends for evaluation, lose schema enforcement, and
read the unenforced result as the model's ceiling.

## Rulebook

Thirteen rules. Every construct that differs between the two APIs falls into one class.

| Class | Handling | Example |
|---|---|---|
| Mechanical | Applied automatically | `tools[].function.parameters` → `input_schema` |
| Choice | Pick a default, change it later | `temperature` → an `output_config.effort` level |
| Blocking | Held for review | schema bounds native structured outputs can't express |

## Parity gate

A language migration gates on a compiler. No compiler tells you whether a prompt still
works, so the merge gates on your eval cases instead: baseline run against migrated
run, same cases, same judge.

This is why Anthropic's published migration kit doesn't apply unchanged. That kit
assumes a new target language, a compiler, and a non-incremental rewrite. None hold here.

In the seeded scan, three cases regress from one root cause and two recover. The pull
request reads **Blocked by parity** until you resolve them.

## Success metrics

Track conversion first. Revenue follows, but lags by a quarter.

| Metric | What it tells you | Target |
|---|---|---|
| Merged migrations per quarter | Whether workloads actually move | Primary |
| Metered spend 90 days after merge | Revenue impact, against the account's pre-migration baseline | Primary |
| Scan → merged PR | Where the funnel leaks | > 40% |
| Days from scan to merge | Whether this is an afternoon or a quarter | < 5 |
| Call sites migrated without review | Rulebook coverage. Low means you aren't saving work | > 85% |
| Parity pass on first run | Migration quality | > 70% |

Two guardrails decide whether to keep shipping:

| Guardrail | Why it matters | Limit |
|---|---|---|
| Reverts within 30 days | A gate that passes bad migrations is worse than no gate | < 5% |
| Production regressions after a passing gate | Measures whether the judge is trustworthy | ~0 |

To test the narrower claim, measure how many teams run the parity gate without
applying the rewrite. If that number is high, the proof matters more than the
rewriting, and the product is smaller than this one.

## Run a migration

The scan runs in Claude Code, not in the Console. Your source never leaves your
machine or your CI runner. The Console holds the rulebook, the decisions, and the
parity history.

```
$ claude /migrate-from-openai --to claude-sonnet-5

  scanning 11 files… 39 call sites
  rulebook: 34 automatic, 5 held
  → pushed to Console · Build › Migrations
```

In CI, use the action you already run:

```yaml
- uses: anthropics/claude-code-action@v1
  with:
    prompt: /migrate-from-openai --to claude-sonnet-5
```

The slash command is proposed, not shipped. Everything it builds on exists.

## Contents

| Path | What it does |
|---|---|
| `app/src/data.js` | The seeded scan and rulebook. Every metric derives from here, so the tabs can't disagree |
| `app/src/App.jsx` | Hash routing and lifted rulebook state |
| `app/src/views/` | One file per tab |
| `prototype/migration_lint.py` | Static analyser the rulebook came from. Classifies each field by whether it changes the result, then emits the native request |
| `prototype/test_migration_lint.py` | 28 invariants |
| `page/build-single-file.py` | Folds the build into one file for preview hosting |

To run the app:

```
cd app && npm ci && npm run dev
```

The linter withholds `strict: true` and `output_config.format` unless the schema is
expressible natively. Promising enforcement the API can't deliver would reproduce the
defect this idea is about.

## Prior art

The pattern is proven, which de-risks the design and is also the sharpest objection.

| Product | What it does |
|---|---|
| AWS Transform / Amazon Q Developer | First-party agentic migration onto AWS |
| Moderne | Dashboard tracking campaigns that open PRs across many repos |

Neither exists for LLM provider migration. Every provider ships a compatibility shim
instead, and the shim is what fails silently.

## Risks

| Risk | Kills the idea if |
|---|---|
| Rewrite is small | Most OpenAI workloads take an afternoon to port, so switching cost isn't the barrier |
| Judge disagrees with the team | The gate is theatre and this is just a codemod |
| Teams refuse repo access | They already grant it for Code Review, but this asks for write |

## Evidence

Quotations come from Anthropic documentation fetched on 1 September 2026 and are
linked from each rule.

The prototype runs on seeded data. It reads no repository and runs no inference.

No user report backs the claim that developers reach the wrong conclusion from a
compatibility-layer evaluation. It follows from documented behaviour. Close that gap
first.
