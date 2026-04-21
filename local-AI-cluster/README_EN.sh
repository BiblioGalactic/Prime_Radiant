#!/usr/bin/env bash
cat <<'EOF'
# 🤖 AI Cluster - Distributed AI System

**Process AI queries in parallel using multiple machines on your local network (intranet).**

No cloud • Private • Scalable • Open Source

---

## 📋 Description

AI Cluster is a system that allows you to leverage idle computers on a local network to run AI models in a distributed manner. Perfect for companies that want:

- ✅ **Total privacy** - Data never leaves your network
- ✅ **No cloud costs** - Use existing hardware
- ✅ **GDPR compliance** - Everything in your infrastructure
- ✅ **Scalable** - Add more machines easily
- ✅ **Parallel processing** - Queries executed simultaneously

---

## 🚀 Use Cases

### For Companies
- Process multiple AI queries using office PCs
- Distributed document analysis
- Parallel content generation
- Automation of repetitive tasks

### For Developers
- Experiment with distributed systems
- Learn about parallelization
- Test model performance
- Rapid solution prototyping

---

## 🎯 Features

- ✨ **Interactive wizard** - Step-by-step guided configuration
- 🔐 **Automatic SSH setup** - Configure passwordless connections
- 🌐 **Multi-machine** - Supports N computers on the network
- ⚖️ **Round-robin balancing** - Distributes load evenly
- 📊 **Detailed statistics** - Monitor processing
- 🛡️ **Robust error handling** - Continues even if a machine fails

---

## 📦 Requirements

### On ALL machines:

1. **llama.cpp compiled**
   ```bash
   git clone https://github.com/ggerganov/llama.cpp
   cd llama.cpp
   make
   ```

2. **GGUF model downloaded**
   - Mistral, Llama, Qwen, etc.
   - Located at the same path on all machines

3. **SSH active** (only on remote machines)
   ```bash
   # macOS
   sudo systemsetup -setremotelogin on
   
   # Linux
   sudo systemctl enable ssh
   sudo systemctl start ssh
   ```

---

## ⚙️ Installation

### 1. Download the script

```bash
# Clone the repository
git clone https://github.com/BiblioGalactic/ai-cluster
cd ai-cluster

# Or download directly
curl -O https://raw.githubusercontent.com/BiblioGalactic/ai-cluster/main/ai-cluster.sh
chmod +x ai-cluster.sh
```

### 2. Initial configuration

```bash
./ai-cluster.sh setup
```

The wizard will guide you through:
- ✅ Detect llama.cpp and local models
- ✅ Configure remote machine IPs
- ✅ Configure passwordless SSH
- ✅ Verify connectivity and files

---

## 📖 Usage

### Basic command

```bash
./ai-cluster.sh run queries.txt
```

### Queries file

Create a `queries.txt` file with your questions (one per line):

```
Explain what a neural network is
Summarize the theory of relativity
What is the capital of Japan?
Write a haiku about technology
```

### Other commands

```bash
# View current configuration
./ai-cluster.sh config

# Test connectivity
./ai-cluster.sh test

# Reconfigure
./ai-cluster.sh setup

# Help
./ai-cluster.sh help
```

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────┐
│           ai-cluster.sh (Orchestrator)          │
└─────────────┬───────────────────────────────────┘
              │
      ┌───────┴────────┬──────────────┬──────────┐
      │                │              │          │
  ┌───▼────┐      ┌───▼────┐    ┌───▼────┐ ┌───▼────┐
  │ Local  │      │ PC 1   │    │ PC 2   │ │ PC N   │
  │ (Mac)  │      │ (SSH)  │    │ (SSH)  │ │ (SSH)  │
  └────────┘      └────────┘    └────────┘ └────────┘
  Query 1,5,9     Query 2,6,10  Query 3,7  Query 4,8
