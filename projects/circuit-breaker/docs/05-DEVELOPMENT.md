# 开发文档: 熔断器开发指南

## 1. 开发环境

### 1.1 环境要求

- Go 1.21+
- 操作系统：Linux/macOS/Windows
- 编辑器：VS Code / GoLand / Vim

### 1.2 环境配置

```bash
# 安装Go
# https://golang.org/doc/install

# 验证安装
go version

# 配置GOPATH
export GOPATH=$HOME/go
export PATH=$PATH:$GOPATH/bin
```

## 2. 项目结构

```
circuit-breaker/
├── README.md                    # 项目说明
├── src/                         # 源代码
│   ├── circuit_breaker.go      # 熔断器核心
│   ├── states.go               # 状态定义
│   ├── metrics.go              # 指标统计
│   └── fallback.go             # 降级策略
├── tests/                       # 测试代码
│   ├── circuit_breaker_test.go
│   ├── states_test.go
│   └── metrics_test.go
├── examples/                    # 使用示例
│   └── main.go
└── docs/                        # 学习文档
    ├── 01-RESEARCH.md
    ├── 02-DESIGN.md
    ├── 03-IMPLEMENTATION.md
    ├── 04-TESTING.md
    └── 05-DEVELOPMENT.md
```

## 3. 开发流程

### 3.1 功能开发

1. **需求分析**
   - 理解熔断器模式
   - 确定功能需求
   - 设计API接口

2. **设计阶段**
   - 设计状态机
   - 设计指标统计
   - 设计降级策略

3. **编码实现**
   - 实现核心组件
   - 编写单元测试
   - 代码审查

4. **测试验证**
   - 运行单元测试
   - 运行集成测试
   - 性能测试

5. **文档编写**
   - 编写API文档
   - 编写使用示例
   - 更新README

### 3.2 代码规范

**命名规范：**
- 包名：小写单词
- 结构体：大写驼峰
- 函数：大写驼峰（导出）/ 小写驼峰（内部）
- 常量：大写驼峰或下划线分隔

**注释规范：**
- 包注释：每个包必须有包注释
- 导出函数：必须有注释
- 复杂逻辑：必须有注释

**错误处理：**
- 使用 `error` 接口
- 提供有意义的错误信息
- 使用 `fmt.Errorf` 格式化错误

### 3.3 Git规范

**提交信息格式：**
```
<type>(<scope>): <subject>

<body>

<footer>
```

**类型：**
- feat: 新功能
- fix: 修复bug
- docs: 文档更新
- style: 代码格式调整
- refactor: 重构
- test: 测试相关
- chore: 构建/工具相关

**示例：**
```
feat(circuit-breaker): 实现熔断器状态机

- 实现关闭、打开、半开三种状态
- 支持失败率统计
- 支持降级策略

Closes #123
```

## 4. 开发工具

### 4.1 Go工具链

```bash
# 格式化代码
go fmt ./...

# 静态检查
go vet ./...

# 运行测试
go test ./tests/...

# 生成文档
go doc ./src/

# 构建项目
go build ./...
```

### 4.2 IDE配置

**VS Code：**
- 安装Go扩展
- 配置gopls
- 配置linting

**GoLand：**
- 自动配置
- 代码补全
- 重构工具

### 4.3 调试工具

**Delve调试器：**
```bash
# 安装
go install github.com/go-delve/delve/cmd/dlv@latest

# 调试测试
dlv test ./tests/...

# 调试程序
dlv debug ./examples/main.go
```

## 5. 依赖管理

### 5.1 Go Modules

```bash
# 初始化模块
go mod init circuit-breaker

# 添加依赖
go get github.com/xxx

# 整理依赖
go mod tidy

# 查看依赖
go mod graph
```

### 5.2 依赖选择

- 优先使用标准库
- 选择活跃维护的库
- 避免过度依赖

## 6. 性能优化

### 6.1 锁优化

- 使用读写锁
- 最小化锁持有时间
- 避免锁嵌套

### 6.2 内存优化

- 复用对象
- 避免不必要的分配
- 使用sync.Pool

### 6.3 CPU优化

- 避免重复计算
- 使用缓存
- 并行处理

## 7. 并发编程

### 7.1 Goroutine

```go
go func() {
    // 并发执行
}()
```

### 7.2 Channel

```go
ch := make(chan int, 10)
ch <- 1
value := <-ch
```

### 7.3 Sync包

```go
var mu sync.Mutex
mu.Lock()
defer mu.Unlock()

var wg sync.WaitGroup
wg.Add(1)
go func() {
    defer wg.Done()
}()
wg.Wait()
```

### 7.4 原子操作

```go
var counter int64
atomic.AddInt64(&counter, 1)
value := atomic.LoadInt64(&counter)
```

## 8. 错误处理

### 8.1 错误类型

