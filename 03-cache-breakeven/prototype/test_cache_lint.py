#!/usr/bin/env python3
"""Invariants for cache_lint. Run: python3 test_cache_lint.py"""

import copy
import json
import cache_lint as cl

FAIL = []


def check(name, cond, detail=""):
    if cond:
        print(f"  pass  {name}")
    else:
        FAIL.append(name)
        print(f"  FAIL  {name} {detail}")


def reason(prev, nxt):
    r = cl.compare(prev, nxt)
    return r["type"] if r else None


def base(**extra):
    body = {"model": "claude-sonnet-5", "max_tokens": 1024,
            "tools": [{"name": "lookup", "description": "d",
                       "input_schema": {"type": "object",
                                        "properties": {"a": {"type": "string"}}}}],
            "system": [{"type": "text", "text": "stable prefix"}],
            "messages": [{"role": "user", "content": [{"type": "text", "text": "hi"}]}]}
    body.update(extra)
    return body


def turn(role, text):
    return {"role": role, "content": [{"type": "text", "text": text}]}


# -- pricing constants match the documented multipliers ---------------------
check("5-minute write multiplier is 1.25", cl.WRITE_5M == 1.25)
check("1-hour write multiplier is 2", cl.WRITE_1H == 2.00)
check("standard cache read multiplier is 0.1", cl.READ_STANDARD == 0.1)
check("Fable/Mythos 5.1 read multiplier is 0.025", cl.READ_DISCOUNTED == 0.025)
check("Fable 5.1 gets the discounted read rate",
      cl.read_multiplier("claude-fable-5-1") == 0.025)
check("Opus 5 gets the standard read rate",
      cl.read_multiplier("claude-opus-5") == 0.1)
check("an unknown model prices at zero rather than guessing",
      cl.input_price("claude-something-unreleased") == 0.0)

# -- break-even amortization ------------------------------------------------
# The number the Console's amortization chart does not draw.
check("5-minute break-even is 0.28x",
      round(cl.breakeven_amortization("claude-sonnet-5", "5m"), 4) == 0.2778)
check("1-hour break-even is 1.11x",
      round(cl.breakeven_amortization("claude-sonnet-5", "1h"), 4) == 1.1111)
check("the discounted read rate lowers the break-even",
      cl.breakeven_amortization("claude-fable-5-1", "5m")
      < cl.breakeven_amortization("claude-sonnet-5", "5m"))
check("the 1-hour TTL needs more reuse than the 5-minute TTL",
      cl.breakeven_amortization("claude-sonnet-5", "1h")
      > cl.breakeven_amortization("claude-sonnet-5", "5m"))
check("the 5-minute break-even sits below the chart's 0.50x axis floor",
      cl.breakeven_amortization("claude-sonnet-5", "5m") < 0.50)

def bills_more(model, ttl, amort):
    """Cached cost vs uncached cost for W written tokens read back `amort` times."""
    w = cl.WRITE_5M if ttl == "5m" else cl.WRITE_1H
    return (w + cl.read_multiplier(model) * amort) > (1.0 + amort)

be = cl.breakeven_amortization("claude-sonnet-5", "5m")
check("just below break-even, caching bills more than not caching",
      bills_more("claude-sonnet-5", "5m", be - 0.05))
check("just above break-even, caching bills less",
      not bills_more("claude-sonnet-5", "5m", be + 0.05))
check("zero amortization always bills more",
      bills_more("claude-sonnet-5", "5m", 0.0) and bills_more("claude-sonnet-5", "1h", 0.0))

# -- cache_control markers are stripped before diffing ---------------------
marked = {"system": [{"type": "text", "text": "x",
                      "cache_control": {"type": "ephemeral"}}]}
check("strip_cache_control removes nested markers",
      "cache_control" not in json.dumps(cl.strip_cache_control(marked)))

moved_a = base()
moved_a["system"] = [{"type": "text", "text": "stable prefix",
                      "cache_control": {"type": "ephemeral"}}]
moved_b = base()
moved_b["messages"] = [{"role": "user", "content": [
    {"type": "text", "text": "hi", "cache_control": {"type": "ephemeral"}}]}]
