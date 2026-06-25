package src

import (
	"math"
	"math/rand"
	"time"
)

// RetryConfig 重试配置
type RetryConfig struct {
	// MaxRetries 最大重试次数
	MaxRetries int
	// InitialInterval 初始重试间隔
	InitialInterval time.Duration
	// MaxInterval 最大重试间隔
	MaxInterval time.Duration
	// Multiplier 退避乘数
	Multiplier float64
	// Jitter 是否添加随机抖动
	Jitter bool
	// RetryableFunc 判断错误是否可重试
	RetryableFunc func(error) bool
}

// DefaultRetryConfig 返回默认重试配置
func DefaultRetryConfig() RetryConfig {
	return RetryConfig{
		MaxRetries:      3,
		InitialInterval: 100 * time.Millisecond,
		MaxInterval:     10 * time.Second,
		Multiplier:      2.0,
		Jitter:          true,
		RetryableFunc:   nil, // nil表示所有错误都重试
	}
}

// RetryResult 重试结果
type RetryResult struct {
	// Value 返回值
	Value interface{}
	// Err 最后一次错误
	Err error
	// Attempts 实际尝试次数
	Attempts int
	// TotalDuration 总耗时
	TotalDuration time.Duration
}

// Retryer 重试器
type Retryer struct {
	config RetryConfig
}

// NewRetryer 创建重试器
func NewRetryer(config RetryConfig) *Retryer {
	return &Retryer{
		config: config,
	}
}

// Execute 执行带重试的操作
func (r *Retryer) Execute(fn func() (interface{}, error)) RetryResult {
	startTime := time.Now()
	var lastErr error

	for attempt := 0; attempt <= r.config.MaxRetries; attempt++ {
		// 第一次不等待
		if attempt > 0 {
			interval := r.calculateInterval(attempt)
			time.Sleep(interval)
		}

		result, err := fn()
		if err == nil {
			return RetryResult{
				Value:         result,
				Attempts:      attempt + 1,
				TotalDuration: time.Since(startTime),
			}
		}

		lastErr = err

		// 检查是否可重试
		if r.config.RetryableFunc != nil && !r.config.RetryableFunc(err) {
			return RetryResult{
				Err:           err,
				Attempts:      attempt + 1,
				TotalDuration: time.Since(startTime),
			}
		}
	}

	return RetryResult{
		Err:           lastErr,
		Attempts:      r.config.MaxRetries + 1,
		TotalDuration: time.Since(startTime),
	}
}

// calculateInterval 计算重试间隔（指数退避 + 可选抖动）
func (r *Retryer) calculateInterval(attempt int) time.Duration {
	// 指数退避: initialInterval * multiplier^(attempt-1)
	interval := float64(r.config.InitialInterval) * math.Pow(r.config.Multiplier, float64(attempt-1))

	// 添加随机抖动
	if r.config.Jitter {
		// 在 [0, interval) 范围内添加随机偏移
		jitter := rand.Float64() * interval
		interval = interval/2 + jitter/2
	}

	// 限制最大间隔
	duration := time.Duration(interval)
	if duration > r.config.MaxInterval {
		duration = r.config.MaxInterval
	}

	return duration
}

// ============================================================
// RetryWithCircuitBreaker 组合重试与熔断器
// ============================================================

// RetryableCircuitBreaker 带重试的熔断器
type RetryableCircuitBreaker struct {
	breaker *CircuitBreaker
	retryer *Retryer
}

// NewRetryableCircuitBreaker 创建带重试的熔断器
func NewRetryableCircuitBreaker(breaker *CircuitBreaker, retryConfig RetryConfig) *RetryableCircuitBreaker {
	return &RetryableCircuitBreaker{
		breaker: breaker,
		retryer: NewRetryer(retryConfig),
	}
}

// Execute 执行带重试的熔断器操作
// 先通过熔断器检查，再在熔断器允许的情况下进行重试
func (rcb *RetryableCircuitBreaker) Execute(fn func() (interface{}, error)) (interface{}, error) {
	// 先检查熔断器状态
	state := rcb.breaker.GetState()
	if state == StateOpen {
		if rcb.breaker.fallback != nil {
			return rcb.breaker.fallback.Execute()
		}
		return nil, ErrCircuitOpen
	}

	// 使用重试器执行
	result := rcb.retryer.Execute(func() (interface{}, error) {
		return rcb.breaker.Execute(fn)
	})

	return result.Value, result.Err
}

// ErrCircuitOpen 熔断器打开错误
var ErrCircuitOpen = &CircuitOpenError{}

// CircuitOpenError 熔断器打开错误类型
type CircuitOpenError struct{}

func (e *CircuitOpenError) Error() string {
	return "circuit breaker is open"
}
