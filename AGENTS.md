# AGENTS.md ― AI漫画制作ワークフロー指示書

このファイルは **Codex（AIアシスタント）への指示書**です。受講者はこのフォルダを開いて、
やりたいことを日本語で頼むだけで、Codex がここに書かれた手順に従って Step0〜8 を進めます。

> 受講者へ：このファイルの中身は読まなくてOKです。「Step0をやりたい」「企画を考えたい」のように
> 普通の言葉で頼んでください。Codex が必要なステップを判断して進めます。

---

## 0. 全体の流れ（Step0〜8）

| Step | やること | 入力 | 出力（保存先） |
|------|----------|------|----------------|
| 0 企画立案 | テーマ・構成・キャラの設計図を対話で作る | 受講者の経験・発想 | `step0_企画/[作品名]_step0_planning.md` |
| 1 構成最適化 | 章構成を「売れる目次」に整える | Step0 | `step1_構成最適化/[作品名]_step1_outline.md` |
| 2 脚本 | 各章のシーン・セリフ・ト書きを作る | Step0,1 | `step2_脚本/[作品名]_step2_script.md` |
| 3 設定資料＋参照画像 | キャラ/ロケ詳細・名簿・参照画像を作る | Step0〜2 | `step3_設定資料/[作品名]_step3_settings.md` ＋ `step3_設定資料/*_sheets/` ＋ 名簿2つ |
| 4 ページ設計 | 章をページ単位の設計図に分解 | Step2,3 | `step4_ページ設計/第○章_〇〇/...md` |
| 5 コマ構成 | ページをコマ単位に割り、演出とセリフを設計 | Step2,3,4 | `step5_コマ構成/第○章_〇〇/...md` |
| 6 YAML生成 | コマ構成を構造化YAMLプロンプトに変換 | Step5＋名簿 | `step6_yaml生成/第○章_〇〇/..._ch○_p○○-○○.yaml` |
| 7 画像生成 | `image_gen` で全ページを生成・保存 | Step6 YAML＋名簿＋参照画像 | `step7_完成画像/第○章_〇〇/ch○_p○○_1000x1414.png` |
| 8 表紙作成 | タイトル・帯コピーを固め、`image_gen` で文字入り版・文字なし版の表紙を生成 | Step0（タイトル）＋Step3（参照画像・art_style） | `step8_表紙/[作品名]_step8_cover_prompt.md` ＋ `step8_表紙/[作品名]_cover_with_text.png` ＋ `step8_表紙/[作品名]_cover_no_text.png` |

**Stepは必ず Step0→1→2→…→8 の順に進めます。前提となる Step の成果物ファイルが揃っていない場合、
そのStepには絶対に進まないでください。** 受講者が「Step3をやりたい」のように先のStepを指定してきても、
まず入力欄（上表「入力」列）に挙がっている前提ファイルの存在を確認し、無いものがあれば：

1. どのStepの成果物が足りないかを具体的に伝える（例:「Step2の脚本 `step2_脚本/[作品名]_step2_script.md` がまだ無いので、Step3には進めません」）。
2. 先にそのStepをやるか尋ねる（「Step2から始めますか？」）。「はい」と言われたら、指定された先のStepではなく**足りないStepから**着手する。
3. 確認だけ取って先のStepに進む、という運用はしない。受講者が「前提が無くてもいいから先に進めて」と明示的に指示した場合のみ例外とし、
   その場合も「前のStepの成果物が無い状態で進めています」と明示してから進める。

---

## 1. 全体ルール（全Step共通）

- **対話と出力は必ず日本語**で行う。
- **段階的に進める**。一度に大量の質問をせず、要所で受講者に選択・確認を求める。
- **作品タイトル**は Step0 で（仮でも）決め、`config.yaml` の `project_name` と各ファイル名に使う。
- **絵柄スタイル**は `config.yaml` の `art_style` を土台にする（作品ごとに違う）。
- **`config.yaml` は受講者に手編集させず、Codex がステップの中で自動更新する**。
  タイトルと章構成は Step0 末尾、絵柄は Step3 で書き込む（→ 各Step詳細）。書き込み前に必ず内容を提示し、確認を取ってから保存する。
