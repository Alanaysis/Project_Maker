package main

import (
	"context"
	"fmt"
	"log"
	"sync"
	"time"

	"github.com/redis/go-redis/v9"
)

func main() {
	fmt.Println("=== 分布式锁示例 ===")
	fmt.Println()

	// 注意: 此示例需要运行中的 Redis 服务器
	// 请确保 Redis 在 localhost:6379 上运行

	client := redis.NewClient(&redis.Options{
		Addr: "localhost:6379",
	})
	defer client.Close()

	ctx := context.Background()

	// 测试连接
	if err := client.Ping(ctx).Err(); err != nil {
		log.Fatalf("无法连接到 Redis: %v", err)
	}
	fmt.Println("已连接到 Redis")
	fmt.Println()

	// 示例 1: 基本分布式锁
	basicLockExample(client, ctx)

	// 示例 2: 并发锁竞争
	concurrentLockExample(client, ctx)

	// 示例 3: 锁续期 (Watchdog)
	watchdogExample(client, ctx)

	// 示例 4: 可重入锁
	reentrantLockExample(client, ctx)
}

func basicLockExample(client *redis.Client, ctx context.Context) {
	fmt.Println("--- 示例 1: 基本分布式锁 ---")

	lockKey := "example:basic-lock"
	lockValue := "client-001"
	lockTTL := 10 * time.Second

	// 获取锁
	ok, err := client.SetNX(ctx, lockKey, lockValue, lockTTL).Result()
	if err != nil {
		log.Printf("获取锁失败: %v", err)
		return
	}
	if !ok {
		fmt.Println("锁已被其他客户端持有")
		return
	}
	fmt.Println("成功获取锁")

	// 查看锁的 TTL
	ttl, _ := client.TTL(ctx, lockKey).Result()
	fmt.Printf("锁的 TTL: %v\n", ttl)

	// 模拟业务逻辑
	fmt.Println("执行业务逻辑...")
	time.Sleep(500 * time.Millisecond)

	// 释放锁
	releaseScript := `
		if redis.call("GET", KEYS[1]) == ARGV[1] then
			return redis.call("DEL", KEYS[1])
		else
			return 0
		end
	`
	result, err := client.Eval(ctx, releaseScript, []string{lockKey}, lockValue).Int64()
	if err != nil {
		log.Printf("释放锁失败: %v", err)
		return
	}
	if result == 1 {
		fmt.Println("锁已释放")
	} else {
		fmt.Println("锁不属于当前客户端")
	}
	fmt.Println()
}

func concurrentLockExample(client *redis.Client, ctx context.Context) {
	fmt.Println("--- 示例 2: 并发锁竞争 ---")

	lockKey := "example:concurrent-lock"
	lockTTL := 5 * time.Second
	numWorkers := 5

	var wg sync.WaitGroup
	successCount := 0
	var mu sync.Mutex

	for i := 0; i < numWorkers; i++ {
		wg.Add(1)
		go func(workerID int) {
			defer wg.Done()

			workerValue := fmt.Sprintf("worker-%d", workerID)

			// 尝试获取锁
			ok, _ := client.SetNX(ctx, lockKey, workerValue, lockTTL).Result()
			if ok {
				mu.Lock()
				successCount++
				mu.Unlock()

				fmt.Printf("  Worker %d: 获取锁成功\n", workerID)

				// 模拟工作
				time.Sleep(100 * time.Millisecond)

				// 释放锁
				releaseScript := `
					if redis.call("GET", KEYS[1]) == ARGV[1] then
						return redis.call("DEL", KEYS[1])
					else
						return 0
					end
				`
				client.Eval(ctx, releaseScript, []string{lockKey}, workerValue)
				fmt.Printf("  Worker %d: 释放锁\n", workerID)
			} else {
				fmt.Printf("  Worker %d: 获取锁失败 (锁已被持有)\n", workerID)
			}
		}(i)
	}

	wg.Wait()
	fmt.Printf("成功获取锁的 Worker 数量: %d/%d\n", successCount, numWorkers)
	fmt.Println()
}

