#!/usr/bin/env python3
"""Real-estate tax benefits for a JPY10M salaried worker - one-off video.
Reuses the tax series design (teal/amber cards, TAX_THEME BGM) and the
tax fact-check gate. One-off: no posting here; Hide publishes manually.
Usage:
  python3 src/estate_main.py                      # newest data/estate_*.json
  python3 src/estate_main.py --file data/estate_2026-11.json
"""
import argparse, glob, json, os, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))
import tax_factcheck, tax_cards, music, estate_cards  # noqa: E402
from tax_main import TAX_THEME, LANDING  # noqa: E402

SEGMENTS = [4, 6, 8, 8, 8, 8, 8, 11]  # title, list, 5 detail cards, summary = 61s
TOTAL = sum(SEGMENTS)


def build_video(data, outdir):
    card_paths = tax_cards.build_all(data, os.path.join(outdir, "cards"))
    # Hide's request: the trial card uses its own comparison layout.
    estate_cards.trial_card(data, os.path.join(outdir, "cards", "card_detail_3.png"))
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
    return (f"【不動産投資の節税メリット】5つのポイント\n"
            f"{names}\n"
            f"年収1,000万円会社員の場合を例に、仕組みと試算、注意点までまとめました\n"
            f"※試算は単身・社会保険料は概算などの前提で変わります\n"
            f"※2026年11月時点の制度です。税制は変更される場合があります\n"
            f"※本動画は一般的な制度紹介です。個別の税務相談は税理士にご相談ください\n"
            f"#不動産投資 #節税 #損益通算 #減価償却 #サラリーマン #会社員 #確定申告 #資産形成")


def youtube_texts(data):
    title = ("【不動産の節税まとめ】年収1,000万円会社員の場合の不動産投資の節税メリット"
             "｜損益通算・減価償却・試算と注意点")
    lines = ["年収1,000万円会社員の場合を例に、不動産投資で得られる節税メリットを5つのポイントで紹介します。", ""]
    for p in data["picks"]:
        lines.append(f"■ {p['name']}")
        for ln in p["detail_lines"]:
            lines.append(f"・{ln}")
        lines.append("")
    desc = "\n".join(lines) + (
        "【試算の前提】単身、社会保険料は年収の約14%で概算。給与所得控除195万円（上限）を差し引いた給与所得805万円から、課税所得は約605万円となり、所得税率20%の区分に入ります。"
        "限界税率は所得税20%（復興特別所得税込みで20.42%）＋住民税10%＝約30.4%です。家族構成や各種控除で実際の税額は変わります。税金の目安は、課税所得約605万円で約140万円（所得税の速算表＋住民税10%で計算）、不動産所得の赤字100万円で課税所得が約505万円になると約110万円で、差は約30万円です。うち所得税分（約20万円）は確定申告で還付され、住民税分（約10万円）は翌年分の住民税が軽くなります。\n\n"
        "※2026年11月時点の制度です。税制は変更される場合があります\n"
        "※本動画は一般的な制度紹介であり、投資の勧誘や個別の税務相談ではありません。個別の判断は税理士にご相談ください\n"
        "※数値・条件は国税庁などの公式情報でご確認ください\n\n"
        f"▼お役立ちリンク集（SNSまとめ）\n{LANDING}\n"
        "▼TikTok\nhttps://www.tiktok.com/@toushi_daisuki\n"
        "▼Instagram\nhttps://www.instagram.com/toushi_daisuki_\n\n"
        "#不動産投資 #節税 #損益通算 #減価償却 #サラリーマン #確定申告 #資産形成 #Shorts")
    return title, desc


def instagram_caption(data):
    names = "／".join(p["name"] for p in data["picks"])
    return (f"【不動産投資の節税メリット】5つのポイント\n"
            f"{names}\n\n"
            f"年収1,000万円会社員の場合、税率が高い分、不動産の赤字を給与と相殺する効果が大きくなります\n"
            f"ただし土地の利息分は相殺できないなど、注意点もあわせてチェックしてみてね\n\n"
            f"※試算は単身・社会保険料は概算などの前提で変わります\n"
            f"※2026年11月時点の制度です。税制は変更される場合があります\n"
            f"※本動画は一般的な制度紹介です。個別の税務相談は税理士にご相談ください\n\n"
            f"#不動産投資 #節税 #節税対策 #損益通算 #減価償却 #サラリーマン #会社員 "
            f"#確定申告 #資産形成 #お金の勉強")


def publish_guide(data):
    yt_title, yt_desc = youtube_texts(data)
    return (f"【手動公開ガイド】不動産投資の節税メリット（年収1,000万円会社員の場合）\n"
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
            f"ファクトチェック済み（{data['checked_date']}時点、出典は国税庁）\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", help="data/estate_YYYY-MM.json; default: newest")
    args = ap.parse_args()

    if args.file:
        data_path = os.path.join(ROOT, args.file)
    else:
        files = sorted(glob.glob(os.path.join(ROOT, "data", "estate_*.json")))
        if not files:
            print("no estate file in data/; add a fact-checked estate_YYYY-MM.json first")
            return 1
        data_path = files[-1]
    with open(data_path, encoding="utf-8") as f:
        data = json.load(f)
    tag = os.path.basename(data_path)[len("estate_"):-len(".json")]

    errors = tax_factcheck.check(data)
    if errors:
        print("FACT-CHECK FAILED:")
        for e in errors:
            print(" -", e)
        return 1
    print(f"fact-check OK (estate {tag}, checked {data['checked_date']})")

    outdir = os.path.join(ROOT, "output", f"estate-{tag}")
    os.makedirs(outdir, exist_ok=True)
    video = build_video(data, outdir)
    package = {"series": "estate", "tag": tag, "video": video,
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
