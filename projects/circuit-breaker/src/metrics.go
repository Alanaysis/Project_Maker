package src

import (
    "sync"
    "time"
)

// Metrics 指标统计
type Metrics struct {
    mu              sync.RWMutex
    totalRequests   int64
    successCount    int64
    failureCount    int64
    lastFailureTime time.Time
    consecutiveSuccess int64
    consecutiveFailure int64
}

// NewMetrics 创建新的指标统计实例
func NewMetrics() *Metrics {
    return &Metrics{}
}

// RecordSuccess 记录成功请求
func (m *Metrics) RecordSuccess() {
    m.mu.Lock()
    defer m.mu.Unlock()

    m.totalRequests++
    m.successCount++
    m.consecutiveSuccess++
    m.consecutiveFailure = 0
}

// RecordFailure 记录失败请求
func (m *Metrics) RecordFailure() {
    m.mu.Lock()
    defer m.mu.Unlock()

    m.totalRequests++
    m.failureCount++
    m.consecutiveFailure++
    m.consecutiveSuccess = 0
    m.lastFailureTime = time.Now()
}

// GetFailureRate 获取失败率
func (m *Metrics) GetFailureRate() float64 {
    m.mu.RLock()
    defer m.mu.RUnlock()

    if m.totalRequests == 0 {
        return 0
    }
    return float64(m.failureCount) / float64(m.totalRequests)
}

// GetConsecutiveSuccess 获取连续成功次数
func (m *Metrics) GetConsecutiveSuccess() int64 {
    m.mu.RLock()
    defer m.mu.RUnlock()
    return m.consecutiveSuccess
}

// GetConsecutiveFailure 获取连续失败次数
func (m *Metrics) GetConsecutiveFailure() int64 {
    m.mu.RLock()
    defer m.mu.RUnlock()
    return m.consecutiveFailure
}

// GetTotalRequests 获取总请求数
func (m *Metrics) GetTotalRequests() int64 {
    m.mu.RLock()
    defer m.mu.RUnlock()
    return m.totalRequests
}

// GetSuccessCount 获取成功请求数
func (m *Metrics) GetSuccessCount() int64 {
    m.mu.RLock()
    defer m.mu.RUnlock()
    return m.successCount
}

// GetFailureCount 获取失败请求数
func (m *Metrics) GetFailureCount() int64 {
    m.mu.RLock()
    defer m.mu.RUnlock()
    return m.failureCount
}

// GetLastFailureTime 获取最后失败时间
func (m *Metrics) GetLastFailureTime() time.Time {
    m.mu.RLock()
    defer m.mu.RUnlock()
    return m.lastFailureTime
}

// Reset 重置指标
func (m *Metrics) Reset() {
    m.mu.Lock()
    defer m.mu.Unlock()

    m.totalRequests = 0
    m.successCount = 0
    m.failureCount = 0
    m.consecutiveSuccess = 0
    m.consecutiveFailure = 0
    m.lastFailureTime = time.Time{}
}
