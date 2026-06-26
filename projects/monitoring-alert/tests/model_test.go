package tests_test

import (
	"testing"
	"time"

	"github.com/monitoring-alert/internal/model"
)

// TestMetricCreation 测试指标创建
func TestMetricCreation(t *testing.T) {
	m := model.NewMetric("test_metric", model.MetricTypeGauge, "A test metric")

	if m.Name != "test_metric" {
		t.Errorf("expected name 'test_metric', got '%s'", m.Name)
	}
	if m.Type != model.MetricTypeGauge {
		t.Errorf("expected type Gauge, got %v", m.Type)
	}
	if m.Help != "A test metric" {
		t.Errorf("expected help 'A test metric', got '%s'", m.Help)
	}
	if m.Labels == nil {
		t.Error("expected non-nil labels")
	}
}

// TestMetricSetValue 测试设置值
func TestMetricSetValue(t *testing.T) {
	m := model.NewMetric("cpu", model.MetricTypeGauge, "CPU").
		SetValue(42.5)

	if m.Value != 42.5 {
		t.Errorf("expected value 42.5, got %f", m.Value)
	}
	if m.Timestamp.IsZero() {
		t.Error("expected non-zero timestamp")
	}
}

// TestMetricSetLabels 测试设置标签
func TestMetricSetLabels(t *testing.T) {
	m := model.NewMetric("cpu", model.MetricTypeGauge, "CPU").
		SetLabels(map[string]string{"host": "web-01", "region": "us-east"})

	labels := m.GetLabels()
	if labels["host"] != "web-01" {
		t.Errorf("expected host 'web-01', got '%s'", labels["host"])
	}
	if labels["region"] != "us-east" {
		t.Errorf("expected region 'us-east', got '%s'", labels["region"])
	}
}

// TestMetricGetValue 测试获取值
func TestMetricGetValue(t *testing.T) {
	m := model.NewMetric("cpu", model.MetricTypeGauge, "CPU").
		SetValue(75.0)

	value := m.GetValue()
	if value != 75.0 {
		t.Errorf("expected value 75.0, got %f", value)
	}
}

// TestMetricTypeString 测试指标类型字符串
func TestMetricTypeString(t *testing.T) {
	tests := []struct {
		typ      model.MetricType
		expected string
	}{
		{model.MetricTypeCounter, "counter"},
		{model.MetricTypeGauge, "gauge"},
		{model.MetricTypeHistogram, "histogram"},
	}

	for _, tt := range tests {
		result := tt.typ.String()
		if result != tt.expected {
			t.Errorf("MetricType(%s).String() = '%s', want '%s'", tt.typ, result, tt.expected)
		}
	}
}

// TestTimeSeriesAddPoint 测试添加数据点
func TestTimeSeriesAddPoint(t *testing.T) {
	ts := model.NewTimeSeries("cpu", map[string]string{"host": "web-01"})

	ts.AddPoint(time.Now(), 42.0)
	ts.AddPoint(time.Now().Add(time.Second), 45.0)
	ts.AddPoint(time.Now().Add(2*time.Second), 48.0)

	if ts.Len() != 3 {
		t.Errorf("expected 3 points, got %d", ts.Len())
	}
}

// TestTimeSeriesLatest 测试获取最新点
func TestTimeSeriesLatest(t *testing.T) {
	ts := model.NewTimeSeries("cpu", map[string]string{})

	ts.AddPoint(time.Now(), 42.0)
	ts.AddPoint(time.Now().Add(time.Second), 45.0)

	point, ok := ts.Latest()
	if !ok {
		t.Error("expected ok=true for latest point")
	}
	if point.Value != 45.0 {
		t.Errorf("expected latest value 45.0, got %f", point.Value)
	}
}

