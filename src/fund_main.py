#!/usr/bin/env python3
"""High-distribution investment-trust short-video pipeline (third series).
fund JSON -> fact-check gate -> violet/gold cards -> BGM -> 30s TikTok video
-> review frames -> post_package.json + publish_guide.txt. One-off series:
no posting here; Hide publishes manually, same as the other series.
Usage:
  python3 src/fund_main.py                      # newest data/fund_*.json
  python3 src/fund_main.py --file data/fund_2026-11.json
"""
import argparse, glob, json, os, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))
import fund_factcheck, fund_cards, music  # noqa: E402

SEGMENTS = [11, 10, 9]  # list, points, summary = 30s total


def build_video(data, outdir):
    card_paths = fund_cards.build_all(data, os.path.join(outdir, "cards"))
    bgm = music.make_bgm(os.path.join(outdir, "bgm.wav"), dur=30.0)
    video = os.path.join(outdir, "video.mp4")
    fc = ("[0:v]fps=30,format=yuv420p[v0];[1:v]fps=30,format=yuv420p[v1];"
          "[2:v]fps=30,format=yuv420p[v2];[v0][v1][v2]concat=n=3:v=1:a=0[v];"
          "[3:a]atrim=0:30,afade=t=out:st=28:d=2,"
          "aformat=sample_rates=44100:channel_layouts=stereo[a]")
    cmd = ["ffmpeg", "-nostdin", "-y", "-v", "error"]
    for path, dur in zip(card_paths, SEGMENTS):
        cmd += ["-loop", "1", "-t", str(dur), "-i", path]
    cmd += ["-i", bgm, "-filter_complex", fc, "-map", "[v]", "-map", "[a]",
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "22",
            "-c:a", "aac", "-b:a", "160k", "-t", "30", video]
    subprocess.run(cmd, check=True)
    dur = subprocess.check_output(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", video]).decode().strip()
    if not (29.5 <= float(dur) <= 30.5):
        raise RuntimeError(f"video duration {dur}s is not 30s")
    probe = os.path.join(outdir, "probe")
    os.makedirs(probe, exist_ok=True)
    for t in (5, 16, 26):
        subprocess.run(["ffmpeg", "-nostdin", "-y", "-v", "error", "-ss", str(t),
                        "-i", video, "-frames:v", "1", "-q:v", "4",
                        os.path.join(probe, f"frame_{t}s.jpg")], check=True)
    return video


def caption_for(data):
    names = "、".join(p["short_name"] for p in data["picks"])
    return (f"【{data['title_label']}】おすすめ5選\n"
            f"{names}\n"
            f"※分配金利回りは基準価額により変動します（{data['yield_basis_label']}）\n"
            f"※分配金には元本の払戻しが含まれる場合があります\n"
            f"※本動画はファンド紹介であり投資推奨ではありません。分配内容・費用は各社目論見書でご確認ください\n"
            f"#投資信託 #高配当 #分配金 #NISA #投資初心者")


def publish_guide(data, caption):
    checked = max(p["checked_date"] for p in data["picks"])
    return (f"【手動公開ガイド】{data['title_label']} おすすめ5選\n"
            f"\n■ キャプション（そのままコピーして貼り付け）\n{caption}\n"
            f"\n■ 投稿設定\n"
            f"公開範囲: 全員に公開\n"
            f"カバー: 動画の先頭フレーム（一覧カード）を選択\n"
            f"コメント: 許可する\n"
            f"Duet / Stitch: 許可する（拡散用）\n"
            f"AI生成コンテンツのラベル: オン（自動生成した動画のため）\n"
            f"音楽: 動画内のオリジナルBGMのまま（TikTok側の曲は追加しない）\n"
            f"\n■ 投稿前チェック\n"
            f"ファクトチェック済み（{checked}時点）\n"
            f"分配金利回りの基準: {data['yield_basis_label']}\n"
            f"注意: {data['caveat_label']}。毎月分配型はNISA対象外\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", help="data/fund_YYYY-MM.json; default: newest")
    args = ap.parse_args()

    if args.file:
        data_path = os.path.join(ROOT, args.file)
    else:
        files = sorted(glob.glob(os.path.join(ROOT, "data", "fund_*.json")))
        if not files:
            print("no fund file in data/; add a fact-checked fund_YYYY-MM.json first")
            return 1
        data_path = files[-1]
    with open(data_path, encoding="utf-8") as f:
        data = json.load(f)
    tag = os.path.basename(data_path)[len("fund_"):-len(".json")]  # e.g. 2026-11

    errors = fund_factcheck.check(data)
    if errors:
        print("FACT-CHECK FAILED:")
        for e in errors:
            print(" -", e)
        return 1
    print(f"fact-check OK (fund {tag}, checked {data['checked_date']})")

    outdir = os.path.join(ROOT, "output", f"fund-{tag}")
    os.makedirs(outdir, exist_ok=True)
    video = build_video(data, outdir)
    caption = caption_for(data)
    package = {"series": "fund", "tag": tag, "video": video, "caption": caption,
               "duration_sec": 30, "fact_check": "passed",
               "probe_frames": os.path.join(outdir, "probe")}
    print(f"video built: {video}")
    with open(os.path.join(outdir, "post_package.json"), "w", encoding="utf-8") as f:
        json.dump(package, f, ensure_ascii=False, indent=2)
    print(f"package: {os.path.join(outdir, 'post_package.json')}")
    guide_path = os.path.join(outdir, "publish_guide.txt")
    with open(guide_path, "w", encoding="utf-8") as f:
        f.write(publish_guide(data, caption))
    print(f"publish guide: {guide_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
