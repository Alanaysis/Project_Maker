package tests_test

import (
	"testing"
	"time"

	"github.com/monitoring-alert/internal/model"
	"github.com/monitoring-alert/internal/storage"
	"github.com/monitoring-alert/src/alert"
)

// TestCompositeEvaluatorAND 测试 AND 组合
func TestCompositeEvaluatorAND(t *testing.T) {
	db := storage.NewMemoryTSDB(24 * time.Hour)

	now := time.Now()
	db.Write(model.NewMetric("cpu", model.MetricTypeGauge, "CPU").
		SetLabels(map[string]string{"host": "web-01"}).SetValue(90.0))
	m := model.NewMetric("memory", model.MetricTypeGauge, "Memory").
		SetLabels(map[string]string{"host": "web-01"}).
		SetValue(85.0)
	m.Timestamp = now
	db.Write(m)

	evaluator := alert.NewCompositeEvaluator(db)
	rule := alert.NewCompositeRule("high_load", "High Load", "cpu > 80 AND memory > 80", model.SeverityCritical)
	evaluator.AddRule(rule)

	alerts, err := evaluator.Evaluate()
	if err != nil {
		t.Fatalf("evaluate error: %v", err)
	}

	if len(alerts) != 1 {
		t.Errorf("expected 1 alert for AND, got %d", len(alerts))
	}
}

// TestCompositeEvaluatorANDNotFired 测试 AND 不触发
func TestCompositeEvaluatorANDNotFired(t *testing.T) {
	db := storage.NewMemoryTSDB(24 * time.Hour)

	now := time.Now()
	db.Write(model.NewMetric("cpu", model.MetricTypeGauge, "CPU").
		SetLabels(map[string]string{"host": "web-01"}).SetValue(90.0))
	m := model.NewMetric("memory", model.MetricTypeGauge, "Memory").
		SetLabels(map[string]string{"host": "web-01"}).
		SetValue(50.0)
	m.Timestamp = now
	db.Write(m)

	evaluator := alert.NewCompositeEvaluator(db)
	rule := alert.NewCompositeRule("high_load", "High Load", "cpu > 80 AND memory > 80", model.SeverityCritical)
	evaluator.AddRule(rule)

	alerts, err := evaluator.Evaluate()
	if err != nil {
		t.Fatalf("evaluate error: %v", err)
	}

	if len(alerts) != 0 {
		t.Errorf("expected 0 alerts for AND (one condition not met), got %d", len(alerts))
	}
}

// TestCompositeEvaluatorOR 测试 OR 组合
func TestCompositeEvaluatorOR(t *testing.T) {
	db := storage.NewMemoryTSDB(24 * time.Hour)

	now := time.Now()
	db.Write(model.NewMetric("cpu", model.MetricTypeGauge, "CPU").
		SetLabels(map[string]string{"host": "web-01"}).SetValue(90.0))
	m := model.NewMetric("memory", model.MetricTypeGauge, "Memory").
		SetLabels(map[string]string{"host": "web-01"}).
		SetValue(50.0)
	m.Timestamp = now
	db.Write(m)

	evaluator := alert.NewCompositeEvaluator(db)
	rule := alert.NewCompositeRule("high_load", "High Load", "cpu > 80 OR memory > 80", model.SeverityWarning)
	evaluator.AddRule(rule)

	alerts, err := evaluator.Evaluate()
	if err != nil {
		t.Fatalf("evaluate error: %v", err)
	}

	if len(alerts) != 1 {
		t.Errorf("expected 1 alert for OR, got %d", len(alerts))
	}
}

// TestCompositeEvaluatorORNotFired 测试 OR 不触发
func TestCompositeEvaluatorORNotFired(t *testing.T) {
	db := storage.NewMemoryTSDB(24 * time.Hour)

	now := time.Now()
	db.Write(model.NewMetric("cpu", model.MetricTypeGauge, "CPU").
		SetLabels(map[string]string{"host": "web-01"}).SetValue(30.0))
	m := model.NewMetric("memory", model.MetricTypeGauge, "Memory").
		SetLabels(map[string]string{"host": "web-01"}).
		SetValue(50.0)
	m.Timestamp = now
	db.Write(m)

	evaluator := alert.NewCompositeEvaluator(db)
	rule := alert.NewCompositeRule("high_load", "High Load", "cpu > 80 OR memory > 80", model.SeverityWarning)
	evaluator.AddRule(rule)

	alerts, err := evaluator.Evaluate()
	if err != nil {
		t.Fatalf("evaluate error: %v", err)
	}

	if len(alerts) != 0 {
		t.Errorf("expected 0 alerts for OR (no condition met), got %d", len(alerts))
	}
}

