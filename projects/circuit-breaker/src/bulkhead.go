package src

import (
	"errors"
	"sync"
	"sync/atomic"
	"time"
)

// ============================================================
// 舱壁模式 (Bulkhead Pattern)
// ============================================================
//
// 舱壁模式是熔断器的补充模式。熔断器关注失败率，舱壁模式关注资源隔离。
//
// 核心思想：
// - 将资源（goroutine/连接/线程）划分为多个隔离的"舱壁"
// - 每个舱壁有独立的资源配额
// - 一个舱壁耗尽不会影响其他舱壁
// - 防止级联故障扩散到所有资源
//
// 类比：船舶的水密舱壁，一个舱进水不会导致整艘船沉没

// BulkheadConfig 舱壁配置
type BulkheadConfig struct {
	// MaxConcurrency 最大并发数
	MaxConcurrency int
	// MaxWaiters 最大等待队列长度
	MaxWaiters int
	// WaitTimeout 等待超时时间
	WaitTimeout int64 // 纳秒
}

// DefaultBulkheadConfig 返回默认舱壁配置
func DefaultBulkheadConfig() BulkheadConfig {
	return BulkheadConfig{
		MaxConcurrency: 10,
		MaxWaiters:     20,
		WaitTimeout:    5_000_000_000, // 5秒
	}
}

// Bulkhead 舱壁（资源隔离器）
//
// 实现方式：
// 1. 信号量控制并发数
// 2. 等待队列管理超额请求
// 3. 超时机制防止无限等待
type Bulkhead struct {
	mu          sync.Mutex
	remaining   int           // 剩余可用配额
	max         int           // 最大配额
	waiters     int64         // 当前等待数
	maxWaiters  int           // 最大等待数
	cond        *sync.Cond    // 等待队列条件变量
	sem         chan struct{} // 信号量
	closed      bool          // 是否已关闭
}

// NewBulkhead 创建新的舱壁
func NewBulkhead(config BulkheadConfig) *Bulkhead {
	b := &Bulkhead{
		remaining:  config.MaxConcurrency,
		max:        config.MaxConcurrency,
		maxWaiters: config.MaxWaiters,
		sem:        make(chan struct{}, config.MaxConcurrency),
	}
	b.cond = sync.NewCond(&b.mu)
	return b
}

// TryAcquire 尝试获取许可（不等待）
// 返回是否成功获取
func (b *Bulkhead) TryAcquire() bool {
	b.mu.Lock()
	defer b.mu.Unlock()

	if b.closed {
		return false
	}

	if b.remaining > 0 {
		b.remaining--
		return true
	}

	return false
}

// Acquire 获取许可（可等待）
// 如果超过最大等待数或超时，返回错误
func (b *Bulkhead) Acquire() error {
	b.mu.Lock()
	defer b.mu.Unlock()

	if b.closed {
		return errors.New("bulkhead is closed")
	}

	// 检查是否超过最大等待数
	if b.waiters >= int64(b.maxWaiters) {
		return errors.New("bulkhead waiters exhausted")
	}

	// 有可用配额直接获取
	if b.remaining > 0 {
		b.remaining--
		return nil
	}

	// 进入等待队列
	b.waiters++

	// 等待配额释放（使用条件变量）
	// 注意：sync.Cond.Wait 没有内置超时，这里简化为无限等待
	// 实际生产环境应结合 context.WithTimeout 使用
	for b.remaining <= 0 && !b.closed {
		b.cond.Wait()
	}

	if b.closed {
		b.waiters--
		return errors.New("bulkhead is closed")
	}

	b.remaining--
	return nil
}

// Release 释放一个许可
func (b *Bulkhead) Release() {
	b.mu.Lock()
	defer b.mu.Unlock()

	if b.closed {
		return
	}

	b.remaining++
	b.cond.Signal() // 唤醒一个等待者
}

// Close 关闭舱壁（拒绝新请求）
func (b *Bulkhead) Close() {
	b.mu.Lock()
	defer b.mu.Unlock()

	b.closed = true
	b.cond.Broadcast() // 唤醒所有等待者
}

// GetStats 获取舱壁统计信息
func (b *Bulkhead) GetStats() map[string]interface{} {
	b.mu.Lock()
	defer b.mu.Unlock()

	return map[string]interface{}{
		"remaining": b.remaining,
		"max":       b.max,
		"waiters":   b.waiters,
		"utilization": float64(b.max-b.remaining) / float64(b.max),
	}
}

