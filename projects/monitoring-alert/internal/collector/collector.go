package collector

import (
	"context"
	"fmt"
	"math/rand"
	"sync"
	"time"

	"github.com/monitoring-alert/internal/model"
)

// Collector 指标采集器接口
type Collector interface {
	// Name 返回采集器名称
	Name() string
	// Start 启动采集
	Start(ctx context.Context) error
	// Stop 停止采集
	Stop() error
	// Collect 执行一次采集
	Collect() ([]*model.Metric, error)
}

// SystemCollector 系统指标采集器
type SystemCollector struct {
	mu       sync.RWMutex
	name     string
	interval time.Duration
	metrics  map[string]*model.Metric
	stopCh   chan struct{}
	running  bool
}

// NewSystemCollector 创建系统指标采集器
func NewSystemCollector(interval time.Duration) *SystemCollector {
	return &SystemCollector{
		name:     "system",
		interval: interval,
		metrics:  make(map[string]*model.Metric),
		stopCh:   make(chan struct{}),
	}
}

// Name 返回采集器名称
func (c *SystemCollector) Name() string {
	return c.name
}

// Start 启动采集
func (c *SystemCollector) Start(ctx context.Context) error {
	c.mu.Lock()
	if c.running {
		c.mu.Unlock()
		return fmt.Errorf("collector %s already running", c.name)
	}
	c.running = true
	c.mu.Unlock()

	go c.collectLoop(ctx)
	return nil
}

// Stop 停止采集
func (c *SystemCollector) Stop() error {
	c.mu.Lock()
	defer c.mu.Unlock()
	if !c.running {
		return nil
	}
	close(c.stopCh)
	c.running = false
	return nil
}

// collectLoop 采集循环
func (c *SystemCollector) collectLoop(ctx context.Context) {
	ticker := time.NewTicker(c.interval)
	defer ticker.Stop()

	for {
		select {
		case <-ctx.Done():
			return
		case <-c.stopCh:
			return
		case <-ticker.C:
			metrics, err := c.Collect()
			if err != nil {
				continue
			}
			c.mu.Lock()
			for _, m := range metrics {
				c.metrics[m.Name] = m
			}
			c.mu.Unlock()
		}
	}
}

// Collect 执行一次采集
func (c *SystemCollector) Collect() ([]*model.Metric, error) {
	metrics := make([]*model.Metric, 0)

	// CPU 使用率
	cpuMetric := model.NewMetric("cpu_usage", model.MetricTypeGauge, "CPU usage percentage").
		SetLabels(map[string]string{"host": "localhost"}).
		SetValue(c.simulateCPU())

	// 内存使用率
	memMetric := model.NewMetric("memory_usage", model.MetricTypeGauge, "Memory usage percentage").
		SetLabels(map[string]string{"host": "localhost"}).
		SetValue(c.simulateMemory())

	// 磁盘使用率
	diskMetric := model.NewMetric("disk_usage", model.MetricTypeGauge, "Disk usage percentage").
		SetLabels(map[string]string{"host": "localhost", "mount": "/"}).
		SetValue(c.simulateDisk())

	// 网络流量
	netInMetric := model.NewMetric("network_in", model.MetricTypeCounter, "Network bytes in").
		SetLabels(map[string]string{"host": "localhost", "interface": "eth0"}).
		SetValue(c.simulateNetworkIn())

	netOutMetric := model.NewMetric("network_out", model.MetricTypeCounter, "Network bytes out").
		SetLabels(map[string]string{"host": "localhost", "interface": "eth0"}).
		SetValue(c.simulateNetworkOut())

	metrics = append(metrics, cpuMetric, memMetric, diskMetric, netInMetric, netOutMetric)
	return metrics, nil
}

// simulateCPU 模拟 CPU 使用率
func (c *SystemCollector) simulateCPU() float64 {
	return 20.0 + rand.Float64()*60.0 // 20-80%
}

// simulateMemory 模拟内存使用率
func (c *SystemCollector) simulateMemory() float64 {
	return 40.0 + rand.Float64()*40.0 // 40-80%
}

// simulateDisk 模拟磁盘使用率
func (c *SystemCollector) simulateDisk() float64 {
	return 50.0 + rand.Float64()*30.0 // 50-80%
}

// simulateNetworkIn 模拟入站网络流量
func (c *SystemCollector) simulateNetworkIn() float64 {
	return 1000.0 + rand.Float64()*9000.0 // 1000-10000 bytes
}

// simulateNetworkOut 模拟出站网络流量
func (c *SystemCollector) simulateNetworkOut() float64 {
	return 500.0 + rand.Float64()*5000.0 // 500-5500 bytes
}

// GetMetrics 获取已采集的指标
func (c *SystemCollector) GetMetrics() map[string]*model.Metric {
	c.mu.RLock()
	defer c.mu.RUnlock()
	result := make(map[string]*model.Metric, len(c.metrics))
	for k, v := range c.metrics {
		result[k] = v
	}
	return result
}

