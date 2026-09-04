#!/usr/bin/env python3
"""Invariants for migration_lint. Run: python3 test_migration_lint.py

Runs from any working directory: fixtures resolve against this file, not the shell.
"""

import json
import pathlib

import migration_lint as ml

HERE = pathlib.Path(__file__).parent

FAIL = []


def check(name, cond, detail=""):
    if cond:
        print(f"  pass  {name}")
    else:
        FAIL.append(name)
        print(f"  FAIL  {name} {detail}")


def sev(findings, field):
    for f in findings:
        if f["field"] == field:
            return f["severity"]
    return None


# -- a payload with nothing the compat layer touches -----------------------
clean = {"model": "gpt-4o", "max_tokens": 100,
         "messages": [{"role": "user", "content": "hi"}]}
check("clean payload yields no findings", ml.lint(clean) == [])

# -- response_format ------------------------------------------------------
ok_schema = {"type": "object", "additionalProperties": False,
             "required": ["a"], "properties": {"a": {"type": "string"}}}
rf = dict(clean, response_format={"type": "json_schema",
                                  "json_schema": {"name": "x", "schema": ok_schema}})
f = ml.lint(rf)
check("response_format flagged as contract break",
      sev(f, "response_format") == ml.BREAKS_CONTRACT)
check("expressible schema produces no extra schema findings",
      len([x for x in f if "schema $" in x["field"]]) == 0)
check("expressible schema is carried to output_config.format",
      ml.translate(rf).get("output_config", {}).get("format", {}).get("schema") == ok_schema)

bad_schema = {"type": "object", "additionalProperties": False,
              "required": ["a"], "properties": {"a": {"type": "integer", "minimum": 1}}}
rf_bad = dict(clean, response_format={"type": "json_schema",
                                      "json_schema": {"name": "x", "schema": bad_schema}})
check("unsupported keyword is reported",
      any("minimum" in x["field"] for x in ml.lint(rf_bad)))
check("inexpressible schema is NOT promised in the translation",
      "format" not in ml.translate(rf_bad).get("output_config", {}))

# -- strict tools ---------------------------------------------------------
def tool(schema, strict=True):
    return {"type": "function", "function": {
        "name": "t", "description": "d", "strict": strict, "parameters": schema}}

t_ok = dict(clean, tools=[tool(ok_schema)])
check("tools[].strict flagged as contract break",
      sev(ml.lint(t_ok), "tools[0].strict") == ml.BREAKS_CONTRACT)
check("strict preserved natively when the schema allows it",
      ml.translate(t_ok)["tools"][0].get("strict") is True)

t_bad = dict(clean, tools=[tool({"type": "object", "additionalProperties": False,
                                 "properties": {"a": {"type": "string", "minLength": 3}}})])
check("strict withheld natively when the schema blocks it",
      "strict" not in ml.translate(t_bad)["tools"][0])
check("blocking keyword explained",
      any("minLength" in x["field"] for x in ml.lint(t_bad)))

check("additionalProperties omission is reported",
      any("additionalProperties" in w for _, w in
          ml.check_schema({"type": "object", "properties": {}})))

# -- sampling params depend on the TARGET model ---------------------------
temp = dict(clean, temperature=0.2, top_p=0.9)
check("temperature rejected on current-generation target",
      sev(ml.lint(temp, "claude-opus-5"), "temperature") == ml.NATIVE_REJECTS)
check("temperature dropped from current-generation translation",
      "temperature" not in ml.translate(temp, "claude-opus-5"))
check("temperature carried for a model that still accepts it",
      ml.translate(temp, "claude-sonnet-4-6").get("temperature") == 0.2)
check("temperature >1 capped rather than rejected on older target",
      sev(ml.lint(dict(clean, temperature=1.7), "claude-sonnet-4-6"),
          "temperature") == ml.CHANGES_RESULT)

# -- n, prefill, forced tool choice ---------------------------------------
check("n != 1 reported", sev(ml.lint(dict(clean, n=3)), "n") == ml.NATIVE_REJECTS)

prefill = {"model": "gpt-4o", "messages": [
    {"role": "user", "content": "hi"},
    {"role": "assistant", "content": "{"}]}
check("assistant prefill rejected on current generation",
      sev(ml.lint(prefill, "claude-opus-5"), "messages[-1]") == ml.NATIVE_REJECTS)
check("assistant prefill accepted on 4.6",
      sev(ml.lint(prefill, "claude-sonnet-4-6"), "messages[-1]") is None)

forced = dict(clean, tool_choice="required", tools=[tool(ok_schema, strict=False)])
check("forced tool_choice rejected on Fable 5.1",
      sev(ml.lint(forced, "claude-fable-5-1"), "tool_choice") == ml.NATIVE_REJECTS)
check("forced tool_choice fine on Opus 5",
      sev(ml.lint(forced, "claude-opus-5"), "tool_choice") is None)

# -- message translation ---------------------------------------------------
convo = {"model": "gpt-4o", "messages": [
    {"role": "system", "content": "A"},
    {"role": "user", "content": "q"},
    {"role": "assistant", "tool_calls": [{"id": "c1", "type": "function", "function": {
        "name": "f", "arguments": '{"x": 1}'}}]},
    {"role": "tool", "tool_call_id": "c1", "content": "r"},
    {"role": "developer", "content": "B"},
    {"role": "user", "content": "again"}]}
nat = ml.translate(convo)
check("system messages hoisted and joined in order", nat["system"] == "A\nB")
check("roles alternate after merging",
      [m["role"] for m in nat["messages"]] == ["user", "assistant", "user"])
check("tool_call becomes tool_use with parsed args",
      nat["messages"][1]["content"][0] == {"type": "tool_use", "id": "c1",
                                           "name": "f", "input": {"x": 1}})
check("tool_result and following user turn merged",
      [b["type"] for b in nat["messages"][2]["content"]] == ["tool_result", "text"])
check("hoisting out of position is reported",
      sev(ml.lint(convo), "messages[system]") == ml.CHANGES_RESULT)

bad_args = {"model": "gpt-4o", "messages": [
    {"role": "assistant", "tool_calls": [{"id": "c", "type": "function",
                                          "function": {"name": "f", "arguments": "{not json"}}]}]}
check("malformed tool arguments do not crash",
      ml.translate(bad_args)["messages"][0]["content"][0]["input"] == {})

# -- dropped input & severity ordering ------------------------------------
audio = {"model": "gpt-4o", "messages": [{"role": "user", "content": [
    {"type": "input_audio", "input_audio": {}}]}]}
check("audio content block reported as dropped input",
      sev(ml.lint(audio), "messages[0].content[0]") == ml.DROPS_INPUT)

order = [ml.ORDER.index(x["severity"]) for x in ml.lint(json.load(
    open(HERE / "fixtures" / "support-triage.json")))]
check("findings sorted by severity", order == sorted(order))

print()
if FAIL:
    print(f"{len(FAIL)} failing: {FAIL}")
    raise SystemExit(1)
print("all invariants hold")
