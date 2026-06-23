package examples

import (
	"context"
	"fmt"
	"log"
	"time"

	"github.com/redis/go-redis/v9"
)

// ExampleBasicLock demonstrates basic distributed lock usage
func Example_basicLock() {
	// Create Redis client
	client := redis.NewClient(&redis.Options{
		Addr: "localhost:6379",
	})
	defer client.Close()

	ctx := context.Background()

	// Define lock key and unique value
	lockKey := "my-resource-lock"
	lockValue := "unique-client-id"
	lockTTL := 10 * time.Second

	// Acquire lock using SET NX EX
	ok, err := client.SetNX(ctx, lockKey, lockValue, lockTTL).Result()
	if err != nil {
		log.Fatalf("Failed to acquire lock: %v", err)
	}
	if !ok {
		log.Fatal("Lock is already held by another client")
	}
	fmt.Println("Lock acquired successfully")

	// Simulate business logic
	fmt.Println("Executing business logic...")
	time.Sleep(1 * time.Second)

	// Release lock using Lua script for atomicity
	releaseScript := `
		if redis.call("GET", KEYS[1]) == ARGV[1] then
			return redis.call("DEL", KEYS[1])
		else
			return 0
		end
	`
	result, err := client.Eval(ctx, releaseScript, []string{lockKey}, lockValue).Int64()
	if err != nil {
		log.Fatalf("Failed to release lock: %v", err)
	}
	if result == 0 {
		log.Fatal("Lock was not held by this client")
	}
	fmt.Println("Lock released successfully")
}

// ExampleRedlock demonstrates Redlock algorithm usage
func Example_redlock() {
	// Create multiple Redis clients (typically on different machines)
	clients := []*redis.Client{
		redis.NewClient(&redis.Options{Addr: "redis1:6379"}),
		redis.NewClient(&redis.Options{Addr: "redis2:6379"}),
		redis.NewClient(&redis.Options{Addr: "redis3:6379"}),
	}
	defer func() {
		for _, c := range clients {
			c.Close()
		}
	}()

	ctx := context.Background()
	lockKey := "distributed-resource"
	lockValue := "client-uuid-123"
	lockTTL := 10 * time.Second

	// Calculate quorum (majority)
	quorum := len(clients)/2 + 1

	// Try to acquire lock on each node
	acquired := 0
	startTime := time.Now()

	for _, client := range clients {
		ok, err := client.SetNX(ctx, lockKey, lockValue, lockTTL).Result()
		if err != nil {
			continue
		}
		if ok {
			acquired++
		}
	}

	elapsed := time.Since(startTime)

	// Check if we got quorum and within time budget
	if acquired >= quorum && elapsed < lockTTL {
		effectiveTTL := lockTTL - elapsed
		fmt.Printf("Lock acquired on %d/%d nodes, effective TTL: %v\n",
			acquired, len(clients), effectiveTTL)

		// Execute business logic
		fmt.Println("Executing business logic...")

		// Release lock on all nodes
		releaseScript := `
			if redis.call("GET", KEYS[1]) == ARGV[1] then
				return redis.call("DEL", KEYS[1])
			else
				return 0
			end
		`
		for _, client := range clients {
			client.Eval(ctx, releaseScript, []string{lockKey}, lockValue)
		}
		fmt.Println("Lock released on all nodes")
	} else {
		// Release any acquired locks
		releaseScript := `
			if redis.call("GET", KEYS[1]) == ARGV[1] then
				return redis.call("DEL", KEYS[1])
			else
				return 0
			end
		`
		for _, client := range clients {
			client.Eval(ctx, releaseScript, []string{lockKey}, lockValue)
		}
		fmt.Println("Failed to acquire lock (quorum not reached)")
	}
}

