package test

import (
	"testing"
	"time"

	"github.com/monitoring-alert/internal/alert"
	"github.com/monitoring-alert/internal/model"
	"github.com/monitoring-alert/internal/storage"
	"github.com/stretchr/testify/assert"
)

func TestCompositeConditionEvaluate(t *testing.T) {
	tests := []struct {
		name      string
		cond      alert.CompositeCondition
		values    []float64
		expected  bool
	}{
		{
			name: "AND - both true",
			cond: alert.CompositeCondition{
				Conditions: []alert.Condition{
					{Operator: alert.OpGreaterThan, Threshold: 80.0},
					{Operator: alert.OpGreaterThan, Threshold: 70.0},
				},
				Operator: alert.LogicalAnd,
			},
			values:   []float64{85.0, 75.0},
			expected: true,
		},
		{
			name: "AND - one false",
			cond: alert.CompositeCondition{
				Conditions: []alert.Condition{
					{Operator: alert.OpGreaterThan, Threshold: 80.0},
					{Operator: alert.OpGreaterThan, Threshold: 70.0},
				},
				Operator: alert.LogicalAnd,
			},
			values:   []float64{85.0, 65.0},
			expected: false,
		},
		{
			name: "OR - both true",
			cond: alert.CompositeCondition{
				Conditions: []alert.Condition{
					{Operator: alert.OpGreaterThan, Threshold: 80.0},
					{Operator: alert.OpGreaterThan, Threshold: 70.0},
				},
				Operator: alert.LogicalOr,
			},
			values:   []float64{85.0, 75.0},
			expected: true,
		},
		{
			name: "OR - one true",
			cond: alert.CompositeCondition{
				Conditions: []alert.Condition{
					{Operator: alert.OpGreaterThan, Threshold: 80.0},
					{Operator: alert.OpGreaterThan, Threshold: 70.0},
				},
				Operator: alert.LogicalOr,
			},
			values:   []float64{75.0, 75.0},
			expected: true,
		},
		{
			name: "OR - both false",
			cond: alert.CompositeCondition{
				Conditions: []alert.Condition{
					{Operator: alert.OpGreaterThan, Threshold: 80.0},
					{Operator: alert.OpGreaterThan, Threshold: 70.0},
				},
				Operator: alert.LogicalOr,
			},
			values:   []float64{75.0, 65.0},
			expected: false,
		},
		{
			name: "mismatched values count",
			cond: alert.CompositeCondition{
				Conditions: []alert.Condition{
					{Operator: alert.OpGreaterThan, Threshold: 80.0},
				},
				Operator: alert.LogicalAnd,
			},
			values:   []float64{85.0, 75.0},
			expected: false,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := tt.cond.Evaluate(tt.values)
			assert.Equal(t, tt.expected, result)
		})
	}
}

func TestParseCompositeCondition(t *testing.T) {
	tests := []struct {
		name     string
		expr     string
		expected alert.LogicalOperator
		count    int
	}{
		{
			name:     "AND condition",
			expr:     "cpu_usage > 80 AND memory_usage > 70",
			expected: alert.LogicalAnd,
			count:    2,
		},
		{
			name:     "OR condition",
			expr:     "cpu_usage > 80 OR memory_usage > 70",
			expected: alert.LogicalOr,
			count:    2,
		},
		{
			name:     "single condition",
			expr:     "cpu_usage > 80",
			expected: alert.LogicalAnd,
			count:    1,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			cond, err := alert.ParseCompositeCondition(tt.expr)
			assert.NoError(t, err)
			assert.NotNil(t, cond)
			assert.Equal(t, tt.expected, cond.Operator)
			assert.Equal(t, tt.count, len(cond.Conditions))
		})
	}
}

func TestParseCompositeConditionInvalid(t *testing.T) {
	tests := []struct {
		name string
		expr string
	}{
		{"empty", ""},
		{"invalid AND part", "cpu_usage > 80 AND invalid"},
		{"invalid OR part", "cpu_usage > 80 OR invalid"},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			_, err := alert.ParseCompositeCondition(tt.expr)
			assert.Error(t, err)
		})
	}
}

func TestCompositeRuleCreation(t *testing.T) {
	rule := alert.NewCompositeRule("cpu_memory_high", "CPU and Memory High", "cpu_usage > 80 AND memory_usage > 70", model.SeverityCritical)

	assert.NotNil(t, rule)
	assert.Equal(t, "cpu_memory_high", rule.ID)
	assert.Equal(t, "CPU and Memory High", rule.Name)
	assert.Equal(t, "cpu_usage > 80 AND memory_usage > 70", rule.Expr)
	assert.Equal(t, model.SeverityCritical, rule.Severity)
	assert.True(t, rule.IsEnabled())
}

