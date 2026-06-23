package test

import (
	"testing"
	"time"

	"github.com/monitoring-alert/internal/model"
	"github.com/stretchr/testify/assert"
)

func TestMetricCreation(t *testing.T) {
	m := model.NewMetric("cpu_usage", model.MetricTypeGauge, "CPU usage")
	assert.NotNil(t, m)
	assert.Equal(t, "cpu_usage", m.Name)
	assert.Equal(t, model.MetricTypeGauge, m.Type)
	assert.Equal(t, "CPU usage", m.Help)
}

func TestMetricTypeString(t *testing.T) {
	assert.Equal(t, "counter", model.MetricTypeCounter.String())
	assert.Equal(t, "gauge", model.MetricTypeGauge.String())
	assert.Equal(t, "histogram", model.MetricTypeHistogram.String())
}

func TestMetricSetValue(t *testing.T) {
	m := model.NewMetric("test", model.MetricTypeGauge, "test metric")
	m.SetValue(42.5)
	assert.Equal(t, 42.5, m.GetValue())
}

func TestMetricSetLabels(t *testing.T) {
	m := model.NewMetric("test", model.MetricTypeGauge, "test metric")
	labels := map[string]string{"host": "localhost", "env": "prod"}
	m.SetLabels(labels)

	result := m.GetLabels()
	assert.Equal(t, "localhost", result["host"])
	assert.Equal(t, "prod", result["env"])
}

func TestMetricString(t *testing.T) {
	m := model.NewMetric("cpu_usage", model.MetricTypeGauge, "CPU usage")
	m.SetLabels(map[string]string{"host": "localhost"})
	m.SetValue(75.5)

	str := m.String()
	assert.Contains(t, str, "cpu_usage")
	assert.Contains(t, str, "75.5")
}

func TestTimeSeriesCreation(t *testing.T) {
	labels := map[string]string{"host": "localhost"}
	ts := model.NewTimeSeries("cpu_usage", labels)

	assert.NotNil(t, ts)
	assert.Equal(t, "cpu_usage", ts.Metric)
	assert.Equal(t, 0, ts.Len())
}

func TestTimeSeriesAddPoint(t *testing.T) {
	ts := model.NewTimeSeries("test", nil)

	now := time.Now()
	ts.AddPoint(now, 1.0)
	ts.AddPoint(now.Add(time.Second), 2.0)
	ts.AddPoint(now.Add(2*time.Second), 3.0)

	assert.Equal(t, 3, ts.Len())

	points := ts.GetPoints()
	assert.Equal(t, 1.0, points[0].Value)
	assert.Equal(t, 2.0, points[1].Value)
	assert.Equal(t, 3.0, points[2].Value)
}

func TestTimeSeriesGetPointsInRange(t *testing.T) {
	ts := model.NewTimeSeries("test", nil)

	now := time.Now()
	ts.AddPoint(now.Add(-2*time.Hour), 1.0)
	ts.AddPoint(now.Add(-1*time.Hour), 2.0)
	ts.AddPoint(now, 3.0)

	// 查询最近 30 分钟的数据
	start := now.Add(-30 * time.Minute)
	end := now.Add(30 * time.Minute)
	points := ts.GetPointsInRange(start, end)

	assert.Equal(t, 1, len(points))
	assert.Equal(t, 3.0, points[0].Value)
}

func TestTimeSeriesLatest(t *testing.T) {
	ts := model.NewTimeSeries("test", nil)

	// 空时序数据
	_, ok := ts.Latest()
	assert.False(t, ok)

	// 添加数据点
	now := time.Now()
	ts.AddPoint(now, 1.0)
	ts.AddPoint(now.Add(time.Second), 2.0)

	point, ok := ts.Latest()
	assert.True(t, ok)
	assert.Equal(t, 2.0, point.Value)
}

