package test

import (
	"testing"
	"time"

	"github.com/monitoring-alert/internal/model"
	"github.com/monitoring-alert/internal/storage"
	"github.com/stretchr/testify/assert"
)

func TestMemoryTSDBCreation(t *testing.T) {
	db := storage.NewMemoryTSDB(24 * time.Hour)
	assert.NotNil(t, db)
	assert.Equal(t, 0, db.GetSeriesCount())
	assert.Equal(t, 0, db.GetPointCount())
}

func TestMemoryTSDBWrite(t *testing.T) {
	db := storage.NewMemoryTSDB(24 * time.Hour)

	m := model.NewMetric("cpu_usage", model.MetricTypeGauge, "CPU usage")
	m.SetLabels(map[string]string{"host": "localhost"})
	m.SetValue(75.5)

	err := db.Write(m)
	assert.NoError(t, err)

	assert.Equal(t, 1, db.GetSeriesCount())
	assert.Equal(t, 1, db.GetPointCount())
}

func TestMemoryTSDBWriteMultiple(t *testing.T) {
	db := storage.NewMemoryTSDB(24 * time.Hour)

	// 写入同一指标的多个数据点
	for i := 0; i < 10; i++ {
		m := model.NewMetric("cpu_usage", model.MetricTypeGauge, "CPU usage")
		m.SetLabels(map[string]string{"host": "localhost"})
		m.SetValue(float64(i * 10))

		err := db.Write(m)
		assert.NoError(t, err)
	}

	assert.Equal(t, 1, db.GetSeriesCount())
	assert.Equal(t, 10, db.GetPointCount())
}

func TestMemoryTSDBWriteDifferentMetrics(t *testing.T) {
	db := storage.NewMemoryTSDB(24 * time.Hour)

	// 写入不同的指标
	m1 := model.NewMetric("cpu_usage", model.MetricTypeGauge, "CPU usage")
	m1.SetLabels(map[string]string{"host": "localhost"})
	m1.SetValue(75.5)

	m2 := model.NewMetric("memory_usage", model.MetricTypeGauge, "Memory usage")
	m2.SetLabels(map[string]string{"host": "localhost"})
	m2.SetValue(60.0)

	err := db.Write(m1)
	assert.NoError(t, err)

	err = db.Write(m2)
	assert.NoError(t, err)

	assert.Equal(t, 2, db.GetSeriesCount())
}

func TestMemoryTSDBWriteDifferentLabels(t *testing.T) {
	db := storage.NewMemoryTSDB(24 * time.Hour)

	// 写入不同标签的同一指标
	m1 := model.NewMetric("cpu_usage", model.MetricTypeGauge, "CPU usage")
	m1.SetLabels(map[string]string{"host": "host1"})
	m1.SetValue(75.5)

	m2 := model.NewMetric("cpu_usage", model.MetricTypeGauge, "CPU usage")
	m2.SetLabels(map[string]string{"host": "host2"})
	m2.SetValue(80.0)

	err := db.Write(m1)
	assert.NoError(t, err)

	err = db.Write(m2)
	assert.NoError(t, err)

	assert.Equal(t, 2, db.GetSeriesCount())
}

func TestMemoryTSDBRead(t *testing.T) {
	db := storage.NewMemoryTSDB(24 * time.Hour)

	// 写入数据
	now := time.Now()
	for i := 0; i < 10; i++ {
		m := model.NewMetric("cpu_usage", model.MetricTypeGauge, "CPU usage")
		m.SetLabels(map[string]string{"host": "localhost"})
		m.SetValue(float64(i * 10))
		m.Timestamp = now.Add(time.Duration(i) * time.Minute)

		err := db.Write(m)
		assert.NoError(t, err)
	}

	// 读取数据
	start := now.Add(-1 * time.Hour)
	end := now.Add(1 * time.Hour)
	ts, err := db.Read("cpu_usage", map[string]string{"host": "localhost"}, start, end)
	assert.NoError(t, err)
	assert.NotNil(t, ts)
	assert.Equal(t, 10, ts.Len())
}

func TestMemoryTSDBReadNotFound(t *testing.T) {
	db := storage.NewMemoryTSDB(24 * time.Hour)

	start := time.Now().Add(-1 * time.Hour)
	end := time.Now().Add(1 * time.Hour)
	_, err := db.Read("nonexistent", nil, start, end)
	assert.Error(t, err)
}

func TestMemoryTSDBGetLatest(t *testing.T) {
	db := storage.NewMemoryTSDB(24 * time.Hour)

	// 写入数据
	for i := 0; i < 10; i++ {
		m := model.NewMetric("cpu_usage", model.MetricTypeGauge, "CPU usage")
		m.SetLabels(map[string]string{"host": "localhost"})
		m.SetValue(float64(i * 10))

		err := db.Write(m)
		assert.NoError(t, err)
	}

	// 获取最新值
	value, ok := db.GetLatest("cpu_usage", map[string]string{"host": "localhost"})
	assert.True(t, ok)
	assert.Equal(t, 90.0, value) // 最后一个值是 90
}

func TestMemoryTSDBGetLatestNotFound(t *testing.T) {
	db := storage.NewMemoryTSDB(24 * time.Hour)

	_, ok := db.GetLatest("nonexistent", nil)
	assert.False(t, ok)
}

func TestMemoryTSDBDelete(t *testing.T) {
	db := storage.NewMemoryTSDB(24 * time.Hour)

	// 写入数据
	m := model.NewMetric("cpu_usage", model.MetricTypeGauge, "CPU usage")
	m.SetLabels(map[string]string{"host": "localhost"})
	m.SetValue(75.5)

	err := db.Write(m)
	assert.NoError(t, err)

	assert.Equal(t, 1, db.GetSeriesCount())

	// 删除数据
	err = db.Delete("cpu_usage", map[string]string{"host": "localhost"})
	assert.NoError(t, err)

	assert.Equal(t, 0, db.GetSeriesCount())
}

