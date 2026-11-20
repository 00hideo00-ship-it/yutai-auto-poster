#!/usr/bin/env python3
"""Weekly digest video (Saturday 10:00 post): 61s digest of the newest
monthly 5-pick edition (yutai monthly 5th vs dividend monthly 15th,
whichever is newer). Design and BGM reuse the source series as-is;
all numbers come from the source edition's picks data unchanged.

Structure (61s): digest title card (hook in first 3s) -> list card ->
one detail card per pick -> summary card.
Usage:
  python3 src/digest_main.py --file data/picks_2026-12.json
  python3 src/digest_main.py --date 2026-11-21   # picks newest edition
No posting here: Hide publishes manually.
"""
import argparse, glob, json, os, subprocess, sys
from datetime import date

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))
import factcheck, cards, digest_cards, main as yutai_main, music  # noqa: E402
from yutai_long_main import detail_gate, LANDING_URL  # noqa: E402

SEGMENTS = [6, 7, 7, 7, 7, 7, 7, 13]  # title, list, 5 detail cards, summary = 61s
TOTAL = sum(SEGMENTS)
PROBE_TIMES = (3, 9, 16, 23, 30, 37, 44, 55)


def newest_monthly():
    """Newest monthly 5-pick edition: yutai (picks_YYYY-MM, 5th) vs
    dividend (dividend_YYYY-MM, 15th) by checked_date."""
    cands = []
    for pat in ("picks_*.json", "dividend_*.json"):
        for path in glob.glob(os.path.join(ROOT, "data", pat)):
            with open(path, encoding="utf-8") as f:
                d = json.load(f)
            cands.append((d.get("checked_date", ""), path, d))
    if not cands:
        return None, None
    checked, path, data = max(cands, key=lambda c: c[0])
    return path, data


