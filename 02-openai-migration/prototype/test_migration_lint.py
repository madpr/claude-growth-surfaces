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

# The README quotes the linter's summary line for the seeded payload. Pin it, so the
# case and the tool cannot drift apart.
from collections import Counter
_counts = Counter(f["severity"] for f in ml.lint(json.load(
    open(HERE / "fixtures" / "support-triage.json"))))
check("seeded payload: 7 breaks contract, 2 native rejects, 4 changes result, 3 inert",
      (_counts[ml.BREAKS_CONTRACT], _counts[ml.NATIVE_REJECTS],
       _counts[ml.CHANGES_RESULT], _counts[ml.INERT]) == (7, 2, 4, 3),
      dict(_counts))

# -- the seeded repository scenario: scan ----------------------------------
# The terminal demo and the case quote these figures. Every one is computed
# here from fixtures/support-triage-repo.json, and pinned so a surface cannot
# drift from the prototype.
import contextlib
import copy
import io
import re

def captured(argv):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        code = ml.main(["migration_lint.py"] + argv)
    return code, buf.getvalue()

scenario = ml.load_scenario()
scan = ml.scan_report(scenario)
check("scan: 38 places, 33 rewritten without asking, 5 held",
      (scan["places"], scan["automatic"]["sites"], scan["held"]) == (38, 33, 5))
check("scan: nine automatic groups, sites 6 7 3 3 4 2 1 5 2",
      [g["sites"] for g in scan["automatic"]["groups"]] == [6, 7, 3, 3, 4, 2, 1, 5, 2])
check("scan: two decisions, D1 on 3 sites and D2 on 2",
      [(d["id"], d["sites"]) for d in scan["decisions"]] == [("D1", 3), ("D2", 2)])
check("scan: 12 tests, 10 pass on OpenAI, 3 regress on Claude",
      (scan["tests"]["total"], scan["tests"]["baseline"], scan["tests"]["regressed"]) == (12, 10, 3))
check("scan: 9/12 on Claude before decisions",
      scan["tests"]["onTargetBeforeDecisions"] == 9)
check("scan: the regressed tests are tc_006, tc_007, tc_010",
      scan["tests"]["regressedTests"] == ["tc_006", "tc_007", "tc_010"])

by_choice = {o["choices"][0]["option"]: o for o in scan["outcomes"]}
check("scan: 12/12 after Validate after parsing",
      (by_choice["Validate after parsing"]["passing"], by_choice["Validate after parsing"]["total"]) == (12, 12))
check("scan: 9/12 after Drop the bounds",
      (by_choice["Drop the bounds"]["passing"], by_choice["Drop the bounds"]["total"]) == (9, 12))
check("scan: gate line when parity passes",
      by_choice["Validate after parsing"]["gate"] == "parity passed · merge unblocked")
check("scan: gate line when parity fails names the three tests",
      by_choice["Drop the bounds"]["gate"] == "parity failed · merge blocked by tc_006 · tc_007 · tc_010")
check("scan: only D1 changes the count; either D2 option leaves it",
      scan["tests"]["unchangedBy"] == ["D2"] and len(scan["outcomes"]) == 2)
check("scan: pull request #142", scan["pullRequest"] == 142)

code, out = captured(["scan"])
check("scan prints the repo line",
      code == 0 and "acme/support-triage" in out and "11 files" in out and "38 places" in out)
check("scan prints both gate lines",
      "12/12   parity passed · merge unblocked" in out and
      "9/12   parity failed · merge blocked by tc_006 · tc_007 · tc_010" in out)
check("scan prints the test counts",
      "10/12 pass on OpenAI today" in out and "9/12 pass on claude-sonnet-5 before decisions" in out)
code, out = captured(["scan", "--json"])
check("scan --json emits the same report", code == 0 and json.loads(out) == scan)

# -- the cost illustration --------------------------------------------------
cost = ml.cost_illustration(scenario)
check("cost: per request, source $0.0098 and target $0.0052542",
      (cost["perRequest"]["source"], cost["perRequest"]["target"]) == (0.0098, 0.0052542))