func TestAlertCreation(t *testing.T) {
	labels := map[string]string{"host": "localhost"}
	alert := model.NewAlert("rule1", "CPU High", model.SeverityWarning, labels)

	assert.NotNil(t, alert)
	assert.Equal(t, "rule1", alert.RuleID)
	assert.Equal(t, "CPU High", alert.RuleName)
	assert.Equal(t, model.SeverityWarning, alert.Severity)
	assert.Equal(t, model.AlertStatusPending, alert.GetStatus())
}

func TestAlertSeverityString(t *testing.T) {
	assert.Equal(t, "info", model.SeverityInfo.String())
	assert.Equal(t, "warning", model.SeverityWarning.String())
	assert.Equal(t, "critical", model.SeverityCritical.String())
}

func TestAlertStatusTransitions(t *testing.T) {
	alert := model.NewAlert("rule1", "Test", model.SeverityWarning, nil)

	// 初始状态
	assert.Equal(t, model.AlertStatusPending, alert.GetStatus())

	// 转换到 firing
	alert.SetStatus(model.AlertStatusFiring)
	assert.Equal(t, model.AlertStatusFiring, alert.GetStatus())

	// 转换到 resolved
	alert.SetStatus(model.AlertStatusResolved)
	assert.Equal(t, model.AlertStatusResolved, alert.GetStatus())
	assert.NotNil(t, alert.EndsAt)
}

func TestAlertSetValue(t *testing.T) {
	alert := model.NewAlert("rule1", "Test", model.SeverityWarning, nil)
	alert.SetValue(85.5, 80.0)

	assert.Equal(t, 85.5, alert.Value)
	assert.Equal(t, 80.0, alert.Threshold)
}

func TestAlertString(t *testing.T) {
	alert := model.NewAlert("rule1", "CPU High", model.SeverityWarning, nil)
	alert.SetValue(85.5, 80.0)
	alert.SetStatus(model.AlertStatusFiring)

	str := alert.String()
	assert.Contains(t, str, "warning")
	assert.Contains(t, str, "CPU High")
	assert.Contains(t, str, "85.5")
}

func TestAlertRuleCreation(t *testing.T) {
	rule := model.NewAlertRule("cpu_high", "CPU High", "cpu_usage > 80", model.SeverityWarning)

	assert.NotNil(t, rule)
	assert.Equal(t, "cpu_high", rule.ID)
	assert.Equal(t, "CPU High", rule.Name)
	assert.Equal(t, "cpu_usage > 80", rule.Expr)
	assert.Equal(t, model.SeverityWarning, rule.Severity)
	assert.True(t, rule.IsEnabled())
}

func TestAlertRuleSetFor(t *testing.T) {
	rule := model.NewAlertRule("test", "Test", "test > 0", model.SeverityInfo)
	rule.SetFor(5 * time.Minute)

	assert.Equal(t, 5*time.Minute, rule.For)
}

func TestAlertRuleSetEnabled(t *testing.T) {
	rule := model.NewAlertRule("test", "Test", "test > 0", model.SeverityInfo)

	assert.True(t, rule.IsEnabled())

	rule.SetEnabled(false)
	assert.False(t, rule.IsEnabled())

	rule.SetEnabled(true)
	assert.True(t, rule.IsEnabled())
}

func TestMetricConcurrency(t *testing.T) {
	m := model.NewMetric("test", model.MetricTypeGauge, "test")

	done := make(chan bool)
	for i := 0; i < 100; i++ {
		go func(val float64) {
			m.SetValue(val)
			m.GetValue()
			m.GetLabels()
			done <- true
		}(float64(i))
	}

	for i := 0; i < 100; i++ {
		<-done
	}
}

func TestTimeSeriesConcurrency(t *testing.T) {
	ts := model.NewTimeSeries("test", nil)

	done := make(chan bool)
	for i := 0; i < 100; i++ {
		go func(val float64) {
			ts.AddPoint(time.Now(), val)
			ts.GetPoints()
			ts.Latest()
			done <- true
		}(float64(i))
	}

	for i := 0; i < 100; i++ {
		<-done
	}
}
