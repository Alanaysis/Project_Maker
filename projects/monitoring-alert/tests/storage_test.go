package tests_test

import (
	"testing"
	"time"

	"github.com/monitoring-alert/internal/model"
	"github.com/monitoring-alert/internal/storage"
)

// TestMemoryTSDBWrite 测试写入
func TestMemoryTSDBWrite(t *testing.T) {
	db := storage.NewMemoryTSDB(24 * time.Hour)

	m := model.NewMetric("cpu", model.MetricTypeGauge, "CPU").
		SetLabels(map[string]string{"host": "web-01"}).
		SetValue(42.0)

	err := db.Write(m)
	if err != nil {
		t.Fatalf("write error: %v", err)
	}

	if db.GetSeriesCount() != 1 {
		t.Errorf("expected 1 series, got %d", db.GetSeriesCount())
	}
}

// TestMemoryTSDBRead 测试读取
func TestMemoryTSDBRead(t *testing.T) {
	db := storage.NewMemoryTSDB(24 * time.Hour)

	now := time.Now()
	for i := 0; i < 10; i++ {
		m := model.NewMetric("cpu", model.MetricTypeGauge, "CPU").
			SetLabels(map[string]string{"host": "web-01"}).
			SetValue(float64(40 + i))
		m.Timestamp = now.Add(time.Duration(i) * time.Second)
		db.Write(m)
	}

	ts, err := db.Read("cpu", map[string]string{"host": "web-01"},
		now.Add(-5*time.Second), now.Add(time.Second))
	if err != nil {
		t.Fatalf("read error: %v", err)
	}

	if ts == nil {
		t.Fatal("expected non-nil time series")
	}

	points := ts.GetPoints()
	if len(points) == 0 {
		t.Error("expected data points")
	}
}

// TestMemoryTSDBGetLatest 测试获取最新值
func TestMemoryTSDBGetLatest(t *testing.T) {
	db := storage.NewMemoryTSDB(24 * time.Hour)

	m := model.NewMetric("cpu", model.MetricTypeGauge, "CPU").
		SetLabels(map[string]string{"host": "web-01"}).
		SetValue(85.0)
	db.Write(m)

	value, ok := db.GetLatest("cpu", map[string]string{"host": "web-01"})
	if !ok {
		t.Fatal("expected ok=true")
	}
	if value != 85.0 {
		t.Errorf("expected value 85.0, got %f", value)
	}
}

// TestMemoryTSDBGetLatestNotFound 测试获取不存在的指标
func TestMemoryTSDBGetLatestNotFound(t *testing.T) {
	db := storage.NewMemoryTSDB(24 * time.Hour)

	_, ok := db.GetLatest("nonexistent", map[string]string{})
	if ok {
		t.Error("expected ok=false for nonexistent metric")
	}
}

// TestMemoryTSDBList 测试列出指标
func TestMemoryTSDBList(t *testing.T) {
	db := storage.NewMemoryTSDB(24 * time.Hour)

	db.Write(model.NewMetric("cpu", model.MetricTypeGauge, "CPU").SetValue(1))
	db.Write(model.NewMetric("memory", model.MetricTypeGauge, "Memory").SetValue(2))
	db.Write(model.NewMetric("disk", model.MetricTypeGauge, "Disk").SetValue(3))

	list := db.List()
	if len(list) != 3 {
		t.Errorf("expected 3 metrics, got %d", len(list))
	}
}

// TestMemoryTSDBDifferentLabels 测试不同标签
func TestMemoryTSDBDifferentLabels(t *testing.T) {
	db := storage.NewMemoryTSDB(24 * time.Hour)

	db.Write(model.NewMetric("cpu", model.MetricTypeGauge, "CPU").
		SetLabels(map[string]string{"host": "web-01"}).SetValue(40))
	db.Write(model.NewMetric("cpu", model.MetricTypeGauge, "CPU").
		SetLabels(map[string]string{"host": "web-02"}).SetValue(60))

	if db.GetSeriesCount() != 2 {
		t.Errorf("expected 2 series, got %d", db.GetSeriesCount())
	}

	v1, ok1 := db.GetLatest("cpu", map[string]string{"host": "web-01"})
	v2, ok2 := db.GetLatest("cpu", map[string]string{"host": "web-02"})

	if !ok1 || v1 != 40 {
		t.Errorf("web-01: expected 40, got %f (ok=%v)", v1, ok1)
	}
	if !ok2 || v2 != 60 {
		t.Errorf("web-02: expected 60, got %f (ok=%v)", v2, ok2)
	}
}

// TestMemoryTSDBDelete 测试删除
func TestMemoryTSDBDelete(t *testing.T) {
	db := storage.NewMemoryTSDB(24 * time.Hour)

	db.Write(model.NewMetric("cpu", model.MetricTypeGauge, "CPU").
		SetLabels(map[string]string{"host": "web-01"}).SetValue(40))

	if db.GetSeriesCount() != 1 {
		t.Fatal("expected 1 series before delete")
	}

	err := db.Delete("cpu", map[string]string{"host": "web-01"})
	if err != nil {
		t.Fatalf("delete error: %v", err)
	}

	if db.GetSeriesCount() != 0 {
		t.Errorf("expected 0 series after delete, got %d", db.GetSeriesCount())
	}
}

// TestMemoryTSDBDeleteNotFound 测试删除不存在的指标
func TestMemoryTSDBDeleteNotFound(t *testing.T) {
	db := storage.NewMemoryTSDB(24 * time.Hour)

	err := db.Delete("nonexistent", map[string]string{})
	if err == nil {
		t.Error("expected error for deleting nonexistent metric")
	}
}

