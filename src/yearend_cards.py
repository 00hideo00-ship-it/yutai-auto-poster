#!/usr/bin/env python3
"""Cards (720x1280) for the year-end tax-deadline one-off video
「年内にやらないと損する節税の締切」.

Same visual identity as the tax series (mint-white background, deep teal
header band, amber accents) with the badge 「節税」. Structure mirrors
the salary one-off (Hide's standing rules, 2026-11-23): title card with
concrete date hooks -> list card in deadline order -> one detail card
per item, each opening with a one-line conclusion band and closing with
a themed illustration -> summary card whose hero is the conclusion
「締切を守ること」 with the deadlines re-listed per row."""
from PIL import Image, ImageDraw
import os, random
import cards as _c

W, H = _c.W, _c.H
F, BOLD, REG = _c.F, _c.BOLD, _c.REG

BG = (246, 253, 250)          # mint-white
TEAL = (8, 92, 84)            # deep teal, main color
TEAL_DARK = (5, 56, 52)       # title stroke / name text
AMBER = (245, 158, 11)        # amber accent
AMBER_LIGHT = (253, 211, 77)  # badge text / light amber
NAME = (5, 56, 52)
BODY = (55, 65, 81)
ROW_COLORS = [(187, 240, 230), (254, 230, 170), (170, 228, 218),
              (253, 214, 130), (196, 236, 228)]
BADGE = "節税"
FOOTER = "※制度・期限は2026年11月24日時点の情報です"


def _badge(d, cx, cy, r):
    """Series marker: teal disc, amber ring, 「節税」 in light amber."""
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=TEAL, outline=AMBER, width=4)
    d.text((cx, cy - 1), BADGE, font=F(BOLD, int(r * 0.78)), fill=AMBER_LIGHT, anchor="mm")


def _bubbles(d):
    random.seed(5)
    for _ in range(28):  # soft teal/amber bubbles
        x, y = random.randint(-40, W), random.randint(-40, H)
        r = random.randint(8, 42)
        c = random.choice([(13, 148, 136, 22), (245, 158, 11, 24), (45, 180, 165, 26)])
        d.ellipse([x - r, y - r, x + r, y + r], fill=c)
    for _ in range(8):  # tiny amber rings
        x, y = random.randint(20, W - 20), random.randint(220, H - 60)
        r = random.randint(9, 17)
        d.ellipse([x - r, y - r, x + r, y + r], outline=(245, 158, 11, 110), width=3)


