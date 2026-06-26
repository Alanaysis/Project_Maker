package aggregation

import (
	"math"
	"sort"
	"time"

	"github.com/monitoring-alert/internal/model"
)

// AggregationType 聚合类型
type AggregationType string

const (
	// AggAvg 平均值
	AggAvg AggregationType = "avg"
	// AggSum 总和
	AggSum AggregationType = "sum"
	// AggMin 最小值
	AggMin AggregationType = "min"
	// AggMax 最大值
	AggMax AggregationType = "max"
	// AggCount 计数
	AggCount AggregationType = "count"
	// AggStddev 标准差
	AggStddev AggregationType = "stddev"
	// AggPercentile 分位数
	AggPercentile AggregationType = "percentile"
	// AggRate 增长率 (Counter 指标用)
	AggRate AggregationType = "rate"
	// AggDelta 差值 (Counter 指标用)
	AggDelta AggregationType = "delta"
	// AggMedian 中位数
	AggMedian AggregationType = "median"
	// AggLast 最新值
	AggLast AggregationType = "last"
	// AggFirst 最早值
	AggFirst AggregationType = "first"
)

// AggregationResult 聚合结果
type AggregationResult struct {
	Type     AggregationType `json:"type"`
	Value    float64         `json:"value"`
	Count    int             `json:"count"`
	Min      float64         `json:"min,omitempty"`
	Max      float64         `json:"max,omitempty"`
	P05      float64         `json:"p05,omitempty"`
	P25      float64         `json:"p25,omitempty"`
	P50      float64         `json:"p50,omitempty"`
	P75      float64         `json:"p75,omitempty"`
	P95      float64         `json:"p95,omitempty"`
	P99      float64         `json:"p99,omitempty"`
	Duration time.Duration   `json:"duration"`
}

// String 返回结果的字符串表示
func (r *AggregationResult) String() string {
	return r.Format(2)
}

// Format 格式化输出
func (r *AggregationResult) Format(precision int) string {
	precisionStr := ""
	switch r.Type {
	case AggAvg, AggSum, AggStddev:
		precisionStr = "%.2f"
	case AggPercentile:
		precisionStr = "%.4f"
	default:
		precisionStr = "%.0f"
	}

	result := ""
	switch r.Type {
	case AggPercentile:
		result = "percentile("
		if r.P05 != 0 || r.P99 != 0 {
			result += "p05=" + formatValue(r.P05, precisionStr)
			result += ",p50=" + formatValue(r.P50, precisionStr)
			result += ",p99=" + formatValue(r.P99, precisionStr)
		} else {
			result += formatValue(r.Value, precisionStr)
		}
		result += ")"
	default:
		result = formatValue(r.Value, precisionStr)
	}

	return result + " (count=" + stringInt64(int64(r.Count)) + ", duration=" + r.Duration.String() + ")"
}

// formatValue 格式化数值
func formatValue(v float64, format string) string {
	if v == math.Floor(v) {
		return formatFloat(v, 0)
	}
	return formatFloat(v, 2)
}

// formatFloat 格式化浮点数
func formatFloat(v float64, precision int) string {
	if precision == 0 {
		return stringInt(int64(v))
	}
	return stringFloat(v, precision)
}

// stringInt 转换 int64 为字符串
func stringInt(v int64) string {
	if v == int64(int(v)) {
		return stringInt64(v)
	}
	return stringFloat(float64(v), 2)
}

// stringInt64 转换 int64 为字符串
func stringInt64(v int64) string {
	if v == 0 {
		return "0"
	}
	neg := v < 0
	if neg {
		v = -v
	}
	var buf [20]byte
	i := len(buf)
	for v > 0 {
		i--
		buf[i] = byte('0' + v%10)
		v /= 10
	}
	if neg {
		i--
		buf[i] = '-'
	}
	return string(buf[i:])
}

