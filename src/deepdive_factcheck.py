#!/usr/bin/env python3
"""Fact-check gate for the weekly deep-dive series (deepdive_YYYY-MM-DD.json).

Hide's rule: every number and fact on screen must be verified against a
source (company disclosure / IR / securities data) and recorded with
source_url / source_note / checked_date. Nothing unverified goes in.

Checks (generic across stocks; the first edition was Skylark-specific):
- required fields, card structure (title/basic/4 deep/caution/summary),
  title_hook (opening-hook rule) and caution_subtitle, checked_date == today
- arithmetic: min investment == price x 100; each yutai tier's annual
  == per-half x 2 (half-year tiers) or per-event x events (annual tiers);
  dividend yield == annual dividend / price; 100-share total return ==
  (yutai annual + dividend x 100) / investment; optional yutai-tier total
  (e.g. 300 shares) checked the same way
- dividend history: 5 entries, all >= 0, strictly increasing, last forecast
- rights last day 2026-12-28 (December record, verified for this stock)
- sources: at least 3, each with a URL and a note recording the verified fact
- rotation: the stock must not appear in data/deepdive_history.json
  within the last 6 months
"""
import json, os, sys
from datetime import date

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _req(errors, obj, key, label):
    if key not in obj or obj[key] in (None, "", []):
        errors.append(f"{label}: {key} missing or empty")
        return False
    return True