def _base(title, subtitle):
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img, "RGBA")
    _bubbles(d)
    d.rounded_rectangle([16, 16, 704, 196], radius=28, fill=TEAL + (255,))
    title_size = 58 if len(title) <= 9 else 50
    while title_size > 30 and d.textlength(title, font=F(BOLD, title_size)) > 500:
        title_size -= 2  # keep clear of the badge at top-right
    d.text((W // 2, 78), title, font=F(BOLD, title_size), fill=AMBER_LIGHT, anchor="mm",
           stroke_width=6, stroke_fill=TEAL_DARK)
    sub_size = 34 if len(subtitle) <= 15 else (26 if len(subtitle) <= 24 else 22)
    d.rounded_rectangle([40, 118, 680, 178], radius=30, fill=AMBER + (255,))
    d.text((W // 2, 148), subtitle, font=F(BOLD, sub_size), fill=TEAL_DARK, anchor="mm")
    _badge(d, 646, 76, 37)
    return img, d


def _footer(d, text):
    d.text((W // 2, H - 42), text, font=F(REG, 20), fill=TEAL, anchor="mm")


def _fit(d, text, size, max_w):
    while size > 20 and d.textlength(text, font=F(BOLD, size)) > max_w:
        size -= 2
    return size


def title_card(data, out):
    """Opening title card: full title centered, concrete date hooks in
    amber pills under the title (Hide's opening-hook rule)."""
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img, "RGBA")
    _bubbles(d)
    d.rounded_rectangle([36, 300, 684, 980], radius=36, fill=TEAL + (255,))
    _badge(d, 646, 76, 37)
    lines = data["title_lines"]
    y = 448
    for ln in lines:
        size = _fit(d, ln, 66, 600)
        d.text((W // 2, y), ln, font=F(BOLD, size), fill=AMBER_LIGHT,
               anchor="mm", stroke_width=6, stroke_fill=TEAL_DARK)
        y += 112
    hy = 668
    for hook in data["hooks"]:
        d.rounded_rectangle([64, hy, 656, hy + 72], radius=36, fill=AMBER + (255,))
        size = _fit(d, hook, 31, 560)
        d.text((W // 2, hy + 37), hook, font=F(BOLD, size), fill=TEAL_DARK, anchor="mm")
        hy += 92
    d.text((W // 2, 918), "節税の締切は年末に集中する", font=F(BOLD, 30),
           fill=AMBER_LIGHT, anchor="mm")
    _footer(d, FOOTER)
    img.save(out); return out


def list_card(data, out):
    img, d = _base(data["list_title"], data["list_subtitle"])
    y = 205
    for i, p in enumerate(data["picks"]):
        color = ROW_COLORS[i % len(ROW_COLORS)]
        d.rounded_rectangle([28, y, 692, y + 178], radius=26, fill=color + (255,),
                            outline=TEAL + (255,), width=3)
        stage = p.get("stage", "")
        head = f"{i+1}) 【{stage}】{p['name']}" if stage else f"{i+1}) {p['name']}"
        d.text((48, y + 14), head, font=F(BOLD, _fit(d, head, 35, 624)), fill=NAME)
        for j, ln in enumerate(p["list_lines"]):
            d.text((48, y + 66 + j * 50), ln, font=F(BOLD, 30), fill=BODY)
        y += 192
    _footer(d, FOOTER)
    img.save(out); return out


def detail_card(data, idx, out):
    p = data["picks"][idx]
    stage = p.get("stage", "")
    subtitle = f"{stage} {idx+1}／{len(data['picks'])}" if stage else f"{idx+1}／{len(data['picks'])}"
    img, d = _base(p["name"], subtitle)
    # Conclusion band (standing rule): one-line takeaway on an amber band
    # directly under the header, before the detail rows.
    msg = p["message"]
    d.rounded_rectangle([36, 206, 684, 276], radius=22, fill=AMBER + (255,),
                        outline=TEAL + (255,), width=3)
    d.polygon([(64, 228), (64, 254), (86, 241)], fill=TEAL_DARK)
    size = _fit(d, msg, 34, 540)
    d.text((W // 2 + 14, 241), msg, font=F(BOLD, size), fill=TEAL_DARK, anchor="mm")
    lines = p["detail_lines"]
    y = 292
    for ln in lines:
        d.rounded_rectangle([36, y, 684, y + 128], radius=22, fill=(255, 255, 255, 255),
                            outline=TEAL + (255,), width=3)
        d.ellipse([58, y + 44, 98, y + 84], fill=AMBER)
        size = 31
        while size > 22 and d.textlength(ln, font=F(BOLD, size)) > 556:
            size -= 3
        d.text((118, y + 64), ln, font=F(BOLD, size), fill=BODY, anchor="lm")
        y += 148
    _illustration(d, idx, y)
    _footer(d, FOOTER)
    img.save(out); return out


# --- Detail-card illustrations: one flat PIL drawing per pick in the
# free band under the detail rows. Palette stays teal x amber.

def _coin(d, cx, cy, r):
    """Gold yen coin."""
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=AMBER,
              outline=(217, 119, 6), width=max(2, int(r * 0.12)))
    ri = r * 0.66
    d.ellipse([cx - ri, cy - ri, cx + ri, cy + ri],
              outline=AMBER_LIGHT, width=max(2, int(r * 0.12)))
    d.text((cx, cy - 1), "\u00a5", font=F(BOLD, int(r * 1.02)),
           fill=(255, 255, 255), anchor="mm")


def _illus_loss(d, cx, cy, s):
    """Pick 1 - sondashi: a falling chart, the loss fixed at the bottom,
    and a coin coming back (tax refunded)."""
    x0, x1 = cx - 255 * s, cx + 255 * s
    yb = cy + 115 * s
    d.line([x0, yb, x1, yb], fill=TEAL, width=max(3, int(5 * s)))
    d.line([x0, yb, x0, cy - 125 * s], fill=TEAL, width=max(3, int(5 * s)))
    pts = [(x0 + 35 * s, cy - 100 * s), (cx - 70 * s, cy - 30 * s),
           (cx + 30 * s, cy + 10 * s), (cx + 130 * s, cy + 62 * s)]
    d.line(pts, fill=TEAL_DARK, width=max(4, int(9 * s)), joint="curve")
    for px, py in pts[:-1]:
        r = 11 * s
        d.ellipse([px - r, py - r, px + r, py + r], fill=AMBER,
                  outline=TEAL_DARK, width=max(2, int(3 * s)))
    _coin(d, pts[-1][0], pts[-1][1], 28 * s)
    # return arrow: from the sold position back up (the refund)
    ax0, ay0 = cx + 175 * s, cy + 78 * s
    ax1, ay1 = cx + 225 * s, cy - 55 * s
    d.line([ax0, ay0, ax0, ay1], fill=TEAL, width=max(3, int(7 * s)))
    d.polygon([(ax0, ay1 - 16 * s), (ax0 - 12 * s, ay1 + 8 * s),
               (ax0 + 12 * s, ay1 + 8 * s)], fill=TEAL)
    _coin(d, ax0 + 4 * s, ay1 - 48 * s, 22 * s)


def _illus_gift(d, cx, cy, s):
    """Pick 2 - furusato nozei: a gift box with a ribbon (the return gift)."""
    bx0, bx1 = cx - 170 * s, cx + 170 * s
    by0, by1 = cy - 15 * s, cy + 115 * s
    d.rounded_rectangle([bx0, by0, bx1, by1], radius=int(10 * s),
                        fill=(254, 230, 170), outline=AMBER,
                        width=max(3, int(4 * s)))
    d.rounded_rectangle([bx0 - 22 * s, by0 - 52 * s, bx1 + 22 * s, by0],
                        radius=int(10 * s), fill=AMBER_LIGHT, outline=AMBER,
                        width=max(3, int(4 * s)))
    d.rectangle([cx - 24 * s, by0 - 52 * s, cx + 24 * s, by1], fill=TEAL)
    # bow: two loops + knot
    d.ellipse([cx - 118 * s, by0 - 118 * s, cx - 8 * s, by0 - 48 * s],
              outline=TEAL, width=max(3, int(7 * s)))
    d.ellipse([cx + 8 * s, by0 - 118 * s, cx + 118 * s, by0 - 48 * s],
              outline=TEAL, width=max(3, int(7 * s)))
    r = 15 * s
    d.ellipse([cx - r, by0 - 66 * s - r, cx + r, by0 - 66 * s + r], fill=TEAL)
    _coin(d, cx + 218 * s, cy + 62 * s, 30 * s)
    _coin(d, cx - 222 * s, cy + 78 * s, 24 * s)


def _illus_frame(d, cx, cy, s):
    """Pick 3 - NISA frame: a bold frame (the annual allowance) holding a
    rising chart and coins; nothing carries over the edge."""
    fx0, fx1 = cx - 250 * s, cx + 250 * s
    fy0, fy1 = cy - 120 * s, cy + 120 * s
    d.rounded_rectangle([fx0, fy0, fx1, fy1], radius=int(20 * s),
                        fill=(255, 255, 255), outline=TEAL,
                        width=max(4, int(10 * s)))
    pts = [(fx0 + 45 * s, cy + 62 * s), (cx - 70 * s, cy + 18 * s),
           (cx + 30 * s, cy - 28 * s), (fx1 - 55 * s, cy - 72 * s)]
    d.line(pts, fill=TEAL_DARK, width=max(4, int(9 * s)), joint="curve")
    tipx, tipy = pts[-1]
    d.polygon([(tipx + 26 * s, tipy - 4 * s), (tipx - 2 * s, tipy - 20 * s),
               (tipx + 2 * s, tipy + 16 * s)], fill=TEAL_DARK)
    _coin(d, fx0 + 62 * s, cy - 66 * s, 26 * s)
    _coin(d, cx + 120 * s, cy + 62 * s, 30 * s)


def _illus_envelope(d, cx, cy, s):
    """Pick 4 - one-stop application: an envelope on its way, with a
    stamp and a teal approval seal."""
    ex0, ex1 = cx - 250 * s, cx + 160 * s
    ey0, ey1 = cy - 95 * s, cy + 105 * s
    d.rectangle([ex0, ey0, ex1, ey1], fill=(254, 230, 170),
                outline=AMBER, width=max(3, int(4 * s)))
    d.polygon([(ex0, ey0), (ex1, ey0), ((ex0 + ex1) / 2, ey0 + 105 * s)],
              fill=(253, 214, 130), outline=AMBER)
    d.rectangle([ex1 - 78 * s, ey0 + 16 * s, ex1 - 16 * s, ey0 + 78 * s],
                fill=(255, 255, 255), outline=TEAL, width=max(2, int(3 * s)))
    _coin(d, ex1 - 47 * s, ey0 + 47 * s, 17 * s)
    # approval seal: teal disc with a white check
    sx, sy, sr = cx + 205 * s, cy + 55 * s, 52 * s
    d.ellipse([sx - sr, sy - sr, sx + sr, sy + sr], fill=TEAL, outline=AMBER,
              width=max(3, int(4 * s)))
    d.line([(sx - 26 * s, sy + 2 * s), (sx - 7 * s, sy + 22 * s),
            (sx + 28 * s, sy - 22 * s)], fill=(255, 255, 255),
           width=max(4, int(10 * s)), joint="curve")
    for i in range(3):  # motion ticks: the envelope is on its way
        mx = ex0 - 32 * s - i * 26 * s
        d.line([mx, cy - 20 * s, mx + 16 * s, cy - 20 * s], fill=TEAL,
               width=max(2, int(4 * s)))


def _illus_receipt(d, cx, cy, s):
    """Pick 5 - medical expenses: a receipt with a medical cross, kept
    and sorted before the year ends."""
    rx0, rx1 = cx - 130 * s, cx + 130 * s
    ry0, ry1 = cy - 118 * s, cy + 92 * s
    d.rectangle([rx0, ry0, rx1, ry1], fill=(255, 255, 255),
                outline=TEAL, width=max(3, int(4 * s)))
    step = 20 * s  # zigzag bottom edge
    x = rx0
    while x < rx1:
        d.polygon([(x, ry1), (x + step, ry1), (x + step / 2, ry1 + 16 * s)],
                  fill=(255, 255, 255), outline=TEAL)
        x += step
    ccx, ccy = cx, ry0 + 52 * s
    d.rectangle([ccx - 13 * s, ccy - 34 * s, ccx + 13 * s, ccy + 34 * s], fill=TEAL)
    d.rectangle([ccx - 34 * s, ccy - 13 * s, ccx + 34 * s, ccy + 13 * s], fill=TEAL)
    for i in range(3):
        ly = ry0 + 118 * s + i * 32 * s
        d.line([rx0 + 26 * s, ly, rx1 - 26 * s, ly], fill=BODY,
               width=max(2, int(4 * s)))
    _coin(d, cx + 205 * s, cy + 60 * s, 28 * s)
    _coin(d, cx - 208 * s, cy - 40 * s, 22 * s)


_ILLUS = [_illus_loss, _illus_gift, _illus_frame, _illus_envelope, _illus_receipt]


def _illustration(d, idx, y_after):
    """White stage panel + the pick's illustration, under the detail rows."""
    top = y_after - 6
    bottom = H - 84
    if bottom - top < 120:
        return
    d.rounded_rectangle([52, top, 668, bottom], radius=24,
                        fill=(255, 255, 255, 255), outline=TEAL + (255,), width=3)
    cx = W // 2
    cy = (top + bottom) // 2
    s = min((bottom - top - 24) / 300.0, 1.0)
    _ILLUS[idx % len(_ILLUS)](d, cx, cy, s)


def summary_card(data, out):
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img, "RGBA")
    random.seed(13)
    for _ in range(40):  # teal/amber confetti
        x, y = random.randint(0, W), random.randint(0, H)
        c = random.choice([(13, 148, 136, 120), (245, 158, 11, 130),
                           (45, 180, 165, 120), (253, 211, 77, 130)])
        d.rectangle([x, y, x + 10, y + 5], fill=c)
    # The conclusion is the hero of this card: largest type on an amber
    # banner, keyword on a teal pill. Checklist rows re-list each item
    # with its deadline, one checkmark per row by construction.
    full_title = data.get("summary_title", "まとめ：節税で一番大事なのは締切を守ること")
    if "：" in full_title:
        label, conclusion = full_title.split("：", 1)
    else:
        label, conclusion = "まとめ", full_title
    keyword = data.get("summary_keyword", "")
    d.text((W // 2, 52), label, font=F(BOLD, 34), fill=TEAL, anchor="mm",
           stroke_width=4, stroke_fill=AMBER_LIGHT)
    _badge(d, 660, 52, 26)
    head, tail = conclusion, ""
    if keyword and conclusion.endswith(keyword):
        head, tail = conclusion[:-len(keyword)], keyword
    d.rounded_rectangle([24, 88, 696, 300], radius=28, fill=AMBER + (255,),
                        outline=TEAL_DARK + (255,), width=4)
    d.text((W // 2, 140), head, font=F(BOLD, _fit(d, head, 44, 620)),
           fill=TEAL_DARK, anchor="mm")
    if tail:
        d.rounded_rectangle([92, 176, 628, 284], radius=24, fill=TEAL + (255,))
        d.text((W // 2, 231), tail, font=F(BOLD, _fit(d, tail, 84, 500)),
               fill=AMBER_LIGHT, anchor="mm")
    d.rounded_rectangle([24, 324, 696, 1108], radius=30, fill=(255, 255, 255, 255),
                        outline=TEAL + (255,), width=3)
    y = 340
    for i, p in enumerate(data["picks"]):
        color = ROW_COLORS[i % len(ROW_COLORS)]
        d.rounded_rectangle([44, y, 676, y + 138], radius=22, fill=color + (255,),
                            outline=TEAL + (255,), width=3)
        cx, cy, r = 88, y + 69, 24  # exactly one check per row
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=TEAL, outline=AMBER, width=3)
        d.line([(cx - 11, cy), (cx - 2, cy + 10), (cx + 13, cy - 11)], fill=(255, 255, 255), width=6, joint="curve")
        d.text((132, y + 14), p["name"], font=F(BOLD, _fit(d, p["name"], 31, 520)), fill=NAME)
        for j, ln in enumerate(p["summary_lines"]):
            d.text((132, y + 58 + j * 42), ln, font=F(BOLD, 25), fill=BODY)
        y += 152
    d.rounded_rectangle([24, 1132, 696, 1248], radius=22, fill=TEAL + (255,))
    d.text((W // 2, 1172), "※制度・期限は2026年11月24日時点の情報です", font=F(BOLD, 27), fill=(255, 255, 255), anchor="mm")
    d.text((W // 2, 1216), "※投資推奨ではありません", font=F(REG, 24), fill=(255, 255, 255), anchor="mm")
    img.save(out); return out


def build_all(data, outdir):
    os.makedirs(outdir, exist_ok=True)
    paths = [title_card(data, os.path.join(outdir, "card_title.png")),
             list_card(data, os.path.join(outdir, "card_list.png"))]
    for i in range(len(data["picks"])):
        paths.append(detail_card(data, i, os.path.join(outdir, f"card_detail_{i+1}.png")))
    paths.append(summary_card(data, os.path.join(outdir, "card_summary.png")))
    return paths