// stringFloat 格式化浮点数为字符串
func stringFloat(v float64, precision int) string {
	if v == 0 {
		pad := ""
		for i := 0; i < precision; i++ {
			pad += "0"
		}
		return "0." + pad
	}
	neg := v < 0
	if neg {
		v = -v
	}
	multiplier := 1.0
	for i := 0; i < precision; i++ {
		multiplier *= 10
	}
	rounded := v * multiplier + 0.5
	intPart := int64(rounded)
	// Build integer part
	var intStr string
	if intPart == 0 {
		intStr = "0"
	} else {
		tmp := intPart
		var digits []byte
		for tmp > 0 {
			digits = append([]byte{byte('0' + tmp%10)}, digits...)
			tmp /= 10
		}
		if neg {
			digits = append([]byte{'-'}, digits...)
		}
		intStr = string(digits)
	}
	// Build decimal part
	remainder := float64(intPart) - float64(int(float64(intPart)/multiplier))*multiplier
	decimalPart := ""
	for i := 0; i < precision; i++ {
		remainder *= 10
		digit := int(remainder / multiplier)
		decimalPart += string(byte('0' + digit))
		remainder -= float64(int(digit)) * multiplier
	}
	// Remove trailing zeros but keep at least one decimal
	decimalPart = removeTrailingZeros(decimalPart)
	return intStr + "." + decimalPart
}

// removeTrailingZeros 移除末尾零
func removeTrailingZeros(s string) string {
	for len(s) > 1 && s[len(s)-1] == '0' {
		s = s[:len(s)-1]
	}
	return s
}

// AggregationFunc 聚合函数
type AggregationFunc struct {
	db TimeSeriesDB
}

// TimeSeriesDB 时序数据库接口
type TimeSeriesDB interface {
	Read(metric string, labels map[string]string, start, end time.Time) (*model.TimeSeries, error)
	Query(query string) ([]*model.TimeSeries, error)
	List() []string
}

// NewAggregationFunc 创建聚合函数
func NewAggregationFunc(db TimeSeriesDB) *AggregationFunc {
	return &AggregationFunc{db: db}
}

// Aggregate 执行聚合查询
func (a *AggregationFunc) Aggregate(metric string, labels map[string]string, start, end time.Time, agg AggregationType, args ...float64) (*AggregationResult, error) {
	ts, err := a.db.Read(metric, labels, start, end)
	if err != nil {
		return nil, err
	}

	points := ts.GetPoints()
	if len(points) == 0 {
		return &AggregationResult{
			Type:     agg,
			Value:    0,
			Count:    0,
			Duration: end.Sub(start),
		}, nil
	}

	result := &AggregationResult{
		Type:     agg,
		Count:    len(points),
		Duration: end.Sub(start),
	}

	switch agg {
	case AggAvg:
		result.Value = calcAvg(points)
	case AggSum:
		result.Value = calcSum(points)
	case AggMin:
		result.Value, result.Min = calcMin(points)
	case AggMax:
		result.Value, result.Max = calcMax(points)
	case AggCount:
		result.Value = float64(len(points))
	case AggStddev:
		result.Value = calcStddev(points)
	case AggMedian:
		result.Value = calcMedian(points)
	case AggLast:
		result.Value = points[len(points)-1].Value
	case AggFirst:
		result.Value = points[0].Value
	case AggRate:
		result.Value = calcRate(points)
	case AggDelta:
		result.Value = calcDelta(points)
	case AggPercentile:
		result.Value, result.P05, result.P25, result.P50, result.P75, result.P95, result.P99 = calcPercentiles(points, args...)
	}

	return result, nil
}

