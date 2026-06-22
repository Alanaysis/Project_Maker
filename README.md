# 🎯 Learning Project Factory / 学习型项目工厂

> **33 个深度学习项目** | 涵盖自动驾驶、区块链、AI、系统编程、网络安全等领域

---

## 🚀 快速导航

### 按领域浏览

| 领域 | 项目数 | 入口 |
|------|--------|------|
| 🚗 [自动驾驶](projects/ADAS_README.md) | 4 | 感知、规划、CARLA、SLAM |
| ⛓️ [区块链](projects/BLOCKCHAIN_README.md) | 5 | 区块链、智能合约、ERC20、投票 |
| 🤖 [AI 全栈](projects/AI_README.md) | 5 | 量化、LoRA、ViT/CLIP、视觉、LLM |
| ⚙️ [系统基础设施](projects/SYSTEM_README.md) | 5 | 数据库、调度、容器、VM、OS |
| 🌐 [网络服务](projects/NETWORK_README.md) | 5 | HA、MCP、VPN、CDN、防火墙 |
| 🔧 [异构计算](projects/HETERO_README.md) | 2 | CPU+GPU、多 GPU |
| 🎮 [分布式 & 通讯](projects/DISTRIBUTED_README.md) | 2 | 游戏系统、聊天应用 |
| 💰 [金融 & 应用](projects/APPS_README.md) | 5 | 量化交易、VR、文档编辑器、键盘驱动 |

### 按技术栈浏览

| 技术栈 | 项目 |
|--------|------|
| **C++** | high-concurrency-db, ha-server, simple-vm, vr-application, keyboard-driver, adas-perception |
| **Go** | hpc-task-scheduler, container-runtime, cdn-service, simple-blockchain, social-chat-app, distributed-game-system |
| **Python** | finetune-rl-framework, vit-clip-training, industrial-vision-detection, quant-trading-system, adas-planning, carla-rl, slam-mapping |
| **Rust** | mcp-server, vpn-software, smart-contract-vm |
| **Solidity** | erc20-token, decentralized-voting |
| **TypeScript** | document-editor |

### 按难度浏览

| 难度 | 项目 |
|------|------|
| ⭐⭐⭐ 入门 | simple-blockchain, erc20-token, cdn-service |
| ⭐⭐⭐⭐ 初级 | hpc-task-scheduler, container-runtime, social-chat-app, vr-application |
| ⭐⭐⭐⭐⭐ 中级 | high-concurrency-db, ha-server, vpn-software, adas-planning |
| ⭐⭐⭐⭐⭐⭐ 高级 | simple-vm, simple-os, finetune-rl-framework, smart-contract-vm |
| ⭐⭐⭐⭐⭐⭐⭐ 专家 | local-llm-engine, adas-perception, slam-mapping |

---

## 📁 项目目录

### 🚗 自动驾驶模块

| 项目 | 描述 | 技术栈 | 难度 |
|------|------|--------|------|
| [adas-perception](projects/adas-perception/) | 自动驾驶感知系统 | Python, PyTorch | ⭐⭐⭐⭐⭐⭐⭐ |
| [adas-planning](projects/adas-planning/) | 自动驾驶规划控制 | Python | ⭐⭐⭐⭐⭐ |
| [carla-rl](projects/carla-rl/) | CARLA 模拟器集成 | Python, RL | ⭐⭐⭐⭐⭐ |
| [slam-mapping](projects/slam-mapping/) | SLAM 建图系统 | Python, OpenCV | ⭐⭐⭐⭐⭐⭐⭐ |

📖 [自动驾驶模块详细说明](projects/ADAS_README.md)

---

### ⛓️ 区块链模块

| 项目 | 描述 | 技术栈 | 难度 |
|------|------|--------|------|
| [simple-blockchain](projects/simple-blockchain/) | 简易区块链实现 | Go | ⭐⭐⭐ |
| [smart-contract-vm](projects/smart-contract-vm/) | 智能合约虚拟机 | Rust | ⭐⭐⭐⭐⭐⭐ |
| [erc20-token](projects/erc20-token/) | ERC20 代币合约 | Solidity, Hardhat | ⭐⭐⭐ |
| [decentralized-voting](projects/decentralized-voting/) | 去中心化投票系统 | Solidity, Next.js | ⭐⭐⭐⭐ |

📖 [区块链模块详细说明](projects/BLOCKCHAIN_README.md)

---

### 🤖 AI 全栈

| 项目 | 描述 | 技术栈 | 难度 |
|------|------|--------|------|
| [edge-quantized-model](projects/edge-quantized-model/) | 端侧极致量化模型 | Python, C++ | ⭐⭐⭐⭐⭐⭐ |
| [finetune-rl-framework](projects/finetune-rl-framework/) | 微调/RL 后训练框架 | Python, PyTorch | ⭐⭐⭐⭐⭐⭐ |
| [vit-clip-training](projects/vit-clip-training/) | ViT/CLIP 模型训练 | Python, PyTorch | ⭐⭐⭐⭐⭐ |
| [industrial-vision-detection](projects/industrial-vision-detection/) | 工业视觉检测 | Python, PyTorch | ⭐⭐⭐⭐⭐ |
| [local-llm-engine](projects/local-llm-engine/) | 本地 LLM 推理引擎 | C++ | ⭐⭐⭐⭐⭐⭐⭐ |

📖 [AI 模块详细说明](projects/AI_README.md)

---

### ⚙️ 系统基础设施