// TestTimeSeriesEmptyLatest 测试空时序最新值
func TestTimeSeriesEmptyLatest(t *testing.T) {
	ts := model.NewTimeSeries("cpu", map[string]string{})

	_, ok := ts.Latest()
	if ok {
		t.Error("expected ok=false for empty series")
	}
}

// TestTimeSeriesGetPointsInRange 测试范围查询
func TestTimeSeriesGetPointsInRange(t *testing.T) {
	ts := model.NewTimeSeries("cpu", map[string]string{})

	now := time.Now()
	ts.AddPoint(now.Add(-3*time.Second), 10.0)
	ts.AddPoint(now.Add(-2*time.Second), 20.0)
	ts.AddPoint(now.Add(-1*time.Second), 30.0)
	ts.AddPoint(now, 40.0)

	start := now.Add(-2 * time.Second)
	end := now.Add(time.Second)

	points := ts.GetPointsInRange(start, end)
	if len(points) < 2 {
		t.Errorf("expected at least 2 points in range, got %d", len(points))
	}
}

// TestTimeSeriesGetPoints 测试获取所有点
func TestTimeSeriesGetPoints(t *testing.T) {
	ts := model.NewTimeSeries("cpu", map[string]string{})

	ts.AddPoint(time.Now(), 10.0)
	ts.AddPoint(time.Now().Add(time.Second), 20.0)

	points := ts.GetPoints()
	if len(points) != 2 {
		t.Errorf("expected 2 points, got %d", len(points))
	}

	// 验证返回的是副本
	points[0].Value = 999.0
	points2 := ts.GetPoints()
	if points2[0].Value == 999.0 {
		t.Error("expected GetPoints to return a copy")
	}
}

// TestAlertCreation 测试告警创建
func TestAlertCreation(t *testing.T) {
	alert := model.NewAlert("cpu_high", "CPU High Alert", model.SeverityCritical,
		map[string]string{"host": "web-01"})

	if alert.RuleID != "cpu_high" {
		t.Errorf("expected rule_id 'cpu_high', got '%s'", alert.RuleID)
	}
	if alert.Severity != model.SeverityCritical {
		t.Errorf("expected severity Critical, got %v", alert.Severity)
	}
	if alert.Status != model.AlertStatusPending {
		t.Errorf("expected status Pending, got %v", alert.Status)
	}
	if alert.StartsAt.IsZero() {
		t.Error("expected non-zero starts_at")
	}
}

// TestAlertSetStatus 测试设置告警状态
func TestAlertSetStatus(t *testing.T) {
	alert := model.NewAlert("cpu_high", "CPU High", model.SeverityWarning, nil)

	alert.SetStatus(model.AlertStatusFiring)
	if alert.GetStatus() != model.AlertStatusFiring {
		t.Error("expected status Firing")
	}

	alert.SetStatus(model.AlertStatusResolved)
	if alert.GetStatus() != model.AlertStatusResolved {
		t.Error("expected status Resolved")
	}
	if alert.EndsAt == nil {
		t.Error("expected non-zero ends_at for resolved alert")
	}
}

// TestAlertSetValue 测试设置告警值
func TestAlertSetValue(t *testing.T) {
	alert := model.NewAlert("cpu_high", "CPU High", model.SeverityWarning, nil)

	alert.SetValue(85.0, 80.0)
	if alert.Value != 85.0 {
		t.Errorf("expected value 85.0, got %f", alert.Value)
	}
	if alert.Threshold != 80.0 {
		t.Errorf("expected threshold 80.0, got %f", alert.Threshold)
	}
}

// TestAlertSeverityString 测试告警级别字符串
func TestAlertSeverityString(t *testing.T) {
	tests := []struct {
		s        model.AlertSeverity
		expected string
	}{
		{model.SeverityInfo, "info"},
		{model.SeverityWarning, "warning"},
		{model.SeverityCritical, "critical"},
	}

	for _, tt := range tests {
		if tt.s.String() != tt.expected {
			t.Errorf("Severity(%d).String() = '%s', want '%s'", tt.s, tt.s.String(), tt.expected)
		}
	}
}