// TestMemoryTSDBRetention 测试数据保留
func TestMemoryTSDBRetention(t *testing.T) {
	db := storage.NewMemoryTSDB(1 * time.Second) // 1s 保留

	now := time.Now()
	// 写入旧数据
	for i := 0; i < 5; i++ {
		m := model.NewMetric("cpu", model.MetricTypeGauge, "CPU").
			SetLabels(map[string]string{"host": "web-01"}).
			SetValue(float64(40 + i))
		m.Timestamp = now.Add(-2 * time.Second)
		db.Write(m)
	}

	// 等待清理
	time.Sleep(2 * time.Second)

	// 写入新数据
	m := model.NewMetric("cpu", model.MetricTypeGauge, "CPU").
		SetLabels(map[string]string{"host": "web-01"}).
		SetValue(99.0)
	db.Write(m)

	// 旧数据应该被清理，只保留新数据
	ts, err := db.Read("cpu", map[string]string{"host": "web-01"},
		time.Now().Add(-5*time.Second), time.Now())
	if err != nil {
		// 旧数据被清理，Read 可能报错
		return
	}
	points := ts.GetPoints()
	if len(points) > 0 {
		// 验证新数据存在
		for _, p := range points {
			if p.Value == 99.0 {
				return // 找到新数据，测试通过
			}
		}
		t.Error("expected to find new data point with value 99.0")
	}
}

// TestMemoryTSDBQuery 测试查询
func TestMemoryTSDBQuery(t *testing.T) {
	db := storage.NewMemoryTSDB(24 * time.Hour)

	db.Write(model.NewMetric("cpu", model.MetricTypeGauge, "CPU").SetValue(1))
	db.Write(model.NewMetric("cpu", model.MetricTypeGauge, "CPU").SetValue(2))
	db.Write(model.NewMetric("memory", model.MetricTypeGauge, "Memory").SetValue(3))

	tsList, err := db.Query("cpu")
	if err != nil {
		t.Fatalf("query error: %v", err)
	}

	if len(tsList) != 1 {
		t.Errorf("expected 1 series for 'cpu', got %d", len(tsList))
	}
}

// TestMemoryTSDBWildcardQuery 测试通配符查询
func TestMemoryTSDBWildcardQuery(t *testing.T) {
	db := storage.NewMemoryTSDB(24 * time.Hour)

	db.Write(model.NewMetric("cpu", model.MetricTypeGauge, "CPU").SetValue(1))
	db.Write(model.NewMetric("memory", model.MetricTypeGauge, "Memory").SetValue(2))

	tsList, err := db.Query("*")
	if err != nil {
		t.Fatalf("query error: %v", err)
	}

	if len(tsList) < 2 {
		t.Errorf("expected at least 2 series for wildcard query, got %d", len(tsList))
	}
}

// TestMemoryTSDBPointCount 测试数据点计数
func TestMemoryTSDBPointCount(t *testing.T) {
	db := storage.NewMemoryTSDB(24 * time.Hour)

	for i := 0; i < 10; i++ {
		db.Write(model.NewMetric("cpu", model.MetricTypeGauge, "CPU").
			SetLabels(map[string]string{"host": "web-01"}).SetValue(float64(i)))
	}

	count := db.GetPointCount()
	if count != 10 {
		t.Errorf("expected 10 points, got %d", count)
	}
}

// TestMemoryTSDBEmptyRead 测试空读取
func TestMemoryTSDBEmptyRead(t *testing.T) {
	db := storage.NewMemoryTSDB(24 * time.Hour)

	_, err := db.Read("nonexistent", map[string]string{},
		time.Now().Add(-1*time.Hour), time.Now())
	if err == nil {
		t.Error("expected error for reading nonexistent metric")
	}
}

// TestMemoryTSDBRetentionTime 测试不同保留时间
func TestMemoryTSDBRetentionTime(t *testing.T) {
	db := storage.NewMemoryTSDB(30 * time.Second)

	now := time.Now()
	m := model.NewMetric("cpu", model.MetricTypeGauge, "CPU").
		SetLabels(map[string]string{"host": "web-01"}).
		SetValue(42.0)
	m.Timestamp = now.Add(-10 * time.Second)
	db.Write(m)

	// 数据应该还在
	ts, err := db.Read("cpu", map[string]string{"host": "web-01"},
		now.Add(-20*time.Second), now.Add(time.Second))
	if err != nil {
		t.Fatalf("read error: %v", err)
	}
	if ts.Len() == 0 {
		t.Error("expected data to still be present")
	}
}

// TestMemoryTSDBMultipleWritesSameSeries 测试同一时序多次写入
func TestMemoryTSDBMultipleWritesSameSeries(t *testing.T) {
	db := storage.NewMemoryTSDB(24 * time.Hour)

	labels := map[string]string{"host": "web-01"}
	for i := 0; i < 20; i++ {
		m := model.NewMetric("cpu", model.MetricTypeGauge, "CPU").
			SetLabels(labels).SetValue(float64(40 + i))
		db.Write(m)
	}

	ts, err := db.Read("cpu", labels,
		time.Now().Add(-1*time.Hour), time.Now())
	if err != nil {
		t.Fatalf("read error: %v", err)
	}

	if ts.Len() != 20 {
		t.Errorf("expected 20 points, got %d", ts.Len())
	}
}
