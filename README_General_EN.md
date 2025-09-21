# ⚡ Prime Radiant - Local AI Assistant Collection

> 🧠 **I automate complex ideas with local AI. From Bash, for humans.**

---

## 🌟 What is Prime Radiant

**Prime Radiant** is a collection of tools and configurations for working with local AI. This repository contains scripts and systems to automate tasks using local language models through llama.cpp.

### 🎯 Project Philosophy

- **Local First**: All AI runs on your machine
- **Bash Centered**: Powerful and transparent scripts
- **Iterative**: Continuous improvement with each experiment

---

## 📦 Included Tools

### 🤖 [Local AI Assistant](./local-ai-assistant/)
**Advanced configurator with agentic capabilities**

- Automated installation of local AI assistant
- Agent mode with intelligent planning
- Secure file and code management

```bash
./setup_asistente.sh
```

### ⚔️ [Local-CROS (Cross-Referential Optimization)](./local-agentic-asistant/)
**Cross-model evaluation system**

- Compares responses from multiple LLaMA models
- Automatic cross-evaluation
- Intelligent response synthesis

```bash
./local-cros.sh "Your question here"
```

---

## 🚀 Quick Start

### Prerequisites

- **llama.cpp** compiled and functional
- **GGUF models** (Mistral, LLaMA, etc.)
- **Bash 4.0+** on macOS/Linux

### Basic Installation

```bash
git clone https://github.com/BiblioGalactic/Prime_Radiant.git
cd Prime_Radiant

# Explore available tools
ls -la
```

### Configuration

1. **Install llama.cpp**:
```bash
git clone https://github.com/ggerganov/llama.cpp.git
cd llama.cpp
make
```

2. **Download GGUF models**:
```bash
wget https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.1-GGUF/resolve/main/mistral-7b-instruct-v0.1.Q6_K.gguf
```

---

## 🛠️ Tools Catalog

| Tool | Purpose | Status |
|-------------|-----------|--------|
| [Local AI Assistant](./local-ai-assistant/) | Complete agentic assistant | ✅ Stable |
| [Local-CROS](./local-agentic-asistant/) | Model comparator | ✅ Stable |

---

## 🎭 Design Philosophy

### Why Bash

- **Transparency**: You can read every command
- **Portability**: Works on Unix systems
- **Simplicity**: No complex dependencies

### Why Local

- **Privacy**: Your data stays on your machine
- **Control**: You decide which models to use
- **Cost**: No API limits or fees

---

## 📄 License

MIT License - Free use with attribution.

### Author

**Gustavo Silva da Costa (Eto Demerzel)**  
🔗 [BiblioGalactic](https://github.com/BiblioGalactic)

---

*"The most valuable knowledge is what you can control, improve, and share freely."*  
— Eto Demerzel, Prime Radiant
