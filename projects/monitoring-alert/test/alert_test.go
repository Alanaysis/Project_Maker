package test

import (
	"testing"
	"time"

	"github.com/monitoring-alert/internal/alert"
	"github.com/monitoring-alert/internal/model"
	"github.com/monitoring-alert/internal/storage"
	"github.com/stretchr/testify/assert"
)

func TestConditionEvaluate(t *testing.T) {
	tests := []struct {
		name      string
		operator  alert.Operator
		threshold float64
		value     float64
		expected  bool
	}{
		{"greater than - true", alert.OpGreaterThan, 80.0, 85.0, true},
		{"greater than - false", alert.OpGreaterThan, 80.0, 75.0, false},
		{"greater than - equal", alert.OpGreaterThan, 80.0, 80.0, false},
		{"greater than or equal - true", alert.OpGreaterThanOrEqual, 80.0, 80.0, true},
		{"greater than or equal - false", alert.OpGreaterThanOrEqual, 80.0, 75.0, false},
		{"less than - true", alert.OpLessThan, 80.0, 75.0, true},
		{"less than - false", alert.OpLessThan, 80.0, 85.0, false},
		{"less than or equal - true", alert.OpLessThanOrEqual, 80.0, 80.0, true},
		{"less than or equal - false", alert.OpLessThanOrEqual, 80.0, 85.0, false},
		{"equal - true", alert.OpEqual, 80.0, 80.0, true},
		{"equal - false", alert.OpEqual, 80.0, 85.0, false},
		{"not equal - true", alert.OpNotEqual, 80.0, 85.0, true},
		{"not equal - false", alert.OpNotEqual, 80.0, 80.0, false},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			cond := &alert.Condition{
				Operator:  tt.operator,
				Threshold: tt.threshold,
			}
			result := cond.Evaluate(tt.value)
			assert.Equal(t, tt.expected, result)
		})
	}
}

func TestParseCondition(t *testing.T) {
	tests := []struct {
		name     string
		expr     string
		expected *alert.Condition
	}{
		{
			name: "simple condition",
			expr: "cpu_usage > 80",
			expected: &alert.Condition{
				Metric:    "cpu_usage",
				Operator:  alert.OpGreaterThan,
				Threshold: 80.0,
			},
		},
		{
			name: "condition with duration",
			expr: "memory_usage >= 90 for 5m",
			expected: &alert.Condition{
				Metric:    "memory_usage",
				Operator:  alert.OpGreaterThanOrEqual,
				Threshold: 90.0,
				Duration:  5 * time.Minute,
			},
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			cond, err := alert.ParseCondition(tt.expr)
			assert.NoError(t, err)
			assert.Equal(t, tt.expected.Metric, cond.Metric)
			assert.Equal(t, tt.expected.Operator, cond.Operator)
			assert.Equal(t, tt.expected.Threshold, cond.Threshold)
			assert.Equal(t, tt.expected.Duration, cond.Duration)
		})
	}
}

func TestParseConditionInvalid(t *testing.T) {
	tests := []struct {
		name string
		expr string
	}{
		{"empty", ""},
		{"too few parts", "cpu_usage >"},
		{"invalid operator", "cpu_usage >> 80"},
		{"invalid threshold", "cpu_usage > abc"},
		{"invalid duration", "cpu_usage > 80 for abc"},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			_, err := alert.ParseCondition(tt.expr)
			assert.Error(t, err)
		})
	}
}

func TestRuleEvaluatorCreation(t *testing.T) {
	db := storage.NewMemoryTSDB(24 * time.Hour)
	evaluator := alert.NewRuleEvaluator(db)

	assert.NotNil(t, evaluator)
	assert.Equal(t, 0, len(evaluator.ListRules()))
}

func TestRuleEvaluatorAddRule(t *testing.T) {
	db := storage.NewMemoryTSDB(24 * time.Hour)
	evaluator := alert.NewRuleEvaluator(db)

	rule := model.NewAlertRule("cpu_high", "CPU High", "cpu_usage > 80", model.SeverityWarning)
	err := evaluator.AddRule(rule)
	assert.NoError(t, err)

	rules := evaluator.ListRules()
	assert.Equal(t, 1, len(rules))
	assert.Equal(t, "cpu_high", rules[0].ID)
}

