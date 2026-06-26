package main

import (
	"errors"
	"fmt"
	"math/rand"
	"time"

	"circuit-breaker/src"
)

// main 失败模拟演示主程序
//
// 演示熔断器如何从故障中恢复：
// 1. 服务正常 -> 熔断器关闭
// 2. 服务开始失败 -> 触发熔断
// 3. 熔断期间 -> 请求被拒绝
// 4. 超时后 -> 进入半开状态测试
// 5. 测试成功 -> 恢复关闭状态
// 6. 测试失败 -> 回到打开状态
func main() {
	fmt.Println("=== 熔断器故障模拟演示 ===")
	fmt.Println()

	// 配置：5次连续失败触发熔断，1秒后恢复半开，2次成功恢复关闭
	breaker := src.NewCircuitBreaker(src.Config{
		FailureThreshold: 5,
		SuccessThreshold: 2,
		Timeout:          1 * time.Second,
	})

	// 设置缓存降级策略
	cacheFB := src.NewCacheFallback(30 * time.Second)
	cacheFB.SetCache("fallback", map[string]interface{}{
		"source": "cache",
		"data":   "cached response",
	})
	breaker.SetFallback(src.NewCompositeFallback(cacheFB, src.NewStaticFallback("static fallback", nil)))

	// 模拟服务调用
	callCount := 0
	for i := 1; i <= 25; i++ {
		callCount++

		// 模拟服务状态变化：
		// 前5次：正常
		// 6-12次：持续失败（触发熔断）
		// 13-18次：恢复成功（半开测试）
		// 19-25次：继续正常
		serviceHealthy := true
		if callCount >= 6 && callCount <= 12 {
			serviceHealthy = false
		}

		result, err := breaker.Execute(func() (interface{}, error) {
			if !serviceHealthy {
				return nil, errors.New("service unavailable")
			}
			return map[string]interface{}{
				"call_id": callCount,
				"data":    fmt.Sprintf("response-%d", callCount),
			}, nil
		})

		state := breaker.GetState()
		metrics := breaker.GetMetrics()

		var outcome string
		if err != nil {
			outcome = fmt.Sprintf("REJECTED: %v", err)
		} else if result != nil {
			outcome = fmt.Sprintf("OK: %v", result)
		}

		fmt.Printf("[%02d] 状态=%-9s 成功=%3d 失败=%3d 失败率=%.1f%% | %s\n",
			i,
			state.String(),
			metrics.GetSuccessCount(),
			metrics.GetFailureCount(),
			metrics.GetFailureRate()*100,
			outcome,
		)

		// 模拟请求间隔
		time.Sleep(50 * time.Millisecond)
	}

	fmt.Println()
	fmt.Println("--- 最终状态 ---")
	fmt.Printf("状态: %v\n", breaker.GetState())
	fmt.Printf("总请求数: %d\n", breaker.GetMetrics().GetTotalRequests())
	fmt.Printf("成功: %d, 失败: %d\n", breaker.GetMetrics().GetSuccessCount(), breaker.GetMetrics().GetFailureCount())
}

// simulateFluctuatingFailure 模拟波动失败率
func simulateFluctuatingFailure() {
	fmt.Println()
	fmt.Println("=== 波动失败率模拟 ===")
	fmt.Println()

	breaker := src.NewCircuitBreaker(src.Config{
		FailureThreshold:     5,
		SuccessThreshold:     3,
		Timeout:              500 * time.Millisecond,
		FailureRateThreshold: 0.4,
		MinimumRequests:      10,
	})

	breaker.SetFallback(src.NewDefaultFallback("circuit open - service unavailable"))

	phase := 0
	for i := 1; i <= 60; i++ {
		// 模拟不同阶段的失败率
		var failProb float64
		switch {
		case i <= 15:
			failProb = 0.0 // 正常阶段
		case i <= 30:
			failProb = 0.6 // 故障阶段
		case i <= 45:
			failProb = 0.0 // 恢复阶段
		default:
			failProb = 0.1 // 轻微波动
		}

		// 每10个请求切换阶段
		if i%10 == 0 && phase < 4 {
			phase++
			fmt.Printf("\n--- 阶段 %d 开始 ---\n", phase)
		}

		result, err := breaker.Execute(func() (interface{}, error) {
			if rand.Float64() < failProb {
				return nil, errors.New("temporary failure")
			}
			return fmt.Sprintf("ok-%d", i), nil
		})

		state := breaker.GetState()
		if state == src.StateOpen {
			fmt.Printf("  [熔断] 请求 %d: 被拒绝\n", i)
		} else if err != nil {
			fmt.Printf("  [失败] 请求 %d: %v\n", i, err)
		} else {
			if i%10 == 1 || result == "ok-1" {
				fmt.Printf("  [成功] 请求 %d: %v\n", i, result)
			}
		}

		time.Sleep(20 * time.Millisecond)
	}

	fmt.Printf("\n最终状态: %v\n", breaker.GetState())
}
