#!/usr/bin/env python3
"""Fact-check gate for the weekly bargain series (bargain_YYYY-MM-DD.json).

Hide's rule: every number and fact on screen must be verified against a
source (company disclosure / IR / securities data / price API) and recorded
with source_url / source_note / checked_date. Nothing unverified goes in.

Checks:
- required fields, checked_date == today, 1-5 picks (fewer is fine: never
  pad the list to reach 5)
- arithmetic: weekly_change_pct == round((close - prev_close) / prev_close
  * 100, 1) for every pick and for the Nikkei weekly move; every pick fell
  at least ~5% in the week (weekly_change_pct <= -5.0); min investment ==
  close x 100
- card structure: each pick has 2 reason lines + 2 caution lines;
  summary has 3 rows with a head and 2 lines each
- sources: every pick has source_url (https) + source_note (>= 20 chars)
  and at least 2 source entries (earnings/disclosure + price API), each
  with a URL and a note recording the verified fact
- banned recommendation language in display text: no 「買い」「買い時」
  「絶対」「必ず上がる」「おすすめ」「買うべき」「今がチャンス」 and no
  「推奨」 outside the disclaimer 「投資推奨ではありません」
"""
import json, os, re, sys
from datetime import date

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

BANNED = ["買い時", "絶対", "必ず上がる", "おすすめ", "買うべき",
          "今がチャンス", "買いです", "買ってください", "買うなら今"]


def _req(errors, obj, key, label):
    if key not in obj or obj[key] in (None, "", []):
        errors.append(f"{label}: {key} missing or empty")
        return False
    return True


def _pct(prev, close):
    return round((close - prev) / prev * 100, 1)


def check(data, today=None):
    today = today or date.today().isoformat()
    errors = []
    label = f"bargain {data.get('checked_date')} ({data.get('week_label')})"

    for key in ("title_label", "week_label", "checked_date", "source_url",
                "source_note", "picks", "summary_rows", "market"):
        _req(errors, data, key, label)
    if data.get("checked_date") != today:
        errors.append(f"{label}: checked_date {data.get('checked_date')} != today {today}")
    if len(str(data.get("source_note", ""))) < 20:
        errors.append(f"{label}: source_note too short; record the verified facts")
    if not str(data.get("source_url", "")).startswith("https://"):
        errors.append(f"{label}: source_url must be https")

    # market context: Nikkei weekly move must match the two closes
    m = data.get("market", {})
    for key in ("index", "prev_close", "close", "weekly_change_pct"):
        _req(errors, m, key, f"{label} market")
    prev, close = m.get("prev_close"), m.get("close")
    if isinstance(prev, (int, float)) and isinstance(close, (int, float)) and prev > 0:
        if _pct(prev, close) != m.get("weekly_change_pct"):
            errors.append(f"{label}: market weekly_change_pct "
                          f"{m.get('weekly_change_pct')} != "
                          f"({close}-{prev})/{prev} = {_pct(prev, close)}%")

    # picks: 1-5, ranked, each down >= 5% with verified arithmetic
    picks = data.get("picks", [])
    if not 1 <= len(picks) <= 5:
        errors.append(f"{label}: need 1-5 picks, got {len(picks)}")
    for i, p in enumerate(picks, 1):
        plabel = f"{label} pick {i} ({p.get('code')})"
        for key in ("rank", "name", "code", "market", "industry",
                    "business_line", "prev_close", "close",
                    "weekly_change_pct", "price_date_label",
                    "min_investment_yen", "min_investment_label",
                    "reason_lines", "caution_lines",
                    "source_url", "source_note", "sources"):
            _req(errors, p, key, plabel)
        if p.get("rank") != i:
            errors.append(f"{plabel}: rank {p.get('rank')} != position {i}")
        if not re.fullmatch(r"[0-9A-Z]{4}", str(p.get("code", ""))):
            errors.append(f"{plabel}: code {p.get('code')} is not 4 alphanumeric chars")
        pp, cc = p.get("prev_close"), p.get("close")
        if isinstance(pp, (int, float)) and isinstance(cc, (int, float)) and pp > 0:
            if _pct(pp, cc) != p.get("weekly_change_pct"):
                errors.append(f"{plabel}: weekly_change_pct "
                              f"{p.get('weekly_change_pct')} != "
                              f"({cc}-{pp})/{pp} = {_pct(pp, cc)}%")
            if isinstance(p.get("weekly_change_pct"), (int, float)) and \
                    p["weekly_change_pct"] > -5.0:
                errors.append(f"{plabel}: weekly_change_pct "
                              f"{p['weekly_change_pct']}% is above the -5% "
                              f"threshold for this series")
            if p.get("min_investment_yen") != cc * 100:
                errors.append(f"{plabel}: min_investment_yen "
                              f"{p.get('min_investment_yen')} != close {cc} x 100")
        if len(p.get("reason_lines", [])) != 2:
            errors.append(f"{plabel}: reason_lines must have 2 lines")
        if len(p.get("caution_lines", [])) != 2:
            errors.append(f"{plabel}: caution_lines must have 2 lines")
        if not str(p.get("source_url", "")).startswith("https://"):
            errors.append(f"{plabel}: source_url must be https")
        if len(str(p.get("source_note", ""))) < 20:
            errors.append(f"{plabel}: source_note too short; record the verified facts")
        sources = p.get("sources", [])
        if len(sources) < 2:
            errors.append(f"{plabel}: need at least 2 sources "
                          f"(earnings/disclosure + prices), got {len(sources)}")
        for j, s in enumerate(sources, 1):
            if not str(s.get("url", "")).startswith("http"):
                errors.append(f"{plabel}: source {j} has no URL")
            if len(str(s.get("note", ""))) < 20:
                errors.append(f"{plabel}: source {j} note too short; "
                              f"record the verified fact")

    # summary structure
    rows = data.get("summary_rows", [])
    if len(rows) != 3:
        errors.append(f"{label}: summary_rows must have 3 rows")
    for i, row in enumerate(rows, 1):
        if not row.get("head") or len(row.get("lines", [])) != 2:
            errors.append(f"{label}: summary row {i} must have a head and 2 lines")

    # banned recommendation language in display text only
    display = [data.get("title_label", ""), data.get("week_label", "")]
    for p in picks:
        display += [p.get("name", "")] + list(p.get("reason_lines", [])) \
            + list(p.get("caution_lines", []))
    for row in rows:
        display += [row.get("head", "")] + list(row.get("lines", []))
    for text in display:
        for word in BANNED:
            if word in text:
                errors.append(f"{label}: banned recommendation phrase "
                              f"「{word}」 in display text: {text}")
        for mm in re.finditer("推奨", text):
            if text[max(0, mm.start() - 4):mm.start()] != "投資" or \
                    "ではありません" not in text[mm.start():mm.start() + 12]:
                errors.append(f"{label}: 「推奨」 outside the disclaimer in: {text}")
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
    print(f"FACT-CHECK OK: {path} ({len(data['picks'])} picks, "
          f"checked {data['checked_date']})")
