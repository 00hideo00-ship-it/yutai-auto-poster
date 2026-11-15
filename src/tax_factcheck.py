#!/usr/bin/env python3
"""Fact-check gate for the tax-saving (setsuzei) one-off series.

Every on-screen claim must trace to an official source (NTA / FSA / MHLW /
Soumu) recorded in the data file. The gate enforces: exactly 5 items,
unique names, https sources with notes, a fresh checked_date, card line
budgets, and a ban on absolute/guarantee phrasing."""
import datetime

BANNED = ["絶対", "必ず得", "確実に儲かる", "元本保証", "税金がゼロになる",
          "誰でも全額", "ノーリスク"]


def check(data):
    errors = []
    picks = data.get("picks", [])
    if len(picks) != 5:
        errors.append(f"picks must be exactly 5, got {len(picks)}")
    names = [p.get("name", "") for p in picks]
    if len(set(names)) != len(names):
        errors.append("duplicate item names")
    today = datetime.date.today()
    top_checked = data.get("checked_date", "")
    for p in picks:
        label = p.get("name", "?")
        url = p.get("source_url", "")
        if not url.startswith("https://"):
            errors.append(f"{label}: source_url must be https")
        if not p.get("source_note"):
            errors.append(f"{label}: source_note is empty")
        cd = p.get("checked_date", "")
        if cd != top_checked:
            errors.append(f"{label}: checked_date {cd} != data checked_date {top_checked}")
        try:
            d = datetime.date.fromisoformat(cd)
            if (today - d).days > 45:
                errors.append(f"{label}: checked_date {cd} is stale (>45 days)")
        except ValueError:
            errors.append(f"{label}: checked_date {cd} is not a date")
        ll = p.get("list_lines", [])
        if len(ll) != 2 or any(len(x) > 20 for x in ll):
            errors.append(f"{label}: list_lines must be 2 lines of <=20 chars")
        dl = p.get("detail_lines", [])
        if not (4 <= len(dl) <= 5) or any(len(x) > 24 for x in dl):
            errors.append(f"{label}: detail_lines must be 4-5 lines of <=24 chars")
        sl = p.get("summary_lines", [])
        if len(sl) != 2 or any(len(x) > 22 for x in sl):
            errors.append(f"{label}: summary_lines must be 2 lines of <=22 chars")
        blob = "".join(ll + dl + sl)
        for b in BANNED:
            if b in blob:
                errors.append(f"{label}: banned phrase present: {b}")
    return errors
