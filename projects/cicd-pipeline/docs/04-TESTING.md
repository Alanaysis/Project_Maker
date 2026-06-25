# 04 - 测试: CI/CD 流水线

## 测试策略

### 测试金字塔

```
        /  E2E  \          少量：完整流水线执行
       /──────────\
      / 集成测试    \       中量：引擎 + 执行器 + 部署
     /────────────────\
    /    单元测试       \   大量：配置解析、状态、报告、触发
   /────────────────────\
```

### 测试覆盖率目标

| 模块 | 目标覆盖率 | 说明 |
|------|-----------|------|
| pipeline/config | > 90% | 配置解析和校验 |
| pipeline/engine | > 80% | 执行引擎核心逻辑 |
| executor | > 85% | 命令执行和重试 |
| deploy | > 80% | 部署管理和回滚 |
| trigger | > 85% | 触发机制 |
| reporter | > 75% | 输出格式化 |

## 单元测试

### 配置解析测试

```bash
# 运行配置解析测试
go test ./internal/pipeline/ -v -run TestParseConfig
```

**测试场景**：
- 正常配置解析
- 空名称校验
- 空阶段列表校验
- 空任务命令校验
- 重复阶段名校验
- 无效依赖校验
- 自依赖校验
- 循环依赖检测
- 触发配置解析
- 部署配置解析

### 引擎测试

```bash
# 运行引擎测试
go test ./internal/pipeline/ -v -run TestEngine
```

**测试场景**：
- 简单流水线执行
- 并行阶段执行
- 任务失败终止阶段
- 依赖失败跳过阶段
- 超时处理
- 上下文取消
- 多任务串行执行

### 执行器测试

```bash
# 运行执行器测试
go test ./internal/executor/ -v
```

**测试场景**：
- 命令成功执行
- 命令失败处理
- 环境变量传递
- 上下文取消
- 重试机制

### 部署管理器测试

```bash
# 运行部署管理器测试
go test ./internal/deploy/ -v
```

**测试场景**：
- 环境注册和获取
- 滚动部署执行
- 蓝绿部署执行
- 金丝雀部署执行
- 部署历史查询
- 环境不存在处理

**测试代码示例**:
```go
func TestDeployRolling(t *testing.T) {
    d := NewDeployer()
    d.RegisterEnvironment(&Environment{
        Name:    "test",
        URL:     "https://test.example.com",
        Version: "v1.0.0",
    })

    ctx := context.Background()
    deployment, err := d.Deploy(ctx, "test", "v1.1.0", StrategyRolling)
    if err != nil {
        t.Fatalf("Deploy 失败: %v", err)
    }

    if deployment.Status != StatusSuccess {
        t.Errorf("Status = %s, want %s", deployment.Status, StatusSuccess)
    }
}
```

### 回滚管理器测试

```bash
# 运行回滚测试
go test ./internal/deploy/ -v -run TestRollback
```

**测试场景**：
- 版本快照保存
- 获取上一个版本
- 版本历史查询
- 回滚执行
- 无版本可回滚处理

**测试代码示例**:
```go
func TestRollback(t *testing.T) {
    d := NewDeployer()
    d.RegisterEnvironment(&Environment{
        Name:    "test",
        URL:     "https://test.example.com",
        Version: "v1.0.0",
    })

    ctx := context.Background()

    // 第一次部署
    d.Deploy(ctx, "test", "v1.1.0", StrategyRolling)

    // 第二次部署
    d.Deploy(ctx, "test", "v1.2.0", StrategyRolling)

    // 回滚
    deployment, err := d.Rollback(ctx, "test")
    if err != nil {
        t.Fatalf("Rollback 失败: %v", err)
    }

    if deployment.Status != StatusRolledBack {
        t.Errorf("Status = %s, want %s", deployment.Status, StatusRolledBack)
    }

    // 检查版本已回滚
    env, _ := d.GetEnvironment("test")
    if env.Version != "v1.1.0" {
        t.Errorf("Version = %s, want %s", env.Version, "v1.1.0")
    }
}
```