// ExampleWatchdog demonstrates lock renewal with watchdog
func Example_watchdog() {
	client := redis.NewClient(&redis.Options{
		Addr: "localhost:6379",
	})
	defer client.Close()

	ctx := context.Background()
	lockKey := "long-running-task"
	lockValue := "client-id"
	lockTTL := 10 * time.Second

	// Acquire lock
	ok, _ := client.SetNX(ctx, lockKey, lockValue, lockTTL).Result()
	if !ok {
		log.Fatal("Failed to acquire lock")
	}
	fmt.Println("Lock acquired")

	// Start watchdog goroutine
	stopCh := make(chan struct{})
	doneCh := make(chan struct{})

	go func() {
		defer close(doneCh)
		ticker := time.NewTicker(lockTTL / 3)
		defer ticker.Stop()

		for {
			select {
			case <-stopCh:
				return
			case <-ticker.C:
				// Renew lock
				renewScript := `
					if redis.call("GET", KEYS[1]) == ARGV[1] then
						return redis.call("EXPIRE", KEYS[1], ARGV[2])
					else
						return 0
					end
				`
				result, _ := client.Eval(ctx, renewScript,
					[]string{lockKey}, lockValue, int(lockTTL.Seconds())).Int64()
				if result == 0 {
					fmt.Println("Failed to renew lock")
					return
				}
				fmt.Println("Lock renewed")
			}
		}
	}()

	// Simulate long-running task
	fmt.Println("Executing long-running task...")
	time.Sleep(25 * time.Second)

	// Stop watchdog
	close(stopCh)
	<-doneCh

	// Release lock
	releaseScript := `
		if redis.call("GET", KEYS[1]) == ARGV[1] then
			return redis.call("DEL", KEYS[1])
		else
			return 0
		end
	`
	client.Eval(ctx, releaseScript, []string{lockKey}, lockValue)
	fmt.Println("Lock released")
}

// ExampleReentrantLock demonstrates reentrant lock usage
func Example_reentrantLock() {
	client := redis.NewClient(&redis.Options{
		Addr: "localhost:6379",
	})
	defer client.Close()

	ctx := context.Background()
	lockKey := "reentrant-resource"
	clientID := "client-1"
	lockTTL := 10 * time.Second

	// Lua script for reentrant lock
	acquireScript := `
		local key = KEYS[1]
		local owner = ARGV[1]
		local ttl = ARGV[2]

		local current = redis.call('HGET', key, 'owner')
		if current == owner then
			redis.call('HINCRBY', key, 'count', 1)
			redis.call('EXPIRE', key, ttl)
			return 1
		elseif current == false then
			redis.call('HSET', key, 'owner', owner, 'count', 1)
			redis.call('EXPIRE', key, ttl)
			return 1
		else
			return 0
		end
	`

	// First acquisition
	result, _ := client.Eval(ctx, acquireScript,
		[]string{lockKey}, clientID, int(lockTTL.Seconds())).Int64()
	fmt.Printf("First acquire: %d\n", result)

	// Second acquisition (reentrant)
	result, _ = client.Eval(ctx, acquireScript,
		[]string{lockKey}, clientID, int(lockTTL.Seconds())).Int64()
	fmt.Printf("Second acquire (reentrant): %d\n", result)

	// Release script
	releaseScript := `
		local key = KEYS[1]
		local owner = ARGV[1]

		local current = redis.call('HGET', key, 'owner')
		if current == owner then
			local count = redis.call('HINCRBY', key, 'count', -1)
			if count <= 0 then
				redis.call('DEL', key)
				return 1
			end
			return count
		else
			return 0
		end
	`

	// First release (count decreases)
	result, _ = client.Eval(ctx, releaseScript,
		[]string{lockKey}, clientID).Int64()
	fmt.Printf("First release, remaining count: %d\n", result)

	// Second release (lock fully released)
	result, _ = client.Eval(ctx, releaseScript,
		[]string{lockKey}, clientID).Int64()
	fmt.Printf("Second release, lock released: %d\n", result)
}

// ExampleFairLock demonstrates fair lock with waiting queue
func Example_fairLock() {
	client := redis.NewClient(&redis.Options{
		Addr: "localhost:6379",
	})
	defer client.Close()

	ctx := context.Background()
	lockKey := "fair-resource"
	queueKey := "fair-resource:queue"
	clientID := "client-1"
	lockTTL := 10 * time.Second

	// Join queue
	client.RPush(ctx, queueKey, clientID)
	fmt.Printf("Joined queue, position: %d\n", client.LLen(ctx, queueKey).Val())

	// Check if first in queue
	first, _ := client.LIndex(ctx, queueKey, 0).Result()
	if first == clientID {
		// Try to acquire lock
		ok, _ := client.SetNX(ctx, lockKey, clientID, lockTTL).Result()
		if ok {
			fmt.Println("Lock acquired (first in queue)")

			// Execute business logic
			fmt.Println("Executing business logic...")

			// Release lock and leave queue
			releaseScript := `
				if redis.call("GET", KEYS[1]) == ARGV[1] then
					redis.call("DEL", KEYS[1])
					redis.call("LPOP", KEYS[2])
					return 1
				else
					return 0
				end
			`
			client.Eval(ctx, releaseScript, []string{lockKey, queueKey}, clientID)
			fmt.Println("Lock released, left queue")
		}
	}
}