// AggregateMultiple 对多个指标执行聚合
func (a *AggregationFunc) AggregateMultiple(metrics []string, start, end time.Time, agg AggregationType) (map[string]*AggregationResult, error) {
	results := make(map[string]*AggregationResult)

	for _, metric := range metrics {
		tsList, err := a.db.Query(metric)
		if err != nil {
			continue
		}

		for _, ts := range tsList {
			key := metric
		labels := ts.Labels
		if labels == nil {
			labels = make(map[string]string)
		}
		if len(labels) > 0 {
				key = metric + "{" + labelsToString(labels) + "}"
			}

			result, err := a.Aggregate(metric, labels, start, end, agg)
			if err != nil {
				continue
			}

			if existing, ok := results[key]; ok {
				// Merge results for same metric with different labels
				switch agg {
				case AggAvg, AggMedian:
					totalPoints := existing.Count + result.Count
					existing.Value = (existing.Value*float64(existing.Count) + result.Value*float64(result.Count)) / float64(totalPoints)
					existing.Count = totalPoints
				case AggSum:
					existing.Value += result.Value
					existing.Count += result.Count
				case AggMin:
					if result.Value < existing.Value {
						existing.Value = result.Value
					}
					existing.Count += result.Count
				case AggMax:
					if result.Value > existing.Value {
						existing.Value = result.Value
					}
					existing.Count += result.Count
				default:
					existing.Value += result.Value
					existing.Count += result.Count
				}
			} else {
				results[key] = result
			}
		}
	}

	return results, nil
}

// GroupBy 按标签分组聚合
func (a *AggregationFunc) GroupBy(metric string, start, end time.Time, agg AggregationType, groupBy string) (map[string]*AggregationResult, error) {
	tsList, err := a.db.Query(metric)
	if err != nil {
		return nil, err
	}

	groups := make(map[string]*groupAccumulator)

	for _, ts := range tsList {
		labels := ts.Labels
		if labels == nil {
			labels = make(map[string]string)
		}
		var groupKey string

		if groupBy == "*" {
			// Group by all labels
			parts := make([]string, 0, len(labels))
			for k, v := range labels {
				parts = append(parts, k+"="+v)
			}
			groupKey = metric + "{" + joinStrings(parts, ",") + "}"
		} else {
			// Group by specific label
			if v, ok := labels[groupBy]; ok {
				groupKey = v
			} else {
				groupKey = "__missing__"
			}
			groupKey = metric + "{" + groupBy + "=" + groupKey + "}"
		}

		acc, exists := groups[groupKey]
		if !exists {
			acc = &groupAccumulator{
				metric: metric,
				labels: labels,
			}
			groups[groupKey] = acc
		}

		points := ts.GetPointsInRange(start, end)
		acc.addPoints(points)
	}

	results := make(map[string]*AggregationResult)
	for key, acc := range groups {
		result := acc.aggregate(agg)
		result.Duration = end.Sub(start)
		results[key] = result
	}

	return results, nil
}

// groupAccumulator 分组累加器
type groupAccumulator struct {
	metric string
	labels map[string]string
	values []float64
	min    float64
	max    float64
	sum    float64
}

func (g *groupAccumulator) addPoints(points []model.TimeSeriesPoint) {
	for _, p := range points {
		g.values = append(g.values, p.Value)
		g.sum += p.Value
		if len(g.values) == 1 || p.Value < g.min {
			g.min = p.Value
		}
		if len(g.values) == 1 || p.Value > g.max {
			g.max = p.Value
		}
	}
}

func (g *groupAccumulator) aggregate(agg AggregationType) *AggregationResult {
	if len(g.values) == 0 {
		return &AggregationResult{
			Type:  agg,
			Count: 0,
		}
	}

	result := &AggregationResult{
		Type:  agg,
		Count: len(g.values),
		Min:   g.min,
		Max:   g.max,
	}

	switch agg {
	case AggAvg, AggMedian:
		result.Value = g.sum / float64(len(g.values))
	case AggSum:
		result.Value = g.sum
	case AggMin:
		result.Value = g.min
	case AggMax:
		result.Value = g.max
	case AggCount:
		result.Value = float64(len(g.values))
	default:
		result.Value = g.sum / float64(len(g.values))
	}

	return result
}

// 辅助函数
func calcAvg(points []model.TimeSeriesPoint) float64 {
	if len(points) == 0 {
		return 0
	}
	sum := 0.0
	for _, p := range points {
		sum += p.Value
	}
	return sum / float64(len(points))
}

func calcSum(points []model.TimeSeriesPoint) float64 {
	sum := 0.0
	for _, p := range points {
		sum += p.Value
	}
	return sum
}

