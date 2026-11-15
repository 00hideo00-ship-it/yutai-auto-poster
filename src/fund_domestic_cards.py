#!/usr/bin/env python3
"""Cards (720x1280) for the domestic investment-trust edition.

Same fund-series layout, fonts, card structure and timing as fund_cards.py,
but a distinguishable palette variant for the domestic edition: white
background, deep indigo (藍 ai) header band, gold accents, indigo/gold
pastel rows, and a round indigo badge with gold ring and the characters
「国内」 in the header of every card (overseas edition uses violet/plum
with 「投信」). The summary card draws exactly ONE checkmark per row,
by construction."""
from PIL import Image, ImageDraw
import os, random
import cards as _c

W, H = _c.W, _c.H
F, BOLD, REG = _c.F, _c.BOLD, _c.REG

BG = (255, 255, 255)          # white
INDIGO = (38, 49, 107)        # deep ai indigo, main color
INDIGO_DARK = (22, 30, 68)    # title stroke / name text
GOLD = (232, 168, 18)         # gold accent
GOLD_LIGHT = (255, 201, 60)   # badge text / light gold
NAME = (22, 30, 68)           # row title text
BODY = (55, 65, 81)           # row body text (same as other series)
ROW_COLORS = [(203, 213, 242), (252, 216, 116), (182, 196, 235),
              (255, 226, 148), (216, 224, 246)]
FOOTER_LIST = "※分配金には元本の払戻しが含まれる場合があります"
FOOTER_POINTS = "※投資推奨ではありません・分配金は変動・中止される場合があります"


def _badge(d, cx, cy, r):
    """Series marker: indigo disc, gold ring, 「国内」 in gold."""
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=INDIGO, outline=GOLD, width=4)
    d.text((cx, cy - 1), "国内", font=F(BOLD, int(r * 0.78)), fill=GOLD_LIGHT, anchor="mm")


