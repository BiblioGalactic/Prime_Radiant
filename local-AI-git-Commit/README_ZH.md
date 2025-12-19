
本地 Git Commit AI

带 AI 的交互式 Git 脚本
公共可移植版本，用于使用人工智能增强你的提交信息。

⸻

🧑‍💻 作者

Gustavo Silva
创建日期: $(date +%F)

⸻

📌 描述

local-Commit.sh 是一个 带 AI 的交互式 Git 脚本，它可以：
	•	选择要添加的文件（全部或单个，可通过 fzf 交互式选择）。
	•	捕获你的提交信息，并使用 AI 模型 自动优化。
	•	使用另一个 AI 模型验证优化后的提交 不改变原始含义。
	•	在推送前手动编辑优化后的提交信息。
	•	自动检测主分支并安全 推送。
	•	保持脚本 可移植：脚本会提示输入 llama-cli 和 .gguf 模型的路径。

⸻

⚙️ 系统要求
	•	Bash 5+
	•	Git
	•	timeout
	•	nl
	•	fzf
	•	llama-cli 和 .gguf 模型（用于优化与验证）

⸻

📂 安装
	1.	克隆此仓库或下载脚本。
	2.	确保已安装依赖项（git、timeout、nl、fzf）。
	3.	准备好你的 .gguf 模型和已编译的 llama-cli。
	4.	执行：

chmod +x local-Commit.sh
./local-Commit.sh
