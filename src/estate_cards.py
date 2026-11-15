#!/usr/bin/env python3
"""Custom trial-calculation card for the estate one-off video.

Hide asked (2026-11-16) for this one card to break the standard
five-row layout and prioritise clarity: a compact deduction flow on
top, then a side-by-side comparison of taxable income and tax with
and without a JPY1M real-estate loss. Figures are the labelled
estimates documented in data/estate_2026-11.json (single person,
social insurance approximated at about 14% of salary)."""
import tax_cards as tc

W, H = tc.W, tc.H
F, BOLD, REG = tc.F, tc.BOLD, tc.REG
TEAL, TEAL_DARK, AMBER = tc.TEAL, tc.TEAL_DARK, tc.AMBER
BODY, NAME = tc.BODY, tc.NAME
GRAY = (107, 114, 128)
PALE_AMBER = (255, 243, 205)


def _fit(d, text, max_width, start, min_size=19):
    size = start
    while size > min_size and d.textlength(text, font=F(BOLD, size)) > max_width:
        size -= 1
    return size


def _center(d, cx, y, text, size, color):
    d.text((cx, y), text, font=F(BOLD, size), fill=color, anchor="mm")


def trial_card(data, out):
    p = data["picks"][2]
    img, d = tc._base(p["name"], "節税対策 3／5")

    # --- deduction flow panel ---
    d.rounded_rectangle([36, 226, 684, 478], radius=24, fill=(255, 255, 255),
                        outline=TEAL, width=3)
    flow = [
        "年収1,000万円−給与所得控除195万円＝805万円",
        "社会保険料 約140万円（概算）と基礎控除を引く",
        "課税所得は約605万円で税率は約30%",
    ]
    for i, ln in enumerate(flow):
        y = 282 + i * 70
        d.ellipse([58, y - 20, 98, y + 20], fill=AMBER)
        size = _fit(d, ln, 556, 27 if i == 2 else 25)
        d.text((118, y), ln, font=F(BOLD, size), fill=BODY, anchor="lm")

    # --- comparison heading ---
    _center(d, W // 2, 524, "不動産所得の赤字で比べると", 26, TEAL)

    # --- two comparison panels ---
    def panel(x0, header, income, tax, fill, outline, width):
        x1 = x0 + 312
        d.rounded_rectangle([x0, 556, x1, 940], radius=24, fill=fill,
                            outline=outline, width=width)
        cx = (x0 + x1) // 2
        _center(d, cx, 602, header, _fit(d, header, 280, 25), TEAL_DARK)
        _center(d, cx, 676, "課税所得", 21, GRAY)
        _center(d, cx, 730, income, 38, NAME)
        _center(d, cx, 806, "所得税＋住民税の目安", 20, GRAY)
        _center(d, cx, 860, tax, 38, NAME)

    panel(36, "赤字なしの場合", "約605万円", "約140万円",
          (255, 255, 255), TEAL, 3)
    panel(372, "赤字100万円の場合", "約505万円", "約110万円",
          PALE_AMBER, AMBER, 4)

    # --- result banner ---
    d.rounded_rectangle([36, 972, 684, 1052], radius=22, fill=TEAL)
    banner = "赤字100万円で税金は約30万円軽くなる"
    _center(d, W // 2, 1012, banner, _fit(d, banner, 620, 27), (255, 255, 255))

    note = p.get("footnote")
    if note:
        _center(d, W // 2, 1108, note, 22, TEAL)
    tc._footer(d, tc.FOOTER_DETAIL)
    img.save(out)
    return out