def check(data, today=None, history_path=None):
    today = today or date.today().isoformat()
    errors = []
    stock = data.get("stock", {})
    label = f"deepdive {data.get('checked_date')} ({stock.get('code')})"

    for key in ("title_label", "checked_date", "source_url", "source_note",
                "basic_lines", "deep_cards", "caution_lines", "summary_rows",
                "title_hook", "caution_subtitle", "slug"):
        _req(errors, data, key, label)
    if data.get("checked_date") != today:
        errors.append(f"{label}: checked_date {data.get('checked_date')} != today {today}")
    if len(str(data.get("source_note", ""))) < 20:
        errors.append(f"{label}: source_note too short; record the verified facts")
    sources = data.get("sources", [])
    if len(sources) < 3:
        errors.append(f"{label}: need at least 3 sources, got {len(sources)}")
    for i, s in enumerate(sources, 1):
        if not str(s.get("url", "")).startswith("http"):
            errors.append(f"{label}: source {i} has no URL")
        if len(str(s.get("note", ""))) < 20:
            errors.append(f"{label}: source {i} note too short; record the verified fact")

    # card structure
    if len(data.get("basic_lines", [])) != 4:
        errors.append(f"{label}: basic_lines must have 4 lines")
    if len(data.get("deep_cards", [])) != 4:
        errors.append(f"{label}: deep_cards must have 4 cards")
    for i, card in enumerate(data.get("deep_cards", []), 1):
        if not card.get("title") or not card.get("subtitle"):
            errors.append(f"{label}: deep card {i} missing title/subtitle")
        if len(card.get("lines", [])) != 4:
            errors.append(f"{label}: deep card {i} must have 4 lines")
    if len(data.get("caution_lines", [])) != 4:
        errors.append(f"{label}: caution_lines must have 4 lines")
    if len(data.get("summary_rows", [])) != 3:
        errors.append(f"{label}: summary_rows must have 3 rows")
    for i, row in enumerate(data.get("summary_rows", []), 1):
        if not row.get("head") or len(row.get("lines", [])) != 2:
            errors.append(f"{label}: summary row {i} must have a head and 2 lines")

    # stock basics
    for key in ("name", "code", "market", "industry", "business_line",
                "price_yen", "price_date_label", "min_investment_yen",
                "min_investment_label", "rights_last_day", "rights_last_day_label"):
        _req(errors, stock, key, f"{label} stock")
    price = stock.get("price_yen")
    if isinstance(price, (int, float)) and price > 0:
        if stock.get("min_investment_yen") != price * 100:
            errors.append(f"{label}: min_investment_yen {stock.get('min_investment_yen')} "
                          f"!= price {price} x 100")
    if stock.get("rights_last_day") != "2026-12-28":
        errors.append(f"{label}: rights_last_day {stock.get('rights_last_day')} "
                      f"!= 2026-12-28 (verified December record date)")

    # yutai tiers: at least one; annual == per-half x 2 (half-year tiers)
    # or per-event x events (annual tiers, e.g. a once-a-year catalogue gift)
    tiers = stock.get("yutai", {}).get("tiers", [])
    if len(tiers) < 1:
        errors.append(f"{label}: yutai tiers must have at least 1 entry")
    for t in tiers:
        if not t.get("shares") or t.get("annual_yen") is None:
            errors.append(f"{label}: yutai tier missing shares/annual_yen: {t}")
            continue
        if t.get("per_half_yen") is not None:
            if t.get("annual_yen") != t.get("per_half_yen", 0) * 2:
                errors.append(f"{label}: tier {t.get('shares')}: annual {t.get('annual_yen')} "
                              f"!= per-half {t.get('per_half_yen')} x 2")
        if t.get("per_event_yen") is not None and t.get("events_per_year") is not None:
            if t.get("annual_yen") != t.get("per_event_yen") * t.get("events_per_year"):
                errors.append(f"{label}: tier {t.get('shares')}: annual {t.get('annual_yen')} "
                              f"!= per-event {t.get('per_event_yen')} x {t.get('events_per_year')}")

    # dividend: history, yield, payout
    div = stock.get("dividend", {})
    hist = div.get("history", [])
    if len(hist) != 5:
        errors.append(f"{label}: dividend history must have 5 entries (2022-2026)")
    else:
        vals = [h.get("yen") for h in hist]
        if any(v is None or v < 0 for v in vals):
            errors.append(f"{label}: dividend history must be non-negative: {vals}")
        if not all(vals[i] < vals[i + 1] for i in range(4)):
            errors.append(f"{label}: dividend must strictly increase 2022->2026: {vals}")
        if not hist[-1].get("forecast"):
            errors.append(f"{label}: 2026 dividend must be marked as forecast")
        annual = vals[-1]
        if isinstance(price, (int, float)) and price > 0 and isinstance(annual, (int, float)):
            calc = round(annual / price * 100, 2)
            if calc != div.get("yield_pct"):
                errors.append(f"{label}: yield_pct {div.get('yield_pct')} != "
                              f"{annual}/{price} = {calc}%")
        tr = stock.get("total_return_100", {})
        tier_100 = next((t for t in tiers if str(t.get("shares", "")).startswith("100株")), None)
        expected_yutai = tier_100.get("annual_yen") if tier_100 else 0
        if tr.get("yutai_annual_yen") != expected_yutai:
            errors.append(f"{label}: total_return yutai_annual {tr.get('yutai_annual_yen')} "
                          f"!= 100-share tier annual {expected_yutai}")
        if isinstance(annual, (int, float)):
            if tr.get("dividend_annual_yen") != annual * 100:
                errors.append(f"{label}: dividend_annual_yen {tr.get('dividend_annual_yen')} "
                              f"!= {annual} x 100")
        if tr.get("total_yen") != tr.get("yutai_annual_yen", 0) + tr.get("dividend_annual_yen", 0):
            errors.append(f"{label}: total_yen != yutai + dividend annual")
        inv = stock.get("min_investment_yen")
        if isinstance(inv, (int, float)) and inv > 0 and tr.get("total_yen"):
            calc = round(tr["total_yen"] / inv * 100, 2)
            if calc != tr.get("total_yield_pct"):
                errors.append(f"{label}: total_yield_pct {tr.get('total_yield_pct')} != "
                              f"{tr['total_yen']}/{inv} = {calc}%")
        # optional yutai-tier total (e.g. 300 shares where the benefit starts)
        trt = stock.get("total_return_yutai_tier")
        if trt:
            sh = trt.get("shares")
            if isinstance(price, (int, float)) and isinstance(sh, int):
                if trt.get("investment_yen") != price * sh:
                    errors.append(f"{label}: tier investment {trt.get('investment_yen')} "
                                  f"!= price {price} x {sh}")
            tier = next((t for t in tiers if str(t.get("shares", "")).startswith(f"{sh}株")), None)
            if tier and trt.get("yutai_annual_yen") != tier.get("annual_yen"):
                errors.append(f"{label}: tier yutai_annual {trt.get('yutai_annual_yen')} "
                              f"!= tier annual {tier.get('annual_yen')}")
            if isinstance(annual, (int, float)) and isinstance(sh, int):
                if trt.get("dividend_annual_yen") != annual * sh:
                    errors.append(f"{label}: tier dividend_annual {trt.get('dividend_annual_yen')} "
                                  f"!= {annual} x {sh}")
            if trt.get("total_yen") != trt.get("yutai_annual_yen", 0) + trt.get("dividend_annual_yen", 0):
                errors.append(f"{label}: tier total_yen != yutai + dividend annual")
            tinv = trt.get("investment_yen")
            if isinstance(tinv, (int, float)) and tinv > 0 and trt.get("total_yen"):
                calc = round(trt["total_yen"] / tinv * 100, 2)
                if calc != trt.get("total_yield_pct"):
                    errors.append(f"{label}: tier total_yield_pct {trt.get('total_yield_pct')} != "
                                  f"{trt['total_yen']}/{tinv} = {calc}%")

    # rotation: no repeat within 6 months
    history_path = history_path or os.path.join(ROOT, "data", "deepdive_history.json")
    if os.path.exists(history_path):
        try:
            with open(history_path, encoding="utf-8") as f:
                hist_data = json.load(f)
            code = stock.get("code")
            for entry in hist_data.get("history", []):
                if entry.get("code") == code and entry.get("date") != data.get("checked_date"):
                    errors.append(f"{label}: {code} already covered on {entry.get('date')} "
                                  f"(6-month rotation rule)")
        except (json.JSONDecodeError, OSError) as e:
            errors.append(f"{label}: cannot read history {history_path}: {e}")
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
    print(f"FACT-CHECK OK: {path} ({data['stock']['name']} {data['stock']['code']}, "
          f"checked {data['checked_date']})")
