#!/usr/bin/env python3
"""
Cache lint: find workloads paying the prompt-cache write premium for nothing,
and name the byte that broke the prefix.

Prompt caching is priced as an option you buy up front:

    5-minute cache write   1.25x the base input price
    1-hour cache write     2x
    cache read             0.1x  (0.025x on Fable 5.1 / Mythos 5.1)

So a workload that writes the cache and never reads it is not merely failing to
save 90%. It is paying 1.25x to 2x MORE than if it had never enabled caching at
all. The premium is charged for a mechanism that is doing nothing.

Nothing tells the developer this is happening. The only signal is
`cache_read_input_tokens` sitting at zero -- a field you have to already suspect
in order to go and read.

Both halves of the fix already ship, separately:

  DETECTION   The Usage Report API returns cache_creation.ephemeral_5m_input_tokens,
              cache_creation.ephemeral_1h_input_tokens, cache_read_input_tokens and
              uncached_input_tokens, grouped by api_key_id / workspace_id / model,
              in buckets down to 1m. Nothing in the Console reads these fields.

  DIAGNOSIS   Cache diagnostics (beta `cache-diagnosis-2026-04-07`) compares two
              consecutive requests server-side and returns a typed
              cache_miss_reason: model_changed, system_changed, tools_changed,
              messages_changed. But it is opt-in, the beta header must be on
              EVERY request -- a retrofit fails with previous_message_not_found --
              so it only answers a developer who already asked the question.

This tool is the join, run locally against data you already have.

    ./cache_lint.py detect  fixtures/usage-report.json
    ./cache_lint.py explain fixtures/payload-log.json
    ./cache_lint.py explain fixtures/payload-log.json --json

`detect` reads a Usage Report API response and prices the premium.
`explain` reads a log of consecutive request payloads and localises the invalidator,
classifying it into the same discriminated union the beta returns, so the local
answer and the server answer use one vocabulary.

Where a local diff cannot see the cause -- a server-side invalidation, or a turn
that appends past the lookback window -- this reports `unavailable` rather than
guessing, which is also what the API does.

Sources, all fetched 2 September 2026:
  https://platform.claude.com/docs/en/build-with-claude/prompt-caching
  https://platform.claude.com/docs/en/build-with-claude/cache-diagnostics
  https://platform.claude.com/docs/en/api/admin-api/usage-cost/get-messages-usage-report
  https://platform.claude.com/docs/en/about-claude/pricing

Stdlib only.
"""

import json
import re
import sys

# --------------------------------------------------------------------------
# Pricing. Base input $/MTok, from the pricing page. The write and read
# multipliers are properties of the caching feature, not of the model -- except
# the read rate, which Fable 5.1 and Mythos 5.1 cut to 0.025x.

INPUT_PRICE = {
    "claude-fable-5-1": 10.00,
    "claude-mythos-5-1": 10.00,
    "claude-fable-5": 10.00,
    "claude-opus-5": 5.00,
    "claude-opus-4-8": 5.00,
    "claude-opus-4-7": 5.00,
    "claude-opus-4-6": 5.00,
    "claude-sonnet-5": 2.00,
    "claude-sonnet-4-6": 3.00,
    "claude-haiku-4-5": 1.00,
}

WRITE_5M = 1.25
WRITE_1H = 2.00
READ_STANDARD = 0.1
READ_DISCOUNTED = 0.025          # Fable 5.1 / Mythos 5.1
DISCOUNTED_READ_MODELS = ("fable-5-1", "mythos-5-1")

# The minimum cacheable prefix is model-dependent, 512-4096 tokens. Below it a
# breakpoint silently does not cache, and that is documented behaviour rather
# than a defect -- so it must not be reported as one.
MIN_CACHEABLE = {
    "haiku-4-5": 4096,
    "haiku": 2048,
}
MIN_CACHEABLE_DEFAULT = 1024

# A run of buckets is needed before a zero-read workload means anything: the
# first write in any conversation legitimately has nothing to read.
MIN_CONSECUTIVE_BUCKETS = 3