// TestAlertStatusString 测试告警状态字符串
func TestAlertStatusString(t *testing.T) {
	tests := []struct {
		s        model.AlertStatus
		expected string
	}{
		{model.AlertStatusPending, "pending"},
		{model.AlertStatusFiring, "firing"},
		{model.AlertStatusResolved, "resolved"},
	}

	for _, tt := range tests {
		if tt.s.String() != tt.expected {
			t.Errorf("Status(%d).String() = '%s', want '%s'", tt.s, tt.s.String(), tt.expected)
		}
	}
}

// TestAlertRuleCreation 测试告警规则创建
func TestAlertRuleCreation(t *testing.T) {
	rule := model.NewAlertRule("cpu_high", "CPU High", "cpu_usage > 80", model.SeverityWarning)

	if rule.ID != "cpu_high" {
		t.Errorf("expected ID 'cpu_high', got '%s'", rule.ID)
	}
	if rule.Enabled != true {
		t.Error("expected rule enabled")
	}
	if rule.Labels == nil {
		t.Error("expected non-nil labels")
	}
	if rule.Annotations == nil {
		t.Error("expected non-nil annotations")
	}
}

// TestAlertRuleSetFor 测试设置持续时间
func TestAlertRuleSetFor(t *testing.T) {
	rule := model.NewAlertRule("cpu_high", "CPU High", "cpu_usage > 80", model.SeverityWarning)
	rule.SetFor(5 * time.Minute)

	if rule.For != 5*time.Minute {
		t.Errorf("expected for 5m, got %v", rule.For)
	}
}

// TestAlertRuleSetEnabled 测试启用/禁用规则
func TestAlertRuleSetEnabled(t *testing.T) {
	rule := model.NewAlertRule("cpu_high", "CPU High", "cpu_usage > 80", model.SeverityWarning)

	rule.SetEnabled(false)
	if rule.IsEnabled() {
		t.Error("expected rule to be disabled")
	}

	rule.SetEnabled(true)
	if !rule.IsEnabled() {
		t.Error("expected rule to be enabled")
	}
}

// TestMetricString 测试指标字符串表示
func TestMetricString(t *testing.T) {
	m := model.NewMetric("cpu_usage", model.MetricTypeGauge, "CPU usage %").
		SetLabels(map[string]string{"host": "web-01"}).
		SetValue(42.5)

	str := m.String()
	if str == "" {
		t.Error("expected non-empty string representation")
	}
}

// TestAlertString 测试告警字符串表示
func TestAlertString(t *testing.T) {
	alert := model.NewAlert("cpu_high", "CPU High", model.SeverityWarning, nil)
	alert.SetValue(85.0, 80.0)

	str := alert.String()
	if str == "" {
		t.Error("expected non-empty string representation")
	}
}

// TestTimeSeriesSetPoints 测试设置数据点
func TestTimeSeriesSetPoints(t *testing.T) {
	ts := model.NewTimeSeries("cpu", map[string]string{})

	ts.AddPoint(time.Now(), 10.0)
	ts.AddPoint(time.Now().Add(time.Second), 20.0)

	newPoints := []model.TimeSeriesPoint{
		{Timestamp: time.Now(), Value: 30.0},
	}
	ts.SetPoints(newPoints)

	if ts.Len() != 1 {
		t.Errorf("expected 1 point after SetPoints, got %d", ts.Len())
	}
}

// TestTimeSeriesLabels 测试时序标签
func TestTimeSeriesLabels(t *testing.T) {
	labels := map[string]string{"host": "web-01", "region": "us-east"}
	ts := model.NewTimeSeries("cpu", labels)

		tsLabels := ts.Labels
	if tsLabels["host"] != "web-01" {
		t.Errorf("expected host 'web-01', got '%s'", tsLabels["host"])
	}
}
