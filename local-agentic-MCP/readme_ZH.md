# 🤖 MCP Local - 带系统工具的AI聊天

> **完整的模型上下文协议系统，包含11个工具和代理模式，适用于您的本地AI**

```
╔════════════════════════════════════════════════════════════╗
║                                                            ║
║       将您的本地LLM转变为功能强大的助手                       ║
║       可访问您的操作系统                                      ║
║                                                            ║
╚════════════════════════════════════════════════════════════╝
```

---

## 📋 目录

- [这是什么？](#-这是什么)
- [特性](#-特性)
- [要求](#-要求)
- [安装](#-安装)
- [基本使用](#-基本使用)
- [代理模式](#-代理模式)
- [11个工具](#-11个工具)
- [实用示例](#-实用示例)
- [高级配置](#-高级配置)
- [故障排除](#-故障排除)
- [架构](#-架构)
- [致谢](#-致谢)

---

## 🎯 这是什么？

**MCP Local** 是一个将您的本地语言模型（如Mistral、Llama等）与**操作系统的真实工具**连接起来的系统。

### 没有MCP：
```
👤 用户："列出我的Python文件"
🤖 AI："抱歉，我无法访问您的文件系统"
```

### 有了MCP：
```
👤 用户："列出我的Python文件"
🤖 AI：[搜索] ✓
       找到12个文件：main.py、utils.py、config.py...
```

**这就像给您的AI装上双手，让它能与您的计算机交互** 🦾

---

## ✨ 特性

### 🔧 11个完整工具
- ✅ 读写文件
- ✅ 执行bash命令
- ✅ 浏览目录
- ✅ 搜索文件和内容
- ✅ 查询HTTP API
- ✅ 从URL下载文件
- ✅ 压缩/解压缩（zip、tar、tar.gz）
- ✅ Git操作（status、log、diff、branch）
- ✅ 系统监控（RAM、CPU、磁盘）
- ✅ 内容搜索（grep）

### 🧠 代理模式
**明星功能！** AI可以自动链接多个操作：

```
👤："从GitHub下载README并压缩所有markdown文件"

🤖 [代理模式]
   📋 计划：3步
   🔄 下载中... ✅
   🔄 搜索*.md... ✅  
   🔄 压缩中... ✅
   
   ✅ 已下载README（3.4KB），找到5个markdown文件
      并压缩到docs.zip（45KB）
```

### 🔒 内置安全性
- ❌ 阻止危险命令（rm、dd、sudo等）
- 🛡️ 只能在$HOME或/tmp中写入
- ⏱️ 自动超时
- 📦 文件大小限制（10MB）

### 🎨 友好界面
- 💬 交互式聊天
- 📊 调试详细模式
- 🎯 自动检测代理模式
- ⚡ 快速清晰的响应

---

## 📦 要求

安装前，请确保您有：

### 必需要求
```bash
✅ Python 3.8或更高版本
✅ pip3
✅ GGUF模型（Mistral、Llama等）
✅ 编译了llama-cli的llama.cpp
```

### 可选要求
```bash
🔧 git（用于Git工具）
🔧 curl/wget（macOS/Linux已包含）
```

### 操作系统
- ✅ macOS（已测试）
- ✅ Linux（已测试）
- ⚠️ Windows（使用WSL）

---

## 🚀 安装

### 步骤1：下载安装程序

```bash
# 选项A：克隆仓库
git clone https://github.com/your-repo/mcp-local.git
cd mcp-local

# 选项B：直接下载脚本
curl -O https://your-url/mcp_setup.sh
chmod +x mcp_setup.sh
```

### 步骤2：运行安装程序

```bash
./mcp_setup.sh
```

### 步骤3：配置路径

安装程序将询问两个路径：

```
🎯 初始配置
==========================================

📍 步骤1/2：llama-cli可执行文件的路径
   示例：/usr/local/bin/llama-cli
   或：/Users/your-user/llama.cpp/build/bin/llama-cli
   完整路径：_

📍 步骤2/2：GGUF模型的路径
   示例：/Users/your-user/models/mistral-7b-instruct.gguf
   完整路径：_
```

### 步骤4：自动安装

脚本将自动：
1. ✅ 创建Python虚拟环境
2. ✅ 安装依赖项（flask、psutil、requests）
3. ✅ 生成MCP服务器（11个工具）
4. ✅ 生成带代理模式的客户端
5. ✅ 保存配置

```
✅ 安装完成

╔════════════════════════════════════════╗
║     MCP LOCAL - 主菜单                 ║
║     💪 11个工具 + 代理模式             ║
╚════════════════════════════════════════╝

  1) 💬 启动聊天（带代理模式）
  2) 🔧 查看MCP工具（11个）
  3) ⚙️  重新配置路径
  4) 🚪 退出
```

---

## 💬 基本使用

### 启动聊天

```bash
./mcp_setup.sh
# 选择选项1）启动聊天
```

### 聊天命令

```
👤 您：_

可用命令：
  agentic on/off  → 启用/禁用代理模式
  verbose on/off  → 查看详细日志
  herramientas    → 列出11个工具
  salir           → 关闭聊天
```

### 正常对话示例

```bash
👤 您：列出我桌面上的文件

🤖 AI：[列表] ✓
   您的桌面上有23个项目：Documents/、Downloads/、
   image.png、notes.txt...

👤 您：我有多少可用RAM？

🤖 AI：[内存] ✓
   您有8.5GB可用RAM，总共16GB（53%可用）
```

---

## 🧠 代理模式

代理模式允许AI**自动链接多个操作**，无需您逐个发出命令。

### 如何激活？

**选项1：手动**
```bash
👤 您：agentic on
🤖 代理模式：已激活
```

**选项2：自动**（检测这些关键词）
- `然后`
- `之后`
- `并压缩`
- `并搜索`
- `完成所有`
- `做所有`
- `自动`

### 完整示例

#### 没有代理模式（3个单独命令）：
```bash
👤：下载README
🤖：✓

👤：搜索所有markdown文件
🤖：✓

👤：压缩文件
🤖：✓
```

#### 有代理模式（1个命令）：
```bash
👤：从GitHub下载README然后压缩所有markdown文件

🤖 [代理模式已激活]
📋 计划：3步

🔄 步骤1/3：下载:https://raw.githubusercontent.com/...
   ✅ 下载

🔄 步骤2/3：搜索:~/Desktop:*.md
   ✅ 搜索

🔄 步骤3/3：压缩:compress:~/Desktop:~/Desktop/docs.zip
   ✅ 压缩

🔄 正在综合结果...

✅ 任务完成

🤖 已下载README（3456字节），在您的桌面上找到5个markdown文件
   并将它们压缩到docs.zip（总共45KB）。全部完成！
```

### 详细模式（调试）

查看内部流程：

```bash
👤 您：verbose on
📊 详细模式：已激活

👤 您：下载X并压缩Y

🧠 正在规划步骤...
📋 已规划步骤：["下载:...", "搜索:...", "压缩:..."]
🔍 正在执行：下载:https://...
   ✅ 下载
🔍 正在执行：搜索:~/Desktop:*.md
   ✅ 搜索
...
```

---

## 🛠️ 11个工具

### 1. 📖 读取文件
```bash
👤：读取README.md文件
🤖：[读取] ✓
   文件包含关于...的文档
```
- 📦 最大：64KB
- 🔒 仅文本文件

### 2. ✍️ 写入文件
```bash
👤：创建包含"Hello World"的test.txt文件
🤖：[写入] ✓（11字节）
   文件已创建在~/test.txt
```
- 📦 最大：10MB
- 🔒 仅在$HOME或/tmp中
- 🔀 模式：`w`（覆盖）或`a`（追加）

### 3. 📁 列出目录
```bash
👤：我的Downloads文件夹里有什么？
🤖：[列表] ✓
   45个项目：documents/、images/、video.mp4...
```
- 📊 显示：名称、类型、大小、日期
- 📦 限制：100个项目

### 4. 🔍 搜索文件
```bash
👤：找到我所有的Python文件
🤖：[搜索] ✓
   找到12个文件：main.py、utils.py...
```
- 🌲 递归搜索
- 🎯 Glob模式：`*.py`、`test*.txt`等
- 📦 限制：50个文件

### 5. 🔎 搜索内容（Grep）
```bash
👤：在Python文件中搜索"TODO"
🤖：[GREP] ✓（8个匹配）
   main.py:42: # TODO: 实现验证
   utils.py:15: # TODO: 优化算法
```
- 📄 仅<1MB的文件
- 🎯 不区分大小写的正则表达式
- 📦 限制：50个匹配

### 6. ⚡ 执行命令
```bash
👤：执行ls -la
🤖：[命令] ✓
   total 256
   drwxr-xr-x  15 user  staff   480 Oct 10 10:30 .
   ...
```
- ❌ **已阻止**：rm、dd、sudo、su、mkfs
- ⏱️ 超时：10秒
- 📦 输出：最大4KB

### 7. 💾 查询内存
```bash
👤：我有多少可用资源？
🤖：[内存] ✓
   RAM：16GB中有8.5GB可用
   CPU：35%使用率（8核）
   磁盘：500GB中有245GB可用
```

### 8. 📥 下载文件
```bash
👤：下载https://example.com/file.pdf
🤖：[下载] ✓（2.5MB）
   文件已保存在~/Downloads/file.pdf
```
- 🌐 仅http://和https://
- 📦 限制：10MB
- ⏱️ 超时：30秒

### 9. 🗜️ 压缩/解压缩
```bash
👤：压缩我的文档文件夹
🤖：[压缩] ✓
   文件夹已压缩到documents.zip（12MB）
```
- 📦 格式：zip、tar、tar.gz
- 🔄 操作：压缩、解压缩

### 10. 🔧 Git操作
```bash
👤：显示git状态
🤖：[GIT] ✓
   On branch main
   Changes not staged for commit:
     modified: src/main.py
```
- ✅ 允许：status、log、diff、branch、remote
- ❌ **已阻止**：commit、push、pull（只读）

### 11. 🌐 查询API
```bash
👤：查询example.com API
🤖：[API] ✓（200）
   状态：OK
   响应：{"data": "example"}
```
- 📡 方法：GET、POST、PUT、DELETE、PATCH
- ⏱️ 超时：10秒
- 📦 响应：最大4KB

---

## 💡 实用示例

### 示例1：项目分析
```bash
👤：agentic on

👤：列出所有Python文件并搜索待办TODO

🤖 [代理模式]
   步骤1：搜索*.py... ✅
   步骤2：搜索'TODO'... ✅
   
   找到12个Python文件，有8个待办TODO：
   - main.py：3个TODO
   - utils.py：2个TODO
   - config.py：3个TODO
```

### 示例2：自动备份
```bash
👤：搜索所有重要文件并将它们压缩到备份中

🤖 [代理模式]
   步骤1：搜索文件... ✅
   步骤2：压缩中... ✅
   
   已创建backup.zip，包含45个文件（总共234MB）
```

### 示例3：系统监控
```bash
👤：显示git状态和系统资源

🤖 [代理模式]
   步骤1：Git状态... ✅
   步骤2：查询资源... ✅
   
   Git：main分支上有3个修改的文件
   系统：RAM 45%可用，CPU 25%，磁盘50%可用
```

### 示例4：完整工作流
```bash
👤：从GitHub下载README，在我的桌面上搜索它
    并压缩您找到的所有markdown文件

🤖 [代理模式]
   📋 计划：3步
   
   步骤1：从GitHub下载... ✅（3.4KB）
   步骤2：在桌面上搜索*.md... ✅（5个文件）
   步骤3：压缩文件... ✅（45KB）
   
   ✅ 已下载README，找到5个markdown文件并
      将它们压缩到docs.zip。一切都在您的桌面上。
```

---

## ⚙️ 高级配置

### 更改模型或llama-cli路径

```bash
./mcp_setup.sh
# 选择选项3）重新配置路径
```

### 手动编辑配置

```bash
nano ~/.mcp_local/config.env
```

```bash
# MCP Local配置
LLAMA_CLI="/path/to/your/llama-cli"
MODELO_GGUF="/path/to/your/model.gguf"
```

### 环境变量

```bash
# 启用MCP服务器调试
export MCP_DEBUG=1

# 运行
./mcp_setup.sh
```

### 文件结构

```
~/.mcp_local/
├── config.env           # 您的配置
├── venv/                # Python环境
├── mcp_server.py        # 带11个工具的服务器
└── chat_mcp.py          # 带代理模式的客户端
```

---

## 🔧 故障排除

### 问题："未找到llama-cli"

**解决方案：**
```bash
# 验证llama.cpp已编译
cd ~/llama.cpp
cmake -B build
cmake --build build

# 验证路径
ls ~/llama.cpp/build/bin/llama-cli

# 重新配置MCP
./mcp_setup.sh
# 选项3）重新配置路径
```

### 问题："未找到模型"

**解决方案：**
```bash
# 验证模型存在
ls ~/path/to/your/model.gguf

# 如果没有模型，下载一个
# 示例：Mistral 7B
wget https://huggingface.co/...model.gguf

# 重新配置
./mcp_setup.sh
# 选项3）重新配置路径
```

### 问题："安装Python依赖项时出错"

**解决方案：**
```bash
# 验证Python
python3 --version  # 必须是3.8+

# 清理虚拟环境
rm -rf ~/.mcp_local/venv

# 重新安装
./mcp_setup.sh
```

### 问题："代理模式效果不佳"

**解决方案：**
```bash
# 使用详细模式查看发生了什么
👤：verbose on
👤：您的问题命令

# 代理模式取决于模型质量
# 推荐模型：
# - Mistral 7B Instruct（最低）
# - Llama 3 8B Instruct（更好）
# - Mixtral 8x7B（最佳）
```

### 问题："查询超时"

**解决方案：**
```bash
# 如果模型很慢，增加超时
# 编辑~/.mcp_local/chat_mcp.py

# 第~40行：
IA_CMD = [
    config.get('LLAMA_CLI', 'llama-cli'),
    "--model", config.get('MODELO_GGUF', ''),
    "--n-predict", "512",
    "--temp", "0.7",
    "--ctx-size", "4096"
]

# 如果有GPU，添加：
# "--n-gpu-layers", "35"
```

### 问题："命令因安全原因被阻止"

**解决方案：**
这是故意的。危险命令已被阻止：
- ❌ `rm -rf`
- ❌ `dd`
- ❌ `sudo`
- ❌ `su`

如果您确实需要执行特权命令，请在MCP外部手动执行。

---

## 🏗️ 架构

```
┌─────────────────────────────────────────────┐
│           👤 用户（您）                      │
└─────────────────┬───────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────┐
│      💬 聊天客户端（chat_mcp.py）           │
│  ┌────────────────────────────────────┐     │
│  │  🧠 代理模式                       │     │
│  │  - 步骤规划                        │     │
│  │  - 顺序执行                        │     │
│  │  - 结果综合                        │     │
│  └────────────────────────────────────┘     │
└─────────────────┬───────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────┐
│        🤖 本地LLM模型                       │
│     （Mistral、Llama、Mixtral等）          │
└─────────────────┬───────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────┐
│   🔧 MCP服务器（mcp_server.py）             │
│  ┌────────────────────────────────────┐     │
│  │  11个工具：                        │     │
│  │  ✓ 文件（读/写）                   │     │
│  │  ✓ 系统（内存/命令）               │     │
│  │  ✓ 网络（API/下载）                │     │
│  │  ✓ 搜索（文件/内容）               │     │
│  │  ✓ 实用工具（git/压缩）            │     │
│  └────────────────────────────────────┘     │
└─────────────────┬───────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────┐
│     💻 您的操作系统                         │
│  （文件、命令、资源）                       │
└─────────────────────────────────────────────┘
```

### 正常查询流程

```
1. 用户输入命令
   👤 "列出Python文件"
   
2. 客户端查询LLM
   💬 → 🤖 "使用哪个工具？"
   
3. LLM决定工具
   🤖 → 💬 "[使用工具:搜索:.:*.py]"
   
4. 客户端调用MCP服务器
   💬 → 🔧 {"method": "search_files", ...}
   
5. 服务器执行工具
   🔧 → 💻 真实系统搜索
   
6. 服务器返回结果
   🔧 → 💬 {"result": ["main.py", ...]}
   
7. 客户端将结果发送给LLM
   💬 → 🤖 "找到的文件：..."
   
8. LLM生成自然响应
   🤖 → 💬 "找到12个Python文件：..."
   
9. 用户看到响应
   💬 → 👤 "找到12个Python文件：..."
```

### 代理模式流程

```
1. 用户给出复杂命令
   👤 "下载X然后压缩Y"
   
2. 客户端检测代理模式
   💬 [检测关键词"然后"]
   
3. LLM规划步骤
   💬 → 🤖 "分解成步骤"
   🤖 → 💬 ["下载:...", "搜索:...", "压缩:..."]
   
4. 客户端顺序执行步骤
   💬 → 🔧 步骤1：下载 ✅
   💬 → 🔧 步骤2：搜索 ✅
   💬 → 🔧 步骤3：压缩 ✅
   
5. LLM综合结果
   💬 → 🤖 "总结所做的一切"
   🤖 → 💬 "已下载、搜索和压缩..."
   
6. 用户看到最终摘要
   💬 → 👤 "✅ 任务完成：..."
```

---

## 📚 其他资源

### 模型上下文协议（MCP）
- 📖 [MCP规范](https://spec.modelcontextprotocol.io/)
- 🔗 [Anthropic MCP GitHub](https://github.com/anthropics/mcp)

### 推荐模型
- 🦙 [Llama 3 8B Instruct](https://huggingface.co/meta-llama/Meta-Llama-3-8B-Instruct)
- 🌟 [Mistral 7B Instruct](https://huggingface.co/mistralai/Mistral-7B-Instruct-v0.1)
- 🚀 [Mixtral 8x7B](https://huggingface.co/mistralai/Mixtral-8x7B-Instruct-v0.1)

### llama.cpp
- 🔗 [llama.cpp GitHub](https://github.com/ggerganov/llama.cpp)
- 📖 [文档](https://github.com/ggerganov/llama.cpp/blob/master/README.md)

---

## 🎓 用例

### 开发人员
- ✅ 自动化重复任务
- ✅ 分析代码并搜索TODO
- ✅ 管理Git仓库
- ✅ 生成文档
- ✅ 监控系统资源

### 系统管理员
- ✅ 自动化备份
- ✅ 监控日志
- ✅ 管理配置文件
- ✅ 在日志中搜索信息
- ✅ 压缩/解压缩文件

### 高级用户
- ✅ 自动组织文件
- ✅ 下载和处理网络内容
- ✅ 在文档中搜索信息
- ✅ 自动化复杂工作流
- ✅ 与外部API集成

---

## 🤝 贡献

有改进MCP Local的想法吗？欢迎贡献！

### 新工具想法
- 📧 电子邮件客户端
- 📅 日历集成
- 🗄️ 数据库操作
- 🐳 Docker集成
- 📊 报告生成

### 如何贡献
1. Fork项目
2. 创建分支（`git checkout -b feature/new-tool`）
3. 提交更改（`git commit -am 'Add new tool X'`）
4. 推送到分支（`git push origin feature/new-tool`）
5. 打开Pull Request

---

## 📄 许可证

该项目采用MIT许可证。自由使用、修改和分享。

```
MIT许可证

版权所有 (c) 2025 Gustavo Silva Da Costa

特此免费授予任何获得本软件副本和相关文档文件（"软件"）的人
不受限制地处理本软件的权利，包括但不限于使用、复制、修改、合并、
发布、分发、再许可和/或出售本软件副本的权利，并允许向其提供
本软件的人这样做，但须符合以下条件：

上述版权声明和本许可声明应包含在本软件的所有副本或
主要部分中。

本软件按"原样"提供，不提供任何明示或暗示的担保，
包括但不限于对适销性、特定用途的适用性和非侵权的担保。
在任何情况下，作者或版权持有人均不对任何索赔、损害或其他
责任负责，无论是在合同诉讼、侵权行为还是其他方面，由本软件
或本软件的使用或其他交易引起、产生或与之相关。
```

---

## 🙏 致谢

- Anthropic提供的模型上下文协议概念
- llama.cpp社区使本地运行LLM成为可能
- 所有为开源AI生态系统做出贡献的人

---

## 📞 支持

有问题？有疑问？有建议？

- 📧 电子邮件：gsilvadacosta0@gmail.com 
- 🆇 前Twitter 😂：https://x.com/bibliogalactic

---

<div align="center">

## ⭐ 如果您喜欢这个项目，请在GitHub上给它一个星标 ⭐

```
╔════════════════════════════════════════════════════════╗
║                                                        ║
║   用❤️为本地AI社区制作                                 ║
║                                                        ║
║   "为AI装上双手，一次一个工具"                          ║
║                                                        ║
╚════════════════════════════════════════════════════════╝
```

### 👨‍💻 创建者

**Gustavo Silva Da Costa** (Eto Demerzel) 🤫

🚀 *将本地AI转变为强大的助手*

</div>

---

**版本：** 1.0.0  
**最后更新：** 2025年10月  
**状态：** ✅ 生产环境

---