# Reads never reach exactly zero in a mixed workload, so the trigger is a ratio.
ZERO_READ_RATIO = 0.02

# Being technically correct about forty cents is how a billing warning gets
# trained into background noise. Below this, the finding is real and not worth
# anyone's attention.
MATERIALITY_FLOOR_USD = 5.00


def input_price(model):
    """Base input $/MTok. Unknown models price at 0 so they report tokens only."""
    return INPUT_PRICE.get(model, 0.0)


def read_multiplier(model):
    m = (model or "").lower()
    return READ_DISCOUNTED if any(t in m for t in DISCOUNTED_READ_MODELS) else READ_STANDARD


def min_cacheable(model):
    m = (model or "").lower()
    for tag, floor in MIN_CACHEABLE.items():
        if tag in m:
            return floor
    return MIN_CACHEABLE_DEFAULT


# --------------------------------------------------------------------------
# detect: read the Usage Report API and price the premium.

PREMIUM_FOR_NOTHING = "PREMIUM FOR NOTHING"   # writing, never reading
NEVER_ENGAGED = "never engaged"               # large input, no cache activity at all

DETECT_ORDER = [PREMIUM_FOR_NOTHING, NEVER_ENGAGED]


def _key_of(result):
    """Group results by whatever dimensions the caller grouped by."""
    return (result.get("api_key_id"), result.get("workspace_id"), result.get("model"))


def detect(report):
    """
    Flag keys paying the write premium with nothing to show for it.

    The premium is the honest number. "You could have saved 90%" assumes the
    prefix would have been reused, which this data cannot establish. What it CAN
    establish is that the caller paid 1.25x-2x base input rate on tokens that
    were never read back -- strictly worse than not caching. That figure is
    arithmetic, not a projection.
    """
    series = {}
    for bucket in report.get("data") or []:
        for result in bucket.get("results") or []:
            creation = result.get("cache_creation") or {}
            series.setdefault(_key_of(result), []).append({
                "starting_at": bucket.get("starting_at"),
                "w5m": creation.get("ephemeral_5m_input_tokens", 0) or 0,
                "w1h": creation.get("ephemeral_1h_input_tokens", 0) or 0,
                "read": result.get("cache_read_input_tokens", 0) or 0,
                "uncached": result.get("uncached_input_tokens", 0) or 0,
            })

    findings = []
    for (api_key_id, workspace_id, model), buckets in series.items():
        price = input_price(model)
        floor = min_cacheable(model)

        written = [b for b in buckets if (b["w5m"] + b["w1h"]) > floor]
        run = _longest_zero_read_run(written)

        if len(run) >= MIN_CONSECUTIVE_BUCKETS:
            w5m = sum(b["w5m"] for b in run)
            w1h = sum(b["w1h"] for b in run)
            read = sum(b["read"] for b in run)

            # What was actually billed for those writes, over base rate.
            premium = ((w5m * (WRITE_5M - 1.0)) + (w1h * (WRITE_1H - 1.0))) / 1e6 * price
            # What the same traffic would have cost with caching off entirely.
            uncached_equiv = (w5m + w1h) / 1e6 * price
            billed = (w5m * WRITE_5M + w1h * WRITE_1H) / 1e6 * price
            # Clearly-labelled counterfactual: what a hit would have cost instead.
            if_hit = (w5m + w1h) / 1e6 * price * read_multiplier(model)

            # Suppress findings too small to act on -- but only where the model
            # is priceable. An unknown model prices at 0, and dropping it here
            # would silently hide a large finding behind a missing price.
            if price > 0 and premium < MATERIALITY_FLOOR_USD:
                continue

            findings.append({
                "severity": PREMIUM_FOR_NOTHING,
                "api_key_id": api_key_id,
                "workspace_id": workspace_id,
                "model": model,
                "buckets": len(run),
                "from": run[0]["starting_at"],
                "to": run[-1]["starting_at"],
                "write_tokens": w5m + w1h,
                "read_tokens": read,
                "billed": round(billed, 2),
                "uncached_equivalent": round(uncached_equiv, 2),
                "premium_paid": round(premium, 2),
                "if_it_had_hit": round(if_hit, 2),
                "note": (
                    f"{w5m + w1h:,} tokens written to cache across {len(run)} consecutive "
                    f"buckets, {read:,} read back. At {WRITE_5M}x/{WRITE_1H}x write rates "
                    f"this billed ${billed:,.2f} against ${uncached_equiv:,.2f} for the same "
                    f"traffic with caching switched off -- a ${premium:,.2f} premium for a "
                    f"mechanism that returned nothing."
                ),
                "remedy": (
                    "Enable cache diagnostics (beta cache-diagnosis-2026-04-07) on this "
                    "key and thread previous_message_id through consecutive requests; the "
                    "response names which of model / system / tools / messages diverged. "
                    "Or run: cache_lint.py explain <payload-log.json>"
                ),
            })
            continue

        # Weaker signal: substantial uncached input, no cache activity at all.
        # This cannot distinguish "should be caching" from "correctly not
        # caching a workload with no stable prefix", so it is reported as
        # informational and never priced.
        quiet = [b for b in buckets
                 if b["uncached"] > floor and (b["w5m"] + b["w1h"] + b["read"]) == 0]
        if len(quiet) >= MIN_CONSECUTIVE_BUCKETS:
            findings.append({
                "severity": NEVER_ENGAGED,
                "api_key_id": api_key_id,
                "workspace_id": workspace_id,
                "model": model,
                "buckets": len(quiet),
                "from": quiet[0]["starting_at"],
                "to": quiet[-1]["starting_at"],
                "write_tokens": 0,
                "read_tokens": 0,
                "billed": None,
                "uncached_equivalent": None,
                "premium_paid": None,
                "if_it_had_hit": None,
                "note": (
                    f"{sum(b['uncached'] for b in quiet):,} uncached input tokens across "
                    f"{len(quiet)} buckets with no cache_control activity at all. This may "
                    f"be correct -- a workload with no stable prefix should not cache. Not "
                    f"priced, because this data cannot tell the two apart."
                ),
                "remedy": "Check whether the caller emits cache_control breakpoints at all.",
            })

    findings.sort(key=lambda f: (DETECT_ORDER.index(f["severity"]),
                                 -(f["premium_paid"] or 0)))
    return findings


