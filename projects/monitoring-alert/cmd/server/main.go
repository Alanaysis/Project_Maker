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

	// 创建查询引擎
	queryEngine := storage.NewQueryEngine(db)

	// 创建规则评估器
	evaluator := alert.NewRuleEvaluator(db)

	// 添加告警规则
	rules := []*model.AlertRule{
		model.NewAlertRule("cpu_high", "CPU 使用率过高", "cpu_usage > 70", model.SeverityWarning),
		model.NewAlertRule("memory_high", "内存使用率过高", "memory_usage > 80", model.SeverityCritical),
		model.NewAlertRule("disk_high", "磁盘使用率过高", "disk_usage > 90", model.SeverityCritical),
	}

	for _, rule := range rules {
		if err := evaluator.AddRule(rule); err != nil {
			fmt.Printf("Failed to add rule %s: %v\n", rule.Name, err)
		} else {
			fmt.Printf("Added rule: %s\n", rule.Name)
		}
	}

	// 创建通知器
	logNotifier := notifier.NewLogNotifier(100)
	webhookNotifier := notifier.NewWebhookNotifier("http://localhost:8080/webhook", 100)

	// 创建告警管理器
	alertMgr := alert.NewAlertManager(evaluator, 1000)
	alertMgr.AddNotifier(logNotifier)
	alertMgr.AddNotifier(webhookNotifier)

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

				// 检查告警
				if err := alertMgr.CheckAndNotify(); err != nil {
					fmt.Printf("Failed to check alerts: %v\n", err)
				}

				// 打印状态
				fmt.Printf("[%s] Metrics: %d, Active Alerts: %d\n",
					time.Now().Format(time.RFC3339),
					db.GetPointCount(),
					len(alertMgr.GetActiveAlerts()))
			}
		}
	}()

	// 启动 HTTP API 服务器（简化版本）
	go func() {
		ticker := time.NewTicker(30 * time.Second)
		defer ticker.Stop()

		for {
			select {
			case <-ctx.Done():
				return
			case <-ticker.C:
				// 打印查询结果示例
				if results, err := queryEngine.SimpleQuery("cpu_usage", 5*time.Minute); err == nil {
					for _, ts := range results {
						if point, ok := ts.Latest(); ok {
							fmt.Printf("[QUERY] cpu_usage latest: %.2f\n", point.Value)
						}
					}
				}

				// 打印活跃告警
				activeAlerts := alertMgr.GetActiveAlerts()
				if len(activeAlerts) > 0 {
					fmt.Printf("[ALERTS] Active alerts: %d\n", len(activeAlerts))
					for _, a := range activeAlerts {
						fmt.Printf("  - %s\n", a.String())
					}
				}
			}
		}
	}()

	// 等待信号
	sigCh := make(chan os.Signal, 1)
	signal.Notify(sigCh, syscall.SIGINT, syscall.SIGTERM)

	fmt.Println("Monitoring Alert System is running. Press Ctrl+C to stop.")
	<-sigCh

	fmt.Println("\nShutting down...")
	cancel()

	// 停止采集器
	if err := collectorMgr.Stop(); err != nil {
		fmt.Printf("Failed to stop collectors: %v\n", err)
	}

	fmt.Println("Monitoring Alert System stopped.")
}
