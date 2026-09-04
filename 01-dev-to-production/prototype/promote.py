#!/usr/bin/env python3
"""
Promote: turn a working Claude Code project into the Managed Agents resources
that would run it unattended, and name every field that does not survive.

Claude Code and the Claude Developer Platform are two command-line tools that
divide one account and cannot see each other. `claude` is where developers work;
`ant` owns the hosted-agent control plane and is the documented way to drive it:

    ant beta:agents create < agent.yaml
    ant beta:environments create < environment.yaml
    ant beta:deployments create < deployment.yaml

Neither binary has a verb pointing at the other. `claude import` acquires config
from competing agents; there is no outbound equivalent, and `ant` has no reference
to Claude Code anywhere in its agent, environment or deployment surface.

This is the missing verb, run locally against a project directory.

    ./promote.py map  fixtures/ledger-reconcile
    ./promote.py emit fixtures/ledger-reconcile
    ./promote.py emit fixtures/ledger-reconcile --json
    ./promote.py size

`map` reports what each Managed Agents field resolves to, and why the ones that
do not, do not. `emit` writes the YAML bodies `ant` accepts on stdin. `size`
prints what one promoted workload bills per month at list price, tokens only,
swept over the two inputs nobody outside Anthropic can know. It reads nothing.
It is an illustration, not a forecast.

The point of the exercise is the honesty of the mapping, not the volume of it.
Six of the seven meaningful `ant beta:agents create` fields have a direct source
in a working Claude Code project. The interesting output is the remainder, which
falls into four kinds:

    lossy        maps, but drops detail the local config carried
    human        no local source; a person has to supply it
    blocked      the local value cannot be expressed on the target at all
    underivable  a laptop structurally cannot supply it

`blocked` and `underivable` are the two that matter. A stdio MCP server -- one
Claude Code launches as a subprocess -- has no representation on a hosted agent,
because Managed Agents MCP servers are `type: "url"` over Streamable HTTP and
nothing else. And an environment is a sandbox, which is the one thing a developer
machine cannot hand over.

One field is missing from this tool because it is missing from the product: the
destination org. Claude Code authenticates through claude.ai against a
subscription; `ant` authenticates through the developer platform against a
separate organization. On the account this was built against they were two
different org IDs for one email address, so the resources emitted here target an
organization the developer is not logged into. That boundary is reported, not
crossed -- see `check_identity()`.

Verified 2-3 September 2026 against Claude Code 2.1.259 and ant 1.29.0:
  ant beta:agents create --help          (the seven fields)
  claude --help, claude agents --help    (the vocabulary collision)
  shared/managed-agents-tools.md         (mcp_toolset is url-only;
                                          agent_toolset_20260401 per-tool configs)

Reads a directory. Makes no API calls and touches no account. Stdlib only.
"""

import json
import os
import sys

# ---------------------------------------------------------------------------
# Model aliases. Claude Code accepts short aliases; ant wants a model id.
# ---------------------------------------------------------------------------

MODEL_ALIASES = {
    "opus": "claude-opus-5",
    "sonnet": "claude-sonnet-5",
    "haiku": "claude-haiku-4-5",
    "fable": "claude-fable-5-1",
}

# The prebuilt hosted toolset: file ops, bash, web search, code execution.
AGENT_TOOLSET = "agent_toolset_20260401"

# Claude Code built-ins that the hosted toolset covers. Names as Claude Code
# spells them, mapped to the tool names the agent toolset reports.
TOOL_EQUIVALENTS = {
    "Bash": "bash",
    "Read": "read_file",
    "Write": "write_file",
    "Edit": "edit_file",
    "Glob": "glob",
    "Grep": "grep",
    "WebFetch": "web_fetch",
    "WebSearch": "web_search",
}

RESOLVED, LOSSY, HUMAN, BLOCKED, UNDERIVABLE = (
    "resolved", "lossy", "human", "blocked", "underivable")

ORDER = [RESOLVED, LOSSY, HUMAN, BLOCKED, UNDERIVABLE]


def _finding(field, status, value=None, source=None, note=None):
    return {"field": field, "status": status, "value": value,
            "source": source, "note": note}


# ---------------------------------------------------------------------------
# Reading a Claude Code project
# ---------------------------------------------------------------------------

