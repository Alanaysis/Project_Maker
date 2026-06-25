// Package redis implements distributed locks using Redis.
package redis

import (
	"context"
	"errors"
	"time"

	goredis "github.com/redis/go-redis/v9"

	"github.com/example/distributed-lock/internal/lock"
	"github.com/example/distributed-lock/pkg/utils"
)

// Lua scripts for atomic operations.
var (
	// acquireScript atomically sets a key if not exists with expiration.
	// Returns 1 if acquired, 0 if not.
	acquireScript = goredis.NewScript(`
		if redis.call("SET", KEYS[1], ARGV[1], "NX", "EX", ARGV[2]) then
			return 1
		end
		return 0
	`)

	// releaseScript atomically releases a lock if owned by the caller.
	// Returns 1 if released, 0 if not owned.
	releaseScript = goredis.NewScript(`
		if redis.call("GET", KEYS[1]) == ARGV[1] then
			return redis.call("DEL", KEYS[1])
		end
		return 0
	`)

	// extendScript atomically extends TTL if owned by the caller.
	// Returns 1 if extended, 0 if not.
	extendScript = goredis.NewScript(`
		if redis.call("GET", KEYS[1]) == ARGV[1] then
			return redis.call("EXPIRE", KEYS[1], ARGV[2])
		end
		return 0
	`)

	// reentrantAcquireScript atomically increments reentrant count.
	// Returns the new count.
	reentrantAcquireScript = goredis.NewScript(`
		local current = redis.call("GET", KEYS[1])
		if current == false then
			redis.call("SET", KEYS[1], "1", "EX", ARGV[2])
			return 1
		end
		if current == ARGV[1] then
			redis.call("INCR", KEYS[2])
			redis.call("EXPIRE", KEYS[1], ARGV[2])
			return redis.call("GET", KEYS[2])
		end
		return 0
	`)

	// reentrantReleaseScript atomically decrements reentrant count.
	reentrantReleaseScript = goredis.NewScript(`
		if redis.call("GET", KEYS[1]) ~= ARGV[1] then
			return -1
		end
		local count = redis.call("DECR", KEYS[2])
		if count <= 0 then
			redis.call("DEL", KEYS[1])
			redis.call("DEL", KEYS[2])
			return 0
		end
		return count
	`)
)

var (
	ErrLockNotAcquired = errors.New("lock not acquired")
	ErrLockNotOwned    = errors.New("lock not owned by this caller")
)

// RedisLock implements a single-node Redis distributed lock.
type RedisLock struct {
	client   *goredis.Client
	key      string
	ownerID  string
	ttl      time.Duration
	retryCount int
	retryDelay time.Duration
}

// NewRedisLock creates a new Redis distributed lock.
func NewRedisLock(client *goredis.Client, key string, opts ...lock.Option) *RedisLock {
	cfg := lock.ApplyOptions(opts)
	if cfg.OwnerID == "" {
		cfg.OwnerID = utils.GenerateID()
	}
	return &RedisLock{
		client:     client,
		key:        "lock:" + key,
		ownerID:    cfg.OwnerID,
		ttl:        cfg.TTL,
		retryCount: cfg.RetryCount,
		retryDelay: cfg.RetryDelay,
	}
}

// Acquire attempts to acquire the lock with retry logic.
func (l *RedisLock) Acquire(ctx context.Context) (bool, error) {
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
				return false, ctx.Err()
			case <-time.After(l.retryDelay):
			}
		}
	}
	return false, nil
}

// tryAcquire attempts to acquire the lock once.
func (l *RedisLock) tryAcquire(ctx context.Context) (bool, error) {
	result, err := acquireScript.Run(ctx, l.client, []string{l.key}, l.ownerID, int(l.ttl.Seconds())).Int()
	if err != nil {
		return false, err
	}
	return result == 1, nil
}

// Release releases the lock.
func (l *RedisLock) Release(ctx context.Context) error {
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
func (l *RedisLock) TTL(ctx context.Context) (time.Duration, error) {
	ttl, err := l.client.TTL(ctx, l.key).Result()
	if err != nil {
		return 0, err
	}
	if ttl < 0 {
		return 0, nil
	}
	return ttl, nil
}

// Extend extends the lock TTL. Only works if owned by this caller.
func (l *RedisLock) Extend(ctx context.Context, ttl time.Duration) (bool, error) {
	result, err := extendScript.Run(ctx, l.client, []string{l.key}, l.ownerID, int(ttl.Seconds())).Int()
	if err != nil {
		return false, err
	}
	return result == 1, nil
}

// OwnerID returns the lock owner identifier.
func (l *RedisLock) OwnerID() string {
	return l.ownerID
}

// Key returns the lock key.
func (l *RedisLock) Key() string {
	return l.key
}
