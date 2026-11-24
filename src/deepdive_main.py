#!/usr/bin/env python3
"""61-second video for the weekly deep-dive series (1 stock).

Editions: Skylark HD (3197, 2026-11-17, angle (a) benefit),
Hulic (3003, 2026-11-24, angle (b) dividend).
Structure (61s): title 4s, basic info 6s, deep-dive cards 4 x 8s,
caution 8s, summary 11s. Dark navy x light blue cards, badge,
chill F-major BGM at 92 BPM (DEEPDIVE_THEME). No posting;
Hide publishes manually.
Usage:
  python3 src/deepdive_main.py --file data/deepdive_2026-11-24.json
"""
import argparse, json, os, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))
import deepdive_factcheck, deepdive_cards, music  # noqa: E402

SEGMENTS = [4, 6, 8, 8, 8, 8, 8, 11]  # title, basic, deep x4, caution, summary = 61s
LANDING_URL = ("https://muse.ai/s/tou-zi-da-hao-ki-shou-kemin-pezi-xop6xzxuxsng8w8/"
               "k3ru9cej7TKfxuaIdLAMDCxtN-lr54HyOVmqpbWFP2s")
DISCLAIMER = "※本動画は銘柄紹介であり投資推奨ではありません。優待・配当は変更される場合があります"


def build_video(data, outdir):
    card_paths = deepdive_cards.build_all_long(data, os.path.join(outdir, "cards"))
    bgm = music.make_bgm(os.path.join(outdir, "bgm.wav"), dur=61.0, **music.DEEPDIVE_THEME)
    video = os.path.join(outdir, f"deepdive-{data['slug']}_tiktok_61s_v1.mp4")
    inputs = "".join(f"[{i}:v]fps=30,format=yuv420p[v{i}];" for i in range(len(card_paths)))
    concat = "".join(f"[v{i}]" for i in range(len(card_paths)))
    fc = (f"{inputs}{concat}concat=n={len(card_paths)}:v=1:a=0[v];"
          f"[{len(card_paths)}:a]atrim=0:61,afade=t=out:st=59:d=2,"
          "aformat=sample_rates=44100:channel_layouts=stereo[a]")
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
        raise RuntimeError(f"video duration {dur}s is not 61s")
    probe = os.path.join(outdir, "probe")
    os.makedirs(probe, exist_ok=True)
    for t in (2, 7, 14, 22, 30, 38, 46, 56):
        subprocess.run(["ffmpeg", "-nostdin", "-y", "-v", "error", "-ss", str(t),
                        "-i", video, "-frames:v", "1", "-q:v", "4",
                        os.path.join(probe, f"frame_{t}s.jpg")], check=True)
    return video


def _tier_line(t, yutai):
    if t.get("per_half_yen") is not None:
        return (f"・{t['shares']}：{t['per_half_yen']:,}円分×年2回"
                f"＝年{t['annual_yen']:,}円分")
    holding = f"（{t['holding']}）" if t.get("holding") else ""
    note = f"（{t['note']}）" if t.get("note") else ""
    desc = yutai.get("description", "")
    if "円相当" in desc:  # description already carries the amount
        return f"・{t['shares']}{holding}：{desc}{note}"
    return f"・{t['shares']}{holding}：{t['annual_yen']:,}円相当の{desc}{note}"


def caption_for(data):
    s = data["stock"]
    body = "\n".join(data["caption_lines"])
    return (f"【{s['name']} 深掘り】{data['caption_lead']}\n"
            f"{body}\n"
            f"{DISCLAIMER}\n"
            f"{data['hashtags_tiktok']}")


def youtube_title(data):
    return data["youtube_title"]


