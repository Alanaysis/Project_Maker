package tests_test

import (
	"math"
	"testing"
	"time"

	"github.com/monitoring-alert/internal/model"
	"github.com/monitoring-alert/internal/storage"
	"github.com/monitoring-alert/src/alert"
)

// TestTrendEvaluatorIncrease 测试增长趋势
func TestTrendEvaluatorIncrease(t *testing.T) {
	db := storage.NewMemoryTSDB(24 * time.Hour)

	now := time.Now()
	for i := 0; i < 20; i++ {
		m := model.NewMetric("cpu", model.MetricTypeGauge, "CPU").
			SetLabels(map[string]string{"host": "web-01"}).
			SetValue(20.0 + float64(i)*5) // 从 20 增长到 115
		m.Timestamp = now.Add(-time.Duration(20-i) * time.Second)
		db.Write(m)
	}

	evaluator := alert.NewTrendEvaluator(db)
	rule := alert.NewTrendRule("cpu_increase", "CPU Increasing", "cpu",
		alert.TrendTypeIncrease, 10, 30*time.Second, true, model.SeverityWarning)
	evaluator.AddRule(rule)

	alerts, err := evaluator.Evaluate()
	if err != nil {
		t.Fatalf("evaluate error: %v", err)
	}

	if len(alerts) == 0 {
		t.Error("expected firing alert for increasing trend")
	}
}

// TestTrendEvaluatorDecrease 测试下降趋势
func TestTrendEvaluatorDecrease(t *testing.T) {
	db := storage.NewMemoryTSDB(24 * time.Hour)

	now := time.Now()
	for i := 0; i < 20; i++ {
		m := model.NewMetric("cpu", model.MetricTypeGauge, "CPU").
			SetLabels(map[string]string{"host": "web-01"}).
			SetValue(100.0 - float64(i)*5) // 从 100 下降到 5
		m.Timestamp = now.Add(-time.Duration(20-i) * time.Second)
		db.Write(m)
	}

	evaluator := alert.NewTrendEvaluator(db)
	rule := alert.NewTrendRule("cpu_decrease", "CPU Decreasing", "cpu",
		alert.TrendTypeDecrease, 50, 30*time.Second, true, model.SeverityWarning)
	evaluator.AddRule(rule)

	alerts, err := evaluator.Evaluate()
	if err != nil {
		t.Fatalf("evaluate error: %v", err)
	}

	if len(alerts) == 0 {
		t.Error("expected firing alert for decreasing trend")
	}
}

// TestTrendEvaluatorSpike 测试尖峰检测
func TestTrendEvaluatorSpike(t *testing.T) {
	db := storage.NewMemoryTSDB(24 * time.Hour)

	now := time.Now()
	// 正常值
	for i := 0; i < 19; i++ {
		m := model.NewMetric("cpu", model.MetricTypeGauge, "CPU").
			SetLabels(map[string]string{"host": "web-01"}).
			SetValue(50.0)
		m.Timestamp = now.Add(-time.Duration(20-i) * time.Second)
		db.Write(m)
	}
	// 尖峰
	m := model.NewMetric("cpu", model.MetricTypeGauge, "CPU").
		SetLabels(map[string]string{"host": "web-01"}).
		SetValue(200.0)
	m.Timestamp = now
	db.Write(m)

	evaluator := alert.NewTrendEvaluator(db)
	rule := alert.NewTrendRule("cpu_spike", "CPU Spike", "cpu",
		alert.TrendTypeSpike, 50, 30*time.Second, true, model.SeverityCritical)
	evaluator.AddRule(rule)

	alerts, err := evaluator.Evaluate()
	if err != nil {
		t.Fatalf("evaluate error: %v", err)
	}

	if len(alerts) == 0 {
		t.Error("expected firing alert for spike")
	}
}

// TestTrendEvaluatorDisabledRule 测试禁用规则
func TestTrendEvaluatorDisabledRule(t *testing.T) {
	db := storage.NewMemoryTSDB(24 * time.Hour)

	now := time.Now()
	m := model.NewMetric("cpu", model.MetricTypeGauge, "CPU").
		SetLabels(map[string]string{"host": "web-01"}).
		SetValue(95.0)
	m.Timestamp = now
	db.Write(m)

	evaluator := alert.NewTrendEvaluator(db)
	rule := alert.NewTrendRule("cpu_spike", "CPU Spike", "cpu",
		alert.TrendTypeSpike, 10, 30*time.Second, false, model.SeverityWarning)
	evaluator.AddRule(rule)

	alerts, err := evaluator.Evaluate()
	if err != nil {
		t.Fatalf("evaluate error: %v", err)
	}

	if len(alerts) != 0 {
		t.Errorf("expected no alerts for disabled rule, got %d", len(alerts))
	}
}

