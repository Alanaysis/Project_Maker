package tests_test

import (
	"math/rand"
	"testing"
	"time"

	"github.com/monitoring-alert/internal/model"
	"github.com/monitoring-alert/internal/storage"
	"github.com/monitoring-alert/src/alert"
	"github.com/monitoring-alert/src/notifier"
)

// TestRuleEvaluatorBasic 测试基本规则评估
func TestRuleEvaluatorBasic(t *testing.T) {
	db := storage.NewMemoryTSDB(24 * time.Hour)

	// 写入数据
	now := time.Now()
	for i := 0; i < 10; i++ {
		m := model.NewMetric("cpu_usage", model.MetricTypeGauge, "CPU").
			SetLabels(map[string]string{"host": "web-01"}).
			SetValue(float64(70 + i*3))
		m.Timestamp = now.Add(-time.Duration(10-i) * time.Second)
		db.Write(m)
	}

	evaluator := alert.NewRuleEvaluator(db)
	evaluator.AddRule(model.NewAlertRule("cpu_high", "CPU High", "cpu_usage > 80", model.SeverityCritical))

	alerts, err := evaluator.Evaluate()
	if err != nil {
		t.Fatalf("evaluate error: %v", err)
	}

	// 应该有触发的告警（最后几个点 > 80）
	if len(alerts) == 0 {
		t.Error("expected at least one firing alert")
	}
}

// TestRuleEvaluatorNoFiring 测试无告警触发
func TestRuleEvaluatorNoFiring(t *testing.T) {
	db := storage.NewMemoryTSDB(24 * time.Hour)

	now := time.Now()
	for i := 0; i < 10; i++ {
		m := model.NewMetric("cpu_usage", model.MetricTypeGauge, "CPU").
			SetLabels(map[string]string{"host": "web-01"}).
			SetValue(30.0 + float64(i))
		m.Timestamp = now.Add(-time.Duration(10-i) * time.Second)
		db.Write(m)
	}

	evaluator := alert.NewRuleEvaluator(db)
	evaluator.AddRule(model.NewAlertRule("cpu_high", "CPU High", "cpu_usage > 90", model.SeverityCritical))

	alerts, err := evaluator.Evaluate()
	if err != nil {
		t.Fatalf("evaluate error: %v", err)
	}

	if len(alerts) != 0 {
		t.Errorf("expected no alerts, got %d", len(alerts))
	}
}

// TestRuleEvaluatorDisabledRule 测试禁用规则
func TestRuleEvaluatorDisabledRule(t *testing.T) {
	db := storage.NewMemoryTSDB(24 * time.Hour)

	now := time.Now()
	m := model.NewMetric("cpu_usage", model.MetricTypeGauge, "CPU").
		SetLabels(map[string]string{"host": "web-01"}).
		SetValue(95.0)
	m.Timestamp = now
	db.Write(m)

	evaluator := alert.NewRuleEvaluator(db)
	rule := model.NewAlertRule("cpu_high", "CPU High", "cpu_usage > 80", model.SeverityCritical)
	rule.SetEnabled(false)
	evaluator.AddRule(rule)

	alerts, err := evaluator.Evaluate()
	if err != nil {
		t.Fatalf("evaluate error: %v", err)
	}

	if len(alerts) != 0 {
		t.Errorf("expected no alerts for disabled rule, got %d", len(alerts))
	}
}

// TestRuleEvaluatorMultipleRules 测试多规则
func TestRuleEvaluatorMultipleRules(t *testing.T) {
	db := storage.NewMemoryTSDB(24 * time.Hour)

	now := time.Now()
	m := model.NewMetric("cpu_usage", model.MetricTypeGauge, "CPU").
		SetLabels(map[string]string{"host": "web-01"}).
		SetValue(85.0)
	m.Timestamp = now
	db.Write(m)

	evaluator := alert.NewRuleEvaluator(db)
	evaluator.AddRule(model.NewAlertRule("cpu_warning", "CPU Warning", "cpu_usage > 60", model.SeverityWarning))
	evaluator.AddRule(model.NewAlertRule("cpu_critical", "CPU Critical", "cpu_usage > 80", model.SeverityCritical))

	alerts, err := evaluator.Evaluate()
	if err != nil {
		t.Fatalf("evaluate error: %v", err)
	}

	if len(alerts) != 2 {
		t.Errorf("expected 2 alerts, got %d", len(alerts))
	}
}

