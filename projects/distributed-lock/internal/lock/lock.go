// Package lock defines the core interfaces for distributed locks.
package lock

import (
	"context"
	"time"
)

// Lock is the base interface for all distributed lock implementations.
type Lock interface {
	// Acquire attempts to acquire the lock. Returns true if successful.
	Acquire(ctx context.Context) (bool, error)

	// Release releases the lock. Only the holder should call this.
	Release(ctx context.Context) error

	// TTL returns the remaining time-to-live of the lock.
	TTL(ctx context.Context) (time.Duration, error)
}

// ReentrantLock extends Lock with reentrant (recursive) acquisition support.
type ReentrantLock interface {
	Lock

	// Count returns the current reentrant count for the caller.
	Count(ctx context.Context) (int, error)
}

// ReadWriteLock provides reader-writer lock semantics.
type ReadWriteLock interface {
	// AcquireRead acquires a read lock (shared).
	AcquireRead(ctx context.Context) (bool, error)

	// AcquireWrite acquires a write lock (exclusive).
	AcquireWrite(ctx context.Context) (bool, error)

	// ReleaseRead releases a read lock.
	ReleaseRead(ctx context.Context) error

	// ReleaseWrite releases a write lock.
	ReleaseWrite(ctx context.Context) error
}

// FairLock extends Lock with FIFO ordering guarantees.
type FairLock interface {
	Lock

	// Position returns the caller's position in the waiting queue.
	// Returns -1 if not in queue.
	Position(ctx context.Context) (int, error)

	// QueueLength returns the current number of waiters.
	QueueLength(ctx context.Context) (int, error)
}

// Option is a functional option for configuring locks.
type Option func(*Config)

// Config holds lock configuration.
type Config struct {
	TTL         time.Duration
	RetryCount  int
	RetryDelay  time.Duration
	OwnerID     string
}

// WithTTL sets the lock TTL.
func WithTTL(ttl time.Duration) Option {
	return func(c *Config) {
		c.TTL = ttl
	}
}

// WithRetryCount sets the number of retry attempts.
func WithRetryCount(count int) Option {
	return func(c *Config) {
		c.RetryCount = count
	}
}

// WithRetryDelay sets the delay between retries.
func WithRetryDelay(delay time.Duration) Option {
	return func(c *Config) {
		c.RetryDelay = delay
	}
}

// WithOwnerID sets the owner identifier.
func WithOwnerID(id string) Option {
	return func(c *Config) {
		c.OwnerID = id
	}
}

// DefaultConfig returns a Config with sensible defaults.
func DefaultConfig() *Config {
	return &Config{
		TTL:        10 * time.Second,
		RetryCount: 3,
		RetryDelay: 200 * time.Millisecond,
	}
}

// ApplyOptions applies functional options to a Config.
func ApplyOptions(opts []Option) *Config {
	cfg := DefaultConfig()
	for _, opt := range opts {
		opt(cfg)
	}
	return cfg
}
