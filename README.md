# Inspector Plugins

GitHub・コード構造・実験モデルを調べる、独立した3つのローカルCodexプラグインです。
必要なものだけ選んで導入できます。Rustのビルドは不要です。

| プラグイン | バージョン | 主な用途 |
| --- | --- | --- |
| [github-work-inspector](https://github.com/iwashita-nozomu/github-work-inspector) | 0.3.4 | ブランチ・コミット・Issue・PR・CIを読み取り |
| [code-structure-inspector](https://github.com/iwashita-nozomu/code-structure-inspector) | 0.1.2 | 指定したフォルダの宣言・構文上の依存・関連ファイルを確認 |
| [experiment-model-inspector](https://github.com/iwashita-nozomu/experiment-model-inspector) | 0.1.2 | 宣言ファイルとソースの根拠から数理モデル・データフローを確認 |

## 最短の導入手順

前提は、Gitと `codex plugin marketplace add` / `codex plugin add` を持つCodex CLIです。
CLI 0.164.0で検証しています。CLIが古く、このコマンドが出ない場合はCodexを更新してください。
プラグインは実行するホスト側に入れます。Webやモバイルだけでローカルプロセスは動きません。

1. **使うOSのカタログを1つ登録**します。次の3行を全部実行する必要はありません。

Mac（Apple Silicon）:

```sh
codex plugin marketplace add iwashita-nozomu/inspector-plugins --ref macos-arm64
```

Linux（x64 / glibc）:

```sh
codex plugin marketplace add iwashita-nozomu/inspector-plugins --ref linux-x64
```

Windows（x64、PowerShellでも同じ）:

```sh
codex plugin marketplace add iwashita-nozomu/inspector-plugins --ref windows-x64
```

2. **必要なプラグインだけ追加**します。たとえばGitHubを見るなら1行目だけです。

```sh
codex plugin add github-work-inspector@inspector-plugins
codex plugin add code-structure-inspector@inspector-plugins
codex plugin add experiment-model-inspector@inspector-plugins
```

3. **新しいCodexセッションを開き**、対象を明示して依頼します。

- GitHub: 「github-work-inspectorで `OWNER/REPO` のブランチ・PR・CIを確認して」
- コード: 「code-structure-inspectorで、このプロジェクトの構造を読み取りで調べて」
- 実験: 「experiment-model-inspectorで、このフォルダの `experiment-model.json` を使ってモデルとデータフローを確認して」

Codex CLIの `/plugins` からも、登録したマーケットプレイス内の3候補を選べます。
確認は `codex plugin marketplace list` と `codex plugin list --marketplace inspector-plugins` で行えます。

### Workでの利用・グラフ表示について

この配布で確認しているのは、**ローカルCodexでの導入と専用MCPツールの認識・呼び出し**です。
Workのすべての会話で専用ツールが使えることや、Work画面内のグラフ表示は確認できていません。
専用のWebViewや対話的グラフ画面は含めていません。解析結果の取得と表示は別の段階です。
別のホスト・別の会話では、プラグインの選択と専用ツールの可用性を改めて確認してください。
通常のGitHubコネクタによる調査だけでは、github-work-inspectorの動作確認にはなりません。

## 必要な準備と対応範囲

| 環境 | 配布ブランチ | 同梱バイナリ |
| --- | --- | --- |
| macOS Apple Silicon | `macos-arm64` | aarch64-apple-darwin |
| Linux x64 / glibc | `linux-x64` | x86_64-unknown-linux-gnu |
| Windows x64 | `windows-x64` | x86_64-pc-windows-msvc |

Intel Mac、Linux ARM、musl/Alpine、Windows ARMのネイティブ版は含めていません。
Linux版はUbuntu 24.04系の公開runnerでビルドされたバイナリです。古いglibc環境は未検証です。
バイナリは開発者署名・Apple notarizationなしです。

GitHub側のプラグインには、別途GitHub CLI (`gh`) と、利用者自身の既存GitHub認証が必要です。
`gh auth status --hostname github.com` で確認できます。インストールで認証や権限は追加しません。
privateリポジトリは、その認証で既に読めるものだけが対象です。
残り2本は外部サービスの認証やネット接続を使わず、利用者が許可したローカルフォルダだけを解析します。

実験プラグインは利用者が用意した宣言ファイルと、そこに示したソースの根拠が必要です。
宣言形式は[実験プラグインのREADME](https://github.com/iwashita-nozomu/experiment-model-inspector#readme)を参照してください。
コード解析は構文上の根拠であり、完全な呼び出しグラフや計算結果の正しさを保証しません。

## 更新

自動アップデーターはありません。まずカタログだけを取得します。

```sh
codex plugin marketplace upgrade inspector-plugins
```

[更新履歴](docs/RELEASES.md)と対象ブランチの `releases.lock.json` で変更するバージョン・元コミットを確認し、
更新したい1本だけを入れ直して、新しいセッションを開きます。

```sh
codex plugin remove code-structure-inspector@inspector-plugins
codex plugin add code-structure-inspector@inspector-plugins
```

カタログの取得だけで、未選択のプラグインを自動インストール・有効化しません。
再導入後の実行確認や許可は、利用中のCodexホストの設定に従ってください。
配布を固定したい場合は、ブランチ名の代わりに
`v0.1.0-macos-arm64` / `v0.1.0-linux-x64` / `v0.1.0-windows-x64` のタグ、
またはその完全なコミットSHAを `--ref` に指定できます。

## 削除

消したいプラグインを指定します。

```sh
codex plugin remove github-work-inspector@inspector-plugins
```

すべての利用を終えたら、各プラグインを削除したうえでカタログも解除できます。

```sh
codex plugin marketplace remove inspector-plugins
```

GitHub CLIの認証は別管理なので、プラグインの削除では変更しません。

## 既にローカル導入している場合

`@personal-local` など別のマーケットプレイスからの導入とは別のプラグイン識別子になります。
既存登録の移行・削除・設定の引き継ぎは、このリポジトリでは自動実行しません。
同じツールを重複して読み込まないよう、移行する際は以前の提供元と許可設定を先に確認してください。
Gitプラグインの呼び出し確認やツール許可リストもホスト側の設定であり、配布物には埋め込みません。

## 配布の仕組み・ライセンス

`main` は案内・固定リリース情報・配布作成用ツールを置くブランチです。**登録時はOS別の `--ref` が必要です。**
正式なCodexカタログ `.agents/plugins/marketplace.json` は各OS別ブランチにあります。
公開ReleaseのアーカイブをSHA256で照合し、その内容を変更せず `plugins/` に収録しています。
選択したGitスナップショット内の同梱バイナリを使うため、実行時のダウンロードやソースビルドはありません。
OSは自動判定しません。カタログ登録時に利用者が選びます。

各プラグインはstdio MCP＋明示的に選択するSkillです。相互呼び出し、共有DB、共有キャッシュ、待受ポート、
独自AI API呼び出しを持ちません。GitHubの解析は `gh` による読み取りリクエストを使います。
stdio MCPはホスト側のプロセスとして動きます。読み取りの注記はOS権限の制限ではなく、
Codexのコマンド用サンドボックスと同じ隔離を受けるとは限りません。
送信・解析する範囲は利用者の依頼とホスト側の許可で決まります。

独自カタログであり、OpenAI公式ディレクトリへの掲載・審査済みを意味しません。
カタログと各プラグインのオリジナルコードはMITです。各配布物内の `LICENSE`、`THIRD_PARTY_NOTICES.md`、
`third-party/` に依存ライセンスをそのまま含めています。

[設計・検証方法](docs/DISTRIBUTION.md) / [各プラグインREADMEへの導線案](docs/UPSTREAM_README_SNIPPETS.md) /
[セキュリティ報告](SECURITY.md)
