package main

import (
	"errors"
	"fmt"
	"math/rand"
	"sync"
	"sync/atomic"
	"time"

	"circuit-breaker/src"
)

// main 舱壁模式演示主程序
//
// 演示舱壁模式（Bulkhead Pattern）：
// 1. 资源隔离 - 不同服务使用独立的资源池
// 2. 并发限制 - 限制每个服务最大并发数
// 3. 故障隔离 - 一个服务故障不影响其他服务
// 4. 优雅降级 - 舱壁满时快速失败
func main() {
	fmt.Println("=== 舱壁模式演示 ===")
	fmt.Println()

	basicBulkheadDemo()
	fmt.Println("---")
	bulkheadPoolDemo()
	fmt.Println("---")
	bulkheadWithCircuitBreakerDemo()
	fmt.Println("---")
	resourceIsolationDemo()
}

// basicBulkheadDemo 基本舱壁演示
func basicBulkheadDemo() {
	fmt.Println("1. 基本舱壁")
	fmt.Println("   限制最大并发数，超额请求快速失败")

	// 创建舱壁：最多5个并发
	bh := src.NewBulkhead(src.BulkheadConfig{
		MaxConcurrency: 5,
		MaxWaiters:     10,
	})

	var successCount int64
	var rejectedCount int64
	var wg sync.WaitGroup

	start := time.Now()
	for i := 0; i < 20; i++ {
		wg.Add(1)
		go func(id int) {
			defer wg.Done()

			if !bh.TryAcquire() {
				atomic.AddInt64(&rejectedCount, 1)
				fmt.Printf("  [请求-%02d] 被拒绝（舱壁已满）\n", id)
				return
			}
			defer bh.Release()

			// 模拟处理
			duration := time.Duration(50+rand.Intn(100)) * time.Millisecond
			time.Sleep(duration)

			atomic.AddInt64(&successCount, 1)
			fmt.Printf("  [请求-%02d] 成功 (耗时: %v)\n", id, duration.Truncate(time.Millisecond))
		}(i)
	}

	wg.Wait()
	elapsed := time.Since(start)

	fmt.Printf("\n  统计:\n")
	fmt.Printf("    成功: %d\n", successCount)
	fmt.Printf("    拒绝: %d\n", rejectedCount)
	fmt.Printf("    总耗时: %v\n", elapsed.Truncate(time.Millisecond))
	fmt.Printf("    舱壁状态: %v\n", bh.GetStats())
}

// bulkheadPoolDemo 舱壁池演示
func bulkheadPoolDemo() {
	fmt.Println()
	fmt.Println("2. 舱壁池")
	fmt.Println("   为不同服务创建独立的舱壁")

	pool := src.NewBulkheadPool(src.BulkheadConfig{
		MaxConcurrency: 3,
		MaxWaiters:     5,
	})

	// 获取不同服务的舱壁
	userBH := pool.GetOrCreate("user-service")
	orderBH := pool.GetOrCreate("order-service")
	paymentBH := pool.GetOrCreate("payment-service")

	fmt.Println("  注册服务舱壁:")
	fmt.Printf("    user-service:  并发上限=%d\n", userBH.(*src.Bulkhead).GetStats()["max"])
	fmt.Printf("    order-service: 并发上限=%d\n", orderBH.(*src.Bulkhead).GetStats()["max"])
	fmt.Printf("    payment-service: 并发上限=%d\n", paymentBH.(*src.Bulkhead).GetStats()["max"])

	// 模拟各服务并发请求
	var wg sync.WaitGroup

	// user-service: 10个并发请求
	fmt.Println("\n  模拟 user-service 10个并发请求...")
	for i := 0; i < 10; i++ {
		wg.Add(1)
		go func(id int) {
			defer wg.Done()
			if userBH.TryAcquire() {
				defer userBH.Release()
				time.Sleep(30 * time.Millisecond)
				fmt.Printf("    [user-%02d] 成功\n", id)
			} else {
				fmt.Printf("    [user-%02d] 被拒绝\n", id)
			}
		}(i)
	}

	// order-service: 5个并发请求（独立舱壁，不受user-service影响）
	fmt.Println("  模拟 order-service 5个并发请求...")
	for i := 0; i < 5; i++ {
		wg.Add(1)
		go func(id int) {
			defer wg.Done()
			if orderBH.TryAcquire() {
				defer orderBH.Release()
				time.Sleep(30 * time.Millisecond)
				fmt.Printf("    [order-%02d] 成功\n", id)
			} else {
				fmt.Printf("    [order-%02d] 被拒绝\n", id)
			}
		}(i)
	}

	wg.Wait()

	fmt.Println("\n  所有舱壁状态:")
	for name, stats := range pool.GetAllStats() {
		fmt.Printf("    %s: 剩余=%v, 利用率=%.0f%%\n",
			name,
			stats["remaining"],
			stats["utilization"].(float64)*100,
		)
	}
}

