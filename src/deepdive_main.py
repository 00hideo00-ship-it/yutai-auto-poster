#!/usr/bin/env python3
"""61-second video for the weekly deep-dive series (1 stock).

First edition: Skylark HD (3197), angle (a) shareholder benefit.
Structure (61s): title 4s, basic info 6s, deep-dive cards 4 x 8s,
caution 8s, summary 11s. Dark navy x light blue cards, badge,
chill F-major BGM at 92 BPM (DEEPDIVE_THEME). No posting;
Hide publishes manually.
Usage:
  python3 src/deepdive_main.py --file data/deepdive_2026-11-17.json
"""
import argparse, json, os, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))
import deepdive_factcheck, deepdive_cards, music  # noqa: E402

SEGMENTS = [4, 6, 8, 8, 8, 8, 8, 11]  # title, basic, deep x4, caution, summary = 61s
LANDING_URL = ("https://muse.ai/s/tou-zi-da-hao-ki-shou-kemin-pezi-xop6xzxuxsng8w8/"
               "k3ru9cej7TKfxuaIdLAMDCxtN-lr54HyOVmqpbWFP2s")
VIDEO_NAME = "deepdive-skylark-3197_tiktok_61s_v1.mp4"


def build_video(data, outdir):
    card_paths = deepdive_cards.build_all_long(data, os.path.join(outdir, "cards"))
    bgm = music.make_bgm(os.path.join(outdir, "bgm.wav"), dur=61.0, **music.DEEPDIVE_THEME)
    video = os.path.join(outdir, VIDEO_NAME)
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


def caption_for(data):
    s = data["stock"]
    return (f"【{s['name']} 深掘り】100株で年4,000円分の食事券\n"
            f"ガスト・バーミヤン・しゃぶ葉などで使える電子チケット\n"
            f"2026年12月末分は条件なし／権利付き最終日は12月28日\n"
            f"2027年6月末分からは6か月以上の継続保有が必要に\n"
            f"配当は2026/12期27円へ増配予想（前期22円）\n"
            f"※本動画は銘柄紹介であり投資推奨ではありません。優待・配当は変更される場合があります\n"
            f"#株主優待 #すかいらーく #ガスト #高配当 #投資初心者")


def youtube_title(data):
    return ("【すかいらーくHD 深掘り】100株で年4,000円分の食事券｜"
            "2027年6月から優待条件が変わる注意点")


def youtube_description(data):
    s = data["stock"]
    tiers = "\n".join(
        f"・{t['shares']}：{t['per_half_yen']:,}円分×年2回＝年{t['annual_yen']:,}円分"
        for t in s["yutai"]["tiers"])
    hist = " → ".join(
        f"{h['fiscal']} {h['yen']}円" + ("（予想）" if h.get("forecast") else "")
        for h in s["dividend"]["history"])
    return (f"12月優待の筆頭銘柄、すかいらーくホールディングス（3197）を1銘柄だけ深掘りします。\n\n"
            f"■ 株主優待（電子チケット・年2回、基準日6月末・12月末）\n{tiers}\n"
            f"・使える店：{s['yutai']['brands']}、{s['yutai']['delivery']}\n\n"
            f"■ 配当の実績\n{hist}\n"
            f"・配当性向は{s['dividend']['payout_ratio_target']}が目安、2025/12期は{s['dividend']['payout_ratio_2025']}%\n"
            f"・予想配当利回り {s['dividend']['yield_pct']}%（{s['price_date_label']} {s['price_yen']:,}円ベース）\n\n"
            f"■ 優待＋配当（100株の場合）\n"
            f"・優待 年{s['total_return_100']['yutai_annual_yen']:,}円＋配当 年{s['total_return_100']['dividend_annual_yen']:,}円"
            f"＝年{s['total_return_100']['total_yen']:,}円、総合利回り約{s['total_return_100']['total_yield_pct']}%（{s['price_date_label']}）\n\n"
            f"■ 注意点：2027年6月末分から優待に「6か月以上の継続保有」が必要になります（2026年11月12日発表）。2026年12月末分は従来どおり条件なしで、権利付き最終日は12月28日です。長期保有でポイント付与率が上がる制度も2027年10月1日から始まる予定です。\n\n"
            f"■ 業績\n"
            f"・売上高 {s['performance']['sales_2025']}（2025/12期）→ {s['performance']['sales_2026_forecast']}（2026/12期予想）\n"
            f"・純利益 {s['performance']['net_income_2025']}（2025/12期）→ {s['performance']['net_income_2026_forecast']}（2026/12期予想）\n\n"
            f"※数値は会社開示・決算短信・配当ゴーで確認（{data['checked_date']}時点）。優待・配当は変更される場合があります\n"
            f"※本動画は銘柄紹介であり投資推奨ではありません\n\n"
            f"▼お役立ちリンク集（SNSまとめ）\n{LANDING_URL}\n"
            f"▼TikTok\nhttps://www.tiktok.com/@toushi_daisuki\n"
            f"▼Instagram\nhttps://www.instagram.com/toushi_daisuki_\n\n"
            f"#株主優待 #すかいらーく #ガスト #高配当 #投資初心者 #資産形成 #Shorts")


def instagram_caption(data):
    return (f"【すかいらーくHD 深掘り】100株で年4,000円分の食事券\n\n"
            f"ガスト・バーミヤン・しゃぶ葉などで使える電子チケットだよ。\n"
            f"2026年12月末分は条件なしで、権利付き最終日は12月28日。\n"
            f"でも2027年6月末分からは、6か月以上の継続保有が必要になるから注意してね。\n"
            f"配当も2026/12期は27円へ増配予想だよ\n\n"
            f"※本動画は銘柄紹介であり投資推奨ではありません。優待・配当は変更される場合があります\n\n"
            f"#株主優待 #すかいらーく #ガスト #高配当 #投資初心者 #資産形成 #お金の勉強")


def publish_guide(data, caption):
    s = data["stock"]
    return (f"【手動公開ガイド】{s['name']} 深掘り（61秒版・2026年11月17日作成）\n"
            f"投稿予定：TikTok 水曜20:00（2026年11月18日）\n"
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
            f"出典: 会社開示「株主優待制度の一部変更に関するお知らせ」（2026/11/12）、2026年12月期第3四半期決算短信（2026/11/12）、配当ゴー（2026/11/17終値）\n"
            f"注意: 2026年12月末分は従来どおり条件なし。2027年6月末分から6か月以上の継続保有が必要。優待・配当は変更される場合があります\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", default="data/deepdive_2026-11-17.json")
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
