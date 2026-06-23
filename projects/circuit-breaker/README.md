# 熔断降级 (Circuit Breaker)

实现熔断器模式，学习分布式系统中的容错机制。

## 项目概述

这是一个学习型项目，旨在深入理解熔断器模式（Circuit Breaker Pattern），这是微服务架构中常用的容错模式。

### 核心概念

熔断器模式通过监控服务调用的失败率，在检测到异常时自动"熔断"，防止故障扩散，实现优雅降级。

### 状态机

```
关闭 (Closed) → 打开 (Open) → 半开 (Half-Open) → 关闭 (Closed)
```

- **关闭状态**：正常处理请求，统计失败率
- **打开状态**：直接拒绝请求，返回降级响应
- **半开状态**：允许部分请求通过，测试服务是否恢复

## 快速开始

### 1. 运行测试

```bash
cd projects/circuit-breaker
go test ./tests/...
```

### 2. 使用示例

```go
package main

import (
    "fmt"
    "time"
    "circuit-breaker/src"
)

func main() {
    // 创建熔断器
    breaker := src.NewCircuitBreaker(src.Config{
        FailureThreshold: 5,
        SuccessThreshold: 3,
        Timeout:         30 * time.Second,
    })

    // 执行可能失败的操作
    result, err := breaker.Execute(func() (interface{}, error) {
        // 模拟远程调用
        return "success", nil
    })

    if err != nil {
        fmt.Printf("请求失败: %v\n", err)
    } else {
        fmt.Printf("请求成功: %v\n", result)
    }
}
```

## 项目结构

```
circuit-breaker/
├── README.md                    # 项目说明
├── src/                         # 源代码
│   ├── circuit_breaker.go      # 熔断器核心实现
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

## 学习目标

通过本项目，您将学习到：

1. **熔断原理**：理解熔断器模式的工作机制
2. **状态机**：掌握有限状态机的设计与实现
3. **降级策略**：学会设计优雅的降级方案
4. **指标统计**：理解如何收集和分析系统指标

## 文档导航

- [研究文档](docs/01-RESEARCH.md) - 熔断器模式的理论基础
- [设计文档](docs/02-DESIGN.md) - 系统架构设计
- [实现文档](docs/03-IMPLEMENTATION.md) - 核心代码实现
- [测试文档](docs/04-TESTING.md) - 测试策略与用例
- [开发文档](docs/05-DEVELOPMENT.md) - 开发指南
- [学习笔记](LEARNING_NOTES.md) - 学习过程记录

## 依赖

- Go 1.21+
- 无第三方依赖

## 许可证

本项目仅用于学习目的。
