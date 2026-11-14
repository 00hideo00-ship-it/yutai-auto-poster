#!/usr/bin/env python3
"""Fact-check gate for the domestic-fund edition (fund_domestic_YYYY-MM.json).

Runs the shared fund gate (fund_factcheck.check) and adds one rule for
non-monthly funds: a pick may declare `settlements_per_year` (e.g. 4) and
`distribution_per_settlement_yen`; then the per-settlement amount times the
number of settlements must equal monthly_distribution_yen x 12 (the monthly
equivalent used by the base gate), and the stated yield must match
per-settlement x settlements / NAV. Card labels for such a pick must state
the real per-settlement amount, never a monthly one.
"""
import json, sys, os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fund_factcheck  # noqa: E402


def check(data, today=None):
    errors = fund_factcheck.check(data, today=today)
    for i, p in enumerate(data.get("picks", []), 1):
        label = f"pick {i} ({p.get('short_name')})"
        per_year = p.get("settlements_per_year", 12)
        if per_year == 12:
            continue
        per_settle = p.get("distribution_per_settlement_yen")
        if per_settle is None:
            errors.append(f"{label}: settlements_per_year={per_year} but no "
                          f"distribution_per_settlement_yen")
            continue
        try:
            monthly = float(p["monthly_distribution_yen"])
            nav = float(p["nav_yen"]); y = float(p["yield_pct"])
            if abs(float(per_settle) * per_year - monthly * 12) > 0.01:
                errors.append(f"{label}: per-settlement {per_settle} x {per_year} "
                              f"!= monthly-equivalent {monthly} x 12")
            calc = float(per_settle) * per_year / nav * 100
            if abs(y - calc) > 0.06:
                errors.append(f"{label}: yield_pct {y} != per-settlement*per_year/nav {calc:.2f}")
            if str(int(per_settle)) not in str(p.get("distribution_label", "")):
                errors.append(f"{label}: distribution_label must state the real "
                              f"per-settlement amount {per_settle}")
        except (KeyError, TypeError, ValueError):
            errors.append(f"{label}: settlement fields missing or not numeric")
    return errors


if __name__ == "__main__":
    path = sys.argv[1]
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    errs = check(data)
    if errs:
        print("FACT-CHECK FAILED:")
        for e in errs:
            print(" -", e)
        sys.exit(1)
    print(f"FACT-CHECK OK: {path} (5 funds, sources dated {data['checked_date']})")
