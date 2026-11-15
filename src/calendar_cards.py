#!/usr/bin/env python3
"""Weekly rights-date calendar cards (720x1280), orange x cream theme.

Design (fixed for this theme): orange #F97316 on a cream background,
badge「今週」. Title card -> one detail card per pick (this week) ->
next-week preview card -> summary checklist card. The summary card
draws exactly ONE checkmark per row, by construction.
"""
from PIL import Image, ImageDraw, ImageFont
import os, random

W, H = 720, 1280

def _pick(cands):
    for c in cands:
        if os.path.exists(c):
            return c
    return cands[0]

_WIN = os.path.join(os.environ.get("WINDIR", "C:\\Windows"), "Fonts")
BOLD = _pick([
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
    os.path.join(_WIN, "YuGothB.ttc"),
    os.path.join(_WIN, "meiryob.ttc"),
    os.path.join(_WIN, "msgothic.ttc"),
])
REG = _pick([
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    os.path.join(_WIN, "YuGothR.ttc"),
    os.path.join(_WIN, "meiryo.ttc"),
    os.path.join(_WIN, "msgothic.ttc"),
])

ORANGE = (249, 115, 22)
ORANGE_DARK = (194, 65, 12)
ORANGE_LIGHT = (255, 237, 213)
CREAM = (255, 247, 237)
INK = (31, 41, 55)
GRAY = (75, 85, 99)
GREEN = (34, 197, 94)

def F(p, s):
    return ImageFont.truetype(p, s)

def _cream_base():
    img = Image.new("RGB", (W, H), CREAM)
    d = ImageDraw.Draw(img, "RGBA")
    random.seed(7)
    for _ in range(26):
        x, y = random.randint(-40, W), random.randint(-40, H)
        r = random.randint(8, 40)
        d.ellipse([x - r, y - r, x + r, y + r], fill=(249, 115, 22, 18))
    return img, d

def _badge(d, text="今週", x=600, y=48):
    d.rounded_rectangle([x - 62, y - 30, x + 62, y + 30], radius=30, fill=ORANGE)
    d.text((x, y), text, font=F(BOLD, 34), fill=(255, 255, 255), anchor="mm")