func watchdogExample(client *redis.Client, ctx context.Context) {
	fmt.Println("--- 示例 3: 锁续期 (Watchdog) ---")

	lockKey := "example:watchdog-lock"
	lockValue := "client-003"
	lockTTL := 2 * time.Second

	// 获取锁
	ok, _ := client.SetNX(ctx, lockKey, lockValue, lockTTL).Result()
	if !ok {
		fmt.Println("获取锁失败")
		return
	}
	fmt.Println("获取锁成功")

	// 启动 Watchdog
	stopCh := make(chan struct{})
	doneCh := make(chan struct{})

	go func() {
		defer close(doneCh)
		renewInterval := lockTTL / 3
		ticker := time.NewTicker(renewInterval)
		defer ticker.Stop()

		renewCount := 0
		for {
			select {
			case <-stopCh:
				return
			case <-ticker.C:
				renewScript := `
					if redis.call("GET", KEYS[1]) == ARGV[1] then
						return redis.call("EXPIRE", KEYS[1], ARGV[2])
					else
						return 0
					end
				`
				result, _ := client.Eval(ctx, renewScript,
					[]string{lockKey}, lockValue, int(lockTTL.Seconds())).Int64()
				if result == 1 {
					renewCount++
					fmt.Printf("  锁已续期 %d 次\n", renewCount)
				}
			}
		}
	}()

	// 模拟长时间运行的任务
	fmt.Println("执行长时间任务 (5 秒)...")
	time.Sleep(5 * time.Second)

	// 停止 Watchdog
	close(stopCh)
	<-doneCh

	// 释放锁
	releaseScript := `
		if redis.call("GET", KEYS[1]) == ARGV[1] then
			return redis.call("DEL", KEYS[1])
		else
			return 0
		end
	`
	client.Eval(ctx, releaseScript, []string{lockKey}, lockValue)
	fmt.Println("锁已释放")
	fmt.Println()
}

func reentrantLockExample(client *redis.Client, ctx context.Context) {
	fmt.Println("--- 示例 4: 可重入锁 ---")

	lockKey := "example:reentrant-lock"
	clientID := "client-004"
	lockTTL := 10 * time.Second

	acquireScript := `
		local key = KEYS[1]
		local owner = ARGV[1]
		local ttl = ARGV[2]

		local current = redis.call('HGET', key, 'owner')
		if current == owner then
			redis.call('HINCRBY', key, 'count', 1)
			redis.call('EXPIRE', key, ttl)
			return redis.call('HGET', key, 'count')
		elseif current == false then
			redis.call('HSET', key, 'owner', owner, 'count', 1)
			redis.call('EXPIRE', key, ttl)
			return 1
		else
			return 0
		end
	`

	releaseScript := `
		local key = KEYS[1]
		local owner = ARGV[1]

		local current = redis.call('HGET', key, 'owner')
		if current == owner then
			local count = redis.call('HINCRBY', key, 'count', -1)
			if count <= 0 then
				redis.call('DEL', key)
				return 0
			end
			return count
		else
			return -1
		end
	`

	// 第一次获取
	count, _ := client.Eval(ctx, acquireScript,
		[]string{lockKey}, clientID, int(lockTTL.Seconds())).Int64()
	fmt.Printf("第一次获取, 计数: %d\n", count)

	// 第二次获取 (可重入)
	count, _ = client.Eval(ctx, acquireScript,
		[]string{lockKey}, clientID, int(lockTTL.Seconds())).Int64()
	fmt.Printf("第二次获取 (可重入), 计数: %d\n", count)

	// 第三次获取 (可重入)
	count, _ = client.Eval(ctx, acquireScript,
		[]string{lockKey}, clientID, int(lockTTL.Seconds())).Int64()
	fmt.Printf("第三次获取 (可重入), 计数: %d\n", count)

	// 释放
	count, _ = client.Eval(ctx, releaseScript,
		[]string{lockKey}, clientID).Int64()
	fmt.Printf("第一次释放, 剩余计数: %d\n", count)

	count, _ = client.Eval(ctx, releaseScript,
		[]string{lockKey}, clientID).Int64()
	fmt.Printf("第二次释放, 剩余计数: %d\n", count)

	count, _ = client.Eval(ctx, releaseScript,
		[]string{lockKey}, clientID).Int64()
	fmt.Printf("第三次释放, 锁已完全释放: %d\n", count)

	fmt.Println()
}
