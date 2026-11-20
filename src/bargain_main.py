#!/usr/bin/env python3
"""61-second video for the weekly bargain series (stocks that fell sharply
this week, Fri 20:00 post).

First edition: week of 2026-11-16 to 2026-11-20. The Nikkei fell 7.7% in
the week as US AI stocks sold off after the Anthropic IPO; the 5 picks are
AI/semiconductor names whose latest earnings (Oct 28-Nov 9) all raised
forecasts, so the drop is a market adjustment, not a company problem.
Structure (61s): title 6s, list 7s, stock cards 5 x 7s, summary 13s.
Crimson x charcoal cards, badge, driving A-minor BGM at 132 BPM
(BARGAIN_THEME). No posting; Hide publishes manually.
Usage:
  python3 src/bargain_main.py --file data/bargain_2026-11-20.json
"""
import argparse
import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))
import bargain_factcheck
import bargain_cards
import music

SEGMENTS = [6, 7, 7, 7, 7, 7, 7, 13]  # title, list, stocks x5, summary = 61s
LANDING_URL = ("https://muse.ai/s/tou-zi-da-hao-ki-shou-kemin-pezi-xop6xzxuxsng8w8/"
               "k3ru9cej7TKfxuaIdLAMDCxtN-lr54HyOVmqpbWFP2s")
VIDEO_NAME = "bargain-2026-11-20_tiktok_61s_v1.mp4"


def _fmt_yen(v):
    if float(v) == int(v):
        return "{:,}円".format(int(v))
    return "{:,}円".format(v)


