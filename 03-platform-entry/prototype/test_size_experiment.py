#!/usr/bin/env python3
"""Invariants for size_experiment. Run: python3 test_size_experiment.py

Two kinds of check here. The first is that the statistics are right, because the
whole case rests on how much traffic a decision needs. The second is that the tool
refuses to look more certain than it is: the swept inputs must stay swept, and the
fixture must carry no account data.
"""

import json
import pathlib
import re

import size_experiment as s

FAIL = []
HERE = pathlib.Path(__file__).parent
FIXTURE = HERE / "fixtures" / "experiment.json"


def check(name, cond, detail=""):
    if cond:
        print("  pass  %s" % name)
    else:
        FAIL.append(name)
        print("  FAIL  %s %s" % (name, detail))


cfg = json.loads(FIXTURE.read_text())
rep = s.build_report(cfg)

# --- the statistics ---------------------------------------------------------

# Textbook two-proportion sizing, 0.5% vs 1.0% at alpha .05 / power .80, lands
# near 4,700 per arm. Computed independently of the tool's own sweep.
n = s.sample_size_per_arm(0.005, 1.0, 0.05, 0.80)
check("100% lift on 0.5% baseline sizes near 4,700/arm", 4500 <= n <= 4900, f"got {n:,}")

check(
    "a bigger effect needs less traffic",
    s.sample_size_per_arm(0.005, 0.50, 0.05, 0.80)
    < s.sample_size_per_arm(0.005, 0.25, 0.05, 0.80),
)

check(
    "a higher baseline needs less traffic",
    s.sample_size_per_arm(0.020, 0.25, 0.05, 0.80)
    < s.sample_size_per_arm(0.005, 0.25, 0.05, 0.80),
)

check(
    "more power needs more traffic",
    s.sample_size_per_arm(0.005, 0.25, 0.05, 0.95)
    > s.sample_size_per_arm(0.005, 0.25, 0.05, 0.80),
)

try:
    s.sample_size_per_arm(0.6, 1.0, 0.05, 0.80)
    check("a lift past 100% is refused", False, "accepted p2 > 1")
except ValueError:
    check("a lift past 100% is refused", True)

# --- the funnel and the money ----------------------------------------------

f = rep["funnel"]
expected = f["click_to_org"] * f["org_to_first_call"] * f["first_call_to_day30"]
check("compounded rate is the product of its stages", abs(rep["click_to_payer"] - expected) < 1e-12)

check(
    "no stage rate silently exceeds 1",
    all(0.0 < v <= 1.0 for v in f.values()),
    str(f),
)

doubled = s.incremental_annual_usd(200_000, 0.005, 0.25, f, 100)
single = s.incremental_annual_usd(100_000, 0.005, 0.25, f, 100)
check("revenue is linear in impressions", abs(doubled - 2 * single) < 1e-6)

check(
    "run rate compounds the daily sweep over a year",
    all(r["annual_impressions"] == r["daily_sessions"] * 365 for r in rep["run_rate"]),
)

# --- the tool must not fake certainty ---------------------------------------

check(
    "eligible traffic is swept, not asserted",
    len(rep["run_rate"]) > 1 and len({r["daily_sessions"] for r in rep["run_rate"]}) > 1,
)

check(
    "spend per converted caller is swept, not asserted",
    len(rep["per_100k_impressions"]) > 1,
)

check(
    "the fixture says its rates are assumptions",
    "_provenance" in cfg and "synthetic" in cfg["_provenance"].lower(),
)

# --- privacy: the repo is public -------------------------------------------

raw = FIXTURE.read_text()
check(
    "fixture carries no uuid",
    not re.search(r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}", raw),
)
check("fixture carries no email", not re.search(r"[\w.+-]+@[\w-]+\.[\w.]+", raw))
check("fixture carries no bearer token or key", not re.search(r"sk-[A-Za-z0-9_-]{8,}", raw))

print()
if FAIL:
    print("%d failed: %s" % (len(FAIL), ", ".join(FAIL)))
    raise SystemExit(1)
print("all invariants hold")
