# CI/CD Pipeline / CI/CD 流水线

> A learning project implementing a simplified CI/CD pipeline framework in Go.
> 实现一个简易的 CI/CD 流水线框架的学习项目。

---

## English

### Overview

This project implements a simplified CI/CD (Continuous Integration / Continuous Deployment) pipeline framework from scratch in Go. It serves as an educational tool to understand the core concepts of CI/CD without relying on external tools like Jenkins, GitLab CI, or GitHub Actions.

### Learning Objectives

- **Understand CI/CD**: Learn the principles of continuous integration and continuous deployment
- **Master Pipeline Orchestration**: Understand how to define, execute, and manage multi-stage pipelines
- **Learn Build & Deploy**: Practice build processes, artifact management, and deployment strategies

### CI/CD Concepts Explained

```
Code Commit → Build → Test → Deploy
```

1. **Continuous Integration (CI)**: Automatically build and test code changes when they are committed. This catches bugs early and ensures code quality.

2. **Continuous Deployment (CD)**: Automatically deploy passing builds to staging and production environments, enabling rapid, reliable releases.

3. **Pipeline**: An automated workflow that transforms code changes into deployed software. Pipelines consist of stages (build, test, deploy) which contain steps (compile, run tests, deploy).

4. **Quality Gates**: Each stage acts as a gate - code must pass tests before deployment, and staging must succeed before production release.

5. **Fast Feedback Loop**: Developers should know about failures within minutes, not hours. Parallel execution and quick builds enable this.

6. **Deployment Strategies**:
   - **Rolling Update**: Gradually replace old instances with new ones
   - **Blue-Green**: Maintain two identical environments, switch traffic instantly
   - **Canary**: Deploy to a small subset first, then expand

### Project Structure

```
cicd-pipeline/
├── go.mod              # Go module definition
├── README.md           # This file
├── pipeline/           # Core pipeline package
│   └── pipeline.go     # Pipeline types, stages, runners, triggers
├── examples/           # Demo programs
│   ├── basic_pipeline.go       # Single-stage pipeline
│   ├── multi_stage.go          # Full CI/CD pipeline
│   ├── parallel_test.go        # Parallel test execution
│   └── deployment.go           # Deployment with artifacts & webhooks
└── tests/              # Unit tests
    └── pipeline_test.go    # 40+ unit tests
```

### How to Run Examples

```bash
# Example 1: Basic Pipeline (single-stage)
go run examples/basic_pipeline.go

# Example 2: Multi-Stage Pipeline (build → test → deploy)
go run examples/multi_stage.go

# Example 3: Parallel Test Execution
go run examples/parallel_test.go

# Example 4: Deployment Pipeline (with artifacts and webhooks)
go run examples/deployment.go

# Run all tests
go test ./tests/
```

### Core Types

| Type | Purpose |
|------|---------|
| `Pipeline` | Top-level pipeline definition with stages and triggers |
| `Stage` | Logical phase (build, test, deploy) containing steps |
| `Step` | Individual task within a stage (compile, run tests) |
| `Trigger` | Event that starts a pipeline (commit, tag, schedule, webhook) |
| `Context` | Shared state between stages during execution |
| `PipelineResult` | Tracks overall pipeline execution results |
| `ArtifactManager` | Manages build artifacts (binaries, reports, etc.) |
| `WebhookHandler` | Processes incoming webhook events |
| `Runner` | Executes a pipeline definition |

---

## 中文

### 概述

本项目从零实现了一个简易的 CI/CD（持续集成/持续部署）流水线框架，使用 Go 语言编写。作为一个学习工具，帮助理解 CI/CD 的核心概念，而不依赖 Jenkins、GitLab CI 或 GitHub Actions 等外部工具。

### 学习目标

- **理解 CI/CD**：学习持续集成和持续部署的原理
- **掌握流水线编排**：理解如何定义、执行和管理多阶段流水线
- **学会构建部署**：实践构建流程、制品管理和部署策略

### CI/CD 核心概念

```
代码提交 → 构建 → 测试 → 部署
```

1. **持续集成 (CI)**：当代码被提交时，自动构建和测试代码变更。这能尽早发现 bug 并确保代码质量。