```

**Round-robin distribution:**
- Query #1 → Local Machine
- Query #2 → Remote Machine 1
- Query #3 → Remote Machine 2
- Query #4 → Remote Machine 3
- Query #5 → Local Machine (returns to start)

---

## 🔧 Advanced Configuration

### `.ai_cluster_config` file

After setup, this file is created with your configuration:

```bash
# Local Machine
LOCAL_LLAMA="/Users/user/modelo/llama.cpp/build/bin/llama-cli"
LOCAL_MODEL="/Users/user/modelo/mistral-7b.gguf"

# Remote Machines (comma-separated)
REMOTE_IPS="192.168.1.82,192.168.1.83"
REMOTE_USER="username"
REMOTE_LLAMA="/home/user/llama.cpp/build/bin/llama-cli"
REMOTE_MODEL="/home/user/mistral-7b.gguf"

# Delay between SSH connections (seconds)
REMOTE_DELAY=10
```

You can edit it manually if needed.

---

## 📊 Example Output

```
╔═══════════════════════════════════════════════════════════╗
║     🤖 AI CLUSTER - Distributed AI System 🤖              ║
║   Process queries in parallel using your local network   ║
╚═══════════════════════════════════════════════════════════╝

[17:30:00] 🎯 Total queries: 20
[i] Available machines: 3 (1 local + 2 remote)

[17:30:00] 💻 [Local] Query #1: Explain what a neural network is...
[17:30:00] 🌐 [192.168.1.82] Query #2: Summarize the theory...
[17:30:00] 🌐 [192.168.1.83] Query #3: What is the capital...
[17:30:02] ✓ [Local] Query #1 completed
[17:30:15] ✓ [192.168.1.82] Query #2 completed
[17:30:18] ✓ [192.168.1.83] Query #3 completed

...

[17:35:00] ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[17:35:00] ✓ ✨ COMPLETED
[17:35:00] ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[i] Total processed: 20 queries
[i] Results in: results_cluster/
```

---

## 🐛 Troubleshooting

### SSH asks for password every time

```bash
# Run setup again to configure ssh-copy-id
./ai-cluster.sh setup
```

### "llama-cli not found" on remote machine

Verify the path in `.ai_cluster_config` is correct:

```bash
# On the remote machine, run:
which llama-cli
# Or search:
find ~ -name "llama-cli" 2>/dev/null
```

### Queries not processing

```bash
# Test connectivity
./ai-cluster.sh test

# Check individual logs
cat results_cluster/result_2_*.txt
```

### Slow script on Mac Mini

Automatic scripts in `.zshrc` can slow down SSH. Add to the beginning of `.zshrc` on remote machines:

```bash
# Silence for non-interactive SSH
[[ -n "$SSH_CONNECTION" ]] && [[ ! -t 0 ]] && return
```

---

## 🤝 Contributing

Contributions are welcome!

1. Fork the project
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📝 Roadmap

- [ ] Real-time web dashboard
- [ ] Docker container support
- [ ] Auto-detection of network machines
- [ ] Result caching
- [ ] Priority system
- [ ] Performance metrics
- [ ] Kubernetes integration

---

## 📄 License

MIT License - see [LICENSE](LICENSE) file

---

## 👨‍💻 Author

**Gustavo Silva da Costa** (BiblioGalactic)

- GitHub: [@BiblioGalactic](https://github.com/BiblioGalactic)
- Project: Cyberrealism applied to corporate infrastructure

---

## 🙏 Acknowledgments

- [llama.cpp](https://github.com/ggerganov/llama.cpp) - Inference engine
- [Anthropic Claude](https://claude.ai) - Development assistance
- Local AI open source community

---

## ⚠️ Disclaimer

This software is provided "as is", without warranties. Use at your own risk. The authors are not responsible for data loss, hardware malfunction, or any damage derived from the use of this software.

---

## 📚 Resources

- [llama.cpp Documentation](https://github.com/ggerganov/llama.cpp)
- [Available GGUF models](https://huggingface.co/models?library=gguf)
- [Passwordless SSH configuration](https://www.ssh.com/academy/ssh/copy-id)

---

**If you find this project useful, give it a ⭐ on GitHub**
EOF
