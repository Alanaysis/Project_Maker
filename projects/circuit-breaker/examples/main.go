package main

import (
	"errors"
	"fmt"
	"math/rand"
	"time"

	"circuit-breaker/src"
)

func main() {
	fmt.Println("=== 熔断降级完整示例 ===")
	fmt.Println()

	// 示例1: 基本使用
	basicExample()

	// 示例2: 带降级策略
	fallbackExample()

	// 示例3: 模拟真实场景
	simulateRealScenario()

	// 示例4: 限流器示例
	rateLimiterExample()

	// 示例5: 重试机制示例
	retryExample()

	// 示例6: API 网关示例
	runAPIGatewayExample()

	// 示例7: 微服务调用示例
	runMicroserviceExample()
}

func basicExample() {
    fmt.Println("1. 基本使用示例")
    fmt.Println("---")

    // 创建熔断器
    breaker := src.NewCircuitBreaker(src.Config{
        FailureThreshold: 3,
        SuccessThreshold: 2,
        Timeout:         2 * time.Second,
    })

    // 执行成功请求
    result, err := breaker.Execute(func() (interface{}, error) {
        return "Hello, World!", nil
    })

    if err != nil {
        fmt.Printf("请求失败: %v\n", err)
    } else {
        fmt.Printf("请求成功: %v\n", result)
    }

    fmt.Printf("当前状态: %v\n", breaker.GetState())
    fmt.Println()
}

func fallbackExample() {
    fmt.Println("2. 带降级策略示例")
    fmt.Println("---")

    // 创建熔断器
    breaker := src.NewCircuitBreaker(src.Config{
        FailureThreshold: 2,
        SuccessThreshold: 2,
        Timeout:         1 * time.Second,
    })

    // 设置降级策略
    fallback := src.NewStaticFallback("降级响应: 服务暂时不可用，请稍后重试", nil)
    breaker.SetFallback(fallback)

    // 模拟连续失败
    for i := 0; i < 3; i++ {
        result, err := breaker.Execute(func() (interface{}, error) {
            return nil, errors.New("服务调用失败")
        })

        fmt.Printf("请求 %d: ", i+1)
        if err != nil {
            fmt.Printf("错误: %v\n", err)
        } else {
            fmt.Printf("降级: %v\n", result)
        }
    }

    fmt.Printf("当前状态: %v\n", breaker.GetState())
    fmt.Println()
}

func simulateRealScenario() {
	fmt.Println("3. 模拟真实场景")
	fmt.Println("---")

	// 创建熔断器
	breaker := src.NewCircuitBreaker(src.Config{
		FailureThreshold:     5,
		SuccessThreshold:     3,
		Timeout:             5 * time.Second,
		FailureRateThreshold: 0.5,
		MinimumRequests:      10,
	})

	// 设置降级策略
	fallback := src.NewCacheFallback(30 * time.Second)
	fallback.SetCache("user:123", map[string]interface{}{
		"id":   123,
		"name": "缓存用户",
	})
	breaker.SetFallback(fallback)

	// 模拟100个请求
	successCount := 0
	failureCount := 0
	fallbackCount := 0

	for i := 0; i < 100; i++ {
		result, err := breaker.Execute(func() (interface{}, error) {
			// 模拟30%的失败率
			if rand.Float64() < 0.3 {
				return nil, errors.New("服务调用失败")
			}
			return fmt.Sprintf("用户数据 %d", i), nil
		})

		if err != nil {
			failureCount++
		} else if result != nil {
			if str, ok := result.(string); ok && str[:2] == "用户" {
				successCount++
			} else {
				fallbackCount++
			}
		}

		// 每10个请求打印一次状态
		if (i+1)%10 == 0 {
			fmt.Printf("请求 %d: 成功=%d, 失败=%d, 降级=%d, 状态=%v\n",
				i+1, successCount, failureCount, fallbackCount, breaker.GetState())
		}
	}

	fmt.Println()
	fmt.Printf("最终统计:\n")
	fmt.Printf("  成功请求: %d\n", successCount)
	fmt.Printf("  失败请求: %d\n", failureCount)
	fmt.Printf("  降级请求: %d\n", fallbackCount)
	fmt.Printf("  最终状态: %v\n", breaker.GetState())
	fmt.Printf("  失败率: %.2f%%\n", breaker.GetMetrics().GetFailureRate()*100)
}

