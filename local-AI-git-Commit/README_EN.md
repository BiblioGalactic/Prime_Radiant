Local Git Commit AI

Interactive Git Script with AI
Public and portable version to enhance your commits with artificial intelligence assistance.

⸻

🧑‍💻 Author

Gustavo Silva
Creation date: $(date +%F)

⸻

📌 Description

local-Commit.sh is an interactive Git script with AI that allows you to:
	•	Select files to add (all or individually, interactively using fzf).
	•	Capture your commit message and auto-curate it using an AI model.
	•	Verify that the curated commit does not change the original meaning using another AI model.
	•	Manually edit the curated commit before pushing.
	•	Automatically detect the main branch and safely push.
	•	Keep everything portable: the script will prompt for paths to llama-cli and .gguf models.

⸻

⚙️ Requirements
	•	Bash 5+
	•	Git
	•	timeout
	•	nl
	•	fzf
	•	llama-cli and .gguf models (for curation and verification)

⸻

📂 Installation
	1.	Clone this repository or download the script.
	2.	Make sure dependencies are installed (git, timeout, nl, fzf).
	3.	Prepare your .gguf models and compiled llama-cli.
	4.	Run:

chmod +x local-Commit.sh
./local-Commit.sh
