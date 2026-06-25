package tests

import (
	"sync"
	"testing"
	"time"

	"circuit-breaker/src"
)

// ============================================================
// 固定窗口限流器测试
// ============================================================

func TestFixedWindowLimiter_Allow(t *testing.T) {
	limiter := src.NewFixedWindowLimiter(src.FixedWindowConfig{
		MaxRequests: 5,
		WindowSize:  1 * time.Second,
	})

	// 应该允许5个请求
	for i := 0; i < 5; i++ {
		if !limiter.Allow() {
			t.Errorf("Request %d should be allowed", i+1)
		}
	}

	// 第6个应该被拒绝
	if limiter.Allow() {
		t.Error("6th request should be rejected")
	}
}

func TestFixedWindowLimiter_WindowReset(t *testing.T) {
	limiter := src.NewFixedWindowLimiter(src.FixedWindowConfig{
		MaxRequests: 3,
		WindowSize:  100 * time.Millisecond,
	})

	// 用完配额
	for i := 0; i < 3; i++ {
		limiter.Allow()
	}

	if limiter.Allow() {
		t.Error("Should be rate limited")
	}

	// 等待窗口重置
	time.Sleep(150 * time.Millisecond)

	if !limiter.Allow() {
		t.Error("Should be allowed after window reset")
	}
}

func TestFixedWindowLimiter_AllowN(t *testing.T) {
	limiter := src.NewFixedWindowLimiter(src.FixedWindowConfig{
		MaxRequests: 10,
		WindowSize:  1 * time.Second,
	})

	// 一次申请5个
	if !limiter.AllowN(5) {
		t.Error("Should allow 5 requests")
	}

	// 再申请4个
	if !limiter.AllowN(4) {
		t.Error("Should allow 4 more requests")
	}

	// 再申请2个应该失败（只剩1个配额）
	if limiter.AllowN(2) {
		t.Error("Should reject 2 requests (only 1 left)")
	}
}

func TestFixedWindowLimiter_GetAvailable(t *testing.T) {
	limiter := src.NewFixedWindowLimiter(src.FixedWindowConfig{
		MaxRequests: 10,
		WindowSize:  1 * time.Second,
	})

	if limiter.GetAvailable() != 10 {
		t.Errorf("Expected 10 available, got %d", limiter.GetAvailable())
	}

	limiter.AllowN(7)

	if limiter.GetAvailable() != 3 {
		t.Errorf("Expected 3 available, got %d", limiter.GetAvailable())
	}
}

func TestFixedWindowLimiter_Concurrent(t *testing.T) {
	limiter := src.NewFixedWindowLimiter(src.FixedWindowConfig{
		MaxRequests: 100,
		WindowSize:  1 * time.Second,
	})

	var wg sync.WaitGroup
	allowed := int64(0)
	var mu sync.Mutex

	for i := 0; i < 200; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			if limiter.Allow() {
				mu.Lock()
				allowed++
				mu.Unlock()
			}
		}()
	}

	wg.Wait()

	if allowed > 100 {
		t.Errorf("Allowed %d requests, should be <= 100", allowed)
	}
}

// ============================================================
// 滑动窗口限流器测试
// ============================================================

func TestSlidingWindowLimiter_Allow(t *testing.T) {
	limiter := src.NewSlidingWindowLimiter(src.SlidingWindowConfig{
		MaxRequests: 5,
		WindowSize:  1 * time.Second,
	})

	for i := 0; i < 5; i++ {
		if !limiter.Allow() {
			t.Errorf("Request %d should be allowed", i+1)
		}
	}

	if limiter.Allow() {
		t.Error("6th request should be rejected")
	}
}

func TestSlidingWindowLimiter_SlidingBehavior(t *testing.T) {
	limiter := src.NewSlidingWindowLimiter(src.SlidingWindowConfig{
		MaxRequests: 3,
		WindowSize:  200 * time.Millisecond,
	})

	// 发送3个请求
	for i := 0; i < 3; i++ {
		limiter.Allow()
	}

	if limiter.Allow() {
		t.Error("Should be rate limited")
	}

	// 等待部分窗口滑过
	time.Sleep(250 * time.Millisecond)

	// 窗口滑过后应该可以发送新请求
	if !limiter.Allow() {
		t.Error("Should be allowed after window slides")
	}
}