def _longest_zero_read_run(buckets):
    """Longest run of consecutive buckets writing cache and reading ~nothing."""
    best, cur = [], []
    for b in buckets:
        written = b["w5m"] + b["w1h"]
        if written and (b["read"] / written) < ZERO_READ_RATIO:
            cur.append(b)
            if len(cur) > len(best):
                best = list(cur)
        else:
            cur = []
    return best


# --------------------------------------------------------------------------
# explain: localise the invalidator in a payload log.
#
# The render order of the cached prefix is tools -> system -> messages, and any
# byte change anywhere in the prefix invalidates everything after it. So the
# comparison walks the prefix in that order and stops at the first divergence:
# later ones hide behind it, exactly as the API reports only the earliest.

MODEL_CHANGED = "model_changed"
SYSTEM_CHANGED = "system_changed"
TOOLS_CHANGED = "tools_changed"
MESSAGES_CHANGED = "messages_changed"
UNAVAILABLE = "unavailable"

# Parameters outside the prefix that still invalidate it. The API folds these
# into `unavailable` rather than naming them; so does this.
PROMPT_AFFECTING = ("tool_choice", "thinking", "context_management",
                    "output_config", "output_format", "betas")

# The cache lookback spans 20 content-block positions. A turn that appends more
# than that pushes the previous entry out of range, and every subsequent request
# rewrites the whole conversation with byte-identical payloads -- a miss no diff
# can see, because there is no difference to find.
LOOKBACK_POSITIONS = 20

TIMESTAMP = re.compile(
    r"\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}|\d{2}:\d{2}:\d{2}|\b\d{10,13}\b")