- **画像生成は `image_gen` に一本化**する。外部ツールは使わない。
- **スクリプトは Codex が必要時に実行**する。受講者にターミナルや Python 環境構築を要求しない。
  受講者がコマンドを打つ必要はない（`scripts/` の中身は触らせない）。
- **キャラ・場所の対応表はコードに書かない**。すべて `characters.yaml` / `locations.yaml`（名簿）で管理する（→ §3, §4）。
- 固有名詞（キャラ名・地名）は作品ごとに変わる。本書の例は**あくまで例**として扱い、
  実際の値は `config.yaml` と名簿、各 Step の成果物から読む。

---

## 2. 名簿の使い方（Step3で作り、Step6・7で使う）

`characters.yaml` / `locations.yaml` は「この名前が出てきたら、この参照画像を使う」という対応表（名簿）。

- **キャラ・場所の判定はこの名簿を唯一の根拠にする**。AGENTS.md やスクリプトに名前のリストを埋め込まない。
- 各エントリは `key`（内部キー）/ `name`（正式名）/ `aliases`（表記ゆれ）/ `sheets`（参照画像パス）を持つ。
- 服装や季節が場面で変わる場合のみ `variants`（`when_tone` / `when_location` ＋ `sheets`）を使う。
  どの variant を使うかは、ページの `emotional_tone` やロケーションを見て **Codex が判断**する。
- 名簿に**未登録の名前**がコマ構成に出てきたら、勝手に進めず受講者に知らせ、名簿へ追加するか確認する。

---

## 3. 各ステップの詳細手順

### Step 0 ― 企画立案（プロ編集者として）
プロの漫画編集者として、受講者を導きながら「売れるテーマ」と「設計図」を完成させる。

1. **経験の棚卸し**：まず3つだけ質問する ―
   ①大変だった経験は？ ②それをどう乗り越えた？ ③人に教えられることは？
2. 以降は Codex が案を出し、受講者に選択・確認してもらう形で進める：
   仮テーマ3案 → 読者の悩み → 学べること → 手にする未来 → テーマ確定 → 妥当性チェック（市場需要・物語の深さを⭐評価）。
3. **ページ数とストーリー型**を決める（110ページを推奨提示）。型は4つから選ばせ、特徴・配分例を示す：
   起承転結（推奨, 2:3:3:2）／三幕構成／問題解決型／ヒーローズ・ジャーニー。
4. 型に沿って **章構成** と **主要キャラ案** を作る。
5. 最後に企画完成版（テーマ／悩み／学び／未来／章構成／キャラ／まとめ）を出力し、
   **`step0_企画/[作品名]_step0_planning.md`** に保存するよう案内する（`step0_企画/` フォルダが無ければ作る）。
6. **`config.yaml` を自動更新**する：確定した作品タイトルを `project_name` に、確定した章構成を `chapters` の各 `name` に書き込む
   （`key` は `ch1, ch2 …` のまま。章数が変わったら項目を増減する）。書き込む前に更新後の内容を提示し、
   **受講者の確認を取ってから保存**する。受講者に手編集は求めない。`art_style` はここでは触らず Step3 で確定させる。

### Step 1 ― 構成最適化
企画書 `step0_企画/[作品名]_step0_planning.md` を読み、章構成を「売れる目次」に磨く。

1. テーマ・ストーリー型・総ページ数・章構成を抽出。
2. ページ配分をチェック（起承転結なら 起20-25% / 承25-30% / 転30-35% / 結15-20%）。長短やクライマックス不足を補正。
3. 感情の流れ（共感→危機→逆転→希望）を最適化。
4. 各章末に「引き（クリフハンガー）」を作る。
5. **そのまま表計算に貼れる形**の完成版目次を出力し、**`step1_構成最適化/[作品名]_step1_outline.md`** で保存案内。

