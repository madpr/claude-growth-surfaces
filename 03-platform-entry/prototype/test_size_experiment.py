#!/usr/bin/env python3
"""Invariants for size_experiment. Run: python3 test_size_experiment.py

Two kinds of check. The first is that the statistics are right, because the case rests
on how much traffic a decision needs. The second is that the tool predicts nothing: a
forecast built from invented conversion rates would pass a "the prototype printed it"
check while being worth less than no number at all, so several of these assert the
absence of one.
"""

import json
import pathlib
import re

import size_experiment as s

FAIL = []
FIXTURE = pathlib.Path(__file__).parent / "fixtures" / "experiment.json"


def check(name, cond, detail=""):
    if cond:
        print("  pass  %s" % name)
    else:
        FAIL.append(name)
        print("  FAIL  %s %s" % (name, detail))


raw = FIXTURE.read_text()
cfg = json.loads(raw)
rep = s.build_report(cfg)

# --- the statistics ---------------------------------------------------------

n = s.sample_size_per_arm(0.005, 1.0, 0.05, 0.80)
check("100% lift on 0.5% baseline sizes near 4,700/arm", 4500 <= n <= 4900, f"got {n:,}")

check(
    "a bigger effect needs less traffic",
    s.sample_size_per_arm(0.005, 0.50, 0.05, 0.80) < s.sample_size_per_arm(0.005, 0.25, 0.05, 0.80),
)
check(
    "a higher baseline needs less traffic",
    s.sample_size_per_arm(0.020, 0.25, 0.05, 0.80) < s.sample_size_per_arm(0.005, 0.25, 0.05, 0.80),
)
check(
    "more power needs more traffic",
    s.sample_size_per_arm(0.005, 0.25, 0.05, 0.95) > s.sample_size_per_arm(0.005, 0.25, 0.05, 0.80),
)
check(
    "more traffic reaches a decision sooner",
    s.days_to_decision(50_000, 2, 100_000) < s.days_to_decision(50_000, 2, 5_000),
)

try:
    s.sample_size_per_arm(0.6, 1.0, 0.05, 0.80)
    check("a lift past 100% is refused", False, "accepted p2 > 1")
except ValueError:
    check("a lift past 100% is refused", True)

# --- the tool must predict nothing -----------------------------------------

# Inspect the fixture's DATA, not its prose. The provenance note names the things it
# refuses to contain, so a raw-text search would flag the very sentence promising their
# absence. Keys starting with "_" are commentary and are skipped.
BANNED = (
    "click_to_org", "org_to_first_call", "first_call_to_day30", "funnel",
    "arpu", "revenue", "conversion", "payer", "target", "usd",
)


def data_keys(node, acc=None):
    acc = [] if acc is None else acc
    if isinstance(node, dict):
        for k, v in node.items():
            if k.startswith("_"):
                continue
            acc.append(k.lower())
            data_keys(v, acc)
    elif isinstance(node, list):
        for v in node:
            data_keys(v, acc)
    return acc


keys = data_keys(cfg)
for term in BANNED:
    check(f"fixture holds no {term} input", not any(term in k for k in keys), str(keys))

check(
    "no revenue key reaches the report",
    not any(k in rep for k in ("revenue", "run_rate", "requirement", "click_to_payer")),
    str(sorted(rep.keys())),
)

# --- unknowns are swept, never asserted as a point -------------------------

check("baseline click-through is swept", len(rep["sizing"]) > 1)
check("effect size is swept", len(rep["mde_sweep"]) > 1)
check("eligible traffic is swept", len(rep["traffic_sweep"]) > 1)
check(
    "the fixture says the reporting effect is a choice, not a prediction",
    "not a prediction" in raw,
)
check("the fixture states it predicts nothing", "predicts nothing" in raw)

# --- privacy: the repo is public -------------------------------------------

check("fixture carries no uuid", not re.search(r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}", raw))
check("fixture carries no email", not re.search(r"[\w.+-]+@[\w-]+\.[\w.]+", raw))
check("fixture carries no bearer token or key", not re.search(r"sk-[A-Za-z0-9_-]{8,}", raw))

print()
if FAIL:
    print("%d failed: %s" % (len(FAIL), ", ".join(FAIL)))
    raise SystemExit(1)
print("all invariants hold")