// CustomCollector 自定义指标采集器
type CustomCollector struct {
	mu       sync.RWMutex
	name     string
	interval time.Duration
	collectFn func() ([]*model.Metric, error)
	metrics  map[string]*model.Metric
	stopCh   chan struct{}
	running  bool
}

// NewCustomCollector 创建自定义采集器
func NewCustomCollector(name string, interval time.Duration, collectFn func() ([]*model.Metric, error)) *CustomCollector {
	return &CustomCollector{
		name:      name,
		interval:  interval,
		collectFn: collectFn,
		metrics:   make(map[string]*model.Metric),
		stopCh:    make(chan struct{}),
	}
}

// Name 返回采集器名称
func (c *CustomCollector) Name() string {
	return c.name
}

// Start 启动采集
func (c *CustomCollector) Start(ctx context.Context) error {
	c.mu.Lock()
	if c.running {
		c.mu.Unlock()
		return fmt.Errorf("collector %s already running", c.name)
	}
	c.running = true
	c.mu.Unlock()

	go c.collectLoop(ctx)
	return nil
}

// Stop 停止采集
func (c *CustomCollector) Stop() error {
	c.mu.Lock()
	defer c.mu.Unlock()
	if !c.running {
		return nil
	}
	close(c.stopCh)
	c.running = false
	return nil
}

// collectLoop 采集循环
func (c *CustomCollector) collectLoop(ctx context.Context) {
	ticker := time.NewTicker(c.interval)
	defer ticker.Stop()

	for {
		select {
		case <-ctx.Done():
			return
		case <-c.stopCh:
			return
		case <-ticker.C:
			metrics, err := c.Collect()
			if err != nil {
				continue
			}
			c.mu.Lock()
			for _, m := range metrics {
				c.metrics[m.Name] = m
			}
			c.mu.Unlock()
		}
	}
}

// Collect 执行一次采集
func (c *CustomCollector) Collect() ([]*model.Metric, error) {
	if c.collectFn == nil {
		return nil, fmt.Errorf("collect function not set")
	}
	return c.collectFn()
}

// GetMetrics 获取已采集的指标
func (c *CustomCollector) GetMetrics() map[string]*model.Metric {
	c.mu.RLock()
	defer c.mu.RUnlock()
	result := make(map[string]*model.Metric, len(c.metrics))
	for k, v := range c.metrics {
		result[k] = v
	}
	return result
}

// CollectorManager 采集器管理器
type CollectorManager struct {
	mu         sync.RWMutex
	collectors map[string]Collector
	running    bool
	ctx        context.Context
	cancel     context.CancelFunc
}

// NewCollectorManager 创建采集器管理器
func NewCollectorManager() *CollectorManager {
	return &CollectorManager{
		collectors: make(map[string]Collector),
	}
}

// Register 注册采集器
func (m *CollectorManager) Register(c Collector) {
	m.mu.Lock()
	defer m.mu.Unlock()
	m.collectors[c.Name()] = c
}

// Unregister 注销采集器
func (m *CollectorManager) Unregister(name string) {
	m.mu.Lock()
	defer m.mu.Unlock()
	delete(m.collectors, name)
}

// Start 启动所有采集器
func (m *CollectorManager) Start(ctx context.Context) error {
	m.mu.Lock()
	if m.running {
		m.mu.Unlock()
		return fmt.Errorf("collector manager already running")
	}
	m.ctx, m.cancel = context.WithCancel(ctx)
	m.running = true
	m.mu.Unlock()

	m.mu.RLock()
	defer m.mu.RUnlock()
	for _, c := range m.collectors {
		if err := c.Start(m.ctx); err != nil {
			return err
		}
	}
	return nil
}

// Stop 停止所有采集器
func (m *CollectorManager) Stop() error {
	m.mu.Lock()
	defer m.mu.Unlock()
	if !m.running {
		return nil
	}
	m.cancel()
	for _, c := range m.collectors {
		if err := c.Stop(); err != nil {
			return err
		}
	}
	m.running = false
	return nil
}

// CollectAll 从所有采集器收集指标
func (m *CollectorManager) CollectAll() ([]*model.Metric, error) {
	m.mu.RLock()
	defer m.mu.RUnlock()

	var allMetrics []*model.Metric
	for _, c := range m.collectors {
		metrics, err := c.Collect()
		if err != nil {
			continue
		}
		allMetrics = append(allMetrics, metrics...)
	}
	return allMetrics, nil
}

// GetCollector 获取采集器
func (m *CollectorManager) GetCollector(name string) (Collector, bool) {
	m.mu.RLock()
	defer m.mu.RUnlock()
	c, ok := m.collectors[name]
	return c, ok
}

// ListCollectors 列出所有采集器
func (m *CollectorManager) ListCollectors() []string {
	m.mu.RLock()
	defer m.mu.RUnlock()
	names := make([]string, 0, len(m.collectors))
	for name := range m.collectors {
		names = append(names, name)
	}
	return names
}
