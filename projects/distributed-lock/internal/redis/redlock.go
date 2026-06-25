package redis

import (
	"context"
	"sync"
	"time"

	goredis "github.com/redis/go-redis/v9"

	"github.com/example/distributed-lock/internal/lock"
	"github.com/example/distributed-lock/pkg/utils"
)

// RedLock implements the Redlock algorithm for distributed locking
// across multiple independent Redis nodes.
type RedLock struct {
	clients    []*goredis.Client
	key        string
	ownerID    string
	ttl        time.Duration
	quorum     int
	retryCount int
	retryDelay time.Duration
	mu         sync.Mutex
	acquiredOn []int // indices of nodes where lock is acquired
}

// NewRedLock creates a new Redlock instance.
// The quorum is automatically set to len(clients)/2 + 1.
func NewRedLock(clients []*goredis.Client, key string, opts ...lock.Option) *RedLock {
	cfg := lock.ApplyOptions(opts)
	if cfg.OwnerID == "" {
		cfg.OwnerID = utils.GenerateID()
	}
	return &RedLock{
		clients:    clients,
		key:        "lock:" + key,
		ownerID:    cfg.OwnerID,
		ttl:        cfg.TTL,
		quorum:     len(clients)/2 + 1,
		retryCount: cfg.RetryCount,
		retryDelay: cfg.RetryDelay,
	}
}

// Acquire attempts to acquire the lock using the Redlock algorithm.
func (rl *RedLock) Acquire(ctx context.Context) (bool, error) {
	for i := 0; i <= rl.retryCount; i++ {
		acquired, err := rl.tryAcquire(ctx)
		if err != nil {
			return false, err
		}
		if acquired {
			return true, nil
		}
		if i < rl.retryCount {
			select {
			case <-ctx.Done():
				return false, ctx.Err()
			case <-time.After(rl.retryDelay):
			}
		}
	}
	return false, nil
}

// tryAcquire implements a single Redlock acquisition attempt.
func (rl *RedLock) tryAcquire(ctx context.Context) (bool, error) {
	startTime := time.Now()
	acquiredNodes := make([]int, 0, len(rl.clients))

	// Step 1: Try to acquire lock on all nodes
	for i, client := range rl.clients {
		result, err := acquireScript.Run(ctx, client, []string{rl.key}, rl.ownerID, int(rl.ttl.Seconds())).Int()
		if err != nil {
			continue // Skip failed nodes
		}
		if result == 1 {
			acquiredNodes = append(acquiredNodes, i)
		}
	}

	// Step 2: Calculate elapsed time
	elapsed := time.Since(startTime)

	// Step 3: Check if we have quorum and time validity
	validityTime := rl.ttl - elapsed

	if len(acquiredNodes) < rl.quorum || validityTime <= 0 {
		// Failed to acquire quorum or validity expired, release all
		rl.releaseAll(ctx, acquiredNodes)
		return false, nil
	}

	// Success
	rl.mu.Lock()
	rl.acquiredOn = acquiredNodes
	rl.mu.Unlock()

	return true, nil
}

// Release releases the lock on all nodes where it was acquired.
func (rl *RedLock) Release(ctx context.Context) error {
	rl.mu.Lock()
	nodes := rl.acquiredOn
	rl.acquiredOn = nil
	rl.mu.Unlock()

	rl.releaseAll(ctx, nodes)
	return nil
}

// releaseAll releases the lock on specified nodes.
func (rl *RedLock) releaseAll(ctx context.Context, nodes []int) {
	for _, i := range nodes {
		releaseScript.Run(ctx, rl.clients[i], []string{rl.key}, rl.ownerID)
	}
}

// TTL returns the remaining TTL (minimum across all acquired nodes).
func (rl *RedLock) TTL(ctx context.Context) (time.Duration, error) {
	rl.mu.Lock()
	nodes := rl.acquiredOn
	rl.mu.Unlock()

	if len(nodes) == 0 {
		return 0, nil
	}

	var minTTL time.Duration = -1
	for _, i := range nodes {
		ttl, err := rl.clients[i].TTL(ctx, rl.key).Result()
		if err != nil {
			continue
		}
		if minTTL < 0 || ttl < minTTL {
			minTTL = ttl
		}
	}
	if minTTL < 0 {
		return 0, nil
	}
	return minTTL, nil
}

// Extend extends the lock TTL on all acquired nodes.
func (rl *RedLock) Extend(ctx context.Context, ttl time.Duration) (bool, error) {
	rl.mu.Lock()
	nodes := rl.acquiredOn
	rl.mu.Unlock()

	if len(nodes) < rl.quorum {
		return false, nil
	}

	successCount := 0
	for _, i := range nodes {
		result, err := extendScript.Run(ctx, rl.clients[i], []string{rl.key}, rl.ownerID, int(ttl.Seconds())).Int()
		if err != nil {
			continue
		}
		if result == 1 {
			successCount++
		}
	}

	return successCount >= rl.quorum, nil
}
