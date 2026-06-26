package anomaly

import (
	"math"
	"time"

	"github.com/monitoring-alert/internal/model"
)

// DetectionType 检测类型
type DetectionType string

const (
	// DetectionStaticThreshold 静态阈值
	DetectionStaticThreshold DetectionType = "static_threshold"
	// DetectionDynamicThreshold 动态阈值 (移动平均)
	DetectionDynamicThreshold DetectionType = "dynamic_threshold"
	// DetectionZScore Z-Score 异常检测
	DetectionZScore DetectionType = "zscore"
	// DetectionIQR IQR 异常检测
	DetectionIQR DetectionType = "iqr"
	// DetectionEWMA 指数加权移动平均
	DetectionEWMA DetectionType = "ewma"
)

// AnomalyRule 异常检测规则
type AnomalyRule struct {
	ID               string              `json:"id"`
	Name             string              `json:"name"`
	Metric           string              `json:"metric"`
	Labels           map[string]string   `json:"labels"`
	DetectionType    DetectionType       `json:"detection_type"`
	Severity         model.AlertSeverity `json:"severity"`
	Window           time.Duration       `json:"window"`
	StaticUpperBound float64             `json:"static_upper_bound,omitempty"`
	StaticLowerBound float64             `json:"static_lower_bound,omitempty"`
	DynamicThreshold float64             `json:"dynamic_threshold,omitempty"`
	ZScoreThreshold  float64             `json:"zscore_threshold,omitempty"`
	IQRMultiplier    float64             `json:"iqr_multiplier,omitempty"`
	EWMAAlpha        float64             `json:"ewma_alpha,omitempty"`
	EWMAThreshold    float64             `json:"ewma_threshold,omitempty"`
	Enabled          bool                `json:"enabled"`
}

// NewAnomalyRule 创建异常检测规则
func NewAnomalyRule(id, name, metric string, detType DetectionType) *AnomalyRule {
	return &AnomalyRule{
		ID:            id,
		Name:          name,
		Metric:        metric,
		Labels:        make(map[string]string),
		DetectionType: detType,
		Severity:      model.SeverityWarning,
		Window:        5 * time.Minute,
		Enabled:       true,
	}
}

// AnomalyResult 异常检测结果
type AnomalyResult struct {
	RuleID       string            `json:"rule_id"`
	RuleName     string            `json:"rule_name"`
	Metric       string            `json:"metric"`
	Labels       map[string]string `json:"labels"`
	Value        float64           `json:"value"`
	Expected     float64           `json:"expected"`
	Deviation    float64           `json:"deviation"`
	Severity     model.AlertSeverity `json:"severity"`
	Timestamp    time.Time         `json:"timestamp"`
	DetectionType DetectionType    `json:"detection_type"`
	Description  string            `json:"description"`
}

// String 返回结果的字符串表示
func (r *AnomalyResult) String() string {
	return "ANOMALY[" + r.RuleName + "]: " + r.Metric + " value=" + stringFloat(r.Value) +
		" expected=" + stringFloat(r.Expected) + " deviation=" + stringFloat(r.Deviation)
}

func stringFloat(v float64) string {
	if v == math.Floor(v) {
		return stringInt64(int64(v))
	}
	return formatFloat(v, 2)
}

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

