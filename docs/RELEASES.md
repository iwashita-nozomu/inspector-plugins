# カタログ v0.1.1

Gitの改行変換を無効にし、元のReleaseに含まれるライセンスやJSONのバイト列を
全OSのcheckoutで保持します。混在改行を実際にGitへcommit/cloneする回帰テストを追加しました。
プラグイン本体のバージョン・バイナリ・機能は変えていません。

初回の `v0.1.0-<platform>` タグは、ライセンス1件の改行変換とWindowsでの
固定情報の改行変換により完全性検証が通らないため、使用しないでください。
既存タグは書き換えず保持し、以下の修正版タグで配布します。

| Plugin | Version | Upstream source commit |
| --- | --- | --- |
| github-work-inspector | 0.3.4 | `a15a11b3168410611baa11af37b8e9532b928c0c` |
| code-structure-inspector | 0.1.2 | `b3bbfa1ed6dc150e5238b5863211747718e3f5c0` |
| experiment-model-inspector | 0.1.2 | `09f541c0099857c51a284899f34118ca4e6b567c` |

macOS ARM64 / Linux x64 / Windows x64それぞれに同じ3候補を提供します。
配布タグは `v0.1.1-<platform>`。元のアーカイブURL・SHA256・サイズは
[`releases.lock.json`](../releases.lock.json)に固定しています。
カタログに追加してもプラグインを自動インストールしません。
