🤖 本地增强型 AI 助手安装

描述

自动化安装系统，用于本地 AI 助手，具备高级代理能力。本脚本配置了完整的开发环境，可与本地 LLaMA 模型交互，提供代码分析、文件管理及系统命令执行功能。

主要特性

🧠 智能代理模式
	•	自动规划：将复杂任务分解为具体子任务
	•	自动读取文件：自动分析项目相关文件
	•	无冗余综合：合并多个分析结果，消除重复信息
	•	质量验证：自动回答质量控制系统

🔧 高级功能
	•	50+ 已启用命令：Git、Docker、NPM、Python 等
	•	危险命令防护：集成安全系统
	•	智能文件管理：文件读取、写入与代码分析
	•	自适应配置：根据环境自动调整

🎯 模块化架构
	•	核心：助手主引擎
	•	LLM 客户端：与 llama.cpp 模型通信
	•	文件管理器：安全管理文件
	•	命令执行器：控制命令执行
	•	代理扩展：高级代理功能

系统要求
	•	Python 3.11+
	•	llama.cpp 已编译并可用
	•	兼容 GGUF 模型
	•	Bash 4.0+
	•	操作系统：macOS、Linux

安装

1. 下载与安装

# 下载脚本
curl -O https://raw.githubusercontent.com/tu-usuario/setup-asistente/main/setup_asistente.sh

# 赋予执行权限
chmod +x setup_asistente.sh

# 执行安装
./setup_asistente.sh

2. 交互式配置

脚本会提示你输入：
	•	安装目录：项目将安装的位置
	•	GGUF 模型路径：你的本地语言模型
	•	llama-cli 路径：llama.cpp 可执行文件

3. 生成的目录结构

asistente-ia/
├── src/
│   ├── core/              # 主引擎
│   ├── llm/               # LLM 客户端
│   ├── file_ops/          # 文件管理
│   └── commands/          # 命令执行
├── config/                # 配置
├── tools/                 # 附加工具
├── tests/                 # 系统测试
├── logs/                  # 日志
└── examples/              # 使用示例

使用方法

基本命令

# 普通助手
claudia "解释此项目"

# 代理模式
claudia-a "完整分析架构"

# verbose 模式（查看内部流程）
claudia-deep "深入研究错误"

# 完整帮助
claudia-help

代理命令示例
	•	"完整分析代码结构"
	•	"深入研究性能问题"
	•	"代理模式：优化全部代码"
	•	"详细检查错误"

交互模式

claudia
💬 > agentic on
💬 > 完整分析此项目
💬 > exit

高级配置

配置文件

{
  "llm": {
    "model_path": "/你的/模型路径/modelo.gguf",
    "llama_bin": "/你的/llama-cli路径",
    "max_tokens": 1024,
    "temperature": 0.7
  },
  "assistant": {
    "safe_mode": false,
    "backup_files": true,
    "supported_extensions": [".py", ".js", ".json", ".md"]
  }
}

个性化
	•	模型：在 config/settings.json 修改模型路径
	•	命令：在 commands/runner.py 修改允许的命令列表
	•	文件类型：添加支持的新文件类型

系统架构

核心组件
	1.	LocalAssistant：协调所有组件的主类
	2.	AgenticAssistant：提供代理功能扩展
	3.	LlamaClient：与 llama.cpp 模型接口
	4.	FileManager：项目文件安全管理
	5.	CommandRunner：系统命令受控执行

代理流程
	1.	规划：将任务拆解为子任务
	2.	执行：在增强上下文中执行子任务
	3.	综合：合并结果，消除冗余
	4.	验证：检查最终回答质量

安全

禁止命令
	•	rm、rmdir、dd、shred
	•	sudo、su、chmod、chown
	•	kill、reboot、shutdown

允许命令
	•	开发工具：git、npm、pip、docker
	•	文件分析：cat、grep、find、head、tail
	•	编译：make、cmake、gradle、maven

故障排除

错误：“llama-cli 未找到”

# 检查 llama.cpp 安装
which llama-cli

# 更新配置路径
vim config/settings.json

错误：“模型未找到”

# 检查模型路径
ls -la /你的/模型路径/modelo.gguf

# 更新配置
claudia --config config/settings.json

代理模式无法工作

# 检查 verbose 模式
claudia-deep "简单测试"

# 查看日志
tail -f logs/assistant.log

贡献
	1.	Fork 仓库
	2.	为新功能创建分支：git checkout -b feature/nueva-funcionalidad
	3.	提交更改：git commit -am '添加新功能'
	4.	推送分支：git push origin feature/nueva-funcionalidad
	5.	创建 Pull Request

许可

MIT License - 详情见 LICENSE 文件

作者

Gustavo Silva da Costa (Eto Demerzel)

版本

2.0.0 - 智能代理增强系统，支持智能规划和无冗余综合

⸻

