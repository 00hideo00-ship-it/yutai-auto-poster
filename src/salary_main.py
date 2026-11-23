#!/usr/bin/env python3
"""Salary-trend one-off video: 「給料は過去最高なのに手取りが増えない理由」.
Reuses the tax series identity (teal/amber, TAX_THEME BGM) and the tax
fact-check gate, with its own cards (src/salary_cards.py, badge 手取り).
Not a 「5選」 format video (Hide, 2026-11-23: non-stock videos need not
use the 5-pick format). One-off: no posting here; Hide publishes manually.
Usage:
  python3 src/salary_main.py                              # newest data/salary_trend_*.json
  python3 src/salary_main.py --file data/salary_trend_2026-11.json
"""
import argparse, glob, json, os, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))
import tax_factcheck, salary_cards, music  # noqa: E402
from tax_main import TAX_THEME, LANDING  # noqa: E402

SEGMENTS = [4, 6, 8, 8, 8, 8, 8, 11]  # title, list, 5 detail cards, summary = 61s
TOTAL = sum(SEGMENTS)

NOTE = "※数値は国税庁・協会けんぽ等の公表値です。本人負担率は各料率からの試算です"
NOTE2 = "※制度・料率は変更される場合があります"


def build_video(data, outdir):
    card_paths = salary_cards.build_all(data, os.path.join(outdir, "cards"))
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
    return (f"【{data['title']}】\n"
            f"平均給与は2025年に487万円と過去最高。それでも手取りが増えた実感が薄いのは、"
            f"社会保険料の本人負担が20年で約12%から約15.5%（試算）に上がったから\n"
            f"{NOTE}\n{NOTE2}\n"
            f"#手取り #社会保険料 #厚生年金 #健康保険 #介護保険 #年収の壁 #サラリーマン #給料 #お金の勉強")


def youtube_texts(data):
    title = (f"{data['title']}｜平均給与487万円でも手取りが増えないワケ")
    lines = ["平均給与は2025年に487万円と、名目では過去最高です。",
             "それでも手取りが増えた実感が薄い理由を、公式統計の数字で解説します。", ""]
    for p in data["picks"]:
        lines.append(f"■ {p['name']}")
        for ln in p["detail_lines"]:
            lines.append(f"・{ln}")
        lines.append("")
    desc = "\n".join(lines) + (
        "【本人負担率の試算について】厚生年金・健康保険・介護保険の本人負担分（労使折半）と"
        "雇用保険の本人負担分を、40〜64歳の前提で合算した概算です。"
        "加入する健康保険組合や都道府県で料率は異なります。\n\n"
        f"{NOTE}\n{NOTE2}\n"
        "※本動画は公表統計をもとにした制度解説です\n\n"
        f"▼お役立ちリンク集（SNSまとめ）\n{LANDING}\n"
        "▼TikTok\nhttps://www.tiktok.com/@toushi_daisuki\n"
        "▼Instagram\nhttps://www.instagram.com/toushi_daisuki_\n\n"
        "#手取り #社会保険料 #厚生年金 #健康保険 #介護保険 #年収の壁 #サラリーマン #給料 #資産形成 #Shorts")
    return title, desc


def instagram_caption(data):
    return (f"【{data['title']}】\n\n"
            f"平均給与は2025年に487万円で過去最高\n"
            f"でも手取りが増えた実感が薄いのは、社会保険料の本人負担が"
            f"20年で約12%から約15.5%（試算）に上がったからだよ\n"
            f"厚生年金は18.3%で固定、介護保険と子育て支援金が上乗せされている\n\n"
            f"{NOTE}\n{NOTE2}\n\n"
            f"#手取り #社会保険料 #厚生年金 #健康保険 #介護保険 #年収の壁 "
            f"#サラリーマン #会社員 #給料 #お金の勉強 #資産形成")


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
            f"ファクトチェック済み（{data['checked_date']}時点、出典は国税庁・日本年金機構・協会けんぽ・財務省）\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", help="data/salary_trend_YYYY-MM.json; default: newest")
    args = ap.parse_args()

    if args.file:
        data_path = os.path.join(ROOT, args.file)
    else:
        files = sorted(glob.glob(os.path.join(ROOT, "data", "salary_trend_*.json")))
        if not files:
            print("no salary_trend file in data/; add a fact-checked salary_trend_YYYY-MM.json first")
            return 1
        data_path = files[-1]
    with open(data_path, encoding="utf-8") as f:
        data = json.load(f)
    tag = os.path.basename(data_path)[len("salary_trend_"):-len(".json")]

    errors = tax_factcheck.check(data)
    if errors:
        print("FACT-CHECK FAILED:")
        for e in errors:
            print(" -", e)
        return 1
    print(f"fact-check OK (salary_trend {tag}, checked {data['checked_date']})")

    outdir = os.path.join(ROOT, "output", f"salary-trend-{tag}")
    os.makedirs(outdir, exist_ok=True)
    video = build_video(data, outdir)
    package = {"series": "salary_trend", "tag": tag, "video": video,
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