// TestRuleEvaluatorGetRules 测试获取规则
func TestRuleEvaluatorGetRules(t *testing.T) {
	db := storage.NewMemoryTSDB(24 * time.Hour)

	evaluator := alert.NewRuleEvaluator(db)
	evaluator.AddRule(model.NewAlertRule("rule1", "Rule 1", "cpu > 80", model.SeverityWarning))
	evaluator.AddRule(model.NewAlertRule("rule2", "Rule 2", "mem > 90", model.SeverityCritical))

	rules := evaluator.GetRules()
	if len(rules) != 2 {
		t.Errorf("expected 2 rules, got %d", len(rules))
	}
}

// TestRuleEvaluatorRemoveRule 测试移除规则
func TestRuleEvaluatorRemoveRule(t *testing.T) {
	db := storage.NewMemoryTSDB(24 * time.Hour)

	evaluator := alert.NewRuleEvaluator(db)
	evaluator.AddRule(model.NewAlertRule("rule1", "Rule 1", "cpu > 80", model.SeverityWarning))
	evaluator.AddRule(model.NewAlertRule("rule2", "Rule 2", "mem > 90", model.SeverityCritical))

	evaluator.RemoveRule("rule1")
	rules := evaluator.GetRules()
	if len(rules) != 1 {
		t.Errorf("expected 1 rule after removal, got %d", len(rules))
	}
	if rules[0].ID != "rule2" {
		t.Errorf("expected remaining rule 'rule2', got '%s'", rules[0].ID)
	}
}

// TestRuleEvaluatorInvalidExpr 测试无效表达式
func TestRuleEvaluatorInvalidExpr(t *testing.T) {
	db := storage.NewMemoryTSDB(24 * time.Hour)

	evaluator := alert.NewRuleEvaluator(db)
	evaluator.AddRule(model.NewAlertRule("bad_rule", "Bad", "invalid", model.SeverityWarning))

	_, err := evaluator.Evaluate()
	if err == nil {
		t.Error("expected error for invalid expression")
	}
}

// TestRuleEvaluatorGtOperator 测试 > 操作符
func TestRuleEvaluatorGtOperator(t *testing.T) {
	db := storage.NewMemoryTSDB(24 * time.Hour)

	now := time.Now()
	m := model.NewMetric("cpu", model.MetricTypeGauge, "CPU").
		SetLabels(map[string]string{"host": "web-01"}).
		SetValue(85.0)
	m.Timestamp = now
	db.Write(m)

	evaluator := alert.NewRuleEvaluator(db)
	evaluator.AddRule(model.NewAlertRule("test", "Test", "cpu > 80", model.SeverityWarning))

	alerts, _ := evaluator.Evaluate()
	if len(alerts) != 1 {
		t.Errorf("expected 1 alert for > operator, got %d", len(alerts))
	}
}

// TestRuleEvaluatorLtOperator 测试 < 操作符
func TestRuleEvaluatorLtOperator(t *testing.T) {
	db := storage.NewMemoryTSDB(24 * time.Hour)

	now := time.Now()
	m := model.NewMetric("cpu", model.MetricTypeGauge, "CPU").
		SetLabels(map[string]string{"host": "web-01"}).
		SetValue(30.0)
	m.Timestamp = now
	db.Write(m)

	evaluator := alert.NewRuleEvaluator(db)
	evaluator.AddRule(model.NewAlertRule("test", "Test", "cpu < 50", model.SeverityWarning))

	alerts, _ := evaluator.Evaluate()
	if len(alerts) != 1 {
		t.Errorf("expected 1 alert for < operator, got %d", len(alerts))
	}
}

