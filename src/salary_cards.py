#!/usr/bin/env python3
"""Cards (720x1280) for the salary-trend one-off video
「給料は過去最高なのに手取りが増えない理由」.

Same visual identity as the tax series (mint-white background, deep teal
header band, amber accents) but the badge reads 「手取り」 and the title
card carries the full long title plus numeric hooks. Structure mirrors
the tax series: title -> list -> one detail card per item -> summary
card with exactly one checkmark per row, by construction."""
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
BADGE = "手取り"
FOOTER_LIST = "※数値は国税庁・協会けんぽ等の公表値。本人負担率は試算です"
FOOTER_DETAIL = "※数値は公表値です。本人負担率は試算です"


def _badge(d, cx, cy, r):
    """Series marker: teal disc, amber ring, 「手取り」 in light amber."""
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=TEAL, outline=AMBER, width=4)
    d.text((cx, cy - 1), BADGE, font=F(BOLD, int(r * 0.62)), fill=AMBER_LIGHT, anchor="mm")


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
    """Opening title card (Hide's rule): full title centered on screen,
    with concrete numeric hooks in amber pills under the title."""
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
    d.text((W // 2, 918), data["list_subtitle"], font=F(BOLD, 30),
           fill=AMBER_LIGHT, anchor="mm")
    _footer(d, FOOTER_LIST)
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
    _footer(d, FOOTER_LIST)
    img.save(out); return out


def detail_card(data, idx, out):
    p = data["picks"][idx]
    stage = p.get("stage", "")
    subtitle = f"{stage} {idx+1}／{len(data['picks'])}" if stage else f"理由 {idx+1}／{len(data['picks'])}"
    img, d = _base(p["name"], subtitle)
    # Message line (v3, Hide 2026-11-23): the card's one-line conclusion on
    # an amber band directly under the header, so a first-time viewer gets
    # the point before the detail rows. Rows shift down to make room.
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
    _footer(d, FOOTER_DETAIL)
    img.save(out); return out


# --- Detail-card illustrations (v2, Hide 2026-11-23): one flat PIL drawing
# per pick in the free band under the detail rows, so the switch between
# detail cards reads clearly. Palette stays teal x amber.

def _coin(d, cx, cy, r):
    """Gold yen coin."""
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=AMBER,
              outline=(217, 119, 6), width=max(2, int(r * 0.12)))
    ri = r * 0.66
    d.ellipse([cx - ri, cy - ri, cx + ri, cy + ri],
              outline=AMBER_LIGHT, width=max(2, int(r * 0.12)))
    d.text((cx, cy - 1), "\u00a5", font=F(BOLD, int(r * 1.02)),
           fill=(255, 255, 255), anchor="mm")


def _illus_chart(d, cx, cy, s):
    """Pick 1 - salary trend: line dips, then climbs past the start."""
    x0, x1 = cx - 255 * s, cx + 255 * s
    yb = cy + 115 * s
    d.line([x0, yb, x1, yb], fill=TEAL, width=max(3, int(5 * s)))
    d.line([x0, yb, x0, cy - 125 * s], fill=TEAL, width=max(3, int(5 * s)))
    pts = [(x0 + 35 * s, cy - 35 * s), (cx - 60 * s, cy + 60 * s),
           (cx + 70 * s, cy - 5 * s), (x1 - 30 * s, cy - 100 * s)]
    d.line(pts, fill=TEAL_DARK, width=max(4, int(9 * s)), joint="curve")
    for px, py in pts[:-1]:
        r = 11 * s
        d.ellipse([px - r, py - r, px + r, py + r], fill=AMBER,
                  outline=TEAL_DARK, width=max(2, int(3 * s)))
    _coin(d, pts[-1][0], pts[-1][1], 30 * s)


