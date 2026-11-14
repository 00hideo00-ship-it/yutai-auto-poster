#!/usr/bin/env python3
"""Pop-style cards (720x1280) for the high-dividend series.

Reuses the exact drawing primitives of cards.py (same base, rows, footer,
fonts and colors as the approved yutai series) so the two series look
identical. The summary card draws exactly ONE checkmark per row, by
construction."""
from PIL import Image, ImageDraw
import os, random
import cards as _c

W, H = _c.W, _c.H
F, BOLD, REG, COLORS = _c.F, _c.BOLD, _c.REG, _c.COLORS
FOOTER = "※投資推奨ではありません・配当は変更される場合があります"

def list_card(data, out):
    img, d = _c._base(f"{data['title_label']} 5選", data["list_subtitle"])
    _c._rows(d, data["picks"], "list_lines")
    _c._footer(d, FOOTER)
    img.save(out); return out

def points_card(data, out):
    img, d = _c._base("おすすめポイント", data["points_subtitle"])
    _c._rows(d, data["picks"], "point_lines")
    _c._footer(d, FOOTER)
    img.save(out); return out

def summary_card(data, out):
    img = Image.new("RGB", (W, H), (186, 230, 253))
    d = ImageDraw.Draw(img, "RGBA")
    random.seed(11)
    for _ in range(40):
        x, y = random.randint(0, W), random.randint(0, H)
        c = random.choice([(248, 113, 113, 120), (250, 204, 21, 120), (45, 212, 191, 120), (96, 165, 250, 120)])
        d.rectangle([x, y, x + 10, y + 5], fill=c)
    d.text((W // 2, 70), f"まとめ：{data['title_label']} 5選", font=F(BOLD, 52),
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
    d.text((W // 2, 1216), "配当は変更・減配される場合があります", font=F(REG, 26), fill=(255, 255, 255), anchor="mm")
    img.save(out); return out

def build_all(data, outdir):
    os.makedirs(outdir, exist_ok=True)
    return [
        list_card(data, os.path.join(outdir, "card_list.png")),
        points_card(data, os.path.join(outdir, "card_points.png")),
        summary_card(data, os.path.join(outdir, "card_summary.png")),
    ]
