package main

import (
	"errors"
	"fmt"
	"math/rand"
	"sync"
	"time"

	"circuit-breaker/src"
)

// ============================================================
// APIGateway 模拟 API 网关
// ============================================================

// ServiceEndpoint 服务端点
type ServiceEndpoint struct {
	Name     string
	Breaker  *src.CircuitBreaker
	Limiter  src.RateLimiter
	Retryer  *src.Retryer
}

// NewServiceEndpoint 创建服务端点
func NewServiceEndpoint(name string, failureThreshold int64, rateLimit int64) *ServiceEndpoint {
	breaker := src.NewCircuitBreaker(src.Config{
		FailureThreshold:     failureThreshold,
		SuccessThreshold:     3,
		Timeout:             5 * time.Second,
		FailureRateThreshold: 0.5,
		MinimumRequests:      10,
	})

	// 设置缓存降级
	fallback := src.NewCompositeFallback(
		src.NewCacheFallback(30*time.Second),
		src.NewStaticFallback(
			map[string]interface{}{"error": "service temporarily unavailable", "service": name},
			nil,
		),
	)
	breaker.SetFallback(fallback)

	limiter := src.NewTokenBucketLimiter(src.TokenBucketConfig{
		Rate:  float64(rateLimit),
		Burst: rateLimit * 2,
	})

	retryer := src.NewRetryer(src.RetryConfig{
		MaxRetries:      2,
		InitialInterval: 100 * time.Millisecond,
		MaxInterval:     1 * time.Second,
		Multiplier:      2.0,
		Jitter:          true,
	})

	return &ServiceEndpoint{
		Name:    name,
		Breaker: breaker,
		Limiter: limiter,
		Retryer: retryer,
	}
}

// HandleRequest 处理请求
func (ep *ServiceEndpoint) HandleRequest(requestID string, handler func() (interface{}, error)) (interface{}, error) {
	// 1. 限流检查
	if !ep.Limiter.Allow() {
		return nil, fmt.Errorf("[%s] rate limited for request %s", ep.Name, requestID)
	}

	// 2. 带重试的熔断器调用
	result := ep.Retryer.Execute(func() (interface{}, error) {
		return ep.Breaker.Execute(handler)
	})

	return result.Value, result.Err
}

// GetStatus 获取端点状态
func (ep *ServiceEndpoint) GetStatus() map[string]interface{} {
	return map[string]interface{}{
		"name":       ep.Name,
		"state":      ep.Breaker.GetState().String(),
		"available":  ep.Limiter.GetAvailable(),
		"failures":   ep.Breaker.GetMetrics().GetFailureCount(),
		"successes":  ep.Breaker.GetMetrics().GetSuccessCount(),
	}
}

// ============================================================
// APIGateway API 网关
// ============================================================

// APIGateway API 网关
type APIGateway struct {
	endpoints map[string]*ServiceEndpoint
	mu        sync.RWMutex
}

// NewAPIGateway 创建 API 网关
func NewAPIGateway() *APIGateway {
	return &APIGateway{
		endpoints: make(map[string]*ServiceEndpoint),
	}
}

// RegisterEndpoint 注册服务端点
func (gw *APIGateway) RegisterEndpoint(name string, endpoint *ServiceEndpoint) {
	gw.mu.Lock()
	defer gw.mu.Unlock()
	gw.endpoints[name] = endpoint
}

// Route 路由请求到对应服务
func (gw *APIGateway) Route(serviceName string, requestID string, handler func() (interface{}, error)) (interface{}, error) {
	gw.mu.RLock()
	endpoint, exists := gw.endpoints[serviceName]
	gw.mu.RUnlock()

	if !exists {
		return nil, fmt.Errorf("service %s not found", serviceName)
	}

	return endpoint.HandleRequest(requestID, handler)
}

// GetStatus 获取所有端点状态
func (gw *APIGateway) GetStatus() map[string]map[string]interface{} {
	gw.mu.RLock()
	defer gw.mu.RUnlock()

	status := make(map[string]map[string]interface{})
	for name, endpoint := range gw.endpoints {
		status[name] = endpoint.GetStatus()
	}
	return status
}

// ============================================================
// 示例运行
// ============================================================

