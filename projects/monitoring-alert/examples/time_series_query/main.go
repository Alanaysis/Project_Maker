package main

import (
	"fmt"
	"math/rand"
	"time"

	"github.com/monitoring-alert/internal/model"
	"github.com/monitoring-alert/internal/storage"
	"github.com/monitoring-alert/src/aggregation"
)

func main() {
	fmt.Println("=== Time-Series Storage & Query Demo ===")
	fmt.Println()

	// 1. 创建时序数据库
	db := storage.NewMemoryTSDB(24 * time.Hour)
	aggFunc := aggregation.NewAggregationFunc(db)
	fmt.Println("[1] Created time-series DB and aggregation functions")

	// 2. 写入模拟数据
	fmt.Println()
	fmt.Println("[2] Writing simulated metric data...")

	// 写入 cpu_usage 指标 (多个实例)
	for i := 0; i < 5; i++ {
		for t := 0; t < 20; t++ {
			ts := time.Now().Add(-time.Duration(20-t) * time.Second)
			m := model.NewMetric("cpu_usage", model.MetricTypeGauge, "CPU usage").
				SetLabels(map[string]string{"host": fmt.Sprintf("server-%d", i)}).
				SetValue(20.0 + rand.Float64()*60.0).
				SetLabels(map[string]string{"host": fmt.Sprintf("server-%d", i)})
			m.Timestamp = ts
			db.Write(m)
		}
	}

	// 写入 memory_usage 指标
	for i := 0; i < 3; i++ {
		for t := 0; t < 20; t++ {
			ts := time.Now().Add(-time.Duration(20-t) * time.Second)
			m := model.NewMetric("memory_usage", model.MetricTypeGauge, "Memory usage").
				SetLabels(map[string]string{"host": fmt.Sprintf("server-%d", i)}).
				SetValue(40.0 + rand.Float64()*40.0)
			m.Timestamp = ts
			db.Write(m)
		}
	}

	// 写入 http_requests_total (Counter)
	for t := 0; t < 20; t++ {
		ts := time.Now().Add(-time.Duration(20-t) * time.Second)
		m := model.NewMetric("http_requests_total", model.MetricTypeCounter, "HTTP requests").
			SetLabels(map[string]string{"method": "GET", "status": "200"}).
			SetValue(float64(t * 100))
		m.Timestamp = ts
		db.Write(m)
	}

	fmt.Println("  Written: 5 cpu_usage series, 3 memory_usage series, 1 http_requests_total")

	// 3. 列出所有指标
	fmt.Println()
	fmt.Println("[3] Metric families:")
	for _, name := range db.List() {
		fmt.Printf("  - %s\n", name)
	}

	// 4. 查询最新值
	fmt.Println()
	fmt.Println("[4] Latest values:")
	queries := []struct {
		metric string
		labels map[string]string
	}{
		{"cpu_usage", map[string]string{"host": "server-0"}},
		{"cpu_usage", map[string]string{"host": "server-4"}},
		{"memory_usage", map[string]string{"host": "server-0"}},
		{"http_requests_total", map[string]string{"method": "GET", "status": "200"}},
	}
	for _, q := range queries {
		value, ok := db.GetLatest(q.metric, q.labels)
		if ok {
			fmt.Printf("  %s{%v} = %.2f\n", q.metric, q.labels, value)
		} else {
			fmt.Printf("  %s{%v} = (no data)\n", q.metric, q.labels)
		}
	}

	// 5. 范围查询
	fmt.Println()
	fmt.Println("[5] Range query: cpu_usage{host=server-0} (last 15s)")
	ts, err := db.Read("cpu_usage", map[string]string{"host": "server-0"},
		time.Now().Add(-15*time.Second), time.Now())
	if err != nil {
		fmt.Printf("  Error: %v\n", err)
	} else {
		points := ts.GetPoints()
		fmt.Printf("  Points: %d\n", len(points))
		if len(points) > 0 {
			fmt.Printf("  Min: %.2f, Max: %.2f\n", points[0].Value, points[len(points)-1].Value)
		}
	}

	// 6. 聚合查询
	fmt.Println()
	fmt.Println("[6] Aggregation queries (last 20s):")

	aggQueries := []struct {
		metric  string
		labels  map[string]string
		aggType string
	}{
		{"cpu_usage", map[string]string{"host": "server-0"}, "avg"},
		{"cpu_usage", map[string]string{"host": "server-0"}, "max"},
		{"cpu_usage", map[string]string{"host": "server-0"}, "min"},
		{"cpu_usage", map[string]string{"host": "server-0"}, "sum"},
		{"cpu_usage", map[string]string{"host": "server-0"}, "stddev"},
		{"cpu_usage", map[string]string{"host": "server-0"}, "median"},
		{"cpu_usage", map[string]string{"host": "server-0"}, "percentile"},
		{"http_requests_total", map[string]string{"method": "GET", "status": "200"}, "rate"},
		{"http_requests_total", map[string]string{"method": "GET", "status": "200"}, "delta"},
	}

	for _, q := range aggQueries {
		result, err := aggFunc.Aggregate(q.metric, q.labels,
			time.Now().Add(-20*time.Second), time.Now(), aggregation.AggregationType(q.aggType))
		if err != nil {
			fmt.Printf("  %s{%v} %s: error=%v\n", q.metric, q.labels, q.aggType, err)
		} else {
			fmt.Printf("  %s{%v} %s = %s\n", q.metric, q.labels, q.aggType, result.Format(2))
		}
	}

	// 7. 多指标聚合
	fmt.Println()
	fmt.Println("[7] Aggregate multiple cpu_usage series:")
	multiResult, err := aggFunc.AggregateMultiple([]string{"cpu_usage"},
		time.Now().Add(-20*time.Second), time.Now(), aggregation.AggAvg)
	if err != nil {
		fmt.Printf("  Error: %v\n", err)
	} else {
		for key, result := range multiResult {
			fmt.Printf("  %s avg = %.2f\n", key, result.Value)
		}
	}

	// 8. 按标签分组聚合
	fmt.Println()
	fmt.Println("[8] GroupBy host for cpu_usage:")
	groupResult, err := aggFunc.GroupBy("cpu_usage",
		time.Now().Add(-20*time.Second), time.Now(), aggregation.AggAvg, "host")
	if err != nil {
		fmt.Printf("  Error: %v\n", err)
	} else {
		for key, result := range groupResult {
			fmt.Printf("  %s avg = %.2f (count=%d)\n", key, result.Value, result.Count)
		}
	}

	fmt.Println()
	fmt.Println("=== Demo Complete ===")
}
