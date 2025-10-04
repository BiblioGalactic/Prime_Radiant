🤖 ローカル AI アシスタント セットアップ - 基本構成

説明

このスクリプトは、llama.cpp モデルを使用する基本的なローカル AI アシスタントを自動的にセットアップするためのものです。シンプルで直感的、使いやすく設計されており、ローカル言語モデルとのやり取りに必要な堅牢な基盤を提供します。

主な特徴

🔧 シンプルで直感的な設定
	•	ガイド付きインストール：ステップごとの対話型設定
	•	自動検証：事前条件とパスの確認
	•	適応型設定：さまざまな環境に適応
	•	モジュラー構造：整理され拡張可能なアーキテクチャ

🎯 コア機能
	•	LLM クライアント：llama.cpp との直接通信
	•	ファイルマネージャー：安全な読み書き操作
	•	コマンド実行：システムコマンドを制御して実行
	•	柔軟な設定：JSON による構成可能

📁 モジュラーアーキテクチャ

src/
├── core/           # アシスタントのメインエンジン
├── llm/            # llama.cpp クライアント
├── file_ops/       # ファイル管理
└── commands/       # コマンド実行

システム要件
	•	Python 3.11+
	•	llama.cpp がコンパイル済みであること
	•	GGUF モデル対応
	•	Python 依存パッケージ用 pip3
	•	OS：macOS, Linux

クイックインストール

1. ダウンロードと実行

# スクリプトをダウンロード
curl -O https://raw.githubusercontent.com/tu-usuario/asistente-basico/main/setup_asistente_basico.sh

# 実行権限を付与
chmod +x setup_asistente_basico.sh

# インストールを実行
./setup_asistente_basico.sh

2. インタラクティブ設定

スクリプトは次を求めます：

プロジェクトディレクトリ：

プロジェクトディレクトリ [/Users/tu-usuario/asistente-ia]: 

GGUF モデルパス：

GGUF モデルパス [/Users/tu-usuario/modelo/modelo.gguf]: 

llama-cli パス：

llama.cpp パス [/Users/tu-usuario/llama.cpp/build/bin/llama-cli]: 

3. 確認

選択された設定：
プロジェクトディレクトリ: /Users/tu-usuario/asistente-ia
モデル: /Users/tu-usuario/modelo/modelo.gguf
Llama.cpp: /Users/tu-usuario/llama.cpp/build/bin/llama-cli

この設定で続行しますか？ (y/N)

生成されるディレクトリ構造

asistente-ia/
├── src/
│   ├── main.py                 # メインエントリポイント
│   ├── core/
│   │   ├── assistant.py        # アシスタント主要クラス
│   │   └── config.py           # 設定管理
│   ├── llm/
│   │   └── client.py           # llama.cpp クライアント
│   ├── file_ops/
│   │   └── manager.py          # ファイル管理
│   └── commands/
│       └── runner.py           # コマンド実行
├── config/
│   └── settings.json           # メイン設定ファイル
├── tools/                      # 追加ツール
├── tests/                      # システムテスト
├── logs/                       # ログファイル
└── examples/                   # 使用例

基本的な使用方法

メインコマンド

cd /path/to/your/asistente-ia
python3 src/main.py "このプロジェクトにある Python ファイルを表示してください"

インタラクティブモード

python3 src/main.py
🤖 ローカル AI アシスタント - インタラクティブモード
終了するには 'exit'、ヘルプは 'help'

💬 > main.py ファイルを説明して
🤖 main.py はメインエントリポイントです...

💬 > exit
さようなら！👋

コマンドラインパラメータ

# 特定の設定を使用
python3 src/main.py --config config/custom.json "このプロジェクトを分析する"

# verbose モード
python3 src/main.py --verbose "Python ファイル一覧"

# ヘルプ
python3 src/main.py --help

設定

設定ファイル (config/settings.json)

{
  "llm": {
    "model_path": "/path/to/your/modelo.gguf",
    "llama_bin": "/path/to/llama-cli",
    "max_tokens": 1024,
    "temperature": 0.7
  },
  "assistant": {
    "safe_mode": true,
    "backup_files": true,
    "max_file_size": 1048576,
    "supported_extensions": [".py", ".js", ".ts", ".json", ".md", ".txt", ".sh"]
  },
  "logging": {
    "level": "INFO",
    "file": "logs/assistant.log"
  }
}

