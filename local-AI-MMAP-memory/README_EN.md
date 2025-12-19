Local AI MMAP Memory


Local AI MMAP Memory is a public Bash + C launcher to run LLaMA with multiple modular prompts loaded directly into memory using mmap. Each profile represents a different AI context (technical, philosophical, security, etc.), allowing efficient prompt handling without creating temporary files.

Features

Load multiple .txt profiles in memory.

Select active profile at runtime.

Runs LLaMA interactively with context loaded via mmap.

Portable and open-source: users input their own paths.

Error handling for file access, mmap, and LLaMA launch.

Usage

./local-AI-MMAP-memory.sh

Follow the prompts to:

Enter your prompt file (.txt)

Enter the path to llama-cli

Enter your .gguf model path

Enter comma-separated profile paths

Choose the active profile index

Requirements

Bash >=5

GCC

LLaMA CLI installed

Local .gguf model

License

Open-source. Use freely, modify, and share.


