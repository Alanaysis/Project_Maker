package storage

import (
	"fmt"
	"sort"
	"sync"
	"time"

	"github.com/monitoring-alert/internal/model"
)

// TimeSeriesDB 时序数据库接口
type TimeSeriesDB interface {
	// Write 写入指标
	Write(metric *model.Metric) error
	// Read 读取时序数据
	Read(metric string, labels map[string]string, start, end time.Time) (*model.TimeSeries, error)
	// Query 查询指标
	Query(query string) ([]*model.TimeSeries, error)
	// Delete 删除时序数据
	Delete(metric string, labels map[string]string) error
	// List 列出所有指标名称
	List() []string
	// GetLatest 获取指标的最新值
	GetLatest(metric string, labels map[string]string) (float64, bool)
	// GetSeriesCount 获取时序数据数量
	GetSeriesCount() int
	// GetPointCount 获取数据点总数
	GetPointCount() int
}

// MemoryTSDB 内存时序数据库
type MemoryTSDB struct {
	mu       sync.RWMutex
	series   map[string]*model.TimeSeries
	index    map[string][]string // metric name -> series keys
	retention time.Duration
}

// NewMemoryTSDB 创建内存时序数据库
func NewMemoryTSDB(retention time.Duration) *MemoryTSDB {
	db := &MemoryTSDB{
		series:    make(map[string]*model.TimeSeries),
		index:     make(map[string][]string),
		retention: retention,
	}
	go db.cleanupLoop()
	return db
}

// generateKey 生成时序数据的键
func generateKey(metric string, labels map[string]string) string {
	key := metric
	if len(labels) > 0 {
		keys := make([]string, 0, len(labels))
		for k := range labels {
			keys = append(keys, k)
		}
		sort.Strings(keys)
		for _, k := range keys {
			key += fmt.Sprintf(";%s=%s", k, labels[k])
		}
	}
	return key
}

// Write 写入指标
func (db *MemoryTSDB) Write(metric *model.Metric) error {
	db.mu.Lock()
	defer db.mu.Unlock()

	labels := metric.GetLabels()
	key := generateKey(metric.Name, labels)

	ts, exists := db.series[key]
	if !exists {
		ts = model.NewTimeSeries(metric.Name, labels)
		db.series[key] = ts
		db.index[metric.Name] = append(db.index[metric.Name], key)
	}

	ts.AddPoint(metric.GetTimestamp(), metric.GetValue())
	return nil
}

// Read 读取时序数据
func (db *MemoryTSDB) Read(metric string, labels map[string]string, start, end time.Time) (*model.TimeSeries, error) {
	db.mu.RLock()
	defer db.mu.RUnlock()

	key := generateKey(metric, labels)
	ts, exists := db.series[key]
	if !exists {
		return nil, fmt.Errorf("metric not found: %s", metric)
	}

	points := ts.GetPointsInRange(start, end)
	result := model.NewTimeSeries(metric, labels)
	for _, p := range points {
		result.AddPoint(p.Timestamp, p.Value)
	}
	return result, nil
}

// Query 查询指标
func (db *MemoryTSDB) Query(query string) ([]*model.TimeSeries, error) {
	db.mu.RLock()
	defer db.mu.RUnlock()

	var result []*model.TimeSeries
	for name, keys := range db.index {
		if matchQuery(name, query) {
			for _, key := range keys {
				if ts, exists := db.series[key]; exists {
					result = append(result, ts)
				}
			}
		}
	}
	return result, nil
}

// matchQuery 匹配查询
func matchQuery(name, query string) bool {
	if query == "" || query == "*" {
		return true
	}
	return name == query
}

// Delete 删除时序数据
func (db *MemoryTSDB) Delete(metric string, labels map[string]string) error {
	db.mu.Lock()
	defer db.mu.Unlock()

	key := generateKey(metric, labels)
	if _, exists := db.series[key]; !exists {
		return fmt.Errorf("metric not found: %s", metric)
	}

	delete(db.series, key)

	// 更新索引
	keys := db.index[metric]
	for i, k := range keys {
		if k == key {
			db.index[metric] = append(keys[:i], keys[i+1:]...)
			break
		}
	}
	if len(db.index[metric]) == 0 {
		delete(db.index, metric)
	}

	return nil
}

