#!/usr/bin/env python3
"""Fact-check gate for yutai picks data.

Fails the build (exit 1) if any check fails. Rules encode the lessons from
the first video: shuffled/ambiguous text, missing sources, stale checks,
and holding-period vs eligibility contradictions.
"""
import json, re, sys
from datetime import date

BANNED_PHRASES = ["今年OK", "今年ok", "神優待", "絶対", "必ず儲かる", "買い推奨"]

def check(data, today=None):
    today = today or date.today()
    errors = []
    picks = data.get("picks", [])
    if len(picks) != 5:
        errors.append(f"picks must be exactly 5, got {len(picks)}")
    codes = set()
    for i, p in enumerate(picks, 1):
        for field in ("name", "code", "benefit_lines", "point_lines", "summary_lines",
                      "source_url", "source_note", "eligible_this_year", "holding_years_required"):
            if field not in p:
                errors.append(f"pick {i}: missing field {field}")
        code = str(p.get("code", ""))
        if not re.fullmatch(r"\d{4}", code):
            errors.append(f"pick {i}: code '{code}' is not 4 digits")
        if code in codes:
            errors.append(f"pick {i}: duplicate code {code}")
        codes.add(code)
        for key in ("benefit_lines", "point_lines", "summary_lines"):
            lines = p.get(key, [])
            if len(lines) != 2:
                errors.append(f"pick {i} ({p.get('name')}): {key} must have exactly 2 lines")
            max_len = 20 if key == "summary_lines" else 16
            for ln in lines:
                if len(ln) > max_len:
                    errors.append(f"pick {i} ({p.get('name')}): line too long for card ({len(ln)} chars): {ln}")
                for b in BANNED_PHRASES:
                    if b in ln:
                        errors.append(f"pick {i} ({p.get('name')}): banned/ambiguous phrase '{b}' in: {ln}")
        if not str(p.get("source_url", "")).startswith("https://"):
            errors.append(f"pick {i} ({p.get('name')}): source_url must be https")
        # eligibility consistency: a stock that needs continuous holding
        # cannot be eligible for this year's benefit from a new purchase
        if p.get("holding_years_required", 0) > 0 and p.get("eligible_this_year"):
            errors.append(f"pick {i} ({p.get('name')}): holding_years_required>0 but eligible_this_year=true")
    checked = data.get("checked_date", "")
    try:
        cd = date.fromisoformat(checked)
        if (today - cd).days > 45:
            errors.append(f"checked_date {checked} is stale (>45 days old); re-verify sources")
    except ValueError:
        errors.append(f"checked_date '{checked}' is not YYYY-MM-DD")
    for field in ("month_label", "rights_last_day", "rights_last_day_label"):
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
