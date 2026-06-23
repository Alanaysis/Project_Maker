# 01 - 研究: CI/CD 流水线

## 什么是 CI/CD？

### CI - 持续集成 (Continuous Integration)
持续集成是一种开发实践，团队成员频繁地将代码集成到共享仓库中。每次集成都通过自动化构建（包括测试）来验证，从而尽早发现集成错误。

**核心原则**：
- 频繁提交代码（至少每天一次）
- 每次提交触发自动化构建和测试
- 构建失败后优先修复
- 保持构建快速（10分钟以内为佳）

### CD - 持续交付/持续部署
- **持续交付 (Continuous Delivery)**: 确保代码随时可以部署到生产环境
- **持续部署 (Continuous Deployment)**: 每次通过测试的变更自动部署到生产环境

## 流水线 (Pipeline) 概念

流水线是 CI/CD 的核心编排机制，它定义了代码从提交到部署的完整流程。

### 基本结构
```
代码提交 → 构建 → 测试 → 部署
```

### 详细流程
```
代码提交
  ↓
┌─────────┐
│  构建    │  编译代码、打包制品
│  Build   │
└────┬────┘
     ↓
┌─────────┐
│  测试    │  单元测试、集成测试、E2E测试
│  Test    │
└────┬────┘
     ↓
┌─────────┐
│  扫描    │  代码质量、安全漏洞
│  Scan    │
└────┬────┘
     ↓
┌─────────┐
│  部署    │  部署到各环境
│  Deploy  │
└─────────┘
```

## 流水线编排模型

### 1. 串行执行
阶段按顺序依次执行，前一个阶段成功后才执行下一个。
```
A → B → C → D
```

### 2. 并行执行
无依赖关系的阶段可以同时执行。
```
    ┌→ B ─┐
A ──┤     ├──→ D
    └→ C ─┘
```

### 3. 有向无环图 (DAG)
最灵活的编排方式，允许定义复杂的依赖关系。
```
A ──→ B ──→ D
 ↓         ↑
 └──→ C ───┘
```

## 主流 CI/CD 工具对比

| 工具 | 类型 | 配置方式 | 特点 |
|------|------|----------|------|
| Jenkins | 自托管 | Groovy/界面 | 插件丰富，灵活强大 |
| GitHub Actions | 云服务 | YAML | 与 GitHub 深度集成 |
| GitLab CI | 自托管/云 | YAML | 与 GitLab 集成 |
| CircleCI | 云服务 | YAML | 快速，Docker 原生 |
| Argo CD | 自托管 | YAML/GitOps | Kubernetes 原生 |

## Go 在 CI/CD 中的应用

Go 语言在 CI/CD 工具开发中有优势：
- **单二进制部署**: 编译后无运行时依赖
- **并发原语**: goroutine 天然支持并行阶段执行
- **标准库**: os/exec 支持命令执行
- **跨平台**: 可编译到多个平台

## 学习资源

- [CI/CD 概念 - Martin Fowler](https://martinfowler.com/bliki/ContinuousIntegration.html)
- [GitHub Actions 文档](https://docs.github.com/en/actions)
- [Jenkins Pipeline 语法](https://www.jenkins.io/doc/book/pipeline/)
