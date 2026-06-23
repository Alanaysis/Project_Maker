# 实现文档: 熔断器核心代码

## 1. 实现概述

本文档详细说明熔断器的核心实现，包括状态机、指标统计和降级策略。

## 2. 状态实现 (states.go)

### 2.1 状态枚举

```go
type State int

const (
    StateClosed State = iota
    StateOpen
    StateHalfOpen
)
```

使用 `iota` 实现枚举，确保状态值唯一且有序。

### 2.2 状态方法

**String()**：返回状态的字符串表示，便于日志输出。

**IsValid()**：检查状态是否有效，防止无效状态。

**CanExecute()**：判断当前状态是否允许执行请求。

## 3. 指标实现 (metrics.go)

### 3.1 指标结构

```go
type Metrics struct {
    mu              sync.RWMutex
    totalRequests   int64
    successCount    int64
    failureCount    int64
    lastFailureTime time.Time
    consecutiveSuccess int64
    consecutiveFailure int64
}
```

### 3.2 记录成功

```go
func (m *Metrics) RecordSuccess() {
    m.mu.Lock()
    defer m.mu.Unlock()

    m.totalRequests++
    m.successCount++
    m.consecutiveSuccess++
    m.consecutiveFailure = 0
}
```

**关键点：**
- 增加总请求数和成功数
- 增加连续成功计数
- 重置连续失败计数

### 3.3 记录失败

```go
func (m *Metrics) RecordFailure() {
    m.mu.Lock()
    defer m.mu.Unlock()

    m.totalRequests++
    m.failureCount++
    m.consecutiveFailure++
    m.consecutiveSuccess = 0
    m.lastFailureTime = time.Now()
}
```

**关键点：**
- 增加总请求数和失败数
- 增加连续失败计数
- 重置连续成功计数
- 记录最后失败时间

### 3.4 计算失败率

```go
func (m *Metrics) GetFailureRate() float64 {
    m.mu.RLock()
    defer m.mu.RUnlock()

    if m.totalRequests == 0 {
        return 0
    }
    return float64(m.failureCount) / float64(m.totalRequests)
}
```

**关键点：**
- 避免除零错误
- 返回0到1之间的浮点数

## 4. 降级策略实现 (fallback.go)

### 4.1 默认降级

```go
type DefaultFallback struct {
    message string
}

func (f *DefaultFallback) Execute() (interface{}, error) {
    return nil, errors.New(f.message)
}
```

**用途：** 返回预设的错误信息。

### 4.2 缓存降级

```go
type CacheFallback struct {
    cache     map[string]interface{}
    cacheTTL  time.Duration
    cacheTime time.Time
}

func (f *CacheFallback) Execute() (interface{}, error) {
    if len(f.cache) == 0 {
        return nil, errors.New("no cached data available")
    }

    if time.Since(f.cacheTime) > f.cacheTTL {
        return nil, errors.New("cached data expired")
    }

    for _, v := range f.cache {
        return v, nil
    }

    return nil, errors.New("no cached data available")
}
```

**关键点：**
- 检查缓存是否存在
- 检查缓存是否过期
- 返回缓存数据

### 4.3 静态降级

```go
type StaticFallback struct {
    value interface{}
    err   error
}

func (f *StaticFallback) Execute() (interface{}, error) {
    return f.value, f.err
}
```

**用途：** 返回固定的静态数据。

### 4.4 组合降级

```go
type CompositeFallback struct {
    strategies []FallbackStrategy
}

func (f *CompositeFallback) Execute() (interface{}, error) {
    for _, strategy := range f.strategies {
        result, err := strategy.Execute()
        if err == nil {
            return result, nil
        }
    }
    return nil, errors.New("all fallback strategies failed")
}
```

**关键点：**
- 按顺序执行降级策略
- 返回第一个成功的结果
- 所有策略都失败才返回错误

## 5. 熔断器实现 (circuit_breaker.go)

### 5.1 配置结构

```go
type Config struct {
    FailureThreshold     int64
    SuccessThreshold     int64
    Timeout              time.Duration
    FailureRateThreshold float64
    MinimumRequests      int64
}
```

### 5.2 熔断器结构

```go
type CircuitBreaker struct {
    mu              sync.RWMutex
    config          Config
    state           State
    metrics         *Metrics
    fallback        FallbackStrategy
    lastStateChange time.Time
}
```

### 5.3 创建熔断器

```go
func NewCircuitBreaker(config Config) *CircuitBreaker {
    return &CircuitBreaker{
        config:          config,
        state:          StateClosed,
        metrics:        NewMetrics(),
        lastStateChange: time.Now(),
    }
}
```

**初始化：**
- 设置配置
- 初始状态为关闭
- 创建指标统计实例
- 记录初始状态变化时间

### 5.4 执行请求

```go
func (cb *CircuitBreaker) Execute(request func() (interface{}, error)) (interface{}, error) {
    cb.mu.Lock()

    if !cb.canExecute() {
        cb.mu.Unlock()
        return cb.executeFallback()
    }

    cb.mu.Unlock()

    result, err := request()

    cb.recordResult(err)

    if err != nil {
        if cb.fallback != nil {
            return cb.fallback.Execute()
        }
        return nil, err
    }

    return result, nil
}
```

**执行流程：**
1. 获取锁
2. 检查是否允许执行
3. 释放锁
4. 执行请求
5. 记录结果
6. 处理错误和降级

### 5.5 检查是否允许执行

