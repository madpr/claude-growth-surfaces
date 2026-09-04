#!/usr/bin/env python3
"""Invariants for promote. Run: python3 test_promote.py

The invariants that matter here are the negative ones. A promoter that quietly
emits a plausible agent is worse than no promoter, because the fields it dropped
are the ones that were holding the work on the laptop. Most of these assert that
something is *refused*, not that something is produced.
"""

import contextlib
import io
import json
import re
import os
import shutil
import tempfile

import promote as p

FAIL = []
HERE = os.path.dirname(os.path.abspath(__file__))
FIXTURE = os.path.join(HERE, "fixtures", "ledger-reconcile")


def check(name, cond, detail=""):
    if cond:
        print("  pass  %s" % name)
    else:
        FAIL.append(name)
        print("  FAIL  %s %s" % (name, detail))


def by_field(findings):
    return {f["field"]: f for f in findings}


def project(**files):
    """Build a throwaway Claude Code project directory."""
    root = tempfile.mkdtemp()
    for rel, body in files.items():
        path = os.path.join(root, rel)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        open(path, "w").write(body)
    return root


# --- the fixture project, end to end -------------------------------------

print("\nfixture project")
proj = p.read_project(FIXTURE)
found = p.map_fields(proj)
f = by_field(found)

check("reads CLAUDE.md as the system prompt",
      f["system"]["status"] == p.RESOLVED and "reconciliation" in f["system"]["value"])
check("resolves the model alias to an id",
      f["model"]["value"] == "claude-sonnet-5",
      "got %r" % f["model"]["value"])
check("names the agent from the directory",
      f["name"]["value"] == "ledger-reconcile")
check("every finding carries a status the renderer knows",
      all(x["status"] in p.LABEL for x in found))
check("every unresolved finding explains itself",
      all(x["note"] for x in found if x["status"] != p.RESOLVED))

# --- the refusals --------------------------------------------------------

print("\nrefusals")
check("stdio MCP servers are blocked, not silently dropped",
      f["mcp_servers (stdio)"]["status"] == p.BLOCKED
      and "local-fs-index" in f["mcp_servers (stdio)"]["value"])
check("url MCP servers still translate",
      any(s["name"] == "ledger-db" for s in f["mcp_servers"]["value"]))
check("a stdio server never reaches the emitted body",
      "local-fs-index" not in json.dumps(p.build_agent(found)))
check("command-pattern permissions are blocked",
      f["permissions (command patterns)"]["status"] == p.BLOCKED)
check("no command pattern leaks into the emitted body",
      "rm *" not in json.dumps(p.build_agent(found)))
check("environment is underivable, never invented",
      f["environment"]["status"] == p.UNDERIVABLE
      and f["environment"]["value"] is None)
check("description is left to a human",
      f["description"]["status"] == p.HUMAN)
check("emitted body carries no null-valued field",
      all(v is not None for v in p.build_agent(found).values()))

# --- tools -------------------------------------------------------------

print("\ntools")
check("a denied bare tool becomes a disabled config",
      any(c["name"] == "web_search" and c["enabled"] is False
          for c in f["tools"]["value"].get("configs", [])))
check("tools are lossy when command patterns are present",
      f["tools"]["status"] == p.LOSSY)

clean = project(**{".claude/settings.json": json.dumps(
    {"model": "opus", "permissions": {"deny": ["WebSearch"]}})})
try:
    cf = by_field(p.map_fields(p.read_project(clean)))
    check("tools are resolved when no command patterns exist",
          cf["tools"]["status"] == p.RESOLVED, "got %s" % cf["tools"]["status"])
    check("no command-pattern finding is raised when there are none",
          "permissions (command patterns)" not in cf)
    check("opus alias resolves", cf["model"]["value"] == "claude-opus-5")
finally:
    shutil.rmtree(clean)

# --- an empty project ----------------------------------------------------

print("\nempty project")
empty = project(**{"README.md": "nothing to see"})
try:
    ef = by_field(p.map_fields(p.read_project(empty)))
    check("missing CLAUDE.md is human, not an empty prompt",
          ef["system"]["status"] == p.HUMAN and ef["system"]["value"] is None)
    check("missing model is human, not a guessed default",
          ef["model"]["status"] == p.HUMAN and ef["model"]["value"] is None)
    check("an empty project emits no system field",
          "system" not in p.build_agent(p.map_fields(p.read_project(empty))))
    check("environment stays underivable even with nothing configured",
          ef["environment"]["status"] == p.UNDERIVABLE)
finally:
    shutil.rmtree(empty)

# --- malformed input -----------------------------------------------------

print("\nmalformed input")
bad = project(**{".mcp.json": "{not json", ".claude/settings.json": "{also not"})
try:
    bf = by_field(p.map_fields(p.read_project(bad)))
    check("unparseable .mcp.json yields no servers rather than a crash",
          bf["mcp_servers"]["value"] == [])
    check("unparseable settings.json falls back to human model",
          bf["model"]["status"] == p.HUMAN)