### Step 2 ― 脚本
`step0_企画/[作品名]_step0_planning.md` と `step1_構成最適化/[作品名]_step1_outline.md` を読み、各章のストーリー脚本を作る。

- **絵として描けること（視覚情報）中心**に書く。小説的な長い心理描写はしない。
- **セリフは30文字以内・小学生でも分かる言葉**。
- 各章に 読者の「悩み・学び・未来」 を自然に織り込む。
- 章ごとに シーン構成 → ト書き → セリフ配置 → 章末の引き を作る。
- **`step2_脚本/[作品名]_step2_script.md`** で保存案内。

### Step 3 ― 設定資料＋参照画像（名簿のもと）
`step0_企画/` `step1_構成最適化/` `step2_脚本/` の成果物を読み、漫画制作に必要な詳細設定と参照画像、そして**名簿**を作る。

1. **キャラクター設定**：基本情報・外見・性格内面・背景・服装パターン・小物まで超詳細に。
2. **ロケーション設定**：主要な場所の基本情報・構成・象徴演出・カメラワーク・動線。
3. **世界観設定**：時代/社会背景・業界ルール・心理演出ルール・物語上の絶対ルール。
4. **色彩・ライティング設定**：ベースカラー・感情別カラー・キャラ配色・時間帯ライティング（カラーコード付き）。
5. **禁止事項（NG設定）**：壊してはいけない描写・テーマ逸脱防止・表現上の配慮。
6. 以上を **`step3_設定資料/[作品名]_step3_settings.md`** に保存案内。
   あわせて **`config.yaml` の `art_style` を自動更新**する：ここで確定した作風・色彩を、画像生成プロンプトの土台になる
   **英語表現**（例: `"japanese shoujo manga style, delicate lines, soft expressions, full color"`）に書き換える。
   書き込む前に内容を提示し、**受講者の確認を取ってから保存**する。以降の Step6・7 はこの `art_style` を土台に使う。
7. **参照画像を `image_gen` で生成**する（→ §4 の手順）。キャラシートは「白背景・全身/表情のリファレンスシート」、
   ロケーションは「No characters の背景イラスト」。生成物を `step3_設定資料/character_sheets/` `step3_設定資料/location_sheets/` に保存。
8. **名簿に登録**：作ったキャラ/場所を `characters.yaml` / `locations.yaml` に
   `name`・`aliases`（脚本に出る表記ゆれを全部）・`sheets`（保存した画像パス）で書き込む。

### Step 4 ― ページ設計
`step2_脚本/[作品名]_step2_script.md` と `step3_設定資料/[作品名]_step3_settings.md` を読み、指定された章の全ページを1枚ずつ設計する。

- **ストーリーは変えない／セリフはまだ作らない**（設計方針のみ）。
- 各ページに：ページ番号（例 1章-1）・章名・シーン概要・登場キャラ・ページの役割・ページの引き・このページで伝えたいこと。
- 1章25〜30ページ想定。章ごとに **`step4_ページ設計/第○章_〇〇/[作品名]_step4_pagedesign_ch○.md`** に保存案内。

### Step 5 ― コマ構成（ネーム）
`step3_設定資料/[作品名]_step3_settings.md`・`step2_脚本/[作品名]_step2_script.md`・該当章の Step4 設計書を読み、ページをコマ単位に割る。

- 1ページ通常 **2〜4コマ**。毎ページを同じコマ数に固定せず、ページの役割に合わせて緩急をつける。
  - **2コマ**: 感情の山場、重要な決断、沈黙、失敗の痛み、達成の余韻など、読者に間を味わわせたいページ。
  - **3コマ**: 通常の会話・行動・理解の前進。迷ったら3コマを基本にする。
  - **4コマ**: 手順説明、比較、情報量が多い画面、短い会話の往復など、テンポよく見せたいページ。
  - **大ゴマ**: 章冒頭、章末の引き、気づき、落選通知、初受注、完成・未来提示などは、最初か最後のコマを大きく使う。
  - 見開きや特殊演出は作らず、1ページ内で「大きいコマ＋小さいコマ」の差をつける。
