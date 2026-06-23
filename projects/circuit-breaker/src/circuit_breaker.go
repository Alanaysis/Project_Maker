package src

import (
    "errors"
    "sync"
    "time"
)

// Config 熔断器配置
type Config struct {
    // FailureThreshold 失败阈值，触发熔断的连续失败次数
    FailureThreshold int64
    // SuccessThreshold 成功阈值，从半开状态恢复到关闭状态的连续成功次数
    SuccessThreshold int64
    // Timeout 超时时间，从打开状态到半开状态的等待时间
    Timeout time.Duration
    // FailureRateThreshold 失败率阈值，触发熔断的失败率
    FailureRateThreshold float64
    // MinimumRequests 最小请求数，计算失败率所需的最小请求数
    MinimumRequests int64
}

// DefaultConfig 返回默认配置
func DefaultConfig() Config {
    return Config{
        FailureThreshold:     5,
        SuccessThreshold:     3,
        Timeout:             30 * time.Second,
        FailureRateThreshold: 0.5,
        MinimumRequests:      10,
    }
}

// CircuitBreaker 熔断器
type CircuitBreaker struct {
    mu          sync.RWMutex
    config      Config
    state       State
    metrics     *Metrics
    fallback    FallbackStrategy
    lastStateChange time.Time
}

// NewCircuitBreaker 创建新的熔断器
func NewCircuitBreaker(config Config) *CircuitBreaker {
    return &CircuitBreaker{
        config:          config,
        state:          StateClosed,
        metrics:        NewMetrics(),
        lastStateChange: time.Now(),
    }
}

// SetFallback 设置降级策略
func (cb *CircuitBreaker) SetFallback(fallback FallbackStrategy) {
    cb.mu.Lock()
    defer cb.mu.Unlock()
    cb.fallback = fallback
}

// GetState 获取当前状态
func (cb *CircuitBreaker) GetState() State {
    cb.mu.RLock()
    defer cb.mu.RUnlock()
    return cb.state
}

// GetMetrics 获取指标
func (cb *CircuitBreaker) GetMetrics() *Metrics {
    return cb.metrics
}

// Execute 执行请求
func (cb *CircuitBreaker) Execute(request func() (interface{}, error)) (interface{}, error) {
    cb.mu.Lock()

    // 检查是否允许执行
    if !cb.canExecute() {
        cb.mu.Unlock()
        return cb.executeFallback()
    }

    cb.mu.Unlock()

    // 执行请求
    result, err := request()

    // 记录结果
    cb.recordResult(err)

    if err != nil {
        // 如果有降级策略，执行降级
        if cb.fallback != nil {
            return cb.fallback.Execute()
        }
        return nil, err
    }

    return result, nil
}

// canExecute 检查是否允许执行请求
func (cb *CircuitBreaker) canExecute() bool {
    switch cb.state {
    case StateClosed:
        return true
    case StateOpen:
        // 检查是否超时
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

// recordResult 记录请求结果
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

// onSuccess 处理成功请求
func (cb *CircuitBreaker) onSuccess() {
    switch cb.state {
    case StateClosed:
        // 重置连续失败计数
        // 这里不需要额外操作，Metrics已经处理了
    case StateHalfOpen:
        // 检查是否达到成功阈值
        if cb.metrics.GetConsecutiveSuccess() >= cb.config.SuccessThreshold {
            cb.setState(StateClosed)
        }
    }
}

// onFailure 处理失败请求
func (cb *CircuitBreaker) onFailure() {
    switch cb.state {
    case StateClosed:
        // 检查是否达到失败阈值
        if cb.shouldTrip() {
            cb.setState(StateOpen)
        }
    case StateHalfOpen:
        // 半开状态下失败，直接打开
        cb.setState(StateOpen)
    }
}

// shouldTrip 检查是否应该触发熔断
func (cb *CircuitBreaker) shouldTrip() bool {
    // 检查连续失败次数
    if cb.metrics.GetConsecutiveFailure() >= cb.config.FailureThreshold {
        return true
    }

    // 检查失败率
    totalRequests := cb.metrics.GetTotalRequests()
    if totalRequests >= cb.config.MinimumRequests {
        failureRate := cb.metrics.GetFailureRate()
        if failureRate >= cb.config.FailureRateThreshold {
            return true
        }
    }

    return false
}

// setState 设置新状态
func (cb *CircuitBreaker) setState(newState State) {
    if cb.state == newState {
        return
    }

    cb.state = newState
    cb.lastStateChange = time.Now()

    // 状态改变时重置指标
    cb.metrics.Reset()
}

// executeFallback 执行降级策略
func (cb *CircuitBreaker) executeFallback() (interface{}, error) {
    if cb.fallback != nil {
        return cb.fallback.Execute()
    }
    return nil, errors.New("circuit breaker is open")
}

// Reset 重置熔断器
func (cb *CircuitBreaker) Reset() {
    cb.mu.Lock()
    defer cb.mu.Unlock()

    cb.state = StateClosed
    cb.metrics.Reset()
    cb.lastStateChange = time.Now()
}
