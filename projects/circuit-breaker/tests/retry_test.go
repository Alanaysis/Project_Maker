package tests

import (
	"errors"
	"testing"
	"time"

	"circuit-breaker/src"
)

// ============================================================
// 重试器测试
// ============================================================

func TestRetryer_SuccessOnFirstAttempt(t *testing.T) {
	retryer := src.NewRetryer(src.RetryConfig{
		MaxRetries:      3,
		InitialInterval: 10 * time.Millisecond,
		MaxInterval:     1 * time.Second,
		Multiplier:      2.0,
		Jitter:          false,
	})

	attempts := 0
	result := retryer.Execute(func() (interface{}, error) {
		attempts++
		return "success", nil
	})

	if result.Err != nil {
		t.Errorf("Expected no error, got %v", result.Err)
	}
	if result.Value != "success" {
		t.Errorf("Expected 'success', got %v", result.Value)
	}
	if result.Attempts != 1 {
		t.Errorf("Expected 1 attempt, got %d", result.Attempts)
	}
}

func TestRetryer_SuccessAfterRetries(t *testing.T) {
	retryer := src.NewRetryer(src.RetryConfig{
		MaxRetries:      3,
		InitialInterval: 10 * time.Millisecond,
		MaxInterval:     1 * time.Second,
		Multiplier:      2.0,
		Jitter:          false,
	})

	attempts := 0
	result := retryer.Execute(func() (interface{}, error) {
		attempts++
		if attempts < 3 {
			return nil, errors.New("temporary failure")
		}
		return "recovered", nil
	})

	if result.Err != nil {
		t.Errorf("Expected no error, got %v", result.Err)
	}
	if result.Value != "recovered" {
		t.Errorf("Expected 'recovered', got %v", result.Value)
	}
	if result.Attempts != 3 {
		t.Errorf("Expected 3 attempts, got %d", result.Attempts)
	}
}

func TestRetryer_MaxRetriesExceeded(t *testing.T) {
	retryer := src.NewRetryer(src.RetryConfig{
		MaxRetries:      2,
		InitialInterval: 10 * time.Millisecond,
		MaxInterval:     1 * time.Second,
		Multiplier:      2.0,
		Jitter:          false,
	})

	attempts := 0
	result := retryer.Execute(func() (interface{}, error) {
		attempts++
		return nil, errors.New("persistent failure")
	})

	if result.Err == nil {
		t.Error("Expected error after max retries")
	}
	if result.Err.Error() != "persistent failure" {
		t.Errorf("Expected 'persistent failure', got %v", result.Err)
	}
	if result.Attempts != 3 { // 1 initial + 2 retries
		t.Errorf("Expected 3 attempts, got %d", result.Attempts)
	}
}

func TestRetryer_RetryableFunc(t *testing.T) {
	retryer := src.NewRetryer(src.RetryConfig{
		MaxRetries:      5,
		InitialInterval: 10 * time.Millisecond,
		MaxInterval:     1 * time.Second,
		Multiplier:      2.0,
		Jitter:          false,
		RetryableFunc: func(err error) bool {
			// 只重试临时错误
			return err.Error() == "temporary"
		},
	})

	attempts := 0
	result := retryer.Execute(func() (interface{}, error) {
		attempts++
		if attempts == 1 {
			return nil, errors.New("temporary")
		}
		return nil, errors.New("permanent")
	})

	// 第一次遇到temporary会重试，第二次遇到permanent不会重试
	if result.Err == nil {
		t.Error("Expected error")
	}
	if result.Err.Error() != "permanent" {
		t.Errorf("Expected 'permanent', got %v", result.Err)
	}
	if result.Attempts != 2 {
		t.Errorf("Expected 2 attempts, got %d", result.Attempts)
	}
}

func TestRetryer_ExponentialBackoff(t *testing.T) {
	retryer := src.NewRetryer(src.RetryConfig{
		MaxRetries:      3,
		InitialInterval: 50 * time.Millisecond,
		MaxInterval:     500 * time.Millisecond,
		Multiplier:      2.0,
		Jitter:          false,
	})

	start := time.Now()
	result := retryer.Execute(func() (interface{}, error) {
		return nil, errors.New("failure")
	})
	elapsed := time.Since(start)

	// 间隔: 50ms + 100ms + 200ms = 350ms (最小)
	if elapsed < 300*time.Millisecond {
		t.Errorf("Expected at least 300ms elapsed, got %v", elapsed)
	}

	if result.Attempts != 4 {
		t.Errorf("Expected 4 attempts, got %d", result.Attempts)
	}
}

