# 04 - 测试: CI/CD 流水线

## 测试策略

### 测试金字塔

```
        /  E2E  \          少量：完整流水线执行
       /──────────\
      / 集成测试    \       中量：引擎 + 执行器
     /────────────────\
    /    单元测试       \   大量：配置解析、状态、报告
   /────────────────────\
```

### 测试覆盖率目标

| 模块 | 目标覆盖率 | 说明 |
|------|-----------|------|
| pipeline/config | > 90% | 配置解析和校验 |
| pipeline/engine | > 80% | 执行引擎核心逻辑 |
| executor | > 85% | 命令执行和重试 |
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

## 运行所有测试

```bash
# 运行所有测试
go test ./... -v

# 运行测试并生成覆盖率报告
go test ./... -coverprofile=coverage.out
go tool cover -html=coverage.out -o coverage.html

# 运行测试并显示覆盖率
go test ./... -cover
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
```
