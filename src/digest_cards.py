#!/usr/bin/env python3
"""Digest title card for the weekly 5-pick digest video.

Reuses the yutai blue-pop design and the list / detail / summary cards
from cards.py unchanged; only the opening title card is digest-specific:
it says "ダイジェスト" and carries a concrete hook in the first 3 seconds
(Hide's rule, 2026-11-18/19): an amount / deadline, not just the theme.
"""
import os, random
from PIL import Image, ImageDraw

from cards import W, H, F, BOLD, REG, _footer


def digest_title_card(data, out):
    """Opening title card: theme + ダイジェスト badge + concrete hook.

    Hook lines are derived from the source edition's own verified data:
    Skylark's annual benefit (2,000 yen x 2 = 4,000 yen / 100 shares)
    and the rights last day. No new numbers are introduced.
    """
    img = Image.new("RGB", (W, H), (29, 140, 248))
    d = ImageDraw.Draw(img, "RGBA")
    random.seed(3)
    for _ in range(28):
        x, y = random.randint(-40, W), random.randint(-40, H)
        r = random.randint(8, 42)
        d.ellipse([x - r, y - r, x + r, y + r], fill=(255, 255, 255, 26))
    d.rounded_rectangle([36, 300, 684, 880], radius=36, fill=(255, 255, 255))
    d.text((W // 2, 430), f"{data['month_label']}の株主優待",
           font=F(BOLD, 66), fill=(239, 68, 68), anchor="mm")
    d.text((W // 2, 540), "5選", font=F(BOLD, 84),
           fill=(239, 68, 68), anchor="mm")
    d.rounded_rectangle([230, 620, 490, 690], radius=35, fill=(30, 64, 175))
    d.text((W // 2, 655), "ダイジェスト", font=F(BOLD, 34),
           fill=(255, 255, 255), anchor="mm")
    d.text((W // 2, 780), "5銘柄の要点だけ、1分でおさらい",
           font=F(BOLD, 30), fill=(17, 24, 39), anchor="mm")
    # Hook pills: concrete benefit amount + deadline (viewer-first).
    d.rounded_rectangle([60, 930, 660, 1000], radius=35, fill=(220, 38, 38))
    d.text((W // 2, 965), "100株で年4,000円分の食事券",
           font=F(BOLD, 28), fill=(255, 255, 255), anchor="mm")
    d.rounded_rectangle([140, 1020, 580, 1090], radius=35, fill=(30, 64, 175))
    d.text((W // 2, 1055), f"権利付き最終日 {data['rights_last_day_label']}",
           font=F(BOLD, 28), fill=(255, 255, 255), anchor="mm")
    _footer(d)
    img.save(out)
    return out
