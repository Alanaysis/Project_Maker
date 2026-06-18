# 🎯 Learning Project Factory / 学习型项目工厂

[English](#english) | [中文](#中文)

---

## 中文

### 概述

这是一个**学习型项目集合**，通过"愿望单"机制，由 AI 子代理自动实现标准化的学习项目。

### 核心理念

```
📝 发布愿望 → 🔍 调研分析 → 🏗️ 设计规划 → 🤖 子代理实现 → 📚 学习探索
```

**学习型项目 vs 普通项目**：

| 维度 | 普通项目 | 学习型项目 |
|------|----------|------------|
| 目标 | 能用就行 | 理解原理 |
| 深度 | 告诉你"怎么做" | 告诉你"为什么这么做" |
| 文档 | 基本说明 | 市场调研 + 设计决策 + 产品思维 |
| 代码 | 功能实现 | 重点标注 + 充分注释 |
| 扩展 | 固定功能 | 提供扩展指南 |

### 学习型项目的核心要素

每个项目必须包含：

- 📦 **技术栈明确标注** - 用了什么，为什么用
- ⭐ **重点难点突出** - 核心概念，关键代码
- 💡 **值得思考指明** - 设计决策，技术权衡
- 📊 **市场调研** - 同类型项目分析，技术变体
- 🎯 **产品思维** - 用户画像，使用场景，差异化

### 目录结构

```
project_copyninja/
├── README.md                  # 项目总览（本文件）
├── WISHLIST.md                # 愿望单 - 发布学习项目需求
├── LEARNING_PATHS.md          # 学习路径图
├── PROJECT_INDEX.md           # 项目索引
├── PROJECT_TEMPLATE.md        # 项目模板规范
├── CONTRIBUTING.md            # 贡献指南
├── _template/                 # 标准化模板
│   ├── README.md.template
│   ├── docs/
│   │   ├── 01-RESEARCH.md.template
│   │   ├── 02-REQUIREMENTS.md.template
│   │   ├── 03-DESIGN.md.template
│   │   ├── 04-PRODUCT.md.template
│   │   └── 05-DEVELOPMENT.md.template
│   ├── LEARNING_NOTES.md.template
│   └── CHECKLIST.md
└── projects/                  # 项目目录
    ├── project-xxx/
    │   ├── README.md          # 项目说明
    │   ├── docs/              # 文档
    │   ├── src/               # 源代码
    │   ├── tests/             # 测试
    │   ├── examples/          # 示例
    │   └── LEARNING_NOTES.md  # 学习笔记模板
    └── ...
```

### 快速开始

1. **查看愿望单**：打开 `WISHLIST.md` 查看当前任务
2. **发布新愿望**：按照模板格式添加你的学习项目想法
3. **等待实现**：AI 子代理会自动实现项目
4. **开始学习**：进入项目目录，阅读文档，运行代码

### 工作流程

```
┌─────────────────────────────────────────────────────────────┐
│                    项目实现流程                               │
├─────────────────────────────────────────────────────────────┤
│  Phase 1: 调研                                                │
│  ├── 搜索 GitHub 同类型项目                                   │
│  ├── 分析技术变体和演进路径                                    │
│  └── 产出：01-RESEARCH.md                                     │
│                                                              │
│  Phase 2: 设计                                                │
│  ├── 需求分析和用户画像                                        │
│  ├── 架构设计和选型                                           │
│  └── 产出：02-REQUIREMENTS.md + 03-DESIGN.md                  │
│                                                              │
│  Phase 3: 产品                                                │
│  ├── 用户吸引力分析                                           │
│  ├── 竞品对比                                                 │
│  └── 产出：04-PRODUCT.md                                      │
│                                                              │
│  Phase 4: 实现                                                │
│  ├── 核心功能开发                                             │
│  ├── 重点难点标注                                             │
│  └── 产出：src/ + tests/                                      │
│                                                              │
│  Phase 5: 文档                                                │
│  ├── 开发手册                                                 │
│  ├── 使用示例                                                 │
│  └── 产出：05-DEVELOPMENT.md + examples/ + README.md          │
│                                                              │
│  Phase 6: 验证                                                │
│  ├── 质量检查                                                 │
│  ├── 运行验证                                                 │
│  └── 产出：CHECKLIST.md                                       │
└─────────────────────────────────────────────────────────────┘
```

### 项目类型

- 🔧 **工具类**：CLI 工具、自动化脚本
- 🌐 **Web 应用**：前端、后端、全栈
- 📊 **数据处理**：数据分析、可视化
- 🤖 **AI/ML**：机器学习、深度学习示例
- 🎮 **小游戏**：学习编程的趣味项目
- 📚 **算法实现**：数据结构、算法演示

---

## English

### Overview

This is a **learning project collection** that uses a "wishlist" mechanism where AI sub-agents automatically implement standardized learning projects.

### Core Philosophy

```
📝 Post Wish → 🔍 Research → 🏗️ Design → 🤖 Agent Implements → 📚 Learn
```

**Learning Projects vs Regular Projects**:

| Dimension | Regular Project | Learning Project |
|-----------|-----------------|------------------|
| Goal | Just works | Understand principles |
| Depth | Tells you "how" | Tells you "why" |
| Docs | Basic readme | Market research + Design decisions + Product thinking |
| Code | Feature implementation | Key annotations + Thorough comments |
| Extension | Fixed features | Extension guidelines |

### Core Elements of Learning Projects

Each project must include:

- 📦 **Tech Stack Clearly Marked** - What's used, why it's used
- ⭐ **Key Difficulties Highlighted** - Core concepts, critical code
- 💡 **Worth Thinking Points** - Design decisions, technical tradeoffs
- 📊 **Market Research** - Similar project analysis, technical variants
- 🎯 **Product Thinking** - User personas, use cases, differentiation

### Directory Structure

```
project_copyninja/
├── README.md                  # Project overview (this file)
├── WISHLIST.md                # Wishlist - post learning project ideas
├── LEARNING_PATHS.md          # Learning path diagram
├── PROJECT_INDEX.md           # Project index
├── PROJECT_TEMPLATE.md        # Project template specification
├── CONTRIBUTING.md            # Contribution guide
├── _template/                 # Standardized templates
│   ├── README.md.template
│   ├── docs/
│   │   ├── 01-RESEARCH.md.template
│   │   ├── 02-REQUIREMENTS.md.template
│   │   ├── 03-DESIGN.md.template
│   │   ├── 04-PRODUCT.md.template
│   │   └── 05-DEVELOPMENT.md.template
│   ├── LEARNING_NOTES.md.template
│   └── CHECKLIST.md
└── projects/                  # Projects directory
    ├── project-xxx/
    │   ├── README.md          # Project description
    │   ├── docs/              # Documentation
    │   ├── src/               # Source code
    │   ├── tests/             # Tests
    │   ├── examples/          # Examples
    │   └── LEARNING_NOTES.md  # Learning notes template
    └── ...
```

### Getting Started

1. **Check Wishlist**: Open `WISHLIST.md` to see current tasks
2. **Post New Wish**: Add your learning project idea following the template
3. **Wait for Implementation**: AI sub-agents will automatically implement the project
4. **Start Learning**: Enter the project directory, read docs, run code

### Workflow

```
┌─────────────────────────────────────────────────────────────┐
│                    Project Implementation Flow               │
├─────────────────────────────────────────────────────────────┤
│  Phase 1: Research                                            │
│  ├── Search GitHub for similar projects                       │
│  ├── Analyze technical variants and evolution paths           │
│  └── Output: 01-RESEARCH.md                                   │
│                                                              │
│  Phase 2: Design                                              │
│  ├── Requirements analysis and user personas                  │
│  ├── Architecture design and tech selection                   │
│  └── Output: 02-REQUIREMENTS.md + 03-DESIGN.md               │
│                                                              │
│  Phase 3: Product                                             │
│  ├── User attraction analysis                                 │
│  ├── Competitive comparison                                   │
│  └── Output: 04-PRODUCT.md                                    │
│                                                              │
│  Phase 4: Implementation                                      │
│  ├── Core functionality development                           │
│  ├── Key difficulty annotations                               │
│  └── Output: src/ + tests/                                    │
│                                                              │
│  Phase 5: Documentation                                       │
│  ├── Development manual                                       │
│  ├── Usage examples                                           │
│  └── Output: 05-DEVELOPMENT.md + examples/ + README.md       │
│                                                              │
│  Phase 6: Verification                                        │
│  ├── Quality check                                            │
│  ├── Runtime verification                                     │
│  └── Output: CHECKLIST.md                                     │
└─────────────────────────────────────────────────────────────┘
```

### Project Types

- 🔧 **Tools**: CLI tools, automation scripts
- 🌐 **Web Apps**: Frontend, backend, full-stack
- 📊 **Data Processing**: Data analysis, visualization
- 🤖 **AI/ML**: Machine learning, deep learning examples
- 🎮 **Mini Games**: Fun projects for learning programming
- 📚 **Algorithm Implementations**: Data structures, algorithm demos