// TestCompositeEvaluatorDisabled 测试禁用规则
func TestCompositeEvaluatorDisabled(t *testing.T) {
	db := storage.NewMemoryTSDB(24 * time.Hour)

	now := time.Now()
	db.Write(model.NewMetric("cpu", model.MetricTypeGauge, "CPU").
		SetLabels(map[string]string{"host": "web-01"}).SetValue(90.0))
	m := model.NewMetric("memory", model.MetricTypeGauge, "Memory").
		SetLabels(map[string]string{"host": "web-01"}).
		SetValue(90.0)
	m.Timestamp = now
	db.Write(m)

	evaluator := alert.NewCompositeEvaluator(db)
	rule := alert.NewCompositeRule("high_load", "High Load", "cpu > 80 AND memory > 80", model.SeverityCritical)
	rule.Enabled = false
	evaluator.AddRule(rule)

	alerts, err := evaluator.Evaluate()
	if err != nil {
		t.Fatalf("evaluate error: %v", err)
	}

	if len(alerts) != 0 {
		t.Errorf("expected 0 alerts for disabled rule, got %d", len(alerts))
	}
}

// TestCompositeEvaluatorComplex 测试复杂组合
func TestCompositeEvaluatorComplex(t *testing.T) {
	db := storage.NewMemoryTSDB(24 * time.Hour)

	now := time.Now()
	for _, metric := range []struct {
		name   string
		value  float64
	}{
		{"cpu", 90.0},
		{"memory", 85.0},
		{"disk", 92.0},
	} {
		m := model.NewMetric(metric.name, model.MetricTypeGauge, "metric").
			SetLabels(map[string]string{"host": "web-01"}).
			SetValue(metric.value)
		m.Timestamp = now
		db.Write(m)
	}

	evaluator := alert.NewCompositeEvaluator(db)
	rule := alert.NewCompositeRule("all_high", "All High", "cpu > 80 AND memory > 80 AND disk > 80", model.SeverityCritical)
	evaluator.AddRule(rule)

	alerts, err := evaluator.Evaluate()
	if err != nil {
		t.Fatalf("evaluate error: %v", err)
	}

	if len(alerts) != 1 {
		t.Errorf("expected 1 alert for complex AND, got %d", len(alerts))
	}
}

// TestCompositeEvaluatorMultipleRules 测试多规则
func TestCompositeEvaluatorMultipleRules(t *testing.T) {
	db := storage.NewMemoryTSDB(24 * time.Hour)

	now := time.Now()
	db.Write(model.NewMetric("cpu", model.MetricTypeGauge, "CPU").
		SetLabels(map[string]string{"host": "web-01"}).SetValue(90.0))
	m := model.NewMetric("memory", model.MetricTypeGauge, "Memory").
		SetLabels(map[string]string{"host": "web-01"}).
		SetValue(90.0)
	m.Timestamp = now
	db.Write(m)

	evaluator := alert.NewCompositeEvaluator(db)
	evaluator.AddRule(alert.NewCompositeRule("rule1", "Rule 1", "cpu > 80 AND memory > 80", model.SeverityCritical))
	evaluator.AddRule(alert.NewCompositeRule("rule2", "Rule 2", "cpu > 50 OR memory > 50", model.SeverityWarning))

	alerts, err := evaluator.Evaluate()
	if err != nil {
		t.Fatalf("evaluate error: %v", err)
	}

	if len(alerts) != 2 {
		t.Errorf("expected 2 alerts, got %d", len(alerts))
	}
}

