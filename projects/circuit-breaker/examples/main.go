package main

import (
    "errors"
    "fmt"
    "math/rand"
    "time"

    "circuit-breaker/src"
)

func main() {
    fmt.Println("=== 熔断器模式示例 ===")
    fmt.Println()

    // 示例1: 基本使用
    basicExample()

    // 示例2: 带降级策略
    fallbackExample()

    // 示例3: 模拟真实场景
    simulateRealScenario()
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