def youtube_description(data):
    s = data["stock"]
    tiers = "\n".join(_tier_line(t, s["yutai"]) for t in s["yutai"]["tiers"])
    hist = " → ".join(
        f"{h['fiscal']} {h['yen']}円" + ("（予想）" if h.get("forecast") else "")
        for h in s["dividend"]["history"])
    tr = s["total_return_100"]
    if tr["yutai_annual_yen"]:
        total_block = (f"・優待 年{tr['yutai_annual_yen']:,}円＋配当 年{tr['dividend_annual_yen']:,}円"
                       f"＝年{tr['total_yen']:,}円、総合利回り約{tr['total_yield_pct']}%"
                       f"（{s['price_date_label']}）")
    else:  # no benefit at 100 shares: say so instead of "優待 年0円"
        total_block = (f"・配当 年{tr['dividend_annual_yen']:,}円のみ（100株では優待なし）"
                       f"＝年{tr['total_yen']:,}円、総合利回り約{tr['total_yield_pct']}%"
                       f"（{s['price_date_label']}）")
    trt = s.get("total_return_yutai_tier")
    if trt:
        total_block += (f"\n・{trt['shares']}株の場合：優待 年{trt['yutai_annual_yen']:,}円"
                        f"＋配当 年{trt['dividend_annual_yen']:,}円"
                        f"＝年{trt['total_yen']:,}円、総合利回り約{trt['total_yield_pct']}%"
                        f"（{trt['investment_yen']:,}円投資・{s['yutai'].get('holding_years', '')}年以上保有で優待対象）")
    yutai_note = ""
    if s["yutai"].get("min_shares", 100) > 100:
        yutai_note = (f"\n・100株では優待の対象外です（{s['yutai']['min_shares']}株以上・"
                      f"{s['yutai']['holding_years']}年以上の継続保有が条件）")
    return (f"{s['name']}（{s['code']}）を1銘柄だけ深掘りします。\n\n"
            f"■ 株主優待（基準日{s['yutai']['record_dates']}）\n{tiers}{yutai_note}\n\n"
            f"■ 配当の実績\n{hist}\n"
            f"・配当性向の目標は{s['dividend']['payout_ratio_target']}、2025/12期は{s['dividend']['payout_ratio_2025']}%\n"
            f"・予想配当利回り {s['dividend']['yield_pct']}%（{s['price_date_label']} {s['price_yen']:,}円ベース）\n\n"
            f"■ 優待＋配当\n{total_block}\n\n"
            f"■ 注意点：{data['caution_note']}\n\n"
            f"■ 業績\n"
            f"・売上高 {s['performance']['sales_2025']}（2025/12期）→ {s['performance']['sales_2026_forecast']}（2026/12期予想）\n"
            f"・純利益 {s['performance']['net_income_2025']}（2025/12期）→ {s['performance']['net_income_2026_forecast']}（2026/12期予想）\n\n"
            f"※数値は会社開示・決算短信・配当ゴーで確認（{data['checked_date']}時点）。優待・配当は変更される場合があります\n"
            f"{DISCLAIMER}\n\n"
            f"▼お役立ちリンク集（SNSまとめ）\n{LANDING_URL}\n"
            f"▼TikTok\nhttps://www.tiktok.com/@toushi_daisuki\n"
            f"▼Instagram\nhttps://www.instagram.com/toushi_daisuki_\n\n"
            f"#株主優待 #ヒューリック #高配当 #配当株 #投資初心者 #資産形成 #Shorts")


def instagram_caption(data):
    s = data["stock"]
    body = "\n".join(data["instagram_lines"])
    return (f"【{s['name']} 深掘り】{data['caption_lead']}\n\n"
            f"{body}\n\n"
            f"{DISCLAIMER}\n\n"
            f"{data['hashtags_instagram']}")


def publish_guide(data, caption):
    s = data["stock"]
    sources = "、".join(src["label"] for src in data["sources"])
    return (f"【手動公開ガイド】{s['name']} 深掘り（61秒版・{data['created_date_label']}作成）\n"
            f"投稿予定：TikTok 水曜20:00（{data['post_date_label']}）\n"
            f"\n■ TikTok\nキャプション（そのままコピーして貼り付け）\n{caption}\n"
            f"\n投稿設定\n"
            f"公開範囲: 全員に公開\n"
            f"カバー: 動画の先頭フレーム（タイトルカード）を選択\n"
            f"コメント: 許可する\n"
            f"Duet / Stitch: 許可する（拡散用）\n"
            f"AI生成コンテンツのラベル: オン（自動生成した動画のため）\n"
            f"音楽: 動画内のオリジナルBGMのまま（TikTok側の曲は追加しない）\n"
            f"\n■ YouTube Shorts（同じファイルで投稿可）\n"
            f"タイトル\n{youtube_title(data)}\n"
            f"\n説明文\n{youtube_description(data)}\n"
            f"\n設定: 視聴者層は「子ども向けではない」を選択／改変されたコンテンツ（AI生成）の開示をオン／公開\n"
            f"\n■ Instagramリール（同じファイルで投稿可）\n"
            f"キャプション\n{instagram_caption(data)}\n"
            f"\n設定: カバーは先頭フレーム（タイトルカード）／AIラベルをオン／フィードにもシェアをオン\n"
            f"\n■ 投稿前チェック\n"
            f"ファクトチェック済み（{data['checked_date']}時点）\n"
            f"出典: {sources}\n"
            f"注意: {data['caution_note']}優待・配当は変更される場合があります\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", default="data/deepdive_2026-11-24.json")
    args = ap.parse_args()

    data_path = os.path.join(ROOT, args.file)
    with open(data_path, encoding="utf-8") as f:
        data = json.load(f)
    tag = os.path.basename(data_path)[len("deepdive_"):-len(".json")]

    errors = deepdive_factcheck.check(data)
    if errors:
        print("FACT-CHECK FAILED:")
        for e in errors:
            print(" -", e)
        return 1
    s = data["stock"]
    print(f"fact-check OK (deepdive {s['name']} {s['code']}, checked {data['checked_date']})")

    outdir = os.path.join(ROOT, "output", f"deepdive-{tag}")
    os.makedirs(outdir, exist_ok=True)
    video = build_video(data, outdir)
    caption = caption_for(data)
    package = {"series": "deepdive", "tag": tag, "video": video,
               "caption": caption, "duration_sec": 61, "fact_check": "passed",
               "probe_frames": os.path.join(outdir, "probe")}
    print(f"video built: {video}")
    with open(os.path.join(outdir, "post_package.json"), "w", encoding="utf-8") as f:
        json.dump(package, f, ensure_ascii=False, indent=2)
    guide_path = os.path.join(outdir, "publish_guide.txt")
    with open(guide_path, "w", encoding="utf-8") as f:
        f.write(publish_guide(data, caption))
    print(f"publish guide: {guide_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
