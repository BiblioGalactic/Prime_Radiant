⚡ Prime Radiant - ローカル AI アシスタントコレクション

🧠 複雑なアイデアをローカル AI で自動化します。Bash から、人のために。

⸻

🌟 Prime Radiantとは

Prime Radiant は、ローカル AI を活用するためのツールと設定のコレクションです。このリポジトリには、llama.cpp を通じてローカル言語モデルを使用し、タスクを自動化するスクリプトやシステムが含まれています。

🎯 プロジェクト哲学
	•	ローカル第一: すべての AI はあなたのマシン上で動作
	•	Bash 中心: 強力で透明性の高いスクリプト
	•	反復的改善: 実験ごとに継続的に改善

⸻

📦 含まれるツール

🤖 ローカル AI アシスタント

高度なエージェント機能を持つ設定ツール
	•	ローカル AI アシスタントの自動インストール
	•	インテリジェントプランニング付きエージェントモード
	•	安全なファイル・コード管理

./setup_asistente.sh

⚔️ Local-CROS（クロス参照最適化）

マルチモデル評価システム
	•	複数の LLaMA モデルの応答を比較
	•	自動クロス評価
	•	インテリジェントな応答の統合

./local-cros.sh "ここに質問を入力"


⸻

🚀 クイックスタート

前提条件
	•	llama.cpp がコンパイル済みで動作可能
	•	GGUF モデル（Mistral、LLaMA など）
	•	macOS/Linux 上で Bash 4.0+

基本インストール

git clone https://github.com/BiblioGalactic/Prime_Radiant.git
cd Prime_Radiant

# 利用可能なツールを確認
ls -la

設定
	1.	llama.cpp をインストール：

git clone https://github.com/ggerganov/llama.cpp.git
cd llama.cpp
make

	2.	GGUF モデルをダウンロード：

wget https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.1-GGUF/resolve/main/mistral-7b-instruct-v0.1.Q6_K.gguf


⸻

🛠️ ツールカタログ

ツール	目的	ステータス
ローカル AI アシスタント	完全なエージェントアシスタント	✅ 安定
Local-CROS	モデル比較ツール	✅ 安定


⸻

🎭 デザイン哲学

なぜ Bash なのか
	•	透明性: すべてのコマンドを確認可能
	•	移植性: Unix 系システムで動作
	•	シンプルさ: 複雑な依存関係なし

なぜローカルなのか
	•	プライバシー: データはマシン内に留まる
	•	コントロール: 使用するモデルを自分で選択
	•	コスト: API制限や料金なし

⸻

📄 ライセンス

MIT ライセンス - 表示ありで自由に使用可能

作者

Gustavo Silva da Costa (Eto Demerzel)
🔗 BiblioGalactic

⸻

“最も価値のある知識とは、自分で制御し、改善し、自由に共有できるものだ。”
— Eto Demerzel, Prime Radiant