def build_video(data, outdir):
    card_paths = bargain_cards.build_all_long(data, os.path.join(outdir, "cards"))
    bgm = music.make_bgm(os.path.join(outdir, "bgm.wav"), dur=61.0, **music.BARGAIN_THEME)
    video = os.path.join(outdir, VIDEO_NAME)
    inputs = "".join("[{0}:v]fps=30,format=yuv420p[v{0}];".format(i) for i in range(len(card_paths)))
    concat = "".join("[v{0}]".format(i) for i in range(len(card_paths)))
    fc = (inputs + concat + "concat=n={0}:v=1:a=0[v];".format(len(card_paths))
          + "[{0}:a]atrim=0:61,afade=t=out:st=59:d=2,".format(len(card_paths))
          + "aformat=sample_rates=44100:channel_layouts=stereo[a]")
    cmd = ["ffmpeg", "-nostdin", "-y", "-v", "error"]
    for path, dur in zip(card_paths, SEGMENTS):
        cmd += ["-loop", "1", "-t", str(dur), "-i", path]
    cmd += ["-i", bgm, "-filter_complex", fc, "-map", "[v]", "-map", "[a]",
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "22",
            "-c:a", "aac", "-b:a", "160k", "-t", "61", video]
    subprocess.run(cmd, check=True)
    dur = subprocess.check_output(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", video]).decode().strip()
    if not (61.0 <= float(dur) <= 63.0):
        raise RuntimeError("video duration {0}s is not 61s".format(dur))
    probe = os.path.join(outdir, "probe")
    os.makedirs(probe, exist_ok=True)
    for t in (3, 9, 16, 23, 30, 37, 44, 54):
        subprocess.run(["ffmpeg", "-nostdin", "-y", "-v", "error", "-ss", str(t),
                        "-i", video, "-frames:v", "1", "-q:v", "4",
                        os.path.join(probe, "frame_{0}s.jpg".format(t))], check=True)
    return video


def caption_for(data):
    m = data["market"]
    lines = []
    lines.append("【{0}】日経平均が1週間で{1}%・{2:,.0f}円安📉".format(
        data["title_label"], m["weekly_change_pct"], abs(m["weekly_change_yen"])))
    lines.append("米AI株安の波及でAI・半導体株が軒並み急落。でも紹介する5銘柄は、"
                 "10月末〜11月の決算でそろって好業績を示した銘柄ばかりです")
    for p in data["picks"]:
        lines.append("{0}位 {1} {2}%（{3}→{4}）".format(
            p["rank"], p["name"], p["weekly_change_pct"],
            _fmt_yen(p["prev_close"]), _fmt_yen(p["close"])))
    lines.append("※本動画は銘柄紹介であり投資推奨ではありません。"
                 "株価はさらに下落する場合があります")
    lines.append("#日本株 #半導体株 #AI株 #株 #投資初心者 #資産形成 #お金の勉強")
    return "\n".join(lines)


def youtube_title(data):
    m = data["market"]
    return "【{0}】日経平均が週間{1}%・{2:,.0f}円安｜AI株急落でも決算は好調な{3}銘柄".format(
        data["title_label"], m["weekly_change_pct"],
        abs(m["weekly_change_yen"]), len(data["picks"]))


def youtube_description(data):
    m = data["market"]
    parts = []
    parts.append("{0}、{1}は{2}から{3}へ、1週間で{4}%下落しました。{5}。"
                 "紹介する{6}銘柄は、いずれも10月末〜11月の決算で上方修正や好調な見通しを発表した銘柄で、"
                 "今週の下げは市場全体の調整によるものです。\n".format(
                     data["week_label"], m["index"], m["prev_close_label"],
                     m["close_label"], m["weekly_change_pct"], m["context"],
                     len(data["picks"])))
    for p in data["picks"]:
        parts.append(
            "■ {0}位 {1}（{2}・{3}）　週間 {4}%\n".format(
                p["rank"], p["name"], p["code"], p["market"], p["weekly_change_pct"])
            + "・株価：{0}（11/13終値）→ {1}（11/20終値）、100株で{2}\n".format(
                _fmt_yen(p["prev_close"]), _fmt_yen(p["close"]), p["min_investment_label"])
            + "・事業：{0}\n".format(p["business_line"])
            + "・下落の理由：{0}\n".format("／".join(p["reason_lines"]))
            + "・注意点：{0}\n".format("／".join(p["caution_lines"])))
    parts.append(
        "※株価はYahoo Finance（{0}終値）で確認。"
        "決算内容は各社の決算短信・開示資料で確認（{0}時点）。"
        "株価・業績は変わる場合があります\n".format(data["checked_date"])
        + "※本動画は銘柄紹介であり投資推奨ではありません\n\n"
        + "▼お役立ちリンク集（SNSまとめ）\n" + LANDING_URL + "\n"
        + "▼TikTok\nhttps://www.tiktok.com/@toushi_daisuki\n"
        + "▼Instagram\nhttps://www.instagram.com/toushi_daisuki_\n\n"
        + "#日本株 #半導体株 #AI株 #株 #投資初心者 #資産形成 #お金の勉強 #Shorts")
    return "\n".join(parts)


def instagram_caption(data):
    m = data["market"]
    lines = []
    lines.append("【{0}】\n".format(data["title_label"]))
    lines.append("日経平均が1週間で{0}%・{1:,.0f}円安になった今週📉\n".format(
        m["weekly_change_pct"], abs(m["weekly_change_yen"])))
    lines.append("米AI株安の波及で、AI・半導体株が軒並み下がりました。\n"
                 "でも紹介する5銘柄は、10月末〜11月の決算でそろって好業績を示した銘柄ばかり。\n"
                 "下げた理由と注意点をまとめました。\n")
    for p in data["picks"]:
        lines.append("{0}位 {1} {2}%".format(p["rank"], p["name"], p["weekly_change_pct"]))
    lines.append("\n※本動画は銘柄紹介であり投資推奨ではありません。"
                 "株価はさらに下落する場合があります\n")
    lines.append("#日本株 #半導体株 #AI株 #株 #投資初心者 #資産形成 #お金の勉強")
    return "\n".join(lines)


def publish_guide(data, caption):
    return (
        "【手動公開ガイド】{0}（61秒版・2026年11月20日作成）\n".format(data["title_label"])
        + "投稿予定：TikTok 金曜20:00（2026年11月20日）\n"
        + "\n■ TikTok\nキャプション（そのままコピーして貼り付け）\n" + caption + "\n"
        + "\n投稿設定\n"
        + "公開範囲: 全員に公開\n"
        + "カバー: 動画の先頭フレーム（タイトルカード）を選択\n"
        + "コメント: 許可する\n"
        + "Duet / Stitch: 許可する（拡散用）\n"
        + "AI生成コンテンツのラベル: オン（自動生成した動画のため）\n"
        + "音楽: 動画内のオリジナルBGMのまま（TikTok側の曲は追加しない）\n"
        + "\n■ YouTube Shorts（同じファイルで投稿可）\n"
        + "タイトル\n" + youtube_title(data) + "\n"
        + "\n説明文\n" + youtube_description(data) + "\n"
        + "\n設定: 視聴者層は「子ども向けではない」を選択／改変されたコンテンツ（AI生成）の開示をオン／公開\n"
        + "\n■ Instagramリール（同じファイルで投稿可）\n"
        + "キャプション\n" + instagram_caption(data) + "\n"
        + "\n設定: カバーは先頭フレーム（タイトルカード）／AIラベルをオン／フィードにもシェアをオン\n"
        + "\n■ 投稿前チェック\n"
        + "ファクトチェック済み（{0}時点）\n".format(data["checked_date"])
        + "出典: 各銘柄の決算短信・開示資料、Yahoo Finance（株価）、日本経済新聞（日経平均終値）、ロイター（市場全体の動き）\n"
        + "注意: 本動画は銘柄紹介であり投資推奨ではありません。株価はさらに下落する場合があります。\n"
        + "ソフトバンクグループ（9984）は11月10日の中間期決算で7,680億円の純損失を発表しており、"
        + "今週の下げに決算要因が含まれるため選定から外しました\n"
    )


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", default="data/bargain_2026-11-20.json")
    args = ap.parse_args()

    data_path = os.path.join(ROOT, args.file)
    with open(data_path, encoding="utf-8") as f:
        data = json.load(f)
    tag = os.path.basename(data_path)[len("bargain_"):-len(".json")]

    errors = bargain_factcheck.check(data)
    if errors:
        print("FACT-CHECK FAILED:")
        for e in errors:
            print(" -", e)
        return 1
    print("fact-check OK (bargain {0} picks, checked {1})".format(
        len(data["picks"]), data["checked_date"]))

    outdir = os.path.join(ROOT, "output", "bargain-{0}".format(tag))
    os.makedirs(outdir, exist_ok=True)
    video = build_video(data, outdir)
    caption = caption_for(data)
    package = {"series": "bargain", "tag": tag, "video": video,
               "caption": caption, "duration_sec": 61, "fact_check": "passed",
               "probe_frames": os.path.join(outdir, "probe")}
    print("video built: {0}".format(video))
    with open(os.path.join(outdir, "post_package.json"), "w", encoding="utf-8") as f:
        json.dump(package, f, ensure_ascii=False, indent=2)
    guide_path = os.path.join(outdir, "publish_guide.txt")
    with open(guide_path, "w", encoding="utf-8") as f:
        f.write(publish_guide(data, caption))
    print("publish guide: {0}".format(guide_path))
    return 0


if __name__ == "__main__":
    sys.exit(main())