def read_project(root):
    """Collect the Claude Code configuration a project carries on disk."""
    proj = {"root": os.path.abspath(root), "name": os.path.basename(
        os.path.abspath(root))}

    claude_md = os.path.join(root, "CLAUDE.md")
    proj["claude_md"] = (open(claude_md).read()
                         if os.path.isfile(claude_md) else None)

    settings = os.path.join(root, ".claude", "settings.json")
    proj["settings"] = _load_json(settings) or {}

    mcp = os.path.join(root, ".mcp.json")
    proj["mcp"] = _load_json(mcp) or {}

    proj["skills"] = _list_skills(os.path.join(root, ".claude", "skills"))
    proj["subagents"] = _list_subagents(os.path.join(root, ".claude", "agents"))
    return proj


def _load_json(path):
    if not os.path.isfile(path):
        return None
    try:
        return json.loads(open(path).read())
    except json.JSONDecodeError:
        return None


def _list_skills(d):
    if not os.path.isdir(d):
        return []
    return sorted(n for n in os.listdir(d)
                  if os.path.isfile(os.path.join(d, n, "SKILL.md")))


def _list_subagents(d):
    if not os.path.isdir(d):
        return []
    return sorted(n[:-3] for n in os.listdir(d) if n.endswith(".md"))


# ---------------------------------------------------------------------------
# The mapping, field by field
# ---------------------------------------------------------------------------

def map_fields(proj):
    """Return one finding per Managed Agents agent field."""
    out = [_map_name(proj), _map_model(proj), _map_system(proj)]
    out.extend(_map_tools(proj))
    out.extend(_map_mcp(proj))
    out.append(_map_skills(proj))
    out.append(_map_description(proj))
    out.append(_map_environment(proj))
    return out


def _map_name(proj):
    return _finding("name", RESOLVED, proj["name"], "directory name")


def _map_model(proj):
    raw = proj["settings"].get("model")
    if not raw:
        return _finding("model", HUMAN, None, None,
                        "no model pinned in .claude/settings.json; the session "
                        "default is a client preference, not project config")
    resolved = MODEL_ALIASES.get(raw, raw)
    if resolved != raw:
        return _finding("model", RESOLVED, resolved,
                        ".claude/settings.json model=%s" % raw,
                        "alias resolved to a model id; ant takes ids, not aliases")
    return _finding("model", RESOLVED, resolved, ".claude/settings.json")


def _map_system(proj):
    if not proj["claude_md"]:
        return _finding("system", HUMAN, None, None, "no CLAUDE.md in the project")
    text = proj["claude_md"]
    return _finding("system", RESOLVED, text, "CLAUDE.md",
                    "%d chars; CLAUDE.md is the project's standing instruction "
                    "and is what a hosted agent needs as its system prompt"
                    % len(text))


def _map_tools(proj):
    """Claude Code permissions -> agent_toolset_20260401 per-tool configs."""
    perms = proj["settings"].get("permissions", {})
    allow, deny = perms.get("allow", []), perms.get("deny", [])
    findings = []

    bare_deny = [r for r in deny if "(" not in r]
    patterned = [r for r in allow + deny if "(" in r]

    configs = [{"name": TOOL_EQUIVALENTS[r], "enabled": False}
               for r in bare_deny if r in TOOL_EQUIVALENTS]
    findings.append(_finding(
        "tools", RESOLVED if not patterned else LOSSY,
        {"type": AGENT_TOOLSET, "configs": configs} if configs
        else {"type": AGENT_TOOLSET},
        ".claude/settings.json permissions",
        "tool-level enable/disable survives via the toolset's `configs`"
        + ("" if not patterned else
           "; %d command-pattern rule(s) do not -- the toolset enables or "
           "disables a whole tool and has no equivalent of %s"
           % (len(patterned), ", ".join(repr(p) for p in patterned[:3])))))

    if patterned:
        findings.append(_finding(
            "permissions (command patterns)", BLOCKED, patterned,
            ".claude/settings.json permissions",
            "containment at this granularity is an environment property on the "
            "target -- the sandbox and vault egress substitution -- not an "
            "agent property, so it cannot ride along on the agent"))
    return findings


def _map_mcp(proj):
    """Managed Agents MCP servers are type:url only. stdio cannot travel."""
    servers = proj["mcp"].get("mcpServers", {})
    if not servers:
        return [_finding("mcp_servers", RESOLVED, [], None, "none configured")]

    remote, local = [], []
    for name, spec in sorted(servers.items()):
        if spec.get("url"):
            remote.append({"type": "url", "name": name, "url": spec["url"]})
        else:
            local.append(name)

    findings = [_finding(
        "mcp_servers", RESOLVED if not local else LOSSY, remote,
        ".mcp.json",
        "%d of %d server(s) are URL-based and translate directly"
        % (len(remote), len(servers)))]

    if local:
        findings.append(_finding(
            "mcp_servers (stdio)", BLOCKED, local, ".mcp.json",
            "Managed Agents MCP servers are `type: \"url\"` over Streamable "
            "HTTP; a server Claude Code launches as a local subprocess has no "
            "representation on a hosted agent and must be published as an "
            "endpoint first"))
    return findings