- 各コマに：状況・登場キャラ・セリフ・カメラアングル・表情・背景・小物・演出。大ゴマにするコマは演出欄に「大ゴマ」「縦長大ゴマ」「余白を広く取る」などと明記する。
- **セリフ7原則を厳守**：①30字以内 ②モノローグは1ページ1回まで ③会話で進める ④簡単な言葉
  ⑤難しい説明はしない ⑥三点リーダー（…）禁止 ⑦句読点（。、）禁止。
- ページ最終コマが Step4 の「引き」と一致するか確認。
- **5ページごとに**保存と確認をはさみ、直近の流れを3行で要約して次へ。
- 装飾付き「コマ構成表」フォーマットで出力し、**`step5_コマ構成/第○章_〇〇/[作品名]_step5_paneldirection_ch○.md`** に保存案内。

### Step 6 ― YAML自動生成
該当章の Step5 コマ構成表を読み、画像生成用の**構造化YAML**を作る。

- **Step5の全項目を一字一句そのままYAMLへ転記**（要約・意訳・省略禁止）。マッピング：
  コマ番号→`panel_number`／状況→`scene_description`／登場キャラ→`characters_in_panel.name`／
  セリフ→`dialogues`／カメラ→`camera_angle`・`shot_type`／表情→`expression`／背景→`location`・`background_details`／
  小物演出→`props`・`effects`・`sound_effects`。
- 各コマに **英語の画像生成プロンプト** `gpt_image_prompt` を構築。先頭/末尾に `config.yaml` の `art_style` を入れ、
  末尾に `", 1000:1414 portrait manga page aspect ratio, full bleed manga page, no white borders, no side margins, no letterboxes"` を付ける。
  - **キャラの外見は名簿（およびStep3設定）を根拠に固定**。人物の見た目を毎コマ同一に保つ。
- 各ページに `page_context`（`prev_page_summary` / `this_page_role` / `next_page_lead` / `emotional_tone` / `lighting_continuity`）を必ず設定。
- **`page_number` は章内の通し番号を表すプレーンな整数**（例: `1`、`2`、`3`…）にする。`"1章-1"` のような章名込みラベルや文字列にしない（後続の `prepare_pages.py` が数値として読むため）。
- Step5で決めた**コマ数・大ゴマ指定・演出の強弱は変えない**。大ゴマ指定があるページは、該当コマの `effects` と `gpt_image_prompt` にそのまま入れ、画像生成時に面積差が出るようにする。
- **暴走防止**：`grid_cols: 1`、`grid_rows`＝コマ数に一致。`negative_prompt` に最低 `extra panels, english text, english sound effects` を含め、
  モノローグが無いページは `thought bubbles` も追加。
- **5ページずつ**バッチ生成し、各バッチ後に保存・進捗報告。
- **`step6_yaml生成/第○章_〇〇/[作品名]_step6_ch○_p○○-○○.yaml`** に保存（章フォルダ単位・5ページ刻み）。

### Step 7 ― 画像生成（`image_gen`）
Step6 のYAMLから、指定ページの漫画ページ画像を生成する。

1. 対象YAMLと対象ページを決める（「P1〜3」「このYAMLのP12」など）。
2. **下ごしらえスクリプトを Codex が実行**し、参照画像候補と保存先を得る：
   ```bash
   python3 scripts/prepare_pages.py "step6_yaml生成/第1章_〇〇/[作品名]_step6_ch1_p01-05.yaml" p01-03
   ```
   出力の `references.characters` / `references.locations` を `view_image` で確認する。
   （`references` が空配列の名前は名簿未登録 → 先に Step3 で登録）
3. 確認した参照シートの**視覚特徴を最優先**でプロンプトに反映する。
   YAMLの記述と参照画像が食い違う場合は**参照画像を優先**（年齢・髪型・服装はシートに揃える）。
