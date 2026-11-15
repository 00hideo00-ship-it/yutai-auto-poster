#!/usr/bin/env python3
"""Cards (720x1280) for the high-dividend series — its own visual identity.

Sibling of the yutai series (same layout, fonts, card structure and timing)
but instantly distinguishable in a feed grid: cream background, deep-green
header band, gold accents, pastel green/gold rows, and a gold coin badge
("¥") in the header of every card. Content, wording and geometry of the
text are unchanged from the yutai layout, so nothing can overflow.
The summary card draws exactly ONE checkmark per row, by construction."""
from PIL import Image, ImageDraw
import os, random
import cards as _c

W, H = _c.W, _c.H
F, BOLD, REG = _c.F, _c.BOLD, _c.REG

CREAM = (255, 248, 231)
GREEN = (14, 122, 61)        # deep emerald, main color
GREEN_DARK = (8, 84, 42)     # subtitle text / darker green
GOLD = (232, 168, 18)        # gold accent
GOLD_LIGHT = (255, 201, 60)  # coin face
GOLD_EDGE = (166, 124, 10)   # coin rim
COIN_TEXT = (122, 84, 4)
NAME = (10, 84, 40)          # row title text
BODY = (55, 65, 81)          # row body text (same as yutai)
ROW_COLORS = [(170, 228, 186), (252, 216, 116), (152, 218, 176),
              (255, 226, 148), (190, 236, 202)]
FOOTER = "※投資推奨ではありません・配当は変更される場合があります"