def _footer(d, text="※投資推奨ではありません・優待は変更される場合があります"):
    d.text((W // 2, H - 42), text, font=F(REG, 21), fill=GRAY, anchor="mm")

def title_card(data, out):
    img, d = _cream_base()
    _badge(d)
    d.text((W // 2, 150), "今週の", font=F(BOLD, 52), fill=ORANGE_DARK, anchor="mm")
    d.text((W // 2, 250), "権利確定日", font=F(BOLD, 78), fill=(234, 88, 12), anchor="mm",
           stroke_width=8, stroke_fill=(255, 255, 255))
    d.text((W // 2, 340), "カレンダー", font=F(BOLD, 78), fill=(234, 88, 12), anchor="mm",
           stroke_width=8, stroke_fill=(255, 255, 255))
    d.rounded_rectangle([60, 430, 660, 500], radius=30, fill=(255, 255, 255))
    d.text((W // 2, 465), data["week_label"], font=F(BOLD, 33), fill=INK, anchor="mm")
    # this week's key date
    d.rounded_rectangle([48, 560, 672, 760], radius=26, fill=ORANGE)
    d.text((W // 2, 612), "今週の山場", font=F(BOLD, 34), fill=(255, 255, 255), anchor="mm")
    d.text((W // 2, 678), f"{data['picks'][0]['rights_label']}  {len(data['picks'])}銘柄",
           font=F(BOLD, 44), fill=(255, 255, 255), anchor="mm")
    # next-week teaser
    d.rounded_rectangle([48, 800, 672, 960], radius=26, fill=(255, 255, 255))
    d.text((W // 2, 852), "来週の予告", font=F(BOLD, 34), fill=ORANGE_DARK, anchor="mm")
    d.text((W // 2, 912), f"{data['next_week']['rights_label']} 月末組が本番",
           font=F(BOLD, 36), fill=INK, anchor="mm")
    d.text((W // 2, 1050), "権利付き最終日までに買えば", font=F(BOLD, 32), fill=GRAY, anchor="mm")
    d.text((W // 2, 1100), "優待・配当の権利がもらえます", font=F(BOLD, 32), fill=GRAY, anchor="mm")
    _footer(d)
    img.save(out); return out

def _info_box(d, y, label, lines, h=150):
    d.rounded_rectangle([36, y, 684, y + h], radius=22, fill=(255, 255, 255))
    d.rounded_rectangle([36, y, 52, y + h], radius=8, fill=ORANGE)
    d.text((72, y + 16), label, font=F(BOLD, 30), fill=ORANGE_DARK)
    for j, ln in enumerate(lines):
        d.text((72, y + 62 + j * 46), ln, font=F(BOLD, 31), fill=INK)

def stock_card(data, pick, out):
    img, d = _cream_base()
    _badge(d)
    d.rounded_rectangle([36, 110, 684, 178], radius=30, fill=ORANGE)
    d.text((W // 2, 144), f"{pick['rights_label']} 権利付き最終日",
           font=F(BOLD, 34), fill=(255, 255, 255), anchor="mm")
    d.text((W // 2, 250), f"{pick['name']} ({pick['code']})",
           font=F(BOLD, 46), fill=INK, anchor="mm")
    _info_box(d, 320, "優待", pick["benefit_lines"], h=160)
    _info_box(d, 510, "配当", [pick["dividend_line"]], h=118)
    _info_box(d, 658, "最低投資", [pick["min_investment_label"]], h=118)
    d.text((W // 2, 830), f"株価は{pick['price_date_label']}",
           font=F(REG, 28), fill=GRAY, anchor="mm")
    d.text((W // 2, 880), "※優待内容・配当は変更される場合があります",
           font=F(REG, 26), fill=GRAY, anchor="mm")
    _footer(d)
    img.save(out); return out

def preview_card(data, out):
    img, d = _cream_base()
    nw = data["next_week"]
    d.rounded_rectangle([36, 96, 684, 168], radius=30, fill=ORANGE)
    d.text((W // 2, 132), "来週の予告", font=F(BOLD, 40), fill=(255, 255, 255), anchor="mm")
    d.text((W // 2, 220), f"{nw['rights_label']} 権利付き最終日",
           font=F(BOLD, 38), fill=ORANGE_DARK, anchor="mm")
    d.text((W // 2, 272), "11月末が権利確定日の銘柄群", font=F(REG, 28), fill=GRAY, anchor="mm")
    y = 320
    for item in nw["items"]:
        d.rounded_rectangle([36, y, 684, y + 158], radius=22, fill=(255, 255, 255))
        d.text((64, y + 16), f"{item['name']} ({item['code']})",
               font=F(BOLD, 34), fill=INK)
        d.text((64, y + 72), item["line"], font=F(BOLD, 30), fill=GRAY)
        y += 176
    d.text((W // 2, y + 30), "※キユーピーは6ヶ月以上の保有が必要です",
           font=F(REG, 26), fill=GRAY, anchor="mm")
    d.text((W // 2, y + 72), "※詳細は来週の動画で紹介します",
           font=F(REG, 26), fill=GRAY, anchor="mm")
    _footer(d)
    img.save(out); return out

def summary_card(data, out):
    img, d = _cream_base()
    d.text((W // 2, 90), "まとめ・今週のチェック", font=F(BOLD, 46),
           fill=(234, 88, 12), anchor="mm", stroke_width=6, stroke_fill=(255, 255, 255))
    d.rounded_rectangle([24, 150, 696, 760], radius=30, fill=(255, 255, 255))
    y = 170
    for p in data["picks"]:
        d.rounded_rectangle([44, y, 676, y + 172], radius=22, fill=ORANGE_LIGHT)
        cx, cy, r = 92, y + 86, 27  # exactly one check per row
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=GREEN)
        d.line([(cx - 13, cy), (cx - 3, cy + 11), (cx + 15, cy - 12)],
               fill=(255, 255, 255), width=7, joint="curve")
        d.text((140, y + 18), f"{p['rights_label']}  {p['name']} ({p['code']})",
               font=F(BOLD, 32), fill=INK)
        d.text((140, y + 72), p["benefit_lines"][0], font=F(BOLD, 28), fill=GRAY)
        d.text((140, y + 116), p["dividend_line"], font=F(BOLD, 28), fill=GRAY)
        y += 190
    d.rounded_rectangle([24, 790, 696, 940], radius=22, fill=ORANGE)
    d.text((W // 2, 838), f"来週 {data['next_week']['rights_label']} 月末組が本番",
           font=F(BOLD, 32), fill=(255, 255, 255), anchor="mm")
    d.text((W // 2, 890), "タマホーム・キユーピーなど", font=F(BOLD, 28),
           fill=(255, 255, 255), anchor="mm")
    d.rounded_rectangle([24, 970, 696, 1210], radius=22, fill=(31, 41, 55))
    d.text((W // 2, 1018), "⚠ 権利付き最終日の15:30までに買う", font=F(BOLD, 30),
           fill=(255, 255, 255), anchor="mm")
    d.text((W // 2, 1072), "権利落ち日は翌営業日 11/19(木)", font=F(BOLD, 28),
           fill=(255, 255, 255), anchor="mm")
    d.text((W // 2, 1126), "優待・配当は変更される場合があります", font=F(REG, 26),
           fill=(255, 255, 255), anchor="mm")
    d.text((W // 2, 1172), "※投資推奨ではありません", font=F(BOLD, 28),
           fill=(255, 255, 255), anchor="mm")
    img.save(out); return out

def build_all(data, outdir):
    os.makedirs(outdir, exist_ok=True)
    paths = [title_card(data, os.path.join(outdir, "card_title.png"))]
    for i, p in enumerate(data["picks"]):
        paths.append(stock_card(data, p, os.path.join(outdir, f"card_stock_{i+1}.png")))
    paths.append(preview_card(data, os.path.join(outdir, "card_preview.png")))
    paths.append(summary_card(data, os.path.join(outdir, "card_summary.png")))
    return paths
