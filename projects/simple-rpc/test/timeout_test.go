package test

import (
	"context"
	"testing"
	"time"

	"github.com/simple-rpc/internal/timeout"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

func TestWithTimeout(t *testing.T) {
	// 测试正常完成
	err := timeout.WithTimeout(context.Background(), 1*time.Second, func(ctx context.Context) error {
		return nil
	})
	assert.NoError(t, err)

	// 测试超时
	err = timeout.WithTimeout(context.Background(), 10*time.Millisecond, func(ctx context.Context) error {
		time.Sleep(100 * time.Millisecond)
		return nil
	})
	assert.Error(t, err)
	assert.Contains(t, err.Error(), "timed out")
}

func TestWithTimeoutError(t *testing.T) {
	// 测试返回错误
	err := timeout.WithTimeout(context.Background(), 1*time.Second, func(ctx context.Context) error {
		return assert.AnError
	})
	assert.Error(t, err)
	assert.Equal(t, assert.AnError, err)
}

func TestWithDeadline(t *testing.T) {
	// 测试正常完成
	deadline := time.Now().Add(1 * time.Second)
	err := timeout.WithDeadline(context.Background(), deadline, func(ctx context.Context) error {
		return nil
	})
	assert.NoError(t, err)

	// 测试超时
	deadline = time.Now().Add(10 * time.Millisecond)
	err = timeout.WithDeadline(context.Background(), deadline, func(ctx context.Context) error {
		time.Sleep(100 * time.Millisecond)
		return nil
	})
	assert.Error(t, err)
	assert.Contains(t, err.Error(), "deadline exceeded")
}

func TestRetryWithTimeout(t *testing.T) {
	// 测试成功重试
	attempts := 0
	err := timeout.RetryWithTimeout(context.Background(), 1*time.Second, 3, func(ctx context.Context) error {
		attempts++
		if attempts < 3 {
			return assert.AnError
		}
		return nil
	})
	assert.NoError(t, err)
	assert.Equal(t, 3, attempts)
}

func TestRetryWithTimeoutMaxRetries(t *testing.T) {
	// 测试达到最大重试次数
	attempts := 0
	err := timeout.RetryWithTimeout(context.Background(), 1*time.Second, 3, func(ctx context.Context) error {
		attempts++
		return assert.AnError
	})
	assert.Error(t, err)
	assert.Contains(t, err.Error(), "max retries exceeded")
	assert.Equal(t, 3, attempts)
}

func TestRetryWithTimeoutTimeout(t *testing.T) {
	// 测试超时
	attempts := 0
	err := timeout.RetryWithTimeout(context.Background(), 100*time.Millisecond, 10, func(ctx context.Context) error {
		attempts++
		time.Sleep(50 * time.Millisecond)
		return assert.AnError
	})
	assert.Error(t, err)
	assert.Contains(t, err.Error(), "timed out")
}

func TestCircuitBreaker(t *testing.T) {
	// 创建熔断器：3 次失败后打开，2 次成功后关闭，超时 1 秒
	cb := timeout.NewCircuitBreaker(3, 2, 1*time.Second)

	// 初始状态应该是关闭的
	assert.Equal(t, "closed", cb.GetState())

	// 执行成功操作
	err := cb.Execute(func() error {
		return nil
	})
	assert.NoError(t, err)
	assert.Equal(t, "closed", cb.GetState())

	// 执行失败操作
	for i := 0; i < 3; i++ {
		err = cb.Execute(func() error {
			return assert.AnError
		})
		assert.Error(t, err)
	}

	// 熔断器应该打开
	assert.Equal(t, "open", cb.GetState())

	// 打开状态下执行应该失败
	err = cb.Execute(func() error {
		return nil
	})
	assert.Error(t, err)
	assert.Contains(t, err.Error(), "circuit breaker is open")
}

func TestCircuitBreakerHalfOpen(t *testing.T) {
	// 创建熔断器：1 次失败后打开，1 次成功后关闭，超时 100ms
	cb := timeout.NewCircuitBreaker(1, 1, 100*time.Millisecond)

	// 触发熔断
	err := cb.Execute(func() error {
		return assert.AnError
	})
	assert.Error(t, err)
	assert.Equal(t, "open", cb.GetState())

	// 等待超时
	time.Sleep(150 * time.Millisecond)

	// 执行成功操作，应该进入半开状态
	err = cb.Execute(func() error {
		return nil
	})
	assert.NoError(t, err)

	// 熔断器应该关闭
	assert.Equal(t, "closed", cb.GetState())
}

func TestCircuitBreakerHalfOpenFailure(t *testing.T) {
	// 创建熔断器：1 次失败后打开，1 次成功后关闭，超时 100ms
	cb := timeout.NewCircuitBreaker(1, 1, 100*time.Millisecond)

	// 触发熔断
	err := cb.Execute(func() error {
		return assert.AnError
	})
	assert.Error(t, err)
	assert.Equal(t, "open", cb.GetState())

	// 等待超时
	time.Sleep(150 * time.Millisecond)

	// 执行失败操作，应该重新打开
	err = cb.Execute(func() error {
		return assert.AnError
	})
	assert.Error(t, err)
	assert.Equal(t, "open", cb.GetState())
}

func TestDefaultConfig(t *testing.T) {
	config := timeout.DefaultConfig()

	require.NotNil(t, config)
	assert.Equal(t, 5*time.Second, config.ConnectTimeout)
	assert.Equal(t, 10*time.Second, config.RequestTimeout)
	assert.Equal(t, 30*time.Second, config.KeepAliveTimeout)
}
