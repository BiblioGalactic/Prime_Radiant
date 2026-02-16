# 🤖 Advanced Local AI Assistant Setup

## Description

Automated installation system for a Local AI Assistant with advanced agentic capabilities. This script sets up a complete development environment to interact with local LLaMA models, providing code analysis, file management, and system command execution functionalities.

## Key Features

### 🧠 Intelligent Agentic Mode
- **Automatic planning**: Breaks down complex tasks into specific subtasks
- **Automatic file reading**: Automatically analyzes relevant project files
- **Non-redundant synthesis**: Combines multiple analyses while eliminating repeated information
- **Quality verification**: Automated quality control system for responses

### 🔧 Advanced Functionalities
- **50+ enabled commands**: Git, Docker, NPM, Python, and more
- **Protection against dangerous commands**: Integrated security system
- **Intelligent file management**: Code reading, writing, and analysis
- **Adaptive configuration**: Automatically adjusts to environment

### 🎯 Modular Architecture
- **Core**: Main assistant engine
- **LLM Client**: Communication with llama.cpp models
- **File Manager**: Safe file management
- **Command Runner**: Controlled command execution
- **Agentic Extension**: Advanced agentic capabilities

## System Requirements

- **Python 3.11+**
- **llama.cpp** compiled and functional
- **GGUF model** compatible
- **Bash 4.0+**
- **Operating System**: macOS, Linux

## Installation

### 1. Download and Installation
```bash
# Download the script
curl -O https://raw.githubusercontent.com/your-user/setup-assistant/main/setup_asistente.sh

# Make executable
chmod +x setup_asistente.sh

# Run installation
./setup_asistente.sh
```

### 2. Interactive Configuration
The script will ask for:
- **Installation directory**: Where the project will be installed
- **GGUF model path**: Your local language model
- **llama-cli path**: llama.cpp binary

### 3. Generated Structure
```
asistente-ia/
├── src/
│   ├── core/              # Main engine
│   ├── llm/               # LLM client
│   ├── file_ops/          # File management
│   └── commands/          # Command execution
├── config/                # Configuration
├── tools/                 # Additional tools
├── tests/                 # System tests
├── logs/                  # Execution logs
└── examples/              # Usage examples
```

## Usage

### Basic Commands
```bash
# Normal assistant
claudia "explain this project"

# Agentic mode
claudia-a "completely analyze the architecture"

# Verbose mode (see internal process)
claudia-deep "deep investigation of errors"

# Complete help
claudia-help
```

### Agentic Command Examples
- `"completely analyze the code structure"`
- `"deep investigation of performance"`
- `"agentic mode: optimize all code"`
- `"examine errors in detail"`

### Interactive Mode
```bash
claudia
💬 > agentic on
💬 > completely analyze this project
💬 > exit
```

## Advanced Configuration

### Configuration File
```json
{
  "llm": {
    "model_path": "/path/to/your/model.gguf",
    "llama_bin": "/path/to/llama-cli",
    "max_tokens": 1024,
    "temperature": 0.7
  },
  "assistant": {
    "safe_mode": false,
    "backup_files": true,
    "supported_extensions": [".py", ".js", ".json", ".md"]
  }
}
```

### Customization
- **Models**: Change model path in `config/settings.json`
- **Commands**: Modify allowed commands list in `commands/runner.py`
- **Extensions**: Add new supported file types

## System Architecture

### Main Components

1. **LocalAssistant**: Main class that coordinates all components
2. **AgenticAssistant**: Extension providing agentic capabilities
3. **LlamaClient**: Interface with llama.cpp models
4. **FileManager**: Safe project file management
5. **CommandRunner**: Controlled system command execution

### Agentic Flow

1. **Planning**: Breaks down task into specific subtasks
2. **Execution**: Executes each subtask with enriched context
3. **Synthesis**: Combines results eliminating redundancies
4. **Verification**: Validates final response quality

## Security

### Forbidden Commands
- `rm`, `rmdir`, `dd`, `shred`
- `sudo`, `su`, `chmod`, `chown`
- `kill`, `reboot`, `shutdown`

### Allowed Commands
- Development tools: `git`, `npm`, `pip`, `docker`
- File analysis: `cat`, `grep`, `find`, `head`, `tail`
- Compilation: `make`, `cmake`, `gradle`, `maven`

## Troubleshooting

### Error: "llama-cli not found"
```bash
# Verify llama.cpp installation
which llama-cli

# Update path in config
vim config/settings.json
```

### Error: "Model not found"
```bash
# Verify model path
ls -la /path/to/your/model.gguf

# Update configuration
claudia --config config/settings.json
```

### Agentic Mode Not Working
```bash
# Check verbose mode
claudia-deep "simple test"

# View logs
tail -f logs/assistant.log
```

## Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature/new-functionality`
3. Commit changes: `git commit -am 'Add new functionality'`
4. Push to branch: `git push origin feature/new-functionality`
5. Create Pull Request

## License

MIT License - See LICENSE file for details.

## Author

**Gustavo Silva da Costa (Eto Demerzel)**

## Version

**2.0.0** - Improved agentic system with intelligent planning and non-redundant synthesis.

---

*For additional support, create an issue in the project repository.*
