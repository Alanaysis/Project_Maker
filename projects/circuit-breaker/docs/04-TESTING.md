# 测试文档: 熔断器测试策略

## 1. 测试概述

### 1.1 测试目标

- 验证熔断器状态机的正确性
- 验证指标统计的准确性
- 验证降级策略的有效性
- 验证并发安全性

### 1.2 测试范围

- 单元测试：核心组件测试
- 集成测试：端到端场景测试
- 并发测试：多goroutine访问测试

## 2. 测试结构

```
tests/
├── circuit_breaker_test.go  # 熔断器核心测试
├── states_test.go          # 状态测试
└── metrics_test.go         # 指标测试
```

## 3. 单元测试

### 3.1 状态测试 (states_test.go)

**测试用例：**

1. **TestState_String**
   - 验证状态的字符串表示
   - 测试所有状态类型

2. **TestState_IsValid**
   - 验证状态的有效性检查
   - 测试有效状态和无效状态

3. **TestState_CanExecute**
   - 验证状态是否允许执行请求
   - 关闭状态：允许
   - 打开状态：不允许
   - 半开状态：允许

### 3.2 指标测试 (metrics_test.go)

**测试用例：**

1. **TestMetrics_RecordSuccess**
   - 验证成功请求记录
   - 检查计数器更新

2. **TestMetrics_RecordFailure**
   - 验证失败请求记录
   - 检查计数器更新

3. **TestMetrics_GetFailureRate**
   - 验证失败率计算
   - 测试无请求情况
   - 测试正常情况

4. **TestMetrics_ConsecutiveCounters**
   - 验证连续成功/失败计数
   - 测试计数重置

5. **TestMetrics_Reset**
   - 验证指标重置功能

### 3.3 熔断器测试 (circuit_breaker_test.go)

**测试用例：**

1. **TestCircuitBreaker_ClosedState**
   - 验证初始状态为关闭
   - 验证成功请求处理
   - 验证状态保持关闭

2. **TestCircuitBreaker_FailureThreshold**
   - 验证失败阈值触发
   - 连续失败N次后状态变为打开
   - 打开状态下拒绝请求

3. **TestCircuitBreaker_TimeoutTransition**
   - 验证超时状态转换
   - 触发熔断
   - 等待超时
   - 再次执行进入半开状态

4. **TestCircuitBreaker_HalfOpenToClosed**
   - 验证半开状态恢复
   - 触发熔断
   - 等待超时
   - 半开状态下连续成功
   - 状态恢复为关闭

5. **TestCircuitBreaker_HalfOpenToOpen**
   - 验证半开状态失败
   - 触发熔断
   - 等待超时
   - 半开状态下失败
   - 状态回到打开

6. **TestCircuitBreaker_Fallback**
   - 验证降级策略执行
   - 设置降级策略
   - 触发熔断
   - 验证降级响应

7. **TestCircuitBreaker_Reset**
   - 验证熔断器重置
   - 触发熔断
   - 重置熔断器
   - 验证状态恢复

8. **TestCircuitBreaker_FailureRate**
   - 验证失败率触发
   - 设置失败率阈值
   - 发送多个请求
   - 验证失败率达到阈值后触发熔断

## 4. 测试用例详解

### 4.1 状态转换测试

```go
func TestCircuitBreaker_TimeoutTransition(t *testing.T) {
    cb := src.NewCircuitBreaker(src.Config{
        FailureThreshold: 2,
        SuccessThreshold: 2,
        Timeout:         100 * time.Millisecond,
    })

    // 触发熔断
    for i := 0; i < 2; i++ {
        _, _ = cb.Execute(func() (interface{}, error) {
            return nil, errors.New("test error")
        })
    }

    if cb.GetState() != src.StateOpen {
        t.Errorf("Expected state to be Open, got %v", cb.GetState())
    }

    // 等待超时
    time.Sleep(150 * time.Millisecond)

    // 再次执行，应该进入半开状态
    _, _ = cb.Execute(func() (interface{}, error) {
        return "success", nil
    })

    if cb.GetState() != src.StateHalfOpen {
        t.Errorf("Expected state to be HalfOpen, got %v", cb.GetState())
    }
}
```

**测试要点：**
- 使用短超时时间（100ms）加快测试
- 等待超时后验证状态转换
- 验证半开状态允许执行请求

### 4.2 降级策略测试

```go
func TestCircuitBreaker_Fallback(t *testing.T) {
    cb := src.NewCircuitBreaker(src.Config{
        FailureThreshold: 2,
        SuccessThreshold: 2,
        Timeout:         1 * time.Second,
    })

    // 设置降级策略
    fallback := src.NewStaticFallback("fallback value", nil)
    cb.SetFallback(fallback)

    // 触发熔断
    for i := 0; i < 2; i++ {
        _, _ = cb.Execute(func() (interface{}, error) {
            return nil, errors.New("test error")
        })
    }

    // 执行请求，应该返回降级值
    result, err := cb.Execute(func() (interface{}, error) {
        return "should not execute", nil
    })

    if err != nil {
        t.Errorf("Expected no error, got %v", err)
    }
    if result != "fallback value" {
        t.Errorf("Expected 'fallback value', got %v", result)
    }
}
```