// TestCompositeEvaluatorMissingMetric 测试缺失指标
func TestCompositeEvaluatorMissingMetric(t *testing.T) {
	db := storage.NewMemoryTSDB(24 * time.Hour)

	db.Write(model.NewMetric("cpu", model.MetricTypeGauge, "CPU").
		SetLabels(map[string]string{"host": "web-01"}).SetValue(90.0))

	evaluator := alert.NewCompositeEvaluator(db)
	rule := alert.NewCompositeRule("test", "Test", "cpu > 80 AND nonexistent > 80", model.SeverityWarning)
	evaluator.AddRule(rule)

	// 不应该 panic
	alerts, err := evaluator.Evaluate()
	if err != nil {
		t.Fatalf("evaluate error: %v", err)
	}

	if len(alerts) != 0 {
		t.Errorf("expected 0 alerts for missing metric, got %d", len(alerts))
	}
}

// TestCompositeRuleNew 测试组合规则创建
func TestCompositeRuleNew(t *testing.T) {
	rule := alert.NewCompositeRule("test", "Test", "cpu > 80 AND memory > 80", model.SeverityCritical)

	if rule.ID != "test" {
		t.Errorf("expected ID 'test', got '%s'", rule.ID)
	}
	if rule.Operator != "AND" {
		t.Errorf("expected operator 'AND', got '%s'", rule.Operator)
	}
	if !rule.Enabled {
		t.Error("expected rule to be enabled")
	}
}

// TestCompositeRuleORDetection 测试 OR 自动检测
func TestCompositeRuleORDetection(t *testing.T) {
	rule := alert.NewCompositeRule("test", "Test", "cpu > 80 OR memory > 80", model.SeverityWarning)

	if rule.Operator != "OR" {
		t.Errorf("expected operator 'OR' for OR expression, got '%s'", rule.Operator)
	}
}

// TestCompositeEvaluatorSeverity 测试告警级别
func TestCompositeEvaluatorSeverity(t *testing.T) {
	db := storage.NewMemoryTSDB(24 * time.Hour)

	now := time.Now()
	db.Write(model.NewMetric("cpu", model.MetricTypeGauge, "CPU").
		SetLabels(map[string]string{"host": "web-01"}).SetValue(90.0))
	m := model.NewMetric("memory", model.MetricTypeGauge, "Memory").
		SetLabels(map[string]string{"host": "web-01"}).
		SetValue(90.0)
	m.Timestamp = now
	db.Write(m)

	evaluator := alert.NewCompositeEvaluator(db)
	rule := alert.NewCompositeRule("test", "Test", "cpu > 80 AND memory > 80", model.SeverityCritical)
	evaluator.AddRule(rule)

	alerts, err := evaluator.Evaluate()
	if err != nil {
		t.Fatalf("evaluate error: %v", err)
	}

	if len(alerts) > 0 && alerts[0].Severity != model.SeverityCritical {
		t.Errorf("expected SeverityCritical, got %v", alerts[0].Severity)
	}
}

// TestCompositeEvaluatorMathEdgeCases 测试数学边界
func TestCompositeEvaluatorMathEdgeCases(t *testing.T) {
	db := storage.NewMemoryTSDB(24 * time.Hour)

	now := time.Now()
	db.Write(model.NewMetric("cpu", model.MetricTypeGauge, "CPU").
		SetLabels(map[string]string{"host": "web-01"}).SetValue(80.0))
	m := model.NewMetric("memory", model.MetricTypeGauge, "Memory").
		SetLabels(map[string]string{"host": "web-01"}).
		SetValue(80.0)
	m.Timestamp = now
	db.Write(m)

	evaluator := alert.NewCompositeEvaluator(db)
	// 等于边界值，> 80 应该不触发
	rule := alert.NewCompositeRule("test", "Test", "cpu > 80 AND memory > 80", model.SeverityWarning)
	evaluator.AddRule(rule)

	alerts, err := evaluator.Evaluate()
	if err != nil {
		t.Fatalf("evaluate error: %v", err)
	}

	if len(alerts) != 0 {
		t.Errorf("expected 0 alerts for boundary values with >, got %d", len(alerts))
	}
}