check("cost: source $3,646 a month", cost["perMonth"]["source"] == 3646)
check("cost: target $1,955 a month", cost["perMonth"]["target"] == 1955)
check("cost: delta -46%", cost["deltaPercent"] == -46)
check("cost: most of the saving is caching (without it the delta is -16%)",
      cost["uncachedDeltaPercent"] == -16 and
      abs(cost["uncachedDeltaPercent"]) < abs(cost["deltaPercent"]) / 2)
check("cost: an illustration on a seeded workload, not a measurement",
      cost["illustration"] is True and cost["measured"] is False)
code, out = captured(["cost"])
check("cost prints $3,646, $1,955, -46%",
      code == 0 and "$3,646" in out and "$1,955" in out and "-46%" in out)
check("cost prints the provenance and says it is not a measurement",
      "September 1, 2026" in out and "Not a measurement" in out)
code, out = captured(["cost", "--json"])
check("cost --json emits the same figures", code == 0 and json.loads(out) == cost)

# -- the default invocation is unchanged ------------------------------------
code, out = captured([str(HERE / "fixtures" / "support-triage.json")])
check("a payload argument still lints and exits 1 on blocking findings",
      code == 1 and "gpt-4o  ->  claude-sonnet-5" in out and "BREAKS CONTRACT" in out)

# -- the fixture guard ------------------------------------------------------
def refused(mutate):
    """Mutate an in-memory copy and return the guard's message, or None."""
    broken = copy.deepcopy(scenario)
    mutate(broken)
    try:
        ml.check_scenario(broken)
    except ValueError as e:
        return str(e)
    return None

check("guard passes the shipped fixture", refused(lambda s: None) is None)
msg = refused(lambda s: s["automatic"][0].__setitem__("sites", 7))
check("guard: an automatic group count that drifts is refused",
      msg is not None and "automatic groups claim 34 sites; 33 call sites are owned by auto" in msg)
msg = refused(lambda s: s["callSites"].pop())
check("guard: a missing call site is refused",
      msg is not None and "call sites" in msg)
msg = refused(lambda s: s["decisions"][0].__setitem__("sites", 4))
check("guard: a decision claiming sites it does not own is refused",
      msg is not None and "D1 claims 4 sites; 3 call sites are owned by D1" in msg)
msg = refused(lambda s: s["project"].__setitem__("files", 10))
check("guard: a file count that disagrees with the call sites is refused",
      msg is not None and "project says 10 files; the call sites name 11" in msg)
msg = refused(lambda s: s["tests"].__setitem__("regressed", 2))
check("guard: a regressed count that disagrees with the decisions is refused",
      msg is not None and "tests.regressed is 2" in msg)
msg = refused(lambda s: s["project"].__setitem__("contact", "someone@example.com"))
check("guard: an email address is refused", msg is not None and "email" in msg)
msg = refused(lambda s: s["project"].__setitem__("id", "00000000-cccc-0000-0000-000000000001"))
check("guard: a uuid is refused", msg is not None and "uuid" in msg)
msg = refused(lambda s: s["project"].__setitem__("checkout", "/srv/example/support-triage"))
check("guard: an absolute path is refused", msg is not None and "absolute path" in msg)
msg = refused(lambda s: s["project"].__setitem__("workspace_id", "wrkspc_000000000000"))
check("guard: a workspace id is refused", msg is not None and "workspace" in msg)

# -- the fixture carries nothing personal -----------------------------------
raw = (HERE / "fixtures" / "support-triage-repo.json").read_text()
check("fixture: no uuid",
      not re.search(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", raw, re.I))
check("fixture: no workspace or organization id",
      not re.search(r"wrkspc[-_]|org[-_][A-Za-z0-9]{6,}|sk-ant-", raw))
check("fixture: no email address", not re.search(r"[\w.+-]+@[\w-]+\.[\w.-]+", raw))
check("fixture: no absolute path",
      not re.search(r'"(/|~/|[A-Za-z]:\\\\)|/(Users|home)/', raw))
check("fixture: says the scenario is seeded and no repository is read",
      "seeded" in scenario["_comment"] and "no repository is read" in scenario["_comment"])

print()
if FAIL:
    print(f"{len(FAIL)} failing: {FAIL}")
    raise SystemExit(1)
print("all invariants hold")