**测试要点：**
- 设置降级策略
- 触发熔断
- 验证降级响应

### 4.3 失败率测试

```go
func TestCircuitBreaker_FailureRate(t *testing.T) {
    cb := src.NewCircuitBreaker(src.Config{
        FailureThreshold:     100,
        SuccessThreshold:     2,
        Timeout:             1 * time.Second,
        FailureRateThreshold: 0.5,
        MinimumRequests:      5,
    })

    // 发送10个请求，6个失败
    for i := 0; i < 4; i++ {
        _, _ = cb.Execute(func() (interface{}, error) {
            return "success", nil
        })
    }
    for i := 0; i < 6; i++ {
        _, _ = cb.Execute(func() (interface{}, error) {
            return nil, errors.New("test error")
        })
    }

    // 失败率60% > 50%，应该触发熔断
    if cb.GetState() != src.StateOpen {
        t.Errorf("Expected state to be Open, got %v", cb.GetState())
    }
}
```

**测试要点：**
- 设置高失败阈值，避免连续失败触发
- 设置失败率阈值
- 发送足够请求数
- 验证失败率触发熔断

## 5. 并发测试

### 5.1 并发访问测试

```go
func TestCircuitBreaker_ConcurrentAccess(t *testing.T) {
    cb := src.NewCircuitBreaker(src.Config{
        FailureThreshold: 100,
        SuccessThreshold: 3,
        Timeout:         1 * time.Second,
    })

    var wg sync.WaitGroup
    for i := 0; i < 100; i++ {
        wg.Add(1)
        go func() {
            defer wg.Done()
            _, _ = cb.Execute(func() (interface{}, error) {
                return "success", nil
            })
        }()
    }

    wg.Wait()

    if cb.GetMetrics().GetTotalRequests() != 100 {
        t.Errorf("Expected 100 requests, got %d", cb.GetMetrics().GetTotalRequests())
    }
}
```

**测试要点：**
- 多goroutine并发访问
- 验证请求计数正确
- 使用 `go test -race` 检测竞态条件

### 5.2 竞态条件检测

```bash
go test -race ./tests/...
```

**检测内容：**
- 并发读写同一变量
- 锁的使用是否正确
- 原子操作是否正确

## 6. 性能测试

### 6.1 基准测试

```go
func BenchmarkCircuitBreaker_Execute(b *testing.B) {
    cb := src.NewCircuitBreaker(src.Config{
        FailureThreshold: 5,
        SuccessThreshold: 3,
        Timeout:         30 * time.Second,
    })

    b.ResetTimer()
    for i := 0; i < b.N; i++ {
        _, _ = cb.Execute(func() (interface{}, error) {
            return "success", nil
        })
    }
}
```

**运行基准测试：**

```bash
go test -bench=. ./tests/...
```

### 6.2 性能指标

- 请求吞吐量
- 平均延迟
- 内存使用
- CPU使用

## 7. 测试覆盖率

### 7.1 生成覆盖率报告

```bash
go test -coverprofile=coverage.out ./tests/...
go tool cover -html=coverage.out -o coverage.html
```

### 7.2 覆盖率目标

- 语句覆盖率：> 90%
- 分支覆盖率：> 80%
- 函数覆盖率：100%

## 8. 测试工具

### 8.1 测试框架

使用Go标准库 `testing` 包。

### 8.2 断言库

使用标准库的 `t.Errorf`、`t.Fatalf` 等方法。

### 8.3 Mock工具

使用接口和依赖注入实现mock。

## 9. 测试最佳实践

### 9.1 测试命名

使用 `TestXxx` 格式，清晰描述测试内容。

### 9.2 测试独立性

每个测试用例独立，不依赖其他测试。

### 9.3 测试可重复性

测试结果一致，不受环境影响。

### 9.4 测试快速性

单元测试应该快速完成。

## 10. 测试运行

### 10.1 运行所有测试

```bash
go test ./tests/...
```

### 10.2 运行特定测试

```bash
go test -run TestCircuitBreaker_ClosedState ./tests/...
```

### 10.3 运行基准测试

```bash
go test -bench=. ./tests/...
```

### 10.4 生成覆盖率报告

```bash
go test -coverprofile=coverage.out ./tests/...
go tool cover -html=coverage.out
```

### 10.5 检测竞态条件

```bash
go test -race ./tests/...
```

## 11. 测试维护

### 11.1 测试更新

当代码变更时，及时更新测试用例。

### 11.2 测试重构

定期重构测试代码，保持可读性。

### 11.3 测试文档

为复杂测试添加注释说明。