2. **持续部署 (CD)**：自动将通过的构建部署到预发和生产环境，实现快速、可靠的发布。

3. **流水线**：将代码变更转化为已部署软件的自动化工作流。流水线由阶段（构建、测试、部署）组成，每个阶段包含步骤（编译、运行测试、部署）。

4. **质量门禁**：每个阶段都是一个门禁——代码必须通过测试才能部署，预发部署成功才能发布到生产环境。

5. **快速反馈循环**：开发者应该在几分钟内知道失败，而不是几小时。并行执行和快速构建可以实现这一点。

6. **部署策略**：
   - **滚动更新**：逐步用新实例替换旧实例
   - **蓝绿部署**：维护两个相同的环境，瞬间切换流量
   - **金丝雀发布**：先部署到小部分用户，然后逐步扩大

### 项目结构

```
cicd-pipeline/
├── go.mod              # Go 模块定义
├── README.md           # 本文件
├── pipeline/           # 核心流水线包
│   └── pipeline.go     # 流水线类型、阶段、运行器、触发器
├── examples/           # 演示程序
│   ├── basic_pipeline.go       # 单阶段流水线
│   ├── multi_stage.go          # 完整 CI/CD 流水线
│   ├── parallel_test.go        # 并行测试执行
│   └── deployment.go           # 带制品和 Webhook 的部署流水线
└── tests/              # 单元测试
    └── pipeline_test.go    # 40+ 单元测试
```

### 如何运行示例

```bash
# 示例 1：基本流水线（单阶段）
go run examples/basic_pipeline.go

# 示例 2：多阶段流水线（构建 → 测试 → 部署）
go run examples/multi_stage.go

# 示例 3：并行测试执行
go run examples/parallel_test.go

# 示例 4：部署流水线（带制品和 Webhook）
go run examples/deployment.go

# 运行所有测试
go test ./tests/
```

### 核心类型

| 类型 | 用途 |
|------|------|
| `Pipeline` | 顶层流水线定义，包含阶段和触发器 |
| `Stage` | 逻辑阶段（构建、测试、部署），包含步骤 |
| `Step` | 阶段内的单个任务（编译、运行测试） |
| `Trigger` | 启动流水线的事件（提交、标签、定时、Webhook） |
| `Context` | 执行期间阶段间的共享状态 |
| `PipelineResult` | 追踪整体流水线执行结果 |
| `ArtifactManager` | 管理构建制品（二进制文件、报告等） |
| `WebhookHandler` | 处理传入的 Webhook 事件 |
| `Runner` | 执行流水线定义 |

---

## Architecture / 架构图

```
┌─────────────┐    ┌──────────┐    ┌─────────┐    ┌──────────┐
│  Trigger    │───>│  Build   │───>│  Test   │───>│  Deploy  │
│  (Commit/   │    │  (Compile│    │ (Unit/  │    │ (Staging │
│   Tag/      │    │   +      │    │  Int/   │    │  +      │
│   Webhook)  │    │  Package)│    │  Lint)  │    │  Prod)   │
└─────────────┘    └──────────┘    └─────────┘    └──────────┘
      │                  │              │              │
      ▼                  ▼              ▼              ▼
  Pipeline          Artifact     Test Report    Deploy Result
  Result           Manager       Manager       Manager
```

---

## Key Learnings / 关键学习点

1. **Pipeline as Code**: Pipelines should be defined in code, not configured through UI. This enables version control, code review, and reuse.

2. **Idempotent Stages**: Each stage should produce the same result given the same input, making pipelines reliable and reproducible.

3. **Fast Feedback**: The faster developers get feedback, the cheaper bugs are to fix. Parallel execution and quick builds are essential.

4. **Artifact Promotion**: Artifacts (binaries, images) should flow through environments unchanged - promote the artifact, not rebuild for each environment.

5. **Deployment Safety**: Use strategies like rolling updates and blue-green deployment to minimize risk and downtime during releases.

6. **Webhook Integration**: External systems (GitHub, GitLab) can trigger pipelines via webhooks, enabling automated CI/CD workflows.

---

## License

MIT
