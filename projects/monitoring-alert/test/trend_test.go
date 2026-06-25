package test

import (
	"testing"
	"time"

	"github.com/monitoring-alert/internal/alert"
	"github.com/monitoring-alert/internal/model"
	"github.com/monitoring-alert/internal/storage"
	"github.com/stretchr/testify/assert"
)

func TestTrendRuleCreation(t *testing.T) {
	rule := alert.NewTrendRule("cpu_spike", "CPU Spike", "cpu_usage", alert.TrendTypeSpike, 50.0, 5*time.Minute, true, model.SeverityWarning)

	assert.NotNil(t, rule)
	assert.Equal(t, "cpu_spike", rule.ID)
	assert.Equal(t, "CPU Spike", rule.Name)
	assert.Equal(t, "cpu_usage", rule.Metric)
	assert.Equal(t, alert.TrendTypeSpike, rule.TrendType)
	assert.Equal(t, 50.0, rule.Threshold)
	assert.Equal(t, 5*time.Minute, rule.Window)
	assert.True(t, rule.IsPercentage)
	assert.Equal(t, model.SeverityWarning, rule.Severity)
	assert.True(t, rule.IsEnabled())
}

func TestTrendRuleSetLabels(t *testing.T) {
	rule := alert.NewTrendRule("test", "Test", "test", alert.TrendTypeIncrease, 10.0, 1*time.Minute, false, model.SeverityInfo)
	rule.SetLabels(map[string]string{"host": "localhost"})

	assert.Equal(t, "localhost", rule.Labels["host"])
}

func TestTrendRuleSetEnabled(t *testing.T) {
	rule := alert.NewTrendRule("test", "Test", "test", alert.TrendTypeIncrease, 10.0, 1*time.Minute, false, model.SeverityInfo)

	assert.True(t, rule.IsEnabled())

	rule.SetEnabled(false)
	assert.False(t, rule.IsEnabled())

	rule.SetEnabled(true)
	assert.True(t, rule.IsEnabled())
}

func TestTrendTypeString(t *testing.T) {
	assert.Equal(t, "increase", alert.TrendTypeIncrease.String())
	assert.Equal(t, "decrease", alert.TrendTypeDecrease.String())
	assert.Equal(t, "spike", alert.TrendTypeSpike.String())
}

func TestTrendEvaluatorCreation(t *testing.T) {
	db := storage.NewMemoryTSDB(24 * time.Hour)
	evaluator := alert.NewTrendEvaluator(db)

	assert.NotNil(t, evaluator)
	assert.Equal(t, 0, len(evaluator.ListRules()))
}

func TestTrendEvaluatorAddRule(t *testing.T) {
	db := storage.NewMemoryTSDB(24 * time.Hour)
	evaluator := alert.NewTrendEvaluator(db)

	rule := alert.NewTrendRule("cpu_spike", "CPU Spike", "cpu_usage", alert.TrendTypeSpike, 50.0, 5*time.Minute, true, model.SeverityWarning)
	evaluator.AddRule(rule)

	rules := evaluator.ListRules()
	assert.Equal(t, 1, len(rules))
	assert.Equal(t, "cpu_spike", rules[0].ID)
}

func TestTrendEvaluatorRemoveRule(t *testing.T) {
	db := storage.NewMemoryTSDB(24 * time.Hour)
	evaluator := alert.NewTrendEvaluator(db)

	rule := alert.NewTrendRule("cpu_spike", "CPU Spike", "cpu_usage", alert.TrendTypeSpike, 50.0, 5*time.Minute, true, model.SeverityWarning)
	evaluator.AddRule(rule)

	evaluator.RemoveRule("cpu_spike")

	rules := evaluator.ListRules()
	assert.Equal(t, 0, len(rules))
}

func TestTrendEvaluatorEvaluateIncrease(t *testing.T) {
	db := storage.NewMemoryTSDB(24 * time.Hour)
	evaluator := alert.NewTrendEvaluator(db)

	// 添加规则：CPU 使用率增长超过 50%（窗口 15 分钟）
	rule := alert.NewTrendRule("cpu_increase", "CPU Increase", "cpu_usage", alert.TrendTypeIncrease, 50.0, 15*time.Minute, true, model.SeverityWarning)
	evaluator.AddRule(rule)

	// 写入数据：从 20% 增长到 90%（在 15 分钟窗口内增长 350%）
	now := time.Now()
	values := []float64{20, 30, 40, 50, 60, 70, 80, 90}
	for i, v := range values {
		m := model.NewMetric("cpu_usage", model.MetricTypeGauge, "CPU usage")
		m.SetValue(v)
		m.Timestamp = now.Add(-time.Duration(len(values)-1-i) * time.Minute)

		err := db.Write(m)
		assert.NoError(t, err)
	}

	// 评估规则
	alerts, err := evaluator.Evaluate()
	assert.NoError(t, err)
	assert.Equal(t, 1, len(alerts))
	assert.Equal(t, "cpu_increase", alerts[0].RuleID)
	assert.Equal(t, model.AlertStatusFiring, alerts[0].GetStatus())
}

