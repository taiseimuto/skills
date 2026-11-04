# デザインとSVGの型

## 原則

同梱の `assets/template/style.css` は、元の教材で確認された完成版から抽出したもの。別エージェントもこのファイルを直接使い、見た目を再解釈しない。文章量と章構成を対象に合わせても、余白・色・タイポグラフィ・部品は変えない。

| 要素 | 共通値 |
| --- | --- |
| 背景・文字 | `#fff` / `#26323e` |
| 補助文字・罫線 | `#52616e` / `#dfe5e8` |
| アクセント | `#21675d` |
| 目次背景 | `#fafbfc`、右罫線、activeは薄い緑 |
| フォント | OSの日本語sans、コードはsystem monospace。外部Webフォントなし |
| PC | 左目次252px、sticky header66px、本文最大1050px、左右48px |
| 中間幅 | 1100px以下で目次222px、左右28px |
| スマホ | 760px以下でdrawer目次、header58px、本文左右18px、本文15px |
| 見出し | h1は36px、スマホ29px。章は番号＋短い補助ラベル＋h2 |
| 部品 | 薄い罫線、小さな角丸、codeだけ暗い背景。技術詳細は閉じたdetails |

文章と図に意味がある場所だけ部品を使う。アプリの宣伝、架空の指標、不要なカード、装飾用のロゴ列を増やさない。

## SVGの作り方

`diagram` blockを `scripts/diagrams.py` が描画する。Mermaidや画像生成で見た目を置き換えない。SVGは単体で開いても同じ図になるよう内部CSS・矢印marker・base64ロゴを含む。

| primitive | 描画 |
| --- | --- |
| node | 白、stroke `#d6e1e8`、rx8 |
| band | fill `#f5f9fa`、stroke `#e2e9ed`、rx10、dash `5 4` |
| arrow | stroke `#729597`、1.5px、直交折線、6px marker |
| node title | 14px / weight650 / `#213b4b` |
| subtitle | 10px / `#5d7184`、行間16px |
| edge label | 10px monospace / `#66778a` |
| service logo | 左上から15px/17px、31px角。タイトル開始は左から58px |
| ロゴなし | タイトル開始は左から17px |

viewBoxの幅は通常880〜920、高さは構成に合わせる。ノード幅は230〜270px、最低120px。高さは通常75〜90px、最低65px。2行のsubtitleには82px以上を目安に確保する。大きな図は境界・視点で分割し、1図に無関係なレイヤーを詰め込まない。

### 配置の順番

1. 何を説明する図か決める：コードの責務、React構成、request flow、auth、環境別インフラ、配信のいずれか。
2. bandで実行場所・環境・信頼境界を示す。未確認の接続を実線で捏造しない。
3. 主要ノードを揃える。左右・上下に40px以上の経路用の余白を確保する。
4. `from` / `to` とsideで直交する矢印を引く。分岐や迂回は `via` か `points` で明示する。
5. path、protocol、Cookie、event等のラベルを `label_at` で矢印や枠に重ならない位置へ置く。
6. 文字が長ければタイトルを短くし、subtitleとcaptionに情報を分ける。文字を小さくして詰め込まない。
7. スマホの横スクロールと「拡大」を確認し、SVG全体をブラウザでも見る。

環境差がある図は `tabs` で切り替える。staging/prodが同じ構成だと仮定しない。コードの構成図とネットワーク構成図も、説明の目的が異なれば分ける。

## ロゴ

同梱の20個のロゴは元の教材で利用した素材。`assets/icons/sources.json` に出典とハッシュ、`LICENSES.txt` に通知を収録。ブラウザからCDNへ取得しない。

- 技術：react、typescript、vite、tailwindcss、express、github、terraform、docker、zod、vitest。
- AWS：cloudfront、alb、ecs、ecr、dynamodb、s3、waf、ses、secrets、route53。

未収録の技術は公式または出典が明らかな素材をローカル保存し、`meta.icons` で追加する。公式ロゴを捏造しない。適切な素材がなければ、ロゴを省略するか技術名のmonogramを使う。Reactのロゴを一般的なBrowserの記号として使うなど、別のサービスを表す用途には流用しない。

## 視覚基準

`assets/example/guide.json` をrenderすると全ブロックと環境別SVGのサンプルになる。`assets/reference-mobile.png` と `assets/reference-desktop.png` はその表示の基準画像。元案件固有の文章や秘密値は含めない。
