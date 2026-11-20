#!/usr/bin/env python3
"""Cards (720x1280) for the weekly bargain series (5 stocks, 61s).

Fixed bargain design (Hide's decision): crimson red x charcoal, round
badge with 「狙い目」 in the header of every card. Same layout rhythm,
fonts and timing as the other 61s series. The summary card draws exactly
ONE checkmark per row, by construction. Title card keeps the title centered
on screen (Hide's rule, 2026-11-15) and leads with a concrete hook:
the Nikkei's weekly drop in yen and percent.
Each stock card shows the weekly drop, the reason for the drop and the
caution points; nothing here recommends buying."""
from PIL import Image, ImageDraw
import os, random
import cards as _c

W, H = _c.W, _c.H
F, BOLD, REG = _c.F, _c.BOLD, _c.REG

BG = (31, 41, 55)            # charcoal
CHARCOAL_DARK = (17, 24, 39)  # darkest charcoal (title stroke / pills)
CRIMSON = (220, 38, 38)      # crimson red accent
CRIMSON_DARK = (153, 27, 27)
CRIMSON_LIGHT = (254, 202, 202)
CRIMSON_SOFT = (254, 226, 226)
ROW_LIGHT = (255, 241, 242)  # row fill
WHITE = (255, 255, 255)
NAME = (31, 41, 55)          # row title text
BODY = (51, 65, 85)          # row body text
FOOTER_TEXT = "※投資推奨ではありません・株価はさらに下がる場合があります"


def _badge(d, cx, cy, r):
    """Series marker: crimson disc, white ring, 「狙い目」 in white."""
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=CRIMSON, outline=WHITE, width=4)
    size = 24
    while size > 14 and d.textlength("狙い目", font=F(BOLD, size)) > r * 2 - 12:
        size -= 1
    d.text((cx, cy - 1), "狙い目", font=F(BOLD, size), fill=WHITE, anchor="mm")


def _bubbles(d):
    random.seed(3)
    for _ in range(28):
        x, y = random.randint(-40, W), random.randint(-40, H)
        r = random.randint(8, 42)
        c = random.choice([(220, 38, 38, 26), (254, 202, 202, 30), (255, 255, 255, 18)])
        d.ellipse([x - r, y - r, x + r, y + r], fill=c)
    for _ in range(8):
        x, y = random.randint(20, W - 20), random.randint(220, H - 60)
        r = random.randint(9, 17)
        d.ellipse([x - r, y - r, x + r, y + r], outline=(220, 38, 38, 120), width=3)