func TestTrendEvaluatorEvaluateDecrease(t *testing.T) {
	db := storage.NewMemoryTSDB(24 * time.Hour)
	evaluator := alert.NewTrendEvaluator(db)

	// 添加规则：CPU 使用率下降超过 30（绝对值，窗口 15 分钟）
	rule := alert.NewTrendRule("cpu_decrease", "CPU Decrease", "cpu_usage", alert.TrendTypeDecrease, 30.0, 15*time.Minute, false, model.SeverityWarning)
	evaluator.AddRule(rule)

	// 写入数据：从 80% 下降到 40%（下降 40，超过阈值 30）
	now := time.Now()
	values := []float64{80, 75, 70, 65, 60, 55, 50, 45, 40}
	for i, v := range values {
		m := model.NewMetric("cpu_usage", model.MetricTypeGauge, "CPU usage")
		m.SetValue(v)
		m.Timestamp = now.Add(-time.Duration(len(values)-1-i) * time.Minute)

		err := db.Write(m)
		assert.NoError(t, err)
	}

	// 评估规则
	alerts, err := evaluator.Evaluate()
	assert.NoError(t, err)
	assert.Equal(t, 1, len(alerts))
	assert.Equal(t, "cpu_decrease", alerts[0].RuleID)
}

func TestTrendEvaluatorEvaluateNoTrigger(t *testing.T) {
	db := storage.NewMemoryTSDB(24 * time.Hour)
	evaluator := alert.NewTrendEvaluator(db)

	// 添加规则：CPU 使用率增长超过 100%（窗口 15 分钟）
	rule := alert.NewTrendRule("cpu_spike", "CPU Spike", "cpu_usage", alert.TrendTypeIncrease, 100.0, 15*time.Minute, true, model.SeverityWarning)
	evaluator.AddRule(rule)

	// 写入数据：从 50% 增长到 60%（增长 20%，不超过 100%）
	now := time.Now()
	values := []float64{50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60}
	for i, v := range values {
		m := model.NewMetric("cpu_usage", model.MetricTypeGauge, "CPU usage")
		m.SetValue(v)
		m.Timestamp = now.Add(-time.Duration(len(values)-1-i) * time.Minute)

		err := db.Write(m)
		assert.NoError(t, err)
	}

	// 评估规则
	alerts, err := evaluator.Evaluate()
	assert.NoError(t, err)
	assert.Equal(t, 0, len(alerts))
}

func TestTrendEvaluatorEvaluateDisabledRule(t *testing.T) {
	db := storage.NewMemoryTSDB(24 * time.Hour)
	evaluator := alert.NewTrendEvaluator(db)

	// 添加禁用的规则
	rule := alert.NewTrendRule("cpu_spike", "CPU Spike", "cpu_usage", alert.TrendTypeIncrease, 50.0, 15*time.Minute, true, model.SeverityWarning)
	rule.SetEnabled(false)
	evaluator.AddRule(rule)

	// 写入数据
	now := time.Now()
	values := []float64{20, 30, 40, 50, 60, 70, 80, 90}
	for i, v := range values {
		m := model.NewMetric("cpu_usage", model.MetricTypeGauge, "CPU usage")
		m.SetValue(v)
		m.Timestamp = now.Add(-time.Duration(len(values)-1-i) * time.Minute)

		err := db.Write(m)
		assert.NoError(t, err)
	}

	// 评估规则
	alerts, err := evaluator.Evaluate()
	assert.NoError(t, err)
	assert.Equal(t, 0, len(alerts))
}

func TestTrendEvaluatorGetActiveAlerts(t *testing.T) {
	db := storage.NewMemoryTSDB(24 * time.Hour)
	evaluator := alert.NewTrendEvaluator(db)

	// 添加规则
	rule := alert.NewTrendRule("cpu_spike", "CPU Spike", "cpu_usage", alert.TrendTypeIncrease, 50.0, 15*time.Minute, true, model.SeverityWarning)
	evaluator.AddRule(rule)

	// 写入触发告警的数据
	now := time.Now()
	values := []float64{20, 30, 40, 50, 60, 70, 80, 90}
	for i, v := range values {
		m := model.NewMetric("cpu_usage", model.MetricTypeGauge, "CPU usage")
		m.SetValue(v)
		m.Timestamp = now.Add(-time.Duration(len(values)-1-i) * time.Minute)

		err := db.Write(m)
		assert.NoError(t, err)
	}

	// 评估规则
	_, err := evaluator.Evaluate()
	assert.NoError(t, err)

	// 获取活跃告警
	activeAlerts := evaluator.GetActiveAlerts()
	assert.Equal(t, 1, len(activeAlerts))
}

func TestTrendEvaluatorResolveAlert(t *testing.T) {
	db := storage.NewMemoryTSDB(24 * time.Hour)
	evaluator := alert.NewTrendEvaluator(db)

	// 添加规则
	rule := alert.NewTrendRule("cpu_spike", "CPU Spike", "cpu_usage", alert.TrendTypeIncrease, 50.0, 15*time.Minute, true, model.SeverityWarning)
	evaluator.AddRule(rule)

	// 写入触发告警的数据
	now := time.Now()
	values := []float64{20, 30, 40, 50, 60, 70, 80, 90}
	for i, v := range values {
		m := model.NewMetric("cpu_usage", model.MetricTypeGauge, "CPU usage")
		m.SetValue(v)
		m.Timestamp = now.Add(-time.Duration(len(values)-1-i) * time.Minute)

		err := db.Write(m)
		assert.NoError(t, err)
	}

	// 评估规则
	alerts, err := evaluator.Evaluate()
	assert.NoError(t, err)
	assert.Equal(t, 1, len(alerts))

	// 解决告警
	err = evaluator.ResolveAlert(alerts[0].ID)
	assert.NoError(t, err)

	// 验证告警已解决
	activeAlerts := evaluator.GetActiveAlerts()
	assert.Equal(t, 0, len(activeAlerts))
}
