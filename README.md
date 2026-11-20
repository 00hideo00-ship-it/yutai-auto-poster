# 優待株ショート動画 自動投稿システム

毎週、株主優待5選の30秒TikTok動画を自動生成し、TikTokへ送る仕組み。
構成は「データ（ファクトチェック済み）→ 生成 → 投稿」の3段で、途中に必ずファクトチェックゲートが入る。

## パイプライン
1. **選定データ** `data/picks_YYYY-MM.json` — 対象月の5銘柄。各銘柄に優待・ポイント・出典URL・確認日が必須。
   優待データの信頼できる無料APIは存在しないため、ここは出典付きで用意する（=人のファクトチェック工程）。
2. **ファクトチェックゲート** `src/factcheck.py` — 5銘柄ちょうど／証券コード4桁／出典https／確認日が45日以内／
   「継続保有が必要なのに今年対象」などの矛盾／曖昧・禁止表現（例:「今年OK」）を検出したら生成を止める。
3. **動画生成** `src/cards.py` + `src/music.py` — ポップデザインの3画面（一覧11秒→おすすめポイント10秒→まとめ9秒）、
   オリジナル合成BGM付き、720×1280・30秒。まとめ画面のチェックは「1行に1個」で生成されるため数がずれない。
   生成後に確認用フレーム（5秒/16秒/26秒）を `output/<月>/probe/` に出すので、必ず目視確認してから投稿する。
4. **投稿** `src/tiktok.py` — TikTok公式 Content Posting API。
   - `draft` モード（推奨・既定）: TikTokの受信トレイに動画が届き、最終公開はアプリで自分が行う。審査不要で始められる。
   - `direct` モード: プロフィールへ直接公開。ただし **TikTokのアプリ審査を通すまで投稿は非公開（SELF_ONLY）固定＋アカウント非公開が条件**。公開の自動投稿には審査申請が必要。

## ローカル実行
```bash
pip install -r requirements.txt   # Pillowのみ。ffmpegとNoto Sans CJKフォントが必要
python3 src/main.py               # 最新のpicksで生成のみ（output/<月>/に動画+投稿パッケージ）
python3 src/main.py --post --mode draft
```