4. **1ページ1枚**で `image_gen` を実行（コマ単位ではない）。`grid_rows` 個のコマを縦1列に積む。
   Step5/6で大ゴマ指定がある場合は「final panel is a large dramatic panel」「first panel is a tall establishing panel」のように、どのコマを大きくするかを英語で明示する。
   含める：用途=ストーリー挿絵 / フルカラー漫画ページ / 比率 `1000:1414` / コマ数固定 / 参照シートの特徴 /
   `style_prompt`・`negative_prompt` / 各コマの状況・構図・表情・背景・小物 / 指定セリフと擬音のみ。
   禁止：余分なコマ・英語テキスト・破綻した人体・縦長/横伸び。日本語は縦書き指定。
5. 生成画像のサイズを確認し、自然な比率（例 1055×1491、約1.414）なら `1000×1414` に縮小保存。
   細長い（例 862×1825）場合は強制変形せず、比率を強く指定して**再生成**する。
   ```bash
   sips -z 1414 1000 "$src" --out "$dst"
   sips -g pixelWidth -g pixelHeight "$dst"
   ```
6. **`step7_完成画像/第○章_〇〇/ch○_p○○_1000x1414.png`** に保存。作り直しは `..._v2_...` で別名保存（明示時のみ上書き）。
7. 画像内の日本語は揺らぐことがある。納品品質が必要なら「写植は後工程で差し替え」と伝える。
8. 完了報告：作成ページ・保存パス・確認済みサイズ・参照した主なシート・日本語揺らぎの注意。

### Step 8 ― 表紙作成（`image_gen`）
表紙は本の顔であり売れ行きを左右する最重要パーツ。プロへの外注も選択肢だが、`image_gen` でも制作できる。
`step0_企画/[作品名]_step0_planning.md`・`step3_設定資料/[作品名]_step3_settings.md`・主人公のキャラシート・名簿（`characters.yaml`）・`config.yaml` の `art_style` を読み、対話でタイトル周りの文言を固めてから生成する。

1. **情報収集（対話・確認しながら埋める）**：以下をStep0/1の企画内容から提案し、受講者に確認・微調整してもらう。
   - `TITLE` / `SUBTITLE`（タイトル・サブタイトル。`config.yaml` の `project_name` を土台にする）
   - `OBI_CATCH`（帯の大見出し・フック一文）／`OBI_BODY`（帯本文・作品の要約訴求）／`OBI_FOOTER`（帯下部の小さい訴求文）
   - `AUTHOR_NAME`（著者名。未定なら仮名やペンネームでも可）
   - `TOP_BADGE`（左上の吹き出しバッジ文言。「マンガでわかる」等・任意、不要なら省略）
   - `BADGE_COLOR`（バッジの色。黒固定にせず、作品テーマに合うアクセントカラーのHEX。帯色と完全一致させる必要はない）
   - `OBI_COLOR`（帯の色。作品のテーマカラーに合わせたHEX）
2. **表紙の主役キャラを1人選ぶ**（通常は主人公）。`characters.yaml` からそのキャラの `sheets` を1枚選び、`view_image` で内容を確認する。
   このシートを参照画像として使う：`CHAR_NAME` / `CHAR_APPEARANCE`（髪型・顔立ち）/ `CHAR_OUTFIT`（服装）は、名簿とStep3設定資料の記述をそのまま使う（新規に作らない）。
3. **表紙のシーンを対話で決める**：`SCENE_LOCATION`（舞台）・`SCENE_POSE`（ポーズ・カメラ目線）・`SCENE_MOOD`（表情・雰囲気）・`CHAR_EMOTION_ARC`（込める感情・変化）・`BACKGROUND`（背景描写）。
   Step0の企画（テーマ・悩み・学び・未来）とStep3の世界観設定に沿った、作品を象徴するワンシーンを提案する。
4. **生成方式は最初から2種類作る**：
   - **文字入り完成版**：タイトル・帯文字までまとめて`image_gen`で生成。すぐ確認できる完成イメージとして使う。ただし日本語文字が崩れることがある。
   - **文字なし安全版**：イラストと帯の色面だけ生成し、文字は空けておく。日本語文字崩れを避けたい最終入稿・Canva等での後入れ用として使う。
   受講者にどちらかを選ばせず、必ず両方を生成する。時間や生成回数を節約したいと受講者が明示した場合のみ、希望する片方だけにしてよい。
