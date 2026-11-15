#!/usr/bin/env python3
"""Weekly rights-date calendar video (61s, orange x cream, badge「今週」).

Structure: title (6s) -> one detail card per pick (11s each) ->
next-week preview (11s) -> summary checklist (11s) = 61s.
BGM: G major, ~112 BPM (music.CALENDAR_THEME).
No posting here: Hide publishes manually, same as the other series.
Usage:
  python3 src/calendar_main.py                        # newest data/calendar_*.json
  python3 src/calendar_main.py --file data/calendar_2026-11-16.json
"""
import argparse, glob, json, os, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))
import calendar_factcheck, calendar_cards, music  # noqa: E402

SEGMENTS = [6, 11, 11, 11, 11, 11]  # title, 3 stock cards, preview, summary = 61s
TOTAL = sum(SEGMENTS)


def build_video(data, outdir):
    card_paths = calendar_cards.build_all(data, os.path.join(outdir, "cards"))
    theme = music.CALENDAR_THEME
    bgm = music.make_bgm(os.path.join(outdir, "bgm.wav"), dur=float(TOTAL),
                         bpm=theme["bpm"], chords=theme["chords"], melody=theme["melody"])
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
    # title 3s, stocks 11/22/33s, preview 45s, summary 56s
    for t in (3, 11, 22, 33, 45, 56):
        subprocess.run(["ffmpeg", "-nostdin", "-y", "-v", "error", "-ss", str(t),
                        "-i", video, "-frames:v", "1", "-q:v", "4",
                        os.path.join(probe, f"frame_{t}s.jpg")], check=True)
    return video


def caption_for(data):
    names = "・".join(f"{p['name']}({p['code']})" for p in data["picks"])
    return (f"【今週の権利確定日カレンダー】{data['week_label']}\n"
            f"権利付き最終日は{data['picks'][0]['rights_label']}！\n"
            f"{names}\n"
            f"来週の予告：{data['next_week']['rights_label']}は月末組が本番\n"
            f"※本動画は銘柄紹介であり投資推奨ではありません。優待内容・条件は各社IRでご確認ください\n"
            f"#株主優待 #権利確定日 #日本株 #投資初心者 #優待株")


def publish_guide(data, caption):
    lines = []
    for p in data["picks"]:
        lines.append(f"{p['rights_label']} {p['name']}({p['code']})："
                     f"{p['benefit_lines'][0]}／{p['dividend_line']}／{p['min_investment_label']}")
    nw_lines = []
    for item in data["next_week"]["items"]:
        nw_lines.append(f"{item['name']}({item['code']})：{item['line']}")
    return (f"【手動公開ガイド】今週の権利確定日カレンダー（{data['week_label']}）\n"
            f"\n■ 対象銘柄（今週）\n" + "\n".join(lines) +
            f"\n\n■ 来週の予告（{data['next_week']['rights_label']} 権利付き最終日）\n" + "\n".join(nw_lines) +
            f"\n\n■ キャプション（そのままコピーして貼り付け）\n{caption}\n"
            f"\n■ 投稿設定\n"
            f"公開範囲: 全員に公開\n"
            f"カバー: 動画の先頭フレーム（タイトルカード）を選択\n"
            f"コメント: 許可する\n"
            f"Duet / Stitch: 許可する（拡散用）\n"
            f"AI生成コンテンツのラベル: オン（自動生成した動画のため）\n"
            f"音楽: 動画内のオリジナルBGMのまま（TikTok側の曲は追加しない）\n"
            f"\n■ その他\n"
            f"同じファイルを YouTube Shorts / Instagramリールにもそのまま投稿できます\n"
            f"\n■ 投稿前チェック\n"
            f"ファクトチェック済み（{data['checked_date']}時点）\n"
            f"権利付き最終日（今週）: {data['picks'][0]['rights_label']}\n"
            f"権利付き最終日（来週）: {data['next_week']['rights_label']}\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", help="data/calendar_YYYY-MM-DD.json; default: newest")
    args = ap.parse_args()

    if args.file:
        data_path = os.path.join(ROOT, args.file)
    else:
        files = sorted(glob.glob(os.path.join(ROOT, "data", "calendar_*.json")))
        if not files:
            print("no calendar file in data/; add a fact-checked calendar_YYYY-MM-DD.json first")
            return 1
        data_path = files[-1]
    with open(data_path, encoding="utf-8") as f:
        data = json.load(f)
    tag = os.path.basename(data_path)[len("calendar_"):-len(".json")]  # e.g. 2026-11-16

    errors = calendar_factcheck.check(data)
    if errors:
        print("FACT-CHECK FAILED:")
        for e in errors:
            print(" -", e)
        return 1
    print(f"fact-check OK (calendar {tag}, checked {data['checked_date']})")

    outdir = os.path.join(ROOT, "output", f"calendar-{tag}")
    os.makedirs(outdir, exist_ok=True)
    video = build_video(data, outdir)
    caption = caption_for(data)
    package = {"series": "calendar", "tag": tag, "video": video,
               "caption": caption, "duration_sec": TOTAL, "fact_check": "passed",
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