func TestRuleEvaluatorAddRuleInvalidExpr(t *testing.T) {
	db := storage.NewMemoryTSDB(24 * time.Hour)
	evaluator := alert.NewRuleEvaluator(db)

	rule := model.NewAlertRule("invalid", "Invalid", "invalid expression", model.SeverityWarning)
	err := evaluator.AddRule(rule)
	assert.Error(t, err)
}

func TestRuleEvaluatorRemoveRule(t *testing.T) {
	db := storage.NewMemoryTSDB(24 * time.Hour)
	evaluator := alert.NewRuleEvaluator(db)

	rule := model.NewAlertRule("cpu_high", "CPU High", "cpu_usage > 80", model.SeverityWarning)
	err := evaluator.AddRule(rule)
	assert.NoError(t, err)

	evaluator.RemoveRule("cpu_high")

	rules := evaluator.ListRules()
	assert.Equal(t, 0, len(rules))
}

func TestRuleEvaluatorGetRule(t *testing.T) {
	db := storage.NewMemoryTSDB(24 * time.Hour)
	evaluator := alert.NewRuleEvaluator(db)

	rule := model.NewAlertRule("cpu_high", "CPU High", "cpu_usage > 80", model.SeverityWarning)
	err := evaluator.AddRule(rule)
	assert.NoError(t, err)

	result, ok := evaluator.GetRule("cpu_high")
	assert.True(t, ok)
	assert.Equal(t, "cpu_high", result.ID)

	_, ok = evaluator.GetRule("nonexistent")
	assert.False(t, ok)
}

func TestRuleEvaluatorEvaluate(t *testing.T) {
	db := storage.NewMemoryTSDB(24 * time.Hour)
	evaluator := alert.NewRuleEvaluator(db)

	// 添加规则
	rule := model.NewAlertRule("cpu_high", "CPU High", "cpu_usage > 80", model.SeverityWarning)
	err := evaluator.AddRule(rule)
	assert.NoError(t, err)

	// 写入触发告警的数据
	m := model.NewMetric("cpu_usage", model.MetricTypeGauge, "CPU usage")
	m.SetLabels(map[string]string{})
	m.SetValue(85.0)
	err = db.Write(m)
	assert.NoError(t, err)

	// 评估规则
	alerts, err := evaluator.Evaluate()
	assert.NoError(t, err)
	assert.Equal(t, 1, len(alerts))
	assert.Equal(t, "cpu_high", alerts[0].RuleID)
	assert.Equal(t, model.AlertStatusFiring, alerts[0].GetStatus())
}

func TestRuleEvaluatorEvaluateNoTrigger(t *testing.T) {
	db := storage.NewMemoryTSDB(24 * time.Hour)
	evaluator := alert.NewRuleEvaluator(db)

	// 添加规则
	rule := model.NewAlertRule("cpu_high", "CPU High", "cpu_usage > 80", model.SeverityWarning)
	err := evaluator.AddRule(rule)
	assert.NoError(t, err)

	// 写入不触发告警的数据
	m := model.NewMetric("cpu_usage", model.MetricTypeGauge, "CPU usage")
	m.SetLabels(map[string]string{})
	m.SetValue(70.0)
	err = db.Write(m)
	assert.NoError(t, err)

	// 评估规则
	alerts, err := evaluator.Evaluate()
	assert.NoError(t, err)
	assert.Equal(t, 0, len(alerts))
}

func TestRuleEvaluatorEvaluateDisabledRule(t *testing.T) {
	db := storage.NewMemoryTSDB(24 * time.Hour)
	evaluator := alert.NewRuleEvaluator(db)

	// 添加禁用的规则
	rule := model.NewAlertRule("cpu_high", "CPU High", "cpu_usage > 80", model.SeverityWarning)
	rule.SetEnabled(false)
	err := evaluator.AddRule(rule)
	assert.NoError(t, err)

	// 写入触发告警的数据
	m := model.NewMetric("cpu_usage", model.MetricTypeGauge, "CPU usage")
	m.SetLabels(map[string]string{})
	m.SetValue(85.0)
	err = db.Write(m)
	assert.NoError(t, err)

	// 评估规则
	alerts, err := evaluator.Evaluate()
	assert.NoError(t, err)
	assert.Equal(t, 0, len(alerts))
}

