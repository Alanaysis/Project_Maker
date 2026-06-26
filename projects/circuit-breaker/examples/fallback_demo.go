package main

import (
	"errors"
	"fmt"
	"math/rand"
	"sync"
	"time"

	"circuit-breaker/src"
)

// main 降级策略演示主程序
//
// 演示四种降级策略：
// 1. 静态降级 - 返回固定的默认值
// 2. 缓存降级 - 返回缓存中的数据
// 3. 组合降级 - 按优先级尝试多种策略
// 4. 自定义降级 - 根据场景自定义逻辑
func main() {
	fmt.Println("=== 降级策略演示 ===")
	fmt.Println()

	staticFallbackDemo()
	fmt.Println("---")
	cacheFallbackDemo()
	fmt.Println("---")
	compositeFallbackDemo()
	fmt.Println("---")
	customFallbackDemo()
	fmt.Println("---")
	fallbackComparisonDemo()
}

// staticFallbackDemo 静态降级策略演示
func staticFallbackDemo() {
	fmt.Println("1. 静态降级策略")
	fmt.Println("   熔断器打开时返回固定的默认值")

	breaker := src.NewCircuitBreaker(src.Config{
		FailureThreshold: 3,
		SuccessThreshold: 2,
		Timeout:          1 * time.Second,
	})

	// 设置静态降级
	breaker.SetFallback(src.NewStaticFallback(
		map[string]interface{}{
			"error":      "service_unavailable",
			"message":    "服务暂时不可用，请稍后重试",
			"retry_after": "30s",
		},
		errors.New("circuit open"),
	))

	// 触发熔断
	fmt.Println("   触发熔断...")
	for i := 0; i < 3; i++ {
		breaker.Execute(func() (interface{}, error) {
			return nil, errors.New("service error")
		})
	}

	// 熔断后请求走降级
	fmt.Println("   熔断后请求:")
	result, err := breaker.Execute(func() (interface{}, error) {
		return nil, errors.New("should not reach here")
	})
	fmt.Printf("   降级结果: %v\n", result)
	fmt.Printf("   错误: %v\n", err)
}

// cacheFallbackDemo 缓存降级策略演示
func cacheFallbackDemo() {
	fmt.Println()
	fmt.Println("2. 缓存降级策略")
	fmt.Println("   熔断器打开时返回缓存中的数据")

	breaker := src.NewCircuitBreaker(src.Config{
		FailureThreshold: 3,
		SuccessThreshold: 2,
		Timeout:          1 * time.Second,
	})

	// 设置缓存降级
	cacheFB := src.NewCacheFallback(30 * time.Second)
	cacheFB.SetCache("user:123", map[string]interface{}{
		"id":     123,
		"name":   "张三",
		"cached": true,
	})
	cacheFB.SetCache("product:456", map[string]interface{}{
		"id":     456,
		"name":   "缓存商品",
		"price":  99.99,
		"cached": true,
	})
	breaker.SetFallback(cacheFB)

	// 触发熔断
	fmt.Println("   触发熔断...")
	for i := 0; i < 3; i++ {
		breaker.Execute(func() (interface{}, error) {
			return nil, errors.New("service error")
		})
	}

	// 熔断后走缓存降级
	fmt.Println("   熔断后请求:")
	result, err := breaker.Execute(func() (interface{}, error) {
		return nil, errors.New("should not reach here")
	})
	fmt.Printf("   降级结果: %v\n", result)
	fmt.Printf("   错误: %v\n", err)
}

// compositeFallbackDemo 组合降级策略演示
func compositeFallbackDemo() {
	fmt.Println()
	fmt.Println("3. 组合降级策略")
	fmt.Println("   按优先级依次尝试多种降级策略")

	breaker := src.NewCircuitBreaker(src.Config{
		FailureThreshold: 3,
		SuccessThreshold: 2,
		Timeout:          1 * time.Second,
	})

	// 创建组合降级：缓存 -> 静态默认值
	cacheFB := src.NewCacheFallback(30 * time.Second)
	cacheFB.SetCache("fallback", map[string]interface{}{
		"source": "cache",
		"data":   "cached data",
	})

	// 组合降级策略
	compositeFB := src.NewCompositeFallback(
		cacheFB,
		src.NewStaticFallback(
			map[string]interface{}{
				"source": "static",
				"data":   "default data",
			},
			nil,
		),
	)
	breaker.SetFallback(compositeFB)

	// 触发熔断
	fmt.Println("   触发熔断...")
	for i := 0; i < 3; i++ {
		breaker.Execute(func() (interface{}, error) {
			return nil, errors.New("service error")
		})
	}

	// 熔断后走组合降级
	fmt.Println("   熔断后请求:")
	result, err := breaker.Execute(func() (interface{}, error) {
		return nil, errors.New("should not reach here")
	})
	fmt.Printf("   降级结果: %v\n", result)
	fmt.Printf("   错误: %v\n", err)

	// 清空缓存，测试次优降级
	fmt.Println("   清空缓存后:")
	cacheFB.SetCache("", nil)
	result, err = breaker.Execute(func() (interface{}, error) {
		return nil, errors.New("should not reach here")
	})
	fmt.Printf("   降级结果: %v\n", result)
	fmt.Printf("   错误: %v\n", err)
}

