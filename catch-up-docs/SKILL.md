---
name: catch-up-docs
description: リポジトリを実装から調査し、開発参加のための技術教材を作る。統一されたシンプルなデザイン、ロゴ入りSVG構成図、折り畳み式の技術解説を使い、静的サイトまたは単一HTMLとして出力する。短いコード説明やアプリ自体の改修には使わない。
---

# Catch-up Docs

開発に参加するエンジニアが、コードの入口から小さな修正・検証・レビューまで辿れる教材を作る。内容は対象リポジトリに合わせ、見た目とSVGの描画方式は同梱のテンプレートで統一する。

## 成果物と作業境界

- 対象コードベースは調査対象。教材作成だけの依頼ではアプリのコード・設定を変更しない。出力は原則リポジトリ外に置く。指定場所やAGENTS.mdがある場合はそれに従う。
- 章数や技術名、DB、インフラ、ブランチ運用を過去の案件から流用しない。ユーザーの経験・参加目的・引継ぎメッセージ・対象範囲から構成を決める。
- ソース、lockfile、workflow、IaCを照合し、READMEや過去の引継ぎとの食い違いを説明する。実装の事実・設計意図の解釈・運用の未確認事項を分ける。
- 秘密値・個人情報・実データを教材へ埋め込まない。初期化や起動時に共有DBへ書き込む可能性があるので、調査なしに起動しない。手順の説明はデプロイ実行の許可ではない。

## 1. 調査して教材を組み立てる

[references/repository-analysis.md](references/repository-analysis.md) を読み、対象SHA、採用バージョン、入口、変更例、環境差、CI/CDを確認する。Context7があればライブラリ仕様を照合し、なければ採用版の公式資料を使う。利用できないMCPを前提に停止しない。

教材は原則として次の疑問に答える。独立した章にするかまとめるかは対象に合わせる。

1. 何を提供するアプリで、今回の担当範囲はどこか。
2. 必要な権限・環境変数をどう揃え、何をインストールし、どのURLで開くか。
3. URL・page・共通部品・CSS・API・保存層・共有schemaはどこか。
4. UIからAPI、認証、データ保存へ処理がどう進むか。
5. 各技術は何を担い、なぜ適するか。メリット、負担、採用版固有の注意は何か。
6. 環境ごとの構成とIaCの境界は何か。
7. 小さな文言修正なら、どのファイルを直し、何を検証し、誰がレビュー・反映判断するか。
8. 根拠・検証結果・未確認事項は何か。

技術詳細は最初から閉じた折り畳みにする。専門用語を使い、比喩で薄めない。実装と繋がらない一般論だけのライブラリ説明にしない。

## 2. 共通デザインで生成する

**CSSやHTMLを雰囲気から作り直さない。** [assets/template/](assets/template/) と `scripts/render_guide.py` を使う。React・CSSフレームワーク・Webフォント・Mermaidへの置換や、独自のテーマ追加はユーザーが求めた場合に限る。

- 白基調、薄い罫線、控えめな緑、システムフォント。大きな装飾見出し、グラデーション、不要なアニメーション、紹介カードの反復を加えない。
- PCは左目次、スマホは開閉目次。章番号、コード、比較表、根拠リンクを主体にする。
- 構成図は同梱のSVG生成処理を使う。座標・角丸・線・文字・サービスロゴを統一し、横スクロールと拡大を提供する。
- 必要な場合だけ技術検索、ファイル探索、環境タブ、学習チェック、理解確認を使う。章数や部品数を埋めるために追加しない。

JSONの書き方は [references/authoring.md](references/authoring.md)、SVG設計とレイアウト値は [references/design-and-svg.md](references/design-and-svg.md) を読む。完成形の入力例は [assets/example/guide.json](assets/example/guide.json)。これは架空の構成例であり、実案件の事実として流用しない。

`<skill-dir>` は、このSKILL.mdがあるフォルダの絶対パスへ置き換える。Python 3.10以上・標準ライブラリだけで実行でき、npmやネット接続は生成時に不要。

```bash
python3 <skill-dir>/scripts/render_guide.py \
  --input /absolute/path/guide.json \
  --output /absolute/path/output \
  --format both
```

- `static` → `output/site/index.html`、CSS・JS・使用したロゴ、単体で開けるSVG。
- `single` → `output/guide.html` の1ファイル。CSS・JS・画像・SVGをすべて埋め込み、外部ファイルやサーバーなしで閲覧可能。
- `both` → 上記の両方。同じ入力・同じテンプレートを使い、見た目と機能を揃える。

形式指定がなければ `both`。出力先はユーザーの指定を優先し、解析対象のコードベースへ不用意に書き込まない。

## 3. 検証と受け渡し

```bash
python3 <skill-dir>/scripts/verify_guide.py /absolute/path/output/site/index.html
python3 <skill-dir>/scripts/verify_guide.py /absolute/path/output/guide.html --single
```

存在する形式だけ検証する。さらにブラウザが使える場合は [references/validation-and-delivery.md](references/validation-and-delivery.md) に従い、スマホ幅・開閉・検索・拡大・単一HTMLのfile://閲覧を確認する。利用できない場合は静的検証の範囲を明示する。

静的サイト／単一HTMLの依頼はローカル成果物で完了できる。ChatGPT Sitesでの公開を求められた場合は、利用可能なSitesスキルのワークフローへ `output/site/` を渡す。既存SiteのIDを流用せず、対象Siteと公開範囲を確認する。個人用・非公開の指定を維持する。Sites以外のホストへのデプロイやアクセス制御の変更をこのスキルが包括的に許可することはない。

最終回答には実際の成果物または確認済みの公開URL、内容の範囲、検証の限界を簡潔に示す。