func runAPIGatewayExample() {
	fmt.Println("========================================")
	fmt.Println("  API 网关熔断降级示例")
	fmt.Println("========================================")
	fmt.Println()

	// 创建 API 网关
	gateway := NewAPIGateway()

	// 注册服务端点
	userService := NewServiceEndpoint("user-service", 3, 50)
	orderService := NewServiceEndpoint("order-service", 5, 30)
	paymentService := NewServiceEndpoint("payment-service", 2, 20)

	gateway.RegisterEndpoint("users", userService)
	gateway.RegisterEndpoint("orders", orderService)
	gateway.RegisterEndpoint("payments", paymentService)

	// 模拟服务调用
	var wg sync.WaitGroup
	requestID := 0

	// 模拟用户服务（30%失败率）
	for i := 0; i < 50; i++ {
		wg.Add(1)
		requestID++
		go func(id int) {
			defer wg.Done()
			_, err := gateway.Route("users", fmt.Sprintf("req-%d", id), func() (interface{}, error) {
				if rand.Float64() < 0.3 {
					return nil, errors.New("user service error")
				}
				return map[string]interface{}{"user_id": id, "name": "test_user"}, nil
			})
			if err != nil {
				// 静默处理错误
			}
		}(requestID)
		time.Sleep(10 * time.Millisecond)
	}

	// 模拟支付服务（50%失败率）
	for i := 0; i < 30; i++ {
		wg.Add(1)
		requestID++
		go func(id int) {
			defer wg.Done()
			_, err := gateway.Route("payments", fmt.Sprintf("req-%d", id), func() (interface{}, error) {
				if rand.Float64() < 0.5 {
					return nil, errors.New("payment service error")
				}
				return map[string]interface{}{"payment_id": id, "status": "success"}, nil
			})
			if err != nil {
				// 静默处理错误
			}
		}(requestID)
		time.Sleep(15 * time.Millisecond)
	}

	wg.Wait()

	// 打印状态
	fmt.Println("\n--- 服务状态 ---")
	status := gateway.GetStatus()
	for name, s := range status {
		fmt.Printf("  %s: 状态=%v, 可用配额=%v, 成功=%v, 失败=%v\n",
			name, s["state"], s["available"], s["successes"], s["failures"])
	}
}

func runMicroserviceExample() {
	fmt.Println()
	fmt.Println("========================================")
	fmt.Println("  微服务调用熔断降级示例")
	fmt.Println("========================================")
	fmt.Println()

	// 创建带重试的熔断器
	breaker := src.NewCircuitBreaker(src.Config{
		FailureThreshold:     3,
		SuccessThreshold:     2,
		Timeout:             2 * time.Second,
		FailureRateThreshold: 0.5,
		MinimumRequests:      5,
	})

	// 设置复合降级策略
	cacheFallback := src.NewCacheFallback(60 * time.Second)
	cacheFallback.SetCache("product:1001", map[string]interface{}{
		"id":    1001,
		"name":  "缓存商品",
		"price": 99.99,
	})

	fallback := src.NewCompositeFallback(
		cacheFallback,
		src.NewStaticFallback(
			map[string]interface{}{"error": "service unavailable", "retry_after": "30s"},
			nil,
		),
	)
	breaker.SetFallback(fallback)

	// 创建重试器
	retryer := src.NewRetryer(src.RetryConfig{
		MaxRetries:      3,
		InitialInterval: 200 * time.Millisecond,
		MaxInterval:     2 * time.Second,
		Multiplier:      2.0,
		Jitter:          true,
	})

	// 模拟商品服务调用
	fmt.Println("--- 模拟商品服务调用 ---")

	successCount := 0
	fallbackCount := 0
	errorCount := 0

	for i := 0; i < 30; i++ {
		productID := 1001 + i%5

		result := retryer.Execute(func() (interface{}, error) {
			return breaker.Execute(func() (interface{}, error) {
				// 模拟40%失败率
				if rand.Float64() < 0.4 {
					return nil, errors.New("product service timeout")
				}
				return map[string]interface{}{
					"id":    productID,
					"name":  fmt.Sprintf("商品-%d", productID),
					"price": float64(50 + rand.Intn(200)),
				}, nil
			})
		})

		if result.Err != nil {
			errorCount++
		} else if result.Value != nil {
			if m, ok := result.Value.(map[string]interface{}); ok {
				if _, hasError := m["error"]; hasError {
					fallbackCount++
				} else {
					successCount++
				}
			}
		}

		if (i+1)%10 == 0 {
			fmt.Printf("  请求 %d: 成功=%d, 降级=%d, 失败=%d, 状态=%v\n",
				i+1, successCount, fallbackCount, errorCount, breaker.GetState())
		}

		time.Sleep(50 * time.Millisecond)
	}

	fmt.Println()
	fmt.Printf("最终结果: 成功=%d, 降级=%d, 失败=%d\n", successCount, fallbackCount, errorCount)
	fmt.Printf("熔断器状态: %v\n", breaker.GetState())
}
