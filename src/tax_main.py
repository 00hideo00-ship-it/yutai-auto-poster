#!/usr/bin/env python3
"""Tax-saving measures for salaried workers - one-off short video.
tax JSON -> fact-check gate -> teal/amber cards -> BGM -> 61s video
-> review frames -> post_package.json + publish_guide.txt (TikTok /
YouTube Shorts / Instagram copy included). One-off: no posting here;
Hide publishes manually, same as the other series.
Usage:
  python3 src/tax_main.py                      # newest data/tax_*.json
  python3 src/tax_main.py --file data/tax_2026-11.json
"""
import argparse, glob, json, os, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))
import tax_factcheck, tax_cards, music  # noqa: E402

SEGMENTS = [4, 6, 8, 8, 8, 8, 8, 11]  # title, list, 5 detail cards, summary = 61s
TOTAL = sum(SEGMENTS)

TAX_THEME = {
    "bpm": 122,
    "chords": [(87.31, [174.61, 220.00, 261.63, 349.23]),    # F
               (65.41, [196.00, 261.63, 329.63, 392.00]),    # C
               (73.42, [146.83, 220.00, 293.66, 349.23]),    # Dm
               (58.27, [174.61, 233.08, 293.66, 349.23])],   # Bb
    "melody": [349.23, 392.00, 440.00, 523.25, 440.00, 392.00, 349.23, 293.66,
               329.63, 349.23, 392.00, 440.00, 392.00, 349.23, 329.63, 293.66],
}

LANDING = "https://muse.ai/s/tou-zi-da-hao-ki-shou-kemin-pezi-xop6xzxuxsng8w8/k3ru9cej7TKfxuaIdLAMDCxtN-lr54HyOVmqpbWFP2s"


def build_video(data, outdir):
    card_paths = tax_cards.build_all(data, os.path.join(outdir, "cards"))
    bgm = music.make_bgm(os.path.join(outdir, "bgm.wav"), dur=float(TOTAL),
                         bpm=TAX_THEME["bpm"], chords=TAX_THEME["chords"],
                         melody=TAX_THEME["melody"])
    video = os.path.join(outdir, "video.mp4")
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
    if not (61.0 <= float(dur) <= 63.0):
        raise RuntimeError(f"video duration {dur}s is not in 61-63s")
    probe = os.path.join(outdir, "probe")
    os.makedirs(probe, exist_ok=True)
    for t in (2, 7, 14, 22, 30, 38, 46, 56):
        subprocess.run(["ffmpeg", "-nostdin", "-y", "-v", "error", "-ss", str(t),
                        "-i", video, "-frames:v", "1", "-q:v", "4",
                        os.path.join(probe, f"frame_{t}s.jpg")], check=True)
    return video


def tiktok_caption(data):
    names = "／".join(p["name"] for p in data["picks"])
    return (f"【サラリーマンの{data['title_label']}】5選\n"
            f"{names}\n"
            f"年末調整でできるものと、確定申告が必要なものがあります\n"
            f"※2026年11月時点の制度です。税制は変更される場合があります\n"
            f"※本動画は一般的な制度紹介です。個別の税務相談は税理士にご相談ください\n"
            f"#節税 #サラリーマン #ふるさと納税 #確定拠出年金 #iDeCo #企業型DC #NISA #年末調整 #確定申告")


def youtube_texts(data):
    title = ("【節税対策5選】サラリーマンができる税金の控除まとめ"
             "｜ふるさと納税・確定拠出年金・NISA・住宅ローン控除・医療費控除")
    lines = ["サラリーマンが使える節税対策を5つ紹介します。", ""]
    for p in data["picks"]:
        lines.append(f"■ {p['name']}")
        for ln in p["detail_lines"]:
            lines.append(f"・{ln}")
        lines.append("")
    desc = "\n".join(lines) + (
        "※2026年11月時点の制度です。税制は変更される場合があります\n"
        "※本動画は一般的な制度紹介であり、個別の税務相談は税理士にご相談ください\n"
        "※数値・条件は各公式情報でご確認ください\n\n"
        f"▼お役立ちリンク集（SNSまとめ）\n{LANDING}\n"
        "▼TikTok\nhttps://www.tiktok.com/@toushi_daisuki\n"
        "▼Instagram\nhttps://www.instagram.com/toushi_daisuki_\n\n"
        "#節税 #サラリーマン #ふるさと納税 #確定拠出年金 #iDeCo #NISA #住宅ローン控除 #医療費控除 #Shorts")
    return title, desc


