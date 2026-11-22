#!/usr/bin/env python3
"""Fact-check gate for the weekly rights-date calendar video.

Fails the build (exit 1) if any check fails. Rules mirror factcheck.py
but fit the calendar shape: 1-5 picks in the target week, each with a
rights date inside the week, sources, fresh check date, and no banned
or ambiguous phrasing. The next-week preview is checked the same way
(name / 4-digit code / one benefit line / source).
"""
import json, re, sys
from datetime import date

BANNED_PHRASES = ["今年OK", "今年ok", "神優待", "絶対", "必ず儲かる", "買い推奨"]


def check(data, today=None):
    today = today or date.today()
    errors = []
    picks = data.get("picks", [])
    if not (1 <= len(picks) <= 5):
        errors.append(f"picks must be 1-5, got {len(picks)}")
    try:
        ws = date.fromisoformat(data.get("week_start", ""))
        we = date.fromisoformat(data.get("week_end", ""))
    except ValueError:
        errors.append("week_start / week_end must be YYYY-MM-DD")
        ws = we = None
    codes = set()
    for i, p in enumerate(picks, 1):
        for field in ("name", "code", "rights_date", "rights_label",
                      "benefit_lines", "dividend_line", "min_investment_label",
                      "min_investment_yen", "price_yen", "price_date_label",
                      "source_url", "source_note", "checked_date"):
            if field not in p:
                errors.append(f"pick {i}: missing field {field}")
        code = str(p.get("code", ""))
        if not re.fullmatch(r"\d{4}", code):
            errors.append(f"pick {i}: code '{code}' is not 4 digits")
        if code in codes:
            errors.append(f"pick {i}: duplicate code {code}")
        codes.add(code)
        try:
            rd = date.fromisoformat(p.get("rights_date", ""))
            if ws and we and not (ws <= rd <= we):
                errors.append(f"pick {i} ({p.get('name')}): rights_date {rd} outside week {ws}..{we}")
        except ValueError:
            errors.append(f"pick {i} ({p.get('name')}): rights_date is not YYYY-MM-DD")
        lines = p.get("benefit_lines", [])
        if len(lines) != 2:
            errors.append(f"pick {i} ({p.get('name')}): benefit_lines must have exactly 2 lines")
        for ln in lines + [p.get("dividend_line", ""), p.get("min_investment_label", "")]:
            if len(ln) > 20:
                errors.append(f"pick {i} ({p.get('name')}): line too long for card ({len(ln)} chars): {ln}")
            for b in BANNED_PHRASES:
                if b in ln:
                    errors.append(f"pick {i} ({p.get('name')}): banned/ambiguous phrase '{b}' in: {ln}")
        if not str(p.get("source_url", "")).startswith("https://"):
            errors.append(f"pick {i} ({p.get('name')}): source_url must be https")
        # price * 100 must match the stated minimum investment (100 shares)
        price = p.get("price_yen")
        inv = p.get("min_investment_yen")
        if isinstance(price, (int, float)) and isinstance(inv, (int, float)):
            if price * 100 != inv:
                errors.append(f"pick {i} ({p.get('name')}): price_yen {price} x 100 != min_investment_yen {inv}")
    nw = data.get("next_week", {})
    try:
        nrd = date.fromisoformat(nw.get("rights_date", ""))
        if we and nrd <= we:
            errors.append(f"next_week rights_date {nrd} is not after this week ({we})")
    except ValueError:
        errors.append("next_week.rights_date is not YYYY-MM-DD")
    if not str(nw.get("source_url", "")).startswith("https://"):
        errors.append("next_week: source_url must be https")
    for field in ("header", "subtitle", "summary_line", "summary_sub", "caption_line"):
        if not nw.get(field):
            errors.append(f"next_week: missing field {field}")
    for note in nw.get("notes", []):
        if len(str(note)) > 40:
            errors.append(f"next_week note too long for card: {note}")
    # Opening hook (Hide's rule, 2026-11-19): concrete amount / deadline
    hook = data.get("hook_lines", [])
    if not (1 <= len(hook) <= 2):
        errors.append("hook_lines must have 1-2 lines")
    for ln in hook:
        if len(str(ln)) > 24:
            errors.append(f"hook line too long for title card ({len(ln)} chars): {ln}")
        for b in BANNED_PHRASES:
            if b in str(ln):
                errors.append(f"hook: banned phrase '{b}' in: {ln}")
    if not data.get("rights_fall_label"):
        errors.append("missing top-level field rights_fall_label")
    for j, item in enumerate(data.get("also_this_week", []), 1):
        for field in ("name", "code", "line"):
            if field not in item:
                errors.append(f"also_this_week item {j}: missing field {field}")
        if not re.fullmatch(r"\d{4}", str(item.get("code", ""))):
            errors.append(f"also_this_week item {j}: code '{item.get('code')}' is not 4 digits")
    for j, item in enumerate(nw.get("items", []), 1):
        for field in ("name", "code", "line"):
            if field not in item:
                errors.append(f"next_week item {j}: missing field {field}")
        if not re.fullmatch(r"\d{4}", str(item.get("code", ""))):
            errors.append(f"next_week item {j}: code '{item.get('code')}' is not 4 digits")
        if len(str(item.get("line", ""))) > 26:
            errors.append(f"next_week item {j}: line too long for card: {item.get('line')}")
        for b in BANNED_PHRASES:
            if b in str(item.get("line", "")):
                errors.append(f"next_week item {j}: banned phrase '{b}' in: {item.get('line')}")
    checked = data.get("checked_date", "")
    try:
        cd = date.fromisoformat(checked)
        if (today - cd).days > 45:
            errors.append(f"checked_date {checked} is stale (>45 days old); re-verify sources")
    except ValueError:
        errors.append(f"checked_date '{checked}' is not YYYY-MM-DD")
    for field in ("week_label", "week_start", "week_end", "theme"):
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
    print(f"FACT-CHECK OK: {path} ({len(data['picks'])} picks, checked {data['checked_date']})")
