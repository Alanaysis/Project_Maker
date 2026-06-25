package main

import (
	"context"
	"fmt"
	"os"
	"os/signal"
	"syscall"
	"time"

	"github.com/monitoring-alert/internal/alert"
	"github.com/monitoring-alert/internal/collector"
	"github.com/monitoring-alert/internal/model"
	"github.com/monitoring-alert/internal/notifier"
	"github.com/monitoring-alert/internal/storage"
)

func main() {
	fmt.Println("=== 高级监控告警示例（趋势告警 + 组合告警）===")

	// 创建上下文
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()

	// 1. 创建时序数据库
	db := storage.NewMemoryTSDB(1 * time.Hour)

	// 2. 创建系统采集器
	systemCollector := collector.NewSystemCollector(3 * time.Second)
	if err := systemCollector.Start(ctx); err != nil {
		fmt.Printf("Failed to start collector: %v\n", err)
		os.Exit(1)
	}
	fmt.Println("Collector started")

	// 3. 创建阈值规则评估器
	evaluator := alert.NewRuleEvaluator(db)
	rules := []*model.AlertRule{
		model.NewAlertRule("cpu_critical", "CPU 使用率严重", "cpu_usage > 80", model.SeverityCritical),
	}
	for _, rule := range rules {
		evaluator.AddRule(rule)
		fmt.Printf("Added threshold rule: %s\n", rule.Name)
	}

	// 4. 创建趋势规则评估器
	trendEval := alert.NewTrendEvaluator(db)
	trendRules := []*alert.TrendRule{
		alert.NewTrendRule("cpu_spike", "CPU 突增", "cpu_usage", alert.TrendTypeSpike, 30.0, 1*time.Minute, true, model.SeverityWarning),
		alert.NewTrendRule("memory_increase", "内存持续增长", "memory_usage", alert.TrendTypeIncrease, 20.0, 2*time.Minute, true, model.SeverityWarning),
	}
	for _, rule := range trendRules {
		trendEval.AddRule(rule)
		fmt.Printf("Added trend rule: %s (%s)\n", rule.Name, rule.TrendType)
	}

	// 5. 创建组合规则评估器
	compositeEval := alert.NewCompositeEvaluator(db)
	compositeRules := []*alert.CompositeRule{
		alert.NewCompositeRule("cpu_memory_high", "CPU 和内存同时过高", "cpu_usage > 60 AND memory_usage > 70", model.SeverityCritical),
	}
	for _, rule := range compositeRules {
		if err := compositeEval.AddRule(rule); err != nil {
			fmt.Printf("Failed to add composite rule: %v\n", err)
		} else {
			fmt.Printf("Added composite rule: %s\n", rule.Name)
		}
	}

	// 6. 创建通知器
	logNotifier := notifier.NewLogNotifier(100)

	// 7. 创建告警管理器
	alertMgr := alert.NewAlertManager(evaluator, 500)
	alertMgr.AddNotifier(logNotifier)

	// 8. 主循环
	go func() {
		ticker := time.NewTicker(5 * time.Second)
		defer ticker.Stop()

		for {
			select {
			case <-ctx.Done():
				return
			case <-ticker.C:
				// 采集指标
				metrics, err := systemCollector.Collect()
				if err != nil {
					continue
				}

				// 存储指标
				for _, m := range metrics {
					db.Write(m)
				}

				// 检查阈值告警
				alertMgr.CheckAndNotify()

				// 检查趋势告警
				trendAlerts, _ := trendEval.Evaluate()
				for _, a := range trendAlerts {
					fmt.Printf("[TREND] %s: %s (value=%.2f)\n", a.Severity, a.RuleName, a.Value)
				}

				// 检查组合告警
				compositeAlerts, _ := compositeEval.Evaluate()
				for _, a := range compositeAlerts {
					fmt.Printf("[COMPOSITE] %s: %s (value=%.2f)\n", a.Severity, a.RuleName, a.Value)
				}

				// 打印状态
				fmt.Printf("[%s] Points: %d, Threshold Alerts: %d, Trend Alerts: %d, Composite Alerts: %d\n",
					time.Now().Format("15:04:05"),
					db.GetPointCount(),
					len(alertMgr.GetActiveAlerts()),
					len(trendEval.GetActiveAlerts()),
					len(compositeEval.GetActiveAlerts()))
			}
		}
	}()

	// 9. 等待信号
	sigCh := make(chan os.Signal, 1)
	signal.Notify(sigCh, syscall.SIGINT, syscall.SIGTERM)

	fmt.Println("Advanced monitoring started. Press Ctrl+C to stop.")
	<-sigCh

	fmt.Println("\nShutting down...")
	cancel()
	systemCollector.Stop()
	fmt.Println("Done.")
}
