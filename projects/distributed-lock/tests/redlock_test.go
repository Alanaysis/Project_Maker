package tests

import (
	"context"
	"testing"
	"time"

	"github.com/alicebob/miniredis/v2"
	"github.com/redis/go-redis/v9"
)

// RedLock represents a Redlock-based distributed lock
type RedLock struct {
	clients []*redis.Client
	key     string
	value   string
	ttl     time.Duration
	quorum  int
}

// NewRedLock creates a new RedLock instance
func NewRedLock(clients []*redis.Client, key string, value string, ttl time.Duration) *RedLock {
	n := len(clients)
	return &RedLock{
		clients: clients,
		key:     key,
		value:   value,
		ttl:     ttl,
		quorum:  n/2 + 1,
	}
}

// Acquire attempts to acquire the lock on majority of nodes
func (rl *RedLock) Acquire(ctx context.Context) (bool, error) {
	startTime := time.Now()
	acquired := 0

	script := `return redis.call('SET', KEYS[1], ARGV[1], 'NX', 'EX', ARGV[2])`

	for _, client := range rl.clients {
		result, err := client.Eval(ctx, script, []string{rl.key}, rl.value, int(rl.ttl.Seconds())).Result()
		if err != nil {
			continue
		}
		if result != nil {
			acquired++
		}
	}

	elapsed := time.Since(startTime)
	if elapsed >= rl.ttl {
		rl.releaseAll(ctx)
		return false, nil
	}

	if acquired < rl.quorum {
		rl.releaseAll(ctx)
		return false, nil
	}

	return true, nil
}

// Release releases the lock on all nodes
func (rl *RedLock) Release(ctx context.Context) error {
	script := `
		if redis.call("GET", KEYS[1]) == ARGV[1] then
			return redis.call("DEL", KEYS[1])
		else
			return 0
		end
	`

	for _, client := range rl.clients {
		client.Eval(ctx, script, []string{rl.key}, rl.value)
	}
	return nil
}

func (rl *RedLock) releaseAll(ctx context.Context) {
	rl.Release(ctx)
}

func TestRedLock_QuorumSuccess(t *testing.T) {
	// Create 5 miniredis instances
	servers := make([]*miniredis.Miniredis, 5)
	clients := make([]*redis.Client, 5)
	for i := 0; i < 5; i++ {
		servers[i] = miniredis.RunT(t)
		clients[i] = redis.NewClient(&redis.Options{Addr: servers[i].Addr()})
		defer clients[i].Close()
	}

	rl := NewRedLock(clients, "redlock-resource", "unique-id", 10*time.Second)
	ctx := context.Background()

	acquired, err := rl.Acquire(ctx)
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if !acquired {
		t.Fatal("expected to acquire lock with quorum")
	}

	rl.Release(ctx)
}

func TestRedLock_QuorumFailure(t *testing.T) {
	// Create 5 miniredis instances
	servers := make([]*miniredis.Miniredis, 5)
	clients := make([]*redis.Client, 5)
	for i := 0; i < 5; i++ {
		servers[i] = miniredis.RunT(t)
		clients[i] = redis.NewClient(&redis.Options{Addr: servers[i].Addr()})
		defer clients[i].Close()
	}

	ctx := context.Background()

	// Pre-acquire on 3 nodes (more than quorum)
	for i := 0; i < 3; i++ {
		clients[i].Set(ctx, "redlock-resource", "other-value", 10*time.Second)
	}

	rl := NewRedLock(clients, "redlock-resource", "unique-id", 10*time.Second)
	acquired, _ := rl.Acquire(ctx)
	if acquired {
		t.Error("expected acquisition to fail (quorum not reached)")
	}
}

func TestRedLock_TimeExceeded(t *testing.T) {
	// Create 5 miniredis instances
	servers := make([]*miniredis.Miniredis, 5)
	clients := make([]*redis.Client, 5)
	for i := 0; i < 5; i++ {
		servers[i] = miniredis.RunT(t)
		clients[i] = redis.NewClient(&redis.Options{Addr: servers[i].Addr()})
		defer clients[i].Close()
	}

	// Use very short TTL
	rl := NewRedLock(clients, "redlock-resource", "unique-id", 1*time.Millisecond)
	ctx := context.Background()

	// This should fail due to time exceeded
	acquired, _ := rl.Acquire(ctx)
	if acquired {
		t.Error("expected acquisition to fail (time exceeded)")
	}
}

func TestRedLock_MultipleClients(t *testing.T) {
	// Create 5 miniredis instances
	servers := make([]*miniredis.Miniredis, 5)
	clients := make([]*redis.Client, 5)
	for i := 0; i < 5; i++ {
		servers[i] = miniredis.RunT(t)
		clients[i] = redis.NewClient(&redis.Options{Addr: servers[i].Addr()})
		defer clients[i].Close()
	}

	ctx := context.Background()

	// First client acquires
	rl1 := NewRedLock(clients, "multi-resource", "client-1", 10*time.Second)
	acquired1, _ := rl1.Acquire(ctx)
	if !acquired1 {
		t.Fatal("expected first client to acquire")
	}

	// Second client should fail
	rl2 := NewRedLock(clients, "multi-resource", "client-2", 10*time.Second)
	acquired2, _ := rl2.Acquire(ctx)
	if acquired2 {
		t.Error("expected second client to fail")
	}

	// Release first client
	rl1.Release(ctx)

	// Second client should now succeed
	acquired2, _ = rl2.Acquire(ctx)
	if !acquired2 {
		t.Error("expected second client to acquire after release")
	}

	rl2.Release(ctx)
}
