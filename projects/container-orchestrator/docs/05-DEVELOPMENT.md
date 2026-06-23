# 05 - 开发指南

## 开发环境

### 前置要求

- Go 1.21+
- Docker（可选，用于容器测试）
- Git

### 安装依赖

```bash
cd projects/container-orchestrator
go mod download
```

### 项目结构

```
container-orchestrator/
├── cmd/                    # 主程序入口
│   └── main.go
├── docs/                   # 文档
├── pkg/                    # 核心包
│   ├── api/               # API 服务器
│   ├── container/         # 容器定义
│   ├── discovery/         # 服务发现
│   ├── health/            # 健康检查
│   ├── manager/           # 管理器
│   ├── scaler/            # 扩缩容
│   └── scheduler/         # 调度器
├── tests/                  # 测试文件
├── examples/               # 示例代码
├── go.mod
├── go.sum
├── Makefile
└── README.md
```

## 核心模块

### 1. Container（容器定义）

**职责**：
- 定义容器、节点、服务的数据结构
- 管理容器状态
- 资源计算

**关键类型**：
- `Container`：容器实例
- `Node`：集群节点
- `Service`：服务定义
- `Resources`：资源规格

### 2. Scheduler（调度器）

**职责**：
- 将容器分配到节点
- 实现多种调度策略
- 管理资源分配

**调度策略**：
- `BinPacking`：紧凑调度
- `Spread`：分散调度
- `RoundRobin`：轮询调度

### 3. Discovery（服务发现）

**职责**：
- 服务注册与注销
- 端点管理
- 服务解析

**核心功能**：
- `RegisterService`：注册服务
- `RegisterEndpoint`：注册端点
- `Resolve`：解析服务地址

### 4. Health（健康检查）

**职责**：
- 执行健康检查
- 管理健康状态
- 发送健康事件

**检查类型**：
- HTTP 检查
- TCP 检查
- 命令检查

### 5. Scaler（扩缩容）

**职责**：
- 自动扩缩容
- 指标收集
- 手动扩缩容

**扩缩容策略**：
- 基于 CPU 使用率
- 基于内存使用率
- 冷却时间控制

### 6. Manager（管理器）

**职责**：
- 协调所有组件
- 管理服务生命周期
- 提供统一接口

## 开发流程

### 1. 添加新功能

1. **设计**：在 `docs/02-DESIGN.md` 中记录设计
2. **实现**：在对应的 `pkg/` 目录中实现
3. **测试**：在 `tests/` 目录中添加测试
4. **文档**：更新相关文档

### 2. 代码规范

#### 命名规范
- 包名：小写单词
- 类型名：大写驼峰
- 函数名：大写驼峰
- 变量名：小写驼峰
- 常量名：大写下划线

#### 注释规范
```go
// FunctionName does something
func FunctionName() {
    // Implementation
}
```

#### 错误处理
```go
result, err := doSomething()
if err != nil {
    return fmt.Errorf("failed to do something: %w", err)
}
```

### 3. 测试规范

#### 单元测试
```go
func TestFunctionName(t *testing.T) {
    // Arrange
    input := "test"

    // Act
    result := FunctionName(input)

    // Assert
    assert.Equal(t, expected, result)
}
```

#### 集成测试
```go
func TestIntegration(t *testing.T) {
    // Setup
    server := setupTestServer()

    // Test
    req := httptest.NewRequest(http.MethodGet, "/api/nodes", nil)
    w := httptest.NewRecorder()
    server.ServeHTTP(w, req)

    // Assert
    assert.Equal(t, http.StatusOK, w.Code)
}
```

## 常用命令

### 构建

```bash
# 构建项目
go build -o bin/orchestrator ./cmd/main.go

# 交叉编译
GOOS=linux GOARCH=amd64 go build -o bin/orchestrator-linux ./cmd/main.go
```

### 测试

```bash
# 运行所有测试
go test ./...

# 运行特定测试
go test ./tests/container_test.go

# 运行带覆盖率的测试
go test -cover ./...

# 生成覆盖率报告
go test -coverprofile=coverage.out ./...
go tool cover -html=coverage.out
```

### 代码检查

```bash
# 格式化代码
gofmt -w .

# 检查代码风格
golangci-lint run

# 检查安全漏洞
gosec ./...
```

## 调试技巧

### 1. 日志输出
```go
import "log"

log.Printf("Container %s scheduled to node %s", container.ID, node.ID)
```

### 2. 断点调试
使用 IDE 的调试功能设置断点

### 3. 测试调试
```bash
# 运行单个测试并显示详细输出
go test -v -run TestFunctionName ./tests/
```

## 扩展开发

### 1. 添加新的调度策略

```go
// 在 scheduler/scheduler.go 中添加
func (s *Scheduler) customStrategy(nodes []*container.Node, c *container.Container) *container.Node {
    // 实现自定义策略
    return nodes[0]
}
```

### 2. 添加新的健康检查器

```go
// 在 health/health.go 中添加
type CustomHealthChecker struct{}

func (c *CustomHealthChecker) Check(ctx context.Context, container *container.Container) (*HealthResult, error) {
    // 实现自定义检查
    return &HealthResult{State: StateHealthy}, nil
}
```

### 3. 添加新的扩缩容策略

```go
// 在 scaler/scaler.go 中添加
func (s *Scaler) customEvaluate(serviceID string) *ScaleDecision {
    // 实现自定义策略
    return nil
}
```

## 部署

### 1. 本地部署

```bash
# 构建
go build -o bin/orchestrator ./cmd/main.go

# 运行
./bin/orchestrator
```

### 2. Docker 部署

```dockerfile
FROM golang:1.21-alpine AS builder
WORKDIR /app
COPY go.mod go.sum ./
RUN go mod download
COPY . .
RUN CGO_ENABLED=0 GOOS=linux go build -o orchestrator ./cmd/main.go

FROM alpine:latest
RUN apk --no-cache add ca-certificates
WORKDIR /root/
COPY --from=builder /app/orchestrator .
CMD ["./orchestrator"]
```

### 3. Kubernetes 部署

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: orchestrator
spec:
  replicas: 1
  selector:
    matchLabels:
      app: orchestrator
  template:
    metadata:
      labels:
        app: orchestrator
    spec:
      containers:
      - name: orchestrator
        image: orchestrator:latest
        ports:
        - containerPort: 8080
```

## 故障排查

### 常见问题

#### 1. 编译错误
```bash
# 检查依赖
go mod tidy

# 清理缓存
go clean -cache
```

#### 2. 测试失败
```bash
# 查看详细输出
go test -v ./...

# 运行单个测试
go test -v -run TestName ./tests/
```

#### 3. 运行时错误
- 检查日志输出
- 使用调试器
- 检查资源限制

## 最佳实践

### 1. 代码组织
- 按功能模块组织代码
- 保持包的职责单一
- 避免循环依赖

### 2. 错误处理
- 使用明确的错误类型
- 提供有用的错误信息
- 适当包装错误

### 3. 并发安全
- 使用适当的同步原语
- 避免数据竞争
- 保持锁的粒度小

### 4. 测试
- 编写全面的测试
- 使用 mock 隔离依赖
- 保持测试独立