UUIDISH = re.compile(
    r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b"
    r"|\b[0-9a-fA-F]{16,}\b")


def strip_cache_control(node):
    """
    Remove cache_control markers before diffing.

    The breakpoint moves between adjacent requests in a growing conversation and
    is NOT an invalidator -- blocks marked on an earlier request still hit. A
    diff that leaves the marker in reports the marker every time and buries the
    real cause.
    """
    if isinstance(node, dict):
        return {k: strip_cache_control(v) for k, v in node.items()
                if k != "cache_control"}
    if isinstance(node, list):
        return [strip_cache_control(v) for v in node]
    return node


def canonical(node):
    """Serialize preserving key order, so non-deterministic serialization shows up."""
    return json.dumps(node, ensure_ascii=False, sort_keys=False)


def _same_content_different_order(a, b):
    """True when two structures are equal as data but serialize differently.

    This is its own bug class: a map iterated in undefined order, or a library
    that re-serializes on resend. The payloads are equivalent to a reader and
    different to the cache.
    """
    return canonical(a) != canonical(b) and \
        json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)


def _describe_text_divergence(before, after):
    """Point at the first differing character and name the kind of change."""
    limit = min(len(before), len(after))
    i = 0
    while i < limit and before[i] == after[i]:
        i += 1

    window_before = before[max(0, i - 30):i + 40]
    window_after = after[max(0, i - 30):i + 40]

    # Look at a window either side of the divergence, not just after it. The
    # first differing byte of a changing timestamp is usually in the middle of
    # it ("14:0[3] vs 14:0[8]"), so a forward-only scan sees a fragment and
    # recognises nothing.
    kind = None
    tail_before = before[max(0, i - 40):i + 80]
    tail_after = after[max(0, i - 40):i + 80]
    if TIMESTAMP.search(tail_before) or TIMESTAMP.search(tail_after):
        kind = ("a timestamp. Interpolating the current time into a cached prefix "
                "rewrites it on every request")
    elif UUIDISH.search(tail_before) or UUIDISH.search(tail_after):
        kind = ("an id that changes per request. Request, session and trace ids "
                "belong after the last breakpoint, not inside the prefix")

    return {"offset": i, "before": window_before, "after": window_after, "kind": kind}


def _appended_positions(prev_msgs, next_msgs):
    """Content-block positions added by the newest turn."""
    added = 0
    for m in next_msgs[len(prev_msgs):]:
        content = m.get("content")
        added += len(content) if isinstance(content, list) else 1
    return added