func TestCompositeRuleSetFor(t *testing.T) {
	rule := alert.NewCompositeRule("test", "Test", "test > 0", model.SeverityInfo)
	rule.SetFor(5 * time.Minute)

	assert.Equal(t, 5*time.Minute, rule.For)
}

func TestCompositeRuleSetEnabled(t *testing.T) {
	rule := alert.NewCompositeRule("test", "Test", "test > 0", model.SeverityInfo)

	assert.True(t, rule.IsEnabled())

	rule.SetEnabled(false)
	assert.False(t, rule.IsEnabled())

	rule.SetEnabled(true)
	assert.True(t, rule.IsEnabled())
}

func TestCompositeEvaluatorCreation(t *testing.T) {
	db := storage.NewMemoryTSDB(24 * time.Hour)
	evaluator := alert.NewCompositeEvaluator(db)

	assert.NotNil(t, evaluator)
	assert.Equal(t, 0, len(evaluator.ListRules()))
}

func TestCompositeEvaluatorAddRule(t *testing.T) {
	db := storage.NewMemoryTSDB(24 * time.Hour)
	evaluator := alert.NewCompositeEvaluator(db)

	rule := alert.NewCompositeRule("cpu_memory_high", "CPU and Memory High", "cpu_usage > 80 AND memory_usage > 70", model.SeverityCritical)
	err := evaluator.AddRule(rule)
	assert.NoError(t, err)

	rules := evaluator.ListRules()
	assert.Equal(t, 1, len(rules))
	assert.Equal(t, "cpu_memory_high", rules[0].ID)
}

func TestCompositeEvaluatorAddRuleInvalidExpr(t *testing.T) {
	db := storage.NewMemoryTSDB(24 * time.Hour)
	evaluator := alert.NewCompositeEvaluator(db)

	rule := alert.NewCompositeRule("invalid", "Invalid", "invalid expression", model.SeverityCritical)
	err := evaluator.AddRule(rule)
	assert.Error(t, err)
}

func TestCompositeEvaluatorRemoveRule(t *testing.T) {
	db := storage.NewMemoryTSDB(24 * time.Hour)
	evaluator := alert.NewCompositeEvaluator(db)

	rule := alert.NewCompositeRule("cpu_memory_high", "CPU and Memory High", "cpu_usage > 80 AND memory_usage > 70", model.SeverityCritical)
	err := evaluator.AddRule(rule)
	assert.NoError(t, err)

	evaluator.RemoveRule("cpu_memory_high")

	rules := evaluator.ListRules()
	assert.Equal(t, 0, len(rules))
}

func TestCompositeEvaluatorEvaluateAND(t *testing.T) {
	db := storage.NewMemoryTSDB(24 * time.Hour)
	evaluator := alert.NewCompositeEvaluator(db)

	// 添加规则：CPU > 70 AND Memory > 80
	rule := alert.NewCompositeRule("cpu_memory_high", "CPU and Memory High", "cpu_usage > 70 AND memory_usage > 80", model.SeverityCritical)
	err := evaluator.AddRule(rule)
	assert.NoError(t, err)

	// 写入触发告警的数据
	cpuMetric := model.NewMetric("cpu_usage", model.MetricTypeGauge, "CPU usage")
	cpuMetric.SetValue(75.0)
	err = db.Write(cpuMetric)
	assert.NoError(t, err)

	memMetric := model.NewMetric("memory_usage", model.MetricTypeGauge, "Memory usage")
	memMetric.SetValue(85.0)
	err = db.Write(memMetric)
	assert.NoError(t, err)

	// 评估规则
	alerts, err := evaluator.Evaluate()
	assert.NoError(t, err)
	assert.Equal(t, 1, len(alerts))
	assert.Equal(t, "cpu_memory_high", alerts[0].RuleID)
	assert.Equal(t, model.AlertStatusFiring, alerts[0].GetStatus())
}

func TestCompositeEvaluatorEvaluateANDNoTrigger(t *testing.T) {
	db := storage.NewMemoryTSDB(24 * time.Hour)
	evaluator := alert.NewCompositeEvaluator(db)

	// 添加规则：CPU > 70 AND Memory > 80
	rule := alert.NewCompositeRule("cpu_memory_high", "CPU and Memory High", "cpu_usage > 70 AND memory_usage > 80", model.SeverityCritical)
	err := evaluator.AddRule(rule)
	assert.NoError(t, err)

	// 写入不触发告警的数据（只有 CPU 满足条件）
	cpuMetric := model.NewMetric("cpu_usage", model.MetricTypeGauge, "CPU usage")
	cpuMetric.SetValue(75.0)
	err = db.Write(cpuMetric)
	assert.NoError(t, err)

	memMetric := model.NewMetric("memory_usage", model.MetricTypeGauge, "Memory usage")
	memMetric.SetValue(70.0) // 不满足 > 80
	err = db.Write(memMetric)
	assert.NoError(t, err)

	// 评估规则
	alerts, err := evaluator.Evaluate()
	assert.NoError(t, err)
	assert.Equal(t, 0, len(alerts))
}