func TestRetryer_MaxInterval(t *testing.T) {
	retryer := src.NewRetryer(src.RetryConfig{
		MaxRetries:      3,
		InitialInterval: 100 * time.Millisecond,
		MaxInterval:     150 * time.Millisecond, // 限制最大间隔
		Multiplier:      10.0,                    // 高乘数
		Jitter:          false,
	})

	start := time.Now()
	retryer.Execute(func() (interface{}, error) {
		return nil, errors.New("failure")
	})
	elapsed := time.Since(start)

	// 总间隔: 100ms + 150ms(限制) + 150ms(限制) = 400ms
	// 不应超过 600ms
	if elapsed > 600*time.Millisecond {
		t.Errorf("Elapsed %v exceeds expected max", elapsed)
	}
}

func TestRetryer_ZeroRetries(t *testing.T) {
	retryer := src.NewRetryer(src.RetryConfig{
		MaxRetries:      0,
		InitialInterval: 10 * time.Millisecond,
		MaxInterval:     1 * time.Second,
		Multiplier:      2.0,
		Jitter:          false,
	})

	attempts := 0
	result := retryer.Execute(func() (interface{}, error) {
		attempts++
		return nil, errors.New("failure")
	})

	if result.Err == nil {
		t.Error("Expected error")
	}
	if result.Attempts != 1 {
		t.Errorf("Expected 1 attempt, got %d", result.Attempts)
	}
}

func TestRetryer_TotalDuration(t *testing.T) {
	retryer := src.NewRetryer(src.RetryConfig{
		MaxRetries:      2,
		InitialInterval: 50 * time.Millisecond,
		MaxInterval:     1 * time.Second,
		Multiplier:      2.0,
		Jitter:          false,
	})

	result := retryer.Execute(func() (interface{}, error) {
		return nil, errors.New("failure")
	})

	if result.TotalDuration < 100*time.Millisecond {
		t.Errorf("TotalDuration %v seems too short", result.TotalDuration)
	}
}

// ============================================================
// 带重试的熔断器测试
// ============================================================

func TestRetryableCircuitBreaker_Success(t *testing.T) {
	breaker := src.NewCircuitBreaker(src.Config{
		FailureThreshold: 3,
		SuccessThreshold: 2,
		Timeout:         1 * time.Second,
	})

	rcb := src.NewRetryableCircuitBreaker(breaker, src.RetryConfig{
		MaxRetries:      2,
		InitialInterval: 10 * time.Millisecond,
		MaxInterval:     100 * time.Millisecond,
		Multiplier:      2.0,
		Jitter:          false,
	})

	attempts := 0
	result, err := rcb.Execute(func() (interface{}, error) {
		attempts++
		if attempts < 2 {
			return nil, errors.New("temporary")
		}
		return "success", nil
	})

	if err != nil {
		t.Errorf("Expected no error, got %v", err)
	}
	if result != "success" {
		t.Errorf("Expected 'success', got %v", result)
	}
}

func TestRetryableCircuitBreaker_CircuitOpen(t *testing.T) {
	breaker := src.NewCircuitBreaker(src.Config{
		FailureThreshold: 2,
		SuccessThreshold: 2,
		Timeout:         10 * time.Second,
	})
	breaker.SetFallback(src.NewStaticFallback("fallback", nil))

	// 触发熔断
	for i := 0; i < 2; i++ {
		breaker.Execute(func() (interface{}, error) {
			return nil, errors.New("failure")
		})
	}

	rcb := src.NewRetryableCircuitBreaker(breaker, src.RetryConfig{
		MaxRetries:      3,
		InitialInterval: 10 * time.Millisecond,
		MaxInterval:     100 * time.Millisecond,
		Multiplier:      2.0,
		Jitter:          false,
	})

	// 熔断器打开时应该直接返回降级结果
	result, err := rcb.Execute(func() (interface{}, error) {
		return "should not execute", nil
	})

	if err != nil {
		t.Errorf("Expected no error (fallback), got %v", err)
	}
	if result != "fallback" {
		t.Errorf("Expected 'fallback', got %v", result)
	}
}