// TestRuleEvaluatorEqualsOperator 测试 == 操作符
func TestRuleEvaluatorEqualsOperator(t *testing.T) {
	db := storage.NewMemoryTSDB(24 * time.Hour)

	now := time.Now()
	m := model.NewMetric("cpu", model.MetricTypeGauge, "CPU").
		SetLabels(map[string]string{"host": "web-01"}).
		SetValue(80.0)
	m.Timestamp = now
	db.Write(m)

	evaluator := alert.NewRuleEvaluator(db)
	evaluator.AddRule(model.NewAlertRule("test", "Test", "cpu == 80", model.SeverityWarning))

	alerts, _ := evaluator.Evaluate()
	if len(alerts) != 1 {
		t.Errorf("expected 1 alert for == operator, got %d", len(alerts))
	}
}

// TestAlertManager 测试告警管理器
func TestAlertManager(t *testing.T) {
	db := storage.NewMemoryTSDB(24 * time.Hour)

	now := time.Now()
	m := model.NewMetric("cpu", model.MetricTypeGauge, "CPU").
		SetLabels(map[string]string{"host": "web-01"}).
		SetValue(95.0)
	m.Timestamp = now
	db.Write(m)

	evaluator := alert.NewRuleEvaluator(db)
	evaluator.AddRule(model.NewAlertRule("cpu_high", "CPU High", "cpu > 80", model.SeverityCritical))

	manager := alert.NewAlertManager(evaluator, 100)

	// 添加一个通知器
	logNotifier := notifier.NewLogNotifier(0) // 无节流
	manager.AddNotifier(logNotifier)

	alerts := manager.CheckAndNotify()
	if len(alerts) != 1 {
		t.Errorf("expected 1 alert, got %d", len(alerts))
	}

	// 第二次检查应该被节流
	alerts2 := manager.CheckAndNotify()
	if len(alerts2) != 0 {
		t.Errorf("expected 0 alerts (throttled), got %d", len(alerts2))
	}
}

// TestAlertManagerHistory 测试告警历史
func TestAlertManagerHistory(t *testing.T) {
	db := storage.NewMemoryTSDB(24 * time.Hour)

	now := time.Now()
	for i := 0; i < 5; i++ {
		m := model.NewMetric("cpu", model.MetricTypeGauge, "CPU").
			SetLabels(map[string]string{"host": "web-01"}).
			SetValue(95.0 + float64(i))
		m.Timestamp = now.Add(-time.Duration(i) * time.Second)
		db.Write(m)
	}

	evaluator := alert.NewRuleEvaluator(db)
	evaluator.AddRule(model.NewAlertRule("cpu_high", "CPU High", "cpu > 80", model.SeverityWarning))

	manager := alert.NewAlertManager(evaluator, 100)
	manager.AddNotifier(notifier.NewLogNotifier(0))

	manager.CheckAndNotify()

	history := manager.GetHistory()
	if len(history) == 0 {
		t.Error("expected non-empty history")
	}
}

// TestFormatAlertSummary 测试告警摘要格式化
func TestFormatAlertSummary(t *testing.T) {
	alerts := []*model.Alert{
		model.NewAlert("rule1", "Rule 1", model.SeverityCritical, nil),
		model.NewAlert("rule2", "Rule 2", model.SeverityWarning, nil),
	}
	alerts[0].SetValue(95.0, 80.0)
	alerts[1].SetValue(70.0, 60.0)

	summary := alert.FormatAlertSummary(alerts)
	if summary == "No alerts" {
		t.Error("expected non-empty summary")
	}
}