// TestTrendEvaluatorNoData 测试无数据
func TestTrendEvaluatorNoData(t *testing.T) {
	db := storage.NewMemoryTSDB(24 * time.Hour)

	evaluator := alert.NewTrendEvaluator(db)
	rule := alert.NewTrendRule("cpu_spike", "CPU Spike", "cpu",
		alert.TrendTypeSpike, 10, 30*time.Second, true, model.SeverityWarning)
	evaluator.AddRule(rule)

	alerts, err := evaluator.Evaluate()
	if err != nil {
		t.Fatalf("evaluate error: %v", err)
	}

	if len(alerts) != 0 {
		t.Errorf("expected no alerts for no data, got %d", len(alerts))
	}
}

// TestTrendEvaluatorTooFewPoints 测试数据点不足
func TestTrendEvaluatorTooFewPoints(t *testing.T) {
	db := storage.NewMemoryTSDB(24 * time.Hour)

	now := time.Now()
	m := model.NewMetric("cpu", model.MetricTypeGauge, "CPU").
		SetLabels(map[string]string{"host": "web-01"}).
		SetValue(95.0)
	m.Timestamp = now
	db.Write(m)

	evaluator := alert.NewTrendEvaluator(db)
	rule := alert.NewTrendRule("cpu_spike", "CPU Spike", "cpu",
		alert.TrendTypeSpike, 10, 30*time.Second, true, model.SeverityWarning)
	evaluator.AddRule(rule)

	alerts, err := evaluator.Evaluate()
	if err != nil {
		t.Fatalf("evaluate error: %v", err)
	}

	if len(alerts) != 0 {
		t.Errorf("expected no alerts for too few points, got %d", len(alerts))
	}
}

// TestTrendRuleString 测试趋势规则字符串
func TestTrendRuleString(t *testing.T) {
	rule := alert.NewTrendRule("test", "Test", "cpu",
		alert.TrendTypeSpike, 50, 10*time.Second, true, model.SeverityWarning)

	str := rule.String()
	if str == "" {
		t.Error("expected non-empty string")
	}
}

// TestTrendEvaluatorConstantValue 测试恒定值
func TestTrendEvaluatorConstantValue(t *testing.T) {
	db := storage.NewMemoryTSDB(24 * time.Hour)

	now := time.Now()
	for i := 0; i < 20; i++ {
		m := model.NewMetric("cpu", model.MetricTypeGauge, "CPU").
			SetLabels(map[string]string{"host": "web-01"}).
			SetValue(50.0)
		m.Timestamp = now.Add(-time.Duration(20-i) * time.Second)
		db.Write(m)
	}

	evaluator := alert.NewTrendEvaluator(db)
	rule := alert.NewTrendRule("cpu_spike", "CPU Spike", "cpu",
		alert.TrendTypeSpike, 10, 30*time.Second, true, model.SeverityWarning)
	evaluator.AddRule(rule)

	alerts, err := evaluator.Evaluate()
	if err != nil {
		t.Fatalf("evaluate error: %v", err)
	}

	// 恒定值不应该触发尖峰告警
	if len(alerts) != 0 {
		t.Errorf("expected no alerts for constant value, got %d", len(alerts))
	}
}

// TestTrendEvaluatorMultipleRules 测试多趋势规则
func TestTrendEvaluatorMultipleRules(t *testing.T) {
	db := storage.NewMemoryTSDB(24 * time.Hour)

	now := time.Now()
	for i := 0; i < 20; i++ {
		m := model.NewMetric("cpu", model.MetricTypeGauge, "CPU").
			SetLabels(map[string]string{"host": "web-01"}).
			SetValue(20.0 + float64(i)*5)
		m.Timestamp = now.Add(-time.Duration(20-i) * time.Second)
		db.Write(m)
	}

	evaluator := alert.NewTrendEvaluator(db)
	evaluator.AddRule(alert.NewTrendRule("cpu_increase", "CPU Increase", "cpu",
		alert.TrendTypeIncrease, 10, 30*time.Second, true, model.SeverityWarning))
	evaluator.AddRule(alert.NewTrendRule("cpu_spike", "CPU Spike", "cpu",
		alert.TrendTypeSpike, 50, 30*time.Second, true, model.SeverityCritical))

	alerts, err := evaluator.Evaluate()
	if err != nil {
		t.Fatalf("evaluate error: %v", err)
	}

	// 应该至少触发一个规则
	if len(alerts) == 0 {
		t.Error("expected at least one alert for multiple rules")
	}
}