check("a breakpoint moving between turns is not an invalidator",
      reason(moved_a, moved_b) is None)

# -- model -----------------------------------------------------------------
check("a different model is model_changed",
      reason(base(), base(model="claude-opus-5")) == cl.MODEL_CHANGED)

# -- system ----------------------------------------------------------------
ts_a = base(system=[{"type": "text", "text": "now: 2026-08-26T14:03:11Z"}])
ts_b = base(system=[{"type": "text", "text": "now: 2026-08-26T14:08:52Z"}])
check("a changing system prompt is system_changed",
      reason(ts_a, ts_b) == cl.SYSTEM_CHANGED)
check("a changing timestamp is named as such",
      "timestamp" in cl.compare(ts_a, ts_b)["note"])

uuid_a = base(system=[{"type": "text", "text": "req 3f2a91b8c4d5e6f7 begins"}])
uuid_b = base(system=[{"type": "text", "text": "req 9a1b22c3d4e5f607 begins"}])
check("a per-request id is named as such",
      "id that changes" in cl.compare(uuid_a, uuid_b)["note"])

reorder_a = base(system=[{"type": "text", "text": "x"}])
reorder_b = base(system=[{"text": "x", "type": "text"}])
check("same system content in a different byte order is still system_changed",
      reason(reorder_a, reorder_b) == cl.SYSTEM_CHANGED)
check("re-serialization is reported as such, not as an edit",
      "serialization" in cl.compare(reorder_a, reorder_b)["detail"])

# -- tools -----------------------------------------------------------------
tools_reordered = copy.deepcopy(base())
tools_reordered["tools"][0]["input_schema"]["properties"] = {
    "b": {"type": "string"}, "a": {"type": "string"}}
with_b = copy.deepcopy(base())
with_b["tools"][0]["input_schema"]["properties"] = {
    "a": {"type": "string"}, "b": {"type": "string"}}
check("non-deterministic tool serialization is tools_changed",
      reason(with_b, tools_reordered) == cl.TOOLS_CHANGED)
check("non-deterministic tool serialization is named as serialization",
      "serialization" in cl.compare(with_b, tools_reordered)["detail"])

added = copy.deepcopy(base())
added["tools"].append({"name": "other", "description": "d",
                       "input_schema": {"type": "object", "properties": {}}})
check("adding a tool is tools_changed", reason(base(), added) == cl.TOOLS_CHANGED)
check("the changed tool names are reported",
      "other" in cl.compare(base(), added)["detail"])

# -- render order: tools, then system, then messages -----------------------
both = copy.deepcopy(added)
both["system"] = [{"type": "text", "text": "different"}]
check("tools render before system, so tools_changed wins",
      reason(base(), both) == cl.TOOLS_CHANGED)

sys_and_msgs = base(system=[{"type": "text", "text": "different"}])
sys_and_msgs["messages"] = [turn("user", "changed")]
check("system renders before messages, so system_changed wins",
      reason(base(), sys_and_msgs) == cl.SYSTEM_CHANGED)

# -- messages --------------------------------------------------------------
convo = base()
convo["messages"] = [turn("user", "one"), turn("assistant", "two")]
appended = base()
appended["messages"] = [turn("user", "one"), turn("assistant", "two"),
                        turn("user", "three")]
check("appending a turn leaves the prefix intact", reason(convo, appended) is None)

edited = base()
edited["messages"] = [turn("user", "one"), turn("assistant", "two, reworded"),
                      turn("user", "three")]
check("editing an earlier turn is messages_changed",
      reason(convo, edited) == cl.MESSAGES_CHANGED)
check("the altered position is identified",
      "messages[1]" in cl.compare(convo, edited)["detail"])

truncated = base()
truncated["messages"] = [turn("assistant", "two")]
check("truncating history is messages_changed",
      reason(convo, truncated) == cl.MESSAGES_CHANGED)

# -- unavailable: real causes a local diff cannot see ----------------------
effort_a = base(output_config={"effort": "high"})
effort_b = base(output_config={"effort": "low"})
check("a prompt-affecting parameter outside the prefix is unavailable",
      reason(effort_a, effort_b) == cl.UNAVAILABLE)

