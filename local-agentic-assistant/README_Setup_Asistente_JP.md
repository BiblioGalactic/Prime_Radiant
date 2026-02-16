🤖 ローカル強化型 AI アシスタントセットアップ

説明

自動化インストールシステムで、ローカル AI アシスタントに高度なエージェント機能を提供します。このスクリプトは完全な開発環境を構築し、ローカルの LLaMA モデルと連携して、コード解析、ファイル管理、システムコマンドの実行機能を提供します。

主な特徴

🧠 スマートエージェントモード
	•	自動計画：複雑なタスクを具体的なサブタスクに分解
	•	自動ファイル読み取り：プロジェクト関連ファイルを自動分析
	•	冗長性なしの統合：複数の分析結果を統合し、重複情報を排除
	•	品質検証：回答品質の自動チェックシステム

🔧 高度な機能
	•	50+ コマンド対応：Git、Docker、NPM、Python など
	•	危険コマンド防止：統合セキュリティシステム
	•	スマートファイル管理：ファイルの読み書きとコード解析
	•	適応型設定：環境に応じて自動調整

🎯 モジュール化アーキテクチャ
	•	コア：アシスタントのメインエンジン
	•	LLM クライアント：llama.cpp モデルとの通信
	•	ファイルマネージャ：安全なファイル管理
	•	コマンドランナー：コマンド実行を制御
	•	エージェント拡張：高度なエージェント機能

システム要件
	•	Python 3.11+
	•	llama.cpp コンパイル済みで動作可能
	•	GGUF モデル互換
	•	Bash 4.0+
	•	OS：macOS、Linux

インストール

1. ダウンロードとインストール

# スクリプトをダウンロード
curl -O https://raw.githubusercontent.com/tu-usuario/setup-asistente/main/setup_asistente.sh

# 実行権限を付与
chmod +x setup_asistente.sh

# インストールを実行
./setup_asistente.sh

2. インタラクティブ設定

スクリプトは以下を入力するよう求めます：
	•	インストールディレクトリ：プロジェクトをインストールする場所
	•	GGUF モデルパス：ローカル言語モデル
	•	llama-cli パス：llama.cpp のバイナリ

3. 生成されるディレクトリ構造

asistente-ia/
├── src/
│   ├── core/              # メインエンジン
│   ├── llm/               # LLM クライアント
│   ├── file_ops/          # ファイル管理
│   └── commands/          # コマンド実行
├── config/                # 設定
├── tools/                 # 追加ツール
├── tests/                 # システムテスト
├── logs/                  # ログ
└── examples/              # 使用例

使用方法

基本コマンド

# 通常アシスタント
claudia "このプロジェクトを説明して"

# エージェントモード
claudia-a "アーキテクチャを完全解析"

# verbose モード（内部処理を確認）
claudia-deep "エラーの詳細調査"

# ヘルプ
claudia-help

エージェントコマンド例
	•	"コード構造を完全に解析"
	•	"パフォーマンスを詳細調査"
	•	"エージェントモード：全コードを最適化"
	•	"エラーを詳細に検証"

インタラクティブモード

claudia
💬 > agentic on
💬 > このプロジェクトを完全解析
💬 > exit

高度設定

設定ファイル

{
  "llm": {
    "model_path": "/あなたの/モデルパス/modelo.gguf",
    "llama_bin": "/あなたの/llama-cliパス",
    "max_tokens": 1024,
    "temperature": 0.7
  },
  "assistant": {
    "safe_mode": false,
    "backup_files": true,
    "supported_extensions": [".py", ".js", ".json", ".md"]
  }
}

カスタマイズ
	•	モデル：config/settings.json でモデルパスを変更
	•	コマンド：commands/runner.py で許可するコマンドを変更
	•	ファイルタイプ：新しい対応ファイルタイプを追加

システムアーキテクチャ

コアコンポーネント
	1.	LocalAssistant：全コンポーネントを統括
	2.	AgenticAssistant：エージェント機能拡張
	3.	LlamaClient：llama.cpp モデルとのインターフェース
	4.	FileManager：プロジェクトファイルの安全管理
	5.	CommandRunner：システムコマンドの制御実行

エージェントフロー
	1.	計画：タスクをサブタスクに分解
	2.	実行：強化コンテキストでサブタスクを実行
	3.	統合：結果を統合し冗長性を排除
	4.	検証：最終回答の品質をチェック

セキュリティ

禁止コマンド
	•	rm, rmdir, dd, shred
	•	sudo, su, chmod, chown
	•	kill, reboot, shutdown

許可コマンド
	•	開発ツール：git, npm, pip, docker
	•	ファイル解析：cat, grep, find, head, tail
	•	コンパイル：make, cmake, gradle, maven

トラブルシューティング

エラー：“llama-cli が見つかりません”

# llama.cpp のインストール確認
which llama-cli

# 設定パスを更新
vim config/settings.json

エラー：“モデルが見つかりません”

# モデルパスを確認
ls -la /あなたの/モデルパス/modelo.gguf

# 設定を更新
claudia --config config/settings.json

エージェントモードが動作しない

# verbose モードを確認
claudia-deep "簡単なテスト"

# ログを確認
tail -f logs/assistant.log

貢献
	1.	リポジトリをフォーク
	2.	新機能ブランチ作成：git checkout -b feature/nueva-funcionalidad
	3.	変更をコミット：git commit -am '新機能を追加'
	4.	ブランチをプッシュ：git push origin feature/nueva-funcionalidad
	5.	プルリクエストを作成

ライセンス

MIT License - 詳細は LICENSE ファイルを参照

著者

Gustavo Silva da Costa (Eto Demerzel)

バージョン

2.0.0 - スマートエージェント強化システム、スマート計画と冗長性なし統合対応

⸻

