#!/usr/bin/env bash
cat <<'EOF'
# 🤖 AI 集群 - 分布式人工智能系统

**使用本地网络(内网)上的多台机器并行处理AI查询。**

无需云服务 • 私密 • 可扩展 • 开源

---

## 📋 描述

AI Cluster 是一个系统,允许您利用本地网络上的闲置计算机以分布式方式运行AI模型。非常适合需要以下功能的企业:

- ✅ **完全隐私** - 数据永不离开您的网络
- ✅ **无云成本** - 使用现有硬件
- ✅ **符合GDPR** - 一切都在您的基础设施中
- ✅ **可扩展** - 轻松添加更多机器
- ✅ **并行处理** - 同时执行查询

---

## 🚀 用例

### 企业应用
- 使用办公室PC处理多个AI查询
- 分布式文档分析
- 并行内容生成
- 重复任务自动化

### 开发者应用
- 实验分布式系统
- 学习并行化
- 测试模型性能
- 快速解决方案原型

---

## 🎯 特性

- ✨ **交互式向导** - 逐步引导配置
- 🔐 **自动SSH设置** - 配置无密码连接
- 🌐 **多机器支持** - 支持网络上的N台计算机
- ⚖️ **轮询负载均衡** - 均匀分配负载
- 📊 **详细统计** - 监控处理过程
- 🛡️ **健壮的错误处理** - 即使某台机器失败也能继续

---

## 📦 要求

### 所有机器上:

1. **编译的llama.cpp**
   ```bash
   git clone https://github.com/ggerganov/llama.cpp
   cd llama.cpp
   make
   ```

2. **下载的GGUF模型**
   - Mistral, Llama, Qwen等
   - 在所有机器上位于相同路径

3. **激活SSH** (仅远程机器)
   ```bash
   # macOS
   sudo systemsetup -setremotelogin on
   
   # Linux
   sudo systemctl enable ssh
   sudo systemctl start ssh
   ```

---

## ⚙️ 安装

### 1. 下载脚本

```bash
# 克隆仓库
git clone https://github.com/BiblioGalactic/ai-cluster
cd ai-cluster

# 或直接下载
curl -O https://raw.githubusercontent.com/BiblioGalactic/ai-cluster/main/ai-cluster.sh
chmod +x ai-cluster.sh
```

### 2. 初始配置

```bash
./ai-cluster.sh setup
```

向导将引导您完成:
- ✅ 检测llama.cpp和本地模型
- ✅ 配置远程机器IP
- ✅ 配置无密码SSH
- ✅ 验证连接和文件

---

## 📖 使用

### 基本命令

```bash
./ai-cluster.sh run queries.txt
```

### 查询文件

创建一个`queries.txt`文件,每行一个问题:

```
解释什么是神经网络
总结相对论
日本的首都是什么?
写一首关于技术的俳句
```

### 其他命令

```bash
# 查看当前配置
./ai-cluster.sh config

# 测试连接
./ai-cluster.sh test

# 重新配置
./ai-cluster.sh setup

# 帮助
./ai-cluster.sh help
```

---

## 🏗️ 架构

```
┌─────────────────────────────────────────────────┐
│           ai-cluster.sh (协调器)                 │
└─────────────┬───────────────────────────────────┘
              │
      ┌───────┴────────┬──────────────┬──────────┐
      │                │              │          │
  ┌───▼────┐      ┌───▼────┐    ┌───▼────┐ ┌───▼────┐
  │ 本地   │      │ PC 1   │    │ PC 2   │ │ PC N   │
  │ (Mac)  │      │ (SSH)  │    │ (SSH)  │ │ (SSH)  │
  └────────┘      └────────┘    └────────┘ └────────┘
  查询1,5,9       查询2,6,10     查询3,7     查询4,8
```

**轮询分配:**
- 查询 #1 → 本地机器
- 查询 #2 → 远程机器1
- 查询 #3 → 远程机器2
- 查询 #4 → 远程机器3
- 查询 #5 → 本地机器(返回开始)

---

## 🔧 高级配置

