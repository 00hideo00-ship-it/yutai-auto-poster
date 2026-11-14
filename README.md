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
3. Login KitのリダイレクトURIに `https://localhost:8080/callback` を登録し、同梱の認可ヘルパーでトークンを取得する:
   `python3 src/auth.py --client-key <key> --client-secret <secret>` を実行 → 表示されたURLをブラウザで開いて承認 →
   遷移先URLの `code=` の値を貼り付けると `.env` が自動で書かれる。
   アクセストークンは24時間で切れるため、本システムは毎回 refresh_token で自動更新する（更新のたびに refresh_token も新しいものに差し替わる点に注意）。
4. ローカルなら `.env`（`.env.example` をコピー）、GitHubなら Secrets に3点を登録。**チャットには貼らないこと。**

## 週次自動実行
`.github/workflows/weekly-yutai.yml` — 毎週月曜10:00 JSTに実行。
Secretsが無ければ動画生成のみ行い、成果物をArtifactsに保存する（投稿はされない）。
新しい対象月を出すときは、その月の `data/picks_YYYY-MM.json` を出典付きで追加する。

## 注意
- TikTokの仕様上、未審査アプリからの direct 投稿は非公開になる。まず draft で運用し、続けるなら審査申請を検討する。
- 動画内の数値・条件は picks データの確認日時点のもの。権利月が近づいたら再確認する。
- 本システムの動画は銘柄紹介であり、投資推奨ではない（免責は動画内とキャプションに入れてある）。
