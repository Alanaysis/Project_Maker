package alert

import (
	"fmt"
	"sync"
	"time"

	"github.com/monitoring-alert/internal/model"
	"github.com/monitoring-alert/internal/storage"
)

// TrendType 趋势类型
type TrendType int

const (
	// TrendTypeIncrease 增长趋势
	TrendTypeIncrease TrendType = iota
	// TrendTypeDecrease 下降趋势
	TrendTypeDecrease
	// TrendTypeSpike 突增趋势
	TrendTypeSpike
)

// String 返回趋势类型的字符串表示
func (t TrendType) String() string {
	switch t {
	case TrendTypeIncrease:
		return "increase"
	case TrendTypeDecrease:
		return "decrease"
	case TrendTypeSpike:
		return "spike"
	default:
		return "unknown"
	}
}

// TrendRule 趋势告警规则
type TrendRule struct {
	mu           sync.RWMutex
	ID           string            `json:"id"`
	Name         string            `json:"name"`
	Metric       string            `json:"metric"`
	Labels       map[string]string `json:"labels"`
	TrendType    TrendType         `json:"trend_type"`
	Threshold    float64           `json:"threshold"`     // 变化阈值（百分比或绝对值）
	Window       time.Duration     `json:"window"`        // 检测窗口
	IsPercentage bool              `json:"is_percentage"` // 是否为百分比阈值
	Severity     model.AlertSeverity `json:"severity"`
	Enabled      bool              `json:"enabled"`
	CreatedAt    time.Time         `json:"created_at"`
	UpdatedAt    time.Time         `json:"updated_at"`
}

// NewTrendRule 创建趋势告警规则
func NewTrendRule(id, name, metric string, trendType TrendType, threshold float64, window time.Duration, isPercentage bool, severity model.AlertSeverity) *TrendRule {
	now := time.Now()
	return &TrendRule{
		ID:           id,
		Name:         name,
		Metric:       metric,
		Labels:       make(map[string]string),
		TrendType:    trendType,
		Threshold:    threshold,
		Window:       window,
		IsPercentage: isPercentage,
		Severity:     severity,
		Enabled:      true,
		CreatedAt:    now,
		UpdatedAt:    now,
	}
}

// SetLabels 设置标签
func (r *TrendRule) SetLabels(labels map[string]string) *TrendRule {
	r.mu.Lock()
	defer r.mu.Unlock()
	r.Labels = labels
	r.UpdatedAt = time.Now()
	return r
}

// SetEnabled 设置启用状态
func (r *TrendRule) SetEnabled(enabled bool) {
	r.mu.Lock()
	defer r.mu.Unlock()
	r.Enabled = enabled
	r.UpdatedAt = time.Now()
}

// IsEnabled 检查是否启用
func (r *TrendRule) IsEnabled() bool {
	r.mu.RLock()
	defer r.mu.RUnlock()
	return r.Enabled
}

// TrendEvaluator 趋势评估器
type TrendEvaluator struct {
	mu       sync.RWMutex
	rules    map[string]*TrendRule
	db       storage.TimeSeriesDB
	alerts   map[string]*model.Alert
}

// NewTrendEvaluator 创建趋势评估器
func NewTrendEvaluator(db storage.TimeSeriesDB) *TrendEvaluator {
	return &TrendEvaluator{
		rules:  make(map[string]*TrendRule),
		db:     db,
		alerts: make(map[string]*model.Alert),
	}
}

// AddRule 添加规则
func (e *TrendEvaluator) AddRule(rule *TrendRule) {
	e.mu.Lock()
	defer e.mu.Unlock()
	e.rules[rule.ID] = rule
}

// RemoveRule 移除规则
func (e *TrendEvaluator) RemoveRule(ruleID string) {
	e.mu.Lock()
	defer e.mu.Unlock()
	delete(e.rules, ruleID)
}