def build_video(data, outdir):
    card_dir = os.path.join(outdir, "cards")
    os.makedirs(card_dir, exist_ok=True)
    card_paths = [
        digest_cards.digest_title_card(data, os.path.join(card_dir, "card_title.png")),
        cards.list_card(data, os.path.join(card_dir, "card_list.png")),
    ]
    for i, p in enumerate(data["picks"]):
        card_paths.append(cards.detail_card(
            data, p, i, os.path.join(card_dir, f"card_detail_{i + 1}.png")))
    card_paths.append(cards.summary_card(data, os.path.join(card_dir, "card_summary.png")))
    bgm = music.make_bgm(os.path.join(outdir, "bgm.wav"), dur=float(TOTAL), **music.YUTAI_THEME)
    video = os.path.join(outdir, "digest_tiktok_61s_v1.mp4")
    inputs = "".join(f"[{i}:v]fps=30,format=yuv420p[v{i}];" for i in range(len(card_paths)))
    concat = "".join(f"[v{i}]" for i in range(len(card_paths)))
    fc = (f"{inputs}{concat}concat=n={len(card_paths)}:v=1:a=0[v];"
          f"[{len(card_paths)}:a]atrim=0:{TOTAL},afade=t=out:st={TOTAL - 2}:d=2,"
          "aformat=sample_rates=44100:channel_layouts=stereo[a]")
    cmd = ["ffmpeg", "-nostdin", "-y", "-v", "error"]
    for path, dur in zip(card_paths, SEGMENTS):
        cmd += ["-loop", "1", "-t", str(dur), "-i", path]
    cmd += ["-i", bgm, "-filter_complex", fc, "-map", "[v]", "-map", "[a]",
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "22",
            "-c:a", "aac", "-b:a", "160k", "-t", str(TOTAL), video]
    subprocess.run(cmd, check=True)
    dur = subprocess.check_output(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", video]).decode().strip()
    if not (TOTAL - 0.5 <= float(dur) <= TOTAL + 0.5):
        raise RuntimeError(f"video duration {dur}s is not {TOTAL}s")
    probe = os.path.join(outdir, "probe")
    os.makedirs(probe, exist_ok=True)
    for t in PROBE_TIMES:
        subprocess.run(["ffmpeg", "-nostdin", "-y", "-v", "error", "-ss", str(t),
                        "-i", video, "-frames:v", "1", "-q:v", "4",
                        os.path.join(probe, f"frame_{t}s.jpg")], check=True)
    return video


def caption_for(data):
    names = "、".join(p["name"] for p in data["picks"])
    return (f"【{data['month_label']}株主優待】おすすめ5選 ダイジェスト\n"
            f"100株で年4,000円分の食事券も！権利付き最終日は{data['rights_last_day_label']}。\n"
            f"{names}\n"
            f"フル版（61秒・各銘柄の詳細つき）は{data['month_label']}の5選動画でチェックしてね。\n"
            f"※楽天グループの優待内容は前回実績です（今期分は発表後に要確認）\n"
            f"※本動画は銘柄紹介であり投資推奨ではありません。優待内容・条件は各社IRでご確認ください\n"
            f"#株主優待 #優待株 #{data['month_label']}優待 #日本株 #投資初心者")


def youtube_title(data):
    return (f"【{data['month_label']}株主優待】おすすめ5選 ダイジェスト｜"
            f"100株で年4,000円分の食事券・権利付き最終日は{data['rights_last_day_label']}")


def youtube_description(data):
    lines = [f"{data['month_label']}の株主優待から、個人投資家に人気の5銘柄を1分でおさらいするダイジェストです。",
             f"権利付き最終日は{data['rights_last_day_label']}です。", "",
             "【5銘柄】"]
    for i, p in enumerate(data["picks"], 1):
        lines.append(f"{i}. {p['name']}（{p['code']}）")
        for ln in p["detail_lines"]:
            lines.append(f"・{ln}")
        lines.append("")
    lines += ["※楽天グループの優待内容は前回実績です（今期分は未発表・発表後に要確認）",
              "※すかいらーくHDは2027年6月末分から6か月以上の継続保有が必要になります（2026年11月12日発表）",
              f"※数値は各社IR・楽天証券トウシル等で確認（{data['checked_date']}時点）。優待は変更される場合があります",
              "※本動画は銘柄紹介であり投資推奨ではありません", "",
              "▼お役立ちリンク集（SNSまとめ）",
              LANDING_URL,
              "▼TikTok",
              "https://www.tiktok.com/@toushi_daisuki",
              "▼Instagram",
              "https://www.instagram.com/toushi_daisuki_", "",
              f"#株主優待 #優待株 #{data['month_label']}優待 #日本株 #投資初心者 #資産形成 #Shorts"]
    return "\n".join(lines)


def instagram_caption(data):
    names = "、".join(p["name"] for p in data["picks"])
    return (f"【{data['month_label']}株主優待】おすすめ5選 ダイジェスト\n\n"
            f"100株で年4,000円分の食事券も！権利付き最終日は{data['rights_last_day_label']}だよ。\n"
            f"{names}\n\n"
            "各銘柄の詳しい条件は、フル版（61秒）の5選動画でチェックしてね。\n"
            "今年から対象なのは、すかいらーくHDと楽天グループの2つだけ。\n"
            "ヤマハ発動機・キリンHD・ヒューリックは継続保有が必要だから、来年以降に向けた仕込み枠だよ。\n"
            "楽天グループの優待内容は前回実績（今期分は未発表）だから、発表後に確認してね。\n\n"
            "※本動画は銘柄紹介であり投資推奨ではありません。優待は変更される場合があります\n\n"
            f"#株主優待 #優待株 #{data['month_label']}優待 #日本株 #投資初心者 #資産形成 #お金の勉強")


def publish_guide(data, caption):
    base = yutai_main.publish_guide(data, caption)
    base = base.replace(f"【手動公開ガイド】{data['month_label']}株主優待 おすすめ5選",
                        f"【手動公開ガイド】{data['month_label']}株主優待 おすすめ5選 ダイジェスト")
    extra = (f"\n■ YouTube Shorts（同じファイルで投稿可）\n"
             f"タイトル\n{youtube_title(data)}\n\n"
             f"説明文\n{youtube_description(data)}\n\n"
             f"設定: 視聴者層は「子ども向けではない」を選択／改変されたコンテンツ（AI生成）の開示をオン／公開\n"
             f"\n■ Instagramリール（同じファイルで投稿可）\n"
             f"キャプション\n{instagram_caption(data)}\n\n"
             f"設定: カバーは先頭フレーム（タイトルカード）／AIラベルをオン／フィードにもシェアをオン\n")
    return base + extra


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", help="data/picks_YYYY-MM.json; default: newest monthly edition")
    ap.add_argument("--date", default=date.today().isoformat(),
                    help="digest date YYYY-MM-DD (post date, default today)")
    args = ap.parse_args()
    if args.file:
        data_path = os.path.join(ROOT, args.file)
        with open(data_path, encoding="utf-8") as f:
            data = json.load(f)
        source = os.path.basename(data_path)
    else:
        data_path, data = newest_monthly()
        if data is None:
            print("no monthly picks file in data/")
            return 1
        source = os.path.basename(data_path)

    errors = factcheck.check(data) + detail_gate(data)
    if errors:
        print("FACT-CHECK FAILED:")
        for e in errors:
            print(" -", e)
        return 1
    print(f"fact-check OK (digest source: {source}, checked {data['checked_date']})")

    outdir = os.path.join(ROOT, "output", f"digest-{args.date}")
    os.makedirs(outdir, exist_ok=True)
    video = build_video(data, outdir)
    caption = caption_for(data)
    package = {"series": "digest", "source_edition": source,
               "month_label": data["month_label"], "video": video,
               "caption": caption, "duration_sec": TOTAL, "fact_check": "passed",
               "probe_frames": os.path.join(outdir, "probe")}
    print(f"video built: {video}")
    with open(os.path.join(outdir, "post_package.json"), "w", encoding="utf-8") as f:
        json.dump(package, f, ensure_ascii=False, indent=2)
    guide_path = os.path.join(outdir, "publish_guide.txt")
    with open(guide_path, "w", encoding="utf-8") as f:
        f.write(publish_guide(data, caption))
    print(f"publish guide: {guide_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