def instagram_caption(data):
    names = "／".join(p["name"] for p in data["picks"])
    return (f"【サラリーマンの{data['title_label']}】5選\n"
            f"{names}\n\n"
            f"年末調整でできるものと、確定申告が必要なものがあるよ\n"
            f"知らないと損する制度ばかりだから、年末前にチェックしてみてね\n\n"
            f"※2026年11月時点の制度です。税制は変更される場合があります\n"
            f"※本動画は一般的な制度紹介です。個別の税務相談は税理士にご相談ください\n\n"
            f"#節税 #節税対策 #サラリーマン #会社員 #ふるさと納税 #iDeCo #NISA "
            f"#住宅ローン控除 #医療費控除 #年末調整 #確定申告 #お金の勉強 #資産形成")


def publish_guide(data):
    yt_title, yt_desc = youtube_texts(data)
    return (f"【手動公開ガイド】サラリーマンの{data['title_label']} 5選\n"
            f"\n■ TikTok\n"
            f"キャプション（そのままコピーして貼り付け）\n{tiktok_caption(data)}\n"
            f"\n投稿設定\n"
            f"公開範囲: 全員に公開\n"
            f"カバー: 動画の先頭フレーム（タイトルカード）を選択\n"
            f"コメント: 許可する\n"
            f"Duet / Stitch: 許可する（拡散用）\n"
            f"AI生成コンテンツのラベル: オン（自動生成した動画のため）\n"
            f"音楽: 動画内のオリジナルBGMのまま（TikTok側の曲は追加しない）\n"
            f"\n■ YouTube Shorts（同じファイルで投稿可）\n"
            f"タイトル\n{yt_title}\n"
            f"\n説明文\n{yt_desc}\n"
            f"\n設定: 視聴者層は「子ども向けではない」を選択／改変されたコンテンツ（AI生成）の開示をオン／公開\n"
            f"\n■ Instagramリール（同じファイルで投稿可）\n"
            f"キャプション\n{instagram_caption(data)}\n"
            f"\n設定: カバーは先頭フレーム（タイトルカード）／AIラベルをオン／フィードにもシェアをオン\n"
            f"\n■ 投稿前チェック\n"
            f"ファクトチェック済み（{data['checked_date']}時点、出典は国税庁・金融庁・厚生労働省）\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", help="data/tax_YYYY-MM.json; default: newest")
    args = ap.parse_args()

    if args.file:
        data_path = os.path.join(ROOT, args.file)
    else:
        files = sorted(glob.glob(os.path.join(ROOT, "data", "tax_*.json")))
        if not files:
            print("no tax file in data/; add a fact-checked tax_YYYY-MM.json first")
            return 1
        data_path = files[-1]
    with open(data_path, encoding="utf-8") as f:
        data = json.load(f)
    tag = os.path.basename(data_path)[len("tax_"):-len(".json")]

    errors = tax_factcheck.check(data)
    if errors:
        print("FACT-CHECK FAILED:")
        for e in errors:
            print(" -", e)
        return 1
    print(f"fact-check OK (tax {tag}, checked {data['checked_date']})")

    outdir = os.path.join(ROOT, "output", f"tax-{tag}")
    os.makedirs(outdir, exist_ok=True)
    video = build_video(data, outdir)
    package = {"series": "tax", "tag": tag, "video": video,
               "caption": tiktok_caption(data), "duration_sec": TOTAL,
               "fact_check": "passed",
               "probe_frames": os.path.join(outdir, "probe")}
    print(f"video built: {video}")
    with open(os.path.join(outdir, "post_package.json"), "w", encoding="utf-8") as f:
        json.dump(package, f, ensure_ascii=False, indent=2)
    print(f"package: {os.path.join(outdir, 'post_package.json')}")
    guide_path = os.path.join(outdir, "publish_guide.txt")
    with open(guide_path, "w", encoding="utf-8") as f:
        f.write(publish_guide(data))
    print(f"publish guide: {guide_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