func calcMin(points []model.TimeSeriesPoint) (float64, float64) {
	if len(points) == 0 {
		return 0, 0
	}
	min := points[0].Value
	for _, p := range points[1:] {
		if p.Value < min {
			min = p.Value
		}
	}
	return min, min
}

func calcMax(points []model.TimeSeriesPoint) (float64, float64) {
	if len(points) == 0 {
		return 0, 0
	}
	max := points[0].Value
	for _, p := range points[1:] {
		if p.Value > max {
			max = p.Value
		}
	}
	return max, max
}

func calcStddev(points []model.TimeSeriesPoint) float64 {
	if len(points) < 2 {
		return 0
	}
	mean := calcAvg(points)
	varSum := 0.0
	for _, p := range points {
		diff := p.Value - mean
		varSum += diff * diff
	}
	return math.Sqrt(varSum / float64(len(points)-1))
}

func calcMedian(points []model.TimeSeriesPoint) float64 {
	if len(points) == 0 {
		return 0
	}
	sorted := make([]float64, len(points))
	for i, p := range points {
		sorted[i] = p.Value
	}
	sort.Float64s(sorted)
	n := len(sorted)
	if n%2 == 0 {
		return (sorted[n/2-1] + sorted[n/2]) / 2
	}
	return sorted[n/2]
}

func calcRate(points []model.TimeSeriesPoint) float64 {
	if len(points) < 2 {
		return 0
	}
	// 计算单位时间内的增长率
	first := points[0]
	last := points[len(points)-1]
	duration := last.Timestamp.Sub(first.Timestamp).Seconds()
	if duration <= 0 {
		return 0
	}
	return (last.Value - first.Value) / duration
}

func calcDelta(points []model.TimeSeriesPoint) float64 {
	if len(points) < 2 {
		return 0
	}
	return points[len(points)-1].Value - points[0].Value
}

func calcPercentiles(points []model.TimeSeriesPoint, args ...float64) (float64, float64, float64, float64, float64, float64, float64) {
	if len(points) == 0 {
		return 0, 0, 0, 0, 0, 0, 0
	}

	// 提取分位数值，默认 p05, p25, p50, p75, p95, p99
	percentiles := []float64{5, 25, 50, 75, 95, 99}
	if len(args) > 0 {
		percentiles = make([]float64, len(args))
		for i, a := range args {
			percentiles[i] = a
		}
	}

	sorted := make([]float64, len(points))
	for i, p := range points {
		sorted[i] = p.Value
	}
	sort.Float64s(sorted)

	// 计算所有请求的分位数
	result := make(map[float64]float64)
	for _, p := range percentileValues {
		result[p] = calcSinglePercentile(sorted, p)
	}

	return result[50], result[5], result[25], result[50], result[75], result[95], result[99]
}

// 预定义的分位数值
var percentileValues = []float64{5, 25, 50, 75, 95, 99}

func calcSinglePercentile(sorted []float64, percentile float64) float64 {
	if len(sorted) == 0 {
		return 0
	}
	if len(sorted) == 1 {
		return sorted[0]
	}

	// 使用线性插值法
	rank := (percentile / 100.0) * float64(len(sorted)-1)
	lower := int(math.Floor(rank))
	upper := int(math.Ceil(rank))

	if lower == upper || upper >= len(sorted) {
		return sorted[lower]
	}

	frac := rank - float64(lower)
	return sorted[lower]*(1-frac) + sorted[upper]*frac
}

func labelsToString(labels map[string]string) string {
	if len(labels) == 0 {
		return ""
	}
	keys := make([]string, 0, len(labels))
	for k := range labels {
		keys = append(keys, k)
	}
	sort.Strings(keys)
	parts := make([]string, 0, len(keys))
	for _, k := range keys {
		parts = append(parts, k+"="+labels[k])
	}
	return joinStrings(parts, ",")
}

func joinStrings(parts []string, sep string) string {
	if len(parts) == 0 {
		return ""
	}
	result := parts[0]
	for _, p := range parts[1:] {
		result += sep + p
	}
	return result
}
