package tests

import (
    "errors"
    "testing"
    "time"

    "circuit-breaker/src"
)

func TestCircuitBreaker_ClosedState(t *testing.T) {
    cb := src.NewCircuitBreaker(src.Config{
        FailureThreshold: 5,
        SuccessThreshold: 3,
        Timeout:         30 * time.Second,
    })

    // 初始状态应该是关闭
    if cb.GetState() != src.StateClosed {
        t.Errorf("Expected initial state to be Closed, got %v", cb.GetState())
    }

    // 执行成功请求
    result, err := cb.Execute(func() (interface{}, error) {
        return "success", nil
    })

    if err != nil {
        t.Errorf("Expected no error, got %v", err)
    }
    if result != "success" {
        t.Errorf("Expected 'success', got %v", result)
    }

    // 状态应该保持关闭
    if cb.GetState() != src.StateClosed {
        t.Errorf("Expected state to be Closed, got %v", cb.GetState())
    }
}

func TestCircuitBreaker_FailureThreshold(t *testing.T) {
    cb := src.NewCircuitBreaker(src.Config{
        FailureThreshold: 3,
        SuccessThreshold: 2,
        Timeout:         1 * time.Second,
    })

    // 连续失败3次
    for i := 0; i < 3; i++ {
        _, _ = cb.Execute(func() (interface{}, error) {
            return nil, errors.New("test error")
        })
    }

    // 状态应该变为打开
    if cb.GetState() != src.StateOpen {
        t.Errorf("Expected state to be Open, got %v", cb.GetState())
    }

    // 打开状态下应该拒绝请求
    _, err := cb.Execute(func() (interface{}, error) {
        return "should not execute", nil
    })

    if err == nil {
        t.Error("Expected error when circuit breaker is open")
    }
}

func TestCircuitBreaker_TimeoutTransition(t *testing.T) {
    cb := src.NewCircuitBreaker(src.Config{
        FailureThreshold: 2,
        SuccessThreshold: 2,
        Timeout:         100 * time.Millisecond,
    })

    // 触发熔断
    for i := 0; i < 2; i++ {
        _, _ = cb.Execute(func() (interface{}, error) {
            return nil, errors.New("test error")
        })
    }

    if cb.GetState() != src.StateOpen {
        t.Errorf("Expected state to be Open, got %v", cb.GetState())
    }

    // 等待超时
    time.Sleep(150 * time.Millisecond)

    // 再次执行，应该进入半开状态
    _, _ = cb.Execute(func() (interface{}, error) {
        return "success", nil
    })

    if cb.GetState() != src.StateHalfOpen {
        t.Errorf("Expected state to be HalfOpen, got %v", cb.GetState())
    }
}

func TestCircuitBreaker_HalfOpenToClosed(t *testing.T) {
    cb := src.NewCircuitBreaker(src.Config{
        FailureThreshold: 2,
        SuccessThreshold: 2,
        Timeout:         100 * time.Millisecond,
    })

    // 触发熔断
    for i := 0; i < 2; i++ {
        _, _ = cb.Execute(func() (interface{}, error) {
            return nil, errors.New("test error")
        })
    }

    // 等待超时
    time.Sleep(150 * time.Millisecond)

    // 半开状态下连续成功2次
    for i := 0; i < 2; i++ {
        _, _ = cb.Execute(func() (interface{}, error) {
            return "success", nil
        })
    }

    // 状态应该恢复为关闭
    if cb.GetState() != src.StateClosed {
        t.Errorf("Expected state to be Closed, got %v", cb.GetState())
    }
}

func TestCircuitBreaker_HalfOpenToOpen(t *testing.T) {
    cb := src.NewCircuitBreaker(src.Config{
        FailureThreshold: 2,
        SuccessThreshold: 2,
        Timeout:         100 * time.Millisecond,
    })

    // 触发熔断
    for i := 0; i < 2; i++ {
        _, _ = cb.Execute(func() (interface{}, error) {
            return nil, errors.New("test error")
        })
    }

    // 等待超时
    time.Sleep(150 * time.Millisecond)

    // 半开状态下失败
    _, _ = cb.Execute(func() (interface{}, error) {
        return nil, errors.New("test error")
    })

    // 状态应该回到打开
    if cb.GetState() != src.StateOpen {
        t.Errorf("Expected state to be Open, got %v", cb.GetState())
    }
}

func TestCircuitBreaker_Fallback(t *testing.T) {
    cb := src.NewCircuitBreaker(src.Config{
        FailureThreshold: 2,
        SuccessThreshold: 2,
        Timeout:         1 * time.Second,
    })

    // 设置降级策略
    fallback := src.NewStaticFallback("fallback value", nil)
    cb.SetFallback(fallback)

    // 触发熔断
    for i := 0; i < 2; i++ {
        _, _ = cb.Execute(func() (interface{}, error) {
            return nil, errors.New("test error")
        })
    }

    // 执行请求，应该返回降级值
    result, err := cb.Execute(func() (interface{}, error) {
        return "should not execute", nil
    })

    if err != nil {
        t.Errorf("Expected no error, got %v", err)
    }
    if result != "fallback value" {
        t.Errorf("Expected 'fallback value', got %v", result)
    }
}

func TestCircuitBreaker_Reset(t *testing.T) {
    cb := src.NewCircuitBreaker(src.Config{
        FailureThreshold: 2,
        SuccessThreshold: 2,
        Timeout:         1 * time.Second,
    })

    // 触发熔断
    for i := 0; i < 2; i++ {
        _, _ = cb.Execute(func() (interface{}, error) {
            return nil, errors.New("test error")
        })
    }

    if cb.GetState() != src.StateOpen {
        t.Errorf("Expected state to be Open, got %v", cb.GetState())
    }

    // 重置熔断器
    cb.Reset()

    if cb.GetState() != src.StateClosed {
        t.Errorf("Expected state to be Closed, got %v", cb.GetState())
    }
}

func TestCircuitBreaker_FailureRate(t *testing.T) {
    cb := src.NewCircuitBreaker(src.Config{
        FailureThreshold:     100, // 高阈值，不会触发
        SuccessThreshold:     2,
        Timeout:             1 * time.Second,
        FailureRateThreshold: 0.5,
        MinimumRequests:      5,
    })

    // 发送10个请求，6个失败
    for i := 0; i < 4; i++ {
        _, _ = cb.Execute(func() (interface{}, error) {
            return "success", nil
        })
    }
    for i := 0; i < 6; i++ {
        _, _ = cb.Execute(func() (interface{}, error) {
            return nil, errors.New("test error")
        })
    }

    // 失败率60% > 50%，应该触发熔断
    if cb.GetState() != src.StateOpen {
        t.Errorf("Expected state to be Open, got %v", cb.GetState())
    }
}