long_turn = base()
long_turn["messages"] = base()["messages"] + [{
    "role": "user",
    "content": [{"type": "text", "text": f"b{i}"} for i in range(21)]}]
check("appending past the lookback window is unavailable",
      reason(base(), long_turn) == cl.UNAVAILABLE)

at_limit = base()
at_limit["messages"] = base()["messages"] + [{
    "role": "user",
    "content": [{"type": "text", "text": f"b{i}"} for i in range(20)]}]
check("appending exactly the lookback window is not reported",
      reason(base(), at_limit) is None)

# -- explain ---------------------------------------------------------------
log = json.load(open("fixtures/payload-log.json"))
rows = cl.explain(log)
check("explain returns one row per transition", len(rows) == len(log) - 1)
check("the seeded log's first transition is clean",
      rows[0]["cache_miss_reason"] is None)

# -- detect ----------------------------------------------------------------
report = json.load(open("fixtures/usage-report.json"))
findings = cl.detect(report)
flagged = {f["api_key_id"]: f for f in findings}

check("the zero-read key is flagged",
      flagged.get("apikey_01SilentMiss", {}).get("severity") == cl.PREMIUM_FOR_NOTHING)
check("a key that reads its cache back is not flagged",
      "apikey_01Healthy" not in flagged)
check("a prefix below the minimum cacheable length is not flagged",
      "apikey_01ShortPrefix" not in flagged)
check("a key with no cache activity is reported but never priced",
      flagged.get("apikey_01NoBreakpoints", {}).get("severity") == cl.NEVER_ENGAGED
      and flagged["apikey_01NoBreakpoints"]["premium_paid"] is None)

f = flagged["apikey_01SilentMiss"]
w5m, w1h, price = 7_500_000, 1_030_100, 2.00
expect_billed = (w5m * 1.25 + w1h * 2.0) / 1e6 * price
expect_premium = (w5m * 0.25 + w1h * 1.0) / 1e6 * price
check("billed cost matches the multipliers", f["billed"] == round(expect_billed, 2))
check("the premium is the excess over base input rate",
      f["premium_paid"] == round(expect_premium, 2))
check("writing without reading costs MORE than not caching at all",
      f["billed"] > f["uncached_equivalent"])
check("a cache hit would have cost less than not caching",
      f["if_it_had_hit"] < f["uncached_equivalent"])

def scaled(factor, model="claude-sonnet-5"):
    """The same report with cache writes scaled, to move the premium."""
    r = copy.deepcopy(report)
    for bucket in r["data"]:
        for res in bucket["results"]:
            if res["api_key_id"] != "apikey_01SilentMiss":
                continue
            res["model"] = model
            for k in ("ephemeral_5m_input_tokens", "ephemeral_1h_input_tokens"):
                res["cache_creation"][k] = int(res["cache_creation"][k] * factor)
    return r


def flagged_keys(rep):
    return {x["api_key_id"] for x in cl.detect(rep)
            if x["severity"] == cl.PREMIUM_FOR_NOTHING}


check("a surcharge below the materiality floor is not flagged",
      "apikey_01SilentMiss" not in flagged_keys(scaled(0.1)))
check("a surcharge above the materiality floor is flagged",
      "apikey_01SilentMiss" in flagged_keys(scaled(4.0)))
check("an unpriceable model is still flagged despite the floor",
      "apikey_01SilentMiss" in flagged_keys(
          scaled(0.1, model="claude-something-unreleased")))

short = {"data": report["data"][:2]}
check("a run shorter than the minimum is not flagged",
      not [x for x in cl.detect(short)
           if x["severity"] == cl.PREMIUM_FOR_NOTHING])

broken = copy.deepcopy(report)
broken["data"][2]["results"][0]["cache_read_input_tokens"] = 5_000_000
check("a read in the middle breaks the run",
      not [x for x in cl.detect(broken)
           if x["severity"] == cl.PREMIUM_FOR_NOTHING])

order = [cl.DETECT_ORDER.index(x["severity"]) for x in findings]
check("findings sorted by severity", order == sorted(order))

print()
if FAIL:
    print(f"{len(FAIL)} failing: {FAIL}")
    raise SystemExit(1)
print("all invariants hold")