5. 文字入り完成版プロンプトと文字なし安全版プロンプトを、埋めた項目でそれぞれ組み立てて `image_gen` を2回実行する（`ART_STYLE` は `config.yaml` の `art_style` をそのまま使う）。どちらも縦長 **3:4** 比率を指定する。

   **文字入り完成版プロンプト**：
   ```
   Design a complete professional Japanese manga book cover, vertical 3:4 format.

   Use the attached character reference image for {CHAR_NAME}'s face, hairstyle,
   body proportions, clothing, and overall atmosphere. Keep them recognizable:
   {CHAR_APPEARANCE}, delicate features, consistent build with the reference.

   ━━ ILLUSTRATION (upper 60%) ━━
   {CHAR_NAME} is at {SCENE_LOCATION}. {SCENE_POSE}.
   They wear the same outfit as the reference image: {CHAR_OUTFIT}.
   Their expression should convey {SCENE_MOOD}. {CHAR_EMOTION_ARC}
   Background: {BACKGROUND}.
   Backlight and rim light matching the scene mood.

   ━━ TOP BADGE (top-left corner, optional) ━━
   A small {BADGE_COLOR} theme-color rounded-rectangle badge (speech-bubble style, with a small
   tail pointing down-left), placed in the top-left corner, overlapping
   slightly onto the illustration. Bold white Japanese text reading exactly:
   「{TOP_BADGE}」（{TOP_BADGE}が無ければこのセクションは省略）

   ━━ TITLE TEXT (left side, vertical layout) ━━
   Large bold vertical Japanese title text reading exactly:「{TITLE}」
   Written vertically top to bottom along the LEFT side.
   Bold serif (明朝体), white with subtle dark outline.
   Below it, smaller vertical text:「{SUBTITLE}」

   ━━ OBI BAND (bottom 38%) ━━
   A solid {OBI_COLOR} rectangular band across the full bottom.
   Top of band, large bold white text: {OBI_CATCH}
   Middle, smaller white body text: {OBI_BODY}
   Bottom right corner, small white italic text: {OBI_FOOTER}

   ━━ AUTHOR (top right, small) ━━
   Small vertical Japanese text top-right corner:「{AUTHOR_NAME}」

   ━━ STYLE ━━
   {ART_STYLE}, clean professional book cover design, publishing quality.
   No speech bubbles, no manga panels.
   ```

   **文字なし安全版プロンプト**（Canvaで文字を後入れする場合）：
   ```
   Create a professional Japanese manga book cover illustration, vertical 3:4 format,
   with clean empty areas reserved for later typography.

   Use the attached character reference image for {CHAR_NAME}'s face, hairstyle,
   body proportions, clothing, and overall atmosphere. Keep them recognizable:
   {CHAR_APPEARANCE}, delicate features, consistent build with the reference.

   Upper 60%: {CHAR_NAME} is at {SCENE_LOCATION}, wearing the same outfit as
   the reference image: {CHAR_OUTFIT}. {SCENE_POSE}. Their expression should
   convey {SCENE_MOOD}. {CHAR_EMOTION_ARC}
   Background: {BACKGROUND}, backlight matching the scene mood.

   Leave clear negative space on the left side of the illustration for a
   vertical Japanese title. Do not place text in this area.

   Top-left corner (optional): a small {BADGE_COLOR} theme-color rounded-rectangle speech-bubble-style
   badge (with a small tail pointing down-left), left completely blank inside.

   Bottom 38%: a solid {OBI_COLOR} rectangular obi band across the full bottom,
   left completely blank for later text placement.

   Top right: leave a small blank area for a vertical author name.

   Style: {ART_STYLE}, clean professional book cover composition, publishing
   quality. No text, no letters, no speech bubbles, no manga panels, no logo,
   no watermark.
   ```

   文字なし安全版用に、以下のテキスト一覧をあわせて提示し、Canva等での配置を案内する：
   バッジ（左上・任意）＝`TOP_BADGE` ／ バッジ色＝`BADGE_COLOR` ／ タイトル（縦・左）＝`TITLE` ／ サブタイトル＝`SUBTITLE` ／
   帯キャッチ（大）＝`OBI_CATCH` ／ 帯本文＝`OBI_BODY` ／ 帯下部（小）＝`OBI_FOOTER` ／ 著者名（右上）＝`AUTHOR_NAME`。
