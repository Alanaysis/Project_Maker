package test

import (
	"context"
	"testing"
	"time"

	"github.com/monitoring-alert/internal/collector"
	"github.com/monitoring-alert/internal/model"
	"github.com/stretchr/testify/assert"
)

func TestSystemCollectorCreation(t *testing.T) {
	c := collector.NewSystemCollector(5 * time.Second)
	assert.NotNil(t, c)
	assert.Equal(t, "system", c.Name())
}

func TestSystemCollectorCollect(t *testing.T) {
	c := collector.NewSystemCollector(5 * time.Second)

	metrics, err := c.Collect()
	assert.NoError(t, err)
	assert.NotNil(t, metrics)
	assert.Greater(t, len(metrics), 0)

	// 验证指标名称
	metricNames := make(map[string]bool)
	for _, m := range metrics {
		metricNames[m.Name] = true
	}

	assert.True(t, metricNames["cpu_usage"])
	assert.True(t, metricNames["memory_usage"])
	assert.True(t, metricNames["disk_usage"])
	assert.True(t, metricNames["network_in"])
	assert.True(t, metricNames["network_out"])
}

func TestSystemCollectorStartStop(t *testing.T) {
	c := collector.NewSystemCollector(100 * time.Millisecond)
	ctx := context.Background()

	// 启动
	err := c.Start(ctx)
	assert.NoError(t, err)

	// 重复启动应该失败
	err = c.Start(ctx)
	assert.Error(t, err)

	// 等待一段时间让采集器运行
	time.Sleep(200 * time.Millisecond)

	// 停止
	err = c.Stop()
	assert.NoError(t, err)
}

func TestCustomCollector(t *testing.T) {
	collectFn := func() ([]*model.Metric, error) {
		m := model.NewMetric("custom_metric", model.MetricTypeGauge, "Custom metric")
		m.SetValue(100.0)
		return []*model.Metric{m}, nil
	}

	c := collector.NewCustomCollector("custom", 5*time.Second, collectFn)
	assert.NotNil(t, c)
	assert.Equal(t, "custom", c.Name())

	metrics, err := c.Collect()
	assert.NoError(t, err)
	assert.Equal(t, 1, len(metrics))
	assert.Equal(t, "custom_metric", metrics[0].Name)
	assert.Equal(t, 100.0, metrics[0].GetValue())
}

func TestCustomCollectorStartStop(t *testing.T) {
	collectFn := func() ([]*model.Metric, error) {
		return []*model.Metric{}, nil
	}

	c := collector.NewCustomCollector("custom", 100*time.Millisecond, collectFn)
	ctx := context.Background()

	err := c.Start(ctx)
	assert.NoError(t, err)

	time.Sleep(200 * time.Millisecond)

	err = c.Stop()
	assert.NoError(t, err)
}

func TestCollectorManager(t *testing.T) {
	mgr := collector.NewCollectorManager()

	// 注册采集器
	c1 := collector.NewSystemCollector(5 * time.Second)
	mgr.Register(c1)

	collectFn := func() ([]*model.Metric, error) {
		return []*model.Metric{}, nil
	}
	c2 := collector.NewCustomCollector("custom", 5*time.Second, collectFn)
	mgr.Register(c2)

	// 列出采集器
	names := mgr.ListCollectors()
	assert.Equal(t, 2, len(names))
	assert.Contains(t, names, "system")
	assert.Contains(t, names, "custom")

	// 获取采集器
	_, ok := mgr.GetCollector("system")
	assert.True(t, ok)

	_, ok = mgr.GetCollector("nonexistent")
	assert.False(t, ok)
}

func TestCollectorManagerStartStop(t *testing.T) {
	mgr := collector.NewCollectorManager()

	c := collector.NewSystemCollector(100 * time.Second)
	mgr.Register(c)

	ctx := context.Background()

	err := mgr.Start(ctx)
	assert.NoError(t, err)

	// 重复启动应该失败
	err = mgr.Start(ctx)
	assert.Error(t, err)

	time.Sleep(100 * time.Millisecond)

	err = mgr.Stop()
	assert.NoError(t, err)
}

func TestCollectorManagerCollectAll(t *testing.T) {
	mgr := collector.NewCollectorManager()

	c := collector.NewSystemCollector(5 * time.Second)
	mgr.Register(c)

	metrics, err := mgr.CollectAll()
	assert.NoError(t, err)
	assert.Greater(t, len(metrics), 0)
}

func TestCollectorManagerUnregister(t *testing.T) {
	mgr := collector.NewCollectorManager()

	c := collector.NewSystemCollector(5 * time.Second)
	mgr.Register(c)

	names := mgr.ListCollectors()
	assert.Equal(t, 1, len(names))

	mgr.Unregister("system")

	names = mgr.ListCollectors()
	assert.Equal(t, 0, len(names))
}
