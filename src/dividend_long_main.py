#!/usr/bin/env python3
"""Long (60s+) version of the high-dividend stock video, built from the
same data/dividend_YYYY-MM.json as the 30s cut.

Structure: list card (8s) -> one detail card per pick (10s each) ->
summary card (10s) = 68s. Same deep-green x gold design with the ¥ badge
and the same BGM system as the 30s dividend series. No posting here:
Hide publishes manually, same as the 30s version.
Usage:
  python3 src/dividend_long_main.py                      # newest data/dividend_*.json
  python3 src/dividend_long_main.py --file data/dividend_2026-11.json
"""
import argparse, glob, json, os, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))
import dividend_factcheck, dividend_cards, dividend_main, music  # noqa: E402

SEGMENTS = [8, 10, 10, 10, 10, 10, 10]  # list, 5 detail cards, summary = 68s
TOTAL = sum(SEGMENTS)


def build_video(data, outdir):
    card_paths = dividend_cards.build_long_all(data, os.path.join(outdir, "cards_long"))
    bgm = music.make_bgm(os.path.join(outdir, "bgm_long.wav"), dur=float(TOTAL), **music.DIVIDEND_THEME)
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
    # list 4s, detail cards 13/23/33/43/53s, summary 63s
    for t in (4, 13, 23, 33, 43, 53, 63):
        subprocess.run(["ffmpeg", "-nostdin", "-y", "-v", "error", "-ss", str(t),
                        "-i", video, "-frames:v", "1", "-q:v", "4",
                        os.path.join(probe, f"frame_{t}s.jpg")], check=True)
    return video


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", help="data/dividend_YYYY-MM.json; default: newest")
    args = ap.parse_args()

    if args.file:
        data_path = os.path.join(ROOT, args.file)
    else:
        files = sorted(glob.glob(os.path.join(ROOT, "data", "dividend_*.json")))
        if not files:
            print("no dividend file in data/; add a fact-checked dividend_YYYY-MM.json first")
            return 1
        data_path = files[-1]
    with open(data_path, encoding="utf-8") as f:
        data = json.load(f)
    tag = os.path.basename(data_path)[len("dividend_"):-len(".json")]  # e.g. 2026-11

    errors = dividend_factcheck.check(data)
    if errors:
        print("FACT-CHECK FAILED:")
        for e in errors:
            print(" -", e)
        return 1
    print(f"fact-check OK (dividend {tag}, checked {data['checked_date']})")

    outdir = os.path.join(ROOT, "output", f"dividend-{tag}")
    os.makedirs(outdir, exist_ok=True)
    video = build_video(data, outdir)
    caption = dividend_main.caption_for(data)
    package = {"series": "dividend-long", "tag": tag, "video": video,
               "caption": caption, "duration_sec": TOTAL, "fact_check": "passed",
               "probe_frames": os.path.join(outdir, "probe_long")}
    print(f"video built: {video}")
    with open(os.path.join(outdir, "post_package_long.json"), "w", encoding="utf-8") as f:
        json.dump(package, f, ensure_ascii=False, indent=2)
    print(f"package: {os.path.join(outdir, 'post_package_long.json')}")
    # Regenerate the publish guide (same caption/settings for both cuts),
    # adding the two video files and the Shorts/Reels note.
    guide = dividend_main.publish_guide(data, caption)
    files_section = (f"■ 動画ファイル\n"
                     f"30秒版: video.mp4（30秒）\n"
                     f"1分超版: video_long.mp4（{TOTAL}秒）\n")
    guide = guide.replace("■ 投稿前チェック", files_section + "\n■ 投稿前チェック")
    guide_path = os.path.join(outdir, "publish_guide.txt")
    with open(guide_path, "w", encoding="utf-8") as f:
        f.write(guide)
    print(f"publish guide: {guide_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