// TestTrendEvaluatorNegativeTrend 测试负增长
func TestTrendEvaluatorNegativeTrend(t *testing.T) {
	db := storage.NewMemoryTSDB(24 * time.Hour)

	now := time.Now()
	for i := 0; i < 20; i++ {
		m := model.NewMetric("cpu", model.MetricTypeGauge, "CPU").
			SetLabels(map[string]string{"host": "web-01"}).
			SetValue(100.0 - float64(i)*5)
		m.Timestamp = now.Add(-time.Duration(20-i) * time.Second)
		db.Write(m)
	}

	evaluator := alert.NewTrendEvaluator(db)
	rule := alert.NewTrendRule("cpu_increase", "CPU Increasing", "cpu",
		alert.TrendTypeIncrease, 10, 30*time.Second, true, model.SeverityWarning)
	evaluator.AddRule(rule)

	alerts, err := evaluator.Evaluate()
	if err != nil {
		t.Fatalf("evaluate error: %v", err)
	}

	// 负增长不应该触发增长告警
	if len(alerts) != 0 {
		t.Errorf("expected no alerts for negative trend, got %d", len(alerts))
	}
}

// TestTrendEvaluatorMathEdgeCases 测试数学边界情况
func TestTrendEvaluatorMathEdgeCases(t *testing.T) {
	db := storage.NewMemoryTSDB(24 * time.Hour)

	now := time.Now()
	// 写入交替的极高和极低值
	for i := 0; i < 20; i++ {
		value := 50.0
		if i%2 == 0 {
			value = 100.0
		} else {
			value = 0.0
		}
		m := model.NewMetric("cpu", model.MetricTypeGauge, "CPU").
			SetLabels(map[string]string{"host": "web-01"}).
			SetValue(value)
		m.Timestamp = now.Add(-time.Duration(20-i) * time.Second)
		db.Write(m)
	}

	evaluator := alert.NewTrendEvaluator(db)
	rule := alert.NewTrendRule("cpu_spike", "CPU Spike", "cpu",
		alert.TrendTypeSpike, 50, 30*time.Second, true, model.SeverityWarning)
	evaluator.AddRule(rule)

	// 不应该 panic
	_, err := evaluator.Evaluate()
	if err != nil {
		t.Fatalf("evaluate should not error: %v", err)
	}
}

// TestTrendEvaluatorPrecision 测试精度
func TestTrendEvaluatorPrecision(t *testing.T) {
	db := storage.NewMemoryTSDB(24 * time.Hour)

	now := time.Now()
	// 非常小的增长
	for i := 0; i < 20; i++ {
		m := model.NewMetric("cpu", model.MetricTypeGauge, "CPU").
			SetLabels(map[string]string{"host": "web-01"}).
			SetValue(50.0 + float64(i)*0.001)
		m.Timestamp = now.Add(-time.Duration(20-i) * time.Second)
		db.Write(m)
	}

	evaluator := alert.NewTrendEvaluator(db)
	rule := alert.NewTrendRule("cpu_increase", "CPU Increase", "cpu",
		alert.TrendTypeIncrease, 0.01, 30*time.Second, true, model.SeverityWarning)
	evaluator.AddRule(rule)

	alerts, err := evaluator.Evaluate()
	if err != nil {
		t.Fatalf("evaluate error: %v", err)
	}

	if len(alerts) == 0 {
		t.Error("expected alert for small but consistent increase")
	}
}

// TestTrendTypeConstants 测试趋势类型常量
func TestTrendTypeConstants(t *testing.T) {
	if string(alert.TrendTypeIncrease) != "increase" {
		t.Error("TrendTypeIncrease should be 'increase'")
	}
	if string(alert.TrendTypeDecrease) != "decrease" {
		t.Error("TrendTypeDecrease should be 'decrease'")
	}
	if string(alert.TrendTypeSpike) != "spike" {
		t.Error("TrendTypeSpike should be 'spike'")
	}
}

