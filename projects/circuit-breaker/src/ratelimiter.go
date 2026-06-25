package src

import (
	"sync"
	"time"
)

// RateLimiter 限流器接口
type RateLimiter interface {
	// Allow 检查是否允许请求通过
	Allow() bool
	// AllowN 检查是否允许N个请求通过
	AllowN(n int) bool
	// GetAvailable 获取当前可用配额
	GetAvailable() int64
}

// ============================================================
// FixedWindowLimiter 固定窗口限流器
// ============================================================

// FixedWindowConfig 固定窗口限流器配置
type FixedWindowConfig struct {
	// MaxRequests 窗口内最大请求数
	MaxRequests int64
	// WindowSize 窗口大小
	WindowSize time.Duration
}

// FixedWindowLimiter 固定窗口限流器
// 在固定时间窗口内限制请求数量，窗口结束时计数器重置
type FixedWindowLimiter struct {
	mu        sync.Mutex
	config    FixedWindowConfig
	count     int64
	windowStart time.Time
}

// NewFixedWindowLimiter 创建固定窗口限流器
func NewFixedWindowLimiter(config FixedWindowConfig) *FixedWindowLimiter {
	return &FixedWindowLimiter{
		config:      config,
		windowStart: time.Now(),
	}
}

// Allow 检查是否允许请求通过
func (l *FixedWindowLimiter) Allow() bool {
	return l.AllowN(1)
}

// AllowN 检查是否允许N个请求通过
func (l *FixedWindowLimiter) AllowN(n int) bool {
	l.mu.Lock()
	defer l.mu.Unlock()

	now := time.Now()

	// 检查是否需要重置窗口
	if now.Sub(l.windowStart) >= l.config.WindowSize {
		l.count = 0
		l.windowStart = now
	}

	// 检查是否超过限制
	if l.count+int64(n) > l.config.MaxRequests {
		return false
	}

	l.count += int64(n)
	return true
}

// GetAvailable 获取当前可用配额
func (l *FixedWindowLimiter) GetAvailable() int64 {
	l.mu.Lock()
	defer l.mu.Unlock()

	now := time.Now()
	if now.Sub(l.windowStart) >= l.config.WindowSize {
		return l.config.MaxRequests
	}

	remaining := l.config.MaxRequests - l.count
	if remaining < 0 {
		return 0
	}
	return remaining
}

// ============================================================
// SlidingWindowLimiter 滑动窗口限流器
// ============================================================

// SlidingWindowConfig 滑动窗口限流器配置
type SlidingWindowConfig struct {
	// MaxRequests 窗口内最大请求数
	MaxRequests int64
	// WindowSize 窗口大小
	WindowSize time.Duration
}

// SlidingWindowLimiter 滑动窗口限流器
// 使用时间戳列表实现精确的滑动窗口限流
type SlidingWindowLimiter struct {
	mu       sync.Mutex
	config   SlidingWindowConfig
	requests []time.Time
}

// NewSlidingWindowLimiter 创建滑动窗口限流器
func NewSlidingWindowLimiter(config SlidingWindowConfig) *SlidingWindowLimiter {
	return &SlidingWindowLimiter{
		config:   config,
		requests: make([]time.Time, 0),
	}
}

// Allow 检查是否允许请求通过
func (l *SlidingWindowLimiter) Allow() bool {
	return l.AllowN(1)
}

// AllowN 检查是否允许N个请求通过
func (l *SlidingWindowLimiter) AllowN(n int) bool {
	l.mu.Lock()
	defer l.mu.Unlock()

	now := time.Now()
	windowStart := now.Add(-l.config.WindowSize)

	// 清理过期的请求记录
	validIdx := 0
	for _, ts := range l.requests {
		if ts.After(windowStart) {
			break
		}
		validIdx++
	}
	l.requests = l.requests[validIdx:]

	// 检查是否超过限制
	if int64(len(l.requests))+int64(n) > l.config.MaxRequests {
		return false
	}

	// 记录请求时间
	for i := 0; i < n; i++ {
		l.requests = append(l.requests, now)
	}
	return true
}

// GetAvailable 获取当前可用配额
func (l *SlidingWindowLimiter) GetAvailable() int64 {
	l.mu.Lock()
	defer l.mu.Unlock()

	now := time.Now()
	windowStart := now.Add(-l.config.WindowSize)

	// 清理过期记录
	validIdx := 0
	for _, ts := range l.requests {
		if ts.After(windowStart) {
			break
		}
		validIdx++
	}
	l.requests = l.requests[validIdx:]

	remaining := l.config.MaxRequests - int64(len(l.requests))
	if remaining < 0 {
		return 0
	}
	return remaining
}

// ============================================================
// TokenBucketLimiter 令牌桶限流器
// ============================================================

// TokenBucketConfig 令牌桶限流器配置
type TokenBucketConfig struct {
	// Rate 令牌生成速率（每秒）
	Rate float64
	// Burst 桶容量（最大令牌数）
	Burst int64
}

// TokenBucketLimiter 令牌桶限流器
// 以固定速率向桶中添加令牌，请求消耗令牌，桶空时拒绝请求
type TokenBucketLimiter struct {
	mu         sync.Mutex
	config     TokenBucketConfig
	tokens     float64
	lastRefill time.Time
}

// NewTokenBucketLimiter 创建令牌桶限流器
func NewTokenBucketLimiter(config TokenBucketConfig) *TokenBucketLimiter {
	return &TokenBucketLimiter{
		config:     config,
		tokens:     float64(config.Burst),
		lastRefill: time.Now(),
	}
}

// Allow 检查是否允许请求通过
func (l *TokenBucketLimiter) Allow() bool {
	return l.AllowN(1)
}

// AllowN 检查是否允许N个请求通过
func (l *TokenBucketLimiter) AllowN(n int) bool {
	l.mu.Lock()
	defer l.mu.Unlock()

	l.refill()

	if l.tokens >= float64(n) {
		l.tokens -= float64(n)
		return true
	}
	return false
}

// GetAvailable 获取当前可用令牌数
func (l *TokenBucketLimiter) GetAvailable() int64 {
	l.mu.Lock()
	defer l.mu.Unlock()

	l.refill()
	available := int64(l.tokens)
	if available < 0 {
		return 0
	}
	return available
}

// refill 补充令牌
func (l *TokenBucketLimiter) refill() {
	now := time.Now()
	elapsed := now.Sub(l.lastRefill).Seconds()
	l.tokens += elapsed * l.config.Rate

	// 限制不超过桶容量
	if l.tokens > float64(l.config.Burst) {
		l.tokens = float64(l.config.Burst)
	}
	l.lastRefill = now
}
