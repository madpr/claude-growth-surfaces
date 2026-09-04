#!/usr/bin/env python3
"""Size the placement test for a developer-platform row in the claude.ai left rail.

Reads a seeded fixture. Reads no account, makes no API calls, needs no login.

    ./size_experiment.py
    ./size_experiment.py --json

Every figure on the published page is printed here. Where a number is not knowable
from outside Anthropic, this tool sweeps it instead of asserting a point estimate,
and says so on the line that uses it.
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


def incremental_annual_usd(
    impressions: int,
    baseline_ctr: float,
    relative_lift: float,
    funnel: dict,
    monthly_arpu: float,
) -> float:
    """Annualized incremental platform revenue from the extra clicks the row wins."""
    extra_clicks = impressions * baseline_ctr * relative_lift
    payers = (
        extra_clicks
        * funnel["click_to_org"]
        * funnel["org_to_first_call"]
        * funnel["first_call_to_day30"]
    )
    return payers * monthly_arpu * 12.0


def build_report(cfg: dict) -> dict:
    test = cfg["test"]
    alpha, power, arms = test["alpha"], test["power"], test["arms"]
    funnel = {k: v for k, v in cfg["funnel"].items() if not k.startswith("_")}

    sizing = []
    for ctr in test["baseline_ctr_sweep"]:
        row = {"baseline_ctr": ctr, "per_arm": {}}
        for mde in test["mde_relative_sweep"]:
            row["per_arm"][mde] = sample_size_per_arm(ctr, mde, alpha, power)
        sizing.append(row)

    design_n = sample_size_per_arm(
        test["design_baseline_ctr"], test["design_mde_relative"], alpha, power
    )
    runtime = [
        {
            "daily_sessions": d,
            "days": days_to_decision(design_n, arms, d),
        }
        for d in cfg["eligible_traffic"]["daily_sessions_sweep"]
    ]

    per_100k = [
        {
            "monthly_arpu_usd": arpu,
            "annual_usd": incremental_annual_usd(
                100_000,
                test["design_baseline_ctr"],
                test["design_mde_relative"],
                funnel,
                arpu,
            ),
        }
        for arpu in cfg["revenue"]["monthly_arpu_usd_sweep"]
    ]

    run_rate = []
    for d in cfg["eligible_traffic"]["daily_sessions_sweep"]:
        annual_impressions = d * 365
        run_rate.append(
            {
                "daily_sessions": d,
                "annual_impressions": annual_impressions,
                "by_arpu": {
                    arpu: incremental_annual_usd(
                        annual_impressions,
                        test["design_baseline_ctr"],
                        test["design_mde_relative"],
                        funnel,
                        arpu,
                    )
                    for arpu in cfg["revenue"]["monthly_arpu_usd_sweep"]
                },
            }
        )

    click_to_payer = (
        funnel["click_to_org"] * funnel["org_to_first_call"] * funnel["first_call_to_day30"]
    )

    return {
        "design": {
            "baseline_ctr": test["design_baseline_ctr"],
            "mde_relative": test["design_mde_relative"],
            "alpha": alpha,
            "power": power,
            "arms": arms,
            "per_arm": design_n,
            "total_impressions": design_n * arms,
        },
        "sizing": sizing,
        "runtime": runtime,
        "funnel": funnel,
        "click_to_payer": click_to_payer,
        "per_100k_impressions": per_100k,
        "run_rate": run_rate,
    }


def emit(rep: dict) -> None:
    d = rep["design"]
    print("Placement test — developer platform row, claude.ai left rail")
    print("Seeded fixture. No account read, no API calls.\n")

    print("=== 1. Impressions per arm to detect a relative lift on click-through ===")
    mdes = sorted(rep["sizing"][0]["per_arm"].keys())
    print("  baseline CTR " + "".join(f"{m:>13.0%}" for m in mdes))
    for row in rep["sizing"]:
        cells = "".join(f"{row['per_arm'][m]:>13,}" for m in mdes)
        print(f"  {row['baseline_ctr']:>11.2%}{cells}")
    print(f"\n  alpha {d['alpha']}, power {d['power']:.0%}, {d['arms']} arms, two-sided.")

    print(
        f"\n=== 2. Design point: {d['mde_relative']:.0%} lift on a "
        f"{d['baseline_ctr']:.2%} baseline ==="
    )
    print(f"  {d['per_arm']:,} impressions per arm, {d['total_impressions']:,} total.")
    print("  Days to decision, by eligible daily sessions:")
    print("  (eligible traffic is not knowable from outside Anthropic, so it is swept)")
    for r in rep["runtime"]:
        days = r["days"]
        label = f"{days:,.1f} days" if days >= 1 else f"{days * 24:,.1f} hours"
        print(f"    {r['daily_sessions']:>9,} sessions/day  ->  {label}")

    print("\n=== 3. Click to retained payer ===")
    f = rep["funnel"]
    print(f"    click -> organization            {f['click_to_org']:>7.0%}")
    print(f"    organization -> first API call   {f['org_to_first_call']:>7.0%}")
    print(f"    first call -> still calling d30  {f['first_call_to_day30']:>7.0%}")
    print(f"    compounded                       {rep['click_to_payer']:>7.2%}")
    print("  All three rates are assumptions. Replace before quoting.")

    print("\n=== 4. Incremental annual platform revenue per 100,000 impressions ===")
    print("  (at the design point; monthly spend per converted caller is swept)")
    for r in rep["per_100k_impressions"]:
        print(f"    ${r['monthly_arpu_usd']:>4,}/mo per caller  ->  ${r['annual_usd']:>12,.0f}/yr")

    print("\n=== 5. Annual run rate, once the row is shipped to everyone eligible ===")
    print("  (a sidebar row is shown every session, so impressions recur; both axes swept)")
    arpus = sorted(rep["run_rate"][0]["by_arpu"].keys())
    print("  sessions/day " + "".join(f"{('$' + str(a) + '/mo'):>14}" for a in arpus))
    for r in rep["run_rate"]:
        cells = "".join(f"{r['by_arpu'][a]:>14,.0f}" for a in arpus)
        print(f"  {r['daily_sessions']:>12,}{cells}")
    print("  US dollars per year of incremental platform revenue.")

    print("\n  What this tool cannot tell you: eligible traffic, the true baseline, and")
    print("  every funnel rate above. It tells you how much traffic a decision needs")
    print("  and what the answer is worth once those are measured.")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--json", action="store_true", help="emit the report as JSON")
    ap.add_argument("--fixture", type=pathlib.Path, default=FIXTURE)
    args = ap.parse_args()

    cfg = json.loads(args.fixture.read_text())
    rep = build_report(cfg)

    if args.json:
        print(json.dumps(rep, indent=2))
    else:
        emit(rep)
    return 0


if __name__ == "__main__":
    sys.exit(main())
