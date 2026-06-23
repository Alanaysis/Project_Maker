# 02 - 设计: CI/CD 流水线架构

## 系统架构

```
┌──────────────────────────────────────────────────────────┐
│                      CLI (cmd/cicd)                       │
│         run | validate | plan                             │
└────────────────────────┬─────────────────────────────────┘
                         │
        ┌────────────────┼────────────────┐
        ↓                ↓                ↓
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│   Pipeline   │  │   Executor   │  │   Reporter   │
│   Config     │  │   Engine     │  │   Module     │
│              │  │              │  │              │
│ - YAML 解析  │  │ - 阶段编排   │  │ - 控制台输出 │
│ - 依赖验证   │  │ - 并行执行   │  │ - 状态报告   │
│ - 拓扑排序   │  │ - 重试机制   │  │ - 进度显示   │
└──────────────┘  └──────────────┘  └──────────────┘
```

## 核心设计决策

### 1. 配置格式选择 - YAML

选择 YAML 作为配置格式的原因：
- 人类可读性好
- 支持注释
- 层级结构清晰
- CI/CD 工具广泛采用（GitHub Actions, GitLab CI）

### 2. DAG 依赖模型

使用有向无环图 (DAG) 表示阶段依赖关系：
- 支持并行执行无依赖的阶段
- 通过拓扑排序检测循环依赖
- 依赖失败时自动跳过下游阶段

### 3. 执行器抽象

定义 Executor 接口，支持多种执行方式：
- **LocalExecutor**: 本地 Shell 执行
- **DockerExecutor**: Docker 容器执行

通过接口抽象，可以轻松扩展新的执行方式。

### 4. 并发模型

```
Pipeline Run
    │
    ├── Group 1: [stage_a] ────────────── 串行执行任务
    │
    ├── Group 2: [stage_b, stage_c] ───── 并行执行（goroutine）
    │         ├── stage_b ── 串行任务
    │         └── stage_c ── 串行任务
    │
    └── Group 3: [stage_d] ── 依赖 Group 2 全部成功
```

## 数据模型

### PipelineConfig
```go
type PipelineConfig struct {
    Name   string        // 流水线名称
    Stages []StageConfig // 阶段列表
}
```

### StageConfig
```go
type StageConfig struct {
    Name      string       // 阶段名称
    DependsOn []string     // 依赖阶段
    Tasks     []TaskConfig // 任务列表
}
```

### TaskConfig
```go
type TaskConfig struct {
    Name    string            // 任务名称
    Command string            // 执行命令
    Image   string            // Docker 镜像
    Env     map[string]string // 环境变量
    Timeout int               // 超时秒数
    Retries int               // 重试次数
}
```

## 状态机

```
Task/Stage 状态流转:

Pending ──→ Running ──→ Success
                │
                ├──→ Failed
                │
                └──→ Timeout

(依赖失败时)
Pending ──→ Skipped
```

## 错误处理策略

1. **任务失败**: 终止当前阶段，标记为失败
2. **依赖失败**: 跳过依赖该阶段的所有下游阶段
3. **超时**: 通过 context.Context 实现超时控制
4. **取消**: 支持 Ctrl+C 优雅取消

## 可扩展点

1. **执行器**: 实现 Executor 接口可添加新的执行后端
2. **报告器**: 可扩展为文件报告、Webhook 通知等
3. **配置源**: 可支持从 Git、HTTP 等加载配置
4. **制品管理**: 可添加构建产物的存储和传递