func TestMemoryTSDBDeleteNotFound(t *testing.T) {
	db := storage.NewMemoryTSDB(24 * time.Hour)

	err := db.Delete("nonexistent", nil)
	assert.Error(t, err)
}

func TestMemoryTSDBList(t *testing.T) {
	db := storage.NewMemoryTSDB(24 * time.Hour)

	// 写入数据
	m1 := model.NewMetric("cpu_usage", model.MetricTypeGauge, "CPU usage")
	m1.SetLabels(map[string]string{"host": "localhost"})
	m1.SetValue(75.5)

	m2 := model.NewMetric("memory_usage", model.MetricTypeGauge, "Memory usage")
	m2.SetLabels(map[string]string{"host": "localhost"})
	m2.SetValue(60.0)

	err := db.Write(m1)
	assert.NoError(t, err)

	err = db.Write(m2)
	assert.NoError(t, err)

	// 列出指标
	names := db.List()
	assert.Equal(t, 2, len(names))
	assert.Contains(t, names, "cpu_usage")
	assert.Contains(t, names, "memory_usage")
}

func TestMemoryTSDBQuery(t *testing.T) {
	db := storage.NewMemoryTSDB(24 * time.Hour)

	// 写入数据
	m := model.NewMetric("cpu_usage", model.MetricTypeGauge, "CPU usage")
	m.SetLabels(map[string]string{"host": "localhost"})
	m.SetValue(75.5)

	err := db.Write(m)
	assert.NoError(t, err)

	// 查询
	results, err := db.Query("cpu_usage")
	assert.NoError(t, err)
	assert.Equal(t, 1, len(results))
	assert.Equal(t, "cpu_usage", results[0].Metric)
}

func TestMemoryTSDBQueryAll(t *testing.T) {
	db := storage.NewMemoryTSDB(24 * time.Hour)

	// 写入数据
	m1 := model.NewMetric("cpu_usage", model.MetricTypeGauge, "CPU usage")
	m1.SetLabels(map[string]string{"host": "localhost"})
	m1.SetValue(75.5)

	m2 := model.NewMetric("memory_usage", model.MetricTypeGauge, "Memory usage")
	m2.SetLabels(map[string]string{"host": "localhost"})
	m2.SetValue(60.0)

	err := db.Write(m1)
	assert.NoError(t, err)

	err = db.Write(m2)
	assert.NoError(t, err)

	// 查询所有
	results, err := db.Query("*")
	assert.NoError(t, err)
	assert.Equal(t, 2, len(results))
}

func TestQueryEngineSimpleQuery(t *testing.T) {
	db := storage.NewMemoryTSDB(24 * time.Hour)
	engine := storage.NewQueryEngine(db)

	// 写入数据（时间戳在过去，以便查询能匹配）
	now := time.Now()
	for i := 0; i < 10; i++ {
		m := model.NewMetric("cpu_usage", model.MetricTypeGauge, "CPU usage")
		m.SetValue(float64(i * 10))
		m.Timestamp = now.Add(-time.Duration(10-i) * time.Minute) // 10分钟前到现在

		err := db.Write(m)
		assert.NoError(t, err)
	}

	// 查询最近 15 分钟
	results, err := engine.SimpleQuery("cpu_usage", 15*time.Minute)
	assert.NoError(t, err)
	assert.NotNil(t, results)
	assert.Equal(t, 10, results[0].Len())
}

func TestQueryEngineAggregateQuery(t *testing.T) {
	db := storage.NewMemoryTSDB(24 * time.Hour)
	engine := storage.NewQueryEngine(db)

	// 写入数据（时间戳在过去，以便查询能匹配）
	now := time.Now()
	for i := 0; i < 10; i++ {
		m := model.NewMetric("cpu_usage", model.MetricTypeGauge, "CPU usage")
		m.SetValue(float64(i * 10))
		m.Timestamp = now.Add(-time.Duration(10-i) * time.Minute) // 10分钟前到现在

		err := db.Write(m)
		assert.NoError(t, err)
	}

	// 测试不同的聚合函数
	tests := []struct {
		name        string
		aggregation string
		expected    float64
	}{
		{"avg", "avg", 45.0},
		{"sum", "sum", 450.0},
		{"min", "min", 0.0},
		{"max", "max", 90.0},
		{"count", "count", 10.0},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result, err := engine.AggregateQuery("cpu_usage", 1*time.Hour, tt.aggregation)
			assert.NoError(t, err)
			assert.Equal(t, tt.expected, result)
		})
	}
}

func TestQueryEngineAggregateQueryUnknownAggregation(t *testing.T) {
	db := storage.NewMemoryTSDB(24 * time.Hour)
	engine := storage.NewQueryEngine(db)

	_, err := engine.AggregateQuery("cpu_usage", 1*time.Hour, "unknown")
	assert.Error(t, err)
}

func TestMemoryTSDBConcurrency(t *testing.T) {
	db := storage.NewMemoryTSDB(24 * time.Hour)

	done := make(chan bool)
	for i := 0; i < 100; i++ {
		go func(val float64) {
			m := model.NewMetric("cpu_usage", model.MetricTypeGauge, "CPU usage")
			m.SetLabels(map[string]string{"host": "localhost"})
			m.SetValue(val)

			_ = db.Write(m)
			_, _ = db.GetLatest("cpu_usage", map[string]string{"host": "localhost"})
			_ = db.List()
			done <- true
		}(float64(i))
	}

	for i := 0; i < 100; i++ {
		<-done
	}
}
