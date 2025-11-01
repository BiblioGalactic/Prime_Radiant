# 🤖 AI クラスター - 分散AIシステム

**ローカルネットワーク(イントラネット)上の複数のマシンを使用してAIクエリを並列処理します。**

クラウド不要 • プライベート • スケーラブル • オープンソース

---

## 📋 説明

AI Clusterは、ローカルネットワーク上のアイドル状態のコンピューターを活用して、AIモデルを分散的に実行できるシステムです。以下を求める企業に最適です:

- ✅ **完全なプライバシー** - データがネットワークから出ることはありません
- ✅ **クラウドコストなし** - 既存のハードウェアを使用
- ✅ **GDPR準拠** - すべて自社インフラ内
- ✅ **スケーラブル** - マシンを簡単に追加
- ✅ **並列処理** - クエリを同時実行

---

## 🚀 ユースケース

### 企業向け
- オフィスPCを使用した複数のAIクエリ処理
- 分散ドキュメント分析
- 並列コンテンツ生成
- 反復タスクの自動化

### 開発者向け
- 分散システムの実験
- 並列化の学習
- モデルパフォーマンステスト
- 迅速なソリューションプロトタイピング

---

## 🎯 機能

- ✨ **対話型ウィザード** - ステップバイステップのガイド付き設定
- 🔐 **自動SSH設定** - パスワードなし接続の設定
- 🌐 **マルチマシン** - ネットワーク上のN台のコンピューターをサポート
- ⚖️ **ラウンドロビンバランシング** - 負荷を均等に分散
- 📊 **詳細な統計** - 処理を監視
- 🛡️ **堅牢なエラー処理** - マシンが故障しても継続

---

## 📦 要件

### すべてのマシンで:

1. **コンパイルされたllama.cpp**
   ```bash
   git clone https://github.com/ggerganov/llama.cpp
   cd llama.cpp
   make
   ```

2. **ダウンロードされたGGUFモデル**
   - Mistral、Llama、Qwenなど
   - すべてのマシンで同じパスに配置

3. **SSH有効化** (リモートマシンのみ)
   ```bash
   # macOS
   sudo systemsetup -setremotelogin on
   
   # Linux
   sudo systemctl enable ssh
   sudo systemctl start ssh
   ```

---

## ⚙️ インストール

### 1. スクリプトのダウンロード

```bash
# リポジトリをクローン
git clone https://github.com/BiblioGalactic/ai-cluster
cd ai-cluster

# または直接ダウンロード
curl -O https://raw.githubusercontent.com/BiblioGalactic/ai-cluster/main/ai-cluster.sh
chmod +x ai-cluster.sh
```

### 2. 初期設定

```bash
./ai-cluster.sh setup
```

ウィザードが以下を案内します:
- ✅ llama.cppとローカルモデルの検出
- ✅ リモートマシンIPの設定
- ✅ パスワードなしSSHの設定
- ✅ 接続とファイルの確認

---

## 📖 使用方法

### 基本コマンド

```bash
./ai-cluster.sh run queries.txt
```

### クエリファイル

質問を1行ずつ記載した`queries.txt`ファイルを作成:

```
ニューラルネットワークとは何かを説明してください
相対性理論を要約してください
日本の首都はどこですか?
テクノロジーについての俳句を書いてください
```

### その他のコマンド

```bash
# 現在の設定を表示
./ai-cluster.sh config

# 接続をテスト
./ai-cluster.sh test

# 再設定
./ai-cluster.sh setup

# ヘルプ
./ai-cluster.sh help
```

---

## 🏗️ アーキテクチャ

```
┌─────────────────────────────────────────────────┐
│           ai-cluster.sh (オーケストレーター)     │
└─────────────┬───────────────────────────────────┘
              │
      ┌───────┴────────┬──────────────┬──────────┐
      │                │              │          │
  ┌───▼────┐      ┌───▼────┐    ┌───▼────┐ ┌───▼────┐
  │ ローカル│      │ PC 1   │    │ PC 2   │ │ PC N   │
  │ (Mac)  │      │ (SSH)  │    │ (SSH)  │ │ (SSH)  │
  └────────┘      └────────┘    └────────┘ └────────┘
  クエリ1,5,9     クエリ2,6,10   クエリ3,7   クエリ4,8
```

**ラウンドロビン配布:**
- クエリ #1 → ローカルマシン
- クエリ #2 → リモートマシン1
- クエリ #3 → リモートマシン2
- クエリ #4 → リモートマシン3
- クエリ #5 → ローカルマシン(最初に戻る)

---

## 🔧 高度な設定

### `.ai_cluster_config` ファイル