| 项目 | 描述 | 技术栈 | 难度 |
|------|------|--------|------|
| [high-concurrency-db](projects/high-concurrency-db/) | 高并发数据库查询 | C++ | ⭐⭐⭐⭐⭐ |
| [hpc-task-scheduler](projects/hpc-task-scheduler/) | HPC 任务调度系统 | Go | ⭐⭐⭐⭐ |
| [container-runtime](projects/container-runtime/) | 容器化基础设施 | Go | ⭐⭐⭐⭐ |
| [simple-vm](projects/simple-vm/) | 简易虚拟机 | C++, KVM | ⭐⭐⭐⭐⭐⭐ |
| [simple-os](projects/simple-os/) | 简易操作系统 | C, 汇编 | ⭐⭐⭐⭐⭐⭐ |

📖 [系统模块详细说明](projects/SYSTEM_README.md)

---

### 🌐 网络服务

| 项目 | 描述 | 技术栈 | 难度 |
|------|------|--------|------|
| [ha-server](projects/ha-server/) | 高可用服务器 | C++ | ⭐⭐⭐⭐⭐ |
| [mcp-server](projects/mcp-server/) | MCP 服务端 | Rust | ⭐⭐⭐⭐ |
| [vpn-software](projects/vpn-software/) | VPN 软件 | Rust | ⭐⭐⭐⭐⭐ |
| [cdn-service](projects/cdn-service/) | CDN 服务 | Go | ⭐⭐⭐ |
| [firewall](projects/firewall/) | 防火墙 | C | ⭐⭐⭐⭐⭐ |

📖 [网络模块详细说明](projects/NETWORK_README.md)

---

### 🔧 异构计算

| 项目 | 描述 | 技术栈 | 难度 |
|------|------|--------|------|
| [heterogeneous-computing](projects/heterogeneous-computing/) | CPU+GPU 异构计算 | C++ | ⭐⭐⭐⭐⭐ |
| [multi-gpu-computing](projects/multi-gpu-computing/) | 多 GPU 并行计算 | Python | ⭐⭐⭐⭐⭐ |

📖 [异构计算模块详细说明](projects/HETERO_README.md)

---

### 🎮 分布式 & 通讯

| 项目 | 描述 | 技术栈 | 难度 |
|------|------|--------|------|
| [distributed-game-system](projects/distributed-game-system/) | 分布式游戏系统 | Go | ⭐⭐⭐⭐ |
| [social-chat-app](projects/social-chat-app/) | 社交聊天应用 | Go | ⭐⭐⭐⭐ |

📖 [分布式模块详细说明](projects/DISTRIBUTED_README.md)

---

### 💰 金融 & 应用

| 项目 | 描述 | 技术栈 | 难度 |
|------|------|--------|------|
| [quant-trading-system](projects/quant-trading-system/) | 量化交易系统 | Python | ⭐⭐⭐⭐⭐ |
| [vr-application](projects/vr-application/) | VR 应用 | C++, OpenGL | ⭐⭐⭐⭐⭐ |
| [document-editor](projects/document-editor/) | 文档编辑器 | TypeScript | ⭐⭐⭐⭐ |
| [keyboard-driver](projects/keyboard-driver/) | 键盘驱动 | C | ⭐⭐⭐⭐⭐ |
| [disaster-recovery-storage](projects/disaster-recovery-storage/) | 容灾存储 | C++ | ⭐⭐⭐⭐⭐ |

📖 [应用模块详细说明](projects/APPS_README.md)

---

## 📚 学习资源

### 学习路径

- 🛤️ [学习路径图](LEARNING_PATHS.md) - 推荐的学习顺序
- 📋 [项目索引](PROJECT_INDEX.md) - 按技术栈/难度索引
- 📝 [愿望单](WISHLIST.md) - 所有项目需求

### 项目模板

- 📄 [项目模板规范](PROJECT_TEMPLATE.md) - 标准项目结构
- 📝 [学习笔记模板](LEARNING_NOTES.md) - 学习记录模板
- ✅ [质量检查清单](CHECKLIST.md) - 项目质量标准

### 贡献指南

- 🤝 [贡献指南](CONTRIBUTING.md) - 如何参与贡献

---

## 📊 项目统计

| 维度 | 数量 |
|------|------|
| **总项目数** | 33 |
| **技术栈** | 6 (C++, Go, Python, Rust, Solidity, TypeScript) |
| **领域** | 8 |
| **总代码行数** | 100,000+ |
| **文档数量** | 200+ |

---

## 🎯 快速开始

### 1. 选择一个领域

```bash
# 查看所有领域
cat README.md

# 进入感兴趣的领域
cd projects/ADAS_README.md  # 自动驾驶
cd projects/BLOCKCHAIN_README.md  # 区块链
```

### 2. 选择一个项目

```bash
# 进入项目目录
cd projects/adas-perception

# 查看项目说明
cat README.md

# 查看学习笔记模板
cat LEARNING_NOTES.md
```

### 3. 开始学习

```bash
# 安装依赖
pip install -r requirements.txt

# 运行示例
python examples/demo.py

# 运行测试
pytest tests/
```

---

## 🔗 相关链接

- 📊 [代码审查报告](CODE_REVIEW_REPORT.md) - 项目质量分析
- 📈 [GitHub 仓库](https://github.com/Alanaysis/Project_Maker) - 源代码

---

## 📝 更新日志

### 2026-06-22
- ✅ 完成所有 33 个项目
- ✅ 新增自动驾驶模块（4 个项目）
- ✅ 新增区块链模块（5 个项目）
- ✅ 修复 Critical/High 问题
- ✅ 添加多层导航 README

---

## 🤝 贡献

欢迎贡献！请查看 [贡献指南](CONTRIBUTING.md)。

---

## 📄 许可证

MIT License

---

## 🙏 致谢

感谢所有开源项目的贡献者！

---

[English Version](README_EN.md)
