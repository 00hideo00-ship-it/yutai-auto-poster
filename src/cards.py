#!/usr/bin/env python3
"""Pop-style cards (720x1280) generated deterministically from picks data.
Design matches the approved first-series style: bright blue background,
colorful rounded rows, red title with white stroke. The summary card draws
exactly ONE checkmark per row, by construction."""
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
COLORS = [(249, 168, 212), (252, 165, 165), (196, 181, 253), (134, 239, 172), (94, 234, 212)]

def F(p, s):
    return ImageFont.truetype(p, s)

def _base(title, subtitle, light=False):
    img = Image.new("RGB", (W, H), (186, 230, 253) if light else (29, 140, 248))
    d = ImageDraw.Draw(img, "RGBA")
    random.seed(3 if not light else 11)
    for _ in range(28):
        x, y = random.randint(-40, W), random.randint(-40, H)
        r = random.randint(8, 42)
        d.ellipse([x - r, y - r, x + r, y + r], fill=(255, 255, 255, 26))
    d.text((W // 2, 78), title, font=F(BOLD, 58), fill=(239, 68, 68), anchor="mm",
           stroke_width=8, stroke_fill=(255, 255, 255))
    sub_size = 34 if len(subtitle) <= 15 else (26 if len(subtitle) <= 24 else 22)
    d.rounded_rectangle([40, 118, 680, 178], radius=30, fill=(30, 64, 175))
    d.text((W // 2, 148), subtitle, font=F(BOLD, sub_size), fill=(255, 255, 255), anchor="mm")
    return img, d

def _rows(d, picks, lines_key, y0=205):
    y = y0
    for i, p in enumerate(picks):
        color = COLORS[i % len(COLORS)]
        d.rounded_rectangle([28, y, 692, y + 178], radius=26, fill=color + (255,))
        d.text((48, y + 14), f"{i+1}) {p['name']} ({p['code']})", font=F(BOLD, 35), fill=(17, 24, 39))
        for j, ln in enumerate(p[lines_key]):
            d.text((48, y + 66 + j * 50), ln, font=F(BOLD, 30), fill=(55, 65, 81))
        y += 192

def _footer(d, text="※投資推奨ではありません・優待は変更される場合があります"):
    d.text((W // 2, H - 42), text, font=F(REG, 21), fill=(255, 255, 255), anchor="mm")

def list_card(data, out):
    img, d = _base(f"{data['month_label']}優待 5選", f"権利付き最終日 {data['rights_last_day_label']}")
    _rows(d, data["picks"], "benefit_lines")
    _footer(d)
    img.save(out); return out

def points_card(data, out):
    eligible = [str(i + 1) + ")" for i, p in enumerate(data["picks"]) if p["eligible_this_year"]]
    if len(eligible) == len(data["picks"]):
        subtitle = "全銘柄、今から買って今年もらえます"
    elif eligible:
        subtitle = "今から買って今年もらえるのは " + " ".join(eligible) + " だけ"
    else:
        subtitle = "全銘柄、継続保有が必要です"
    img, d = _base("おすすめポイント", subtitle)
    _rows(d, data["picks"], "point_lines")
    _footer(d)
    img.save(out); return out

def summary_card(data, out):
    img = Image.new("RGB", (W, H), (186, 230, 253))
    d = ImageDraw.Draw(img, "RGBA")
    random.seed(11)
    for _ in range(40):
        x, y = random.randint(0, W), random.randint(0, H)
        c = random.choice([(248, 113, 113, 120), (250, 204, 21, 120), (45, 212, 191, 120), (96, 165, 250, 120)])
        d.rectangle([x, y, x + 10, y + 5], fill=c)
    d.text((W // 2, 70), f"まとめ：{data['month_label']}優待 5選", font=F(BOLD, 52),
           fill=(220, 38, 38), anchor="mm", stroke_width=6, stroke_fill=(255, 255, 255))
    d.rounded_rectangle([24, 128, 696, 1108], radius=30, fill=(255, 255, 255, 255))
    y = 148
    for i, p in enumerate(data["picks"]):
        color = COLORS[i % len(COLORS)]
        d.rounded_rectangle([44, y, 676, y + 172], radius=22, fill=color + (255,))
        cx, cy, r = 92, y + 86, 27  # exactly one check per row
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(34, 197, 94))
        d.line([(cx - 13, cy), (cx - 3, cy + 11), (cx + 15, cy - 12)], fill=(255, 255, 255), width=7, joint="curve")
        d.text((140, y + 18), f"{p['name']} ({p['code']})", font=F(BOLD, 33), fill=(17, 24, 39))
        for j, ln in enumerate(p["summary_lines"]):
            d.text((140, y + 66 + j * 46), ln, font=F(BOLD, 27), fill=(55, 65, 81))
        y += 188
    d.rounded_rectangle([24, 1132, 696, 1248], radius=22, fill=(31, 41, 55, 255))
    d.text((W // 2, 1172), "⚠ 投資推奨ではありません", font=F(BOLD, 29), fill=(255, 255, 255), anchor="mm")
    d.text((W // 2, 1216), "優待内容は変更される場合があります", font=F(REG, 26), fill=(255, 255, 255), anchor="mm")
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
    img = Image.new("RGB", (W, H), (29, 140, 248))
    d = ImageDraw.Draw(img, "RGBA")
    random.seed(3)
    for _ in range(28):
        x, y = random.randint(-40, W), random.randint(-40, H)
        r = random.randint(8, 42)
        d.ellipse([x - r, y - r, x + r, y + r], fill=(255, 255, 255, 26))
    d.rounded_rectangle([36, 400, 684, 880], radius=36, fill=(255, 255, 255))
    d.text((W // 2, 552), f"{data['month_label']}の株主優待", font=F(BOLD, 72),
           fill=(239, 68, 68), anchor="mm")
    d.text((W // 2, 672), "5選", font=F(BOLD, 88), fill=(239, 68, 68), anchor="mm")
    d.rounded_rectangle([120, 756, 600, 830], radius=37, fill=(30, 64, 175))
    d.text((W // 2, 793), f"権利付き最終日 {data['rights_last_day_label']}",
           font=F(BOLD, 28), fill=(255, 255, 255), anchor="mm")
    _footer(d)
    img.save(out); return out



def detail_card(data, pick, idx, out):
    """One per-pick detail card for the 61s version, in the yutai pop
    style: blue background, white boxes with the row color as a bullet."""
    img = Image.new("RGB", (W, H), (29, 140, 248))
    d = ImageDraw.Draw(img, "RGBA")
    random.seed(3)
    for _ in range(28):
        x, y = random.randint(-40, W), random.randint(-40, H)
        r = random.randint(8, 42)
        d.ellipse([x - r, y - r, x + r, y + r], fill=(255, 255, 255, 26))
    d.text((W // 2, 78), f"{pick['name']} ({pick['code']})", font=F(BOLD, 46),
           fill=(239, 68, 68), anchor="mm", stroke_width=7, stroke_fill=(255, 255, 255))
    d.rounded_rectangle([40, 118, 680, 178], radius=30, fill=(30, 64, 175))
    d.text((W // 2, 148), f"{data['month_label']}優待 {idx + 1}／5", font=F(BOLD, 30),
           fill=(255, 255, 255), anchor="mm")
    color = COLORS[idx % len(COLORS)]
    y = 210
    for ln in pick["detail_lines"]:
        d.rounded_rectangle([36, y, 684, y + 150], radius=24, fill=(255, 255, 255))
        d.ellipse([64, y + 58, 98, y + 92], fill=color + (255,))
        d.text((122, y + 75), ln, font=F(BOLD, 31), fill=(17, 24, 39), anchor="lm")
        y += 168
    _footer(d)
    img.save(out); return out


def build_long_all(data, outdir):
    os.makedirs(outdir, exist_ok=True)
    paths = [
        title_card(data, os.path.join(outdir, "card_title.png")),
        list_card(data, os.path.join(outdir, "card_list.png")),
    ]
    for i, p in enumerate(data["picks"]):
        paths.append(detail_card(data, p, i, os.path.join(outdir, f"card_detail_{i + 1}.png")))
    paths.append(summary_card(data, os.path.join(outdir, "card_summary.png")))
    return paths
