Local IA Modular Memory

English Version

Local IA Modular Memory is a public Bash script to generate and run a complete prompt with LLaMA from your Markdown notes. It concatenates all .md files in a directory, cleans them, and launches an interactive LLaMA session.

Features

Works with any directory of .md files.

Cleans whitespace and empty lines while preserving UTF-8.

Prompts for model path and llama-cli executable.

Optional dynamic state update before generating the prompt.

Usage

./local_ia_modular_memory.sh

Follow the prompts:

Enter your .md directory.

Enter your LLaMA model path (.gguf).

Enter the path to llama-cli.

The script will generate prompt_completo.txt and start an interactive LLaMA session.

Requirements

Bash >=5

LLaMA CLI installed

A local .gguf model

License

Open-source. Use freely, modify, and share.