6. 埋めた項目・文字入り完成版プロンプト・文字なし安全版プロンプト・Canva等での文字配置一覧を **`step8_表紙/[作品名]_step8_cover_prompt.md`** に保存案内する。
7. 生成画像を以下の名前で保存案内する。作り直しは `..._v2_...` で別名保存（明示時のみ上書き）。
   - 文字入り完成版：**`step8_表紙/[作品名]_cover_with_text.png`**
   - 文字なし安全版：**`step8_表紙/[作品名]_cover_no_text.png`**
8. 完了報告：使用した参照シート・生成方式（文字入り完成版＋文字なし安全版）・両方の保存パス・Canva等での文字配置一覧・日本語文字崩れがある場合の注意。

---

## 4. 参照画像の作り方（`image_gen`・Step3で使用）

参照画像（キャラシート・ロケーションシート）はすべて `image_gen` で作り、`step3_設定資料/` 配下に保存する。

**キャラクターシート**：白背景・フルカラー・portrait（2:3）。3列×4行グリッド（顔アップ各種＋全身正面/側面/背面）。
Row1以外に文字を入れない。髪型・目・服装を全コマ統一。服装等にカラーコードを含める。

**ロケーションシート**：`No characters.` を必ず入れる。主人公キャラシートを「視覚スタイルの基準」として参照させる。
床・壁・照明にカラーコード、Step3で決めたカメラワークを構図に反映。同じ場所でも章で光が変わるならバージョンを分ける。

保存先：`step3_設定資料/character_sheets/` と `step3_設定資料/location_sheets/`。
保存したパスを名簿（`characters.yaml` / `locations.yaml`）の `sheets:` に登録する。

---

## 5. フォルダ構成（このテンプレート）

ルート直下に置くのは**設定ファイル5個だけ**。生成物はすべて番号付きフォルダ（読む順）に入れる。

```
作品フォルダ/
├── AGENTS.md            ← この指示書（受講者は読まなくてよい）
├── README.md            ← 受講者向けの最初の道案内
├── config.yaml          ← 作品の基本設定（最初に編集）
├── characters.yaml      ← キャラ名簿（Step3で埋める）
├── locations.yaml       ← ロケーション名簿（Step3で埋める）
├── step0_企画/          ← Step0の成果物
│   └── [作品名]_step0_planning.md
├── step1_構成最適化/    ← Step1の成果物
│   └── [作品名]_step1_outline.md
├── step2_脚本/          ← Step2の成果物
│   └── [作品名]_step2_script.md
├── step3_設定資料/      ← Step3の成果物（文章＋参照画像）
│   ├── [作品名]_step3_settings.md
│   ├── character_sheets/   ← キャラ参照画像（Step3で生成）
│   └── location_sheets/    ← 背景参照画像（Step3で生成）
├── step4_ページ設計/第○章_〇〇/   ← Step4の成果物
├── step5_コマ構成/第○章_〇〇/     ← Step5の成果物
├── step6_yaml生成/第○章_〇〇/     ← Step6のYAML
├── step7_完成画像/第○章_〇〇/     ← Step7の完成ページ画像
├── step8_表紙/          ← Step8の成果物
│   ├── [作品名]_step8_cover_prompt.md
│   ├── [作品名]_cover_with_text.png
│   └── [作品名]_cover_no_text.png
└── scripts/
    └── prepare_pages.py    ← 参照画像候補と保存先を出す汎用ローダー（Codexが実行）
```
