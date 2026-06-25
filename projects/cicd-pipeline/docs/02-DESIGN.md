# 02 - 设计: CI/CD 流水线架构

## 系统架构

```
┌──────────────────────────────────────────────────────────────────────┐
│                           CLI (cmd/cicd)                             │
│              run | validate | plan | trigger                         │
└────────────────────────┬─────────────────────────────────────────────┘
                         │
        ┌────────────────┼────────────────┬────────────────┐
        ↓                ↓                ↓                ↓
┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│   Pipeline   │  │   Executor   │  │   Deployer   │  │   Trigger    │
│   Config     │  │   Engine     │  │   Manager    │  │   Manager    │
│              │  │              │  │              │  │              │
│ - YAML 解析  │  │ - 阶段编排   │  │ - 环境管理   │  │ - Git Push   │
│ - 依赖验证   │  │ - 并行执行   │  │ - 滚动部署   │  │ - 定时触发   │
│ - 拓扑排序   │  │ - 重试机制   │  │ - 蓝绿部署   │  │ - 手动触发   │
│ - 触发配置   │  │              │  │ - 金丝雀     │  │              │
│ - 变量定义   │  │              │  │ - 回滚管理   │  │              │
└──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘
                         │
                         ↓
                 ┌──────────────┐
                 │   Reporter   │
                 │   Module     │
                 │              │
                 │ - 控制台输出 │
                 │ - 状态报告   │
                 │ - 进度显示   │
                 └──────────────┘
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

### 4. 部署策略设计

支持多种部署策略：

#### 滚动部署 (Rolling)
```
旧版本: [v1] [v1] [v1] [v1]
                 ↓
阶段1:  [v1] [v2] [v1] [v1]
阶段2:  [v1] [v2] [v2] [v1]
阶段3:  [v2] [v2] [v2] [v1]
阶段4:  [v2] [v2] [v2] [v2]
```

#### 蓝绿部署 (Blue-Green)
```
蓝环境: [v1] [v1] [v1] ← 当前流量
绿环境: [v2] [v2] [v2] ← 部署新版本
            ↓
流量切换: [v2] [v2] [v2] ← 切换流量
蓝环境: [v1] [v1] [v1] ← 下线
```

#### 金丝雀部署 (Canary)
```
阶段1:  10% 流量 → [v2]  90% 流量 → [v1]
阶段2:  50% 流量 → [v2]  50% 流量 → [v1]
阶段3: 100% 流量 → [v2]
```

### 5. 触发机制设计

```
                    ┌─────────────────┐
                    │   Trigger       │
                    │   Manager       │
                    └────────┬────────┘
                             │
        ┌────────────────────┼────────────────────┐
        ↓                    ↓                    ↓
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│  Git Push    │    │   Schedule   │    │   Manual     │
│  Trigger     │    │   Trigger    │    │   Trigger    │
│              │    │              │    │              │
│ - 分支过滤   │    │ - Cron 表达式│    │ - CLI 触发   │
│ - 路径过滤   │    │ - 定时执行   │    │ - API 触发   │
└──────────────┘    └──────────────┘    └──────────────┘
```

### 6. 回滚机制设计

```
版本历史管理:
┌────────────────────────────────────────────┐
│  Snapshot Stack (每个环境独立)              │
├────────────────────────────────────────────┤
│  [v3] ← 当前版本                           │
│  [v2] ← 可回滚                             │
│  [v1] ← 可回滚                             │
│  ...                                       │
│  [v(n-max_versions)] ← 自动清理            │
└────────────────────────────────────────────┘

回滚流程:
1. 获取上一个版本快照
2. 执行滚动部署到旧版本
3. 更新环境版本信息
4. 记录回滚操作
```

### 7. 并发模型

```
Pipeline Run
    │
    ├── Group 1: [checkout] ──────────────── 串行执行任务
    │
    ├── Group 2: [dependencies] ──────────── 串行执行任务
    │
    ├── Group 3: [build] ─────────────────── 串行执行任务
    │
    ├── Group 4: [unit-test, quality,       │
    │             integration-test] ──────── 并行执行（goroutine）
    │         ├── unit-test ── 串行任务
    │         ├── quality ──── 串行任务
    │         └── integration ─ 串行任务
    │
    ├── Group 5: [coverage, docker-build] ── 并行执行
    │
    ├── Group 6: [deploy-staging] ────────── 串行执行
    │
    └── Group 7: [deploy-production] ─────── 串行执行
```

## 数据模型

### PipelineConfig
```go
type PipelineConfig struct {
    Name      string            // 流水线名称
    Trigger   TriggerConfig     // 触发配置
    Variables map[string]string // 全局变量
    Stages    []StageConfig     // 阶段列表
}
```

### TriggerConfig
```go
type TriggerConfig struct {
    Push     *PushTrigger // Git Push 触发
    Schedule string       // Cron 表达式
    Manual   bool         // 手动触发
}

type PushTrigger struct {
    Branches []string // 分支列表
    Paths    []string // 路径过滤
}
```

### StageConfig
```go
type StageConfig struct {
    Name      string        // 阶段名称
    DependsOn []string      // 依赖阶段
    Tasks     []TaskConfig  // 任务列表
    Deploy    *DeployConfig // 部署配置（可选）
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

### DeployConfig
```go
type DeployConfig struct {
    Strategy string         // 部署策略: rolling, blue-green, canary
    Targets  []DeployTarget // 部署目标
    Rollback RollbackConfig // 回滚配置
    Env      map[string]string // 环境变量
}

type DeployTarget struct {
    Name   string // 目标名称
    URL    string // 目标 URL
    Region string // 区域
    Weight int    // 流量权重
}

type RollbackConfig struct {
    Enabled     bool // 是否启用自动回滚
    MaxVersions int  // 保留的历史版本数
    HealthCheck int  // 健康检查超时(秒)
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

Deployment 状态流转:

Pending ──→ InProgress ──→ Success
                   │
                   ├──→ Failed
                   │
                   └──→ RolledBack
```

## 错误处理策略

1. **任务失败**: 终止当前阶段，标记为失败
2. **依赖失败**: 跳过依赖该阶段的所有下游阶段
3. **超时**: 通过 context.Context 实现超时控制
4. **取消**: 支持 Ctrl+C 优雅取消
5. **部署失败**: 根据配置决定是否自动回滚

## 可扩展点

1. **执行器**: 实现 Executor 接口可添加新的执行后端（K8s, Cloud Functions）
2. **报告器**: 可扩展为文件报告、Webhook 通知、Slack/钉钉通知
3. **配置源**: 可支持从 Git、HTTP、数据库加载配置
4. **制品管理**: 可添加构建产物的存储和传递
5. **部署策略**: 可实现自定义部署策略
6. **触发器**: 可添加 Webhook、事件触发等