def compare(prev, nxt):
    """
    Classify the first divergence between two consecutive request payloads.

    Returns a dict shaped like the API's cache_miss_reason, or None when the
    prefix is byte-identical and no local explanation is needed.
    """
    a, b = strip_cache_control(prev), strip_cache_control(nxt)

    if a.get("model") != b.get("model"):
        return {"type": MODEL_CHANGED,
                "detail": f"{a.get('model')!r} -> {b.get('model')!r}",
                "note": "The cache is per-model. A router, fallback or A/B split "
                        "moved this request to a different model, so it could not "
                        "read the previous model's entry.",
                "remedy": "Hold the model constant for the life of a cached conversation."}

    # tools renders first.
    if a.get("tools") != b.get("tools") or canonical(a.get("tools")) != canonical(b.get("tools")):
        if _same_content_different_order(a.get("tools"), b.get("tools")):
            return {"type": TOOLS_CHANGED,
                    "detail": "same tools, different serialization",
                    "note": "The tools array carries identical data in a different "
                            "byte order. Something is iterating a map with undefined "
                            "order, or re-serializing schemas on resend. Nothing is "
                            "visibly wrong with the request, and the cache misses "
                            "every time.",
                    "remedy": "Serialize tool schemas deterministically (sort keys) "
                              "and send the tool list in a fixed order."}
        names_a = [t.get("name") for t in (a.get("tools") or [])]
        names_b = [t.get("name") for t in (b.get("tools") or [])]
        if names_a != names_b:
            detail = f"{names_a} -> {names_b}"
        else:
            detail = "tool definitions changed"
        return {"type": TOOLS_CHANGED, "detail": detail,
                "note": "Tools were added, removed or reordered between turns. "
                        "The tools block renders first, so this invalidates the "
                        "whole prefix behind it.",
                "remedy": "Send the same tool list, in the same order, every turn."}

    if canonical(a.get("system")) != canonical(b.get("system")):
        if _same_content_different_order(a.get("system"), b.get("system")):
            return {"type": SYSTEM_CHANGED,
                    "detail": "same system content, different serialization",
                    "note": "The system block carries identical data in a different "
                            "byte order.",
                    "remedy": "Serialize the system block deterministically."}
        where = _describe_text_divergence(canonical(a.get("system")),
                                          canonical(b.get("system")))
        note = ("The system prompt is not byte-stable between requests. It renders "
                "before every message, so this invalidates the entire conversation "
                "behind it.")
        if where["kind"]:
            note += " The first divergence is " + where["kind"] + "."
        return {"type": SYSTEM_CHANGED,
                "detail": f"first divergence at character {where['offset']}",
                "before": where["before"], "after": where["after"], "note": note,
                "remedy": "Make the system prompt a byte-stable constant and move "
                          "anything per-request into the first user message after "
                          "the last cache breakpoint."}

    prev_msgs = a.get("messages") or []
    next_msgs = b.get("messages") or []

    # History must be append-only: the previous request's messages should
    # reappear unchanged as a prefix of this one.
    overlap = min(len(prev_msgs), len(next_msgs))
    for i in range(overlap):
        if canonical(prev_msgs[i]) != canonical(next_msgs[i]):
            if _same_content_different_order(prev_msgs[i], next_msgs[i]):
                detail = f"messages[{i}] re-serialized"
                note = ("An earlier turn carries the same content in a different "
                        "byte order on resend -- typically assistant content or "
                        "tool_result blocks rebuilt rather than echoed verbatim.")
            else:
                detail = f"messages[{i}] altered"
                note = ("An earlier turn was edited, truncated or reordered rather "
                        "than appended to. Everything from that point on is a "
                        "fresh write.")
            where = _describe_text_divergence(canonical(prev_msgs[i]),
                                              canonical(next_msgs[i]))
            return {"type": MESSAGES_CHANGED, "detail": detail,
                    "before": where["before"], "after": where["after"], "note": note,
                    "remedy": "Treat history as append-only; echo assistant content "
                              "and tool results back verbatim."}

    if len(next_msgs) < len(prev_msgs):
        return {"type": MESSAGES_CHANGED,
                "detail": f"history shrank, {len(prev_msgs)} -> {len(next_msgs)} messages",
                "note": "Conversation history was truncated. Trimming old turns to "
                        "save context rewrites the prefix and re-bills the rest.",
                "remedy": "Use context editing or compaction, which preserve the "
                          "cached prefix, rather than dropping messages yourself."}

    # Prefix is identical. Anything left is outside what a diff can see.
    differing = [k for k in PROMPT_AFFECTING if canonical(a.get(k)) != canonical(b.get(k))]
    if differing:
        return {"type": UNAVAILABLE,
                "detail": "prompt-affecting parameters changed: " + ", ".join(differing),
                "note": "The prefix is byte-identical, but a request parameter "
                        "outside it changed. These are not part of the diff and "
                        "the API reports them as unavailable too.",
                "remedy": "Hold these constant for the life of a cached conversation."}

    added = _appended_positions(prev_msgs, next_msgs)
    if added > LOOKBACK_POSITIONS:
        return {"type": UNAVAILABLE,
                "detail": f"{added} content-block positions appended in one turn",
                "note": f"The cache lookback spans {LOOKBACK_POSITIONS} positions. A "
                        f"turn appending more than that pushes the previous entry out "
                        f"of range, so every later request rewrites the conversation "
                        f"with byte-identical payloads. There is no difference to find.",
                "remedy": "Consolidate tool results, or set a breakpoint inside the "
                          "long turn so a nearer entry stays in range."}

    return None


