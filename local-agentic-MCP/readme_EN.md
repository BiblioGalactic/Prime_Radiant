# 🤖 MCP Local - AI Chat with System Tools

> **Complete Model Context Protocol system with 11 tools and agentic mode for your local AI**

```
╔════════════════════════════════════════════════════════════╗
║                                                            ║
║       Transform your local LLM into a powerful assistant   ║
║       with access to your operating system                 ║
║                                                            ║
╚════════════════════════════════════════════════════════════╝
```

---

## 📋 Table of Contents

- [What is this?](#-what-is-this)
- [Features](#-features)
- [Requirements](#-requirements)
- [Installation](#-installation)
- [Basic Usage](#-basic-usage)
- [Agentic Mode](#-agentic-mode)
- [The 11 Tools](#-the-11-tools)
- [Practical Examples](#-practical-examples)
- [Advanced Configuration](#-advanced-configuration)
- [Troubleshooting](#-troubleshooting)
- [Architecture](#-architecture)
- [Credits](#-credits)

---

## 🎯 What is this?

**MCP Local** is a system that connects your local language model (like Mistral, Llama, etc.) with **real tools from your operating system**.

### Without MCP:
```
👤 User: "List my Python files"
🤖 AI: "Sorry, I cannot access your file system"
```

### With MCP:
```
👤 User: "List my Python files"
🤖 AI: [SEARCH] ✓
       Found 12 files: main.py, utils.py, config.py...
```

**It's like giving hands to your AI so it can interact with your computer** 🦾

---

## ✨ Features

### 🔧 11 Complete Tools
- ✅ Read and write files
- ✅ Execute bash commands
- ✅ Navigate directories
- ✅ Search files and content
- ✅ Query HTTP APIs
- ✅ Download files from URLs
- ✅ Compress/decompress (zip, tar, tar.gz)
- ✅ Git operations (status, log, diff, branch)
- ✅ System monitoring (RAM, CPU, disk)
- ✅ Content search (grep)

### 🧠 Agentic Mode
**The star feature!** The AI can chain multiple actions automatically:

```
👤: "download the README from GitHub and compress all markdown files"

🤖 [AGENTIC MODE]
   📋 Plan: 3 steps
   🔄 Downloading... ✅
   🔄 Searching *.md... ✅  
   🔄 Compressing... ✅
   
   ✅ Downloaded README (3.4KB), found 5 markdown files
      and compressed them in docs.zip (45KB)
```

### 🔒 Built-in Security
- ❌ Dangerous commands blocked (rm, dd, sudo, etc.)
- 🛡️ Can only write in $HOME or /tmp
- ⏱️ Automatic timeouts
- 📦 File size limits (10MB)

### 🎨 User-Friendly Interface
- 💬 Interactive chat
- 📊 Verbose mode for debugging
- 🎯 Automatic agentic mode detection
- ⚡ Quick and clear responses

---

## 📦 Requirements

Before installing, make sure you have:

### Mandatory Requirements
```bash
✅ Python 3.8 or higher
✅ pip3
✅ A GGUF model (Mistral, Llama, etc.)
✅ llama.cpp compiled with llama-cli
```

### Optional Requirements
```bash
🔧 git (for Git tool)
🔧 curl/wget (already included in macOS/Linux)
```

### Operating System
- ✅ macOS (tested)
- ✅ Linux (tested)
- ⚠️ Windows (with WSL)

---

## 🚀 Installation

### Step 1: Download the installer

```bash
# Option A: Clone the repository
git clone https://github.com/your-repo/mcp-local.git
cd mcp-local

# Option B: Download the script directly
curl -O https://your-url/mcp_setup.sh
chmod +x mcp_setup.sh
```

### Step 2: Run the installer

```bash
./mcp_setup.sh
```

### Step 3: Configure paths

The installer will ask for two paths:

```
🎯 INITIAL CONFIGURATION
==========================================

📍 Step 1/2: Path to llama-cli executable
   Example: /usr/local/bin/llama-cli
   or: /Users/your-user/llama.cpp/build/bin/llama-cli
   Full path: _

📍 Step 2/2: Path to GGUF model
   Example: /Users/your-user/models/mistral-7b-instruct.gguf
   Full path: _
```

### Step 4: Automatic installation

The script will automatically:
1. ✅ Create Python virtual environment
2. ✅ Install dependencies (flask, psutil, requests)
3. ✅ Generate MCP server (11 tools)
4. ✅ Generate client with agentic mode
5. ✅ Save configuration

```
✅ INSTALLATION COMPLETED

╔════════════════════════════════════════╗
║     MCP LOCAL - MAIN MENU              ║
║     💪 11 Tools + Agentic              ║
╚════════════════════════════════════════╝

  1) 💬 Start chat (with agentic mode)
  2) 🔧 View MCP tools (11)
  3) ⚙️  Reconfigure paths
  4) 🚪 Exit
```

---

## 💬 Basic Usage

### Start the Chat

```bash
./mcp_setup.sh
# Select option 1) Start chat
```

### Chat Commands

```
👤 You: _

Available commands:
  agentic on/off  → Enable/disable agentic mode
  verbose on/off  → View detailed logs
  herramientas    → List the 11 tools
  salir           → Close chat
```

### Normal Conversation Example

```bash
👤 You: list the files on my desktop

🤖 AI: [LIST] ✓
   You have 23 items on your desktop: Documents/, Downloads/,
   image.png, notes.txt...

👤 You: how much free RAM do I have?

🤖 AI: [MEMORY] ✓
   You have 8.5GB of available RAM out of 16GB total (53% free)
```

---

## 🧠 Agentic Mode

Agentic mode allows the AI to **chain multiple actions automatically** without you having to give commands one by one.

### How to Activate?

**Option 1: Manual**
```bash
👤 You: agentic on
🤖 Agentic mode: ACTIVATED
```

**Option 2: Automatic** (detects these keywords)
- `and then`
- `after that`
- `and compress`
- `and search`
- `complete everything`
- `do everything`
- `automatic`

### Complete Example

#### Without Agentic Mode (3 separate commands):
```bash
👤: download the README
🤖: ✓

👤: search all markdown files
🤖: ✓

👤: compress the files
🤖: ✓
```

#### With Agentic Mode (1 single command):
```bash
👤: download the README from GitHub and then compress all markdown files

🤖 [AGENTIC MODE ACTIVATED]
📋 Plan: 3 steps

🔄 Step 1/3: DOWNLOAD:https://raw.githubusercontent.com/...
   ✅ DOWNLOAD

🔄 Step 2/3: SEARCH:~/Desktop:*.md
   ✅ SEARCH

🔄 Step 3/3: COMPRESS:compress:~/Desktop:~/Desktop/docs.zip
   ✅ COMPRESS

🔄 Synthesizing results...

✅ Task completed

🤖 Downloaded README (3456 bytes), found 5 markdown files 
   on your desktop and compressed them in docs.zip 
   (45KB total). All done!
```

### Verbose Mode (Debug)

To see the internal process:

```bash
👤 You: verbose on
📊 Verbose mode: ACTIVATED

👤 You: download X and compress Y

🧠 Planning steps...
📋 Planned steps: ["DOWNLOAD:...", "SEARCH:...", "COMPRESS:..."]
🔍 Executing: DOWNLOAD:https://...
   ✅ DOWNLOAD
🔍 Executing: SEARCH:~/Desktop:*.md
   ✅ SEARCH
...
```

---

## 🛠️ The 11 Tools

### 1. 📖 Read File
```bash
👤: read the README.md file
🤖: [READ] ✓
   The file contains documentation about...
```
- 📦 Maximum: 64KB
- 🔒 Text files only

### 2. ✍️ Write File
```bash
👤: create a test.txt file with "Hello World"
🤖: [WRITE] ✓ (11 bytes)
   File created at ~/test.txt
```
- 📦 Maximum: 10MB
- 🔒 Only in $HOME or /tmp
- 🔀 Modes: `w` (overwrite) or `a` (append)

### 3. 📁 List Directory
```bash
👤: what's in my Downloads folder?
🤖: [LIST] ✓
   45 items: documents/, images/, video.mp4...
```
- 📊 Shows: name, type, size, date
- 📦 Limit: 100 items

### 4. 🔍 Search Files
```bash
👤: find all my Python files
🤖: [SEARCH] ✓
   12 files found: main.py, utils.py...
```
- 🌲 Recursive search
- 🎯 Glob patterns: `*.py`, `test*.txt`, etc.
- 📦 Limit: 50 files

### 5. 🔎 Search in Content (Grep)
```bash
👤: search for "TODO" in Python files
🤖: [GREP] ✓ (8 matches)
   main.py:42: # TODO: Implement validation
   utils.py:15: # TODO: Optimize algorithm
```
- 📄 Files <1MB only
- 🎯 Case-insensitive regex
- 📦 Limit: 50 matches

### 6. ⚡ Execute Command
```bash
👤: execute ls -la
🤖: [COMMAND] ✓
   total 256
   drwxr-xr-x  15 user  staff   480 Oct 10 10:30 .
   ...
```
- ❌ **Blocked**: rm, dd, sudo, su, mkfs
- ⏱️ Timeout: 10 seconds
- 📦 Output: 4KB maximum

### 7. 💾 Query Memory
```bash
👤: how many resources do I have available?
🤖: [MEMORY] ✓
   RAM: 8.5GB free out of 16GB
   CPU: 35% usage (8 cores)
   Disk: 245GB free out of 500GB
```

### 8. 📥 Download File
```bash
👤: download https://example.com/file.pdf
🤖: [DOWNLOAD] ✓ (2.5MB)
   File saved at ~/Downloads/file.pdf
```
- 🌐 http:// and https:// only
- 📦 Limit: 10MB
- ⏱️ Timeout: 30 seconds

### 9. 🗜️ Compress/Decompress
```bash
👤: compress my documents folder
🤖: [COMPRESS] ✓
   Folder compressed in documents.zip (12MB)
```
- 📦 Formats: zip, tar, tar.gz
- 🔄 Operations: compress, decompress

### 10. 🔧 Git Operations
```bash
👤: show git status
🤖: [GIT] ✓
   On branch main
   Changes not staged for commit:
     modified: src/main.py
```
- ✅ Allowed: status, log, diff, branch, remote
- ❌ **Blocked**: commit, push, pull (read-only)

### 11. 🌐 Query API
```bash
👤: query the example.com API
🤖: [API] ✓ (200)
   Status: OK
   Response: {"data": "example"}
```
- 📡 Methods: GET, POST, PUT, DELETE, PATCH
- ⏱️ Timeout: 10 seconds
- 📦 Response: 4KB maximum

---

## 💡 Practical Examples

### Example 1: Project Analysis
```bash
👤: agentic on

👤: list all Python files and search for pending TODOs

🤖 [AGENTIC MODE]
   Step 1: Searching *.py... ✅
   Step 2: Searching 'TODO'... ✅
   
   Found 12 Python files with 8 pending TODOs:
   - main.py: 3 TODOs
   - utils.py: 2 TODOs
   - config.py: 3 TODOs
```

### Example 2: Automated Backup
```bash
👤: search all important files and compress them in a backup

🤖 [AGENTIC MODE]
   Step 1: Searching files... ✅
   Step 2: Compressing... ✅
   
   Created backup.zip with 45 files (234MB total)
```

### Example 3: System Monitoring
```bash
👤: show git status and system resources

🤖 [AGENTIC MODE]
   Step 1: Git status... ✅
   Step 2: Querying resources... ✅
   
   Git: 3 modified files on main branch
   System: RAM 45% free, CPU 25%, Disk 50% free
```

### Example 4: Complete Workflow
```bash
👤: download the README from GitHub, search it on my desktop 
    and compress all markdown files you find

🤖 [AGENTIC MODE]
   📋 Plan: 3 steps
   
   Step 1: Downloading from GitHub... ✅ (3.4KB)
   Step 2: Searching *.md on Desktop... ✅ (5 files)
   Step 3: Compressing files... ✅ (45KB)
   
   ✅ Downloaded README, found 5 markdown files and 
      compressed them in docs.zip. Everything is on your desktop.
```

---

## ⚙️ Advanced Configuration

### Change Model or llama-cli Path

```bash
./mcp_setup.sh
# Select option 3) Reconfigure paths
```

### Manual Configuration Edit

```bash
nano ~/.mcp_local/config.env
```

```bash
# MCP Local Configuration
LLAMA_CLI="/path/to/your/llama-cli"
MODELO_GGUF="/path/to/your/model.gguf"
```

### Environment Variables

```bash
# Enable MCP server debug
export MCP_DEBUG=1

# Run
./mcp_setup.sh
```

### File Structure

```
~/.mcp_local/
├── config.env           # Your configuration
├── venv/                # Python environment
├── mcp_server.py        # Server with 11 tools
└── chat_mcp.py          # Client with agentic mode
```

---

## 🔧 Troubleshooting

### Problem: "llama-cli not found"

**Solution:**
```bash
# Verify llama.cpp is compiled
cd ~/llama.cpp
cmake -B build
cmake --build build

# Verify path
ls ~/llama.cpp/build/bin/llama-cli

# Reconfigure MCP
./mcp_setup.sh
# Option 3) Reconfigure paths
```

### Problem: "Model not found"

**Solution:**
```bash
# Verify the model exists
ls ~/path/to/your/model.gguf

# If you don't have a model, download one
# Example: Mistral 7B
wget https://huggingface.co/...model.gguf

# Reconfigure
./mcp_setup.sh
# Option 3) Reconfigure paths
```

### Problem: "Error installing Python dependencies"

**Solution:**
```bash
# Verify Python
python3 --version  # Must be 3.8+

# Clean virtual environment
rm -rf ~/.mcp_local/venv

# Reinstall
./mcp_setup.sh
```

### Problem: "Agentic mode doesn't work well"

**Solution:**
```bash
# Use verbose mode to see what happens
👤: verbose on
👤: your problematic command

# Agentic mode depends on model quality
# Recommended models:
# - Mistral 7B Instruct (minimum)
# - Llama 3 8B Instruct (better)
# - Mixtral 8x7B (optimal)
```

### Problem: "Query timeout"

**Solution:**
```bash
# If the model is very slow, increase timeout
# Edit ~/.mcp_local/chat_mcp.py

# Line ~40:
IA_CMD = [
    config.get('LLAMA_CLI', 'llama-cli'),
    "--model", config.get('MODELO_GGUF', ''),
    "--n-predict", "512",
    "--temp", "0.7",
    "--ctx-size", "4096"
]

# Add GPU if available:
# "--n-gpu-layers", "35"
```

### Problem: "Command blocked for security"

**Solution:**
This is intentional. Dangerous commands are blocked:
- ❌ `rm -rf`
- ❌ `dd`
- ❌ `sudo`
- ❌ `su`

If you really need to execute privileged commands, do it manually outside of MCP.

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────┐
│           👤 User (YOU)                     │
└─────────────────┬───────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────┐
│      💬 Chat Client (chat_mcp.py)           │
│  ┌────────────────────────────────────┐     │
│  │  🧠 Agentic Mode                   │     │
│  │  - Step planning                   │     │
│  │  - Sequential execution            │     │
│  │  - Result synthesis                │     │
│  └────────────────────────────────────┘     │
└─────────────────┬───────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────┐
│        🤖 Local LLM Model                   │
│     (Mistral, Llama, Mixtral, etc.)         │
└─────────────────┬───────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────┐
│   🔧 MCP Server (mcp_server.py)             │
│  ┌────────────────────────────────────┐     │
│  │  11 Tools:                         │     │
│  │  ✓ Files (read/write)              │     │
│  │  ✓ System (memory/commands)        │     │
│  │  ✓ Network (API/downloads)         │     │
│  │  ✓ Search (files/content)          │     │
│  │  ✓ Utilities (git/compress)        │     │
│  └────────────────────────────────────┘     │
└─────────────────┬───────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────┐
│     💻 Your Operating System                │
│  (Files, Commands, Resources)               │
└─────────────────────────────────────────────┘
```

### Normal Query Flow

```
1. User types command
   👤 "list Python files"
   
2. Client queries LLM
   💬 → 🤖 "Which tool to use?"
   
3. LLM decides tool
   🤖 → 💬 "[USE_TOOL:SEARCH:.:*.py]"
   
4. Client calls MCP server
   💬 → 🔧 {"method": "search_files", ...}
   
5. Server executes tool
   🔧 → 💻 Real system search
   
6. Server returns results
   🔧 → 💬 {"result": ["main.py", ...]}
   
7. Client sends results to LLM
   💬 → 🤖 "Files found: ..."
   
8. LLM generates natural response
   🤖 → 💬 "Found 12 Python files: ..."
   
9. User sees response
   💬 → 👤 "Found 12 Python files: ..."
```

### Agentic Mode Flow

```
1. User gives complex command
   👤 "download X and then compress Y"
   
2. Client detects agentic mode
   💬 [Detects keywords "and then"]
   
3. LLM plans steps
   💬 → 🤖 "Break down into steps"
   🤖 → 💬 ["DOWNLOAD:...", "SEARCH:...", "COMPRESS:..."]
   
4. Client executes steps sequentially
   💬 → 🔧 Step 1: DOWNLOAD ✅
   💬 → 🔧 Step 2: SEARCH ✅
   💬 → 🔧 Step 3: COMPRESS ✅
   
5. LLM synthesizes results
   💬 → 🤖 "Summarize everything done"
   🤖 → 💬 "Downloaded, searched and compressed..."
   
6. User sees final summary
   💬 → 👤 "✅ Task completed: ..."
```

---

## 📚 Additional Resources

### Model Context Protocol (MCP)
- 📖 [MCP Specification](https://spec.modelcontextprotocol.io/)
- 🔗 [Anthropic MCP GitHub](https://github.com/anthropics/mcp)

### Recommended Models
- 🦙 [Llama 3 8B Instruct](https://huggingface.co/meta-llama/Meta-Llama-3-8B-Instruct)
- 🌟 [Mistral 7B Instruct](https://huggingface.co/mistralai/Mistral-7B-Instruct-v0.1)
- 🚀 [Mixtral 8x7B](https://huggingface.co/mistralai/Mixtral-8x7B-Instruct-v0.1)

### llama.cpp
- 🔗 [llama.cpp GitHub](https://github.com/ggerganov/llama.cpp)
- 📖 [Documentation](https://github.com/ggerganov/llama.cpp/blob/master/README.md)

---

## 🎓 Use Cases

### For Developers
- ✅ Automate repetitive tasks
- ✅ Analyze code and search TODOs
- ✅ Manage Git repositories
- ✅ Generate documentation
- ✅ Monitor system resources

### For System Administrators
- ✅ Automate backups
- ✅ Monitor logs
- ✅ Manage configuration files
- ✅ Search information in logs
- ✅ Compress/decompress files

### For Advanced Users
- ✅ Automatically organize files
- ✅ Download and process web content
- ✅ Search information in documents
- ✅ Automate complex workflows
- ✅ Integrate with external APIs

---

## 🤝 Contributing

Have ideas to improve MCP Local? Contribute!

### New Tool Ideas
- 📧 Email client
- 📅 Calendar integration
- 🗄️ Database operations
- 🐳 Docker integration
- 📊 Report generation

### How to Contribute
1. Fork the project
2. Create a branch (`git checkout -b feature/new-tool`)
3. Commit your changes (`git commit -am 'Add new tool X'`)
4. Push to the branch (`git push origin feature/new-tool`)
5. Open a Pull Request

---

## 📄 License

This project is under the MIT license. Use it freely, modify it, and share it.

```
MIT License

Copyright (c) 2025 Gustavo Silva Da Costa

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

---

## 🙏 Acknowledgments

- Anthropic for the Model Context Protocol concept
- llama.cpp community for making it possible to run LLMs locally
- Everyone who contributes to the open source AI ecosystem

---

## 📞 Support

Problems? Questions? Suggestions?

- 📧 Email: gsilvadacosta0@gmail.com 
- 🆇 Former Twitter 😂: https://x.com/bibliogalactic

---

<div align="center">

## ⭐ If you like this project, give it a star on GitHub ⭐

```
╔════════════════════════════════════════════════════════╗
║                                                        ║
║   Made with ❤️ for the local AI community             ║
║                                                        ║
║   "Giving hands to AIs, one tool at a time"           ║
║                                                        ║
╚════════════════════════════════════════════════════════╝
```

### 👨‍💻 Created by

**Gustavo Silva Da Costa** (Eto Demerzel) 🤫

🚀 *Transforming local AIs into powerful assistants*

</div>

---

**Version:** 1.0.0  
**Last updated:** October 2025  
**Status:** ✅ Production

---
