#!/usr/bin/env python3
"""Cards (720x1280) for the tax-saving (setsuzei) one-off series.

Own visual identity: mint-white background, deep teal header band, amber
accents, pastel teal/amber rows, and a round teal badge with amber ring
and the characters 「節税」 in the header of every card. Structure mirrors
the other series: list card -> one detail card per item -> summary card
with exactly one checkmark per row, by construction."""
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
FOOTER_LIST = "※2026年11月時点の制度です。金額・上限は変更される場合があります"
FOOTER_DETAIL = "※条件の詳細は国税庁などの公式情報を確認してください"


def _badge(d, cx, cy, r):
    """Series marker: teal disc, amber ring, 「節税」 in light amber."""
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=TEAL, outline=AMBER, width=4)
    d.text((cx, cy - 1), "節税", font=F(BOLD, int(r * 0.78)), fill=AMBER_LIGHT, anchor="mm")


def _base(title, subtitle):
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img, "RGBA")
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
    d.rounded_rectangle([16, 16, 704, 196], radius=28, fill=TEAL + (255,))
    title_size = 58 if len(title) <= 9 else 50
    d.text((W // 2, 78), title, font=F(BOLD, title_size), fill=AMBER_LIGHT, anchor="mm",
           stroke_width=6, stroke_fill=TEAL_DARK)
    sub_size = 34 if len(subtitle) <= 15 else (26 if len(subtitle) <= 24 else 22)
    d.rounded_rectangle([40, 118, 680, 178], radius=30, fill=AMBER + (255,))
    d.text((W // 2, 148), subtitle, font=F(BOLD, sub_size), fill=TEAL_DARK, anchor="mm")
    _badge(d, 646, 76, 37)
    return img, d


def _footer(d, text):
    d.text((W // 2, H - 42), text, font=F(REG, 20), fill=TEAL, anchor="mm")


def list_card(data, out):
    img, d = _base(f"{data['title_label']} 5選", data["list_subtitle"])
    y = 205
    for i, p in enumerate(data["picks"]):
        color = ROW_COLORS[i % len(ROW_COLORS)]
        d.rounded_rectangle([28, y, 692, y + 178], radius=26, fill=color + (255,),
                            outline=TEAL + (255,), width=3)
        head = f"{i+1}) {p['name']}"
        d.text((48, y + 14), head, font=F(BOLD, 35), fill=NAME)
        for j, ln in enumerate(p["list_lines"]):
            d.text((48, y + 66 + j * 50), ln, font=F(BOLD, 30), fill=BODY)
        y += 192
    _footer(d, FOOTER_LIST)
    img.save(out); return out


def detail_card(data, idx, out):
    p = data["picks"][idx]
    img, d = _base(p["name"], f"節税対策 {idx+1}／5")
    lines = p["detail_lines"]
    y = 250
    for ln in lines:
        d.rounded_rectangle([36, y, 684, y + 128], radius=22, fill=(255, 255, 255, 255),
                            outline=TEAL + (255,), width=3)
        d.ellipse([58, y + 44, 98, y + 84], fill=AMBER)
        size = 31
        while size > 22 and d.textlength(ln, font=F(BOLD, size)) > 556:
            size -= 3
        d.text((118, y + 64), ln, font=F(BOLD, size), fill=BODY, anchor="lm")
        y += 148
    note = p.get("footnote")
    if note:
        d.text((W // 2, 1150), note, font=F(BOLD, 23), fill=TEAL, anchor="mm")
    _footer(d, FOOTER_DETAIL)
    img.save(out); return out


def summary_card(data, out):
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img, "RGBA")
    random.seed(13)
    for _ in range(40):  # teal/amber confetti
        x, y = random.randint(0, W), random.randint(0, H)
        c = random.choice([(13, 148, 136, 120), (245, 158, 11, 130),
                           (45, 180, 165, 120), (253, 211, 77, 130)])
        d.rectangle([x, y, x + 10, y + 5], fill=c)
    d.text((W // 2, 70), f"まとめ：{data['title_label']} 5選", font=F(BOLD, 40),
           fill=TEAL, anchor="mm", stroke_width=5, stroke_fill=AMBER_LIGHT)
    _badge(d, 652, 68, 30)
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
    d.text((W // 2, 1172), "⚠ 税制は変更される場合があります", font=F(BOLD, 29), fill=(255, 255, 255), anchor="mm")
    d.text((W // 2, 1216), "個別の税務相談は税理士へ。詳細は国税庁で確認を", font=F(REG, 24), fill=(255, 255, 255), anchor="mm")
    img.save(out); return out


def build_all(data, outdir):
    os.makedirs(outdir, exist_ok=True)
    paths = [title_card(data, os.path.join(outdir, "card_title.png")),
             list_card(data, os.path.join(outdir, "card_list.png"))]
    for i in range(len(data["picks"])):
        paths.append(detail_card(data, i, os.path.join(outdir, f"card_detail_{i+1}.png")))
    paths.append(summary_card(data, os.path.join(outdir, "card_summary.png")))
    return paths




def title_card(data, out):
    """Opening title card (Hide's rule, 2026-11-15): the video title is
    centered on screen so viewers know the topic immediately."""
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img, "RGBA")
    random.seed(5)
    for _ in range(28):
        x, y = random.randint(-40, W), random.randint(-40, H)
        r = random.randint(8, 42)
        c = random.choice([(13, 148, 136, 22), (245, 158, 11, 24), (45, 180, 165, 26)])
        d.ellipse([x - r, y - r, x + r, y + r], fill=c)
    for _ in range(8):
        x, y = random.randint(20, W - 20), random.randint(220, H - 60)
        r = random.randint(9, 17)
        d.ellipse([x - r, y - r, x + r, y + r], outline=(245, 158, 11, 110), width=3)
    d.rounded_rectangle([36, 400, 684, 880], radius=36, fill=TEAL + (255,))
    _badge(d, 646, 76, 37)
    d.text((W // 2, 552), data["title_label"], font=F(BOLD, 88), fill=AMBER_LIGHT,
           anchor="mm", stroke_width=6, stroke_fill=TEAL_DARK)
    d.text((W // 2, 672), "5選", font=F(BOLD, 88), fill=AMBER_LIGHT,
           anchor="mm", stroke_width=6, stroke_fill=TEAL_DARK)
    d.rounded_rectangle([120, 756, 600, 830], radius=37, fill=AMBER + (255,))
    d.text((W // 2, 793), data["list_subtitle"], font=F(BOLD, 28),
           fill=TEAL_DARK, anchor="mm")
    d.text((W // 2, H - 42), FOOTER_LIST, font=F(REG, 20), fill=TEAL, anchor="mm")
    img.save(out); return out