def _map_skills(proj):
    skills = proj["skills"]
    if not skills:
        return _finding("skills", RESOLVED, [], None, "none in .claude/skills")
    return _finding("skills", LOSSY, skills, ".claude/skills/*/SKILL.md",
                    "skill names carry over, but each must be uploaded to the "
                    "Skills API and referenced by id -- the local directory is "
                    "not a source the platform can read")


def _map_description(proj):
    return _finding("description", HUMAN, None, None,
                    "no local source; nothing in a Claude Code project states "
                    "what the agent is for in one line")


def _map_environment(proj):
    return _finding("environment", UNDERIVABLE, None, None,
                    "an environment is a sandbox: a container image, network "
                    "policy and credential vaults. A developer machine has none "
                    "of these to hand over, and it is the reason the hosted "
                    "surface is worth reaching in the first place")


# ---------------------------------------------------------------------------
# The boundary this tool reports and does not cross
# ---------------------------------------------------------------------------

def check_identity(auth_state):
    """Compare the org Claude Code is in against the org ant is in.

    Takes a captured auth state rather than calling either binary, so this
    reads no account. Returns None when the two agree.
    """
    cc = (auth_state or {}).get("claude_code", {})
    plat = (auth_state or {}).get("platform", {})
    if not cc or not plat:
        return None
    if cc.get("organization_id") == plat.get("organization_id"):
        return None
    return {
        "claude_code": cc,
        "platform": plat,
        "note": "the resources emitted here target an organization the "
                "developer is not logged into from Claude Code. Promotion "
                "crosses an identity boundary, not just a binary boundary.",
    }


# ---------------------------------------------------------------------------
# Emitting what ant accepts
# ---------------------------------------------------------------------------

def build_agent(findings):
    """The agent body, carrying only fields that actually resolved."""
    by = {f["field"]: f for f in findings}
    body = {}
    for field in ("name", "model", "system"):
        f = by.get(field)
        if f and f["status"] in (RESOLVED, LOSSY) and f["value"]:
            body[field] = f["value"]

    tools = by.get("tools")
    if tools and tools["value"]:
        body["tools"] = [tools["value"]]

    mcp = by.get("mcp_servers")
    if mcp and mcp["value"]:
        body["mcp_servers"] = mcp["value"]
        body.setdefault("tools", []).extend(
            {"type": "mcp_toolset", "mcp_server_name": s["name"]}
            for s in mcp["value"])
    return body


def to_yaml(obj, indent=0):
    """Minimal YAML writer for the shapes emitted here. Stdlib only."""
    pad = "  " * indent
    if isinstance(obj, dict):
        lines = []
        for k, v in obj.items():
            if isinstance(v, str) and "\n" in v:
                lines.append("%s%s: |" % (pad, k))
                lines.extend(("%s  %s" % (pad, ln)) if ln.strip() else ""
                             for ln in v.rstrip("\n").split("\n"))
            elif isinstance(v, (dict, list)) and v:
                lines.append("%s%s:" % (pad, k))
                lines.append(to_yaml(v, indent + 1))
            else:
                lines.append("%s%s: %s" % (pad, k, _scalar(v)))
        return "\n".join(lines)
    if isinstance(obj, list):
        lines = []
        for item in obj:
            if isinstance(item, dict):
                inner = to_yaml(item, indent + 1)
                first, rest = inner.split("\n", 1) if "\n" in inner else (inner, "")
                lines.append("%s- %s" % (pad, first.strip()))
                if rest:
                    lines.append(rest)
            else:
                lines.append("%s- %s" % (pad, _scalar(item)))
        return "\n".join(lines)
    return "%s%s" % (pad, _scalar(obj))


def _scalar(v):
    if v is None:
        return "null"
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, (int, float)):
        return str(v)
    s = str(v)
    if s == "" or any(c in s for c in ":#{}[],&*?|<>=!%@`\"'") or s.strip() != s:
        return json.dumps(s)
    return s