セットアップ後、このファイルが設定と共に作成されます:

```bash
# ローカルマシン
LOCAL_LLAMA="/Users/user/modelo/llama.cpp/build/bin/llama-cli"
LOCAL_MODEL="/Users/user/modelo/mistral-7b.gguf"

# リモートマシン(カンマ区切り)
REMOTE_IPS="192.168.1.82,192.168.1.83"
REMOTE_USER="username"
REMOTE_LLAMA="/home/user/llama.cpp/build/bin/llama-cli"
REMOTE_MODEL="/home/user/mistral-7b.gguf"

# SSH接続間の遅延(秒)
REMOTE_DELAY=10
```

必要に応じて手動で編集できます。

---

## 📊 出力例

```
╔═══════════════════════════════════════════════════════════╗
║     🤖 AI クラスター - 分散AIシステム 🤖                  ║
║     ローカルネットワークを使用して並列処理               ║
╚═══════════════════════════════════════════════════════════╝

[17:30:00] 🎯 総クエリ数: 20
[i] 利用可能なマシン: 3 (ローカル1台 + リモート2台)

[17:30:00] 💻 [ローカル] クエリ #1: ニューラルネットワークとは...
[17:30:00] 🌐 [192.168.1.82] クエリ #2: 理論を要約...
[17:30:00] 🌐 [192.168.1.83] クエリ #3: 首都は...
[17:30:02] ✓ [ローカル] クエリ #1 完了
[17:30:15] ✓ [192.168.1.82] クエリ #2 完了
[17:30:18] ✓ [192.168.1.83] クエリ #3 完了

...

[17:35:00] ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[17:35:00] ✓ ✨ 完了
[17:35:00] ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[i] 処理済み総数: 20クエリ
[i] 結果の場所: results_cluster/
```

---

## 🐛 トラブルシューティング

### SSHが毎回パスワードを要求する

```bash
# ssh-copy-idを設定するためにsetupを再実行
./ai-cluster.sh setup
```

### リモートマシンで「llama-cli not found」

`.ai_cluster_config`のパスが正しいか確認:

```bash
# リモートマシンで実行:
which llama-cli
# または検索:
find ~ -name "llama-cli" 2>/dev/null
```

### クエリが処理されない

```bash
# 接続をテスト
./ai-cluster.sh test

# 個別ログを確認
cat results_cluster/result_2_*.txt
```

### Mac Miniでスクリプトが遅い

`.zshrc`の自動スクリプトがSSHを遅くする可能性があります。リモートマシンの`.zshrc`の先頭に追加:

```bash
# 非対話型SSHを無音化
[[ -n "$SSH_CONNECTION" ]] && [[ ! -t 0 ]] && return
```

---

## 🤝 貢献

貢献を歓迎します!

1. プロジェクトをフォーク
2. 機能ブランチを作成 (`git checkout -b feature/AmazingFeature`)
3. 変更をコミット (`git commit -m 'Add some AmazingFeature'`)
4. ブランチにプッシュ (`git push origin feature/AmazingFeature`)
5. プルリクエストを開く

---

## 📝 ロードマップ

- [ ] リアルタイムWebダッシュボード
- [ ] Dockerコンテナサポート
- [ ] ネットワークマシンの自動検出
- [ ] 結果キャッシング
- [ ] 優先順位システム
- [ ] パフォーマンスメトリクス
- [ ] Kubernetes統合

---

## 📄 ライセンス

MITライセンス - [LICENSE](LICENSE)ファイルを参照

---

## 👨‍💻 著者

**Gustavo Silva da Costa** (BiblioGalactic)

- GitHub: [@BiblioGalactic](https://github.com/BiblioGalactic)
- プロジェクト: 企業インフラに適用されたサイバーリアリズム

---

## 🙏 謝辞

- [llama.cpp](https://github.com/ggerganov/llama.cpp) - 推論エンジン
- [Anthropic Claude](https://claude.ai) - 開発支援
- ローカルAIオープンソースコミュニティ

---

## ⚠️ 免責事項

このソフトウェアは「現状のまま」提供され、保証はありません。使用は自己責任で行ってください。著者は、このソフトウェアの使用から生じるデータ損失、ハードウェアの故障、またはその他の損害について責任を負いません。

---

## 📚 リソース

- [llama.cppドキュメント](https://github.com/ggerganov/llama.cpp)
- [利用可能なGGUFモデル](https://huggingface.co/models?library=gguf)
- [パスワードなしSSH設定](https://www.ssh.com/academy/ssh/copy-id)

---

**このプロジェクトが役立つと思われた場合は、GitHubで ⭐ をお願いします**
