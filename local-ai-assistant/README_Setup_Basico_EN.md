# 🤖 Local AI Assistant Setup - Basic Configurator

## Description

Automated installation script to configure a basic Local AI Assistant that uses llama.cpp models. This installer is designed to be simple, straightforward, and easy to use, providing a solid foundation for interacting with local language models.

## Key Features

### 🔧 Simple and Intuitive Configuration
- **Guided installation**: Interactive step-by-step configuration
- **Automatic validation**: Verification of prerequisites and paths
- **Adaptive configuration**: Adjusts to different environments
- **Modular structure**: Organized and extensible architecture

### 🎯 Core Functionalities
- **LLM Client**: Direct communication with llama.cpp
- **File Manager**: Safe read/write operations
- **Command Executor**: Controlled system execution
- **Flexible Configuration**: Configurable JSON

### 📁 Modular Architecture
```
src/
├── core/           # Main assistant engine
├── llm/            # Client for llama.cpp
├── file_ops/       # File management
└── commands/       # Command execution
```

## System Requirements

- **Python 3.11+**
- **llama.cpp** compiled
- **GGUF model** compatible
- **pip3** for Python dependencies
- **Operating System**: macOS, Linux

## Quick Installation

### 1. Download and Execute
```bash
# Download the script
curl -O https://raw.githubusercontent.com/your-user/basic-assistant/main/setup_asistente_basico.sh

# Make executable
chmod +x setup_asistente_basico.sh

# Run installation
./setup_asistente_basico.sh
```

### 2. Interactive Configuration

The script will request:

**Project directory:**
```
Project directory [/Users/your-user/asistente-ia]: 
```

**GGUF model path:**
```
GGUF model path [/Users/your-user/modelo/modelo.gguf]: 
```

**llama-cli path:**
```
llama.cpp path [/Users/your-user/llama.cpp/build/bin/llama-cli]: 
```

### 3. Confirmation
```
Selected configuration:
Project directory: /Users/your-user/asistente-ia
Model: /Users/your-user/modelo/modelo.gguf
Llama.cpp: /Users/your-user/llama.cpp/build/bin/llama-cli

Continue with this configuration? (y/N)
```

## Generated Structure

```
asistente-ia/
├── src/
│   ├── main.py                 # Main entry point
│   ├── core/
│   │   ├── assistant.py        # Main assistant class
│   │   └── config.py          # Configuration management
│   ├── llm/
│   │   └── client.py          # llama.cpp client
│   ├── file_ops/
│   │   └── manager.py         # File management
│   └── commands/
│       └── runner.py          # Command execution
├── config/
│   └── settings.json          # Main configuration
├── tools/                     # Additional tools
├── tests/                     # System tests
├── logs/                      # Log files
└── examples/                  # Usage examples
```

## Basic Usage

### Main Command
```bash
cd /path/to/your/asistente-ia
python3 src/main.py "What Python files are in this project?"
```

### Interactive Mode
```bash
python3 src/main.py
🤖 Local AI Assistant - Interactive mode
Type 'exit' to quit, 'help' for help

💬 > explain the main.py file
🤖 The main.py file is the entry point...

💬 > exit
See you later! 👋
```

### Command Line Parameters
```bash
# Use specific configuration
python3 src/main.py --config config/custom.json "analyze this project"

# Verbose mode
python3 src/main.py --verbose "list Python files"

# Help
python3 src/main.py --help
```

## Configuration

### Configuration File (config/settings.json)
```json
{
  "llm": {
    "model_path": "/path/to/your/model.gguf",
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
```

### LLM Parameter Customization
- **max_tokens**: Maximum response length
- **temperature**: Creativity (0.0 = deterministic, 1.0 = creative)
- **model_path**: Path to your GGUF model
- **llama_bin**: Path to llama-cli binary

### Security Configuration
- **safe_mode**: Enable safe mode for commands
- **backup_files**: Create backups before modifying
- **max_file_size**: Maximum file size to process
- **supported_extensions**: Supported file types

## Main Functionalities

### 1. File Analysis
```bash
python3 src/main.py "explain what the config.py file does"
```

### 2. File Listing
```bash
python3 src/main.py "show all Python files in the project"
```

### 3. Structure Analysis
```bash
python3 src/main.py "describe the architecture of this project"
```

### 4. Code Help
```bash
python3 src/main.py "how can I improve the load_config function?"
```

## Available Commands

### Help Commands
- `help` - Show complete help
- `exit` - Exit interactive mode

### Example Queries
- "explain file X"
- "list files of type Y"
- "describe project structure"
- "how does class Z work"
- "what does function W do"

## Validations and Security

### Automatic Validations
- ✅ Python 3.11+ verification
- ✅ pip3 verification
- ✅ llama-cli path validation
- ✅ GGUF model validation
- ⚠️ Warnings for files not found

### Safe Mode
```json
{
  "assistant": {
    "safe_mode": true,     // Command restrictions
    "backup_files": true,  // Automatic backups
    "max_file_size": 1048576  // 1MB limit per file
  }
}
```

## Extension and Customization

### Add New File Types
```json
{
  "assistant": {
    "supported_extensions": [".py", ".js", ".go", ".rust", ".cpp"]
  }
}
```

### Modify Prompts
Edit `src/core/assistant.py` in the `_build_prompt()` method:

```python
def _build_prompt(self, context: Dict, user_input: str) -> str:
    prompt = f"""You are an assistant specialized in {your_domain}.
    
    CONTEXT: {context}
    QUERY: {user_input}
    
    Respond in a {your_style} manner."""
    
    return prompt
```

### Add New Commands
Modify `src/commands/runner.py` to include new allowed commands:

```python
self.safe_commands = {
    'ls', 'cat', 'grep', 'find',  # Basic
    'git', 'npm', 'pip',          # Development
    'your_custom_command'         # New command
}
```

## Troubleshooting

### Error: "Python3 not installed"
```bash
# macOS
brew install python@3.11

# Ubuntu/Debian
sudo apt update && sudo apt install python3.11
```

### Error: "llama-cli not found"
```bash
# Verify llama.cpp installation
ls -la /path/to/llama.cpp/build/bin/llama-cli

# Update path in configuration
vim config/settings.json
```

### Error: "Model not found"
```bash
# Verify model
ls -la /path/to/your/model.gguf

# Download model if necessary
wget https://huggingface.co/model/resolve/main/model.gguf
```

### Performance Issues
```json
{
  "llm": {
    "max_tokens": 512,      // Reduce for faster responses
    "temperature": 0.3      // Less creativity = faster
  }
}
```

## Editor Integration

### VSCode
```json
// tasks.json
{
    "label": "Query Assistant",
    "type": "shell",
    "command": "python3",
    "args": ["src/main.py", "${input:query}"],
    "group": "build"
}
```

### Vim/NeoVim
```vim
" Mapping to query assistant
nnoremap <leader>ai :!python3 src/main.py "<C-R><C-W>"<CR>
```

## Contributing and Development

### Structure for Contributing
1. Fork the repository
2. Create branch: `git checkout -b feature/new-functionality`
3. Develop within existing modular architecture
4. Add tests in `tests/`
5. Document in `examples/`
6. Create Pull Request

### Development Guide
- Follow existing modular architecture
- Add validations for new functionalities
- Maintain JSON configuration compatibility
- Include appropriate logging

## License

MIT License

## Author

**Gustavo Silva da Costa (Eto Demerzel)**

## Version

**1.0.0** - Basic configurator with solid modular architecture

---

*A simple yet powerful local AI assistant to enhance your development workflow.*