// ListRules 列出所有规则
func (e *TrendEvaluator) ListRules() []*TrendRule {
	e.mu.RLock()
	defer e.mu.RUnlock()

	rules := make([]*TrendRule, 0, len(e.rules))
	for _, rule := range e.rules {
		rules = append(rules, rule)
	}
	return rules
}

// Evaluate 评估所有规则
func (e *TrendEvaluator) Evaluate() ([]*model.Alert, error) {
	e.mu.Lock()
	defer e.mu.Unlock()

	var newAlerts []*model.Alert
	for _, rule := range e.rules {
		if !rule.IsEnabled() {
			continue
		}

		alert, err := e.evaluateRule(rule)
		if err != nil {
			continue
		}

		if alert != nil {
			newAlerts = append(newAlerts, alert)
			e.alerts[alert.ID] = alert
		}
	}

	return newAlerts, nil
}

// evaluateRule 评估单个规则
func (e *TrendEvaluator) evaluateRule(rule *TrendRule) (*model.Alert, error) {
	// 获取时间窗口内的数据
	end := time.Now()
	start := end.Add(-rule.Window)

	ts, err := e.db.Read(rule.Metric, rule.Labels, start, end)
	if err != nil {
		return nil, err
	}

	points := ts.GetPoints()
	if len(points) < 2 {
		return nil, fmt.Errorf("insufficient data points for trend analysis")
	}

	// 计算趋势
	trendValue := calculateTrend(points, rule.TrendType, rule.IsPercentage)

	// 评估是否触发告警
	if !evaluateTrendThreshold(trendValue, rule.TrendType, rule.Threshold) {
		return nil, nil
	}

	// 检查是否已有相同的告警
	for _, alert := range e.alerts {
		if alert.RuleID == rule.ID && alert.GetStatus() == model.AlertStatusFiring {
			// 更新现有告警的值
			alert.SetValue(trendValue, rule.Threshold)
			return nil, nil
		}
	}

	// 创建新告警
	alert := model.NewAlert(rule.ID, rule.Name, rule.Severity, rule.Labels)
	alert.SetValue(trendValue, rule.Threshold)
	alert.SetStatus(model.AlertStatusFiring)
	return alert, nil
}

// calculateTrend 计算趋势值
func calculateTrend(points []model.TimeSeriesPoint, trendType TrendType, isPercentage bool) float64 {
	if len(points) < 2 {
		return 0
	}

	firstValue := points[0].Value
	lastValue := points[len(points)-1].Value

	if isPercentage {
		// 计算百分比变化
		if firstValue == 0 {
			if lastValue > 0 {
				return 100.0
			}
			return 0
		}
		return ((lastValue - firstValue) / firstValue) * 100
	}

	// 计算绝对值变化
	return lastValue - firstValue
}

// evaluateTrendThreshold 评估趋势阈值
func evaluateTrendThreshold(trendValue float64, trendType TrendType, threshold float64) bool {
	switch trendType {
	case TrendTypeIncrease:
		return trendValue > threshold
	case TrendTypeDecrease:
		return trendValue < -threshold
	case TrendTypeSpike:
		absValue := trendValue
		if absValue < 0 {
			absValue = -absValue
		}
		return absValue > threshold
	default:
		return false
	}
}

// GetActiveAlerts 获取活跃告警
func (e *TrendEvaluator) GetActiveAlerts() []*model.Alert {
	e.mu.RLock()
	defer e.mu.RUnlock()

	var alerts []*model.Alert
	for _, alert := range e.alerts {
		if alert.GetStatus() == model.AlertStatusFiring {
			alerts = append(alerts, alert)
		}
	}
	return alerts
}

// ResolveAlert 解决告警
func (e *TrendEvaluator) ResolveAlert(alertID string) error {
	e.mu.Lock()
	defer e.mu.Unlock()

	alert, ok := e.alerts[alertID]
	if !ok {
		return fmt.Errorf("alert not found: %s", alertID)
	}

	alert.SetStatus(model.AlertStatusResolved)
	return nil
}
