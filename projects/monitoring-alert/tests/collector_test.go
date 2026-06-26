package tests_test

import (
	"context"
	"math/rand"
	"testing"
	"time"

	"github.com/monitoring-alert/internal/collector"
	"github.com/monitoring-alert/internal/model"
)

// TestSystemCollectorCollect 测试系统采集器采集
func TestSystemCollectorCollect(t *testing.T) {
	c := collector.NewSystemCollector(1 * time.Second)

	metrics, err := c.Collect()
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}

	if len(metrics) != 5 {
		t.Errorf("expected 5 metrics, got %d", len(metrics))
	}

	// 验证每个指标都有值
	for _, m := range metrics {
		if m.GetValue() <= 0 {
			t.Errorf("metric %s has non-positive value: %f", m.Name, m.GetValue())
		}
	}
}

// TestSystemCollectorName 测试采集器名称
func TestSystemCollectorName(t *testing.T) {
	c := collector.NewSystemCollector(1 * time.Second)
	if c.Name() != "system" {
		t.Errorf("expected name 'system', got '%s'", c.Name())
	}
}

// TestSystemCollectorStartStop 测试启动/停止
func TestSystemCollectorStartStop(t *testing.T) {
	c := collector.NewSystemCollector(100 * time.Millisecond)

	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()

	err := c.Start(ctx)
	if err != nil {
		t.Fatalf("unexpected start error: %v", err)
	}

	// 等待采集
	time.Sleep(250 * time.Millisecond)

	metrics := c.GetMetrics()
	if len(metrics) == 0 {
		t.Error("expected some collected metrics")
	}

	err = c.Stop()
	if err != nil {
		t.Fatalf("unexpected stop error: %v", err)
	}
}

// TestSystemCollectorDoubleStart 测试重复启动
func TestSystemCollectorDoubleStart(t *testing.T) {
	c := collector.NewSystemCollector(1 * time.Second)

	ctx := context.Background()
	err := c.Start(ctx)
	if err != nil {
		t.Fatalf("first start error: %v", err)
	}

	err = c.Start(ctx)
	if err == nil {
		t.Error("expected error on double start")
	}

	c.Stop()
}

// TestCustomCollector 测试自定义采集器
func TestCustomCollector(t *testing.T) {
	collectFn := func() ([]*model.Metric, error) {
		m := model.NewMetric("custom_metric", model.MetricTypeGauge, "Custom").
			SetValue(42.0)
		return []*model.Metric{m}, nil
	}

	c := collector.NewCustomCollector("custom", 1*time.Second, collectFn)

	metrics, err := c.Collect()
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}

	if len(metrics) != 1 {
		t.Errorf("expected 1 metric, got %d", len(metrics))
	}
	if metrics[0].Name != "custom_metric" {
		t.Errorf("expected metric name 'custom_metric', got '%s'", metrics[0].Name)
	}
}

// TestCustomCollectorNilFunction 测试空采集函数
func TestCustomCollectorNilFunction(t *testing.T) {
	c := collector.NewCustomCollector("custom", 1*time.Second, nil)

	_, err := c.Collect()
	if err == nil {
		t.Error("expected error for nil collect function")
	}
}

// TestCollectorManager 测试采集器管理器
func TestCollectorManager(t *testing.T) {
	manager := collector.NewCollectorManager()

	sysC := collector.NewSystemCollector(1 * time.Second)
	customC := collector.NewCustomCollector("custom", 1*time.Second, func() ([]*model.Metric, error) {
		return []*model.Metric{model.NewMetric("test", model.MetricTypeGauge, "test").SetValue(1.0)}, nil
	})

	manager.Register(sysC)
	manager.Register(customC)

	names := manager.ListCollectors()
	if len(names) != 2 {
		t.Errorf("expected 2 collectors, got %d", len(names))
	}

	// 测试获取采集器
	_, ok := manager.GetCollector("system")
	if !ok {
		t.Error("expected to find 'system' collector")
	}

	// 测试 CollectAll
	metrics, err := manager.CollectAll()
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if len(metrics) != 6 { // 5 system + 1 custom
		t.Errorf("expected 6 metrics, got %d", len(metrics))
	}

	// 测试注销
	manager.Unregister("system")
	names = manager.ListCollectors()
	if len(names) != 1 {
		t.Errorf("expected 1 collector after unregister, got %d", len(names))
	}
}

// TestCollectorManagerStartStop 测试管理器启动/停止
func TestCollectorManagerStartStop(t *testing.T) {
	manager := collector.NewCollectorManager()

	c := collector.NewSystemCollector(100 * time.Millisecond)
	manager.Register(c)

	ctx := context.Background()
	err := manager.Start(ctx)
	if err != nil {
		t.Fatalf("unexpected start error: %v", err)
	}

	time.Sleep(250 * time.Millisecond)
	err = manager.Stop()
	if err != nil {
		t.Fatalf("unexpected stop error: %v", err)
	}
}

// TestCollectorMetricTypes 测试不同指标类型
func TestCollectorMetricTypes(t *testing.T) {
	collectFn := func() ([]*model.Metric, error) {
		return []*model.Metric{
			model.NewMetric("counter_test", model.MetricTypeCounter, "Counter").SetValue(100),
			model.NewMetric("gauge_test", model.MetricTypeGauge, "Gauge").SetValue(50),
			model.NewMetric("histogram_test", model.MetricTypeHistogram, "Histogram").SetValue(75),
		}, nil
	}

	c := collector.NewCustomCollector("types", 1*time.Second, collectFn)
	metrics, _ := c.Collect()

	expectedTypes := []model.MetricType{
		model.MetricTypeCounter,
		model.MetricTypeGauge,
		model.MetricTypeHistogram,
	}

	for i, m := range metrics {
		if m.Type != expectedTypes[i] {
			t.Errorf("metric %s: expected type %v, got %v", m.Name, expectedTypes[i], m.Type)
		}
	}
}

// TestCollectorConcurrentCollect 测试并发采集
func TestCollectorConcurrentCollect(t *testing.T) {
	collectFn := func() ([]*model.Metric, error) {
		return []*model.Metric{
			model.NewMetric("concurrent_test", model.MetricTypeGauge, "test").
				SetValue(rand.Float64() * 100),
		}, nil
	}

	c := collector.NewCustomCollector("concurrent", 1*time.Second, collectFn)

	done := make(chan bool, 10)
	for i := 0; i < 10; i++ {
		go func() {
			_, err := c.Collect()
			if err != nil {
				t.Errorf("collect error: %v", err)
			}
			done <- true
		}()
	}

	for i := 0; i < 10; i++ {
		<-done
	}
}

// TestCollectorGetMetrics 测试获取已采集指标
func TestCollectorGetMetrics(t *testing.T) {
	collectFn := func() ([]*model.Metric, error) {
		return []*model.Metric{
			model.NewMetric("get_test", model.MetricTypeGauge, "test").SetValue(42),
		}, nil
	}

	c := collector.NewCustomCollector("get_test", 1*time.Second, collectFn)
	metrics, _ := c.Collect()

	if len(metrics) != 1 {
		t.Errorf("expected 1 metric, got %d", len(metrics))
	}
	if metrics[0].Name != "get_test" {
		t.Errorf("expected metric name 'get_test', got '%s'", metrics[0].Name)
	}
	if metrics[0].GetValue() != 42 {
		t.Errorf("expected value 42, got %f", metrics[0].GetValue())
	}
}
