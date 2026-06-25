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
	fmt.Println("=== 基本监控告警示例 ===")

	// 创建上下文
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()

	// 1. 创建时序数据库（保留 1 小时数据）
	db := storage.NewMemoryTSDB(1 * time.Hour)

	// 2. 创建系统采集器（每 3 秒采集一次）
	systemCollector := collector.NewSystemCollector(3 * time.Second)

	// 3. 启动采集器
	if err := systemCollector.Start(ctx); err != nil {
		fmt.Printf("Failed to start collector: %v\n", err)
		os.Exit(1)
	}
	fmt.Println("Collector started")

	// 4. 创建告警规则评估器
	evaluator := alert.NewRuleEvaluator(db)

	// 5. 添加告警规则
	rules := []*model.AlertRule{
		model.NewAlertRule("cpu_warning", "CPU 使用率警告", "cpu_usage > 60", model.SeverityWarning),
		model.NewAlertRule("cpu_critical", "CPU 使用率严重", "cpu_usage > 80", model.SeverityCritical),
		model.NewAlertRule("memory_warning", "内存使用率警告", "memory_usage > 70", model.SeverityWarning),
	}

	for _, rule := range rules {
		if err := evaluator.AddRule(rule); err != nil {
			fmt.Printf("Failed to add rule: %v\n", err)
		} else {
			fmt.Printf("Added rule: %s (%s)\n", rule.Name, rule.Expr)
		}
	}

	// 6. 创建通知器
	logNotifier := notifier.NewLogNotifier(50)

	// 7. 创建告警管理器
	alertMgr := alert.NewAlertManager(evaluator, 100)
	alertMgr.AddNotifier(logNotifier)

	// 8. 主循环：采集、存储、告警检查
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
					fmt.Printf("Collection error: %v\n", err)
					continue
				}

				// 存储指标
				for _, m := range metrics {
					if err := db.Write(m); err != nil {
						fmt.Printf("Write error: %v\n", err)
					}
				}

				// 检查告警
				if err := alertMgr.CheckAndNotify(); err != nil {
					fmt.Printf("Alert check error: %v\n", err)
				}

				// 打印状态
				fmt.Printf("[%s] Metrics: %d, Active Alerts: %d\n",
					time.Now().Format("15:04:05"),
					db.GetPointCount(),
					len(alertMgr.GetActiveAlerts()))
			}
		}
	}()

	// 9. 等待信号
	sigCh := make(chan os.Signal, 1)
	signal.Notify(sigCh, syscall.SIGINT, syscall.SIGTERM)

	fmt.Println("Monitoring started. Press Ctrl+C to stop.")
	<-sigCh

	fmt.Println("\nShutting down...")
	cancel()
	systemCollector.Stop()
	fmt.Println("Done.")
}