// List 列出所有指标名称
func (db *MemoryTSDB) List() []string {
	db.mu.RLock()
	defer db.mu.RUnlock()

	names := make([]string, 0, len(db.index))
	for name := range db.index {
		names = append(names, name)
	}
	return names
}

// GetLatest 获取指标的最新值
func (db *MemoryTSDB) GetLatest(metric string, labels map[string]string) (float64, bool) {
	db.mu.RLock()
	defer db.mu.RUnlock()

	key := generateKey(metric, labels)
	ts, exists := db.series[key]
	if !exists {
		return 0, false
	}

	point, ok := ts.Latest()
	if !ok {
		return 0, false
	}
	return point.Value, true
}

// GetSeriesCount 获取时序数据数量
func (db *MemoryTSDB) GetSeriesCount() int {
	db.mu.RLock()
	defer db.mu.RUnlock()
	return len(db.series)
}

// GetPointCount 获取数据点总数
func (db *MemoryTSDB) GetPointCount() int {
	db.mu.RLock()
	defer db.mu.RUnlock()

	count := 0
	for _, ts := range db.series {
		count += ts.Len()
	}
	return count
}

// cleanupLoop 清理过期数据
func (db *MemoryTSDB) cleanupLoop() {
	ticker := time.NewTicker(time.Minute)
	defer ticker.Stop()

	for range ticker.C {
		db.cleanup()
	}
}

// cleanup 清理过期数据点
func (db *MemoryTSDB) cleanup() {
	db.mu.Lock()
	defer db.mu.Unlock()

	cutoff := time.Now().Add(-db.retention)
	for _, ts := range db.series {
		points := ts.GetPoints()
		validPoints := make([]model.TimeSeriesPoint, 0)
		for _, p := range points {
			if p.Timestamp.After(cutoff) {
				validPoints = append(validPoints, p)
			}
		}
		ts.SetPoints(validPoints)
	}
}

// QueryEngine 查询引擎
type QueryEngine struct {
	db TimeSeriesDB
}

// NewQueryEngine 创建查询引擎
func NewQueryEngine(db TimeSeriesDB) *QueryEngine {
	return &QueryEngine{db: db}
}

// SimpleQuery 简单查询
func (e *QueryEngine) SimpleQuery(metric string, duration time.Duration) ([]*model.TimeSeries, error) {
	end := time.Now()
	start := end.Add(-duration)

	labels := map[string]string{}
	ts, err := e.db.Read(metric, labels, start, end)
	if err != nil {
		return nil, err
	}
	return []*model.TimeSeries{ts}, nil
}

// AggregateQuery 聚合查询
func (e *QueryEngine) AggregateQuery(metric string, duration time.Duration, aggregation string) (float64, error) {
	end := time.Now()
	start := end.Add(-duration)

	labels := map[string]string{}
	ts, err := e.db.Read(metric, labels, start, end)
	if err != nil {
		return 0, err
	}

	points := ts.GetPoints()
	if len(points) == 0 {
		return 0, fmt.Errorf("no data points found")
	}

	switch aggregation {
	case "avg":
		return calculateAvg(points), nil
	case "sum":
		return calculateSum(points), nil
	case "min":
		return calculateMin(points), nil
	case "max":
		return calculateMax(points), nil
	case "count":
		return float64(len(points)), nil
	default:
		return 0, fmt.Errorf("unknown aggregation: %s", aggregation)
	}
}

// calculateAvg 计算平均值
func calculateAvg(points []model.TimeSeriesPoint) float64 {
	if len(points) == 0 {
		return 0
	}
	sum := calculateSum(points)
	return sum / float64(len(points))
}

// calculateSum 计算总和
func calculateSum(points []model.TimeSeriesPoint) float64 {
	sum := 0.0
	for _, p := range points {
		sum += p.Value
	}
	return sum
}

// calculateMin 计算最小值
func calculateMin(points []model.TimeSeriesPoint) float64 {
	if len(points) == 0 {
		return 0
	}
	min := points[0].Value
	for _, p := range points[1:] {
		if p.Value < min {
			min = p.Value
		}
	}
	return min
}

// calculateMax 计算最大值
func calculateMax(points []model.TimeSeriesPoint) float64 {
	if len(points) == 0 {
		return 0
	}
	max := points[0].Value
	for _, p := range points[1:] {
		if p.Value > max {
			max = p.Value
		}
	}
	return max
}