### `.ai_cluster_config` 文件

设置后,将创建此配置文件:

```bash
# 本地机器
LOCAL_LLAMA="/Users/user/modelo/llama.cpp/build/bin/llama-cli"
LOCAL_MODEL="/Users/user/modelo/mistral-7b.gguf"

# 远程机器(逗号分隔)
REMOTE_IPS="192.168.1.82,192.168.1.83"
REMOTE_USER="username"
REMOTE_LLAMA="/home/user/llama.cpp/build/bin/llama-cli"
REMOTE_MODEL="/home/user/mistral-7b.gguf"

# SSH连接之间的延迟(秒)
REMOTE_DELAY=10
```

如需要可手动编辑。

---

## 📊 输出示例

```
╔═══════════════════════════════════════════════════════════╗
║     🤖 AI 集群 - 分布式人工智能系统 🤖                     ║
║     使用本地网络并行处理查询                              ║
╚═══════════════════════════════════════════════════════════╝

[17:30:00] 🎯 总查询数: 20
[i] 可用机器: 3 (1台本地 + 2台远程)

[17:30:00] 💻 [本地] 查询 #1: 解释什么是神经网络...
[17:30:00] 🌐 [192.168.1.82] 查询 #2: 总结理论...
[17:30:00] 🌐 [192.168.1.83] 查询 #3: 首都是什么...
[17:30:02] ✓ [本地] 查询 #1 完成
[17:30:15] ✓ [192.168.1.82] 查询 #2 完成
[17:30:18] ✓ [192.168.1.83] 查询 #3 完成

...

[17:35:00] ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[17:35:00] ✓ ✨ 完成
[17:35:00] ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[i] 总处理数: 20 个查询
[i] 结果位于: results_cluster/
```

---

## 🐛 故障排除

### SSH每次都要求密码

```bash
# 重新运行setup配置ssh-copy-id
./ai-cluster.sh setup
```

### 远程机器上"找不到llama-cli"

验证`.ai_cluster_config`中的路径是否正确:

```bash
# 在远程机器上运行:
which llama-cli
# 或搜索:
find ~ -name "llama-cli" 2>/dev/null
```

### 查询未处理

```bash
# 测试连接
./ai-cluster.sh test

# 检查单个日志
cat results_cluster/result_2_*.txt
```

### Mac Mini上脚本缓慢

`.zshrc`中的自动脚本可能会减慢SSH速度。在远程机器的`.zshrc`开头添加:

```bash
# 静默非交互式SSH
[[ -n "$SSH_CONNECTION" ]] && [[ ! -t 0 ]] && return
```

---

## 🤝 贡献

欢迎贡献!

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开 Pull Request

---

## 📝 路线图

- [ ] 实时Web仪表板
- [ ] Docker容器支持
- [ ] 自动检测网络机器
- [ ] 结果缓存
- [ ] 优先级系统
- [ ] 性能指标
- [ ] Kubernetes集成

---

## 📄 许可证

MIT许可证 - 请参阅 [LICENSE](LICENSE) 文件

---

## 👨‍💻 作者

**Gustavo Silva da Costa** (BiblioGalactic)

- GitHub: [@BiblioGalactic](https://github.com/BiblioGalactic)
- 项目: 网络现实主义应用于企业基础设施

---

## 🙏 致谢

- [llama.cpp](https://github.com/ggerganov/llama.cpp) - 推理引擎
- [Anthropic Claude](https://claude.ai) - 开发协助
- 本地AI开源社区

---

## ⚠️ 免责声明

本软件按"原样"提供,不提供任何保证。使用风险自负。作者不对数据丢失、硬件故障或使用本软件导致的任何损害负责。

---

## 📚 资源

- [llama.cpp 文档](https://github.com/ggerganov/llama.cpp)
- [可用的GGUF模型](https://huggingface.co/models?library=gguf)
- [无密码SSH配置](https://www.ssh.com/academy/ssh/copy-id)

---

**如果您觉得这个项目有用,请在GitHub上给它一个 ⭐**
EOF
