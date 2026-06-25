package application

import (
	"sync"
	"time"

	"github.com/distributed-cache/internal/cache"
)

// RateLimiter implements rate limiting using cache
type RateLimiter struct {
	cache    *cache.Cache
	config   RateLimiterConfig
	mu       sync.RWMutex
}

// RateLimiterConfig holds rate limiter configuration
type RateLimiterConfig struct {
	// RequestsPerWindow is the max requests allowed in the time window
	RequestsPerWindow int
	// WindowSize is the time window duration
	WindowSize time.Duration
	// BurstSize is the max burst allowed
	BurstSize int
}

// RateLimitResult represents the result of a rate limit check
type RateLimitResult struct {
	Allowed    bool
	Remaining  int
	ResetAt    time.Time
	RetryAfter time.Duration
}

// DefaultRateLimiterConfig returns default rate limiter configuration
func DefaultRateLimiterConfig() RateLimiterConfig {
	return RateLimiterConfig{
		RequestsPerWindow: 100,
		WindowSize:        time.Minute,
		BurstSize:         10,
	}
}

// NewRateLimiter creates a new rate limiter
func NewRateLimiter(c *cache.Cache, config RateLimiterConfig) *RateLimiter {
	return &RateLimiter{
		cache:  c,
		config: config,
	}
}

// Allow checks if a request should be allowed
func (rl *RateLimiter) Allow(key string) RateLimitResult {
	rl.mu.Lock()
	defer rl.mu.Unlock()

	// Get current counter
	counterKey := "ratelimit:" + key
	val, exists := rl.cache.Get(counterKey)

	var counter *RequestCounter
	if exists {
		counter = val.(*RequestCounter)
	} else {
		counter = &RequestCounter{
			Count:     0,
			WindowStart: time.Now(),
		}
	}

	now := time.Now()

	// Check if window has expired
	if now.Sub(counter.WindowStart) >= rl.config.WindowSize {
		// Reset counter for new window
		counter = &RequestCounter{
			Count:       0,
			WindowStart: now,
		}
	}

	// Check rate limit
	if counter.Count >= rl.config.RequestsPerWindow {
		resetAt := counter.WindowStart.Add(rl.config.WindowSize)
		return RateLimitResult{
			Allowed:    false,
			Remaining:  0,
			ResetAt:    resetAt,
			RetryAfter: resetAt.Sub(now),
		}
	}

	// Allow request
	counter.Count++
	remaining := rl.config.RequestsPerWindow - counter.Count

	// Update cache
	ttl := rl.config.WindowSize - now.Sub(counter.WindowStart)
	rl.cache.Set(counterKey, counter, ttl)

	return RateLimitResult{
		Allowed:   true,
		Remaining: remaining,
		ResetAt:   counter.WindowStart.Add(rl.config.WindowSize),
	}
}

// RequestCounter tracks request count in a time window
type RequestCounter struct {
	Count       int
	WindowStart time.Time
}

// ============ Sliding Window Rate Limiter ============

// SlidingWindowRateLimiter implements sliding window rate limiting
type SlidingWindowRateLimiter struct {
	cache    *cache.Cache
	config   RateLimiterConfig
	mu       sync.RWMutex
}

// NewSlidingWindowRateLimiter creates a new sliding window rate limiter
func NewSlidingWindowRateLimiter(c *cache.Cache, config RateLimiterConfig) *SlidingWindowRateLimiter {
	return &SlidingWindowRateLimiter{
		cache:  c,
		config: config,
	}
}

