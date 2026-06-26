package main

import (
	"fmt"
	"math/rand"
	"time"

	"github.com/monitoring-alert/internal/collector"
	"github.com/monitoring-alert/internal/model"
	"github.com/monitoring-alert/internal/storage"
)

func main() {
	fmt.Println("=== Metrics Collection Demo ===")
	fmt.Println()

	// 1. 创建时序数据库
	db := storage.NewMemoryTSDB(24 * time.Hour)
	fmt.Println("[1] Time-series DB created with 24h retention")

	// 2. 创建系统指标采集器
	sysCollector := collector.NewSystemCollector(1 * time.Second)
	fmt.Println("[2] System collector created (1s interval)")

	// 3. 创建自定义指标采集器
	customCollector := collector.NewCustomCollector("http_requests", 1*time.Second, func() ([]*model.Metric, error) {
		metrics := make([]*model.Metric, 0)

		// 模拟 HTTP 请求计数 (Counter)
		reqCount := rand.Float64() * 1000
		reqMetric := model.NewMetric("http_requests_total", model.MetricTypeCounter, "Total HTTP requests").
			SetLabels(map[string]string{"method": "GET", "status": "200", "handler": "/api/users"}).
			SetValue(reqCount)
		metrics = append(metrics, reqMetric)

		// 模拟响应时间 (Histogram-like gauge)
		respTime := 50.0 + rand.Float64()*450.0
		respMetric := model.NewMetric("http_response_time_ms", model.MetricTypeGauge, "HTTP response time").
			SetLabels(map[string]string{"method": "GET", "handler": "/api/users"}).
			SetValue(respTime)
		metrics = append(metrics, respMetric)

		// 模拟活跃连接数 (Gauge)
		connections := float64(int(rand.Float64() * 100))
		connMetric := model.NewMetric("http_active_connections", model.MetricTypeGauge, "Active connections").
			SetLabels(map[string]string{"server": "web-01"}).
			SetValue(connections)
		metrics = append(metrics, connMetric)

		return metrics, nil
	})
	fmt.Println("[3] Custom HTTP collector created")

	// 4. 采集多轮数据
	fmt.Println()
	fmt.Println("--- Collecting data (10 rounds) ---")
	for round := 0; round < 10; round++ {
		// 系统指标
		sysMetrics, _ := sysCollector.Collect()
		for _, m := range sysMetrics {
			db.Write(m)
		}

		// 自定义指标
		customMetrics, _ := customCollector.Collect()
		for _, m := range customMetrics {
			db.Write(m)
		}

		fmt.Printf("  Round %d: collected %d system metrics + %d custom metrics\n",
			round+1, len(sysMetrics), len(customMetrics))
		time.Sleep(100 * time.Millisecond)
	}

	// 5. 查看存储的指标
	fmt.Println()
	fmt.Println("--- Stored Metrics ---")
	metricsList := db.List()
	fmt.Printf("Metric families: %v\n", metricsList)
	fmt.Printf("Total time series: %d\n", db.GetSeriesCount())
	fmt.Printf("Total data points: %d\n", db.GetPointCount())

	// 6. 查询最新值
	fmt.Println()
	fmt.Println("--- Latest Values ---")
	latestQueries := []struct {
		metric string
		labels map[string]string
	}{
		{"cpu_usage", map[string]string{"host": "localhost"}},
		{"memory_usage", map[string]string{"host": "localhost"}},
		{"http_requests_total", map[string]string{"method": "GET", "status": "200", "handler": "/api/users"}},
		{"http_response_time_ms", map[string]string{"method": "GET", "handler": "/api/users"}},
	}

	for _, q := range latestQueries {
		value, ok := db.GetLatest(q.metric, q.labels)
		if ok {
			fmt.Printf("  %s: %.2f\n", q.metric, value)
		} else {
			fmt.Printf("  %s: (no data)\n", q.metric)
		}
	}

	// 7. 范围查询
	fmt.Println()
	fmt.Println("--- Range Query: cpu_usage (last 5s) ---")
	ts, err := db.Read("cpu_usage", map[string]string{"host": "localhost"},
		time.Now().Add(-5*time.Second), time.Now())
	if err != nil {
		fmt.Printf("  Error: %v\n", err)
	} else {
		points := ts.GetPoints()
		fmt.Printf("  Found %d data points\n", len(points))
		if len(points) > 0 {
			fmt.Printf("  First: %.2f @ %s\n", points[0].Value, points[0].Timestamp.Format("15:04:05"))
			fmt.Printf("  Last:  %.2f @ %s\n", points[len(points)-1].Value, points[len(points)-1].Timestamp.Format("15:04:05"))
		}
	}

	fmt.Println()
	fmt.Println("=== Demo Complete ===")
}
