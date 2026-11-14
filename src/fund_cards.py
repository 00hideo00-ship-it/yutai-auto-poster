#!/usr/bin/env python3
"""Cards (720x1280) for the high-distribution investment-trust (fund) series.

Third visual identity in the family: same layout, fonts, card structure and
timing as the yutai / dividend series, but a premium "fund/trust" look —
light lavender-white background, deep violet/plum header band, gold accents,
pastel violet/gold rows, and a round plum badge with gold ring and the
characters 「投信」 in the header of every card (instead of the dividend
series' gold ¥ coin). The summary card draws exactly ONE checkmark per row,
by construction."""
from PIL import Image, ImageDraw
import os, random
import cards as _c

W, H = _c.W, _c.H
F, BOLD, REG = _c.F, _c.BOLD, _c.REG

BG = (250, 247, 255)          # light lavender-white
PLUM = (75, 32, 100)          # deep violet/plum, main color
PLUM_DARK = (46, 16, 66)      # title stroke / name text
GOLD = (232, 168, 18)         # gold accent
GOLD_LIGHT = (255, 201, 60)   # badge text / light gold
NAME = (46, 16, 66)           # row title text
BODY = (55, 65, 81)           # row body text (same as other series)
ROW_COLORS = [(226, 208, 248), (252, 216, 116), (206, 186, 240),
              (255, 226, 148), (216, 198, 246)]
FOOTER_LIST = "※分配金には元本の払戻しが含まれる場合があります"
FOOTER_POINTS = "※投資推奨ではありません・分配金は変動・中止される場合があります"


def _badge(d, cx, cy, r):
    """Series marker: plum disc, gold ring, 「投信」 in gold."""
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=PLUM, outline=GOLD, width=4)
    d.text((cx, cy - 1), "投信", font=F(BOLD, int(r * 0.78)), fill=GOLD_LIGHT, anchor="mm")


def _base(title, subtitle):
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img, "RGBA")
    random.seed(3)
    for _ in range(28):  # soft violet/gold bubbles, same rhythm as other series
        x, y = random.randint(-40, W), random.randint(-40, H)
        r = random.randint(8, 42)
        c = random.choice([(117, 66, 168, 22), (232, 168, 18, 24), (168, 130, 220, 26)])
        d.ellipse([x - r, y - r, x + r, y + r], fill=c)
    for _ in range(8):  # tiny gold rings scattered in the background
        x, y = random.randint(20, W - 20), random.randint(220, H - 60)
        r = random.randint(9, 17)
        d.ellipse([x - r, y - r, x + r, y + r], outline=(232, 168, 18, 110), width=3)
    # deep-plum header band holding title + subtitle
    d.rounded_rectangle([16, 16, 704, 196], radius=28, fill=PLUM + (255,))
    title_size = 58 if len(title) <= 9 else 50
    d.text((W // 2, 78), title, font=F(BOLD, title_size), fill=GOLD_LIGHT, anchor="mm",
           stroke_width=6, stroke_fill=PLUM_DARK)
    sub_size = 34 if len(subtitle) <= 15 else (26 if len(subtitle) <= 24 else 22)
    d.rounded_rectangle([40, 118, 680, 178], radius=30, fill=GOLD + (255,))
    d.text((W // 2, 148), subtitle, font=F(BOLD, sub_size), fill=PLUM_DARK, anchor="mm")
    _badge(d, 646, 76, 37)  # series marker
    return img, d


def _rows(d, picks, lines_key, y0=205):
    y = y0
    for i, p in enumerate(picks):
        color = ROW_COLORS[i % len(ROW_COLORS)]
        d.rounded_rectangle([28, y, 692, y + 178], radius=26, fill=color + (255,),
                            outline=PLUM + (255,), width=3)
        head = f"{i+1}) {p['short_name']}"
        head_size = 35 if len(head) <= 19 else 31
        d.text((48, y + 14), head, font=F(BOLD, head_size), fill=NAME)
        for j, ln in enumerate(p[lines_key]):
            d.text((48, y + 66 + j * 50), ln, font=F(BOLD, 30), fill=BODY)
        y += 192


def _footer(d, text):
    d.text((W // 2, H - 42), text, font=F(REG, 21), fill=PLUM, anchor="mm")


def list_card(data, out):
    img, d = _base(f"{data['title_label']} 5選", data["list_subtitle"])
    _rows(d, data["picks"], "list_lines")
    _footer(d, FOOTER_LIST)
    img.save(out); return out


def points_card(data, out):
    img, d = _base("おすすめポイント", data["points_subtitle"])
    _rows(d, data["picks"], "point_lines")
    _footer(d, FOOTER_POINTS)
    img.save(out); return out


def summary_card(data, out):
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img, "RGBA")
    random.seed(11)
    for _ in range(40):  # violet/gold confetti, same rhythm as other series
        x, y = random.randint(0, W), random.randint(0, H)
        c = random.choice([(117, 66, 168, 120), (232, 168, 18, 130),
                           (168, 130, 220, 120), (255, 201, 60, 130)])
        d.rectangle([x, y, x + 10, y + 5], fill=c)
    d.text((W // 2, 70), f"まとめ：{data['title_label']} 5選", font=F(BOLD, 40),
           fill=PLUM, anchor="mm", stroke_width=5, stroke_fill=GOLD_LIGHT)
    _badge(d, 652, 68, 30)  # series marker
    d.rounded_rectangle([24, 128, 696, 1108], radius=30, fill=(255, 255, 255, 255),
                        outline=PLUM + (255,), width=3)
    y = 148
    for i, p in enumerate(data["picks"]):
        color = ROW_COLORS[i % len(ROW_COLORS)]
        d.rounded_rectangle([44, y, 676, y + 172], radius=22, fill=color + (255,),
                            outline=PLUM + (255,), width=3)
        cx, cy, r = 92, y + 86, 27  # exactly one check per row
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=PLUM, outline=GOLD, width=3)
        d.line([(cx - 13, cy), (cx - 3, cy + 11), (cx + 15, cy - 12)], fill=(255, 255, 255), width=7, joint="curve")
        head = p["short_name"]
        head_size = 33 if len(head) <= 17 else 29
        d.text((140, y + 18), head, font=F(BOLD, head_size), fill=NAME)
        for j, ln in enumerate(p["summary_lines"]):
            d.text((140, y + 66 + j * 46), ln, font=F(BOLD, 27), fill=BODY)
        y += 188
    d.rounded_rectangle([24, 1132, 696, 1248], radius=22, fill=PLUM + (255,))
    d.text((W // 2, 1172), "⚠ 投資推奨ではありません", font=F(BOLD, 29), fill=(255, 255, 255), anchor="mm")
    d.text((W // 2, 1216), "分配金には元本の払戻しが含まれる場合があります", font=F(REG, 24), fill=(255, 255, 255), anchor="mm")
    img.save(out); return out


def build_all(data, outdir):
    os.makedirs(outdir, exist_ok=True)
    return [
        list_card(data, os.path.join(outdir, "card_list.png")),
        points_card(data, os.path.join(outdir, "card_points.png")),
        summary_card(data, os.path.join(outdir, "card_summary.png")),
    ]