```go
func (cb *CircuitBreaker) canExecute() bool {
    switch cb.state {
    case StateClosed:
        return true
    case StateOpen:
        if time.Since(cb.lastStateChange) >= cb.config.Timeout {
            cb.setState(StateHalfOpen)
            return true
        }
        return false
    case StateHalfOpen:
        return true
    default:
        return false
    }
}
```

**状态处理：**
- 关闭状态：允许执行
- 打开状态：检查是否超时，超时则切换到半开状态
- 半开状态：允许执行

### 5.6 记录结果

```go
func (cb *CircuitBreaker) recordResult(err error) {
    cb.mu.Lock()
    defer cb.mu.Unlock()

    if err != nil {
        cb.metrics.RecordFailure()
        cb.onFailure()
    } else {
        cb.metrics.RecordSuccess()
        cb.onSuccess()
    }
}
```

### 5.7 成功处理

```go
func (cb *CircuitBreaker) onSuccess() {
    switch cb.state {
    case StateClosed:
        // 重置连续失败计数
    case StateHalfOpen:
        if cb.metrics.GetConsecutiveSuccess() >= cb.config.SuccessThreshold {
            cb.setState(StateClosed)
        }
    }
}
```

### 5.8 失败处理

```go
func (cb *CircuitBreaker) onFailure() {
    switch cb.state {
    case StateClosed:
        if cb.shouldTrip() {
            cb.setState(StateOpen)
        }
    case StateHalfOpen:
        cb.setState(StateOpen)
    }
}
```

### 5.9 判断是否应该触发熔断

```go
func (cb *CircuitBreaker) shouldTrip() bool {
    if cb.metrics.GetConsecutiveFailure() >= cb.config.FailureThreshold {
        return true
    }

    totalRequests := cb.metrics.GetTotalRequests()
    if totalRequests >= cb.config.MinimumRequests {
        failureRate := cb.metrics.GetFailureRate()
        if failureRate >= cb.config.FailureRateThreshold {
            return true
        }
    }

    return false
}
```

**触发条件：**
- 连续失败次数达到阈值
- 或失败率达到阈值（请求数足够）

### 5.10 设置状态

```go
func (cb *CircuitBreaker) setState(newState State) {
    if cb.state == newState {
        return
    }

    cb.state = newState
    cb.lastStateChange = time.Now()
    cb.metrics.Reset()
}
```

**关键点：**
- 避免重复设置相同状态
- 更新状态变化时间
- 重置指标统计

### 5.11 执行降级

```go
func (cb *CircuitBreaker) executeFallback() (interface{}, error) {
    if cb.fallback != nil {
        return cb.fallback.Execute()
    }
    return nil, errors.New("circuit breaker is open")
}
```

### 5.12 重置熔断器

```go
func (cb *CircuitBreaker) Reset() {
    cb.mu.Lock()
    defer cb.mu.Unlock()

    cb.state = StateClosed
    cb.metrics.Reset()
    cb.lastStateChange = time.Now()
}
```

## 6. 并发安全

### 6.1 锁的使用

- 使用 `sync.RWMutex` 保护状态
- 读操作使用 `RLock()`
- 写操作使用 `Lock()`

### 6.2 锁的粒度

- 检查状态时持有锁
- 执行请求时不持有锁
- 记录结果时再次获取锁

### 6.3 避免死锁

- 不在锁内调用可能获取锁的方法
- 使用 `defer` 确保锁释放

## 7. 错误处理

### 7.1 错误类型

- 熔断器打开错误
- 降级失败错误
- 请求失败错误

### 7.2 错误传播

- 优先返回降级结果
- 降级失败返回原始错误
- 熔断器打开返回熔断器错误

## 8. 性能优化

### 8.1 锁优化

- 使用读写锁减少竞争
- 最小化锁持有时间
- 避免在锁内执行耗时操作

### 8.2 内存优化

- 复用指标统计实例
- 避免不必要的内存分配

### 8.3 CPU优化

- 状态检查快速返回
- 避免复杂计算

## 9. 测试要点

### 9.1 状态转换测试

- 关闭状态正常处理
- 失败阈值触发熔断
- 超时后进入半开状态
- 半开状态成功恢复
- 半开状态失败回到打开

### 9.2 降级策略测试

- 默认降级返回错误
- 缓存降级返回缓存数据
- 静态降级返回固定值
- 组合降级按优先级执行

### 9.3 并发测试

- 多goroutine并发访问
- 竞态条件检测
- 性能基准测试

## 10. 使用示例

### 10.1 基本使用

```go
breaker := NewCircuitBreaker(Config{
    FailureThreshold: 5,
    SuccessThreshold: 3,
    Timeout:         30 * time.Second,
})

result, err := breaker.Execute(func() (interface{}, error) {
    return "success", nil
})
```

### 10.2 带降级策略

```go
breaker := NewCircuitBreaker(Config{
    FailureThreshold: 3,
    SuccessThreshold: 2,
    Timeout:         10 * time.Second,
})

fallback := NewStaticFallback("default value", nil)
breaker.SetFallback(fallback)

result, err := breaker.Execute(func() (interface{}, error) {
    return nil, errors.New("service unavailable")
})
// result = "default value", err = nil
```

### 10.3 缓存降级

```go
breaker := NewCircuitBreaker(Config{
    FailureThreshold: 5,
    SuccessThreshold: 3,
    Timeout:         30 * time.Second,
})

fallback := NewCacheFallback(5 * time.Minute)
fallback.SetCache("user:123", userData)
breaker.SetFallback(fallback)
```
