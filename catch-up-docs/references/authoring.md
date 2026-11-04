# 入力JSONと生成CLI

## 入力の構造

完全な例は `assets/example/guide.json`。文章を対象リポジトリへ置き換え、必要な部品だけ残す。JSONはUTF-8。scriptの既定デザインを変更する必要はない。

```json
{
  "meta": {
    "guide_id": "example-project",
    "title": "開発参加のための技術ガイド",
    "repo_name": "organization/repository",
    "repo_url": null,
    "commit": null,
    "verified_at": "調査日を記載",
    "lead": "何を理解し、どこまでできるようになる教材か。"
  },
  "chapters": [
    {
      "id": "orientation",
      "title": "全体像",
      "eyebrow": "ORIENTATION",
      "intro": "この章で理解すること。",
      "blocks": [{"type": "html", "html": "<p>実装の根拠に基づく本文。</p>"}]
    }
  ]
}
```

実案件では `repo_url` にGitHubのリポジトリURL、`commit` に確認したfull SHA（40または64桁）を入れる。`path` の根拠リンクを自動生成する。他のGitホストではsourcesに `url` を明示する。サンプルのような明示的な架空例だけnullを使う。

### meta

| field | 用途 |
| --- | --- |
| guide_id | 小文字英数字・ハイフン、英字開始。ブラウザ保存の教材別namespace |
| title / lead / repo_name / verified_at | 必須。ページtitle、説明文、対象名、調査日 |
| repo_url / commit | GitHubのURLと対象full SHA。認証情報入りURLは禁止 |
| heading_lines | 任意。h1の行ごとの配列。通常はタイトルだけ、または短い2行 |
| short_name | ヘッダー用の短い名前 |
| description / audience / footer | 任意。メタ説明、目次下の読者、末尾の説明。公開制御を行う設定ではない |
| snapshot | 任意。branch @ short SHA等。省略時はcommitの先頭7桁 |
| actions | 任意。`[{"target":"setup","label":"開発準備から読む"}]`。対象IDが存在すること |
| icons | 任意。`{"fastapi":"logos/fastapi.svg"}`。入力JSONと同じディレクトリ配下のローカル画像。外部URLや親ディレクトリ参照は不可 |

章の `id` も英字開始の小文字英数字・ハイフン。`nav` で目次の短い表示名を指定できる。IDは章・widget・図を含め文書全体で一意にする。章番号は生成するため手書きしない。

## ブロック

### 本文・コード・注記

```json
{"type":"html","html":"<h3>見出し</h3><p><code>src/main.ts</code> から処理を辿る。</p>"}
{"type":"code","text":"npm ci\nnpm run check"}
{"type":"note","title":"実装の注意","html":"<p>このrepoでだけ成立する条件。</p>"}
{"type":"note","kind":"warn","title":"未確認事項","html":"<p>根拠から確定できなかったこと。</p>"}
```

`html` と表のcellには文章用の限定HTMLを使用できる：p / h3 / h4 / ul / ol / li / strong / b / em / i / code / br / a / span / small。許可属性はhref / title / class、classはsmallまたはtag。script、style、event属性、埋め込みiframeや外部画像は使わない。コード断片は `code.text` に渡せば自動escapeされる。

### 表・比較

```json
{"type":"table","headers":["目的","入口"],"rows":[["画面の変更","<code>src/pages/</code>"]]}
{"type":"columns","items":[{"eyebrow":"CLIENT","title":"フロント","html":"<p>画面を担当する。</p>"},{"eyebrow":"SERVER","title":"バック","html":"<p>APIと保存を担当する。</p>"}]}
```

columnは責務や役割を比較するときだけ使う。長い本文をすべてカードに入れない。表はスマホで横スクロールする。

### 根拠

```json
{"type":"sources","items":[{"path":"src/main.ts","line":12},{"url":"https://react.dev/reference/react/lazy","label":"React公式"}]}
```

`path` はリポジトリ相対。`label` は任意。`line` は任意の開始行で、コードを読んで確かめた番号にする。commitがnullの架空例ではリンクを生成せずパスだけ表示する。

### 技術解説