def _illus_pig(d, cx, cy, s):
    """Pick 3 - pension premium: piggy bank with a coin dropping in."""
    w3 = max(2, int(3 * s))
    for lx in (cx - 95 * s, cx + 55 * s):  # legs (behind body)
        d.rounded_rectangle([lx, cy + 78 * s, lx + 35 * s, cy + 118 * s],
                            radius=int(8 * s), fill=(253, 214, 130),
                            outline=AMBER, width=w3)
    d.arc([cx - 188 * s, cy - 32 * s, cx - 132 * s, cy + 28 * s],
          start=80, end=310, fill=AMBER, width=max(3, int(6 * s)))
    d.ellipse([cx - 155 * s, cy - 65 * s, cx + 155 * s, cy + 100 * s],
              fill=(254, 230, 170), outline=AMBER, width=max(3, int(4 * s)))
    d.polygon([(cx - 110 * s, cy - 42 * s), (cx - 76 * s, cy - 90 * s),
               (cx - 40 * s, cy - 40 * s)], fill=(253, 214, 130), outline=AMBER)
    d.ellipse([cx + 92 * s, cy - 8 * s, cx + 168 * s, cy + 52 * s],
              fill=(253, 214, 130), outline=AMBER, width=w3)
    for nx in (cx + 118 * s, cx + 142 * s):
        r = 4.5 * s
        d.ellipse([nx - r, cy + 22 * s - r, nx + r, cy + 22 * s + r], fill=TEAL_DARK)
    r = 7 * s
    d.ellipse([cx + 52 * s - r, cy - 22 * s - r, cx + 52 * s + r, cy - 22 * s + r],
              fill=TEAL_DARK)
    d.line([cx - 38 * s, cy - 56 * s, cx + 30 * s, cy - 56 * s],
           fill=TEAL_DARK, width=max(3, int(7 * s)))
    _coin(d, cx - 5 * s, cy - 118 * s, 30 * s)
    for mx in (cx - 52 * s, cx + 42 * s):  # motion ticks beside the coin
        d.line([mx, cy - 100 * s, mx, cy - 76 * s], fill=TEAL, width=max(2, int(4 * s)))


def _illus_medical(d, cx, cy, s):
    """Pick 4 - health / care insurance: medical cross badge + heart."""
    bx0, bx1 = cx - 205 * s, cx - 5 * s
    d.rounded_rectangle([bx0, cy - 105 * s, bx1, cy + 105 * s],
                        radius=int(24 * s), fill=(255, 255, 255),
                        outline=TEAL, width=max(3, int(5 * s)))
    ccx = (bx0 + bx1) / 2
    d.rectangle([ccx - 20 * s, cy - 62 * s, ccx + 20 * s, cy + 62 * s], fill=TEAL)
    d.rectangle([ccx - 62 * s, cy - 20 * s, ccx + 62 * s, cy + 20 * s], fill=TEAL)
    hx, hy, r = cx + 128 * s, cy - 2 * s, 88 * s
    d.ellipse([hx - 1.05 * r, hy - 0.88 * r, hx + 0.05 * r, hy + 0.22 * r], fill=AMBER)
    d.ellipse([hx - 0.05 * r, hy - 0.88 * r, hx + 1.05 * r, hy + 0.22 * r], fill=AMBER)
    d.polygon([(hx - 1.0 * r, hy - 0.08 * r), (hx + 1.0 * r, hy - 0.08 * r),
               (hx, hy + 1.05 * r)], fill=AMBER)
    hr = 13 * s
    d.ellipse([hx - 0.52 * r - hr, hy - 0.52 * r - hr, hx - 0.52 * r + hr,
               hy - 0.52 * r + hr], fill=AMBER_LIGHT)


def _illus_wallet(d, cx, cy, s):
    """Pick 2 - total employee burden: pay envelope, coins deducted away."""
    ex0, ex1 = cx - 245 * s, cx + 25 * s
    ey0, ey1 = cy - 55 * s, cy + 105 * s
    d.rectangle([ex0, ey0, ex1, ey1], fill=(254, 230, 170),
                outline=AMBER, width=max(3, int(4 * s)))
    d.polygon([(ex0, ey0), (ex1, ey0), ((ex0 + ex1) / 2, ey0 + 88 * s)],
              fill=(253, 214, 130), outline=AMBER)
    _coin(d, (ex0 + ex1) / 2, cy + 42 * s, 30 * s)
    ax0, ay0 = cx + 52 * s, cy - 110 * s
    ax1, ay1 = cx + 228 * s, cy + 38 * s
    n = 8  # dashed trajectory running above the trail of shrinking coins
    for i in range(n):
        if i % 2 == 0:
            t0, t1 = i / n, (i + 0.82) / n
            d.line([ax0 + (ax1 - ax0) * t0, ay0 + (ay1 - ay0) * t0,
                    ax0 + (ax1 - ax0) * t1, ay0 + (ay1 - ay0) * t1],
                   fill=TEAL, width=max(3, int(5 * s)))
    ux, uy = 0.765, 0.643  # unit vector along the dashed line
    tip = (ax1 + 18 * s * ux, ay1 + 18 * s * uy)
    b1 = (ax1 - 4 * s * ux - 14 * s * uy, ay1 - 4 * s * uy + 14 * s * ux)
    b2 = (ax1 - 4 * s * ux + 14 * s * uy, ay1 - 4 * s * uy - 14 * s * ux)
    d.polygon([tip, b1, b2], fill=TEAL)
    _coin(d, cx + 100 * s, cy - 30 * s, 26 * s)
    _coin(d, cx + 163 * s, cy + 18 * s, 21 * s)
    _coin(d, cx + 218 * s, cy + 62 * s, 16 * s)