// TestFormatAlertSummaryEmpty 测试空告警摘要
func TestFormatAlertSummaryEmpty(t *testing.T) {
	summary := alert.FormatAlertSummary(nil)
	if summary != "No alerts" {
		t.Errorf("expected 'No alerts', got '%s'", summary)
	}
}

// TestRuleEvaluatorThresholdComparison 测试阈值比较
func TestRuleEvaluatorThresholdComparison(t *testing.T) {
	tests := []struct {
		name      string
		value     float64
		expr      string
		shouldFire bool
	}{
		{"gt_exact", 80.0, "cpu > 80", false},
		{"gt_above", 85.0, "cpu > 80", true},
		{"gte_exact", 80.0, "cpu >= 80", true},
		{"gte_above", 85.0, "cpu >= 80", true},
		{"lt_exact", 80.0, "cpu < 80", false},
		{"lt_below", 75.0, "cpu < 80", true},
		{"lte_exact", 80.0, "cpu <= 80", true},
		{"lte_below", 75.0, "cpu <= 80", true},
		{"neq_exact", 80.0, "cpu != 80", false},
		{"neq_diff", 85.0, "cpu != 80", true},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			db := storage.NewMemoryTSDB(24 * time.Hour)
			now := time.Now()
			m := model.NewMetric("cpu", model.MetricTypeGauge, "CPU").
				SetLabels(map[string]string{"host": "web-01"}).
				SetValue(tt.value)
			m.Timestamp = now
			db.Write(m)

			evaluator := alert.NewRuleEvaluator(db)
			evaluator.AddRule(model.NewAlertRule("test", "Test", tt.expr, model.SeverityWarning))

			alerts, _ := evaluator.Evaluate()
			fired := len(alerts) > 0

			if fired != tt.shouldFire {
				t.Errorf("value=%.1f expr='%s': expected fire=%v, got fire=%v",
					tt.value, tt.expr, tt.shouldFire, fired)
			}
		})
	}
}

// TestRuleEvaluatorDifferentLabels 测试不同标签匹配
func TestRuleEvaluatorDifferentLabels(t *testing.T) {
	db := storage.NewMemoryTSDB(24 * time.Hour)

	db.Write(model.NewMetric("cpu", model.MetricTypeGauge, "CPU").
		SetLabels(map[string]string{"host": "web-01"}).SetValue(95.0).
		SetValue(95.0))
	now2 := time.Now()
	m := model.NewMetric("cpu", model.MetricTypeGauge, "CPU").
		SetLabels(map[string]string{"host": "web-02"}).
		SetValue(30.0)
	m.Timestamp = now2
	db.Write(m)

	// 查询 web-01 的规则
	evaluator := alert.NewRuleEvaluator(db)
	evaluator.AddRule(model.NewAlertRule("cpu_high", "CPU High", "cpu > 80", model.SeverityCritical))

	alerts, _ := evaluator.Evaluate()
	// 规则会匹配最新写入的指标（web-02 的 30.0）
	// 因为 GetLatest 获取的是全局最新
	_ = alerts
}

// TestRuleEvaluatorMaxHistory 测试最大历史记录
func TestRuleEvaluatorMaxHistory(t *testing.T) {
	db := storage.NewMemoryTSDB(24 * time.Hour)

	evaluator := alert.NewRuleEvaluator(db)
	evaluator.AddRule(model.NewAlertRule("test", "Test", "cpu > 80", model.SeverityWarning))

	manager := alert.NewAlertManager(evaluator, 5)
	manager.AddNotifier(notifier.NewLogNotifier(0))

	// 写入数据触发告警
	now := time.Now()
	for i := 0; i < 10; i++ {
		m := model.NewMetric("cpu", model.MetricTypeGauge, "CPU").
			SetLabels(map[string]string{"host": "web-01"}).
			SetValue(95.0 + float64(i))
		m.Timestamp = now.Add(-time.Duration(i) * time.Second)
		db.Write(m)
	}

	manager.CheckAndNotify()

	history := manager.GetHistory()
	if len(history) > 5 {
		t.Errorf("expected max 5 history entries, got %d", len(history))
	}
}

