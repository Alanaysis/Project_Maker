package main

import (
	"context"
	"fmt"
	"os"
	"os/signal"
	"syscall"
	"time"

	"github.com/monitoring-alert/internal/alert"
	"github.com/monitoring-alert/internal/api"
	"github.com/monitoring-alert/internal/collector"
	"github.com/monitoring-alert/internal/model"
	"github.com/monitoring-alert/internal/notifier"
	"github.com/monitoring-alert/internal/storage"
)

func main() {
	fmt.Println("Starting Monitoring Alert System...")

	// 创建上下文
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()

	// 创建时序数据库
	db := storage.NewMemoryTSDB(24 * time.Hour)

	// 创建采集器管理器
	collectorMgr := collector.NewCollectorManager()

	// 注册系统采集器
	systemCollector := collector.NewSystemCollector(5 * time.Second)
	collectorMgr.Register(systemCollector)

	// 启动采集器
	if err := collectorMgr.Start(ctx); err != nil {
		fmt.Printf("Failed to start collectors: %v\n", err)
		os.Exit(1)
	}
	fmt.Println("Collectors started")

	// 创建阈值规则评估器
	evaluator := alert.NewRuleEvaluator(db)

	// 添加阈值告警规则
	rules := []*model.AlertRule{
		model.NewAlertRule("cpu_high", "CPU 使用率过高", "cpu_usage > 70", model.SeverityWarning),
		model.NewAlertRule("memory_high", "内存使用率过高", "memory_usage > 80", model.SeverityCritical),
		model.NewAlertRule("disk_high", "磁盘使用率过高", "disk_usage > 90", model.SeverityCritical),
	}

	for _, rule := range rules {
		if err := evaluator.AddRule(rule); err != nil {
			fmt.Printf("Failed to add rule %s: %v\n", rule.Name, err)
		} else {
			fmt.Printf("Added threshold rule: %s\n", rule.Name)
		}
	}

	// 创建趋势规则评估器
	trendEval := alert.NewTrendEvaluator(db)

	// 添加趋势告警规则
	trendRules := []*alert.TrendRule{
		alert.NewTrendRule("cpu_spike", "CPU 使用率突增", "cpu_usage", alert.TrendTypeSpike, 50.0, 5*time.Minute, true, model.SeverityWarning),
		alert.NewTrendRule("memory_increase", "内存使用率持续增长", "memory_usage", alert.TrendTypeIncrease, 20.0, 10*time.Minute, true, model.SeverityWarning),
	}

	for _, rule := range trendRules {
		trendEval.AddRule(rule)
		fmt.Printf("Added trend rule: %s\n", rule.Name)
	}

	// 创建组合规则评估器
	compositeEval := alert.NewCompositeEvaluator(db)

	// 添加组合告警规则
	compositeRules := []*alert.CompositeRule{
		alert.NewCompositeRule("cpu_memory_high", "CPU 和内存同时过高", "cpu_usage > 70 AND memory_usage > 80", model.SeverityCritical),
		alert.NewCompositeRule("disk_or_memory_high", "磁盘或内存过高", "disk_usage > 90 OR memory_usage > 85", model.SeverityWarning),
	}

	for _, rule := range compositeRules {
		if err := compositeEval.AddRule(rule); err != nil {
			fmt.Printf("Failed to add composite rule %s: %v\n", rule.Name, err)
		} else {
			fmt.Printf("Added composite rule: %s\n", rule.Name)
		}
	}

	// 创建通知器
	logNotifier := notifier.NewLogNotifier(100)
	webhookNotifier := notifier.NewWebhookNotifier("http://localhost:8080/webhook", 100)

	// 创建告警管理器
	alertMgr := alert.NewAlertManager(evaluator, 1000)
	alertMgr.AddNotifier(logNotifier)
	alertMgr.AddNotifier(webhookNotifier)

	// 创建 HTTP API 服务器
	apiServer := api.NewServer(":8080", db, collectorMgr, evaluator, trendEval, compositeEval, alertMgr)
	if err := apiServer.Start(); err != nil {
		fmt.Printf("Failed to start API server: %v\n", err)
		os.Exit(1)
	}
	fmt.Println("HTTP API server started on :8080")

	// 启动数据采集和告警检查循环
	go func() {
		ticker := time.NewTicker(10 * time.Second)
		defer ticker.Stop()

		for {
			select {
			case <-ctx.Done():
				return
			case <-ticker.C:
				// 采集指标
				metrics, err := collectorMgr.CollectAll()
				if err != nil {
					fmt.Printf("Failed to collect metrics: %v\n", err)
					continue
				}

				// 存储指标
				for _, m := range metrics {
					if err := db.Write(m); err != nil {
						fmt.Printf("Failed to write metric: %v\n", err)
					}
				}

				// 检查阈值告警
				if err := alertMgr.CheckAndNotify(); err != nil {
					fmt.Printf("Failed to check threshold alerts: %v\n", err)
				}

				// 检查趋势告警
				trendAlerts, err := trendEval.Evaluate()
				if err != nil {
					fmt.Printf("Failed to evaluate trend rules: %v\n", err)
				} else if len(trendAlerts) > 0 {
					for _, a := range trendAlerts {
						fmt.Printf("[TREND ALERT] %s: %s (value=%.2f, threshold=%.2f)\n",
							a.Severity, a.RuleName, a.Value, a.Threshold)
					}
				}

				// 检查组合告警
				compositeAlerts, err := compositeEval.Evaluate()
				if err != nil {
					fmt.Printf("Failed to evaluate composite rules: %v\n", err)
				} else if len(compositeAlerts) > 0 {
					for _, a := range compositeAlerts {
						fmt.Printf("[COMPOSITE ALERT] %s: %s (value=%.2f, threshold=%.2f)\n",
							a.Severity, a.RuleName, a.Value, a.Threshold)
					}
				}

				// 打印状态
				fmt.Printf("[%s] Metrics: %d, Active Alerts: %d\n",
					time.Now().Format(time.RFC3339),
					db.GetPointCount(),
					len(alertMgr.GetActiveAlerts()))
			}
		}
	}()

	// 等待信号
	sigCh := make(chan os.Signal, 1)
	signal.Notify(sigCh, syscall.SIGINT, syscall.SIGTERM)

	fmt.Println("Monitoring Alert System is running. Press Ctrl+C to stop.")
	fmt.Println("API endpoints:")
	fmt.Println("  GET  /api/v1/health          - Health check")
	fmt.Println("  GET  /api/v1/metrics          - List metrics")
	fmt.Println("  GET  /api/v1/metrics/query    - Query metric")
	fmt.Println("  GET  /api/v1/alerts           - List alerts")
	fmt.Println("  GET  /api/v1/alerts/rules     - List threshold rules")
	fmt.Println("  POST /api/v1/alerts/rules     - Add threshold rule")
	fmt.Println("  GET  /api/v1/alerts/trend-rules     - List trend rules")
	fmt.Println("  POST /api/v1/alerts/trend-rules     - Add trend rule")
	fmt.Println("  GET  /api/v1/alerts/composite-rules - List composite rules")
	fmt.Println("  POST /api/v1/alerts/composite-rules - Add composite rule")
	fmt.Println("  GET  /api/v1/collectors       - List collectors")

	<-sigCh

	fmt.Println("\nShutting down...")
	cancel()

	// 停止 API 服务器
	if err := apiServer.Stop(); err != nil {
		fmt.Printf("Failed to stop API server: %v\n", err)
	}

	// 停止采集器
	if err := collectorMgr.Stop(); err != nil {
		fmt.Printf("Failed to stop collectors: %v\n", err)
	}

	fmt.Println("Monitoring Alert System stopped.")
}