def _illus_wall(d, cx, cy, s):
    """Pick 5 - tax threshold: arrow rising over a brick wall (the 'wall')."""
    wx0 = cx - 262 * s
    wy, bh = cy + 2 * s, 42 * s
    joints = [[0, 103, 203, 310], [0, 52, 155, 258, 310], [0, 103, 203, 310]]
    for i, js in enumerate(joints):
        yy = wy + i * bh
        for j, (a, b) in enumerate(zip(js, js[1:])):
            d.rounded_rectangle([wx0 + (a + 3) * s, yy + 3 * s,
                                 wx0 + (b - 3) * s, yy + bh - 3 * s],
                                radius=int(6 * s),
                                fill=(253, 214, 130) if (i + j) % 2 else AMBER_LIGHT,
                                outline=(217, 119, 6), width=max(2, int(2 * s)))
    pts = [(cx - 238 * s, cy + 108 * s), (cx - 140 * s, cy - 12 * s),
           (cx - 10 * s, cy - 68 * s), (cx + 218 * s, cy - 54 * s)]
    d.line(pts, fill=TEAL, width=max(4, int(15 * s)), joint="curve")
    d.polygon([(cx + 262 * s, cy - 57 * s), (cx + 206 * s, cy - 84 * s),
               (cx + 210 * s, cy - 26 * s)], fill=TEAL)

# v4 order (前提 -> 核心 -> 内訳1 -> 内訳2 -> 対比):
# chart, wallet (pay envelope), pig, medical, wall.
_ILLUS = [_illus_chart, _illus_wallet, _illus_pig, _illus_medical, _illus_wall]


def _illustration(d, idx, y_after):
    """White stage panel + the pick's illustration, under the detail rows.
    y_after is the y just past the last row slot (last row bottom = y_after-20)."""
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
    summary_title = data.get("summary_title", "まとめ：手取りが増えない理由")
    d.text((W // 2, 70), summary_title, font=F(BOLD, _fit(d, summary_title, 36, 540)),
           fill=TEAL, anchor="mm", stroke_width=5, stroke_fill=AMBER_LIGHT)
    _badge(d, 660, 66, 27)
    d.rounded_rectangle([24, 128, 696, 1108], radius=30, fill=(255, 255, 255, 255),
                        outline=TEAL + (255,), width=3)
    y = 148
    for i, p in enumerate(data["picks"]):
        color = ROW_COLORS[i % len(ROW_COLORS)]
        d.rounded_rectangle([44, y, 676, y + 172], radius=22, fill=color + (255,),
                            outline=TEAL + (255,), width=3)
        cx, cy, r = 92, y + 86, 27  # exactly one check per row
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=TEAL, outline=AMBER, width=3)
        d.line([(cx - 13, cy), (cx - 3, cy + 11), (cx + 15, cy - 12)], fill=(255, 255, 255), width=7, joint="curve")
        d.text((140, y + 18), p["name"], font=F(BOLD, 33), fill=NAME)
        for j, ln in enumerate(p["summary_lines"]):
            d.text((140, y + 66 + j * 46), ln, font=F(BOLD, 27), fill=BODY)
        y += 188
    d.rounded_rectangle([24, 1132, 696, 1248], radius=22, fill=TEAL + (255,))
    d.text((W // 2, 1172), "※数値は国税庁・協会けんぽ等の公表値です", font=F(BOLD, 27), fill=(255, 255, 255), anchor="mm")
    d.text((W // 2, 1216), "本人負担率は各料率からの試算です", font=F(REG, 24), fill=(255, 255, 255), anchor="mm")
    img.save(out); return out


def build_all(data, outdir):
    os.makedirs(outdir, exist_ok=True)
    paths = [title_card(data, os.path.join(outdir, "card_title.png")),
             list_card(data, os.path.join(outdir, "card_list.png"))]
    for i in range(len(data["picks"])):
        paths.append(detail_card(data, i, os.path.join(outdir, f"card_detail_{i+1}.png")))
    paths.append(summary_card(data, os.path.join(outdir, "card_summary.png")))
    return paths
