# 調査と内容の組み立て

## 最初に固定する情報

- ユーザーの経験、チーム構成、参加する改修、引継ぎで求められた到達点。
- 対象リポジトリ、ローカル変更の有無、対象branchとfull commit SHA、確認日。
- 教材の保存先と公開範囲。個人用なら公開配布を前提にしない。

利用可能なローカルcheckoutや接続済みGitHubを先に使う。ソースリンクは確認したSHAへ固定する。動いているAWS等の構成を直接調べていなければ、「IaCの定義」として示す。

## 探索の入口

`rg --files` と `rg` でファイルを絞り、独立した読み取りはまとめる。

| 観点 | 読むもの | 確定すること |
| --- | --- | --- |
| 依存と起動 | manifest、lockfile、runtime設定、Docker、Compose、env example | 宣言rangeと解決済みversion、起動script、port、env読込、DB初期化 |
| フロント | entry、router、layout、pages、features、components、CSS、query client | URL→pageの対応、共通部品、状態の寿命、CSSの範囲 |
| バック | server entry、routes、auth middleware、storage契約と実装、schema | HTTP境界、認証/認可、入力検証、DB操作とトランザクション |
| インフラ | Terraform root/backend、CDN、app runtime、DB、object storage | 環境の境界、通信経路、永続化、秘密値の注入元 |
| 配信 | workflow triggers、paths、jobs、environments、build scripts | PR CIの対象、pushの影響、両環境の反映手順、実際のチェック |
| 背景 | README、設計、引継ぎ、ADR | 事実との相違、過去時点の状況、採用理由の記録 |

READMEと依存一覧だけで構成を断定しない。未使用のパッケージ、旧DB説明、古い画面配置、現在は解消した課題が混ざる。

## ローカル起動の説明を検証する

手順を書く前に、次をコードから確認する。

- envファイルはどのプロセスが読むか。npm scriptが暗黙に読むと決めつけない。
- Composeのcontainer portとhost port、appのportはどれか。
- テーブル・監査ログ・session等の初期化が揃うか。seedが空DBだけに作用するか。
- DB endpoint省略時の接続先、AWS認証の解決、S3・通知・外部APIの副作用。
- production modeのsecure Cookieと、HTTP localhostの不一致。
- ローカル用envがGitに除外されるか。除外されなければ共有設定を勝手に変えず、ローカルexclude等の方法を説明する。

アプリの起動やテストは教材の精度に必要で、安全に分離できる場合に限る。既存worktreeの変更を保持する。解析しただけの手順と、実行して確認した手順を区別する。

## ライブラリ解説

各技術は「何か／このrepoの場所／採用動機／利点／負担／実装固有の注意／公式資料」で説明する。長い説明は `tech_stack` に置く。

- versionはlockfileを優先。最新資料しかない場合はversion差を明記。
- Context7が利用可能なら採用版の仕様を参照する。利用できなければ公式資料を参照し、未確認APIを生成しない。
- ADR等で採用理由を確認できた場合だけ `motivation_status: documented` にし、その根拠を付ける。それ以外はinferredとして表示。
- 単なる「高速・軽量」ではなく、既存のルーティング、キャッシュ、認可、配信方式と関連付ける。

## 最初の小変更

文言変更を1つ選び、URL・file・識別しやすい文字列またはtest IDを固定する。変更例は教材上の仮想差分であり、依頼がない限り実コードへ適用しない。

型検査、テスト、build、format、lintはmanifestとCIにある実際のscript名を使う。検証の対象範囲と見た目の確認を分ける。CIがすべてのPRで動くと仮定しない。branch/pathの条件と、複数workflowの同時起動・非原子的な反映も説明する。

本番の決裁者やbranch protectionは、ソースだけで確定できないことがある。分からない場合は「要確認」とし、役割分担の提案を事実として書かない。

## 根拠の章

少なくとも対象SHA・確認日・実行した検証・実行していない検証・未確認運用を残す。過去の引継ぎにある公開人数、稼働version、権限不足等を現状として転記しない。
