#!/usr/bin/env python3
"""Fact-check gate for high-dividend picks data.

Mirror of factcheck.py (yutai) with dividend-specific rules: the stated
yield must match annual_dividend / price, and the minimum investment must
equal price x 100 shares. Fails the build (exit 1) if any check fails.
"""
import json, re, sys
from datetime import date

BANNED_PHRASES = ["今年OK", "今年ok", "神配当", "絶対", "必ず儲かる", "買い推奨",
                  "配当保証", "元本保証", "ノーリスク"]

REQUIRED_PICK_FIELDS = ("name", "code", "yield_pct", "annual_dividend_yen",
                        "annual_dividend_label", "price_yen", "price_date_label",
                        "min_investment_yen", "min_investment_label",
                        "stability_note", "rights_label",
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
    codes = set()
    for i, p in enumerate(picks, 1):
        label = f"pick {i} ({p.get('name')})"
        for field in REQUIRED_PICK_FIELDS:
            if field not in p:
                errors.append(f"pick {i}: missing field {field}")
        code = str(p.get("code", ""))
        if not re.fullmatch(r"\d{4}", code):
            errors.append(f"pick {i}: code '{code}' is not 4 digits")
        if code in codes:
            errors.append(f"pick {i}: duplicate code {code}")
        codes.add(code)
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
        # numeric consistency: stated yield vs dividend/price, min investment
        try:
            y = float(p["yield_pct"]); div = float(p["annual_dividend_yen"])
            price = float(p["price_yen"]); mininv = float(p["min_investment_yen"])
            calc = div / price * 100
            if abs(y - calc) > 0.05:
                errors.append(f"{label}: yield_pct {y} != dividend/price {calc:.2f}")
            if not (3.0 <= y <= 12.0):
                errors.append(f"{label}: yield_pct {y} outside sane range 3.0-12.0")
            if div <= 0:
                errors.append(f"{label}: annual_dividend_yen must be positive")
            if abs(mininv - price * 100) > 1:
                errors.append(f"{label}: min_investment_yen {mininv} != price*100 {price * 100}")
        except (KeyError, TypeError, ValueError):
            errors.append(f"{label}: numeric fields missing or not numeric")
    _check_date(data.get("checked_date", ""), "top-level", today, errors)
    for field in ("title_label", "list_subtitle", "points_subtitle", "yield_basis_label"):
        if not data.get(field):
            errors.append(f"missing top-level field {field}")
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
    print(f"FACT-CHECK OK: {path} (5 picks, sources dated {data['checked_date']})")
