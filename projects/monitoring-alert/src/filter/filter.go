package filter

import (
	"strings"
	"time"

	"github.com/monitoring-alert/internal/model"
)

// Filter 指标过滤器
type Filter struct {
	metricName string
	labels     map[string]string
	timeRange  *TimeRangeFilter
	valueRange *ValueRangeFilter
	types      []model.MetricType
}

// TimeRangeFilter 时间范围过滤器
type TimeRangeFilter struct {
	Start time.Time
	End   time.Time
}

// ValueRangeFilter 值范围过滤器
type ValueRangeFilter struct {
	Min float64
	Max float64
}

// NewFilter 创建过滤器
func NewFilter() *Filter {
	return &Filter{
		labels: make(map[string]string),
	}
}

// FilterMetric 过滤单个指标
func (f *Filter) FilterMetric(m *model.Metric) bool {
	// 检查指标名称
	if f.metricName != "" && f.metricName != "*" && f.metricName != m.Name {
		return false
	}

	// 检查标签
	for k, v := range f.labels {
		mLabels := m.GetLabels()
		if mVal, ok := mLabels[k]; !ok || mVal != v {
			return false
		}
	}

	// 检查时间范围
	if f.timeRange != nil {
		ts := m.GetTimestamp()
		if !ts.After(f.timeRange.Start) || !ts.Before(f.timeRange.End) {
			return false
		}
	}

	// 检查值范围
	if f.valueRange != nil {
		v := m.GetValue()
		if f.valueRange.Min != 0 || f.valueRange.Max != 0 {
			if v < f.valueRange.Min || v > f.valueRange.Max {
				return false
			}
		}
	}

	// 检查类型
	if len(f.types) > 0 {
		found := false
		for _, t := range f.types {
			if t == m.Type {
				found = true
				break
			}
		}
		if !found {
			return false
		}
	}

	return true
}

// FilterMetrics 过滤指标列表
func (f *Filter) FilterMetrics(metrics []*model.Metric) []*model.Metric {
	var result []*model.Metric
	for _, m := range metrics {
		if f.FilterMetric(m) {
			result = append(result, m)
		}
	}
	return result
}

// FilterTimeSeries 过滤时序数据
func (f *Filter) FilterTimeSeries(tsList []*model.TimeSeries) []*model.TimeSeries {
	var result []*model.TimeSeries
	for _, ts := range tsList {
		if f.matchesTimeSeries(ts) {
			result = append(result, ts)
		}
	}
	return result
}

// matchesTimeSeries 检查时序数据是否匹配
func (f *Filter) matchesTimeSeries(ts *model.TimeSeries) bool {
	// 检查指标名称
	if f.metricName != "" && f.metricName != "*" && f.metricName != ts.Metric {
		return false
	}

	// 检查标签
	for k, v := range f.labels {
		tsLabels := ts.Labels
		if tsVal, ok := tsLabels[k]; !ok || tsVal != v {
			return false
		}
	}

	return true
}

// WithMetricName 设置指标名称过滤
func (f *Filter) WithMetricName(name string) *Filter {
	f.metricName = name
	return f
}

// WithLabel 设置标签过滤
func (f *Filter) WithLabel(key, value string) *Filter {
	f.labels[key] = value
	return f
}

// WithLabels 设置多个标签过滤
func (f *Filter) WithLabels(labels map[string]string) *Filter {
	for k, v := range labels {
		f.labels[k] = v
	}
	return f
}

// WithTimeRange 设置时间范围
func (f *Filter) WithTimeRange(start, end time.Time) *Filter {
	f.timeRange = &TimeRangeFilter{Start: start, End: end}
	return f
}

// WithValueRange 设置值范围
func (f *Filter) WithValueRange(min, max float64) *Filter {
	f.valueRange = &ValueRangeFilter{Min: min, Max: max}
	return f
}

// WithTypes 设置指标类型过滤
func (f *Filter) WithTypes(types []model.MetricType) *Filter {
	f.types = types
	return f
}

// Matcher 匹配器接口
type Matcher interface {
	Match(metric string, labels map[string]string) bool
}