func TestCompositeEvaluatorEvaluateOR(t *testing.T) {
	db := storage.NewMemoryTSDB(24 * time.Hour)
	evaluator := alert.NewCompositeEvaluator(db)

	// 添加规则：CPU > 80 OR Memory > 90
	rule := alert.NewCompositeRule("cpu_or_memory_high", "CPU or Memory High", "cpu_usage > 80 OR memory_usage > 90", model.SeverityWarning)
	err := evaluator.AddRule(rule)
	assert.NoError(t, err)

	// 写入触发告警的数据（只有 Memory 满足条件）
	cpuMetric := model.NewMetric("cpu_usage", model.MetricTypeGauge, "CPU usage")
	cpuMetric.SetValue(70.0) // 不满足 > 80
	err = db.Write(cpuMetric)
	assert.NoError(t, err)

	memMetric := model.NewMetric("memory_usage", model.MetricTypeGauge, "Memory usage")
	memMetric.SetValue(95.0) // 满足 > 90
	err = db.Write(memMetric)
	assert.NoError(t, err)

	// 评估规则
	alerts, err := evaluator.Evaluate()
	assert.NoError(t, err)
	assert.Equal(t, 1, len(alerts))
	assert.Equal(t, "cpu_or_memory_high", alerts[0].RuleID)
}

func TestCompositeEvaluatorEvaluateDisabledRule(t *testing.T) {
	db := storage.NewMemoryTSDB(24 * time.Hour)
	evaluator := alert.NewCompositeEvaluator(db)

	// 添加禁用的规则
	rule := alert.NewCompositeRule("cpu_memory_high", "CPU and Memory High", "cpu_usage > 70 AND memory_usage > 80", model.SeverityCritical)
	rule.SetEnabled(false)
	err := evaluator.AddRule(rule)
	assert.NoError(t, err)

	// 写入触发告警的数据
	cpuMetric := model.NewMetric("cpu_usage", model.MetricTypeGauge, "CPU usage")
	cpuMetric.SetValue(75.0)
	err = db.Write(cpuMetric)
	assert.NoError(t, err)

	memMetric := model.NewMetric("memory_usage", model.MetricTypeGauge, "Memory usage")
	memMetric.SetValue(85.0)
	err = db.Write(memMetric)
	assert.NoError(t, err)

	// 评估规则
	alerts, err := evaluator.Evaluate()
	assert.NoError(t, err)
	assert.Equal(t, 0, len(alerts))
}

func TestCompositeEvaluatorGetActiveAlerts(t *testing.T) {
	db := storage.NewMemoryTSDB(24 * time.Hour)
	evaluator := alert.NewCompositeEvaluator(db)

	// 添加规则
	rule := alert.NewCompositeRule("cpu_memory_high", "CPU and Memory High", "cpu_usage > 70 AND memory_usage > 80", model.SeverityCritical)
	err := evaluator.AddRule(rule)
	assert.NoError(t, err)

	// 写入触发告警的数据
	cpuMetric := model.NewMetric("cpu_usage", model.MetricTypeGauge, "CPU usage")
	cpuMetric.SetValue(75.0)
	err = db.Write(cpuMetric)
	assert.NoError(t, err)

	memMetric := model.NewMetric("memory_usage", model.MetricTypeGauge, "Memory usage")
	memMetric.SetValue(85.0)
	err = db.Write(memMetric)
	assert.NoError(t, err)

	// 评估规则
	_, err = evaluator.Evaluate()
	assert.NoError(t, err)

	// 获取活跃告警
	activeAlerts := evaluator.GetActiveAlerts()
	assert.Equal(t, 1, len(activeAlerts))
}

func TestCompositeEvaluatorResolveAlert(t *testing.T) {
	db := storage.NewMemoryTSDB(24 * time.Hour)
	evaluator := alert.NewCompositeEvaluator(db)

	// 添加规则
	rule := alert.NewCompositeRule("cpu_memory_high", "CPU and Memory High", "cpu_usage > 70 AND memory_usage > 80", model.SeverityCritical)
	err := evaluator.AddRule(rule)
	assert.NoError(t, err)

	// 写入触发告警的数据
	cpuMetric := model.NewMetric("cpu_usage", model.MetricTypeGauge, "CPU usage")
	cpuMetric.SetValue(75.0)
	err = db.Write(cpuMetric)
	assert.NoError(t, err)

	memMetric := model.NewMetric("memory_usage", model.MetricTypeGauge, "Memory usage")
	memMetric.SetValue(85.0)
	err = db.Write(memMetric)
	assert.NoError(t, err)

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
