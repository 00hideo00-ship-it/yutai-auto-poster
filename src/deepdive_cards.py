#!/usr/bin/env python3
"""Cards (720x1280) for the weekly deep-dive series (1 stock, 61s).

Fixed deep-dive design (Hide's decision): dark navy x light blue,
round badge with 「深掘り」 in the header of every card. Same layout
rhythm, fonts and timing as the other 61s series. The summary card
draws exactly ONE checkmark per row, by construction. Title card keeps
the title centered on screen (Hide's rule, 2026-11-15)."""
from PIL import Image, ImageDraw
import os, random
import cards as _c

W, H = _c.W, _c.H
F, BOLD, REG = _c.F, _c.BOLD, _c.REG

BG = (13, 27, 62)            # dark navy
NAVY_DARK = (8, 17, 40)      # darkest navy (title stroke / pills)
LIGHT_BLUE = (147, 197, 253)  # light blue accent
LIGHT_BLUE_SOFT = (191, 219, 254)
ROW_LIGHT = (219, 234, 254)  # row fill
WHITE = (255, 255, 255)
NAME = (13, 27, 62)          # row title text
BODY = (30, 58, 95)          # row body text
FOOTER_TEXT = "※投資推奨ではありません・優待は変更される場合があります"


def _badge(d, cx, cy, r):
    """Series marker: light-blue disc, navy ring, 「深掘り」 in navy."""
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=LIGHT_BLUE, outline=NAVY_DARK, width=4)
    size = 24
    while size > 14 and d.textlength("深掘り", font=F(BOLD, size)) > r * 2 - 12:
        size -= 1
    d.text((cx, cy - 1), "深掘り", font=F(BOLD, size), fill=NAVY_DARK, anchor="mm")


def _bubbles(d):
    random.seed(3)
    for _ in range(28):
        x, y = random.randint(-40, W), random.randint(-40, H)
        r = random.randint(8, 42)
        c = random.choice([(147, 197, 253, 26), (191, 219, 254, 30), (255, 255, 255, 18)])
        d.ellipse([x - r, y - r, x + r, y + r], fill=c)
    for _ in range(8):
        x, y = random.randint(20, W - 20), random.randint(220, H - 60)
        r = random.randint(9, 17)
        d.ellipse([x - r, y - r, x + r, y + r], outline=(147, 197, 253, 120), width=3)