### 触发管理器测试

```bash
# 运行触发管理器测试
go test ./internal/trigger/ -v
```

**测试场景**：
- 手动触发
- 手动触发禁用
- Push 触发
- 分支匹配
- 分支不匹配
- 路径过滤
- 通配符分支
- 多个处理函数

**测试代码示例**:
```go
func TestPushTrigger(t *testing.T) {
    config := &TriggerConfig{
        Push: &PushConfig{
            Branches: []string{"main", "develop"},
        },
    }

    m := NewManager(config)

    called := false
    m.RegisterHandler(TriggerPush, func(ctx context.Context, event *TriggerEvent) error {
        called = true
        if event.Branch != "main" {
            t.Errorf("Branch = %s, want %s", event.Branch, "main")
        }
        return nil
    })

    ctx := context.Background()
    err := m.TriggerPush(ctx, "main", "abc123", "testuser", "test commit", []string{"main.go"})
    if err != nil {
        t.Fatalf("TriggerPush 失败: %v", err)
    }

    if !called {
        t.Error("处理函数未被调用")
    }
}
```

### 报告器测试

```bash
# 运行报告器测试
go test ./internal/reporter/ -v
```

**测试场景**：
- 各种事件输出格式
- 详细模式输出
- 错误信息显示

## 集成测试

### 完整流水线测试

```bash
# 使用示例配置运行
go run ./cmd/cicd run -f examples/pipeline.yaml -v
```

**验证点**：
1. 所有阶段按顺序执行
2. 依赖关系正确处理
3. 并行阶段同时执行
4. 输出格式正确
5. 最终状态正确

### 部署流程测试

```bash
# 运行完整 CI/CD 流水线
go run ./cmd/cicd run -f examples/full-pipeline.yaml -v
```

**验证点**：
1. 构建阶段正常执行
2. 测试阶段包括单元测试、集成测试、覆盖率
3. 部署阶段支持滚动/蓝绿/金丝雀策略
4. 回滚机制正常工作

## 运行所有测试

```bash
# 运行所有测试
go test ./... -v

# 运行测试并生成覆盖率报告
go test ./... -coverprofile=coverage.out
go tool cover -html=coverage.out -o coverage.html

# 运行测试并显示覆盖率
go test ./... -cover

# 运行特定包的测试
go test ./internal/pipeline/...
go test ./internal/deploy/...
go test ./internal/trigger/...
```

## 测试数据

### 测试用 YAML 配置

**简单流水线**:
```yaml
name: test
stages:
  - name: build
    tasks:
      - name: compile
        command: echo "build"
```

**带依赖的流水线**:
```yaml
name: test
stages:
  - name: build
    tasks:
      - name: compile
        command: echo "build"
  - name: test
    depends_on:
      - build
    tasks:
      - name: test
        command: echo "test"
```

**并行流水线**:
```yaml
name: test
stages:
  - name: build
    tasks:
      - name: compile
        command: echo "build"
  - name: lint
    depends_on:
      - build
    tasks:
      - name: lint
        command: echo "lint"
  - name: security
    depends_on:
      - build
    tasks:
      - name: scan
        command: echo "scan"
```

**带触发配置的流水线**:
```yaml
name: test
trigger:
  push:
    branches: [main]
  manual: true
stages:
  - name: build
    tasks:
      - name: compile
        command: echo "build"
```

**带部署配置的流水线**:
```yaml
name: test
stages:
  - name: deploy
    deploy:
      strategy: rolling
      targets:
        - name: production
          url: "https://www.example.com"
      rollback:
        enabled: true
        max_versions: 5
    tasks:
      - name: deploy
        command: echo "deploy"
```

## 持续集成

项目自身的 CI 配置示例（GitHub Actions）：

```yaml
name: CI
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-go@v4
        with:
          go-version: '1.21'
      - run: go test ./... -v -cover
      - run: go build ./cmd/cicd

  deploy-test:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v3
      - run: go run ./cmd/cicd run -f examples/full-pipeline.yaml
```
