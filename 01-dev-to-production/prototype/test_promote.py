#!/usr/bin/env python3
"""Invariants for promote. Run: python3 test_promote.py

The invariants that matter here are the negative ones. A promoter that quietly
emits a plausible agent is worse than no promoter, because the fields it dropped
are the ones that were holding the work on the laptop. Most of these assert that
something is *refused*, not that something is produced.
"""

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

print()
if FAIL:
    print("%d FAILED: %s" % (len(FAIL), ", ".join(FAIL)))
    raise SystemExit(1)
print("all passed")