## TikTok認証（Hide側の作業・初回のみ）
1. TikTokアカウントを作る（投稿用）。
2. [TikTok for Developers](https://developers.tiktok.com/) でアプリを作成し、製品に **Content Posting API** を追加、
   スコープ `video.upload`（directも使うなら `video.publish` も）を有効化。
3. Login KitのリダイレクトURIに `https://00hideo00-ship-it.github.io/yutai-auto-poster/callback.html` を登録し、同梱の認可ヘルパーでトークンを取得する:
   `python3 src/auth.py --client-key <key> --client-secret <secret>` を実行 → 表示されたURLをブラウザで開いて承認 →
   遷移先URLの `code=` の値を貼り付けると `.env` が自動で書かれる。
   アクセストークンは24時間で切れるため、本システムは毎回 refresh_token で自動更新する（更新のたびに refresh_token も新しいものに差し替わる点に注意）。
4. ローカルなら `.env`（`.env.example` をコピー）、GitHubなら Secrets に3点を登録。**チャットには貼らないこと。**

## 週次自動実行
`.github/workflows/weekly-yutai.yml` — 毎週月曜10:00 JSTに実行。
Secretsが無ければ動画生成のみ行い、成果物をArtifactsに保存する（投稿はされない）。
新しい対象月を出すときは、その月の `data/picks_YYYY-MM.json` を出典付きで追加する。

## 週次カレンダー動画「今週の権利確定日カレンダー」（月曜20:00投稿分）
- **パイプライン**: `data/calendar_YYYY-MM-DD.json`（対象週の月曜日の日付）→
  `src/calendar_factcheck.py`（ゲート：週内に権利日がある1〜5銘柄、来週の予告、価格×100=最低投資額）→
  `src/calendar_cards.py`（オレンジ×クリーム、「今週」バッジ）→
  `src/music.py` の `CALENDAR_THEME`（Gメジャー、約112BPM）→ 61秒動画
- **構成（61秒）**: タイトル 6秒 → 銘柄カード 各11秒 → 来週の予告 11秒 → まとめ 11秒
- **実行**: `python3 src/calendar_main.py --file data/calendar_2026-11-16.json`
- **成果物**: `output/calendar-<週>/video.mp4` + `publish_guide.txt` + `probe/`、
  ファクトチェックシートは `~/workspace/yutai-shorts/<週>_calendar/factcheck.md`
- 対象週に該当銘柄が少ない週は、翌週分の主なものを「来週の予告」として明示して含める。
  予告銘柄の株価は動画内に表示せず、翌週の動画で最新終値ベースに更新する。

## 週次動画「1銘柄の深掘り」（水曜20:00投稿分）
- **パイプライン**: `data/deepdive_YYYY-MM-DD.json`（1銘柄・優待(a)または配当(b)の切り口）→
  `src/deepdive_factcheck.py`（ゲート：株価×100=最低投資額、優待年額=半期×2、配当利回り・総合利回りの計算一致、配当推移、権利付き最終日、出典3件以上、6か月ローテーション）→
  `src/deepdive_cards.py`（ダークネイビー×ライトブルー、「深掘り」バッジ）→
  `src/music.py` の `DEEPDIVE_THEME`（Fメジャー、約92BPMのチルポップ）→ 61秒動画
- **構成（61秒）**: タイトル 4秒 → 基本情報 6秒 → 深掘りカード 4枚×8秒 → 注意点 8秒 → まとめ 11秒
- **選定**: 直近の月次5選（優待・配当株）の採用銘柄や主要な優待・配当銘柄からローテーション。
  履歴は `data/deepdive_history.json` に記録し、過去に取り上げた銘柄は原則6か月は繰り返さない。
- **実行**: `python3 src/deepdive_main.py --file data/deepdive_2026-11-17.json`
- **成果物**: `output/deepdive-<日>/deepdive-<銘柄>_<コード>_tiktok_61s_v1.mp4` + `publish_guide.txt` + `probe/`、
  ファクトチェックシートは `~/workspace/yutai-shorts/<日>_deepdive-<銘柄>/factcheck.md`
- **第1回（2026-11-17）**: すかいらーくHD（3197）、切り口(a)優待。2026年11月12日の優待制度変更（2027年6月末分から6か月以上の継続保有が必要）を注意点カードで扱う。

## 週次動画「今週の下げから狙い目5選」（金曜20:00投稿分）
- **パイプライン**: `data/bargain_YYYY-MM-DD.json`（対象週の金曜日の日付）→
  `src/bargain_factcheck.py`（ゲート：週間下落率の計算一致、5銘柄とも週間-5%以上、100株金額＝終値×100、出典2件以上／銘柄、推奨表現の禁止）→
  `src/bargain_cards.py`（クリムゾンレッド×チャコール、「狙い目」バッジ）→
  `src/music.py` の `BARGAIN_THEME`（Aマイナー、約132BPM）→ 61秒動画
- **構成（61秒）**: タイトル 6秒 → 一覧 7秒 → 銘柄カード 5枚×7秒 → まとめ 13秒
- **選定**: 前週金曜終値→今週金曜終値で週間-5%前後〜下落した流動性のある大型・中型株。不祥事・粉飾・構造的な業績悪化の銘柄は除外し、下落の主因をニュースで確認できたものだけ採用。5件に満たない週は件数を減らして正直に作る。
- **実行**: `python3 src/bargain_main.py --file data/bargain_2026-11-20.json`
- **成果物**: `output/bargain-<日>/bargain-<日>_tiktok_61s_v1.mp4` + `publish_guide.txt` + `probe/`、
  ファクトチェックシートは `~/workspace/yutai-shorts/<日>_bargain/factcheck.md`
- **第1回（2026-11-20）**: 日経平均が週間-7.7%の大幅安となった週。JX金属 -26.7%、イビデン -23.2%、アドバンテスト -20.8%、キオクシアHD -19.6%、東京エレクトロン -12.2%。5銘柄とも10月末〜11月の決算は好調で、下げは市場全体の調整によるもの。ソフトバンクGは11/10決算で7,680億円の純損失を発表しており決算要因が含まれるため選定から外した。

## 週次動画「5選ダイジェスト」（土曜10:00投稿分）
- **パイプライン**: 直近の月次5選（優待・毎月5日作成分と高配当・毎月15日作成分のうち新しい方）→ `src/digest_main.py`（factcheck ゲート＋detail ゲート）→ `src/digest_cards.py`（ダイジェスト専用タイトルカード＋元のシリーズのカードを流用）→ 元のシリーズの BGM → 61秒動画
- **構成（61秒）**: タイトル 6秒 → 一覧 7秒 → 銘柄カード 5枚×7秒 → まとめ 13秒。タイトルカードには「ダイジェスト」と冒頭フック（金額・期限の具体例）を入れる
- **実行**: `python3 src/digest_main.py --date 2026-11-21`（既定で最新月次版を自動選定、`--file` で指定も可）
- **成果物**: `output/digest-<日>/digest_tiktok_61s_v1.mp4` + `publish_guide.txt` + `probe/`、ファクトチェックシートは `~/workspace/yutai-shorts/<日>_digest/factcheck.md`
- **第1回（2026-11-21）**: 12月優待5選を題材に、優待シリーズの青ポップ設計＋YUTAI_THEME BGMで作成。現行パイプラインは優待版データ（detail_lines あり）専用で、高配当版が新しい週は未対応

## 注意
- TikTokの仕様上、未審査アプリからの direct 投稿は非公開になる。まず draft で運用し、続けるなら審査申請を検討する。
- 動画内の数値・条件は picks データの確認日時点のもの。権利月が近づいたら再確認する。
- 本システムの動画は銘柄紹介であり、投資推奨ではない（免責は動画内とキャプションに入れてある）。
