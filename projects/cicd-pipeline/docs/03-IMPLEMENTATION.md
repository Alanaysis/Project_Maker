# 03 - 实现: CI/CD 流水线

## 项目结构

```
cicd-pipeline/
├── cmd/cicd/main.go              # CLI 入口
├── internal/
│   ├── pipeline/
│   │   ├── config.go             # 配置解析与验证
│   │   ├── config_test.go        # 配置测试
│   │   ├── engine.go             # 执行引擎
│   │   ├── engine_test.go        # 引擎测试
│   │   └── status.go             # 状态定义
│   ├── executor/
│   │   ├── executor.go           # 命令执行器
│   │   └── executor_test.go      # 执行器测试
│   └── reporter/
│       ├── reporter.go           # 报告输出
│       └── reporter_test.go      # 报告测试
├── examples/
│   └── pipeline.yaml             # 示例配置
├── Dockerfile                    # Docker 构建
├── go.mod                        # Go 模块定义
└── docs/                         # 文档
```

## 核心模块实现

### 1. 配置解析 (config.go)

配置解析负责：
- 读取 YAML 文件
- 反序列化为 Go 结构体
- 校验配置合法性
- 检测循环依赖

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

### 4. 报告器 (reporter.go)

报告器负责格式化输出执行过程：
- 流水线开始/结束
- 阶段进度
- 任务执行详情
- 错误信息

## YAML 配置规范

```yaml
name: "流水线名称"
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
