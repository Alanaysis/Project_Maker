package redis

import (
	"context"
	"fmt"
	"time"

	goredis "github.com/redis/go-redis/v9"

	"github.com/example/distributed-lock/internal/lock"
	"github.com/example/distributed-lock/pkg/utils"
)

// FairRedisLock implements a fair (FIFO) distributed lock using Redis.
// Waiters are served in the order they requested the lock.
type FairRedisLock struct {
	client     *goredis.Client
	key        string
	queueKey   string
	ownerID    string
	ttl        time.Duration
	retryCount int
	retryDelay time.Duration
	entryID    string // ID in the waiting queue
}

// NewFairRedisLock creates a new fair Redis lock.
func NewFairRedisLock(client *goredis.Client, key string, opts ...lock.Option) *FairRedisLock {
	cfg := lock.ApplyOptions(opts)
	if cfg.OwnerID == "" {
		cfg.OwnerID = utils.GenerateID()
	}
	return &FairRedisLock{
		client:     client,
		key:        "lock:fair:" + key,
		queueKey:   "lock:fair:" + key + ":queue",
		ownerID:    cfg.OwnerID,
		ttl:        cfg.TTL,
		retryCount: cfg.RetryCount,
		retryDelay: cfg.RetryDelay,
		entryID:    fmt.Sprintf("%s:%d", cfg.OwnerID, time.Now().UnixNano()),
	}
}

// Acquire attempts to acquire the fair lock.
// Uses a Redis List as a FIFO queue to ensure ordering.
func (l *FairRedisLock) Acquire(ctx context.Context) (bool, error) {
	// Join the waiting queue
	err := l.client.RPush(ctx, l.queueKey, l.entryID).Err()
	if err != nil {
		return false, err
	}

	// Wait for our turn
	for i := 0; i <= l.retryCount; i++ {
		acquired, err := l.tryAcquire(ctx)
		if err != nil {
			return false, err
		}
		if acquired {
			return true, nil
		}
		if i < l.retryCount {
			select {
			case <-ctx.Done():
				// Remove from queue on cancellation
				l.client.LRem(ctx, l.queueKey, 0, l.entryID)
				return false, ctx.Err()
			case <-time.After(l.retryDelay):
			}
		}
	}

	// Timed out, remove from queue
	l.client.LRem(ctx, l.queueKey, 0, l.entryID)
	return false, nil
}

// tryAcquire checks if it's our turn to acquire the lock.
func (l *FairRedisLock) tryAcquire(ctx context.Context) (bool, error) {
	// Get the first entry in the queue
	first, err := l.client.LIndex(ctx, l.queueKey, 0).Result()
	if err == goredis.Nil {
		return false, nil
	}
	if err != nil {
		return false, err
	}

	// If it's not our turn, wait
	if first != l.entryID {
		return false, nil
	}

	// It's our turn, try to acquire the actual lock
	result, err := acquireScript.Run(ctx, l.client, []string{l.key}, l.ownerID, int(l.ttl.Seconds())).Int()
	if err != nil {
		return false, err
	}
	if result == 1 {
		// Remove from queue
		l.client.LRem(ctx, l.queueKey, 0, l.entryID)
		return true, nil
	}

	return false, nil
}

// Release releases the lock.
func (l *FairRedisLock) Release(ctx context.Context) error {
	result, err := releaseScript.Run(ctx, l.client, []string{l.key}, l.ownerID).Int()
	if err != nil {
		return err
	}
	if result == 0 {
		return ErrLockNotOwned
	}
	return nil
}

// TTL returns the remaining TTL of the lock.
func (l *FairRedisLock) TTL(ctx context.Context) (time.Duration, error) {
	ttl, err := l.client.TTL(ctx, l.key).Result()
	if err != nil {
		return 0, err
	}
	if ttl < 0 {
		return 0, nil
	}
	return ttl, nil
}

// Position returns the caller's position in the waiting queue.
// Returns -1 if not in queue.
func (l *FairRedisLock) Position(ctx context.Context) (int, error) {
	entries, err := l.client.LRange(ctx, l.queueKey, 0, -1).Result()
	if err != nil {
		return -1, err
	}
	for i, entry := range entries {
		if entry == l.entryID {
			return i, nil
		}
	}
	return -1, nil
}

// QueueLength returns the current number of waiters.
func (l *FairRedisLock) QueueLength(ctx context.Context) (int, error) {
	length, err := l.client.LLen(ctx, l.queueKey).Result()
	if err != nil {
		return 0, err
	}
	return int(length), nil
}