def _base(title, subtitle):
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img, "RGBA")
    _bubbles(d)
    # crimson header band holding title + subtitle
    d.rounded_rectangle([16, 16, 704, 196], radius=28, fill=CRIMSON + (255,))
    size = 50
    while size > 24 and d.textlength(title, font=F(BOLD, size)) > 500:
        size -= 2
    d.text((W // 2 - 20, 78), title, font=F(BOLD, size), fill=WHITE, anchor="mm",
           stroke_width=5, stroke_fill=CHARCOAL_DARK)
    sub_size = 34 if len(subtitle) <= 15 else (26 if len(subtitle) <= 24 else 22)
    d.rounded_rectangle([40, 118, 680, 178], radius=30, fill=CHARCOAL_DARK + (255,))
    d.text((W // 2, 148), subtitle, font=F(BOLD, sub_size), fill=CRIMSON_LIGHT, anchor="mm")
    _badge(d, 646, 76, 37)  # series marker
    return img, d


def _footer(d, text=FOOTER_TEXT):
    d.text((W // 2, H - 42), text, font=F(REG, 21), fill=CRIMSON_LIGHT, anchor="mm")


def _fmt_yen(v):
    if float(v) == int(v):
        return f"{int(v):,}円"
    return f"{v:,}円"


def title_card(data, out):
    """Opening title card (Hide's rule, 2026-11-15): the video title is
    centered on screen so viewers know the topic immediately. The first
    3 seconds carry a concrete hook: the Nikkei's weekly drop."""
    m = data["market"]
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img, "RGBA")
    _bubbles(d)
    _badge(d, 646, 76, 37)
    d.rounded_rectangle([36, 380, 684, 900], radius=36, fill=WHITE + (255,))
    d.text((W // 2, 470), f"日経平均 週間 {m['weekly_change_pct']}%",
           font=F(BOLD, 58), fill=CRIMSON,
           anchor="mm", stroke_width=5, stroke_fill=WHITE)
    d.text((W // 2, 552), f"1週間で{abs(m['weekly_change_yen']):,.0f}円安",
           font=F(BOLD, 52), fill=CHARCOAL_DARK,
           anchor="mm", stroke_width=5, stroke_fill=WHITE)
    line3 = m.get("title_line3", "AI株が軒並み急落")
    size3 = 52
    while size3 > 24 and d.textlength(line3, font=F(BOLD, size3)) > 612:
        size3 -= 2
    d.text((W // 2, 640), line3,
           font=F(BOLD, size3), fill=CHARCOAL_DARK,
           anchor="mm", stroke_width=5, stroke_fill=WHITE)
    d.rounded_rectangle([120, 706, 600, 786], radius=40, fill=CRIMSON + (255,))
    d.text((W // 2, 746), data["title_label"], font=F(BOLD, 32), fill=WHITE, anchor="mm")
    d.text((W // 2, 838), f"{data['week_label']}・終値ベース", font=F(BOLD, 28),
           fill=BODY, anchor="mm")
    d.text((W // 2, H - 42), FOOTER_TEXT, font=F(REG, 20), fill=CRIMSON_LIGHT, anchor="mm")
    img.save(out); return out


def list_card(data, out):
    """All 5 picks with weekly drop and the two Friday closes."""
    img, d = _base("今週の下げ {0}選".format(len(data["picks"])),
                   data["picks"][0]["price_date_label"])
    y = 226
    for p in data["picks"]:
        d.rounded_rectangle([28, y, 692, y + 178], radius=26, fill=WHITE + (255,),
                            outline=CRIMSON_LIGHT + (255,), width=3)
        name = f"{p['rank']}) {p['name']} ({p['code']})"
        pct = f"週間 {p['weekly_change_pct']}%"
        pct_w = d.textlength(pct, font=F(BOLD, 34))
        name_size = 35
        while name_size > 20 and d.textlength(name, font=F(BOLD, name_size)) > 672 - 48 - pct_w - 24:
            name_size -= 1
        d.text((48, y + 14), name, font=F(BOLD, name_size), fill=NAME)
        d.text((672, y + 22), pct, font=F(BOLD, 34), fill=CRIMSON, anchor="ra")
        d.text((48, y + 78),
               f"{_fmt_yen(p['prev_close'])} → {_fmt_yen(p['close'])}",
               font=F(BOLD, 34), fill=BODY)
        line3 = f"100株で{p['min_investment_label']}・{p['business_line']}"
        size3 = 26
        while size3 > 16 and d.textlength(line3, font=F(BOLD, size3)) > 616:
            size3 -= 1
        d.text((48, y + 128), line3, font=F(BOLD, size3), fill=BODY)
        y += 192
    _footer(d)
    img.save(out); return out


def _section_label(d, y, text):
    d.rounded_rectangle([36, y, 240, y + 52], radius=26, fill=CHARCOAL_DARK + (255,))
    d.text((138, y + 26), text, font=F(BOLD, 26), fill=CRIMSON_LIGHT, anchor="mm")
    return y + 68


def _detail_row(d, y, ln, bullet=CRIMSON):
    d.rounded_rectangle([36, y, 684, y + 118], radius=24, fill=WHITE + (255,),
                        outline=CRIMSON_LIGHT + (255,), width=3)
    d.ellipse([58, y + 44, 88, y + 74], fill=bullet)
    size = 31
    while size > 18 and d.textlength(ln, font=F(BOLD, size)) > 556:
        size -= 1
    d.text((112, y + 59), ln, font=F(BOLD, size), fill=BODY, anchor="lm")
    return y + 148


def stock_card(data, pick, out):
    """One pick: weekly drop in the header, reason lines, caution lines."""
    title = f"{pick['name']} ({pick['code']})"
    subtitle = f"週間 {pick['weekly_change_pct']}%　100株で{pick['min_investment_label']}"
    img, d = _base(title, subtitle)
    y = _section_label(d, 226, "▼ 下落の理由")
    for ln in pick["reason_lines"]:
        y = _detail_row(d, y, ln)
    y = _section_label(d, y + 8, "▼ 注意点")
    for ln in pick["caution_lines"]:
        y = _detail_row(d, y, ln, bullet=CHARCOAL_DARK)
    _footer(d)
    img.save(out); return out


def summary_card(data, out):
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img, "RGBA")
    random.seed(11)
    for _ in range(40):  # crimson confetti, same rhythm as other series
        x, y = random.randint(0, W), random.randint(0, H)
        c = random.choice([(220, 38, 38, 120), (254, 202, 202, 130),
                           (255, 255, 255, 110), (153, 27, 27, 120)])
        if y < 120:  # keep the title band clear
            continue
        d.rectangle([x, y, x + 10, y + 5], fill=c)
    title = f"まとめ：{data['title_label']}"
    tsize = 40
    while tsize > 24 and d.textlength(title, font=F(BOLD, tsize)) > 540:
        tsize -= 2
    d.text((W // 2 - 20, 70), title, font=F(BOLD, tsize),
           fill=CRIMSON_LIGHT, anchor="mm", stroke_width=5, stroke_fill=CHARCOAL_DARK)
    _badge(d, 652, 68, 30)  # series marker
    d.rounded_rectangle([24, 128, 696, 1108], radius=30, fill=WHITE + (255,),
                        outline=CRIMSON_LIGHT + (255,), width=3)
    y = 152
    for row in data["summary_rows"]:
        d.rounded_rectangle([44, y, 676, y + 272], radius=22, fill=ROW_LIGHT + (255,),
                            outline=CRIMSON_LIGHT + (255,), width=3)
        cx, cy, r = 96, y + 136, 34  # exactly one check per row
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=CRIMSON, outline=CHARCOAL_DARK, width=3)
        d.line([(cx - 16, cy), (cx - 4, cy + 14), (cx + 18, cy - 15)], fill=WHITE, width=8, joint="curve")
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
    # extra space below the three rows: risk reminder
    d.rounded_rectangle([24, 1132, 696, 1248], radius=22, fill=CHARCOAL_DARK + (255,))
    d.text((W // 2, 1172), "⚠ 投資推奨ではありません", font=F(BOLD, 29), fill=WHITE, anchor="mm")
    d.text((W // 2, 1216), "株価はさらに下がる場合があります", font=F(REG, 24),
           fill=CRIMSON_LIGHT, anchor="mm")
    img.save(out); return out


def build_all_long(data, outdir):
    os.makedirs(outdir, exist_ok=True)
    paths = [
        title_card(data, os.path.join(outdir, "card_title.png")),
        list_card(data, os.path.join(outdir, "card_list.png")),
    ]
    for i, pick in enumerate(data["picks"]):
        paths.append(stock_card(data, pick, os.path.join(outdir, f"card_stock_{i + 1}.png")))
    paths.append(summary_card(data, os.path.join(outdir, "card_summary.png")))
    return paths
