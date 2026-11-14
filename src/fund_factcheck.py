#!/usr/bin/env python3
"""Fact-check gate for high-distribution investment-trust (fund) picks data.

Mirror of dividend_factcheck.py with fund-specific rules: the stated
distribution yield must match (latest monthly distribution x 12) / NAV,
the return-of-capital caveat must be present, and fund names must be
unique. Fails the build (exit 1) if any check fails.
"""
import json, sys
from datetime import date

BANNED_PHRASES = ["今年OK", "今年ok", "神配当", "絶対", "必ず儲かる", "買い推奨",
                  "分配金保証", "元本保証", "ノーリスク", "タコ足で安心"]

REQUIRED_PICK_FIELDS = ("name", "short_name", "manager", "yield_pct",
                        "monthly_distribution_yen", "distribution_label",
                        "frequency_label", "nav_yen", "nav_date_label",
                        "net_assets_oku", "net_assets_label",
                        "trust_fee_pct", "trust_fee_label",
                        "list_lines", "point_lines", "summary_lines",
                        "source_url", "source_note", "checked_date")

def _check_date(value, label, today, errors):
    try:
        cd = date.fromisoformat(value)
        if (today - cd).days > 45:
            errors.append(f"{label}: checked_date {value} is stale (>45 days old); re-verify sources")
    except (ValueError, TypeError):
        errors.append(f"{label}: checked_date '{value}' is not YYYY-MM-DD")

def check(data, today=None):
    today = today or date.today()
    errors = []
    picks = data.get("picks", [])
    if len(picks) != 5:
        errors.append(f"picks must be exactly 5, got {len(picks)}")
    names = set()
    for i, p in enumerate(picks, 1):
        label = f"pick {i} ({p.get('short_name')})"
        for field in REQUIRED_PICK_FIELDS:
            if field not in p:
                errors.append(f"pick {i}: missing field {field}")
        name = str(p.get("name", ""))
        if name in names:
            errors.append(f"pick {i}: duplicate fund name {name}")
        names.add(name)
        if len(str(p.get("short_name", ""))) > 16:
            errors.append(f"{label}: short_name too long for card (>16 chars)")
        for key in ("list_lines", "point_lines", "summary_lines"):
            lines = p.get(key, [])
            if len(lines) != 2:
                errors.append(f"{label}: {key} must have exactly 2 lines")
            max_len = 20 if key == "summary_lines" else 16
            for ln in lines:
                if len(ln) > max_len:
                    errors.append(f"{label}: line too long for card ({len(ln)} chars): {ln}")
                for b in BANNED_PHRASES:
                    if b in ln:
                        errors.append(f"{label}: banned/ambiguous phrase '{b}' in: {ln}")
        if not str(p.get("source_url", "")).startswith("https://"):
            errors.append(f"{label}: source_url must be https")
        _check_date(p.get("checked_date", ""), label, today, errors)
        # numeric consistency: stated yield vs (monthly distribution x 12) / NAV
        try:
            y = float(p["yield_pct"]); dist = float(p["monthly_distribution_yen"])
            nav = float(p["nav_yen"]); fee = float(p["trust_fee_pct"])
            calc = dist * 12 / nav * 100
            if abs(y - calc) > 0.06:
                errors.append(f"{label}: yield_pct {y} != dist*12/nav {calc:.2f}")
            if not (3.0 <= y <= 40.0):
                errors.append(f"{label}: yield_pct {y} outside sane range 3.0-40.0")
            if dist <= 0:
                errors.append(f"{label}: monthly_distribution_yen must be positive")
            if not (0 < fee <= 3.5):
                errors.append(f"{label}: trust_fee_pct {fee} outside sane range 0-3.5")
            if float(p["net_assets_oku"]) <= 0:
                errors.append(f"{label}: net_assets_oku must be positive")
        except (KeyError, TypeError, ValueError):
            errors.append(f"{label}: numeric fields missing or not numeric")
    _check_date(data.get("checked_date", ""), "top-level", today, errors)
    for field in ("title_label", "list_subtitle", "points_subtitle",
                  "yield_basis_label", "caveat_label"):
        if not data.get(field):
            errors.append(f"missing top-level field {field}")
    # honesty requirement: the return-of-capital caveat must be carried in the data
    if "元本" not in str(data.get("caveat_label", "")):
        errors.append("caveat_label must mention 元本 (return of capital)")
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