func TestSlidingWindowLimiter_GetAvailable(t *testing.T) {
	limiter := src.NewSlidingWindowLimiter(src.SlidingWindowConfig{
		MaxRequests: 10,
		WindowSize:  1 * time.Second,
	})

	if limiter.GetAvailable() != 10 {
		t.Errorf("Expected 10 available, got %d", limiter.GetAvailable())
	}

	limiter.AllowN(6)

	if limiter.GetAvailable() != 4 {
		t.Errorf("Expected 4 available, got %d", limiter.GetAvailable())
	}
}

func TestSlidingWindowLimiter_Concurrent(t *testing.T) {
	limiter := src.NewSlidingWindowLimiter(src.SlidingWindowConfig{
		MaxRequests: 50,
		WindowSize:  1 * time.Second,
	})

	var wg sync.WaitGroup
	allowed := int64(0)
	var mu sync.Mutex

	for i := 0; i < 100; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			if limiter.Allow() {
				mu.Lock()
				allowed++
				mu.Unlock()
			}
		}()
	}

	wg.Wait()

	if allowed > 50 {
		t.Errorf("Allowed %d requests, should be <= 50", allowed)
	}
}

// ============================================================
// 令牌桶限流器测试
// ============================================================

func TestTokenBucketLimiter_Allow(t *testing.T) {
	limiter := src.NewTokenBucketLimiter(src.TokenBucketConfig{
		Rate:  10,
		Burst: 10,
	})

	// 应该允许10个突发请求
	for i := 0; i < 10; i++ {
		if !limiter.Allow() {
			t.Errorf("Request %d should be allowed (burst)", i+1)
		}
	}

	// 第11个应该被拒绝
	if limiter.Allow() {
		t.Error("11th request should be rejected (bucket empty)")
	}
}

func TestTokenBucketLimiter_Refill(t *testing.T) {
	limiter := src.NewTokenBucketLimiter(src.TokenBucketConfig{
		Rate:  100, // 100 tokens/sec
		Burst: 10,
	})

	// 用完令牌
	for i := 0; i < 10; i++ {
		limiter.Allow()
	}

	// 等待补充（100ms应该补充约10个令牌）
	time.Sleep(150 * time.Millisecond)

	if !limiter.Allow() {
		t.Error("Should have refilled tokens")
	}
}

func TestTokenBucketLimiter_GetAvailable(t *testing.T) {
	limiter := src.NewTokenBucketLimiter(src.TokenBucketConfig{
		Rate:  10,
		Burst: 20,
	})

	available := limiter.GetAvailable()
	if available != 20 {
		t.Errorf("Expected 20 available, got %d", available)
	}

	limiter.AllowN(15)

	available = limiter.GetAvailable()
	if available != 5 {
		t.Errorf("Expected 5 available, got %d", available)
	}
}

func TestTokenBucketLimiter_BurstLimit(t *testing.T) {
	limiter := src.NewTokenBucketLimiter(src.TokenBucketConfig{
		Rate:  1000,
		Burst: 5,
	})

	// 等待一段时间让桶满
	time.Sleep(10 * time.Millisecond)

	// 即使速率很高，桶容量限制了突发
	available := limiter.GetAvailable()
	if available > 5 {
		t.Errorf("Available %d should not exceed burst limit 5", available)
	}
}

func TestTokenBucketLimiter_Concurrent(t *testing.T) {
	limiter := src.NewTokenBucketLimiter(src.TokenBucketConfig{
		Rate:  100,
		Burst: 50,
	})

	var wg sync.WaitGroup
	allowed := int64(0)
	var mu sync.Mutex

	for i := 0; i < 100; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			if limiter.Allow() {
				mu.Lock()
				allowed++
				mu.Unlock()
			}
		}()
	}

	wg.Wait()

	if allowed > 50 {
		t.Errorf("Allowed %d requests, should be <= burst (50)", allowed)
	}
}

// ============================================================
// 限流器接口测试
// ============================================================

func TestRateLimiter_Interface(t *testing.T) {
	// 验证所有限流器都实现了 RateLimiter 接口
	var _ src.RateLimiter = src.NewFixedWindowLimiter(src.FixedWindowConfig{})
	var _ src.RateLimiter = src.NewSlidingWindowLimiter(src.SlidingWindowConfig{})
	var _ src.RateLimiter = src.NewTokenBucketLimiter(src.TokenBucketConfig{})
}
