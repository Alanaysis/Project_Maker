# 03 - 实现: CI/CD 流水线

## 项目结构

```
cicd-pipeline/
├── cmd/cicd/main.go                  # CLI 入口
├── internal/
│   ├── pipeline/
│   │   ├── config.go                 # 配置解析与验证
│   │   ├── config_test.go            # 配置测试
│   │   ├── engine.go                 # 执行引擎
│   │   ├── engine_test.go            # 引擎测试
│   │   └── status.go                 # 状态定义
│   ├── executor/
│   │   ├── executor.go               # 命令执行器
│   │   └── executor_test.go          # 执行器测试
│   ├── deploy/
│   │   ├── deployer.go               # 部署管理器
│   │   ├── deployer_test.go          # 部署测试
│   │   └── rollback.go               # 回滚管理
│   ├── trigger/
│   │   ├── trigger.go                # 触发管理器
│   │   └── trigger_test.go           # 触发测试
│   └── reporter/
│       ├── reporter.go               # 报告输出
│       └── reporter_test.go          # 报告测试
├── examples/
│   ├── simple.yaml                   # 简单流水线
│   ├── pipeline.yaml                 # 示例流水线
│   └── full-pipeline.yaml            # 完整 CI/CD 流水线
├── Dockerfile                        # Docker 构建
├── go.mod                            # Go 模块定义
└── docs/                             # 文档
```

## 核心模块实现

### 1. 配置解析 (config.go)

配置解析负责：
- 读取 YAML 文件
- 反序列化为 Go 结构体
- 校验配置合法性
- 检测循环依赖
- 解析触发配置
- 解析部署配置

**关键数据结构**:
```go
type PipelineConfig struct {
    Name      string            `yaml:"name"`
    Trigger   TriggerConfig     `yaml:"trigger"`
    Variables map[string]string `yaml:"variables"`
    Stages    []StageConfig     `yaml:"stages"`
}

type TriggerConfig struct {
    Push     *PushTrigger `yaml:"push,omitempty"`
    Schedule string       `yaml:"schedule,omitempty"`
    Manual   bool         `yaml:"manual,omitempty"`
}

type StageConfig struct {
    Name      string        `yaml:"name"`
    DependsOn []string      `yaml:"depends_on"`
    Tasks     []TaskConfig  `yaml:"tasks"`
    Deploy    *DeployConfig `yaml:"deploy,omitempty"`
}
```

**关键代码 - 循环依赖检测**:
```go
func checkCyclicDependency(config *PipelineConfig) error {
    // 使用 BFS 拓扑排序
    inDegree := make(map[string]int)
    adjacency := make(map[string][]string)
    // ... 构建邻接表和入度表
    // BFS 遍历
    for len(queue) > 0 {
        current := queue[0]
        queue = queue[1:]
        visited++
        for _, next := range adjacency[current] {
            inDegree[next]--
            if inDegree[next] == 0 {
                queue = append(queue, next)
            }
        }
    }
    if visited != len(config.Stages) {
        return fmt.Errorf("检测到循环依赖")
    }
    return nil
}
```

**执行分组算法**:
```go
func GetExecutionGroups(config *PipelineConfig) [][]string {
    // 按拓扑层级分组
    // 同一入度层级的阶段可以并行执行
    // 返回 [[A], [B, C], [D]] 形式的分组
}
```

### 2. 执行引擎 (engine.go)

引擎是流水线运行的核心，负责：
- 按依赖关系编排阶段
- 并行执行同组阶段
- 串行执行阶段内任务
- 传播失败和跳过状态

**并发控制**:
```go
for _, stageName := range group {
    wg.Add(1)
    go func(sc *StageConfig) {
        defer wg.Done()
        stageResult := e.executeStage(ctx, sc)
        // 使用 mutex 保护结果写入
        mu.Lock()
        *sr = *stageResult
        mu.Unlock()
    }(stageCfg)
}
wg.Wait()
```

**上下文取消支持**:
```go
select {
case <-ctx.Done():
    result.Status = StatusTimeout
    return result, ctx.Err()
default:
    // 继续执行
}
```

### 3. 命令执行器 (executor.go)

执行器接口设计：
```go
type Executor interface {
    Execute(ctx context.Context, command string, env map[string]string) (string, int, error)
    Type() string
}
```

**重试机制**:
```go
func RunWithRetry(ctx context.Context, executor Executor, command string,
    env map[string]string, maxRetries int) (string, int, int, error) {
    for attempt := 0; attempt <= maxRetries; attempt++ {
        output, code, err := executor.Execute(ctx, command, env)
        if err == nil && code == 0 {
            return output, 0, attempt, nil
        }
        // 指数退避重试
        if attempt < maxRetries {
            time.Sleep(time.Duration(attempt+1) * time.Second)
        }
    }
    return lastOutput, exitCode, maxRetries, lastErr
}
```

### 4. 部署管理器 (deploy/deployer.go)

