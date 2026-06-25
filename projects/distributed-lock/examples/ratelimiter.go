package examples

import (
	"context"
	"fmt"
	"log"
	"sync"
	"time"

	"github.com/example/distributed-lock/internal/lock"
)

// RateLimiter demonstrates a distributed rate limiter using locks.
// Ensures rate limits are respected across multiple server instances.
type RateLimiter struct {
	lock         lock.Lock
	key          string
	maxRequests  int
	window       time.Duration
	requests     int
	windowStart  time.Time
	mu           sync.Mutex
}

// NewRateLimiter creates a new distributed rate limiter.
func NewRateLimiter(lock lock.Lock, key string, maxRequests int, window time.Duration) *RateLimiter {
	return &RateLimiter{
		lock:        lock,
		key:         key,
		maxRequests: maxRequests,
		window:      window,
		windowStart: time.Now(),
	}
}

// Allow checks if a request is allowed under the rate limit.
func (r *RateLimiter) Allow(ctx context.Context) (bool, error) {
	// Acquire lock
	acquired, err := r.lock.Acquire(ctx)
	if err != nil {
		return false, err
	}
	if !acquired {
		return false, nil
	}
	defer r.lock.Release(ctx)

	// Check if window has reset
	now := time.Now()
	if now.Sub(r.windowStart) >= r.window {
		r.windowStart = now
		r.requests = 0
	}

	// Check rate limit
	if r.requests >= r.maxRequests {
		return false, nil
	}

	// Increment request count
	r.requests++
	log.Printf("[%s] Request allowed, count: %d/%d",
		r.key, r.requests, r.maxRequests)

	return true, nil
}

// GetUsage returns current usage statistics.
func (r *RateLimiter) GetUsage() (current int, max int, resetIn time.Duration) {
	r.mu.Lock()
	defer r.mu.Unlock()

	elapsed := time.Since(r.windowStart)
	resetIn = r.window - elapsed
	if resetIn < 0 {
		resetIn = 0
	}

	return r.requests, r.maxRequests, resetIn
}

// SlidingWindowLimiter implements a sliding window rate limiter.
type SlidingWindowLimiter struct {
	lock        lock.Lock
	key         string
	maxRequests int
	window      time.Duration
	timestamps  []time.Time
	mu          sync.Mutex
}

// NewSlidingWindowLimiter creates a new sliding window rate limiter.
func NewSlidingWindowLimiter(lock lock.Lock, key string, maxRequests int, window time.Duration) *SlidingWindowLimiter {
	return &SlidingWindowLimiter{
		lock:        lock,
		key:         key,
		maxRequests: maxRequests,
		window:      window,
		timestamps:  make([]time.Time, 0),
	}
}

// Allow checks if a request is allowed using sliding window algorithm.
func (l *SlidingWindowLimiter) Allow(ctx context.Context) (bool, error) {
	// Acquire lock
	acquired, err := l.lock.Acquire(ctx)
	if err != nil {
		return false, err
	}
	if !acquired {
		return false, nil
	}
	defer l.lock.Release(ctx)

	now := time.Now()
	windowStart := now.Add(-l.window)

	// Remove old timestamps
	validTimestamps := make([]time.Time, 0)
	for _, ts := range l.timestamps {
		if ts.After(windowStart) {
			validTimestamps = append(validTimestamps, ts)
		}
	}
	l.timestamps = validTimestamps

	// Check rate limit
	if len(l.timestamps) >= l.maxRequests {
		return false, nil
	}

	// Add current timestamp
	l.timestamps = append(l.timestamps, now)
	log.Printf("[%s] Request allowed, count: %d/%d",
		l.key, len(l.timestamps), l.maxRequests)

	return true, nil
}

// TokenBucketLimiter implements a token bucket rate limiter.
type TokenBucketLimiter struct {
	lock         lock.Lock
	key          string
	maxTokens    int
	refillRate   float64 // tokens per second
	tokens       float64
	lastRefill   time.Time
	mu           sync.Mutex
}

// NewTokenBucketLimiter creates a new token bucket rate limiter.
func NewTokenBucketLimiter(lock lock.Lock, key string, maxTokens int, refillRate float64) *TokenBucketLimiter {
	return &TokenBucketLimiter{
		lock:       lock,
		key:        key,
		maxTokens:  maxTokens,
		refillRate: refillRate,
		tokens:     float64(maxTokens),
		lastRefill: time.Now(),
	}
}

// Allow checks if a request is allowed using token bucket algorithm.
func (l *TokenBucketLimiter) Allow(ctx context.Context) (bool, error) {
	// Acquire lock
	acquired, err := l.lock.Acquire(ctx)
	if err != nil {
		return false, err
	}
	if !acquired {
		return false, nil
	}
	defer l.lock.Release(ctx)

	now := time.Now()

	// Refill tokens
	elapsed := now.Sub(l.lastRefill).Seconds()
	l.tokens += elapsed * l.refillRate
	if l.tokens > float64(l.maxTokens) {
		l.tokens = float64(l.maxTokens)
	}
	l.lastRefill = now

	// Check if token available
	if l.tokens < 1 {
		return false, nil
	}

	// Consume token
	l.tokens--
	log.Printf("[%s] Request allowed, remaining tokens: %.1f",
		l.key, l.tokens)

	return true, nil
}

// ExampleRateLimiter demonstrates rate limiting with distributed locks.
func ExampleRateLimiter() {
	fmt.Println("=== Distributed Rate Limiter Example ===")
	fmt.Println()
	fmt.Println("Problem: API rate limits must be enforced across multiple servers")
	fmt.Println("Solution: Distributed lock ensures consistent rate counting")
	fmt.Println()
	fmt.Println("Algorithms:")
	fmt.Println("  1. Fixed Window: Simple counter per time window")
	fmt.Println("  2. Sliding Window: More accurate, tracks individual requests")
	fmt.Println("  3. Token Bucket: Allows bursts while maintaining average rate")
	fmt.Println()
	fmt.Println("Code Example:")
	fmt.Println(`
  // Create Redis client and lock
  client := redis.NewClient(&redis.Options{Addr: "localhost:6379"})
  distLock := lock.NewRedisLock(client, "ratelimit:api:192.168.1.1",
      lock.WithTTL(1*time.Second))

  // Create rate limiter: 100 requests per minute
  limiter := NewRateLimiter(distLock, "api:192.168.1.1", 100, 1*time.Minute)

  // Check if request is allowed
  allowed, err := limiter.Allow(ctx)
  if !allowed {
      return errors.New("rate limit exceeded")
  }

  // Process request
  processRequest()
`)
}

// ExampleRateLimiter_MultipleServers shows multi-server rate limiting.
func ExampleRateLimiter_MultipleServers() {
	fmt.Println("=== Multi-Server Rate Limiting ===")
	fmt.Println()
	fmt.Println("Server 1 (10.0.0.1):")
	fmt.Println("  - Receives request, acquires lock")
	fmt.Println("  - Reads counter=50, increments to 51")
	fmt.Println("  - Releases lock, processes request")
	fmt.Println()
	fmt.Println("Server 2 (10.0.0.2):")
	fmt.Println("  - Receives request, acquires lock")
	fmt.Println("  - Reads counter=51, increments to 52")
	fmt.Println("  - Releases lock, processes request")
	fmt.Println()
	fmt.Println("All servers see consistent counter state!")
}
