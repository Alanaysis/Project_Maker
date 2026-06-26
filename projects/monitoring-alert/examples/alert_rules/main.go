package main

import (
	"fmt"
	"math/rand"
	"time"

	"github.com/monitoring-alert/internal/model"
	"github.com/monitoring-alert/internal/storage"
	"github.com/monitoring-alert/src/aggregation"
	"github.com/monitoring-alert/src/alert"
	"github.com/monitoring-alert/src/anomaly"
	"github.com/monitoring-alert/src/notifier"
)

func main() {
	fmt.Println("=== Alert Rule Configuration & Firing Demo ===")
	fmt.Println()

	// 1. 创建时序数据库
	db := storage.NewMemoryTSDB(24 * time.Hour)
	fmt.Println("[1] Time-series DB created")

	// 2. 写入模拟数据 (包含一些异常值)
	fmt.Println()
	fmt.Println("[2] Writing simulated data with anomalies...")

	// CPU 使用率 - 包含一个高值异常
	for t := 0; t < 30; t++ {
		ts := time.Now().Add(-time.Duration(30-t) * time.Second)
		value := 30.0 + rand.Float64()*30.0
		if t == 25 {
			value = 95.0 // 异常高值
		}
		m := model.NewMetric("cpu_usage", model.MetricTypeGauge, "CPU usage").
			SetLabels(map[string]string{"host": "web-01"}).
			SetValue(value)
		m.Timestamp = ts
		db.Write(m)
	}

	// 内存使用率 - 持续增长
	for t := 0; t < 30; t++ {
		ts := time.Now().Add(-time.Duration(30-t) * time.Second)
		value := float64(50 + t) // 从 50 增长到 79
		m := model.NewMetric("memory_usage", model.MetricTypeGauge, "Memory usage").
			SetLabels(map[string]string{"host": "web-01"}).
			SetValue(value)
		m.Timestamp = ts
		db.Write(m)
	}

	// 磁盘使用率
	for t := 0; t < 30; t++ {
		ts := time.Now().Add(-time.Duration(30-t) * time.Second)
		m := model.NewMetric("disk_usage", model.MetricTypeGauge, "Disk usage").
			SetLabels(map[string]string{"host": "web-01", "mount": "/"}).
			SetValue(75.0 + rand.Float64()*10.0)
		m.Timestamp = ts
		db.Write(m)
	}

	fmt.Println("  Written 30s of cpu_usage, memory_usage, disk_usage data")

	// 3. 阈值告警引擎
	fmt.Println()
	fmt.Println("[3] Threshold Alert Engine:")

	evaluator := alert.NewRuleEvaluator(db)

	// 添加阈值规则
	rules := []*model.AlertRule{
		model.NewAlertRule("cpu_high", "CPU High", "cpu_usage > 80", model.SeverityCritical).
			SetFor(0),
		model.NewAlertRule("cpu_warning", "CPU Warning", "cpu_usage > 60", model.SeverityWarning).
			SetFor(0),
		model.NewAlertRule("memory_high", "Memory High", "memory_usage > 75", model.SeverityWarning).
			SetFor(0),
		model.NewAlertRule("disk_high", "Disk High", "disk_usage > 85", model.SeverityCritical).
			SetFor(0),
	}

	for _, rule := range rules {
		evaluator.AddRule(rule)
		fmt.Printf("  Rule added: %s - %s (expr: %s, severity: %s)\n",
			rule.ID, rule.Name, rule.Expr, rule.Severity.String())
	}

	// 评估规则
	fmt.Println()
	fmt.Println("  Evaluating rules...")
	alerts, err := evaluator.Evaluate()
	if err != nil {
		fmt.Printf("  Error: %v\n", err)
	} else {
		fmt.Printf("  Found %d firing alerts:\n", len(alerts))
		for _, a := range alerts {
			fmt.Printf("    [%s] %s: %s (value=%.2f, threshold=%.2f)\n",
				a.Severity.String(), a.RuleName, a.Status, a.Value, a.Threshold)
		}
	}

	// 4. 异常检测
	fmt.Println()
	fmt.Println("[4] Anomaly Detection:")

	anomalyDetector := anomaly.NewAnomalyDetector()

	// 添加异常检测规则
	anomalyRules := []*anomaly.AnomalyRule{
		func() *anomaly.AnomalyRule {
			r := anomaly.NewAnomalyRule("cpu_anomaly", "CPU Anomaly", "cpu_usage", anomaly.DetectionDynamicThreshold)
			r.DynamicThreshold = 2.0
			r.Window = 10 * time.Second
			r.Severity = model.SeverityWarning
			return r
		}(),
		func() *anomaly.AnomalyRule {
			r := anomaly.NewAnomalyRule("cpu_zscore", "CPU Z-Score", "cpu_usage", anomaly.DetectionZScore)
			r.ZScoreThreshold = 2.0
			r.Window = 10 * time.Second
			r.Severity = model.SeverityCritical
			return r
		}(),
		func() *anomaly.AnomalyRule {
			r := anomaly.NewAnomalyRule("cpu_ewma", "CPU EWMA", "cpu_usage", anomaly.DetectionEWMA)
			r.EWMAAlpha = 0.3
			r.EWMAThreshold = 2.5
			r.Window = 10 * time.Second
			r.Severity = model.SeverityWarning
			return r
		}(),
		func() *anomaly.AnomalyRule {
			r := anomaly.NewAnomalyRule("memory_static", "Memory Static", "memory_usage", anomaly.DetectionStaticThreshold)
			r.StaticUpperBound = 85.0
			r.StaticLowerBound = 10.0
			r.Window = 10 * time.Second
			r.Severity = model.SeverityWarning
			return r
		}(),
	}

	for _, rule := range anomalyRules {
		anomalyDetector.AddRule(rule)
		fmt.Printf("  Anomaly rule: %s (type: %s)\n", rule.Name, rule.DetectionType)
	}

	// 执行异常检测
	fmt.Println()
	fmt.Println("  Detecting anomalies...")
	now := time.Now()
	ts, err := db.Read("cpu_usage", map[string]string{"host": "web-01"},
		now.Add(-10*time.Second), now)
	if err == nil {
		points := ts.GetPoints()
		anomalyResults := anomalyDetector.Detect(points, now)
		fmt.Printf("  Found %d anomalies:\n", len(anomalyResults))
		for _, ar := range anomalyResults {
			fmt.Printf("    %s: %s\n", ar.RuleName, ar.Description)
		}
	}

	// 5. 通知器
	fmt.Println()
	fmt.Println("[5] Alert Notification:")

	// 控制台通知器 (节流 1s)
	consoleNotifier := notifier.NewLogNotifier(1 * time.Second)
	fmt.Println("  Console notifier created (throttle: 1s)")

	// 创建告警管理器
	alertManager := alert.NewAlertManager(evaluator, 100)
	alertManager.AddNotifier(consoleNotifier)
	fmt.Println("  Alert manager created with console notifier")

	// 6. 告警管理器的评估和通知
	fmt.Println()
	fmt.Println("[6] Alert Manager Evaluation:")
	firingAlerts := alertManager.CheckAndNotify()
	fmt.Printf("  Manager found %d firing alerts\n", len(firingAlerts))

	// 7. 聚合函数在告警中的应用
	fmt.Println()
	fmt.Println("[7] Using Aggregation for Alert Context:")

	aggFunc := aggregation.NewAggregationFunc(db)

	// 计算所有服务器的平均 CPU
	avgResult, err := aggFunc.Aggregate("cpu_usage", map[string]string{"host": "web-01"},
		time.Now().Add(-30*time.Second), time.Now(), aggregation.AggAvg)
	if err == nil {
		fmt.Printf("  Average CPU (last 30s): %s\n", avgResult.Format(2))
	}

	// 计算 CPU 的 95 分位数
	p95Result, err := aggFunc.Aggregate("cpu_usage", map[string]string{"host": "web-01"},
		time.Now().Add(-30*time.Second), time.Now(), aggregation.AggPercentile)
	if err == nil {
		fmt.Printf("  CPU P95 (last 30s): %s\n", p95Result.Format(4))
	}

	// 计算 CPU 的标准差
	stdResult, err := aggFunc.Aggregate("cpu_usage", map[string]string{"host": "web-01"},
		time.Now().Add(-30*time.Second), time.Now(), aggregation.AggStddev)
	if err == nil {
		fmt.Printf("  CPU StdDev (last 30s): %.2f\n", stdResult.Value)
	}

	fmt.Println()
	fmt.Println("=== Demo Complete ===")
}