// TestTrendEvaluatorLargeWindow 测试大窗口
func TestTrendEvaluatorLargeWindow(t *testing.T) {
	db := storage.NewMemoryTSDB(24 * time.Hour)

	now := time.Now()
	for i := 0; i < 100; i++ {
		m := model.NewMetric("cpu", model.MetricTypeGauge, "CPU").
			SetLabels(map[string]string{"host": "web-01"}).
			SetValue(50.0 + float64(i)*0.5)
		m.Timestamp = now.Add(-time.Duration(100-i) * time.Second)
		db.Write(m)
	}

	evaluator := alert.NewTrendEvaluator(db)
	rule := alert.NewTrendRule("cpu_increase", "CPU Increase", "cpu",
		alert.TrendTypeIncrease, 5, 2*time.Minute, true, model.SeverityWarning)
	evaluator.AddRule(rule)

	alerts, err := evaluator.Evaluate()
	if err != nil {
		t.Fatalf("evaluate error: %v", err)
	}

	if len(alerts) == 0 {
		t.Error("expected alert for increasing trend over large window")
	}
}

// TestTrendEvaluatorMathFunctions 测试数学计算正确性
func TestTrendEvaluatorMathFunctions(t *testing.T) {
	db := storage.NewMemoryTSDB(24 * time.Hour)

	now := time.Now()
	// 创建明确的数据: 1, 2, 3, 4, 5
	values := []float64{1, 2, 3, 4, 5}
	for i := 0; i < len(values); i++ {
		m := model.NewMetric("cpu", model.MetricTypeGauge, "CPU").
			SetLabels(map[string]string{"host": "web-01"}).
			SetValue(values[i])
		m.Timestamp = now.Add(-time.Duration(len(values)-i) * time.Second)
		db.Write(m)
	}

	// 测试增长趋势: 后段平均(4+5)/2=4.5, 前段平均(1+2)/2=1.5, 差=3.0
	evaluator := alert.NewTrendEvaluator(db)
	rule := alert.NewTrendRule("test", "Test", "cpu",
		alert.TrendTypeIncrease, 2, 30*time.Second, true, model.SeverityWarning)
	evaluator.AddRule(rule)

	alerts, err := evaluator.Evaluate()
	if err != nil {
		t.Fatalf("evaluate error: %v", err)
	}

	if len(alerts) == 0 {
		t.Error("expected alert for clear increasing trend (1,2,3,4,5)")
	}
}

// TestTrendEvaluatorStddevZero 测试标准差为零
func TestTrendEvaluatorStddevZero(t *testing.T) {
	db := storage.NewMemoryTSDB(24 * time.Hour)

	now := time.Now()
	for i := 0; i < 5; i++ {
		m := model.NewMetric("cpu", model.MetricTypeGauge, "CPU").
			SetLabels(map[string]string{"host": "web-01"}).
			SetValue(50.0)
		m.Timestamp = now.Add(-time.Duration(5-i) * time.Second)
		db.Write(m)
	}

	evaluator := alert.NewTrendEvaluator(db)
	rule := alert.NewTrendRule("test", "Test", "cpu",
		alert.TrendTypeSpike, 10, 30*time.Second, true, model.SeverityWarning)
	evaluator.AddRule(rule)

	// 不应该 panic
	alerts, err := evaluator.Evaluate()
	if err != nil {
		t.Fatalf("evaluate error: %v", err)
	}

	// 恒定值不应该触发
	if len(alerts) != 0 {
		t.Errorf("expected no alerts for constant value, got %d", len(alerts))
	}
}

// TestTrendEvaluatorFloatPrecision 测试浮点精度
func TestTrendEvaluatorFloatPrecision(t *testing.T) {
	db := storage.NewMemoryTSDB(24 * time.Hour)

	now := time.Now()
	// 使用小数值
	for i := 0; i < 10; i++ {
		m := model.NewMetric("cpu", model.MetricTypeGauge, "CPU").
			SetLabels(map[string]string{"host": "web-01"}).
			SetValue(0.001 + float64(i)*0.0001)
		m.Timestamp = now.Add(-time.Duration(10-i) * time.Second)
		db.Write(m)
	}

	evaluator := alert.NewTrendEvaluator(db)
	rule := alert.NewTrendRule("test", "Test", "cpu",
		alert.TrendTypeIncrease, 0.001, 30*time.Second, true, model.SeverityWarning)
	evaluator.AddRule(rule)

	// 不应该 panic
	_, err := evaluator.Evaluate()
	if err != nil {
		t.Fatalf("evaluate error: %v", err)
	}
}

