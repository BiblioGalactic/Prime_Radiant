⚡ Prime Radiant - 本地 AI 助手集合

🧠 我使用本地 AI 自动化复杂的想法。从 Bash，为人类而生。

⸻

🌟 Prime Radiant 是什么

Prime Radiant 是一套用于本地 AI 的工具和配置集合。本仓库包含通过 llama.cpp 使用本地语言模型自动化任务的脚本和系统。

🎯 项目理念
	•	本地优先：所有 AI 在你的机器上运行
	•	以 Bash 为中心：强大且透明的脚本
	•	迭代改进：每次实验持续改进

⸻

📦 包含的工具

🤖 本地 AI 助手

具备高级代理功能的配置工具
	•	本地 AI 助手的自动安装
	•	智能规划的代理模式
	•	安全的文件和代码管理

./setup_asistente.sh

⚔️ Local-CROS（交叉参考优化系统）

多模型评估系统
	•	比较多个 LLaMA 模型的回答
	•	自动交叉评估
	•	智能回答合成

./local-cros.sh "在此输入你的问题"


⸻

🚀 快速开始

前提条件
	•	llama.cpp 已编译并可用
	•	GGUF 模型（Mistral、LLaMA 等）
	•	macOS/Linux 上的 Bash 4.0+

基本安装

git clone https://github.com/BiblioGalactic/Prime_Radiant.git
cd Prime_Radiant

# 查看可用工具
ls -la

配置
	1.	安装 llama.cpp：

git clone https://github.com/ggerganov/llama.cpp.git
cd llama.cpp
make

	2.	下载 GGUF 模型：

wget https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.1-GGUF/resolve/main/mistral-7b-instruct-v0.1.Q6_K.gguf


⸻

🛠️ 工具目录

工具	目的	状态
本地 AI 助手	完整的代理助手	✅ 稳定
Local-CROS	模型比较工具	✅ 稳定


⸻

🎭 设计理念

为什么选择 Bash
	•	透明性：每条命令都可查看
	•	可移植性：适用于 Unix 系统
	•	简单性：无复杂依赖

为什么选择本地
	•	隐私：数据保留在你的设备上
	•	控制权：可自由选择使用的模型
	•	成本：无 API 限制或费用

⸻

📄 许可证

MIT 许可证 - 免费使用并需注明作者

作者

Gustavo Silva da Costa (Eto Demerzel)
🔗 BiblioGalactic

⸻

“最有价值的知识，是你可以控制、改进并自由分享的。”
— Eto Demerzel, Prime Radiant