func formatFloat(v float64, precision int) string {
	if precision == 0 {
		return stringInt64(int64(v))
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
	remainder := float64(intPart) - float64(int(float64(intPart)/multiplier))*multiplier
	decimalPart := ""
	for i := 0; i < precision; i++ {
		remainder *= 10
		digit := int(remainder / multiplier)
		decimalPart += string(byte('0' + digit))
		remainder -= float64(int(digit)) * multiplier
	}
	for len(decimalPart) > 1 && decimalPart[len(decimalPart)-1] == '0' {
		decimalPart = decimalPart[:len(decimalPart)-1]
	}
	return intStr + "." + decimalPart
}

// AnomalyDetector 异常检测器
type AnomalyDetector struct {
	rules []*AnomalyRule
}

// NewAnomalyDetector 创建异常检测器
func NewAnomalyDetector() *AnomalyDetector {
	return &AnomalyDetector{
		rules: make([]*AnomalyRule, 0),
	}
}

// AddRule 添加检测规则
func (d *AnomalyDetector) AddRule(rule *AnomalyRule) {
	d.rules = append(d.rules, rule)
}

// RemoveRule 移除检测规则
func (d *AnomalyDetector) RemoveRule(id string) {
	for i, rule := range d.rules {
		if rule.ID == id {
			d.rules = append(d.rules[:i], d.rules[i+1:]...)
			break
		}
	}
}

// Detect 执行异常检测
func (d *AnomalyDetector) Detect(points []model.TimeSeriesPoint, now time.Time) []*AnomalyResult {
	var results []*AnomalyResult

	for _, rule := range d.rules {
		if !rule.Enabled {
			continue
		}

		// 获取窗口内的数据点
		windowStart := now.Add(-rule.Window)
		var windowPoints []model.TimeSeriesPoint
		for _, p := range points {
			if p.Timestamp.After(windowStart) {
				windowPoints = append(windowPoints, p)
			}
		}

		// 需要至少2个点才能检测
		if len(windowPoints) < 2 {
			continue
		}

		// 获取最新值
		currentValue := windowPoints[len(windowPoints)-1].Value

		var result *AnomalyResult

		switch rule.DetectionType {
		case DetectionStaticThreshold:
			result = d.detectStaticThreshold(currentValue, rule, now)
		case DetectionDynamicThreshold:
			result = d.detectDynamicThreshold(windowPoints, rule, now)
		case DetectionZScore:
			result = d.detectZScore(windowPoints, rule, now)
		case DetectionIQR:
			result = d.detectIQR(windowPoints, rule, now)
		case DetectionEWMA:
			result = d.detectEWMA(windowPoints, rule, now)
		}

		if result != nil {
			results = append(results, result)
		}
	}

	return results
}

// detectStaticThreshold 静态阈值检测
func (d *AnomalyDetector) detectStaticThreshold(value float64, rule *AnomalyRule, now time.Time) *AnomalyResult {
	// 检查是否超出静态阈值
	if rule.StaticUpperBound > 0 && value > rule.StaticUpperBound {
		return &AnomalyResult{
			RuleID:        rule.ID,
			RuleName:      rule.Name,
			Metric:        rule.Metric,
			Labels:        rule.Labels,
			Value:         value,
			Expected:      rule.StaticUpperBound,
			Deviation:     value - rule.StaticUpperBound,
			Severity:      rule.Severity,
			Timestamp:     now,
			DetectionType: rule.DetectionType,
			Description:   "Value " + stringFloat(value) + " exceeds upper bound " + stringFloat(rule.StaticUpperBound),
		}
	}

	if rule.StaticLowerBound > 0 && value < rule.StaticLowerBound {
		return &AnomalyResult{
			RuleID:        rule.ID,
			RuleName:      rule.Name,
			Metric:        rule.Metric,
			Labels:        rule.Labels,
			Value:         value,
			Expected:      rule.StaticLowerBound,
			Deviation:     rule.StaticLowerBound - value,
			Severity:      rule.Severity,
			Timestamp:     now,
			DetectionType: rule.DetectionType,
			Description:   "Value " + stringFloat(value) + " below lower bound " + stringFloat(rule.StaticLowerBound),
		}
	}

	return nil
}

// detectDynamicThreshold 动态阈值检测 (基于移动平均)
func (d *AnomalyDetector) detectDynamicThreshold(points []model.TimeSeriesPoint, rule *AnomalyRule, now time.Time) *AnomalyResult {
	if len(points) < 2 {
		return nil
	}

	mean := calcMean(points)
	stddev := calcStddev(points)

	if stddev == 0 {
		return nil
	}

	currentValue := points[len(points)-1].Value
	upperBound := mean + rule.DynamicThreshold*stddev
	lowerBound := mean - rule.DynamicThreshold*stddev

	if currentValue > upperBound {
		return &AnomalyResult{
			RuleID:        rule.ID,
			RuleName:      rule.Name,
			Metric:        rule.Metric,
			Labels:        rule.Labels,
			Value:         currentValue,
			Expected:      mean,
			Deviation:     currentValue - mean,
			Severity:      rule.Severity,
			Timestamp:     now,
			DetectionType: rule.DetectionType,
			Description:   "Value " + stringFloat(currentValue) + " exceeds dynamic upper bound " + stringFloat(upperBound),
		}
	}

	if currentValue < lowerBound {
		return &AnomalyResult{
			RuleID:        rule.ID,
			RuleName:      rule.Name,
			Metric:        rule.Metric,
			Labels:        rule.Labels,
			Value:         currentValue,
			Expected:      mean,
			Deviation:     mean - currentValue,
			Severity:      rule.Severity,
			Timestamp:     now,
			DetectionType: rule.DetectionType,
			Description:   "Value " + stringFloat(currentValue) + " below dynamic lower bound " + stringFloat(lowerBound),
		}
	}

	return nil
}

// detectZScore Z-Score 异常检测
func (d *AnomalyDetector) detectZScore(points []model.TimeSeriesPoint, rule *AnomalyRule, now time.Time) *AnomalyResult {
	if len(points) < 3 {
		return nil
	}

	mean := calcMean(points)
	stddev := calcStddev(points)

	if stddev == 0 {
		return nil
	}

	currentValue := points[len(points)-1].Value
	zScore := (currentValue - mean) / stddev

	if math.Abs(zScore) > rule.ZScoreThreshold {
		return &AnomalyResult{
			RuleID:        rule.ID,
			RuleName:      rule.Name,
			Metric:        rule.Metric,
			Labels:        rule.Labels,
			Value:         currentValue,
			Expected:      mean,
			Deviation:     zScore,
			Severity:      rule.Severity,
			Timestamp:     now,
			DetectionType: rule.DetectionType,
			Description:   "Z-Score " + stringFloat(zScore) + " exceeds threshold " + stringFloat(rule.ZScoreThreshold),
		}
	}

	return nil
}

// detectIQR IQR 异常检测
func (d *AnomalyDetector) detectIQR(points []model.TimeSeriesPoint, rule *AnomalyRule, now time.Time) *AnomalyResult {
	if len(points) < 4 {
		return nil
	}

	sortedValues := make([]float64, len(points))
	for i, p := range points {
		sortedValues[i] = p.Value
	}
	sortFloats(sortedValues)

	q1 := calcPercentile(sortedValues, 25)
	q3 := calcPercentile(sortedValues, 75)
	iqr := q3 - q1

	if iqr == 0 {
		return nil
	}

	currentValue := points[len(points)-1].Value
	upperBound := q3 + rule.IQRMultiplier*iqr
	lowerBound := q1 - rule.IQRMultiplier*iqr

	if currentValue > upperBound || currentValue < lowerBound {
		direction := "above"
		bound := upperBound
		deviation := currentValue - upperBound
		if currentValue < lowerBound {
			direction = "below"
			bound = lowerBound
			deviation = lowerBound - currentValue
		}
		return &AnomalyResult{
			RuleID:        rule.ID,
			RuleName:      rule.Name,
			Metric:        rule.Metric,
			Labels:        rule.Labels,
			Value:         currentValue,
			Expected:      (q1 + q3) / 2,
			Deviation:     deviation,
			Severity:      rule.Severity,
			Timestamp:     now,
			DetectionType: rule.DetectionType,
			Description:   "Value " + stringFloat(currentValue) + " is " + direction + " IQR bound " + stringFloat(bound),
		}
	}

	return nil
}

// detectEWMA 指数加权移动平均检测
func (d *AnomalyDetector) detectEWMA(points []model.TimeSeriesPoint, rule *AnomalyRule, now time.Time) *AnomalyResult {
	if len(points) < 2 {
		return nil
	}

	alpha := rule.EWMAAlpha
	if alpha <= 0 || alpha > 1 {
		alpha = 0.2 // 默认 alpha
	}

	// 计算 EWMA
	ewma := points[0].Value
	for i := 1; i < len(points); i++ {
		ewma = alpha*points[i].Value + (1-alpha)*ewma
	}

	// 计算 EWMA 的标准差
	varSum := 0.0
	for _, p := range points {
		diff := p.Value - ewma
		varSum += diff * diff
	}
	ewmaStddev := math.Sqrt(varSum / float64(len(points)))

	if ewmaStddev == 0 {
		return nil
	}

	currentValue := points[len(points)-1].Value
	upperBound := ewma + rule.EWMAThreshold*ewmaStddev
	lowerBound := ewma - rule.EWMAThreshold*ewmaStddev

	if currentValue > upperBound {
		return &AnomalyResult{
			RuleID:        rule.ID,
			RuleName:      rule.Name,
			Metric:        rule.Metric,
			Labels:        rule.Labels,
			Value:         currentValue,
			Expected:      ewma,
			Deviation:     currentValue - ewma,
			Severity:      rule.Severity,
			Timestamp:     now,
			DetectionType: rule.DetectionType,
			Description:   "Value " + stringFloat(currentValue) + " exceeds EWMA bound " + stringFloat(upperBound),
		}
	}

	if currentValue < lowerBound {
		return &AnomalyResult{
			RuleID:        rule.ID,
			RuleName:      rule.Name,
			Metric:        rule.Metric,
			Labels:        rule.Labels,
			Value:         currentValue,
			Expected:      ewma,
			Deviation:     ewma - currentValue,
			Severity:      rule.Severity,
			Timestamp:     now,
			DetectionType: rule.DetectionType,
			Description:   "Value " + stringFloat(currentValue) + " below EWMA bound " + stringFloat(lowerBound),
		}
	}

	return nil
}

// 辅助函数
func calcMean(points []model.TimeSeriesPoint) float64 {
	if len(points) == 0 {
		return 0
	}
	sum := 0.0
	for _, p := range points {
		sum += p.Value
	}
	return sum / float64(len(points))
}

func calcStddev(points []model.TimeSeriesPoint) float64 {
	if len(points) < 2 {
		return 0
	}
	mean := calcMean(points)
	varSum := 0.0
	for _, p := range points {
		diff := p.Value - mean
		varSum += diff * diff
	}
	return math.Sqrt(varSum / float64(len(points)))
}

func calcPercentile(sorted []float64, percentile float64) float64 {
	if len(sorted) == 0 {
		return 0
	}
	if len(sorted) == 1 {
		return sorted[0]
	}

	rank := (percentile / 100.0) * float64(len(sorted)-1)
	lower := int(math.Floor(rank))
	upper := int(math.Ceil(rank))

	if lower == upper || upper >= len(sorted) {
		return sorted[lower]
	}

	frac := rank - float64(lower)
	return sorted[lower]*(1-frac) + sorted[upper]*frac
}

func sortFloats(a []float64) {
	// 简单的插入排序，避免 import sort
	for i := 1; i < len(a); i++ {
		key := a[i]
		j := i - 1
		for j >= 0 && a[j] > key {
			a[j+1] = a[j]
			j--
		}
		a[j+1] = key
	}
}