```json
{
  "type":"tech_stack", "id":"tech-notes", "items":[{
    "group":"01 / FRONTEND", "name":"技術名", "version":"lockfileで確認した版",
    "monogram":"UI", "summary":"1行の役割",
    "what":"初めて使うエンジニア向けの仕組みの説明。",
    "locations":[{"path":"src/main.ts"}],
    "motivation":"この構成に適する理由。記録がなければ解釈として書く。",
    "benefits":"メリット。", "tradeoffs":"負担と適用限界。",
    "attention":"一般論とは異なる、このrepoの設定やversion固有の注意。",
    "docs":[{"url":"https://react.dev/","label":"採用版を確認できる公式資料"}]
  }]
}
```

`icon` を指定するとbundled/localのロゴを使い、なければ `monogram` または技術名の先頭2文字を表示する。`motivation_status` の既定は推論。意思決定記録がある場合だけ `"documented"` と `motivation_sources` を付ける。技術詳細は閉じた状態で生成し、検索と全開閉の共通UIを付ける。

### ファイル探索

```json
{"type":"file_finder","id":"page-finder","title":"どの画面を直したい？","items":[{"label":"トップ画面","route":"/","file":"src/pages/home.tsx","description":"このファイルの責務と次に辿る場所。"}]}
```

実際に存在するURL・fileだけ入れる。APIやDBのデータが由来なら説明に明記する。source_urlはrepo_urlとcommitから生成する。

### SVG図

```json
{
  "type":"diagram", "id":"request-flow", "title":"リクエストの流れ",
  "figure_label":"FIG. 01 / REQUEST FLOW", "width":900, "height":220,
  "caption":"どの定義から確認した図か、何を省略したか。",
  "description":"アクセシブルな短い図の説明。",
  "bands":[{"x":15,"y":15,"w":870,"h":190,"label":"APPLICATION"}],
  "nodes":[
    {"id":"client","x":35,"y":75,"w":240,"h":82,"title":"Client","subtitle":["request"],"icon":"react"},
    {"id":"api","x":330,"y":75,"w":240,"h":82,"title":"Express API","subtitle":["validation / storage"],"icon":"express"}
  ],
  "edges":[{"from":"client","to":"api","label":"HTTP","label_at":[280,100]}],
  "sources":[{"path":"server/routes.ts"}]
}
```

- ノード：x / y / w / h、短いtitle、subtitleの行配列、任意のicon。h省略時82px。
- 矢印：from / to、from_side / to_side（left/right/top/bottom）、任意のvia（中間座標配列）。既定はright→leftで自動直交接続。
- 完全指定する場合は `points:[[x,y],[x,y],...]`。`label` を付けるなら `label_at:[x,y]` が必須。
- `annotations:[{"x":35,"y":185,"text":"補足","class":"svg-sub"}]` で補助文字を置ける。
- 同じ図内のnode IDは一意。異なる図間では同じnode IDを使ってよい。
- 正確な寸法とレイアウトの進め方はdesign-and-svg.mdを参照。

### 環境タブ

```json
{"type":"tabs","id":"environments","items":[{"label":"本番","blocks":[]},{"label":"検証","blocks":[]}]}
```

blocksに環境ごとのdiagramや説明を入れる。1つの図へ環境を重ねない。

### 学習チェックと理解確認

```json
{"type":"checklist","id":"first-task","title":"到達チェック","items":[{"id":"locate","label":"対象ファイルを特定できる"}]}
{"type":"quiz","id":"routing-question","question":"確認したい問い","answers":["選択肢A","選択肢B"],"correct":1,"explanation":"根拠を含む説明。"}
```

チェック項目のIDは同じ教材を更新しても意味が変わらないようにする。文字列だけのitemsも可能だがindexからIDになる。quiz.correctは0始まり。チェックはlocalStorageのみ、サーバーや別端末へ同期しない。file://やプライベートモードで保存が拒否されても教材の閲覧は続く。

## 出力と再生成

```bash
python3 <skill-dir>/scripts/render_guide.py --input /path/guide.json --output /path/build --format both
```

静的サイトのentryは `build/site/index.html`。単一HTMLのentryは `build/guide.html`。staticでは `site/diagrams/*.svg` も出力し、図をそのまま資料へ転用できる。singleでは図もHTML内に埋め込み、同梱ファイルを必要としない。

生成は既知の出力ファイルを更新する。無関係なファイルを一括削除しないため、別教材の出力先を使い回さない。生成結果へ直接手修正せず、JSONまたは明示的に依頼されたtemplate変更を直して再生成する。