def _coin(d, cx, cy, r):
    """Gold coin badge: rim + lighter face + ¥ mark."""
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=GOLD, outline=GOLD_EDGE, width=3)
    r2 = r - max(6, r // 5)
    d.ellipse([cx - r2, cy - r2, cx + r2, cy + r2], fill=GOLD_LIGHT, outline=GOLD_EDGE, width=2)
    d.text((cx, cy - 2), "¥", font=F(BOLD, int(r * 1.15)), fill=COIN_TEXT, anchor="mm")


def _base(title, subtitle, title_size=58):
    img = Image.new("RGB", (W, H), CREAM)
    d = ImageDraw.Draw(img, "RGBA")
    random.seed(3)
    for _ in range(28):  # soft gold/green bubbles, same rhythm as yutai
        x, y = random.randint(-40, W), random.randint(-40, H)
        r = random.randint(8, 42)
        c = random.choice([(232, 168, 18, 26), (14, 122, 61, 20), (255, 201, 60, 34)])
        d.ellipse([x - r, y - r, x + r, y + r], fill=c)
    for _ in range(8):  # tiny coin rings scattered in the background
        x, y = random.randint(20, W - 20), random.randint(220, H - 60)
        r = random.randint(9, 17)
        d.ellipse([x - r, y - r, x + r, y + r], outline=(232, 168, 18, 110), width=3)
    # deep-green header band holding title + subtitle
    d.rounded_rectangle([16, 16, 704, 196], radius=28, fill=GREEN + (255,))
    d.text((W // 2, 78), title, font=F(BOLD, title_size), fill=GOLD_LIGHT, anchor="mm",
           stroke_width=6, stroke_fill=GREEN_DARK)
    sub_size = 34 if len(subtitle) <= 15 else (26 if len(subtitle) <= 24 else 22)
    d.rounded_rectangle([40, 118, 680, 178], radius=30, fill=GOLD + (255,))
    d.text((W // 2, 148), subtitle, font=F(BOLD, sub_size), fill=GREEN_DARK, anchor="mm")
    _coin(d, 646, 76, 37)  # series marker
    return img, d


def _wrap(d, text, font, max_w):
    """Wrap text by measured pixel width (CJK-aware: no mid-word breaks needed)."""
    lines, cur = [], ""
    for ch in text:
        if d.textlength(cur + ch, font=font) <= max_w:
            cur += ch
        else:
            lines.append(cur)
            cur = ch
    if cur:
        lines.append(cur)
    return lines


def _info_box(d, y, h, color, heading, lines):
    """One rounded info box. lines: list of (text, size, color)."""
    d.rounded_rectangle([28, y, 692, y + h], radius=26, fill=color + (255,),
                        outline=GREEN + (255,), width=3)
    d.text((52, y + 14), heading, font=F(BOLD, 28), fill=GREEN_DARK)
    yy = y + 58
    for text, size, col in lines:
        d.text((52, yy), text, font=F(BOLD, size), fill=col)
        yy += size + 14
    return y + h


def _rows(d, picks, lines_key, y0=205):
    y = y0
    for i, p in enumerate(picks):
        color = ROW_COLORS[i % len(ROW_COLORS)]
        d.rounded_rectangle([28, y, 692, y + 178], radius=26, fill=color + (255,),
                            outline=GREEN + (255,), width=3)
        d.text((48, y + 14), f"{i+1}) {p['name']} ({p['code']})", font=F(BOLD, 35), fill=NAME)
        for j, ln in enumerate(p[lines_key]):
            d.text((48, y + 66 + j * 50), ln, font=F(BOLD, 30), fill=BODY)
        y += 192


def _footer(d, text=FOOTER):
    d.text((W // 2, H - 42), text, font=F(REG, 21), fill=GREEN, anchor="mm")


def list_card(data, out):
    img, d = _base(f"{data['title_label']} 5選", data["list_subtitle"])
    _rows(d, data["picks"], "list_lines")
    _footer(d)
    img.save(out); return out


def points_card(data, out):
    img, d = _base("おすすめポイント", data["points_subtitle"])
    _rows(d, data["picks"], "point_lines")
    _footer(d)
    img.save(out); return out


def summary_card(data, out):
    img = Image.new("RGB", (W, H), CREAM)
    d = ImageDraw.Draw(img, "RGBA")
    random.seed(11)
    for _ in range(40):  # gold/green confetti, same rhythm as yutai
        x, y = random.randint(0, W), random.randint(0, H)
        c = random.choice([(232, 168, 18, 130), (14, 122, 61, 110),
                           (255, 201, 60, 140), (90, 180, 120, 110)])
        d.rectangle([x, y, x + 10, y + 5], fill=c)
    d.text((W // 2, 70), f"まとめ：{data['title_label']} 5選", font=F(BOLD, 52),
           fill=GREEN, anchor="mm", stroke_width=6, stroke_fill=GOLD_LIGHT)
    _coin(d, 652, 68, 30)  # series marker
    d.rounded_rectangle([24, 128, 696, 1108], radius=30, fill=(255, 255, 255, 255),
                        outline=GREEN + (255,), width=3)
    y = 148
    for i, p in enumerate(data["picks"]):
        color = ROW_COLORS[i % len(ROW_COLORS)]
        d.rounded_rectangle([44, y, 676, y + 172], radius=22, fill=color + (255,),
                            outline=GREEN + (255,), width=3)
        cx, cy, r = 92, y + 86, 27  # exactly one check per row
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=GREEN, outline=GOLD, width=3)
        d.line([(cx - 13, cy), (cx - 3, cy + 11), (cx + 15, cy - 12)], fill=(255, 255, 255), width=7, joint="curve")
        d.text((140, y + 18), f"{p['name']} ({p['code']})", font=F(BOLD, 33), fill=NAME)
        for j, ln in enumerate(p["summary_lines"]):
            d.text((140, y + 66 + j * 46), ln, font=F(BOLD, 27), fill=BODY)
        y += 188
    d.rounded_rectangle([24, 1132, 696, 1248], radius=22, fill=GREEN + (255,))
    d.text((W // 2, 1172), "⚠ 投資推奨ではありません", font=F(BOLD, 29), fill=(255, 255, 255), anchor="mm")
    d.text((W // 2, 1216), "配当は変更・減配される場合があります", font=F(REG, 26), fill=(255, 255, 255), anchor="mm")
    img.save(out); return out


def build_all(data, outdir):
    os.makedirs(outdir, exist_ok=True)
    return [
        title_card(data, os.path.join(outdir, "card_title.png")),
        list_card(data, os.path.join(outdir, "card_list.png")),
        points_card(data, os.path.join(outdir, "card_points.png")),
        summary_card(data, os.path.join(outdir, "card_summary.png")),
    ]


def detail_card(pick, idx, out):
    """One per-pick detail card for the 60s+ long version: yield, annual
    dividend, min investment, rights months, stability record and policy.
    Title uses a smaller font so long names (e.g. 三菱HCキャピタル) clear
    the ¥ coin badge in the header."""
    img, d = _base(f"{pick['name']} ({pick['code']})",
                   f"利回り {pick['yield_pct']}% ・ 年間配当 {pick['annual_dividend_label']}",
                   title_size=40)
    y = 212
    c = ROW_COLORS[idx % len(ROW_COLORS)]
    # 1) 最低投資額
    y = _info_box(d, y, 168, c, "最低投資額（100株）", [
        (f"{pick['min_investment_label']}", 40, NAME),
        (f"株価 {pick['price_yen']:,}円（{pick['price_date_label']}）", 26, BODY),
    ]) + 16
    # 2) 権利確定月
    y = _info_box(d, y, 168, ROW_COLORS[(idx + 1) % len(ROW_COLORS)], "権利確定月", [
        (f"{pick['rights_label']}", 40, NAME),
        ("年2回の配当", 26, BODY),
    ]) + 16
    # 3) 増配・安定の実績（stability_note を折り返し表示）
    note_lines = _wrap(d, pick["stability_note"], F(BOLD, 30), 600)
    y = _info_box(d, y, 210, ROW_COLORS[(idx + 2) % len(ROW_COLORS)], "増配・安定の実績",
                  [(ln, 30, BODY) for ln in note_lines[:3]]) + 16
    # 4) 注目ポイント
    y = _info_box(d, y, 168, ROW_COLORS[(idx + 3) % len(ROW_COLORS)], "注目ポイント",
                  [(ln, 30, BODY) for ln in pick["point_lines"]]) + 16
    # 5) 利回りの根拠（年間配当 ÷ 株価）
    y = _info_box(d, y, 150, ROW_COLORS[(idx + 4) % len(ROW_COLORS)], "利回りの根拠", [
        (f"年間配当 {pick['annual_dividend_label']} ÷ 株価 {pick['price_yen']:,}円", 30, NAME),
        (f"＝ {pick['yield_pct']}%　※配当は会社予想を含みます", 26, BODY),
    ])
    _footer(d)
    img.save(out); return out


def build_long_all(data, outdir):
    """Long version (60s+): list card, one detail card per pick, summary."""
    os.makedirs(outdir, exist_ok=True)
    paths = [title_card(data, os.path.join(outdir, "card_title.png")),
             list_card(data, os.path.join(outdir, "card_list.png"))]
    for i, p in enumerate(data["picks"]):
        paths.append(detail_card(p, i, os.path.join(outdir, f"card_detail_{i+1}.png")))
    paths.append(summary_card(data, os.path.join(outdir, "card_summary.png")))
    return paths




def title_card(data, out):
    """Opening title card (Hide's rule, 2026-11-15): the video title is
    centered on screen so viewers know the topic immediately."""
    img = Image.new("RGB", (W, H), CREAM)
    d = ImageDraw.Draw(img, "RGBA")
    random.seed(3)
    for _ in range(28):
        x, y = random.randint(-40, W), random.randint(-40, H)
        r = random.randint(8, 42)
        c = random.choice([(232, 168, 18, 26), (14, 122, 61, 20), (255, 201, 60, 34)])
        d.ellipse([x - r, y - r, x + r, y + r], fill=c)
    for _ in range(8):
        x, y = random.randint(20, W - 20), random.randint(220, H - 60)
        r = random.randint(9, 17)
        d.ellipse([x - r, y - r, x + r, y + r], outline=(232, 168, 18, 110), width=3)
    d.rounded_rectangle([36, 400, 684, 880], radius=36, fill=GREEN + (255,))
    _coin(d, 646, 76, 37)
    d.text((W // 2, 552), data["title_label"], font=F(BOLD, 88), fill=GOLD_LIGHT,
           anchor="mm", stroke_width=6, stroke_fill=GREEN_DARK)
    d.text((W // 2, 672), "5選", font=F(BOLD, 88), fill=GOLD_LIGHT,
           anchor="mm", stroke_width=6, stroke_fill=GREEN_DARK)
    d.rounded_rectangle([120, 756, 600, 830], radius=37, fill=GOLD + (255,))
    d.text((W // 2, 793), data["list_subtitle"], font=F(BOLD, 28),
           fill=GREEN_DARK, anchor="mm")
    d.text((W // 2, H - 42), FOOTER, font=F(REG, 21), fill=GREEN_DARK, anchor="mm")
    img.save(out); return out

