package model

import (
	"fmt"
	"sync"
	"time"
)

// MetricType 指标类型
type MetricType int

const (
	// MetricTypeCounter 计数器类型，只增不减
	MetricTypeCounter MetricType = iota
	// MetricTypeGauge 仪表盘类型，可增可减
	MetricTypeGauge
	// MetricTypeHistogram 直方图类型，用于统计分布
	MetricTypeHistogram
)

// String 返回指标类型的字符串表示
func (t MetricType) String() string {
	switch t {
	case MetricTypeCounter:
		return "counter"
	case MetricTypeGauge:
		return "gauge"
	case MetricTypeHistogram:
		return "histogram"
	default:
		return "unknown"
	}
}

// Metric 指标定义
type Metric struct {
	mu          sync.RWMutex
	Name        string            `json:"name"`
	Type        MetricType        `json:"type"`
	Labels      map[string]string `json:"labels"`
	Value       float64           `json:"value"`
	Timestamp   time.Time         `json:"timestamp"`
	Help        string            `json:"help"`
	Unit        string            `json:"unit"`
}

// NewMetric 创建新的指标
func NewMetric(name string, metricType MetricType, help string) *Metric {
	return &Metric{
		Name:      name,
		Type:      metricType,
		Labels:    make(map[string]string),
		Timestamp: time.Now(),
		Help:      help,
	}
}

// SetLabels 设置标签
func (m *Metric) SetLabels(labels map[string]string) *Metric {
	m.mu.Lock()
	defer m.mu.Unlock()
	m.Labels = labels
	return m
}

// SetValue 设置值
func (m *Metric) SetValue(value float64) *Metric {
	m.mu.Lock()
	defer m.mu.Unlock()
	m.Value = value
	m.Timestamp = time.Now()
	return m
}

// GetValue 获取值
func (m *Metric) GetValue() float64 {
	m.mu.RLock()
	defer m.mu.RUnlock()
	return m.Value
}

// GetTimestamp 获取时间戳
func (m *Metric) GetTimestamp() time.Time {
	m.mu.RLock()
	defer m.mu.RUnlock()
	return m.Timestamp
}

// GetLabels 获取标签
func (m *Metric) GetLabels() map[string]string {
	m.mu.RLock()
	defer m.mu.RUnlock()
	result := make(map[string]string, len(m.Labels))
	for k, v := range m.Labels {
		result[k] = v
	}
	return result
}

// String 返回指标的字符串表示
func (m *Metric) String() string {
	m.mu.RLock()
	defer m.mu.RUnlock()
	return fmt.Sprintf("%s{%v}=%f@%s", m.Name, m.Labels, m.Value, m.Timestamp.Format(time.RFC3339))
}

// TimeSeriesPoint 时序数据点
type TimeSeriesPoint struct {
	Timestamp time.Time `json:"timestamp"`
	Value     float64   `json:"value"`
}

// TimeSeries 时序数据
type TimeSeries struct {
	mu      sync.RWMutex
	Metric  string                `json:"metric"`
	Labels  map[string]string     `json:"labels"`
	Points  []TimeSeriesPoint     `json:"points"`
}

// NewTimeSeries 创建新的时序数据
func NewTimeSeries(metric string, labels map[string]string) *TimeSeries {
	return &TimeSeries{
		Metric: metric,
		Labels: labels,
		Points: make([]TimeSeriesPoint, 0),
	}
}

// AddPoint 添加数据点
func (ts *TimeSeries) AddPoint(timestamp time.Time, value float64) {
	ts.mu.Lock()
	defer ts.mu.Unlock()
	ts.Points = append(ts.Points, TimeSeriesPoint{
		Timestamp: timestamp,
		Value:     value,
	})
}

// GetPoints 获取所有数据点
func (ts *TimeSeries) GetPoints() []TimeSeriesPoint {
	ts.mu.RLock()
	defer ts.mu.RUnlock()
	result := make([]TimeSeriesPoint, len(ts.Points))
	copy(result, ts.Points)
	return result
}

// GetPointsInRange 获取指定时间范围内的数据点
func (ts *TimeSeries) GetPointsInRange(start, end time.Time) []TimeSeriesPoint {
	ts.mu.RLock()
	defer ts.mu.RUnlock()
	var result []TimeSeriesPoint
	for _, p := range ts.Points {
		if p.Timestamp.After(start) && p.Timestamp.Before(end) {
			result = append(result, p)
		}
	}
	return result
}

// Latest 获取最新的数据点
func (ts *TimeSeries) Latest() (TimeSeriesPoint, bool) {
	ts.mu.RLock()
	defer ts.mu.RUnlock()
	if len(ts.Points) == 0 {
		return TimeSeriesPoint{}, false
	}
	return ts.Points[len(ts.Points)-1], true
}

// Len 返回数据点数量
func (ts *TimeSeries) Len() int {
	ts.mu.RLock()
	defer ts.mu.RUnlock()
	return len(ts.Points)
}

// SetPoints 设置数据点（用于清理过期数据）
func (ts *TimeSeries) SetPoints(points []TimeSeriesPoint) {
	ts.mu.Lock()
	defer ts.mu.Unlock()
	ts.Points = points
}