def explain(payloads):
    """Compare each adjacent pair. Returns one row per transition."""
    rows = []
    for i in range(1, len(payloads)):
        rows.append({"from_index": i - 1, "to_index": i,
                     "cache_miss_reason": compare(payloads[i - 1], payloads[i])})
    return rows


# --------------------------------------------------------------------------

def _wrap(text, width):
    words, lines, cur = text.split(), [], ""
    for w in words:
        if len(cur) + len(w) + 1 > width:
            lines.append(cur)
            cur = w
        else:
            cur = f"{cur} {w}".strip()
    if cur:
        lines.append(cur)
    return lines


def render_detect(findings):
    print()
    if not findings:
        print("  No workload is paying the cache write premium for nothing.")
        print()
        return

    total = sum(f["premium_paid"] or 0 for f in findings)
    priced = [f for f in findings if f["severity"] == PREMIUM_FOR_NOTHING]
    if priced:
        print(f"  {len(priced)} key(s) writing cache and reading nothing back."
              f"  Premium paid: ${total:,.2f}")
        print()

    current = None
    for f in findings:
        if f["severity"] != current:
            current = f["severity"]
            print(f"  ── {current} " + "─" * max(0, 58 - len(current)))
        label = f["api_key_id"] or f["workspace_id"] or "(ungrouped)"
        print(f"  {label}   {f['model'] or '(model not grouped)'}")
        print(f"      {f['from']} → {f['to']}  ({f['buckets']} buckets)")
        for line in _wrap(f["note"], 70):
            print(f"      {line}")
        if f["if_it_had_hit"] is not None:
            print(f"      Had the same tokens been read from cache instead: "
                  f"${f['if_it_had_hit']:,.2f}")
        for k, line in enumerate(_wrap(f["remedy"], 66)):
            print(f"      {'→ ' if k == 0 else '  '}{line}")
        print()


def render_explain(rows):
    print()
    clean = sum(1 for r in rows if r["cache_miss_reason"] is None)
    print(f"  {len(rows)} transition(s), {clean} with a byte-identical prefix")
    print()
    for r in rows:
        reason = r["cache_miss_reason"]
        arrow = f"  [{r['from_index']}] → [{r['to_index']}]"
        if reason is None:
            print(f"{arrow}   prefix intact")
            print()
            continue
        print(f"{arrow}   {reason['type']}")
        print(f"      {reason['detail']}")
        for line in _wrap(reason["note"], 70):
            print(f"      {line}")
        if reason.get("before") is not None:
            print(f"      before: …{reason['before']}…")
            print(f"      after:  …{reason['after']}…")
        for k, line in enumerate(_wrap(reason["remedy"], 66)):
            print(f"      {'→ ' if k == 0 else '  '}{line}")
        print()


def main(argv):
    args = [a for a in argv[1:] if not a.startswith("--")]
    flags = {a for a in argv[1:] if a.startswith("--")}

    if not args or args[0] not in ("detect", "explain"):
        print(__doc__.strip().split("\n\n")[0], file=sys.stderr)
        print("\nusage: cache_lint.py {detect|explain} <file> [--json]", file=sys.stderr)
        return 2

    mode = args[0]
    raw = open(args[1]).read() if len(args) > 1 else sys.stdin.read()
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        print(f"error: input is not valid JSON ({e})", file=sys.stderr)
        return 2

    if mode == "detect":
        findings = detect(data)
        if "--json" in flags:
            print(json.dumps({"findings": findings}, indent=2))
        else:
            render_detect(findings)
        return 1 if any(f["severity"] == PREMIUM_FOR_NOTHING for f in findings) else 0

    rows = explain(data)
    if "--json" in flags:
        print(json.dumps({"transitions": rows}, indent=2))
    else:
        render_explain(rows)
    return 1 if any(r["cache_miss_reason"] for r in rows) else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