// Allow checks if a request should be allowed using sliding window
func (sw *SlidingWindowRateLimiter) Allow(key string) RateLimitResult {
	sw.mu.Lock()
	defer sw.mu.Unlock()

	now := time.Now()
	windowKey := "sliding:" + key

	// Get window data
	val, exists := sw.cache.Get(windowKey)
	var window *SlidingWindow
	if exists {
		window = val.(*SlidingWindow)
	} else {
		window = &SlidingWindow{
			PreviousCount: 0,
			CurrentCount:  0,
			WindowStart:   now,
		}
	}

	// Check if we need to slide the window
	elapsed := now.Sub(window.WindowStart)
	if elapsed >= sw.config.WindowSize {
		// Slide window
		window.PreviousCount = window.CurrentCount
		window.CurrentCount = 0
		window.WindowStart = now
		elapsed = 0
	}

	// Calculate weighted count
	weight := float64(sw.config.WindowSize-elapsed) / float64(sw.config.WindowSize)
	weightedCount := float64(window.PreviousCount)*weight + float64(window.CurrentCount)

	// Check rate limit
	if int(weightedCount) >= sw.config.RequestsPerWindow {
		resetAt := window.WindowStart.Add(sw.config.WindowSize)
		return RateLimitResult{
			Allowed:    false,
			Remaining:  0,
			ResetAt:    resetAt,
			RetryAfter: resetAt.Sub(now),
		}
	}

	// Allow request
	window.CurrentCount++
	remaining := sw.config.RequestsPerWindow - int(weightedCount) - 1

	// Update cache
	ttl := sw.config.WindowSize*2 - elapsed
	sw.cache.Set(windowKey, window, ttl)

	return RateLimitResult{
		Allowed:   true,
		Remaining: remaining,
		ResetAt:   window.WindowStart.Add(sw.config.WindowSize),
	}
}

// SlidingWindow tracks requests in a sliding window
type SlidingWindow struct {
	PreviousCount int
	CurrentCount  int
	WindowStart   time.Time
}

// ============ Token Bucket Rate Limiter ============

// TokenBucketRateLimiter implements token bucket rate limiting
type TokenBucketRateLimiter struct {
	cache    *cache.Cache
	config   TokenBucketConfig
	mu       sync.RWMutex
}

// TokenBucketConfig holds token bucket configuration
type TokenBucketConfig struct {
	Rate       float64 // Tokens per second
	BurstSize  int     // Max tokens
}

// NewTokenBucketRateLimiter creates a new token bucket rate limiter
func NewTokenBucketRateLimiter(c *cache.Cache, config TokenBucketConfig) *TokenBucketRateLimiter {
	return &TokenBucketRateLimiter{
		cache:  c,
		config: config,
	}
}

// Allow checks if a request should be allowed using token bucket
func (tb *TokenBucketRateLimiter) Allow(key string) RateLimitResult {
	tb.mu.Lock()
	defer tb.mu.Unlock()

	now := time.Now()
	bucketKey := "bucket:" + key

	// Get bucket
	val, exists := tb.cache.Get(bucketKey)
	var bucket *TokenBucket
	if exists {
		bucket = val.(*TokenBucket)
	} else {
		bucket = &TokenBucket{
			Tokens:     float64(tb.config.BurstSize),
			LastRefill: now,
		}
	}

	// Refill tokens
	elapsed := now.Sub(bucket.LastRefill).Seconds()
	bucket.Tokens += elapsed * tb.config.Rate
	if bucket.Tokens > float64(tb.config.BurstSize) {
		bucket.Tokens = float64(tb.config.BurstSize)
	}
	bucket.LastRefill = now

	// Check if token available
	if bucket.Tokens < 1 {
		waitTime := time.Duration((1 - bucket.Tokens) / tb.config.Rate * float64(time.Second))
		return RateLimitResult{
			Allowed:    false,
			Remaining:  0,
			ResetAt:    now.Add(waitTime),
			RetryAfter: waitTime,
		}
	}

	// Consume token
	bucket.Tokens--
	remaining := int(bucket.Tokens)

	// Update cache (expires after 2x the time to fill the bucket)
	ttl := time.Duration(float64(tb.config.BurstSize)/tb.config.Rate*2) * time.Second
	tb.cache.Set(bucketKey, bucket, ttl)

	return RateLimitResult{
		Allowed:   true,
		Remaining: remaining,
		ResetAt:   now.Add(time.Duration(1/tb.config.Rate) * time.Second),
	}
}

// TokenBucket represents a token bucket
type TokenBucket struct {
	Tokens     float64
	LastRefill time.Time
}
