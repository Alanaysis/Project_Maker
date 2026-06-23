package timeout

import (
	"context"
	"fmt"
	"sync"
	"time"
)

// TimeoutConfig 超时配置
type TimeoutConfig struct {
	// ConnectTimeout 连接超时
	ConnectTimeout time.Duration
	// RequestTimeout 请求超时
	RequestTimeout time.Duration
	// KeepAliveTimeout 保活超时
	KeepAliveTimeout time.Duration
}

// DefaultConfig 默认超时配置
func DefaultConfig() *TimeoutConfig {
	return &TimeoutConfig{
		ConnectTimeout:   5 * time.Second,
		RequestTimeout:   10 * time.Second,
		KeepAliveTimeout: 30 * time.Second,
	}
}

// WithTimeout 执行带超时的操作
func WithTimeout(ctx context.Context, timeout time.Duration, fn func(ctx context.Context) error) error {
	ctx, cancel := context.WithTimeout(ctx, timeout)
	defer cancel()

	errCh := make(chan error, 1)
	go func() {
		errCh <- fn(ctx)
	}()

	select {
	case err := <-errCh:
		return err
	case <-ctx.Done():
		return fmt.Errorf("operation timed out: %w", ctx.Err())
	}
}

// WithDeadline 执行带截止时间的操作
func WithDeadline(ctx context.Context, deadline time.Time, fn func(ctx context.Context) error) error {
	ctx, cancel := context.WithDeadline(ctx, deadline)
	defer cancel()

	errCh := make(chan error, 1)
	go func() {
		errCh <- fn(ctx)
	}()

	select {
	case err := <-errCh:
		return err
	case <-ctx.Done():
		return fmt.Errorf("operation deadline exceeded: %w", ctx.Err())
	}
}

// RetryWithTimeout 带超时的重试
func RetryWithTimeout(ctx context.Context, timeout time.Duration, maxRetries int, fn func(ctx context.Context) error) error {
	ctx, cancel := context.WithTimeout(ctx, timeout)
	defer cancel()

	var lastErr error
	for i := 0; i < maxRetries; i++ {
		select {
		case <-ctx.Done():
			return fmt.Errorf("retry timed out after %d attempts: %w", i, ctx.Err())
		default:
		}

		if err := fn(ctx); err != nil {
			lastErr = err
			time.Sleep(time.Duration(i+1) * 100 * time.Millisecond)
			continue
		}
		return nil
	}

	return fmt.Errorf("max retries exceeded: %w", lastErr)
}

// CircuitBreaker 熔断器
type CircuitBreaker struct {
	mu               sync.Mutex
	failureCount     int
	successCount     int
	state            string // "closed", "open", "half-open"
	failureThreshold int
	successThreshold int
	timeout          time.Duration
	lastFailureTime  time.Time
}

// NewCircuitBreaker 创建熔断器
func NewCircuitBreaker(failureThreshold, successThreshold int, timeout time.Duration) *CircuitBreaker {
	return &CircuitBreaker{
		state:            "closed",
		failureThreshold: failureThreshold,
		successThreshold: successThreshold,
		timeout:          timeout,
	}
}

// Execute 执行带熔断的操作
func (cb *CircuitBreaker) Execute(fn func() error) error {
	cb.mu.Lock()
	state := cb.state
	cb.mu.Unlock()

	switch state {
	case "open":
		// 检查是否可以进入半开状态
		cb.mu.Lock()
		if time.Since(cb.lastFailureTime) > cb.timeout {
			cb.state = "half-open"
			cb.mu.Unlock()
			return cb.executeHalfOpen(fn)
		}
		cb.mu.Unlock()
		return fmt.Errorf("circuit breaker is open")
	case "half-open":
		return cb.executeHalfOpen(fn)
	default: // closed
		return cb.executeClosed(fn)
	}
}

func (cb *CircuitBreaker) executeClosed(fn func() error) error {
	err := fn()

	cb.mu.Lock()
	defer cb.mu.Unlock()

	if err != nil {
		cb.failureCount++
		if cb.failureCount >= cb.failureThreshold {
			cb.state = "open"
			cb.lastFailureTime = time.Now()
		}
		return err
	}

	cb.failureCount = 0
	return nil
}

func (cb *CircuitBreaker) executeHalfOpen(fn func() error) error {
	err := fn()

	cb.mu.Lock()
	defer cb.mu.Unlock()

	if err != nil {
		cb.state = "open"
		cb.lastFailureTime = time.Now()
		return err
	}

	cb.successCount++
	if cb.successCount >= cb.successThreshold {
		cb.state = "closed"
		cb.successCount = 0
		cb.failureCount = 0
	}
	return nil
}

// GetState 获取熔断器状态
func (cb *CircuitBreaker) GetState() string {
	cb.mu.Lock()
	defer cb.mu.Unlock()
	return cb.state
}