# ---------------------------------------------------------------------------
# What one promoted workload is worth. This is the arithmetic the first
# milestone exists to replace, not a forecast.
# ---------------------------------------------------------------------------

# List price for the model the fixture pins (settings.json model=sonnet
# resolves to claude-sonnet-5). Fetched 2026-09-03 from
#   https://platform.claude.com/docs/en/about-claude/pricing
# which is the redirect target of
#   https://docs.claude.com/en/docs/about-claude/pricing
# The model table on that page reads, for Claude Sonnet 5: base input tokens
# $2 / MTok, output tokens $10 / MTok. A note on the same page says the $2/$10
# introductory price is now the standard price. The same page bills Managed
# Agents session runtime at $0.08 per session-hour on top of tokens; run
# duration is a third unknown, so runtime is named below and not priced.
PRICE = {
    "model": "Claude Sonnet 5",
    "model_id": "claude-sonnet-5",
    "input_per_mtok": 2.00,
    "output_per_mtok": 10.00,
    "runtime_per_session_hour": 0.08,
    "source": "https://platform.claude.com/docs/en/about-claude/pricing",
    "retrieved": "2026-09-03",
}

# Neither axis is knowable from outside Anthropic, so both are swept. Runs per
# night is swept because a schedule can fan out.
INPUT_TOKENS_PER_RUN_SWEEP = [200_000, 1_000_000, 5_000_000]
RUNS_PER_NIGHT_SWEEP = [1, 3, 10]
NIGHTS_PER_MONTH = 30

# Output is fixed rather than swept, at one tenth of input per run. At the
# prices above that puts output at one third of every cell. Input and output
# are both priced uncached; no cache hit rate is assumed.
OUTPUT_SHARE_OF_INPUT = 0.1


def cost_per_run(input_tokens, price=PRICE, output_share=OUTPUT_SHARE_OF_INPUT):
    """Token cost of one run at list price, uncached input and output."""
    output_tokens = input_tokens * output_share
    return (input_tokens * price["input_per_mtok"]
            + output_tokens * price["output_per_mtok"]) / 1_000_000


def size_report(price=PRICE, inputs=INPUT_TOKENS_PER_RUN_SWEEP,
                runs=RUNS_PER_NIGHT_SWEEP, nights=NIGHTS_PER_MONTH,
                output_share=OUTPUT_SHARE_OF_INPUT):
    """Monthly token cost of one agent, swept over both unknowable axes.

    Reads nothing: no project, no fixture, no account.
    """
    cells = [
        {"input_tokens_per_run": i,
         "per_month": {r: cost_per_run(i, price, output_share) * r * nights
                       for r in runs}}
        for i in inputs
    ]
    return {"price": dict(price), "nights_per_month": nights,
            "output_share_of_input": output_share,
            "input_sweep": list(inputs), "runs_sweep": list(runs),
            "cells": cells}


def _usd(x):
    return "${:,.2f}".format(x)


def _rate(x):
    return "${:g}".format(x)


def render_size(rep):
    p = rep["price"]
    runs = rep["runs_sweep"]
    print()
    print("  One promoted workload, per month, tokens only")
    print("  Illustration. No account read, no API calls, nothing predicted.")
    print()
    print("  === %s at list price, uncached ===" % p["model"])
    print("  %s / MTok input, %s / MTok output"
          % (_rate(p["input_per_mtok"]), _rate(p["output_per_mtok"])))
    print("  %s, retrieved %s" % (p["source"], p["retrieved"]))
    print("  The model is the one the fixture pins: settings model=sonnet")
    print("  resolves to %s." % p["model_id"])
    print()
    print("  === One agent, by input tokens per run and runs per night ===")
    print("  Neither axis is knowable from outside Anthropic, so both are swept.")
    print()
    head = "".join("%15s" % ("%d run%s/night" % (r, "" if r == 1 else "s"))
                   for r in runs)
    print("  %-12s%s" % ("input/run", head))
    for row in rep["cells"]:
        print("  %-12s%s" % ("{:,}".format(row["input_tokens_per_run"]),
                             "".join("%15s" % _usd(row["per_month"][r])
                                     for r in runs)))
    print()
    print("  %d nights per month. Output is fixed at one tenth of input per run,"
          % rep["nights_per_month"])
    print("  not swept; at these prices that is one third of every cell.")
    print("  Session runtime bills on top at %s per session-hour, from the"
          % _rate(p["runtime_per_session_hour"]))
    print("  same page, and is not priced here: run duration is a third unknown.")
    print()
    print("  What this tool will not tell you: whether any workload moves, or")
    print("  how many. Those are what the first milestone measures. Predicting")
    print("  them here would substitute arithmetic for that measurement.")
    print()


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------