// ============================================================
// 舱壁池 - 为不同服务/资源创建独立的舱壁
// ============================================================

// BulkheadPool 舱壁池
//
// 为不同的服务或资源组提供独立的舱壁隔离
// 例如：用户服务、订单服务、支付服务各有独立的并发限制
type BulkheadPool struct {
	mu       sync.RWMutex
	bulkheads map[string]*Bulkhead
	config   BulkheadConfig
}

// NewBulkheadPool 创建舱壁池
func NewBulkheadPool(config BulkheadConfig) *BulkheadPool {
	return &BulkheadPool{
		bulkheads: make(map[string]*Bulkhead),
		config:    config,
	}
}

// GetOrCreate 获取或创建指定名称的舱壁
func (p *BulkheadPool) GetOrCreate(name string) *Bulkhead {
	p.mu.RLock()
	if bh, exists := p.bulkheads[name]; exists {
		p.mu.RUnlock()
		return bh
	}
	p.mu.RUnlock()

	// 双重检查锁定
	p.mu.Lock()
	defer p.mu.Unlock()

	if bh, exists := p.bulkheads[name]; exists {
		return bh
	}

	bh := NewBulkhead(p.config)
	p.bulkheads[name] = bh
	return bh
}

// Get 获取指定名称的舱壁
func (p *BulkheadPool) Get(name string) (*Bulkhead, bool) {
	p.mu.RLock()
	defer p.mu.RUnlock()
	bh, exists := p.bulkheads[name]
	return bh, exists
}

// Remove 移除指定名称的舱壁
func (p *BulkheadPool) Remove(name string) {
	p.mu.Lock()
	defer p.mu.Unlock()

	if bh, exists := p.bulkheads[name]; exists {
		bh.Close()
		delete(p.bulkheads, name)
	}
}

// GetAllStats 获取所有舱壁的统计信息
func (p *BulkheadPool) GetAllStats() map[string]map[string]interface{} {
	p.mu.RLock()
	defer p.mu.RUnlock()

	stats := make(map[string]map[string]interface{})
	for name, bh := range p.bulkheads {
		stats[name] = bh.GetStats().(map[string]interface{})
	}
	return stats
}

// ============================================================
// 带舱壁的熔断器
// ============================================================

// BulkheadCircuitBreaker 带舱壁的熔断器
//
// 组合舱壁模式和熔断器模式：
// 1. 先通过舱壁检查（资源隔离）
// 2. 再通过熔断器检查（故障隔离）
// 3. 两者都通过才执行请求
type BulkheadCircuitBreaker struct {
	bulkhead *Bulkhead
	breaker  *CircuitBreaker
}

// NewBulkheadCircuitBreaker 创建带舱壁的熔断器
func NewBulkheadCircuitBreaker(breaker *CircuitBreaker, bulkhead *Bulkhead) *BulkheadCircuitBreaker {
	return &BulkheadCircuitBreaker{
		breaker:  breaker,
		bulkhead: bulkhead,
	}
}

// Execute 执行请求（先舱壁检查，再熔断器检查）
func (bcb *BulkheadCircuitBreaker) Execute(request func() (interface{}, error)) (interface{}, error) {
	// 1. 舱壁检查
	if !bcb.bulkhead.TryAcquire() {
		return nil, errors.New("bulkhead full: resource exhausted")
	}
	defer bcb.bulkhead.Release()

	// 2. 熔断器检查 + 执行
	return bcb.breaker.Execute(request)
}

// GetBulkheadStats 获取舱壁统计
func (bcb *BulkheadCircuitBreaker) GetBulkheadStats() map[string]interface{} {
	return bcb.bulkhead.GetStats().(map[string]interface{})
}

// GetBreakerStats 获取熔断器统计
func (bcb *BulkheadCircuitBreaker) GetBreakerStats() map[string]interface{} {
	return map[string]interface{}{
		"state":      bcb.breaker.GetState().String(),
		"total":      bcb.breaker.GetMetrics().GetTotalRequests(),
		"success":    bcb.breaker.GetMetrics().GetSuccessCount(),
		"failure":    bcb.breaker.GetMetrics().GetFailureCount(),
		"failure_rate": bcb.breaker.GetMetrics().GetFailureRate(),
	}
}
