# 设计文档: 熔断器系统架构

## 1. 设计目标

### 1.1 功能目标

- 实现熔断器状态机（关闭、打开、半开）
- 支持失败率统计和阈值触发
- 提供多种降级策略
- 支持并发安全访问

### 1.2 非功能目标

- 高性能：最小化锁竞争
- 可扩展：支持自定义降级策略
- 易用性：简洁的API设计
- 可观测性：提供详细的指标统计

## 2. 系统架构

### 2.1 模块划分

```
circuit-breaker/
├── src/
│   ├── circuit_breaker.go   # 核心熔断器
│   ├── states.go            # 状态定义
│   ├── metrics.go           # 指标统计
│   ├── fallback.go          # 降级策略
│   ├── ratelimiter.go       # 限流器
│   └── retry.go             # 重试机制
├── tests/                   # 测试代码
├── examples/                # 使用示例
│   ├── main.go              # 基础示例
│   └── api_gateway.go       # API网关示例
└── docs/                    # 学习文档
```

### 2.2 核心组件

1. **CircuitBreaker**：熔断器核心，管理状态和执行请求
2. **State**：状态枚举，定义三种状态
3. **Metrics**：指标统计，记录请求成功率和失败率
4. **FallbackStrategy**：降级策略接口，支持多种降级实现
5. **RateLimiter**：限流器接口，支持固定窗口、滑动窗口、令牌桶
6. **Retryer**：重试器，支持指数退避和抖动

## 3. 类设计

### 3.1 CircuitBreaker

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

**职责：**
- 管理熔断器状态
- 执行请求并记录结果
- 处理状态转换
- 执行降级策略

### 3.2 State

```go
type State int

const (
    StateClosed State = iota
    StateOpen
    StateHalfOpen
)
```

**职责：**
- 定义三种状态
- 提供状态查询方法
- 判断是否允许执行请求

### 3.3 Metrics

```go
type Metrics struct {
    mu                 sync.RWMutex
    totalRequests      int64
    successCount       int64
    failureCount       int64
    lastFailureTime    time.Time
    consecutiveSuccess int64
    consecutiveFailure int64
}
```

**职责：**
- 记录请求统计
- 计算失败率
- 跟踪连续成功/失败次数

### 3.4 FallbackStrategy

```go
type FallbackStrategy interface {
    Execute() (interface{}, error)
}
```

**实现：**
- DefaultFallback：默认降级
- CacheFallback：缓存降级
- StaticFallback：静态降级
- CompositeFallback：组合降级

### 3.5 RateLimiter

```go
type RateLimiter interface {
    Allow() bool
    AllowN(n int) bool
    GetAvailable() int64
}
```

**实现：**
- FixedWindowLimiter：固定窗口限流
- SlidingWindowLimiter：滑动窗口限流
- TokenBucketLimiter：令牌桶限流

### 3.6 Retryer

```go
type Retryer struct {
    config RetryConfig
}

type RetryConfig struct {
    MaxRetries      int
    InitialInterval time.Duration
    MaxInterval     time.Duration
    Multiplier      float64
    Jitter          bool
    RetryableFunc   func(error) bool
}
```

**特性：**
- 指数退避：间隔按倍数递增
- 抖动：添加随机偏移避免惊群
- 可重试判断：自定义错误是否可重试
- 组合熔断器：RetryableCircuitBreaker

## 4. 配置设计

### 4.1 Config

```go
type Config struct {
    FailureThreshold     int64         // 失败阈值
    SuccessThreshold     int64         // 成功阈值
    Timeout              time.Duration // 超时时间
    FailureRateThreshold float64       // 失败率阈值
    MinimumRequests      int64         // 最小请求数
}
```

### 4.2 默认配置

```go
func DefaultConfig() Config {
    return Config{
        FailureThreshold:     5,
        SuccessThreshold:     3,
        Timeout:              30 * time.Second,
        FailureRateThreshold: 0.5,
        MinimumRequests:      10,
    }
}
```

## 5. 状态转换设计

### 5.1 转换条件

**Closed → Open：**
- 连续失败次数达到 FailureThreshold
- 或失败率达到 FailureRateThreshold（请求数 >= MinimumRequests）

**Open → Half-Open：**
- 超过 Timeout 时间

**Half-Open → Closed：**
- 连续成功次数达到 SuccessThreshold

**Half-Open → Open：**
- 任何失败

### 5.2 状态转换流程

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

## 6. 并发设计

### 6.1 锁策略

使用 `sync.RWMutex` 保护状态：

- 读操作（GetState, GetMetrics）使用读锁
- 写操作（Execute, recordResult）使用写锁
- 状态转换时需要写锁

### 6.2 锁粒度

```go
func (cb *CircuitBreaker) Execute(request func() (interface{}, error)) (interface{}, error) {
    cb.mu.Lock()

    // 检查是否允许执行
    if !cb.canExecute() {
        cb.mu.Unlock()
        return cb.executeFallback()
    }

    cb.mu.Unlock()

    // 执行请求（不持有锁）
    result, err := request()

    // 记录结果
    cb.recordResult(err)

    return result, err
}
```

**设计要点：**
- 检查状态时持有锁
- 执行请求时不持有锁，避免长时间阻塞
- 记录结果时再次获取锁

## 7. API设计

### 7.1 创建熔断器

```go
func NewCircuitBreaker(config Config) *CircuitBreaker
```

### 7.2 执行请求

```go
func (cb *CircuitBreaker) Execute(request func() (interface{}, error)) (interface{}, error)
```

### 7.3 获取状态

```go
func (cb *CircuitBreaker) GetState() State
```

### 7.4 设置降级策略

```go
func (cb *CircuitBreaker) SetFallback(fallback FallbackStrategy)
```

### 7.5 重置熔断器

```go
func (cb *CircuitBreaker) Reset()
```

## 8. 错误处理

### 8.1 错误类型

- 熔断器打开错误：`circuit breaker is open`
- 降级失败错误：所有降级策略都失败

### 8.2 错误传播

- 请求失败时，优先返回降级结果
- 如果降级也失败，返回原始错误
- 熔断器打开时，返回熔断器错误或降级结果

## 9. 性能考虑

### 9.1 锁优化

- 使用读写锁减少锁竞争
- 最小化锁持有时间
- 避免在锁内执行耗时操作

### 9.2 内存优化

- 指标统计使用原子操作或简单计数器
- 避免不必要的内存分配

### 9.3 CPU优化

- 状态检查快速返回
- 避免复杂的计算

## 10. 可扩展性

### 10.1 自定义降级策略

实现 `FallbackStrategy` 接口即可添加新的降级策略。

### 10.2 自定义指标

可以扩展 `Metrics` 以支持更多指标。

### 10.3 事件监听

可以添加事件监听器，在状态变化时触发回调。

## 11. 测试策略

### 11.1 单元测试

- 状态转换测试
- 指标统计测试
- 降级策略测试

### 11.2 并发测试

- 多goroutine并发访问
- 竞态条件检测

### 11.3 集成测试

- 端到端场景测试
- 性能基准测试

## 12. 部署考虑

### 12.1 配置管理

- 支持运行时配置更新
- 配置验证和默认值

### 12.2 监控告警

- 暴露指标给监控系统
- 状态变化告警

### 12.3 日志记录

- 状态变化日志
- 错误日志
- 调试日志
