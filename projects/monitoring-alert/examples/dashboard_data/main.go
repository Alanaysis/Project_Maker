package main

import (
	"fmt"
	"math/rand"
	"time"

	"github.com/monitoring-alert/internal/model"
	"github.com/monitoring-alert/internal/storage"
	"github.com/monitoring-alert/src/aggregation"
	"github.com/monitoring-alert/src/dashboard"
)

func main() {
	fmt.Println("=== Dashboard Data Demo ===")
	fmt.Println()

	// 1. 创建时序数据库并填充数据
	db := storage.NewMemoryTSDB(24 * time.Hour)
	fmt.Println("[1] Created time-series DB with simulated data")

	// 模拟 1 小时的数据，每秒一个点
	fmt.Println()
	fmt.Println("[2] Generating 1 hour of simulated metrics...")

	now := time.Now()
	start := now.Add(-1 * time.Hour)

	// CPU 使用率 (带周期性波动)
	for t := start; !t.After(now); t = t.Add(1 * time.Second) {
		// 模拟昼夜周期
		hour := float64(t.Hour()) + float64(t.Minute())/60.0
		cycle := 20.0 * (hour/24.0) * (24.0-hour)/24.0
		value := 30.0 + cycle + rand.Float64()*20.0

		m := model.NewMetric("cpu_usage", model.MetricTypeGauge, "CPU usage %").
			SetLabels(map[string]string{"host": "web-01"}).
			SetValue(value)
		m.Timestamp = t
		db.Write(m)
	}

	// 内存使用率 (缓慢增长)
	for t := start; !t.After(now); t = t.Add(1 * time.Second) {
		minutes := t.Sub(start).Minutes()
		value := 40.0 + minutes*0.01 + rand.Float64()*5.0

		m := model.NewMetric("memory_usage", model.MetricTypeGauge, "Memory usage %").
			SetLabels(map[string]string{"host": "web-01"}).
			SetValue(value)
		m.Timestamp = t
		db.Write(m)
	}

	// HTTP 请求数 (Counter)
	requestCount := 0.0
	for t := start; !t.After(now); t = t.Add(1 * time.Second) {
		requestCount += float64(10 + int(rand.Float64()*20))

		m := model.NewMetric("http_requests_total", model.MetricTypeCounter, "Total HTTP requests").
			SetLabels(map[string]string{"method": "GET", "status": "200"}).
			SetValue(requestCount)
		m.Timestamp = t
		db.Write(m)
	}

	// 响应时间 (带尖峰)
	for t := start; !t.After(now); t = t.Add(1 * time.Second) {
		value := 50.0 + rand.Float64()*100.0
		// 模拟偶尔的延迟尖峰
		if rand.Float64() < 0.02 {
			value += 500.0
		}

		m := model.NewMetric("http_response_time_ms", model.MetricTypeGauge, "Response time ms").
			SetLabels(map[string]string{"method": "GET", "handler": "/api/users"}).
			SetValue(value)
		m.Timestamp = t
		db.Write(m)
	}

	fmt.Printf("  Generated data: %d series, %d points\n", db.GetSeriesCount(), db.GetPointCount())

	// 2. 创建仪表盘
	fmt.Println()
	fmt.Println("[3] Creating dashboard...")

	dash := dashboard.NewDashboard("system-overview", "System Overview", "Main system monitoring dashboard")

	dash.AddPanel(&dashboard.DashboardPanel{
		ID:       "cpu-gauge",
		Title:    "CPU Usage",
		Type:     dashboard.PanelGauge,
		Metric:   "cpu_usage",
		Labels:   map[string]string{"host": "web-01"},
		Thresholds: &dashboard.ThresholdConfig{
			Warning:  70,
			Critical: 90,
		},
	})

	dash.AddPanel(&dashboard.DashboardPanel{
		ID:       "cpu-timeseries",
		Title:    "CPU Over Time",
		Type:     dashboard.PanelTimeSeries,
		Metric:   "cpu_usage",
		Labels:   map[string]string{"host": "web-01"},
		AggType:  aggregation.AggAvg,
		Range:    1 * time.Hour,
		Interval: 1 * time.Minute,
		Thresholds: &dashboard.ThresholdConfig{
			Warning:  70,
			Critical: 90,
		},
	})

	dash.AddPanel(&dashboard.DashboardPanel{
		ID:       "memory-stat",
		Title:    "Memory Stats",
		Type:     dashboard.PanelStat,
		Metric:   "memory_usage",
		Labels:   map[string]string{"host": "web-01"},
		AggType:  aggregation.AggAvg,
		Range:    1 * time.Hour,
		Thresholds: &dashboard.ThresholdConfig{
			Warning:  75,
			Critical: 90,
		},
	})

	dash.AddPanel(&dashboard.DashboardPanel{
		ID:       "http-rate",
		Title:    "HTTP Request Rate",
		Type:     dashboard.PanelStat,
		Metric:   "http_requests_total",
		Labels:   map[string]string{"method": "GET", "status": "200"},
		AggType:  aggregation.AggRate,
		Range:    5 * time.Minute,
	})

	dash.AddPanel(&dashboard.DashboardPanel{
		ID:       "response-bar",
		Title:    "Response Time Distribution",
		Type:     dashboard.PanelBarChart,
		Metric:   "http_response_time_ms",
		Labels:   map[string]string{"method": "GET", "handler": "/api/users"},
		Range:    1 * time.Hour,
		Interval: 5 * time.Minute,
		Thresholds: &dashboard.ThresholdConfig{
			Warning:  200,
			Critical: 500,
		},
	})

	fmt.Printf("  Dashboard '%s' created with %d panels\n", dash.Title, len(dash.Panels))

	// 3. 获取仪表盘数据
	fmt.Println()
	fmt.Println("[4] Fetching dashboard data...")

	provider := dashboard.NewDashboardDataProvider(db)
	dashboardData, err := provider.GetDashboardData(dash)
	if err != nil {
		fmt.Printf("  Error: %v\n", err)
		return
	}

	fmt.Printf("  Dashboard data fetched at %s\n", dashboardData.UpdatedAt.Format("15:04:05"))

	// 4. 展示每个面板的数据
	fmt.Println()
	fmt.Println("[5] Panel Data:")

	for _, panelID := range []string{"cpu-gauge", "cpu-timeseries", "memory-stat", "http-rate", "response-bar"} {
		panelData, ok := dashboardData.PanelData[panelID]
		if !ok {
			fmt.Printf("  Panel '%s': (not found)\n", panelID)
			continue
		}

		fmt.Printf("\n  --- %s (%s) ---\n", panelData.Title, panelData.Type)

		if panelData.Error != "" {
			fmt.Printf("    Error: %s\n", panelData.Error)
			continue
		}

		if panelData.CurrentValue != 0 {
			fmt.Printf("    Current: %.2f\n", panelData.CurrentValue)
		}

		if panelData.Aggregation != nil {
			fmt.Printf("    Aggregation: %s\n", panelData.Aggregation.Format(2))
		}

		if panelData.Status != "" {
			fmt.Printf("    Status: %s\n", panelData.Status)
		}

		if len(panelData.Points) > 0 {
			fmt.Printf("    Data points: %d\n", len(panelData.Points))
		}

		if len(panelData.Buckets) > 0 {
			fmt.Printf("    Buckets: %d\n", len(panelData.Buckets))
			// 展示前 3 个桶
			showCount := len(panelData.Buckets)
			if showCount > 3 {
				showCount = 3
			}
			for i := 0; i < showCount; i++ {
				b := panelData.Buckets[i]
				fmt.Printf("      [%s-%s] avg=%.1f count=%d min=%.1f max=%.1f\n",
					b.Start.Format("15:04"), b.End.Format("15:04"), b.Value, b.Count, b.Min, b.Max)
			}
		}

		if panelData.Groups != nil {
			fmt.Printf("    Groups: %d\n", len(panelData.Groups))
			for gKey, g := range panelData.Groups {
				fmt.Printf("      %s: count=%d avg=%.1f min=%.1f max=%.1f\n",
					gKey, g.Count, g.Avg, g.Min, g.Max)
			}
		}
	}

	// 5. 聚合函数演示
	fmt.Println()
	fmt.Println("[6] Additional Aggregation Examples:")

	aggFunc := aggregation.NewAggregationFunc(db)

	examples := []struct {
		metric  string
		labels  map[string]string
		aggType string
		desc    string
	}{
		{"cpu_usage", map[string]string{"host": "web-01"}, "avg", "Average CPU"},
		{"cpu_usage", map[string]string{"host": "web-01"}, "p95", "P95 CPU"},
		{"cpu_usage", map[string]string{"host": "web-01"}, "stddev", "CPU StdDev"},
		{"http_response_time_ms", map[string]string{"method": "GET", "handler": "/api/users"}, "avg", "Avg Response Time"},
		{"http_response_time_ms", map[string]string{"method": "GET", "handler": "/api/users"}, "max", "Max Response Time"},
		{"http_response_time_ms", map[string]string{"method": "GET", "handler": "/api/users"}, "percentile", "Response Time Percentiles"},
	}

	for _, ex := range examples {
		result, err := aggFunc.Aggregate(ex.metric, ex.labels,
			start, now, aggregation.AggregationType(ex.aggType))
		if err != nil {
			fmt.Printf("  %s: error=%v\n", ex.desc, err)
		} else {
			fmt.Printf("  %s: %s\n", ex.desc, result.Format(2))
		}
	}

	fmt.Println()
	fmt.Println("=== Demo Complete ===")
}