finally:
    shutil.rmtree(bad)

# --- the identity boundary ----------------------------------------------

print("\nidentity boundary")
same = {"claude_code": {"organization_id": "x"},
        "platform": {"organization_id": "x"}}
diff = {"claude_code": {"organization_id": "x"},
        "platform": {"organization_id": "y"}}
check("matching orgs report no boundary", p.check_identity(same) is None)
check("differing orgs report a boundary", p.check_identity(diff) is not None)
check("a missing auth state is not treated as agreement",
      p.check_identity(None) is None and p.check_identity({}) is None)
# Assert a synthetic *shape* rather than listing real values -- a test that
# hardcodes the identifiers it is guarding against leaks them itself.
_auth = open(os.path.join(HERE, "fixtures", "auth-state.json")).read()
check("every uuid in the auth fixture is obviously synthetic",
      all(u.startswith("00000000-") for u in
          re.findall(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}",
                     _auth)))
check("every workspace id in the auth fixture is obviously synthetic",
      all(w.startswith("wrkspc_EXAMPLE")
          for w in re.findall(r"wrkspc_[A-Za-z0-9]+", _auth)))
check("the auth fixture carries no email address",
      not re.search(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", _auth))

# --- YAML ---------------------------------------------------------------

print("\nyaml")
y = p.to_yaml(p.build_agent(found))
check("multi-line system uses a block scalar", "system: |" in y)
check("no blank line in a block scalar carries trailing space",
      not any(line != line.rstrip() for line in y.split("\n")))
check("a url containing a colon is quoted",
      '"https://internal.example.com/mcp/ledger"' in y)
check("list items nest under their key",
      "mcp_servers:" in y and "- type: url" in y)
check("emitted yaml has no tab characters", "\t" not in y)

# --- the size table -----------------------------------------------------
# The table is an illustration at list price. What these pin is that the
# figures the README quotes are the ones this code prints, that the price is
# the fetched one, that both unknowable axes stay swept, and that nothing from
# an account reaches the output.

print("\nsize table")
rep = p.size_report()
cell = {c["input_tokens_per_run"]: c["per_month"] for c in rep["cells"]}
check("one run a night at 200k input bills $18.00 a month",
      abs(cell[200_000][1] - 18.00) < 1e-9, "got %r" % cell[200_000][1])
check("three runs a night at 1M input bill $270.00 a month",
      abs(cell[1_000_000][3] - 270.00) < 1e-9, "got %r" % cell[1_000_000][3])
check("ten runs a night at 5M input bill $4,500.00 a month",
      abs(cell[5_000_000][10] - 4500.00) < 1e-9,
      "got %r" % cell[5_000_000][10])
check("the price is the fetched figure with its retrieval date, not a guess",
      rep["price"]["input_per_mtok"] == 2.00
      and rep["price"]["output_per_mtok"] == 10.00
      and rep["price"]["retrieved"] == "2026-09-03"
      and rep["price"]["source"].startswith("https://"))
check("both unknowable axes stay swept",
      len(rep["input_sweep"]) >= 3 and len(rep["runs_sweep"]) >= 3)
check("cost is linear in runs per night and in input per run",
      abs(cell[1_000_000][1] * 3 - cell[1_000_000][3]) < 1e-9
      and abs(cell[200_000][1] * 5 - cell[1_000_000][1]) < 1e-9)
check("output is one third of every cell at these prices",
      all(abs(p.cost_per_run(i) * 2 / 3
              - i * p.PRICE["input_per_mtok"] / 1_000_000) < 1e-9
          for i in rep["input_sweep"]))

_buf = io.StringIO()
with contextlib.redirect_stdout(_buf):
    p.render_size(rep)
table = _buf.getvalue()
check("the printed table carries the pinned cells",
      "$18.00" in table and "$270.00" in table and "$4,500.00" in table)
check("the printed table names its price, source, and retrieval date",
      "$2 / MTok input" in table and "$10 / MTok output" in table
      and p.PRICE["source"] in table and "2026-09-03" in table)
check("the printed table says runtime bills on top and is not priced",
      "session-hour" in table and "not priced" in table)
check("the printed table says the price is list and uncached",
      "list price" in table and "uncached" in table)

_auth_state = json.loads(_auth)
_account_values = [
    _auth_state[side][key]
    for side in ("claude_code", "platform")
    for key in ("organization_id", "organization_name")
] + [_auth_state["platform"]["workspace_id"]]
check("the size table carries no account data",
      not re.search(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}",
                    table)
      and "wrkspc_" not in table
      and not re.search(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", table)
      and not any(v in table for v in _account_values))

_buf = io.StringIO()
with contextlib.redirect_stdout(_buf):
    rc = p.main(["promote.py", "size"])
check("size needs no project directory and exits 0",
      rc == 0 and "$270.00" in _buf.getvalue())

print()
if FAIL:
    print("%d FAILED: %s" % (len(FAIL), ", ".join(FAIL)))
    raise SystemExit(1)
print("all passed")