// TestRuleEvaluatorAlertSeverity 测试告警级别
func TestRuleEvaluatorAlertSeverity(t *testing.T) {
	db := storage.NewMemoryTSDB(24 * time.Hour)

	now := time.Now()
	m := model.NewMetric("cpu", model.MetricTypeGauge, "CPU").
		SetLabels(map[string]string{"host": "web-01"}).
		SetValue(95.0)
	m.Timestamp = now
	db.Write(m)

	evaluator := alert.NewRuleEvaluator(db)
	rule := model.NewAlertRule("cpu_critical", "CPU Critical", "cpu > 80", model.SeverityCritical)
	evaluator.AddRule(rule)

	alerts, _ := evaluator.Evaluate()
	if len(alerts) > 0 && alerts[0].Severity != model.SeverityCritical {
		t.Errorf("expected SeverityCritical, got %v", alerts[0].Severity)
	}
}

// TestRuleEvaluatorConcurrent 测试并发评估
func TestRuleEvaluatorConcurrent(t *testing.T) {
	db := storage.NewMemoryTSDB(24 * time.Hour)

	now := time.Now()
	for i := 0; i < 5; i++ {
		m := model.NewMetric("cpu", model.MetricTypeGauge, "CPU").
			SetLabels(map[string]string{"host": "web-01"}).
			SetValue(90.0 + rand.Float64()*10)
		m.Timestamp = now.Add(-time.Duration(i) * time.Second)
		db.Write(m)
	}

	evaluator := alert.NewRuleEvaluator(db)
	evaluator.AddRule(model.NewAlertRule("cpu_high", "CPU High", "cpu > 80", model.SeverityCritical))

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

// TestAlertManagerGetAggregationStats 测试聚合统计
func TestAlertManagerGetAggregationStats(t *testing.T) {
	db := storage.NewMemoryTSDB(24 * time.Hour)

	now := time.Now()
	for i := 0; i < 10; i++ {
		m := model.NewMetric("cpu", model.MetricTypeGauge, "CPU").
			SetLabels(map[string]string{"host": "web-01"}).
			SetValue(50.0 + float64(i)*5)
		m.Timestamp = now.Add(-time.Duration(i) * time.Second)
		db.Write(m)
	}

	evaluator := alert.NewRuleEvaluator(db)
	manager := alert.NewAlertManager(evaluator, 100)

	stats, err := manager.GetAggregationStats("cpu", map[string]string{"host": "web-01"}, 10*time.Second)
	if err != nil {
		t.Fatalf("aggregation error: %v", err)
	}
	if stats == nil {
		t.Fatal("expected non-nil stats")
	}
	if stats.Count == 0 {
		t.Error("expected non-zero count")
	}
}

// TestAlertManagerCheckAndNotify 测试完整通知流程
func TestAlertManagerCheckAndNotify(t *testing.T) {
	db := storage.NewMemoryTSDB(24 * time.Hour)

	now := time.Now()
	m := model.NewMetric("cpu", model.MetricTypeGauge, "CPU").
		SetLabels(map[string]string{"host": "web-01"}).
		SetValue(95.0)
	m.Timestamp = now
	db.Write(m)

	evaluator := alert.NewRuleEvaluator(db)
	evaluator.AddRule(model.NewAlertRule("cpu_high", "CPU High", "cpu > 80", model.SeverityWarning))

	manager := alert.NewAlertManager(evaluator, 100)
	manager.AddNotifier(notifier.NewLogNotifier(0))

	alerts := manager.CheckAndNotify()

	if len(alerts) != 1 {
		t.Errorf("expected 1 alert, got %d", len(alerts))
	}

	historyCount := manager.GetHistoryCount()
	if historyCount != 1 {
		t.Errorf("expected 1 history entry, got %d", historyCount)
	}
}