LABEL = {
    RESOLVED: "resolved",
    LOSSY: "lossy",
    HUMAN: "human",
    BLOCKED: "blocked",
    UNDERIVABLE: "underivable",
}


def _wrap(text, width):
    words, line, out = text.split(), "", []
    for w in words:
        if line and len(line) + 1 + len(w) > width:
            out.append(line)
            line = w
        else:
            line = w if not line else line + " " + w
    if line:
        out.append(line)
    return out


def render_map(findings, identity):
    counts = {s: 0 for s in ORDER}
    for f in findings:
        counts[f["status"]] += 1

    print()
    print("  Claude Code project  ->  Managed Agents agent")
    print("  " + "-" * 58)
    print()

    for f in findings:
        val = f["value"]
        if isinstance(val, str):
            shown = val.split("\n")[0][:44] + ("…" if len(val) > 44 else "")
        elif isinstance(val, (list, dict)):
            shown = json.dumps(val)[:44] + ("…" if len(json.dumps(val)) > 44 else "")
        else:
            shown = "—"
        print("  %-11s %-30s %s" % (LABEL[f["status"]], f["field"], shown))
        if f["source"]:
            print("  %-11s %-30s from %s" % ("", "", f["source"]))
        if f["note"]:
            for i, line in enumerate(_wrap(f["note"], 56)):
                print("  %-11s   %s" % ("", line))
        print()

    print("  " + "-" * 58)
    print("  " + "   ".join("%s %d" % (LABEL[s], counts[s])
                            for s in ORDER if counts[s]))
    print()

    if identity:
        print("  identity boundary")
        print("  " + "-" * 58)
        print("    claude  org %s  (%s)" % (
            identity["claude_code"].get("organization_id", "?"),
            identity["claude_code"].get("auth_method", "?")))
        print("    ant     org %s  (%s)" % (
            identity["platform"].get("organization_id", "?"),
            identity["platform"].get("auth_method", "?")))
        for line in _wrap(identity["note"], 56):
            print("      %s" % line)
        print()


def render_emit(agent, findings, identity):
    print("# agent.yaml — apply with:  ant beta:agents create < agent.yaml")
    print(to_yaml(agent))
    print()
    # Anything the body does not carry is reported, whatever its status --
    # a lossy field that could not be expressed is as absent as a blocked one.
    unmet = [f for f in findings if f["field"] not in agent]
    if unmet:
        print("# not emitted, and why:")
        for f in unmet:
            print("#   %-30s %s" % (f["field"], LABEL[f["status"]]))
            for line in _wrap(f["note"] or "", 62):
                print("#     %s" % line)
    if identity:
        print("#")
        print("# destination org differs from the org Claude Code is signed in to.")
        print("#   claude %s / ant %s" % (
            identity["claude_code"].get("organization_id", "?"),
            identity["platform"].get("organization_id", "?")))


# ---------------------------------------------------------------------------

def main(argv):
    args = [a for a in argv[1:] if not a.startswith("--")]
    flags = {a for a in argv[1:] if a.startswith("--")}

    if not args or args[0] not in ("map", "emit", "size"):
        print(__doc__.strip().split("\n\n")[0], file=sys.stderr)
        print("\nusage: promote.py {map|emit} <project-dir> [--json]\n"
              "       promote.py size [--json]", file=sys.stderr)
        return 2

    mode = args[0]
    if mode == "size":
        rep = size_report()
        if "--json" in flags:
            print(json.dumps(rep, indent=2))
        else:
            render_size(rep)
        return 0

    root = args[1] if len(args) > 1 else "."
    if not os.path.isdir(root):
        print("error: %s is not a directory" % root, file=sys.stderr)
        return 2

    proj = read_project(root)
    findings = map_fields(proj)
    identity = check_identity(_load_json(
        os.path.join(os.path.dirname(os.path.abspath(__file__)),
                     "fixtures", "auth-state.json")))

    if "--json" in flags:
        print(json.dumps({"project": proj["name"], "findings": findings,
                          "agent": build_agent(findings),
                          "identity_boundary": identity}, indent=2))
    elif mode == "map":
        render_map(findings, identity)
    else:
        render_emit(build_agent(findings), findings, identity)

    blocked = sum(1 for f in findings
                  if f["status"] in (BLOCKED, UNDERIVABLE))
    return 1 if blocked else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