// bulkheadWithCircuitBreakerDemo 舱壁与熔断器组合演示
func bulkheadWithCircuitBreakerDemo() {
	fmt.Println()
	fmt.Println("3. 舱壁 + 熔断器组合")
	fmt.Println("   先通过舱壁检查，再通过熔断器检查")

	// 创建舱壁
	bh := src.NewBulkhead(src.BulkheadConfig{
		MaxConcurrency: 3,
		MaxWaiters:     5,
	})

	// 创建熔断器
	breaker := src.NewCircuitBreaker(src.Config{
		FailureThreshold: 3,
		SuccessThreshold: 2,
		Timeout:          1 * time.Second,
	})
	breaker.SetFallback(src.NewDefaultFallback("舱壁满或熔断器打开"))

	// 组合
	bcb := src.NewBulkheadCircuitBreaker(breaker, bh)

	var wg sync.WaitGroup
	var success, bulkheadReject, breakerReject int64

	fmt.Println("  模拟 15 个并发请求 (舱壁限3, 熔断阈值3)...")
	for i := 0; i < 15; i++ {
		wg.Add(1)
		go func(id int) {
			defer wg.Done()

			result, err := bcb.Execute(func() (interface{}, error) {
				// 模拟 40% 失败率
				if rand.Float64() < 0.4 {
					return nil, errors.New("service error")
				}
				return map[string]interface{}{"id": id, "ok": true}, nil
			})

			if err == nil {
				atomic.AddInt64(&success, 1)
				fmt.Printf("    [req-%02d] 成功: %v\n", id, result)
			} else if err.Error() == "bulkhead full: resource exhausted" {
				atomic.AddInt64(&bulkheadReject, 1)
				fmt.Printf("    [req-%02d] 舱壁拒绝\n", id)
			} else {
				atomic.AddInt64(&breakerReject, 1)
				fmt.Printf("    [req-%02d] 熔断拒绝: %v\n", id, err)
			}
		}(i)
	}

	wg.Wait()

	fmt.Printf("\n  统计: 成功=%d, 舱壁拒绝=%d, 熔断拒绝=%d\n",
		success, bulkheadReject, breakerReject)
	fmt.Printf("  舱壁状态: %v\n", bcb.GetBulkheadStats())
	fmt.Printf("  熔断器状态: %v\n", bcb.GetBreakerStats())
}

// resourceIsolationDemo 资源隔离演示
func resourceIsolationDemo() {
	fmt.Println()
	fmt.Println("4. 资源隔离演示")
	fmt.Println("   展示舱壁如何防止级联故障")

	// 创建舱壁池
	pool := src.NewBulkheadPool(src.BulkheadConfig{
		MaxConcurrency: 2, // 每个服务仅2个并发
		MaxWaiters:     5,
	})

	// 模拟：用户服务过载，但不影响支付服务
	userBH := pool.GetOrCreate("user-service")
	paymentBH := pool.GetOrCreate("payment-service")

	fmt.Println("  阶段1: user-service 满载")
	for i := 0; i < 5; i++ {
		if !userBH.TryAcquire() {
			fmt.Printf("    user-service [%d]: 被拒绝\n", i)
		}
	}

	fmt.Println("  阶段2: payment-service 仍然可用（隔离成功）")
	paid := 0
	for i := 0; i < 5; i++ {
		if paymentBH.TryAcquire() {
			paid++
			paymentBH.Release()
			fmt.Printf("    payment-service [%d]: 成功\n", i)
		} else {
			fmt.Printf("    payment-service [%d]: 被拒绝\n", i)
		}
	}

	fmt.Printf("\n  隔离结果: payment-service 成功 %d/5 (不受 user-service 影响)\n", paid)

	// 清理
	userBH.Close()
	paymentBH.Close()
}
