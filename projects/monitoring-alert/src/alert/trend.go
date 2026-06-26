package alert

import (
	"fmt"
	"time"

	"github.com/monitoring-alert/internal/model"
)

// TrendEvaluator 趋势评估器
type TrendEvaluator struct {
	db        TimeSeriesDB
	rules     []*TrendRule
	threshold *RuleEvaluator
}

// NewTrendEvaluator 创建趋势评估器
func NewTrendEvaluator(db TimeSeriesDB) *TrendEvaluator {
	return &TrendEvaluator{
		db:        db,
		rules:     make([]*TrendRule, 0),
		threshold: NewRuleEvaluator(db),
	}
}

// AddRule 添加趋势规则
func (e *TrendEvaluator) AddRule(rule *TrendRule) {
	e.rules = append(e.rules, rule)
}

// Evaluate 评估所有趋势规则
func (e *TrendEvaluator) Evaluate() ([]*model.Alert, error) {
	var alerts []*model.Alert

	for _, rule := range e.rules {
		alert, err := e.evaluateTrend(rule)
		if err != nil {
			continue
		}
		if alert != nil {
			alerts = append(alerts, alert)
		}
	}

	return alerts, nil
}

// evaluateTrend 评估单个趋势
func (e *TrendEvaluator) evaluateTrend(rule *TrendRule) (*model.Alert, error) {
	end := time.Now()
	start := end.Add(-rule.Window)

	var points []model.TimeSeriesPoint
	var tsLabels map[string]string

	// 如果规则没有指定标签，通过 Query 查找
	if len(rule.Labels) == 0 {
		tsList, err := e.db.Query(rule.Metric)
		if err != nil || len(tsList) == 0 {
			return nil, nil
		}
		for _, ts := range tsList {
			if ts.Metric == rule.Metric {
				tsLabels = ts.Labels
				if tsLabels == nil {
					tsLabels = make(map[string]string)
				}
				points = ts.GetPointsInRange(start, end)
				break
			}
		}
		if len(points) == 0 {
			return nil, nil
		}
	} else {
		ts, err := e.db.Read(rule.Metric, rule.Labels, start, end)
		if err != nil {
			return nil, err
		}
		points = ts.GetPoints()
		tsLabels = rule.Labels
	}

	if len(points) < 3 {
		return nil, nil
	}

	var trendScore float64

	switch rule.TrendType {
	case TrendTypeIncrease:
		trendScore = e.calculateIncrease(points)
	case TrendTypeDecrease:
		trendScore = e.calculateDecrease(points)
	case TrendTypeSpike:
		trendScore = e.calculateSpike(points)
	}

	if trendScore >= rule.Threshold {
		alert := model.NewAlert(rule.ID, rule.Name, rule.Severity, rule.Labels)
		alert.SetValue(trendScore, rule.Threshold)
		alert.SetStatus(model.AlertStatusFiring)
		return alert, nil
	}

	return nil, nil
}

// calculateIncrease 计算增长趋势
func (e *TrendEvaluator) calculateIncrease(points []model.TimeSeriesPoint) float64 {
	// 计算前后半段的平均值差
	mid := len(points) / 2
	if mid == 0 {
		return 0
	}

	firstHalf := 0.0
	secondHalf := 0.0

	for _, p := range points[:mid] {
		firstHalf += p.Value
	}
	for _, p := range points[mid:] {
		secondHalf += p.Value
	}

	firstHalf /= float64(mid)
	secondHalf /= float64(len(points) - mid)

	return secondHalf - firstHalf
}

// calculateDecrease 计算下降趋势
func (e *TrendEvaluator) calculateDecrease(points []model.TimeSeriesPoint) float64 {
	mid := len(points) / 2
	if mid == 0 {
		return 0
	}

	firstHalf := 0.0
	secondHalf := 0.0

	for _, p := range points[:mid] {
		firstHalf += p.Value
	}
	for _, p := range points[mid:] {
		secondHalf += p.Value
	}

	firstHalf /= float64(mid)
	secondHalf /= float64(len(points) - mid)

	return firstHalf - secondHalf
}

// calculateSpike 计算尖峰
func (e *TrendEvaluator) calculateSpike(points []model.TimeSeriesPoint) float64 {
	if len(points) < 2 {
		return 0
	}

	mean := 0.0
	for _, p := range points {
		mean += p.Value
	}
	mean /= float64(len(points))

	// 计算最大值与平均值的差
	max := points[0].Value
	for _, p := range points[1:] {
		if p.Value > max {
			max = p.Value
		}
	}

	return max - mean
}

// TrendType 趋势类型
type TrendType string

const (
	// TrendTypeIncrease 增长趋势
	TrendTypeIncrease TrendType = "increase"
	// TrendTypeDecrease 下降趋势
	TrendTypeDecrease TrendType = "decrease"
	// TrendTypeSpike 尖峰
	TrendTypeSpike TrendType = "spike"
)

// TrendRule 趋势规则
type TrendRule struct {
	ID        string
	Name      string
	Metric    string
	Labels    map[string]string
	TrendType TrendType
	Threshold float64
	Window    time.Duration
	For       time.Duration
	Enabled   bool
	Severity  model.AlertSeverity
}

// NewTrendRule 创建趋势规则
func NewTrendRule(id, name, metric string, trendType TrendType, threshold float64, window time.Duration, enabled bool, severity model.AlertSeverity) *TrendRule {
	return &TrendRule{
		ID:        id,
		Name:      name,
		Metric:    metric,
		Labels:    make(map[string]string),
		TrendType: trendType,
		Threshold: threshold,
		Window:    window,
		Enabled:   enabled,
		Severity:  severity,
	}
}

func (r *TrendRule) String() string {
	return fmt.Sprintf("TrendRule{%s: %s %s > %.1f}", r.ID, r.Metric, r.TrendType, r.Threshold)
}