def _base(title, subtitle):
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img, "RGBA")
    random.seed(3)
    for _ in range(28):  # soft indigo/gold bubbles, same rhythm as other series
        x, y = random.randint(-40, W), random.randint(-40, H)
        r = random.randint(8, 42)
        c = random.choice([(38, 49, 107, 20), (232, 168, 18, 24), (90, 110, 180, 24)])
        d.ellipse([x - r, y - r, x + r, y + r], fill=c)
    for _ in range(8):  # tiny gold rings scattered in the background
        x, y = random.randint(20, W - 20), random.randint(220, H - 60)
        r = random.randint(9, 17)
        d.ellipse([x - r, y - r, x + r, y + r], outline=(232, 168, 18, 110), width=3)
    # deep-indigo header band holding title + subtitle
    d.rounded_rectangle([16, 16, 704, 196], radius=28, fill=INDIGO + (255,))
    title_size = 58 if len(title) <= 9 else 50
    d.text((W // 2, 78), title, font=F(BOLD, title_size), fill=GOLD_LIGHT, anchor="mm",
           stroke_width=6, stroke_fill=INDIGO_DARK)
    sub_size = 34 if len(subtitle) <= 15 else (26 if len(subtitle) <= 24 else 22)
    d.rounded_rectangle([40, 118, 680, 178], radius=30, fill=GOLD + (255,))
    d.text((W // 2, 148), subtitle, font=F(BOLD, sub_size), fill=INDIGO_DARK, anchor="mm")
    _badge(d, 646, 76, 37)  # series marker
    return img, d


def _rows(d, picks, lines_key, y0=205):
    y = y0
    for i, p in enumerate(picks):
        color = ROW_COLORS[i % len(ROW_COLORS)]
        d.rounded_rectangle([28, y, 692, y + 178], radius=26, fill=color + (255,),
                            outline=INDIGO + (255,), width=3)
        head = f"{i+1}) {p['short_name']}"
        head_size = 35 if len(head) <= 19 else 31
        d.text((48, y + 14), head, font=F(BOLD, head_size), fill=NAME)
        for j, ln in enumerate(p[lines_key]):
            d.text((48, y + 66 + j * 50), ln, font=F(BOLD, 30), fill=BODY)
        y += 192


def _footer(d, text):
    d.text((W // 2, H - 42), text, font=F(REG, 21), fill=INDIGO, anchor="mm")


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
    for _ in range(40):  # indigo/gold confetti, same rhythm as other series
        x, y = random.randint(0, W), random.randint(0, H)
        c = random.choice([(38, 49, 107, 120), (232, 168, 18, 130),
                           (90, 110, 180, 120), (255, 201, 60, 130)])
        d.rectangle([x, y, x + 10, y + 5], fill=c)
    d.text((W // 2, 70), f"まとめ：{data['title_label']} 5選", font=F(BOLD, 40),
           fill=INDIGO, anchor="mm", stroke_width=5, stroke_fill=GOLD_LIGHT)
    _badge(d, 652, 68, 30)  # series marker
    d.rounded_rectangle([24, 128, 696, 1108], radius=30, fill=(255, 255, 255, 255),
                        outline=INDIGO + (255,), width=3)
    y = 148
    for i, p in enumerate(data["picks"]):
        color = ROW_COLORS[i % len(ROW_COLORS)]
        d.rounded_rectangle([44, y, 676, y + 172], radius=22, fill=color + (255,),
                            outline=INDIGO + (255,), width=3)
        cx, cy, r = 92, y + 86, 27  # exactly one check per row
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=INDIGO, outline=GOLD, width=3)
        d.line([(cx - 13, cy), (cx - 3, cy + 11), (cx + 15, cy - 12)], fill=(255, 255, 255), width=7, joint="curve")
        head = p["short_name"]
        head_size = 33 if len(head) <= 17 else 29
        d.text((140, y + 18), head, font=F(BOLD, head_size), fill=NAME)
        for j, ln in enumerate(p["summary_lines"]):
            d.text((140, y + 66 + j * 46), ln, font=F(BOLD, 27), fill=BODY)
        y += 188
    d.rounded_rectangle([24, 1132, 696, 1248], radius=22, fill=INDIGO + (255,))
    d.text((W // 2, 1172), "⚠ 投資推奨ではありません", font=F(BOLD, 29), fill=(255, 255, 255), anchor="mm")
    d.text((W // 2, 1216), "分配金には元本の払戻しが含まれる場合があります", font=F(REG, 24), fill=(255, 255, 255), anchor="mm")
    img.save(out); return out


def build_all(data, outdir):
    os.makedirs(outdir, exist_ok=True)
    return [
        title_card(data, os.path.join(outdir, "card_title.png")),
        list_card(data, os.path.join(outdir, "card_list.png")),
        points_card(data, os.path.join(outdir, "card_points.png")),
        summary_card(data, os.path.join(outdir, "card_summary.png")),
    ]




def title_card(data, out):
    """Opening title card (Hide's rule, 2026-11-15): the video title is
    centered on screen so viewers know the topic immediately."""
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img, "RGBA")
    random.seed(3)
    for _ in range(28):
        x, y = random.randint(-40, W), random.randint(-40, H)
        r = random.randint(8, 42)
        c = random.choice([(38, 49, 107, 20), (232, 168, 18, 24), (90, 110, 180, 24)])
        d.ellipse([x - r, y - r, x + r, y + r], fill=c)
    for _ in range(8):
        x, y = random.randint(20, W - 20), random.randint(220, H - 60)
        r = random.randint(9, 17)
        d.ellipse([x - r, y - r, x + r, y + r], outline=(232, 168, 18, 110), width=3)
    d.rounded_rectangle([36, 400, 684, 880], radius=36, fill=INDIGO + (255,))
    _badge(d, 646, 76, 37)
    d.text((W // 2, 552), data["title_label"], font=F(BOLD, 76), fill=GOLD_LIGHT,
           anchor="mm", stroke_width=6, stroke_fill=INDIGO_DARK)
    d.text((W // 2, 672), "5選", font=F(BOLD, 88), fill=GOLD_LIGHT,
           anchor="mm", stroke_width=6, stroke_fill=INDIGO_DARK)
    d.rounded_rectangle([120, 756, 600, 830], radius=37, fill=GOLD + (255,))
    d.text((W // 2, 793), data["list_subtitle"], font=F(BOLD, 28),
           fill=INDIGO_DARK, anchor="mm")
    d.text((W // 2, H - 42), FOOTER_POINTS, font=F(REG, 20), fill=INDIGO_DARK, anchor="mm")
    img.save(out); return out

