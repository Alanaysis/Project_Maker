package tests

import (
	"errors"
	"sync"
	"sync/atomic"
	"testing"
	"time"

	"circuit-breaker/src"
)

// ============================================================
// 舱壁模式测试
// ============================================================

func TestBulkhead_TryAcquire(t *testing.T) {
	bh := src.NewBulkhead(src.BulkheadConfig{
		MaxConcurrency: 3,
		MaxWaiters:     5,
	})

	// 应该允许3个并发
	for i := 0; i < 3; i++ {
		if !bh.TryAcquire() {
			t.Errorf("Acquire %d should succeed", i+1)
		}
	}

	// 第4个应该被拒绝
	if bh.TryAcquire() {
		t.Error("4th acquire should fail (max concurrency reached)")
	}
}

func TestBulkhead_Release(t *testing.T) {
	bh := src.NewBulkhead(src.BulkheadConfig{
		MaxConcurrency: 2,
		MaxWaiters:     5,
	})

	// 占满
	bh.TryAcquire()
	bh.TryAcquire()

	// 此时应该被拒绝
	if bh.TryAcquire() {
		t.Error("Should be rejected")
	}

	// 释放一个
	bh.Release()

	// 现在应该可以获取
	if !bh.TryAcquire() {
		t.Error("Should be allowed after release")
	}

	bh.Release()
	bh.Release()
}

func TestBulkhead_Concurrent(t *testing.T) {
	bh := src.NewBulkhead(src.BulkheadConfig{
		MaxConcurrency: 10,
		MaxWaiters:     20,
	})

	var wg sync.WaitGroup
	var allowed int64

	for i := 0; i < 50; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			if bh.TryAcquire() {
				atomic.AddInt64(&allowed, 1)
				time.Sleep(10 * time.Millisecond)
				bh.Release()
			}
		}()
	}

	wg.Wait()

	if allowed > 10 {
		t.Errorf("Allowed %d, expected <= 10", allowed)
	}
}

func TestBulkhead_Close(t *testing.T) {
	bh := src.NewBulkhead(src.BulkheadConfig{
		MaxConcurrency: 5,
		MaxWaiters:     5,
	})

	bh.Close()

	if bh.TryAcquire() {
		t.Error("Should be rejected after close")
	}
}

func TestBulkhead_GetStats(t *testing.T) {
	bh := src.NewBulkhead(src.BulkheadConfig{
		MaxConcurrency: 5,
		MaxWaiters:     10,
	})

	bh.TryAcquire()
	bh.TryAcquire()

	stats := bh.GetStats().(map[string]interface{})
	if stats["remaining"].(int) != 3 {
		t.Errorf("Expected remaining=3, got %v", stats["remaining"])
	}
	if stats["max"].(int) != 5 {
		t.Errorf("Expected max=5, got %v", stats["max"])
	}
}

func TestBulkheadPool_GetOrCreate(t *testing.T) {
	pool := src.NewBulkheadPool(src.BulkheadConfig{
		MaxConcurrency: 5,
		MaxWaiters:     10,
	})

	bh1 := pool.GetOrCreate("service-a")
	bh2 := pool.GetOrCreate("service-a")
	bh3 := pool.GetOrCreate("service-b")

	// 相同名称应该返回同一个实例
	if bh1 != bh2 {
		t.Error("Same name should return same bulkhead")
	}

	// 不同名称应该返回不同实例
	if bh1 == bh3 {
		t.Error("Different names should return different bulkheads")
	}
}

func TestBulkheadPool_GetAllStats(t *testing.T) {
	pool := src.NewBulkheadPool(src.BulkheadConfig{
		MaxConcurrency: 5,
		MaxWaiters:     10,
	})

	pool.GetOrCreate("svc-a")
	pool.GetOrCreate("svc-b")

	stats := pool.GetAllStats()
	if len(stats) != 2 {
		t.Errorf("Expected 2 bulkheads, got %d", len(stats))
	}
}

func TestBulkheadPool_Remove(t *testing.T) {
	pool := src.NewBulkheadPool(src.BulkheadConfig{
		MaxConcurrency: 5,
		MaxWaiters:     10,
	})

	pool.GetOrCreate("svc-a")
	pool.Remove("svc-a")

	_, exists := pool.Get("svc-a")
	if exists {
		t.Error("Bulkhead should be removed")
	}
}

