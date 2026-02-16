🤖 本地 AI 助手安装 - 基础配置器

描述

这是一个自动安装脚本，用于配置基础本地 AI 助手，使用 llama.cpp 模型。该安装器设计简单、直观、易用，为与本地语言模型交互提供了稳固的基础。

主要特性

🔧 简单直观的配置
	•	引导安装：交互式分步配置
	•	自动验证：检查先决条件和路径有效性
	•	自适应配置：适应不同环境
	•	模块化结构：组织良好且可扩展

🎯 核心功能
	•	LLM 客户端：直接与 llama.cpp 通信
	•	文件管理器：安全的读写操作
	•	命令执行器：受控执行系统命令
	•	灵活配置：可通过 JSON 文件配置

📁 模块化架构

src/
├── core/           # 助手主引擎
├── llm/            # llama.cpp 客户端
├── file_ops/       # 文件管理
└── commands/       # 命令执行

系统要求
	•	Python 3.11+
	•	已编译的 llama.cpp
	•	兼容 GGUF 模型
	•	Python pip3
	•	操作系统：macOS, Linux

快速安装

1. 下载与运行

# 下载脚本
curl -O https://raw.githubusercontent.com/tu-usuario/asistente-basico/main/setup_asistente_basico.sh

# 添加执行权限
chmod +x setup_asistente_basico.sh

# 执行安装
./setup_asistente_basico.sh

2. 交互式配置

脚本将提示你输入：

项目目录：

项目目录 [/Users/tu-usuario/asistente-ia]: 

GGUF 模型路径：

GGUF 模型路径 [/Users/tu-usuario/modelo/modelo.gguf]: 

llama-cli 路径：

llama.cpp 路径 [/Users/tu-usuario/llama.cpp/build/bin/llama-cli]: 

3. 确认

已选择配置：
项目目录: /Users/tu-usuario/asistente-ia
模型: /Users/tu-usuario/modelo/modelo.gguf
Llama.cpp: /Users/tu-usuario/llama.cpp/build/bin/llama-cli

是否继续此配置？ (y/N)

生成的目录结构

asistente-ia/
├── src/
│   ├── main.py                 # 主入口
│   ├── core/
│   │   ├── assistant.py        # 主助手类
│   │   └── config.py           # 配置管理
│   ├── llm/
│   │   └── client.py           # llama.cpp 客户端
│   ├── file_ops/
│   │   └── manager.py          # 文件管理
│   └── commands/
│       └── runner.py           # 命令执行
├── config/
│   └── settings.json           # 主配置文件
├── tools/                      # 附加工具
├── tests/                      # 系统测试
├── logs/                       # 日志文件
└── examples/                   # 示例

基本使用

主命令

cd /路径/到/你的/asistente-ia
python3 src/main.py "列出项目中有哪些 Python 文件？"

交互模式

python3 src/main.py
🤖 本地 AI 助手 - 交互模式
输入 'exit' 退出，输入 'help' 获取帮助

💬 > 解释 main.py 文件
🤖 main.py 是主入口文件...

💬 > exit
再见！👋

命令行参数

# 使用自定义配置
python3 src/main.py --config config/custom.json "分析此项目"

# verbose 模式
python3 src/main.py --verbose "列出所有 Python 文件"

# 帮助
python3 src/main.py --help

配置

配置文件 (config/settings.json)

{
  "llm": {
    "model_path": "/路径/到/你的/modelo.gguf",
    "llama_bin": "/路径/到/llama-cli",
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

LLM 参数自定义
	•	max_tokens：响应最大长度
	•	temperature：创造性（0.0=确定性, 1.0=创造性）
	•	model_path：GGUF 模型路径
	•	llama_bin：llama-cli 二进制路径

安全配置
	•	safe_mode：启用命令安全模式
	•	backup_files：修改前创建备份
	•	max_file_size：处理文件的最大大小
	•	supported_extensions：支持的文件类型

核心功能

1. 文件分析

python3 src/main.py "解释 config.py 文件的功能"

2. 文件列表

python3 src/main.py "列出项目中所有 Python 文件"

3. 结构分析

python3 src/main.py "描述此项目的架构"

4. 代码帮助

python3 src/main.py "如何优化 load_config 函数？"

可用命令

帮助命令
	•	help - 显示完整帮助
	•	exit - 退出交互模式

查询示例
	•	“解释 X 文件”
	•	“列出 Y 类型文件”
	•	“描述项目结构”
	•	“类 Z 的作用”
	•	“函数 W 的功能”

验证与安全

自动验证
	•	✅ 检查 Python 3.11+
	•	✅ 检查 pip3
	•	✅ 验证 llama-cli 路径
	•	✅ 验证 GGUF 模型
	•	⚠️ 未找到文件的警告

安全模式

{
  "assistant": {
    "safe_mode": true,     
    "backup_files": true,  
    "max_file_size": 1048576
  }
}

扩展与自定义

添加新文件类型

{
  "assistant": {
    "supported_extensions": [".py", ".js", ".go", ".rust", ".cpp"]
  }
}

修改提示词

编辑 src/core/assistant.py 中的 _build_prompt() 方法：

def _build_prompt(self, context: Dict, user_input: str) -> str:
    prompt = f"""你是 {your_domain} 领域的专用助手。
    
    CONTEXT: {context}
    QUERY: {user_input}
    
    请以 {your_style} 风格回答。"""
    
    return prompt

添加新命令

修改 src/commands/runner.py 以包含新的允许命令：

self.safe_commands = {
    'ls', 'cat', 'grep', 'find',  
    'git', 'npm', 'pip',           
    'your_custom_command'          
}

故障排除

错误：“Python3 未安装”

# macOS
brew install python@3.11

# Ubuntu/Debian
sudo apt update && sudo apt install python3.11

错误：“llama-cli 未找到”

# 检查 llama.cpp 安装
ls -la /路径/到/llama.cpp/build/bin/llama-cli

# 更新配置路径
vim config/settings.json

错误：“模型未找到”

# 检查模型路径
ls -la /路径/到/你的/modelo.gguf

# 如有必要下载模型
wget https://huggingface.co/modelo/resolve/main/modelo.gguf

性能问题

{
  "llm": {
    "max_tokens": 512,      
    "temperature": 0.3      
  }
}

编辑器集成

VSCode

// tasks.json
{
    "label": "查询助手",
    "type": "shell",
    "command": "python3",
    "args": ["src/main.py", "${input:consulta}"],
    "group": "build"
}

Vim/NeoVim

" 快捷键调用助手
nnoremap <leader>ai :!python3 src/main.py "<C-R><C-W>"<CR>

贡献与开发

贡献流程
	1.	Fork 仓库
	2.	创建分支：git checkout -b feature/nueva-funcionalidad
	3.	在现有模块化架构中开发
	4.	在 tests/ 添加测试
	5.	在 examples/ 添加文档
	6.	创建 Pull Request

开发指南
	•	遵循现有模块化架构
	•	为新功能添加验证
	•	保持 JSON 配置兼容性
	•	包含适当的日志记录

许可证

MIT License

作者

Gustavo Silva da Costa (Eto Demerzel)

版本

1.0.0 - 基础配置器，模块化架构稳固

⸻