// LabelMatcher 标签匹配器
type LabelMatcher struct {
	matchAll bool // true=AND, false=OR
	filters  map[string][]string
}

// NewLabelMatcher 创建标签匹配器
func NewLabelMatcher(matchAll bool) *LabelMatcher {
	return &LabelMatcher{
		matchAll: matchAll,
		filters:  make(map[string][]string),
	}
}

// Match 匹配
func (m *LabelMatcher) Match(metric string, labels map[string]string) bool {
	if len(m.filters) == 0 {
		return true
	}

	if m.matchAll {
		// AND: 所有条件都要匹配
		for key, values := range m.filters {
			var found bool
			for _, v := range values {
				if labels[key] == v {
					found = true
					break
				}
			}
			if !found {
				return false
			}
		}
		return true
	}

	// OR: 至少一个条件匹配
	for key, values := range m.filters {
		for _, v := range values {
			if labels[key] == v {
				return true
			}
		}
	}
	return false
}

// WithKeyValues 添加键值对匹配
func (m *LabelMatcher) WithKeyValues(key string, values ...string) *LabelMatcher {
	m.filters[key] = values
	return m
}

// MetricNamePattern 指标名称模式匹配器
type MetricNamePattern struct {
	pattern string
	compiled bool
}

// NewMetricNamePattern 创建模式匹配器
func NewMetricNamePattern(pattern string) *MetricNamePattern {
	return &MetricNamePattern{pattern: pattern}
}

// Match 匹配
func (p *MetricNamePattern) Match(metric string, _ map[string]string) bool {
	if p.pattern == "*" {
		return true
	}
	return p.pattern == metric || strings.Contains(metric, p.pattern)
}

// CompositeFilter 复合过滤器
type CompositeFilter struct {
	filters []Filter
}

// NewCompositeFilter 创建复合过滤器
func NewCompositeFilter() *CompositeFilter {
	return &CompositeFilter{}
}

// AddFilter 添加过滤器
func (cf *CompositeFilter) AddFilter(f Filter) *CompositeFilter {
	cf.filters = append(cf.filters, f)
	return cf
}

// Match 匹配
func (cf *CompositeFilter) Match(metric string, labels map[string]string) bool {
	for _, f := range cf.filters {
		if f.metricName != "" && f.metricName != "*" && f.metricName != metric {
			return false
		}
		for k, v := range f.labels {
			if lv, ok := labels[k]; !ok || lv != v {
				return false
			}
		}
	}
	return true
}

// AggregationFilter 聚合过滤器
type AggregationFilter struct {
	groupBy  string
	having   map[string]ValueRangeFilter
}

// NewAggregationFilter 创建聚合过滤器
func NewAggregationFilter(groupBy string) *AggregationFilter {
	return &AggregationFilter{
		groupBy: groupBy,
		having:  make(map[string]ValueRangeFilter),
	}
}

// Having 添加 Having 条件
func (af *AggregationFilter) Having(metric string, min, max float64) *AggregationFilter {
	af.having[metric] = ValueRangeFilter{Min: min, Max: max}
	return af
}

// GroupStats 分组统计（filter 包本地定义，避免循环依赖）
type GroupStats struct {
	Labels map[string]string
	Count  int
	Sum    float64
	Avg    float64
	Min    float64
	Max    float64
}

// FilterGroups 过滤聚合结果
func (af *AggregationFilter) FilterGroups(groups map[string]*GroupStats) map[string]*GroupStats {
	if len(af.having) == 0 {
		return groups
	}

	result := make(map[string]*GroupStats)
	for key, g := range groups {
		// 检查 Having 条件
		match := true
		for metric, vr := range af.having {
			var val float64
			switch metric {
			case "avg":
				val = g.Avg
			case "min":
				val = g.Min
			case "max":
				val = g.Max
			case "count":
				val = float64(g.Count)
			default:
				val = g.Avg
			}
			if val < vr.Min || val > vr.Max {
				match = false
				break
			}
		}
		if match {
			result[key] = g
		}
	}

	return result
}
