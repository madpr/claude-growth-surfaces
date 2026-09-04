#!/usr/bin/env python3
"""Size the placement test for a developer-platform row in the claude.ai left rail.

Reads a seeded fixture. Reads no account, makes no API calls, needs no login.

    ./size_experiment.py
    ./size_experiment.py --json

This tool predicts nothing. It answers one question: how much traffic does a decision
cost? Revenue, conversion, and click-through are all outputs of the experiment, not
inputs to it, so none of them appear here. Anything not knowable from outside Anthropic
is swept rather than assumed.
"""

import argparse
import json
import math
import pathlib
import sys
from statistics import NormalDist

FIXTURE = pathlib.Path(__file__).parent / "fixtures" / "experiment.json"


def sample_size_per_arm(p1: float, relative_lift: float, alpha: float, power: float) -> int:
    """Per-arm impressions for a two-proportion test.

    Standard normal approximation: the pooled term carries the null, the unpooled
    term carries the alternative.
    """
    p2 = p1 * (1.0 + relative_lift)
    if not 0.0 < p1 < 1.0 or not 0.0 < p2 < 1.0:
        raise ValueError(f"rates must be in (0,1); got p1={p1}, p2={p2}")

    z_alpha = NormalDist().inv_cdf(1.0 - alpha / 2.0)
    z_power = NormalDist().inv_cdf(power)

    pooled = (p1 + p2) / 2.0
    null_term = z_alpha * math.sqrt(2.0 * pooled * (1.0 - pooled))
    alt_term = z_power * math.sqrt(p1 * (1.0 - p1) + p2 * (1.0 - p2))

    return math.ceil(((null_term + alt_term) ** 2) / ((p2 - p1) ** 2))


def days_to_decision(per_arm: int, arms: int, daily_sessions: int) -> float:
    return (per_arm * arms) / daily_sessions


def build_report(cfg: dict) -> dict:
    test = cfg["test"]
    alpha, power, arms = test["alpha"], test["power"], test["arms"]
    mde = test["reporting_mde"]

    sizing = [
        {
            "baseline_ctr": ctr,
            "per_arm": {m: sample_size_per_arm(ctr, m, alpha, power) for m in test["mde_relative_sweep"]},
        }
        for ctr in test["baseline_ctr_sweep"]
    ]

    runtime = [
        {
            "baseline_ctr": ctr,
            "days": {
                d: days_to_decision(sample_size_per_arm(ctr, mde, alpha, power), arms, d)
                for d in cfg["eligible_traffic"]["daily_sessions_sweep"]
            },
        }
        for ctr in test["baseline_ctr_sweep"]
    ]

    return {
        "alpha": alpha,
        "power": power,
        "arms": arms,
        "reporting_mde": mde,
        "sizing": sizing,
        "runtime": runtime,
        "traffic_sweep": cfg["eligible_traffic"]["daily_sessions_sweep"],
        "mde_sweep": test["mde_relative_sweep"],
    }


def _dur(days: float) -> str:
    if days < 1:
        return f"{days * 24:,.1f} hours"
    if days < 90:
        return f"{days:,.1f} days"
    return f"{days / 30.44:,.1f} months"


def emit(rep: dict) -> None:
    print("Placement test — developer platform row, claude.ai left rail")
    print("Seeded fixture. No account read, no API calls, nothing predicted.\n")

    print("=== 1. Impressions per arm, by effect size you would act on ===")
    mdes = rep["mde_sweep"]
    print("  baseline CTR " + "".join(f"{m:>13.0%}" for m in mdes))
    for row in rep["sizing"]:
        print(f"  {row['baseline_ctr']:>11.2%}" + "".join(f"{row['per_arm'][m]:>13,}" for m in mdes))
    print(f"\n  alpha {rep['alpha']}, power {rep['power']:.0%}, {rep['arms']} arms, two-sided.")
    print("  The baseline is measurable today: both existing links already carry")
    print("  tracking tags. Read the row that matches it.")

    print(f"\n=== 2. Time to a decision at a {rep['reporting_mde']:.0%} effect ===")
    print("  Eligible traffic is not knowable from outside Anthropic, so it is swept.")
    traffic = rep["traffic_sweep"]
    print("  baseline CTR " + "".join(f"{(f'{d:,}/day'):>16}" for d in traffic))
    for row in rep["runtime"]:
        print(f"  {row['baseline_ctr']:>11.2%}" + "".join(f"{_dur(row['days'][d]):>16}" for d in traffic))

    print("\n  What this tool will not tell you: how many people click, how many convert,")
    print("  or what they spend. Those are the experiment's outputs. Predicting them")
    print("  here would substitute arithmetic for the measurement the test exists to make.")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--json", action="store_true", help="emit the report as JSON")
    ap.add_argument("--fixture", type=pathlib.Path, default=FIXTURE)
    args = ap.parse_args()

    rep = build_report(json.loads(args.fixture.read_text()))
    print(json.dumps(rep, indent=2, default=str) if args.json else "", end="")
    if not args.json:
        emit(rep)
    return 0


if __name__ == "__main__":
    sys.exit(main())