func TestBulkheadCircuitBreaker(t *testing.T) {
	bh := src.NewBulkhead(src.BulkheadConfig{
		MaxConcurrency: 2,
		MaxWaiters:     5,
	})
	breaker := src.NewCircuitBreaker(src.Config{
		FailureThreshold: 3,
		SuccessThreshold: 2,
		Timeout:          1 * time.Second,
	})

	bcb := src.NewBulkheadCircuitBreaker(breaker, bh)

	// 舱壁满时应该被拒绝
	bh.TryAcquire()
	bh.TryAcquire()

	_, err := bcb.Execute(func() (interface{}, error) {
		return "should not execute", nil
	})

	if err == nil || err.Error() != "bulkhead full: resource exhausted" {
		t.Errorf("Expected bulkhead error, got: %v", err)
	}
}

// ============================================================
// 半开状态限制测试
// ============================================================

func TestHalfOpenMaxRequests(t *testing.T) {
	breaker := src.NewCircuitBreaker(src.Config{
		FailureThreshold:    2,
		SuccessThreshold:    3,
		Timeout:             100 * time.Millisecond,
		HalfOpenMaxRequests: 2, // 半开状态最多2个测试请求
	})

	// 触发熔断
	for i := 0; i < 2; i++ {
		breaker.Execute(func() (interface{}, error) {
			return nil, errors.New("error")
		})
	}

	if breaker.GetState() != src.StateOpen {
		t.Errorf("Expected Open, got %v", breaker.GetState())
	}

	// 等待进入半开
	time.Sleep(150 * time.Millisecond)

	// 第一个请求 -> 半开
	result, err := breaker.Execute(func() (interface{}, error) {
		return "ok", nil
	})
	if err != nil {
		t.Errorf("First half-open request should succeed: %v", err)
	}
	if result != "ok" {
		t.Errorf("Expected 'ok', got %v", result)
	}
	if breaker.GetState() != src.StateHalfOpen {
		t.Errorf("Expected HalfOpen, got %v", breaker.GetState())
	}

	// 第二个请求 -> 半开（达到限制）
	result, err = breaker.Execute(func() (interface{}, error) {
		return "ok2", nil
	})
	if err != nil {
		t.Errorf("Second half-open request should succeed: %v", err)
	}
	if result != "ok2" {
		t.Errorf("Expected 'ok2', got %v", result)
	}

	// 第三个请求 -> 应该被拒绝（半开请求数已达上限）
	_, err = breaker.Execute(func() (interface{}, error) {
		return "should not execute", nil
	})
	if err == nil {
		t.Error("Third request should be rejected (half-open limit reached)")
	}
}

func TestHalfOpenMaxRequestsRecovery(t *testing.T) {
	breaker := src.NewCircuitBreaker(src.Config{
		FailureThreshold:    2,
		SuccessThreshold:    2,
		Timeout:             100 * time.Millisecond,
		HalfOpenMaxRequests: 2,
	})

	// 触发熔断
	for i := 0; i < 2; i++ {
		breaker.Execute(func() (interface{}, error) {
			return nil, errors.New("error")
		})
	}

	// 等待进入半开
	time.Sleep(150 * time.Millisecond)

	// 发送2个成功请求（达到限制）
	for i := 0; i < 2; i++ {
		_, err := breaker.Execute(func() (interface{}, error) {
			return "ok", nil
		})
		if err != nil {
			t.Errorf("Half-open request %d failed: %v", i+1, err)
		}
	}

	// 此时应该已达到SuccessThreshold并恢复关闭
	if breaker.GetState() != src.StateClosed {
		t.Errorf("Expected Closed after half-open success, got %v", breaker.GetState())
	}
}

func TestHalfOpenNoLimit(t *testing.T) {
	// HalfOpenMaxRequests = 0 表示不限制
	breaker := src.NewCircuitBreaker(src.Config{
		FailureThreshold:    2,
		SuccessThreshold:    2,
		Timeout:             100 * time.Millisecond,
		HalfOpenMaxRequests: 0, // 不限制
	})

	// 触发熔断
	for i := 0; i < 2; i++ {
		breaker.Execute(func() (interface{}, error) {
			return nil, errors.New("error")
		})
	}

	// 等待进入半开
	time.Sleep(150 * time.Millisecond)

	// 发送多个请求，都应该通过
	for i := 0; i < 5; i++ {
		_, err := breaker.Execute(func() (interface{}, error) {
			return "ok", nil
		})
		if err != nil {
			t.Errorf("Half-open request %d should not be limited: %v", i+1, err)
		}
	}
}