func TestRuleEvaluatorGetActiveAlerts(t *testing.T) {
	db := storage.NewMemoryTSDB(24 * time.Hour)
	evaluator := alert.NewRuleEvaluator(db)

	// 添加规则
	rule := model.NewAlertRule("cpu_high", "CPU High", "cpu_usage > 80", model.SeverityWarning)
	err := evaluator.AddRule(rule)
	assert.NoError(t, err)

	// 写入触发告警的数据
	m := model.NewMetric("cpu_usage", model.MetricTypeGauge, "CPU usage")
	m.SetLabels(map[string]string{})
	m.SetValue(85.0)
	err = db.Write(m)
	assert.NoError(t, err)

	// 评估规则
	_, err = evaluator.Evaluate()
	assert.NoError(t, err)

	// 获取活跃告警
	activeAlerts := evaluator.GetActiveAlerts()
	assert.Equal(t, 1, len(activeAlerts))
}

func TestRuleEvaluatorResolveAlert(t *testing.T) {
	db := storage.NewMemoryTSDB(24 * time.Hour)
	evaluator := alert.NewRuleEvaluator(db)

	// 添加规则
	rule := model.NewAlertRule("cpu_high", "CPU High", "cpu_usage > 80", model.SeverityWarning)
	err := evaluator.AddRule(rule)
	assert.NoError(t, err)

	// 写入触发告警的数据
	m := model.NewMetric("cpu_usage", model.MetricTypeGauge, "CPU usage")
	m.SetLabels(map[string]string{})
	m.SetValue(85.0)
	err = db.Write(m)
	assert.NoError(t, err)

	// 评估规则
	alerts, err := evaluator.Evaluate()
	assert.NoError(t, err)
	assert.Equal(t, 1, len(alerts))

	// 解决告警
	err = evaluator.ResolveAlert(alerts[0].ID)
	assert.NoError(t, err)

	// 验证告警已解决
	alert, ok := evaluator.GetAlert(alerts[0].ID)
	assert.True(t, ok)
	assert.Equal(t, model.AlertStatusResolved, alert.GetStatus())
}

func TestRuleEvaluatorResolveAlertNotFound(t *testing.T) {
	db := storage.NewMemoryTSDB(24 * time.Hour)
	evaluator := alert.NewRuleEvaluator(db)

	err := evaluator.ResolveAlert("nonexistent")
	assert.Error(t, err)
}

func TestRuleEvaluatorCleanupResolvedAlerts(t *testing.T) {
	db := storage.NewMemoryTSDB(24 * time.Hour)
	evaluator := alert.NewRuleEvaluator(db)

	// 添加规则
	rule := model.NewAlertRule("cpu_high", "CPU High", "cpu_usage > 80", model.SeverityWarning)
	err := evaluator.AddRule(rule)
	assert.NoError(t, err)

	// 写入触发告警的数据
	m := model.NewMetric("cpu_usage", model.MetricTypeGauge, "CPU usage")
	m.SetLabels(map[string]string{})
	m.SetValue(85.0)
	err = db.Write(m)
	assert.NoError(t, err)

	// 评估规则
	alerts, err := evaluator.Evaluate()
	assert.NoError(t, err)

	// 解决告警
	err = evaluator.ResolveAlert(alerts[0].ID)
	assert.NoError(t, err)

	// 清理已解决的告警
	count := evaluator.CleanupResolvedAlerts(0)
	assert.Equal(t, 1, count)
}

func TestAlertManagerCreation(t *testing.T) {
	db := storage.NewMemoryTSDB(24 * time.Hour)
	evaluator := alert.NewRuleEvaluator(db)
	manager := alert.NewAlertManager(evaluator, 100)

	assert.NotNil(t, manager)
	assert.Equal(t, 0, len(manager.GetHistory()))
}

func TestAlertManagerCheckAndNotify(t *testing.T) {
	db := storage.NewMemoryTSDB(24 * time.Hour)
	evaluator := alert.NewRuleEvaluator(db)
	manager := alert.NewAlertManager(evaluator, 100)

	// 添加规则
	rule := model.NewAlertRule("cpu_high", "CPU High", "cpu_usage > 80", model.SeverityWarning)
	err := evaluator.AddRule(rule)
	assert.NoError(t, err)

	// 写入触发告警的数据
	m := model.NewMetric("cpu_usage", model.MetricTypeGauge, "CPU usage")
	m.SetLabels(map[string]string{})
	m.SetValue(85.0)
	err = db.Write(m)
	assert.NoError(t, err)

	// 检查并通知
	err = manager.CheckAndNotify()
	assert.NoError(t, err)

	// 验证历史记录
	history := manager.GetHistory()
	assert.Equal(t, 1, len(history))
	assert.Equal(t, "cpu_high", history[0].RuleID)
}
