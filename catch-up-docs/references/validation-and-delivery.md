# 検証と受け渡し

## 自動チェック

`verify_guide.py` は、章・見出し・ID重複・アンカー・画像等の参照・折り畳み初期状態・SVGの外部依存を確認する。singleには必ず `--single` を付ける。これはレイアウトや内容の正しさを保証するものではない。

```bash
python3 <skill-dir>/scripts/verify_guide.py /path/build/site/index.html
python3 <skill-dir>/scripts/verify_guide.py /path/build/guide.html --single
```

JavaScriptを変更した場合、Nodeがあれば `node --check <skill-dir>/assets/template/app.js` も実行する。

## ブラウザで見る項目

利用可能なブラウザQAツールを使う。生成自体はPython標準ライブラリだけで動作し、ブラウザツールの導入や外部サービスへの送信は必須ではない。

1. 320 / 375 / 430pxと、PC幅1280pxで本文全体が横にはみ出さないこと。表・code・構成図の内部スクロールは意図したもの。
2. スマホ目次の開閉・Escape・項目への遷移。固定headerが章見出しを隠さないこと。
3. 技術詳細が初期状態で閉じていること。検索、該当なし、全開閉を確認する。
4. ファイル探索の選択を変えるとURL・file・説明が対応して変わること。
5. 環境タブが正しい図を表示し、SVG拡大dialogが閉じられること。図を全体表示し、線・文字・ロゴ・枠が重ならないこと。
6. チェックを変更し再読込する。保存を拒否するブラウザ設定でも致命的なエラーが出ないこと。理解確認は根拠の説明を返すこと。
7. `guide.html` を `file://` で直接開く。ネットワークをofflineにして、CSS・JS・ロゴ・SVGが表示され、目次・技術詳細・図の拡大が使えること。外部の根拠リンクは当然オンライン接続が必要。
8. JS例外、画像エラー、意図しない外部リクエストがないこと。

clipboard APIやlocalStorageはfile://やブラウザ設定で制限される場合がある。コピー失敗は選択でコピーする案内を表示し、保存失敗は教材を壊さない。端末間の同期を約束しない。

`assets/reference-mobile.png` / `reference-desktop.png` とレイアウトを比較する。長い文章や表がある章、開いた技術詳細、構成図も別途確認する。ブラウザが利用できない場合は、自動チェック済み・描画未確認と報告する。

## 静的サイト

`site/` 全体を成果物として渡す。index.htmlだけを抜き出すとCSSとJSが失われる。ローカルpreview例：

```bash
python3 -m http.server 4183 --bind 127.0.0.1 --directory /path/build/site
```

このloopback URLはスマホや別マシンからの閲覧URLではない。スマホから読みたい要件には、指定されたホスティングへの公開、または単一HTMLの転送で対応する。

## 単一HTML

`guide.html` の1ファイルで渡す。元のJSON、renderer、フォルダ構成は閲覧時には不要。CSS・JS・ロゴ・SVGは埋め込み済み。外部解析、CDN、Webフォントを追加しない。

## ChatGPT Sites

Sitesをユーザーが求めた場合、利用可能なSitesスキルを読んで、そのsource作成・manifest・private/publicの扱い・packaging・保存・公開確認に従う。生成した `site/` を独立したSite sourceのstatic directoryにコピーする。

このスキルに元の教材SiteのID、URL、資格情報は含めない。元のSiteを別案件で更新しない。新規なら新規Siteとして登録し、個人用は非公開を維持する。ネイティブ公開結果が成功してURLを返してから公開済みと報告する。

アプリ本体へのデプロイや、教材のホスト先以外のAWS等の変更はこの手順に含めない。