def _base(title, subtitle):
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img, "RGBA")
    _bubbles(d)
    # light-blue header band holding title + subtitle
    d.rounded_rectangle([16, 16, 704, 196], radius=28, fill=LIGHT_BLUE + (255,))
    size = 50
    while size > 24 and d.textlength(title, font=F(BOLD, size)) > 500:
        size -= 2
    d.text((W // 2 - 20, 78), title, font=F(BOLD, size), fill=NAVY_DARK, anchor="mm",
           stroke_width=5, stroke_fill=WHITE)
    sub_size = 34 if len(subtitle) <= 15 else (26 if len(subtitle) <= 24 else 22)
    d.rounded_rectangle([40, 118, 680, 178], radius=30, fill=NAVY_DARK + (255,))
    d.text((W // 2, 148), subtitle, font=F(BOLD, sub_size), fill=LIGHT_BLUE, anchor="mm")
    _badge(d, 646, 76, 37)  # series marker
    return img, d


def _footer(d, text=FOOTER_TEXT):
    d.text((W // 2, H - 42), text, font=F(REG, 21), fill=LIGHT_BLUE, anchor="mm")


def _detail_rows(d, lines, y0=226):
    """Four white bullet rows, auto-fitting each line to the row width."""
    y = y0
    for ln in lines:
        d.rounded_rectangle([36, y, 684, y + 118], radius=24, fill=WHITE + (255,),
                            outline=LIGHT_BLUE + (255,), width=3)
        d.ellipse([58, y + 44, 88, y + 74], fill=LIGHT_BLUE)
        size = 31
        while size > 18 and d.textlength(ln, font=F(BOLD, size)) > 556:
            size -= 1
        d.text((112, y + 59), ln, font=F(BOLD, size), fill=BODY, anchor="lm")
        y += 148
    return y


def title_card(data, out):
    """Opening title card (Hide's rule, 2026-11-15): the video title is
    centered on screen so viewers know the topic immediately.
    Hook rule (2026-11-18): the hook pill below the title carries the
    concrete amount / deadline the viewer gains, not just the theme."""
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img, "RGBA")
    _bubbles(d)
    d.rounded_rectangle([36, 400, 684, 880], radius=36, fill=LIGHT_BLUE + (255,))
    _badge(d, 646, 76, 37)
    d.text((W // 2, 552), data["stock"]["name"], font=F(BOLD, 76), fill=NAVY_DARK,
           anchor="mm", stroke_width=6, stroke_fill=WHITE)
    d.text((W // 2, 672), data.get("title_angle_label", "株主優待 深掘り"),
           font=F(BOLD, 64), fill=NAVY_DARK,
           anchor="mm", stroke_width=5, stroke_fill=WHITE)
    d.rounded_rectangle([120, 756, 600, 830], radius=37, fill=NAVY_DARK + (255,))
    d.text((W // 2, 793),
           f"コード {data['stock']['code']}・{data['stock']['market']}",
           font=F(BOLD, 28), fill=LIGHT_BLUE, anchor="mm")
    hook = data.get("title_hook", "")
    if hook:
        d.rounded_rectangle([70, 920, 650, 1000], radius=40, fill=NAVY_DARK + (255,),
                            outline=LIGHT_BLUE + (255,), width=3)
        size = 28
        while size > 18 and d.textlength(hook, font=F(BOLD, size)) > 540:
            size -= 1
        d.text((W // 2, 960), hook, font=F(BOLD, size), fill=LIGHT_BLUE, anchor="mm")
    d.text((W // 2, H - 42), FOOTER_TEXT, font=F(REG, 20), fill=LIGHT_BLUE, anchor="mm")
    img.save(out); return out


def basic_card(data, out):
    img, d = _base("基本情報", data["stock"]["business_line"])
    _detail_rows(d, data["basic_lines"])
    _footer(d)
    img.save(out); return out


def deep_card(data, card, out):
    img, d = _base(card["title"], card["subtitle"])
    _detail_rows(d, card["lines"])
    _footer(d)
    img.save(out); return out


def caution_card(data, out):
    img, d = _base("注意点", data.get("caution_subtitle", "条件と期限に注意"))
    _detail_rows(d, data["caution_lines"])
    _footer(d)
    img.save(out); return out


def summary_card(data, out):
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img, "RGBA")
    random.seed(11)
    for _ in range(40):  # light-blue confetti, same rhythm as other series
        x, y = random.randint(0, W), random.randint(0, H)
        c = random.choice([(147, 197, 253, 120), (191, 219, 254, 130),
                           (255, 255, 255, 110), (96, 165, 250, 120)])
        d.rectangle([x, y, x + 10, y + 5], fill=c)
    title = f"まとめ：{data['stock']['name']} 深掘り"
    tsize = 40
    while tsize > 24 and d.textlength(title, font=F(BOLD, tsize)) > 540:
        tsize -= 2
    d.text((W // 2 - 20, 70), title, font=F(BOLD, tsize),
           fill=LIGHT_BLUE, anchor="mm", stroke_width=5, stroke_fill=NAVY_DARK)
    _badge(d, 652, 68, 30)  # series marker
    d.rounded_rectangle([24, 128, 696, 1108], radius=30, fill=WHITE + (255,),
                        outline=LIGHT_BLUE + (255,), width=3)
    y = 152
    for row in data["summary_rows"]:
        d.rounded_rectangle([44, y, 676, y + 272], radius=22, fill=ROW_LIGHT + (255,),
                            outline=LIGHT_BLUE + (255,), width=3)
        cx, cy, r = 96, y + 136, 34  # exactly one check per row
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=LIGHT_BLUE, outline=NAVY_DARK, width=3)
        d.line([(cx - 16, cy), (cx - 4, cy + 14), (cx + 18, cy - 15)], fill=NAVY_DARK, width=8, joint="curve")
        head = row["head"]
        head_size = 38
        while head_size > 26 and d.textlength(head, font=F(BOLD, head_size)) > 500:
            head_size -= 1
        d.text((160, y + 26), head, font=F(BOLD, head_size), fill=NAME)
        for j, ln in enumerate(row["lines"]):
            lsize = 30
            while lsize > 20 and d.textlength(ln, font=F(BOLD, lsize)) > 500:
                lsize -= 1
            d.text((160, y + 104 + j * 56), ln, font=F(BOLD, lsize), fill=BODY)
        y += 296
    # extra space below the three rows: key dates reminder
    d.rounded_rectangle([24, 1132, 696, 1248], radius=22, fill=NAVY_DARK + (255,))
    d.text((W // 2, 1172), "⚠ 投資推奨ではありません", font=F(BOLD, 29), fill=WHITE, anchor="mm")
    d.text((W // 2, 1216), "優待・配当は変更される場合があります", font=F(REG, 24), fill=LIGHT_BLUE, anchor="mm")
    img.save(out); return out


def build_all_long(data, outdir):
    os.makedirs(outdir, exist_ok=True)
    paths = [
        title_card(data, os.path.join(outdir, "card_title.png")),
        basic_card(data, os.path.join(outdir, "card_basic.png")),
    ]
    for i, card in enumerate(data["deep_cards"]):
        paths.append(deep_card(data, card, os.path.join(outdir, f"card_deep_{i + 1}.png")))
    paths.append(caution_card(data, os.path.join(outdir, "card_caution.png")))
    paths.append(summary_card(data, os.path.join(outdir, "card_summary.png")))
    return paths
