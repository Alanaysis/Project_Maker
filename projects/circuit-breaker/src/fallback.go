package src

import (
    "errors"
    "time"
)

// FallbackFunc 降级函数类型
type FallbackFunc func() (interface{}, error)

// FallbackStrategy 降级策略接口
type FallbackStrategy interface {
    Execute() (interface{}, error)
}

// DefaultFallback 默认降级策略
type DefaultFallback struct {
    message string
}

// NewDefaultFallback 创建默认降级策略
func NewDefaultFallback(message string) *DefaultFallback {
    return &DefaultFallback{
        message: message,
    }
}

// Execute 执行降级策略
func (f *DefaultFallback) Execute() (interface{}, error) {
    return nil, errors.New(f.message)
}

// CacheFallback 缓存降级策略
type CacheFallback struct {
    cache     map[string]interface{}
    cacheTTL  time.Duration
    cacheTime time.Time
}

// NewCacheFallback 创建缓存降级策略
func NewCacheFallback(ttl time.Duration) *CacheFallback {
    return &CacheFallback{
        cache:    make(map[string]interface{}),
        cacheTTL: ttl,
    }
}

// SetCache 设置缓存
func (f *CacheFallback) SetCache(key string, value interface{}) {
    f.cache[key] = value
    f.cacheTime = time.Now()
}

// Execute 执行降级策略
func (f *CacheFallback) Execute() (interface{}, error) {
    if len(f.cache) == 0 {
        return nil, errors.New("no cached data available")
    }

    // 检查缓存是否过期
    if time.Since(f.cacheTime) > f.cacheTTL {
        return nil, errors.New("cached data expired")
    }

    // 返回第一个缓存值
    for _, v := range f.cache {
        return v, nil
    }

    return nil, errors.New("no cached data available")
}

// StaticFallback 静态降级策略
type StaticFallback struct {
    value interface{}
    err   error
}

// NewStaticFallback 创建静态降级策略
func NewStaticFallback(value interface{}, err error) *StaticFallback {
    return &StaticFallback{
        value: value,
        err:   err,
    }
}

// Execute 执行降级策略
func (f *StaticFallback) Execute() (interface{}, error) {
    return f.value, f.err
}

// CompositeFallback 组合降级策略
type CompositeFallback struct {
    strategies []FallbackStrategy
}

// NewCompositeFallback 创建组合降级策略
func NewCompositeFallback(strategies ...FallbackStrategy) *CompositeFallback {
    return &CompositeFallback{
        strategies: strategies,
    }
}

// Execute 执行降级策略
func (f *CompositeFallback) Execute() (interface{}, error) {
    for _, strategy := range f.strategies {
        result, err := strategy.Execute()
        if err == nil {
            return result, nil
        }
    }
    return nil, errors.New("all fallback strategies failed")
}