部署管理器负责：
- 环境注册和管理
- 执行部署（支持多种策略）
- 版本历史管理
- 回滚操作

**部署策略实现**:
```go
func (d *Deployer) Deploy(ctx context.Context, envName, version string, strategy Strategy) (*Deployment, error) {
    // 保存回滚点
    d.rollback.SaveSnapshot(envName, env.Version)

    // 根据策略执行部署
    switch strategy {
    case StrategyRolling:
        err = d.rollingDeploy(ctx, env, deployment)
    case StrategyBlueGreen:
        err = d.blueGreenDeploy(ctx, env, deployment)
    case StrategyCanary:
        err = d.canaryDeploy(ctx, env, deployment)
    }
    // ...
}
```

**滚动部署实现**:
```go
func (d *Deployer) rollingDeploy(ctx context.Context, env *Environment, deployment *Deployment) error {
    steps := []string{
        "准备部署环境",
        "上传制品",
        "更新配置",
        "重启服务",
        "健康检查",
    }

    for i, step := range steps {
        select {
        case <-ctx.Done():
            return ctx.Err()
        default:
        }
        deployment.Metadata[fmt.Sprintf("step_%d", i)] = step
        time.Sleep(100 * time.Millisecond)
    }
    return nil
}
```

### 5. 回滚管理器 (deploy/rollback.go)

回滚管理器负责：
- 版本快照存储
- 版本历史管理
- 回滚版本获取

**版本快照**:
```go
type Snapshot struct {
    Version   string            `json:"version"`
    Timestamp int64             `json:"timestamp"`
    Config    map[string]string `json:"config"`
}

func (rm *RollbackManager) SaveSnapshot(envName, version string) {
    snapshot := &Snapshot{
        Version:   version,
        Timestamp: time.Now().UnixNano(),
        Config:    make(map[string]string),
    }

    snapshots := rm.snapshots[envName]
    snapshots = append(snapshots, snapshot)

    // 保持最大版本数限制
    if len(snapshots) > rm.maxVersions {
        snapshots = snapshots[len(snapshots)-rm.maxVersions:]
    }

    rm.snapshots[envName] = snapshots
}
```

### 6. 触发管理器 (trigger/trigger.go)

触发管理器负责：
- 注册触发处理函数
- 处理不同类型的触发事件
- 分支和路径过滤

**触发类型**:
```go
type TriggerType string

const (
    TriggerPush     TriggerType = "push"     // Git Push 触发
    TriggerSchedule TriggerType = "schedule" // 定时触发
    TriggerManual   TriggerType = "manual"   // 手动触发
)
```

**分支过滤**:
```go
func (m *Manager) matchBranch(branch string) bool {
    if m.config.Push == nil || len(m.config.Push.Branches) == 0 {
        return true // 无限制
    }

    for _, b := range m.config.Push.Branches {
        if b == "*" || b == branch {
            return true
        }
        // 支持通配符
        if matched, _ := filepath.Match(b, branch); matched {
            return true
        }
    }
    return false
}
```

### 7. 报告器 (reporter.go)

报告器负责格式化输出执行过程：
- 流水线开始/结束
- 阶段进度
- 任务执行详情
- 错误信息

## YAML 配置规范

### 完整配置格式

```yaml
name: "流水线名称"

# 触发配置
trigger:
  push:
    branches: [main, develop]
    paths: ["src/**"]
  schedule: "0 2 * * *"
  manual: true

# 全局变量
variables:
  APP_NAME: "myapp"

stages:
  - name: "阶段名"
    depends_on: ["前置阶段"]  # 可选
    tasks:
      - name: "任务名"
        command: "要执行的命令"
        image: "docker镜像"    # 可选
        env:                   # 可选
          KEY: value
        timeout: 60            # 可选，秒
        retries: 3             # 可选
    deploy:                    # 可选，仅部署阶段
      strategy: rolling        # rolling, blue-green, canary
      targets:
        - name: production
          url: "https://www.example.com"
          region: "us-east-1"
          weight: 100
      rollback:
        enabled: true
        max_versions: 5
        health_check: 60
```

## 依赖关系处理

### 拓扑排序流程
1. 构建邻接表和入度表
2. 将入度为 0 的节点加入队列
3. BFS 遍历，减少后继节点入度
4. 入度变为 0 时加入队列
5. 如果访问节点数 != 总节点数，说明有环

### 跳过逻辑
当一个阶段失败时，所有直接或间接依赖它的阶段都会被标记为 Skipped。

## 测试覆盖

### 单元测试
- 配置解析测试
- 依赖检测测试
- 执行器测试
- 部署器测试
- 触发器测试

### 集成测试
- 完整流水线执行测试
- 并行阶段测试
- 失败和跳过测试

```bash
# 运行所有测试
go test ./...

# 运行特定包测试
go test ./internal/pipeline/...
go test ./internal/deploy/...
go test ./internal/trigger/...
```
