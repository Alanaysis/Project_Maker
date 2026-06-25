package redis

import (
	"context"
	"strconv"
	"time"

	goredis "github.com/redis/go-redis/v9"

	"github.com/example/distributed-lock/internal/lock"
	"github.com/example/distributed-lock/pkg/utils"
)

// ReentrantRedisLock implements a reentrant distributed lock using Redis.
// The same owner can acquire the lock multiple times; it is released
// only when the release count matches the acquire count.
type ReentrantRedisLock struct {
	client     *goredis.Client
	key        string
	countKey   string
	ownerID    string
	ttl        time.Duration
	retryCount int
	retryDelay time.Duration
}

// NewReentrantRedisLock creates a new reentrant Redis lock.
func NewReentrantRedisLock(client *goredis.Client, key string, opts ...lock.Option) *ReentrantRedisLock {
	cfg := lock.ApplyOptions(opts)
	if cfg.OwnerID == "" {
		cfg.OwnerID = utils.GenerateID()
	}
	return &ReentrantRedisLock{
		client:     client,
		key:        "lock:reentrant:" + key,
		countKey:   "lock:reentrant:" + key + ":count",
		ownerID:    cfg.OwnerID,
		ttl:        cfg.TTL,
		retryCount: cfg.RetryCount,
		retryDelay: cfg.RetryDelay,
	}
}

// Acquire attempts to acquire the reentrant lock.
func (l *ReentrantRedisLock) Acquire(ctx context.Context) (bool, error) {
	for i := 0; i <= l.retryCount; i++ {
		result, err := reentrantAcquireScript.Run(
			ctx, l.client,
			[]string{l.key, l.countKey},
			l.ownerID, int(l.ttl.Seconds()),
		).Int()
		if err != nil {
			return false, err
		}
		if result > 0 {
			return true, nil
		}
		if i < l.retryCount {
			select {
			case <-ctx.Done():
				return false, ctx.Err()
			case <-time.After(l.retryDelay):
			}
		}
	}
	return false, nil
}

// Release decrements the reentrant count. Lock is fully released when count reaches 0.
func (l *ReentrantRedisLock) Release(ctx context.Context) error {
	result, err := reentrantReleaseScript.Run(
		ctx, l.client,
		[]string{l.key, l.countKey},
		l.ownerID,
	).Int()
	if err != nil {
		return err
	}
	if result == -1 {
		return ErrLockNotOwned
	}
	return nil
}

// TTL returns the remaining TTL of the lock.
func (l *ReentrantRedisLock) TTL(ctx context.Context) (time.Duration, error) {
	ttl, err := l.client.TTL(ctx, l.key).Result()
	if err != nil {
		return 0, err
	}
	if ttl < 0 {
		return 0, nil
	}
	return ttl, nil
}

// Count returns the current reentrant count for the owner.
func (l *ReentrantRedisLock) Count(ctx context.Context) (int, error) {
	val, err := l.client.Get(ctx, l.countKey).Result()
	if err == goredis.Nil {
		return 0, nil
	}
	if err != nil {
		return 0, err
	}
	return strconv.Atoi(val)
}