// customFallbackDemo 自定义降级策略演示
func customFallbackDemo() {
	fmt.Println()
	fmt.Println("4. 自定义降级策略")
	fmt.Println("   根据场景自定义降级逻辑")

	breaker := src.NewCircuitBreaker(src.Config{
		FailureThreshold: 3,
		SuccessThreshold: 2,
		Timeout:          1 * time.Second,
	})

	// 自定义降级：延迟降级（等待服务恢复）
	breaker.SetFallback(src.NewFallbackFunc(func() (interface{}, error) {
		fmt.Println("   等待服务恢复...")
		time.Sleep(200 * time.Millisecond)
		return map[string]interface{}{
			"source": "delayed_fallback",
			"data":   "delayed response",
		}, nil
	}))

	// 触发熔断
	fmt.Println("   触发熔断:")
	for i := 0; i < 3; i++ {
		breaker.Execute(func() (interface{}, error) {
			return nil, errors.New("service error")
		})
	}

	// 熔断后走自定义降级
	fmt.Println("   熔断后请求:")
	result, err := breaker.Execute(func() (interface{}, error) {
		return nil, errors.New("should not reach here")
	})
	fmt.Printf("   降级结果: %v\n", result)
	fmt.Printf("   错误: %v\n", err)
}

// fallbackComparisonDemo 降级策略对比演示
func fallbackComparisonDemo() {
	fmt.Println()
	fmt.Println("5. 降级策略对比")
	fmt.Println("   对比不同降级策略在并发场景下的表现")

	// 创建多个熔断器，每个使用不同的降级策略
	strategies := map[string]src.FallbackStrategy{
		"static":  src.NewStaticFallback("static fallback", nil),
		"cache":   func() src.FallbackStrategy { fb := src.NewCacheFallback(30 * time.Second); fb.SetCache("data", "cached"); return fb }(),
		"composite": func() src.FallbackStrategy {
			cache := src.NewCacheFallback(30 * time.Second)
			cache.SetCache("data", "cached")
			return src.NewCompositeFallback(cache, src.NewStaticFallback("default", nil))
		}(),
	}

	results := make(map[string]int)
	var mu sync.Mutex
	var wg sync.WaitGroup

	for name, fb := range strategies {
		breaker := src.NewCircuitBreaker(src.Config{
			FailureThreshold: 1,
			SuccessThreshold: 1,
			Timeout:          1 * time.Second,
		})
		breaker.SetFallback(fb)

		// 触发熔断
		breaker.Execute(func() (interface{}, error) {
			return nil, errors.New("error")
		})

		for i := 0; i < 10; i++ {
			wg.Add(1)
			go func() {
				defer wg.Done()
				_, err := breaker.Execute(func() (interface{}, error) {
					return nil, errors.New("should not reach")
				})
				mu.Lock()
				if err == nil {
					results[name]++
				}
				mu.Unlock()
			}()
		}
	}

	wg.Wait()

	fmt.Println("   降级成功次数（10次请求）:")
	for name, count := range results {
		fmt.Printf("   %-12s: %d/10\n", name, count)
	}
}

// fallbackWithRetryDemo 降级与重试组合演示
func fallbackWithRetryDemo() {
	fmt.Println()
	fmt.Println("6. 降级与重试组合演示")
	fmt.Println("   演示降级策略如何与重试机制配合")

	breaker := src.NewCircuitBreaker(src.Config{
		FailureThreshold: 3,
		SuccessThreshold: 2,
		Timeout:          1 * time.Second,
	})

	// 设置缓存降级
	cacheFB := src.NewCacheFallback(30 * time.Second)
	cacheFB.SetCache("product:1", map[string]interface{}{
		"id":    1,
		"name":  "降级商品",
		"price": 0.01,
	})
	breaker.SetFallback(cacheFB)

	// 重试器
	retryer := src.NewRetryer(src.RetryConfig{
		MaxRetries:      2,
		InitialInterval: 50 * time.Millisecond,
		MaxInterval:     200 * time.Millisecond,
		Multiplier:      2.0,
		Jitter:          false,
	})

	// 模拟商品查询
	fmt.Println("   查询商品（服务故障，走缓存降级）:")
	result := retryer.Execute(func() (interface{}, error) {
		return breaker.Execute(func() (interface{}, error) {
			return nil, errors.New("product service down")
		})
	})
	fmt.Printf("   结果: %v\n", result)
}
