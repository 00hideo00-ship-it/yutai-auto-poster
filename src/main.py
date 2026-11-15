#!/usr/bin/env python3
"""Weekly yutai short-video pipeline.
picks JSON -> fact-check gate -> pop cards -> BGM -> 30s TikTok video ->
review frames -> (optional) TikTok post.
Usage:
  python3 src/main.py                 # newest data/picks_*.json, generate only
  python3 src/main.py --month 2026-12
  python3 src/main.py --post --mode draft
  python3 src/main.py --post --mode direct --privacy SELF_ONLY
"""
import argparse, glob, json, os, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))
import factcheck, cards, music  # noqa: E402

SEGMENTS = [3, 9, 9, 9]  # title, list, points, summary = 30s total


def load_env():
    path = os.path.join(ROOT, ".env")
    if os.path.exists(path):
        for line in open(path, encoding="utf-8"):
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())


def build_video(data, outdir):
    card_paths = cards.build_all(data, os.path.join(outdir, "cards"))
    bgm = music.make_bgm(os.path.join(outdir, "bgm.wav"), dur=30.0, **music.YUTAI_THEME)
    video = os.path.join(outdir, "video.mp4")
    inputs = "".join(f"[{i}:v]fps=30,format=yuv420p[v{i}];" for i in range(len(card_paths)))
    concat = "".join(f"[v{i}]" for i in range(len(card_paths)))
    fc = (f"{inputs}{concat}concat=n={len(card_paths)}:v=1:a=0[v];"
          f"[{len(card_paths)}:a]atrim=0:30,afade=t=out:st=28:d=2,"
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
    for t in (1, 7, 16, 25):
        subprocess.run(["ffmpeg", "-nostdin", "-y", "-v", "error", "-ss", str(t),
                        "-i", video, "-frames:v", "1", "-q:v", "4",
                        os.path.join(probe, f"frame_{t}s.jpg")], check=True)
    return video


def caption_for(data):
    names = "、".join(p["name"] for p in data["picks"])
    return (f"【{data['month_label']}株主優待】おすすめ5選\n"
            f"権利付き最終日は{data['rights_last_day_label']}！\n"
            f"{names}\n"
            f"※楽天グループの優待内容は前回実績です（今期分は発表後に要確認）\n"
            f"※本動画は銘柄紹介であり投資推奨ではありません。優待内容・条件は各社IRでご確認ください\n"
            f"#株主優待 #優待株 #{data['month_label']}優待 #日本株 #投資初心者")


def publish_guide(data, caption):
    checked = data.get("checked_date") or max(p["checked_date"] for p in data["picks"])
    return (f"【手動公開ガイド】{data['month_label']}株主優待 おすすめ5選\n"
            f"\n■ キャプション（そのままコピーして貼り付け）\n{caption}\n"
            f"\n■ 投稿設定\n"
            f"公開範囲: 全員に公開\n"
            f"カバー: 動画の先頭フレーム（タイトルカード）を選択\n"
            f"コメント: 許可する\n"
            f"Duet / Stitch: 許可する（拡散用）\n"
            f"AI生成コンテンツのラベル: オン（自動生成した動画のため）\n"
            f"音楽: 動画内のオリジナルBGMのまま（TikTok側の曲は追加しない）\n"
            f"\n■ 投稿前チェック\n"
            f"ファクトチェック済み（{checked}時点）\n"
            f"権利付き最終日: {data['rights_last_day_label']}\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--month", help="YYYY-MM; default: newest picks file")
    ap.add_argument("--post", action="store_true")
    ap.add_argument("--mode", choices=["draft", "direct"], default="draft")
    ap.add_argument("--privacy", default="SELF_ONLY")
    args = ap.parse_args()
    load_env()

    if args.month:
        picks_path = os.path.join(ROOT, "data", f"picks_{args.month}.json")
        month = args.month
    else:
        files = sorted(glob.glob(os.path.join(ROOT, "data", "picks_*.json")))
        if not files:
            print("no picks file in data/; add a fact-checked picks_YYYY-MM.json first")
            return 1
        picks_path = files[-1]
        month = os.path.basename(picks_path)[6:-5]
    with open(picks_path, encoding="utf-8") as f:
        data = json.load(f)

    errors = factcheck.check(data)
    if errors:
        print("FACT-CHECK FAILED:")
        for e in errors:
            print(" -", e)
        return 1
    print(f"fact-check OK ({month}, checked {data['checked_date']})")

    outdir = os.path.join(ROOT, "output", month)
    os.makedirs(outdir, exist_ok=True)
    video = build_video(data, outdir)
    caption = caption_for(data)
    package = {"month": month, "video": video, "caption": caption,
               "duration_sec": 30, "fact_check": "passed",
               "probe_frames": os.path.join(outdir, "probe")}
    print(f"video built: {video}")

    if args.post:
        import tiktok
        key = os.environ.get("TIKTOK_CLIENT_KEY")
        secret = os.environ.get("TIKTOK_CLIENT_SECRET")
        refresh = os.environ.get("TIKTOK_REFRESH_TOKEN")
        if not (key and secret and refresh):
            print("TikTok credentials missing -> post skipped, package only")
        else:
            tokens = tiktok.refresh_access_token(key, secret, refresh)
            new_refresh = tokens.get("refresh_token", "")
            with open(os.path.join(outdir, "rotated_refresh_token.txt"), "w") as f:
                f.write(new_refresh)
            if new_refresh and new_refresh != refresh:
                # TikTok rotates the refresh token on every refresh; persist
                # the new one back to .env or the next run cannot refresh.
                env_path = os.path.join(ROOT, ".env")
                lines = []
                if os.path.exists(env_path):
                    lines = open(env_path, encoding="utf-8").read().splitlines()
                lines = [f"TIKTOK_REFRESH_TOKEN={new_refresh}" if l.startswith("TIKTOK_REFRESH_TOKEN=") else l
                         for l in lines]
                if not any(l.startswith("TIKTOK_REFRESH_TOKEN=") for l in lines):
                    lines.append(f"TIKTOK_REFRESH_TOKEN={new_refresh}")
                with open(env_path, "w", encoding="utf-8") as f:
                    f.write("\n".join(lines) + "\n")
                print("refresh token rotated -> .env updated")
            result = tiktok.post_video(tokens["access_token"], video, caption,
                                       mode=args.mode, privacy_level=args.privacy)
            package["post_result"] = result
            print(f"posted: {result['status']} ({result['publish_id']})")
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