// TestCompositeEvaluatorConcurrent 测试并发评估
func TestCompositeEvaluatorConcurrent(t *testing.T) {
	db := storage.NewMemoryTSDB(24 * time.Hour)

	now := time.Now()
	db.Write(model.NewMetric("cpu", model.MetricTypeGauge, "CPU").
		SetLabels(map[string]string{"host": "web-01"}).SetValue(90.0))
	m := model.NewMetric("memory", model.MetricTypeGauge, "Memory").
		SetLabels(map[string]string{"host": "web-01"}).
		SetValue(90.0)
	m.Timestamp = now
	db.Write(m)

	evaluator := alert.NewCompositeEvaluator(db)
	evaluator.AddRule(alert.NewCompositeRule("test", "Test", "cpu > 80 AND memory > 80", model.SeverityWarning))

	done := make(chan bool, 10)
	for i := 0; i < 10; i++ {
		go func() {
			_, err := evaluator.Evaluate()
			if err != nil {
				t.Errorf("evaluate error: %v", err)
			}
			done <- true
		}()
	}

	for i := 0; i < 10; i++ {
		<-done
	}
}

// TestCompositeEvaluatorThreeWayOR 测试三路 OR
func TestCompositeEvaluatorThreeWayOR(t *testing.T) {
	db := storage.NewMemoryTSDB(24 * time.Hour)

	now := time.Now()
	db.Write(model.NewMetric("cpu", model.MetricTypeGauge, "CPU").
		SetLabels(map[string]string{"host": "web-01"}).SetValue(30.0))
	m := model.NewMetric("memory", model.MetricTypeGauge, "Memory").
		SetLabels(map[string]string{"host": "web-01"}).
		SetValue(90.0)
	m.Timestamp = now
	db.Write(m)
	db.Write(model.NewMetric("disk", model.MetricTypeGauge, "Disk").
		SetLabels(map[string]string{"host": "web-01"}).SetValue(30.0))

	evaluator := alert.NewCompositeEvaluator(db)
	rule := alert.NewCompositeRule("any_high", "Any High", "cpu > 80 OR memory > 80 OR disk > 80", model.SeverityWarning)
	evaluator.AddRule(rule)

	alerts, err := evaluator.Evaluate()
	if err != nil {
		t.Fatalf("evaluate error: %v", err)
	}

	if len(alerts) != 1 {
		t.Errorf("expected 1 alert for 3-way OR, got %d", len(alerts))
	}
}

// TestCompositeEvaluatorAllFalse 测试全假
func TestCompositeEvaluatorAllFalse(t *testing.T) {
	db := storage.NewMemoryTSDB(24 * time.Hour)

	now := time.Now()
	db.Write(model.NewMetric("cpu", model.MetricTypeGauge, "CPU").
		SetLabels(map[string]string{"host": "web-01"}).SetValue(10.0))
	m := model.NewMetric("memory", model.MetricTypeGauge, "Memory").
		SetLabels(map[string]string{"host": "web-01"}).
		SetValue(20.0)
	m.Timestamp = now
	db.Write(m)

	evaluator := alert.NewCompositeEvaluator(db)
	rule := alert.NewCompositeRule("test", "Test", "cpu > 80 OR memory > 80", model.SeverityWarning)
	evaluator.AddRule(rule)

	alerts, err := evaluator.Evaluate()
	if err != nil {
		t.Fatalf("evaluate error: %v", err)
	}

	if len(alerts) != 0 {
		t.Errorf("expected 0 alerts for all false conditions, got %d", len(alerts))
	}
}

// TestCompositeEvaluatorMixedOperators 测试混合运算符（应全部按 AND 处理）
func TestCompositeEvaluatorMixedOperators(t *testing.T) {
	db := storage.NewMemoryTSDB(24 * time.Hour)

	now := time.Now()
	db.Write(model.NewMetric("cpu", model.MetricTypeGauge, "CPU").
		SetLabels(map[string]string{"host": "web-01"}).SetValue(90.0))
	m := model.NewMetric("memory", model.MetricTypeGauge, "Memory").
		SetLabels(map[string]string{"host": "web-01"}).
		SetValue(90.0)
	m.Timestamp = now
	db.Write(m)

	evaluator := alert.NewCompositeEvaluator(db)
	// 包含 AND 和 OR
	rule := alert.NewCompositeRule("test", "Test", "cpu > 80 AND memory > 80 OR cpu < 50", model.SeverityWarning)
	evaluator.AddRule(rule)

	// 不应该 panic
	_, err := evaluator.Evaluate()
	if err != nil {
		t.Fatalf("evaluate error: %v", err)
	}
}
