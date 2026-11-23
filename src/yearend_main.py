#!/usr/bin/env python3
"""Year-end tax-deadline one-off video: 「年内にやらないと損する節税の締切」.
Reuses the tax series identity (teal/amber, badge 節税, TAX_THEME BGM)
and the tax fact-check gate, with its own cards (src/yearend_cards.py).
Story: tax deadlines cluster at year-end -> walk them in deadline
order -> close on 「締切を守ること」. One-off: no posting here;
Hide publishes manually.
Usage:
  python3 src/yearend_main.py                              # newest data/yearend_*.json
  python3 src/yearend_main.py --file data/yearend_2026-11.json
"""
import argparse, glob, json, os, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))
import tax_factcheck, yearend_cards, music  # noqa: E402
from tax_main import TAX_THEME, LANDING  # noqa: E402

SEGMENTS = [5, 7, 9, 9, 9, 9, 9, 13]  # title, list, 5 detail cards, summary = 70s
TOTAL = sum(SEGMENTS)

NOTE = "※制度・期限は2026年11月24日時点の情報です"
NOTE2 = "※投資推奨ではありません"


def build_video(data, outdir):
    card_paths = yearend_cards.build_all(data, os.path.join(outdir, "cards"))
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
    if not (65.0 <= float(dur) <= 75.0):
        raise RuntimeError(f"video duration {dur}s is not in 65-75s")
    probe = os.path.join(outdir, "probe")
    os.makedirs(probe, exist_ok=True)
    for t in (2, 8, 16, 25, 34, 43, 52, 63):
        subprocess.run(["ffmpeg", "-nostdin", "-y", "-v", "error", "-ss", str(t),
                        "-i", video, "-frames:v", "1", "-q:v", "4",
                        os.path.join(probe, f"frame_{t}s.jpg")], check=True)
    return video


def tiktok_caption(data):
    return (f"【{data['title']}】\n"
            f"節税の締切は年末に集中します。締切の早い順にチェックして、取りこぼしを防ぎましょう\n"
            f"損出しは12月28日まで／ふるさと納税は12月31日まで／ワンストップ申請は1月10日必着\n"
            f"{NOTE}\n{NOTE2}\n"
            f"#節税 #年末 #ふるさと納税 #損出し #NISA #ワンストップ特例 #医療費控除 #確定申告 #サラリーマン")


def youtube_texts(data):
    title = (f"{data['title']}｜損出し12/28・ふるさと納税12/31・ワンストップ申請1/10必着")
    lines = ["節税の締切は年末に集中します。",
             "締切の早い順に5つを確認して、取りこぼしを防ぎましょう。", ""]
    for p in data["picks"]:
        stage = p.get("stage", "")
        lines.append(f"■ 【{stage}】{p['name']}" if stage else f"■ {p['name']}")
        for ln in p["detail_lines"]:
            lines.append(f"・{ln}")
        lines.append("")
    desc = "\n".join(lines) + (
        f"{NOTE}\n{NOTE2}\n"
        "※本動画は公表情報をもとにした制度解説です。個別の税務判断は税理士等にご確認ください\n\n"
        f"▼お役立ちリンク集（SNSまとめ）\n{LANDING}\n"
        "▼TikTok\nhttps://www.tiktok.com/@toushi_daisuki\n"
        "▼Instagram\nhttps://www.instagram.com/toushi_daisuki_\n\n"
        "#節税 #年末 #ふるさと納税 #損出し #NISA #ワンストップ特例 #医療費控除 #確定申告 #サラリーマン #Shorts")
    return title, desc


def instagram_caption(data):
    return (f"【{data['title']}】\n\n"
            f"節税の締切は年末に集中するよ\n"
            f"損出しは12月28日、ふるさと納税は12月31日が締切\n"
            f"NISAの年間枠360万円は翌年に繰り越せない\n"
            f"ワンストップ特例の申請書は1月10日必着だから、出し忘れに注意\n\n"
            f"{NOTE}\n{NOTE2}\n\n"
            f"#節税 #年末 #ふるさと納税 #損出し #NISA #ワンストップ特例 "
            f"#医療費控除 #確定申告 #サラリーマン #会社員 #資産形成")


def publish_guide(data):
    yt_title, yt_desc = youtube_texts(data)
    return (f"【手動公開ガイド】{data['title']}\n"
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
            f"ファクトチェック済み（{data['checked_date']}時点、出典はSBI証券・総務省・金融庁・国税庁）\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", help="data/yearend_YYYY-MM.json; default: newest")
    args = ap.parse_args()

    if args.file:
        data_path = os.path.join(ROOT, args.file)
    else:
        files = sorted(glob.glob(os.path.join(ROOT, "data", "yearend_*.json")))
        if not files:
            print("no yearend file in data/; add a fact-checked yearend_YYYY-MM.json first")
            return 1
        data_path = files[-1]
    with open(data_path, encoding="utf-8") as f:
        data = json.load(f)
    tag = os.path.basename(data_path)[len("yearend_"):-len(".json")]

    errors = tax_factcheck.check(data)
    if errors:
        print("FACT-CHECK FAILED:")
        for e in errors:
            print(" -", e)
        return 1
    print(f"fact-check OK (yearend {tag}, checked {data['checked_date']})")

    outdir = os.path.join(ROOT, "output", f"yearend-{tag}")
    os.makedirs(outdir, exist_ok=True)
    video = build_video(data, outdir)
    package = {"series": "yearend_tax", "tag": tag, "video": video,
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
