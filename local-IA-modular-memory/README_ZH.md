
本地模块化 AI 内存

本地模块化 AI 内存是一个公共 Bash 脚本，用于根据你的 Markdown 笔记生成并执行完整的 LLaMA 提示。它会将目录下的所有 .md 文件合并、清理，并启动一个交互式的 LLaMA 会话。

⸻

功能
	•	支持任意 .md 文件目录
	•	清理空格和空行，同时保持 UTF-8 编码
	•	提示输入模型路径和 llama-cli 可执行文件路径
	•	可选动态更新，在生成提示前更新内容

⸻

使用方法

./local_ia_modular_memory.sh

按照提示操作：
	1.	输入包含 .md 文件的目录
	2.	输入 LLaMA 模型路径（.gguf 文件）
	3.	输入 llama-cli 可执行文件路径

脚本会生成 prompt_completo.txt 并启动交互式 LLaMA 会话。

⸻

系统要求
	•	Bash >= 5
	•	已安装 LLaMA CLI
	•	本地 GGUF 模型

⸻