LLM パラメータのカスタマイズ
	•	max_tokens：応答の最大長
	•	temperature：創造性（0.0=決定論、1.0=創造的）
	•	model_path：GGUF モデルのパス
	•	llama_bin：llama-cli バイナリのパス

セキュリティ設定
	•	safe_mode：コマンドの安全モードを有効化
	•	backup_files：変更前にバックアップ作成
	•	max_file_size：処理可能な最大ファイルサイズ
	•	supported_extensions：対応ファイルタイプ

主な機能

1. ファイル分析

python3 src/main.py "config.py の機能を説明してください"

2. ファイル一覧

python3 src/main.py "プロジェクト内のすべての Python ファイルを表示"

3. 構造分析

python3 src/main.py "このプロジェクトの構造を説明してください"

4. コードヘルプ

python3 src/main.py "load_config 関数を改善するには？"

利用可能なコマンド

ヘルプコマンド
	•	help - 完全なヘルプを表示
	•	exit - インタラクティブモードを終了

クエリ例
	•	“X ファイルを説明”
	•	“Y タイプのファイルを一覧”
	•	“プロジェクト構造を説明”
	•	“Z クラスの機能”
	•	“W 関数の動作”

バリデーションとセキュリティ

自動検証
	•	✅ Python 3.11+ の確認
	•	✅ pip3 の確認
	•	✅ llama-cli パスの検証
	•	✅ GGUF モデルの検証
	•	⚠️ ファイル未検出の警告

セーフモード

{
  "assistant": {
    "safe_mode": true,
    "backup_files": true,
    "max_file_size": 1048576
  }
}

拡張とカスタマイズ

新しいファイルタイプの追加

{
  "assistant": {
    "supported_extensions": [".py", ".js", ".go", ".rust", ".cpp"]
  }
}

プロンプトの編集

src/core/assistant.py の _build_prompt() メソッドを編集：

def _build_prompt(self, context: Dict, user_input: str) -> str:
    prompt = f"""あなたは {your_domain} 専門のアシスタントです。
    
    CONTEXT: {context}
    QUERY: {user_input}
    
    {your_style} スタイルで回答してください。"""
    
    return prompt

新しいコマンドの追加

src/commands/runner.py を編集して許可コマンドを追加：

self.safe_commands = {
    'ls', 'cat', 'grep', 'find',  
    'git', 'npm', 'pip',           
    'your_custom_command'          
}

トラブルシューティング

エラー：“Python3 がインストールされていません”

# macOS
brew install python@3.11

# Ubuntu/Debian
sudo apt update && sudo apt install python3.11

エラー：“llama-cli が見つかりません”

# llama.cpp のインストール確認
ls -la /path/to/llama.cpp/build/bin/llama-cli

# 設定パスを更新
vim config/settings.json

エラー：“モデルが見つかりません”

# モデルパスを確認
ls -la /path/to/your/modelo.gguf

# 必要に応じてダウンロード
wget https://huggingface.co/modelo/resolve/main/modelo.gguf

パフォーマンス問題

{
  "llm": {
    "max_tokens": 512,      
    "temperature": 0.3      
  }
}

エディタ統合

VSCode

// tasks.json
{
    "label": "アシスタントに問い合わせ",
    "type": "shell",
    "command": "python3",
    "args": ["src/main.py", "${input:consulta}"],
    "group": "build"
}

Vim/NeoVim

" アシスタント呼び出し用マッピング
nnoremap <leader>ai :!python3 src/main.py "<C-R><C-W>"<CR>

貢献と開発

貢献の手順
	1.	リポジトリをフォーク
	2.	ブランチを作成：git checkout -b feature/nueva-funcionalidad
	3.	既存のモジュラー構造で開発
	4.	tests/ にテストを追加
	5.	examples/ にドキュメントを追加
	6.	プルリクエストを作成

開発ガイド
	•	既存のモジュラー構造に従う
	•	新機能用の検証を追加
	•	JSON 設定との互換性を維持
	•	適切なログ記録を含める

ライセンス

MIT License

著者

Gustavo Silva da Costa (Eto Demerzel)

バージョン

1.0.0 - 基本構成器、堅牢なモジュラーアーキテクチャ

⸻

