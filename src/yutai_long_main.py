#!/usr/bin/env python3
"""61s version of the monthly yutai video, built from the same
data/picks_YYYY-MM.json as the 30s cut (Hide's rule: all recurring
videos are 61 seconds).

Structure: title card -> list card -> one detail card per pick ->
summary card. Same bright-blue pop design and YUTAI_THEME BGM as the
30s series. No posting here: Hide publishes manually.
Usage:
  python3 src/yutai_long_main.py                 # newest data/picks_*.json
  python3 src/yutai_long_main.py --file data/picks_2026-12.json
"""
import argparse, glob, json, os, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))
import factcheck, cards, main as yutai_main, music  # noqa: E402

SEGMENTS = [4, 7, 8, 8, 8, 8, 8, 10]  # title, list, 5 detail cards, summary = 61s
TOTAL = sum(SEGMENTS)
LANDING_URL = ("https://muse.ai/s/tou-zi-da-hao-ki-shou-kemin-pezi-xop6xzxuxsng8w8/"
               "k3ru9cej7TKfxuaIdLAMDCxtN-lr54HyOVmqpbWFP2s")
BANNED = factcheck.BANNED_PHRASES


def detail_gate(data):
    """Extra gate for the long cut: every pick needs 5 verified detail
    lines that fit the card (<=24 chars) with no banned phrases."""
    errors = []
    for i, p in enumerate(data.get("picks", []), 1):
        lines = p.get("detail_lines")
        if not lines or len(lines) != 5:
            errors.append(f"pick {i} ({p.get('name')}): detail_lines must have exactly 5 lines")
            continue
        for ln in lines:
            if len(ln) > 24:
                errors.append(f"pick {i} ({p.get('name')}): detail line too long ({len(ln)} chars): {ln}")
            for b in BANNED:
                if b in ln:
                    errors.append(f"pick {i} ({p.get('name')}): banned phrase '{b}' in: {ln}")
    return errors


def build_video(data, outdir):
    card_paths = cards.build_long_all(data, os.path.join(outdir, "cards_long"))
    bgm = music.make_bgm(os.path.join(outdir, "bgm_long.wav"), dur=float(TOTAL), **music.YUTAI_THEME)
    video = os.path.join(outdir, "video_long.mp4")
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
    probe = os.path.join(outdir, "probe_long")
    os.makedirs(probe, exist_ok=True)
    for t in (2, 7, 15, 23, 31, 39, 47, 56):
        subprocess.run(["ffmpeg", "-nostdin", "-y", "-v", "error", "-ss", str(t),
                        "-i", video, "-frames:v", "1", "-q:v", "4",
                        os.path.join(probe, f"frame_{t}s.jpg")], check=True)
    return video


def youtube_title(data):
    return f"【{data['month_label']}株主優待】おすすめ5選｜権利付き最終日は{data['rights_last_day_label']}"


def youtube_description(data):
    lines = [f"{data['month_label']}の株主優待から、個人投資家に人気の5銘柄を紹介します。",
             f"権利付き最終日は{data['rights_last_day_label']}です。", ""]
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
    return (f"【{data['month_label']}株主優待】おすすめ5選\n\n"
            f"権利付き最終日は{data['rights_last_day_label']}だよ。\n"
            f"{names}\n\n"
            "今年から対象なのは、すかいらーくHDと楽天グループの2つだけ。\n"
            "ヤマハ発動機・キリンHD・ヒューリックは継続保有が必要だから、来年以降に向けた仕込み枠だよ。\n"
            "楽天グループの優待内容は前回実績（今期分は未発表）だから、発表後に確認してね。\n\n"
            "※本動画は銘柄紹介であり投資推奨ではありません。優待は変更される場合があります\n\n"
            f"#株主優待 #優待株 #{data['month_label']}優待 #日本株 #投資初心者 #資産形成 #お金の勉強")


def publish_guide(data, caption):
    base = yutai_main.publish_guide(data, caption)
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
    ap.add_argument("--file", help="data/picks_YYYY-MM.json; default: newest")
    args = ap.parse_args()
    if args.file:
        data_path = os.path.join(ROOT, args.file)
    else:
        files = sorted(glob.glob(os.path.join(ROOT, "data", "picks_*.json")))
        if not files:
            print("no picks file in data/; add a fact-checked picks_YYYY-MM.json first")
            return 1
        data_path = files[-1]
    with open(data_path, encoding="utf-8") as f:
        data = json.load(f)
    tag = os.path.basename(data_path)[len("picks_"):-len(".json")]

    errors = factcheck.check(data) + detail_gate(data)
    if errors:
        print("FACT-CHECK FAILED:")
        for e in errors:
            print(" -", e)
        return 1
    print(f"fact-check OK (yutai-long {tag}, checked {data['checked_date']})")

    outdir = os.path.join(ROOT, "output", tag)
    os.makedirs(outdir, exist_ok=True)
    video = build_video(data, outdir)
    caption = yutai_main.caption_for(data)
    package = {"series": "yutai-long", "tag": tag, "video": video,
               "caption": caption, "duration_sec": TOTAL, "fact_check": "passed",
               "probe_frames": os.path.join(outdir, "probe_long")}
    print(f"video built: {video}")
    with open(os.path.join(outdir, "post_package_long.json"), "w", encoding="utf-8") as f:
        json.dump(package, f, ensure_ascii=False, indent=2)
    guide_path = os.path.join(outdir, "publish_guide_long.txt")
    with open(guide_path, "w", encoding="utf-8") as f:
        f.write(publish_guide(data, caption))
    print(f"publish guide: {guide_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