func rateLimiterExample() {
	fmt.Println()
	fmt.Println("4. 限流器示例")
	fmt.Println("---")

	// 固定窗口限流器
	fmt.Println("  固定窗口限流器 (10请求/秒):")
	fw := src.NewFixedWindowLimiter(src.FixedWindowConfig{
		MaxRequests: 10,
		WindowSize:  1 * time.Second,
	})
	allowed, rejected := 0, 0
	for i := 0; i < 15; i++ {
		if fw.Allow() {
			allowed++
		} else {
			rejected++
		}
	}
	fmt.Printf("    发送15个请求: 允许=%d, 拒绝=%d\n", allowed, rejected)

	// 滑动窗口限流器
	fmt.Println("  滑动窗口限流器 (5请求/秒):")
	sw := src.NewSlidingWindowLimiter(src.SlidingWindowConfig{
		MaxRequests: 5,
		WindowSize:  1 * time.Second,
	})
	allowed, rejected = 0, 0
	for i := 0; i < 10; i++ {
		if sw.Allow() {
			allowed++
		} else {
			rejected++
		}
	}
	fmt.Printf("    发送10个请求: 允许=%d, 拒绝=%d\n", allowed, rejected)

	// 令牌桶限流器
	fmt.Println("  令牌桶限流器 (20请求/秒, 突发容量40):")
	tb := src.NewTokenBucketLimiter(src.TokenBucketConfig{
		Rate:  20,
		Burst: 40,
	})
	allowed, rejected = 0, 0
	for i := 0; i < 50; i++ {
		if tb.Allow() {
			allowed++
		} else {
			rejected++
		}
	}
	fmt.Printf("    发送50个请求: 允许=%d, 拒绝=%d, 剩余令牌=%d\n", allowed, rejected, tb.GetAvailable())
}

func retryExample() {
	fmt.Println()
	fmt.Println("5. 重试机制示例")
	fmt.Println("---")

	// 基本重试
	fmt.Println("  指数退避重试 (最多3次):")
	retryer := src.NewRetryer(src.RetryConfig{
		MaxRetries:      3,
		InitialInterval: 100 * time.Millisecond,
		MaxInterval:     2 * time.Second,
		Multiplier:      2.0,
		Jitter:          true,
	})

	attemptCount := 0
	result := retryer.Execute(func() (interface{}, error) {
		attemptCount++
		if attemptCount < 3 {
			return nil, fmt.Errorf("attempt %d failed", attemptCount)
		}
		return "success on attempt 3", nil
	})

	fmt.Printf("    结果: %v, 尝试次数: %d, 耗时: %v\n",
		result.Value, result.Attempts, result.TotalDuration)

	// 带熔断器的重试
	fmt.Println("  带熔断器的重试:")
	breaker := src.NewCircuitBreaker(src.Config{
		FailureThreshold: 3,
		SuccessThreshold: 2,
		Timeout:         2 * time.Second,
	})
	breaker.SetFallback(src.NewStaticFallback("fallback response", nil))

	rcb := src.NewRetryableCircuitBreaker(breaker, src.RetryConfig{
		MaxRetries:      2,
		InitialInterval: 50 * time.Millisecond,
		MaxInterval:     500 * time.Millisecond,
		Multiplier:      2.0,
		Jitter:          false,
	})

	failCount := 0
	res, err := rcb.Execute(func() (interface{}, error) {
		failCount++
		if failCount <= 2 {
			return nil, errors.New("service error")
		}
		return "recovered", nil
	})

	if err != nil {
		fmt.Printf("    最终失败: %v\n", err)
	} else {
		fmt.Printf("    最终成功: %v (第%d次尝试)\n", res, failCount)
	}
}
