package redis

import (
	"context"
	"time"

	goredis "github.com/redis/go-redis/v9"

	"github.com/example/distributed-lock/internal/lock"
	"github.com/example/distributed-lock/pkg/utils"
)

// Lua scripts for read-write lock operations.
var (
	// acquireReadScript atomically increments reader count if no writer holds the lock.
	// Returns 1 if acquired, 0 if a writer holds the lock.
	acquireReadScript = goredis.NewScript(`
		local writer = redis.call("GET", KEYS[2])
		if writer == false or writer == ARGV[1] then
			redis.call("INCR", KEYS[1])
			redis.call("EXPIRE", KEYS[1], ARGV[2])
			return 1
		end
		return 0
	`)

	// releaseReadScript atomically decrements reader count.
	releaseReadScript = goredis.NewScript(`
		local count = redis.call("GET", KEYS[1])
		if count == false or tonumber(count) <= 0 then
			return 0
		end
		count = redis.call("DECR", KEYS[1])
		if count <= 0 then
			redis.call("DEL", KEYS[1])
		end
		return 1
	`)

	// acquireWriteScript atomically acquires write lock if no readers and no writer.
	acquireWriteScript = goredis.NewScript(`
		local readers = redis.call("GET", KEYS[1])
		if readers ~= false and tonumber(readers) > 0 then
			return 0
		end
		if redis.call("SET", KEYS[2], ARGV[1], "NX", "EX", ARGV[2]) then
			return 1
		end
		return 0
	`)

	// releaseWriteScript atomically releases write lock if owned.
	releaseWriteScript = goredis.NewScript(`
		if redis.call("GET", KEYS[1]) == ARGV[1] then
			return redis.call("DEL", KEYS[1])
		end
		return 0
	`)
)

// ReadWriteRedisLock implements a reader-writer distributed lock using Redis.
// Multiple readers can hold the lock simultaneously, but writers have exclusive access.
type ReadWriteRedisLock struct {
	client     *goredis.Client
	readKey    string
	writeKey   string
	ownerID    string
	ttl        time.Duration
	retryCount int
	retryDelay time.Duration
}

// NewReadWriteRedisLock creates a new read-write Redis lock.
func NewReadWriteRedisLock(client *goredis.Client, key string, opts ...lock.Option) *ReadWriteRedisLock {
	cfg := lock.ApplyOptions(opts)
	if cfg.OwnerID == "" {
		cfg.OwnerID = utils.GenerateID()
	}
	return &ReadWriteRedisLock{
		client:     client,
		readKey:    "lock:rw:" + key + ":readers",
		writeKey:   "lock:rw:" + key + ":writer",
		ownerID:    cfg.OwnerID,
		ttl:        cfg.TTL,
		retryCount: cfg.RetryCount,
		retryDelay: cfg.RetryDelay,
	}
}

// AcquireRead acquires a read lock (shared).
func (l *ReadWriteRedisLock) AcquireRead(ctx context.Context) (bool, error) {
	for i := 0; i <= l.retryCount; i++ {
		result, err := acquireReadScript.Run(
			ctx, l.client,
			[]string{l.readKey, l.writeKey},
			l.ownerID, int(l.ttl.Seconds()),
		).Int()
		if err != nil {
			return false, err
		}
		if result == 1 {
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

// AcquireWrite acquires a write lock (exclusive).
func (l *ReadWriteRedisLock) AcquireWrite(ctx context.Context) (bool, error) {
	for i := 0; i <= l.retryCount; i++ {
		result, err := acquireWriteScript.Run(
			ctx, l.client,
			[]string{l.readKey, l.writeKey},
			l.ownerID, int(l.ttl.Seconds()),
		).Int()
		if err != nil {
			return false, err
		}
		if result == 1 {
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

// ReleaseRead releases a read lock.
func (l *ReadWriteRedisLock) ReleaseRead(ctx context.Context) error {
	result, err := releaseReadScript.Run(
		ctx, l.client,
		[]string{l.readKey},
	).Int()
	if err != nil {
		return err
	}
	if result == 0 {
		return ErrLockNotOwned
	}
	return nil
}

// ReleaseWrite releases a write lock.
func (l *ReadWriteRedisLock) ReleaseWrite(ctx context.Context) error {
	result, err := releaseWriteScript.Run(
		ctx, l.client,
		[]string{l.writeKey},
		l.ownerID,
	).Int()
	if err != nil {
		return err
	}
	if result == 0 {
		return ErrLockNotOwned
	}
	return nil
}

// ReaderCount returns the current number of readers.
func (l *ReadWriteRedisLock) ReaderCount(ctx context.Context) (int, error) {
	val, err := l.client.Get(ctx, l.readKey).Int()
	if err == goredis.Nil {
		return 0, nil
	}
	if err != nil {
		return 0, err
	}
	return val, nil
}
