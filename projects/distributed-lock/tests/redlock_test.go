package tests

import (
	"context"
	"testing"
	"time"

	"github.com/alicebob/miniredis/v2"
	goredis "github.com/redis/go-redis/v9"

	"github.com/example/distributed-lock/internal/lock"
	"github.com/example/distributed-lock/internal/redis"
)

func setupMultipleMiniredis(t *testing.T, count int) ([]*miniredis.Miniredis, []*goredis.Client) {
	t.Helper()
	servers := make([]*miniredis.Miniredis, count)
	clients := make([]*goredis.Client, count)
	for i := 0; i < count; i++ {
		servers[i] = miniredis.RunT(t)
		clients[i] = goredis.NewClient(&goredis.Options{Addr: servers[i].Addr()})
	}
	return servers, clients
}

func TestRedLock_QuorumSuccess(t *testing.T) {
	servers, clients := setupMultipleMiniredis(t, 5)
	for _, s := range servers {
		defer s.Close()
	}
	for _, c := range clients {
		defer c.Close()
	}

	ctx := context.Background()
	rl := redis.NewRedLock(clients, "redlock-resource",
		lock.WithTTL(10*time.Second),
		lock.WithOwnerID("redlock-owner"))

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
	servers, clients := setupMultipleMiniredis(t, 5)
	for _, s := range servers {
		defer s.Close()
	}
	for _, c := range clients {
		defer c.Close()
	}

	ctx := context.Background()

	// Pre-acquire on 3 nodes (more than quorum)
	for i := 0; i < 3; i++ {
		clients[i].Set(ctx, "lock:redlock-resource", "other-value", 10*time.Second)
	}

	rl := redis.NewRedLock(clients, "redlock-resource",
		lock.WithTTL(10*time.Second),
		lock.WithOwnerID("redlock-owner"),
		lock.WithRetryCount(0))

	acquired, _ := rl.Acquire(ctx)
	if acquired {
		t.Error("expected acquisition to fail (quorum not reached)")
	}
}

func TestRedLock_TimeExceeded(t *testing.T) {
	servers, clients := setupMultipleMiniredis(t, 5)
	for _, s := range servers {
		defer s.Close()
	}
	for _, c := range clients {
		defer c.Close()
	}

	ctx := context.Background()

	// Use very short TTL
	rl := redis.NewRedLock(clients, "redlock-resource",
		lock.WithTTL(1*time.Millisecond),
		lock.WithOwnerID("redlock-owner"),
		lock.WithRetryCount(0))

	// This should fail due to time exceeded
	acquired, _ := rl.Acquire(ctx)
	if acquired {
		t.Error("expected acquisition to fail (time exceeded)")
	}
}

func TestRedLock_MultipleClients(t *testing.T) {
	servers, clients := setupMultipleMiniredis(t, 5)
	for _, s := range servers {
		defer s.Close()
	}
	for _, c := range clients {
		defer c.Close()
	}

	ctx := context.Background()

	// First client acquires
	rl1 := redis.NewRedLock(clients, "multi-resource",
		lock.WithTTL(10*time.Second),
		lock.WithOwnerID("client-1"))
	acquired1, _ := rl1.Acquire(ctx)
	if !acquired1 {
		t.Fatal("expected first client to acquire")
	}

	// Second client should fail
	rl2 := redis.NewRedLock(clients, "multi-resource",
		lock.WithTTL(10*time.Second),
		lock.WithOwnerID("client-2"),
		lock.WithRetryCount(0))
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

// Legacy tests
func TestRedLock_QuorumSuccess_Legacy(t *testing.T) {
	// Create 5 miniredis instances
	servers := make([]*miniredis.Miniredis, 5)
	clients := make([]*goredis.Client, 5)
	for i := 0; i < 5; i++ {
		servers[i] = miniredis.RunT(t)
		clients[i] = goredis.NewClient(&goredis.Options{Addr: servers[i].Addr()})
		defer clients[i].Close()
	}

	rl := redis.NewRedLock(clients, "redlock-resource",
		lock.WithTTL(10*time.Second),
		lock.WithOwnerID("unique-id"))
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

func TestRedLock_QuorumFailure_Legacy(t *testing.T) {
	// Create 5 miniredis instances
	servers := make([]*miniredis.Miniredis, 5)
	clients := make([]*goredis.Client, 5)
	for i := 0; i < 5; i++ {
		servers[i] = miniredis.RunT(t)
		clients[i] = goredis.NewClient(&goredis.Options{Addr: servers[i].Addr()})
		defer clients[i].Close()
	}

	ctx := context.Background()

	// Pre-acquire on 3 nodes (more than quorum)
	for i := 0; i < 3; i++ {
		clients[i].Set(ctx, "lock:redlock-resource", "other-value", 10*time.Second)
	}

	rl := redis.NewRedLock(clients, "redlock-resource",
		lock.WithTTL(10*time.Second),
		lock.WithOwnerID("unique-id"),
		lock.WithRetryCount(0))
	acquired, _ := rl.Acquire(ctx)
	if acquired {
		t.Error("expected acquisition to fail (quorum not reached)")
	}
}