```go
type CircuitBreakerError struct {
    Code    int
    Message string
}

func (e *CircuitBreakerError) Error() string {
    return e.Message
}
```

### 8.2 错误包装

```go
if err != nil {
    return fmt.Errorf("failed to execute: %w", err)
}
```

### 8.3 错误检查

```go
if errors.Is(err, ErrCircuitOpen) {
    // 处理熔断器打开错误
}
```

## 9. 测试开发

### 9.1 测试文件

```go
// file_test.go
package tests

import "testing"

func TestXxx(t *testing.T) {
    // 测试代码
}
```

### 9.2 测试函数

```go
func TestXxx(t *testing.T) {
    // 准备数据
    // 执行操作
    // 验证结果
    if result != expected {
        t.Errorf("Expected %v, got %v", expected, result)
    }
}
```

### 9.3 子测试

```go
func TestXxx(t *testing.T) {
    t.Run("subtest1", func(t *testing.T) {
        // 子测试1
    })
    t.Run("subtest2", func(t *testing.T) {
        // 子测试2
    })
}
```

### 9.4 表驱动测试

```go
func TestXxx(t *testing.T) {
    tests := []struct {
        name     string
        input    int
        expected int
    }{
        {"case1", 1, 2},
        {"case2", 2, 4},
    }

    for _, test := range tests {
        t.Run(test.name, func(t *testing.T) {
            result := function(test.input)
            if result != test.expected {
                t.Errorf("Expected %d, got %d", test.expected, result)
            }
        })
    }
}
```

## 10. 文档开发

### 10.1 代码注释

```go
// CircuitBreaker 熔断器
type CircuitBreaker struct {
    // 字段注释
}

// Execute 执行请求
// 参数：request - 请求函数
// 返回：结果和错误
func (cb *CircuitBreaker) Execute(request func() (interface{}, error)) (interface{}, error) {
    // 实现
}
```

### 10.2 包注释

```go
// Package src 实现熔断器模式
// 提供熔断器状态机、指标统计和降级策略
package src
```

### 10.3 示例代码

```go
func ExampleCircuitBreaker_Execute() {
    breaker := NewCircuitBreaker(DefaultConfig())
    result, err := breaker.Execute(func() (interface{}, error) {
        return "success", nil
    })
    fmt.Println(result, err)
    // Output: success <nil>
}
```

## 11. 构建部署

### 11.1 构建命令

```bash
# 构建可执行文件
go build -o circuit-breaker ./examples/main.go

# 交叉编译
GOOS=linux GOARCH=amd64 go build -o circuit-breaker-linux ./examples/main.go
```

### 11.2 Docker部署

```dockerfile
FROM golang:1.21-alpine AS builder
WORKDIR /app
COPY . .
RUN go build -o circuit-breaker ./examples/main.go

FROM alpine:latest
COPY --from=builder /app/circuit-breaker /usr/local/bin/
CMD ["circuit-breaker"]
```

### 11.3 版本管理

```bash
# 打标签
git tag -a v1.0.0 -m "Release v1.0.0"
git push origin v1.0.0
```

## 12. 调试技巧

### 12.1 日志调试

```go
import "log"

log.Printf("State: %v", cb.GetState())
log.Printf("Metrics: %+v", cb.GetMetrics())
```

### 12.2 断点调试

使用Delve设置断点，逐步调试。

### 12.3 性能分析

```bash
# CPU分析
go test -cpuprofile=cpu.prof ./tests/...
go tool pprof cpu.prof

# 内存分析
go test -memprofile=mem.prof ./tests/...
go tool pprof mem.prof
```

## 13. 常见问题

### 13.1 编译错误

- 检查语法错误
- 检查导入路径
- 检查包名

### 13.2 测试失败

- 检查测试逻辑
- 检查依赖关系
- 检查环境变量

### 13.3 性能问题

- 使用性能分析工具
- 检查锁竞争
- 检查内存分配

## 14. 最佳实践

### 14.1 代码组织

- 单一职责原则
- 接口隔离
- 依赖注入

### 14.2 错误处理

- 显式错误处理
- 错误包装
- 错误恢复

### 14.3 并发安全

- 使用锁保护共享状态
- 避免竞态条件
- 使用channel通信

### 14.4 测试驱动

- 先写测试
- 再写实现
- 持续重构

## 15. 学习资源

### 15.1 官方文档

- [Go语言规范](https://golang.org/ref/spec)
- [Go标准库](https://pkg.go.dev/std)
- [Go测试](https://pkg.go.dev/testing)

### 15.2 推荐书籍

- 《Go语言实战》
- 《Go并发编程实战》
- 《Go语言高级编程》

### 15.3 在线资源

- [Go博客](https://go.dev/blog/)
- [Go Playground](https://go.dev/play/)
- [Go Wiki](https://go.dev/wiki/)