// TestTrendEvaluatorLargeValues 测试大数值
func TestTrendEvaluatorLargeValues(t *testing.T) {
	db := storage.NewMemoryTSDB(24 * time.Hour)

	now := time.Now()
	for i := 0; i < 10; i++ {
		m := model.NewMetric("cpu", model.MetricTypeGauge, "CPU").
			SetLabels(map[string]string{"host": "web-01"}).
			SetValue(1e10 + float64(i)*1e8)
		m.Timestamp = now.Add(-time.Duration(10-i) * time.Second)
		db.Write(m)
	}

	evaluator := alert.NewTrendEvaluator(db)
	rule := alert.NewTrendRule("test", "Test", "cpu",
		alert.TrendTypeIncrease, 1e8, 30*time.Second, true, model.SeverityWarning)
	evaluator.AddRule(rule)

	// 不应该 panic
	alerts, err := evaluator.Evaluate()
	if err != nil {
		t.Fatalf("evaluate error: %v", err)
	}

	// 应该有告警
	if len(alerts) == 0 {
		t.Error("expected alert for large value increase")
	}
}

// TestTrendEvaluatorNegativeValues 测试负数值
func TestTrendEvaluatorNegativeValues(t *testing.T) {
	db := storage.NewMemoryTSDB(24 * time.Hour)

	now := time.Now()
	for i := 0; i < 10; i++ {
		m := model.NewMetric("cpu", model.MetricTypeGauge, "CPU").
			SetLabels(map[string]string{"host": "web-01"}).
			SetValue(-50.0 + float64(i)*10)
		m.Timestamp = now.Add(-time.Duration(10-i) * time.Second)
		db.Write(m)
	}

	evaluator := alert.NewTrendEvaluator(db)
	rule := alert.NewTrendRule("test", "Test", "cpu",
		alert.TrendTypeIncrease, 50, 30*time.Second, true, model.SeverityWarning)
	evaluator.AddRule(rule)

	// 不应该 panic
	_, err := evaluator.Evaluate()
	if err != nil {
		t.Fatalf("evaluate error: %v", err)
	}
}

// TestTrendEvaluatorMathNaN 测试 NaN 处理
func TestTrendEvaluatorMathNaN(t *testing.T) {
	db := storage.NewMemoryTSDB(24 * time.Hour)

	now := time.Now()
	for i := 0; i < 5; i++ {
		m := model.NewMetric("cpu", model.MetricTypeGauge, "CPU").
			SetLabels(map[string]string{"host": "web-01"}).
			SetValue(50.0)
		m.Timestamp = now.Add(-time.Duration(5-i) * time.Second)
		db.Write(m)
	}

	evaluator := alert.NewTrendEvaluator(db)
	rule := alert.NewTrendRule("test", "Test", "cpu",
		alert.TrendTypeSpike, 10, 30*time.Second, true, model.SeverityWarning)
	evaluator.AddRule(rule)

	// 不应该 panic
	alerts, err := evaluator.Evaluate()
	if err != nil {
		t.Fatalf("evaluate error: %v", err)
	}

	// 恒定值不应该触发
	if len(alerts) != 0 {
		t.Errorf("expected no alerts for constant value, got %d", len(alerts))
	}
}

// TestTrendEvaluatorMathInfinite 测试无穷大处理
func TestTrendEvaluatorMathInfinite(t *testing.T) {
	db := storage.NewMemoryTSDB(24 * time.Hour)

	now := time.Now()
	for i := 0; i < 4; i++ {
		m := model.NewMetric("cpu", model.MetricTypeGauge, "CPU").
			SetLabels(map[string]string{"host": "web-01"}).
			SetValue(50.0)
		m.Timestamp = now.Add(-time.Duration(4-i) * time.Second)
		db.Write(m)
	}
	// 最后一个点设为无穷大
	m := model.NewMetric("cpu", model.MetricTypeGauge, "CPU").
		SetLabels(map[string]string{"host": "web-01"}).
		SetValue(math.Inf(1))
	m.Timestamp = now
	db.Write(m)

	evaluator := alert.NewTrendEvaluator(db)
	rule := alert.NewTrendRule("test", "Test", "cpu",
		alert.TrendTypeSpike, 10, 30*time.Second, true, model.SeverityWarning)
	evaluator.AddRule(rule)

	// 不应该 panic
	_, err := evaluator.Evaluate()
	if err != nil {
		t.Fatalf("evaluate error: %v", err)
	}
}
