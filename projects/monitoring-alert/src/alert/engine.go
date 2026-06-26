package alert

import (
	"fmt"
	"sort"
	"strings"
	"time"

	"github.com/monitoring-alert/internal/model"
	"github.com/monitoring-alert/src/aggregation"
)

// RuleEvaluator 告警规则评估器
type RuleEvaluator struct {
	db       TimeSeriesDB
	aggFunc  *aggregation.AggregationFunc
	rules    []*model.AlertRule
	knownAlerts map[string]*model.Alert
}

// TimeSeriesDB 时序数据库接口
type TimeSeriesDB interface {
	Read(metric string, labels map[string]string, start, end time.Time) (*model.TimeSeries, error)
	GetLatest(metric string, labels map[string]string) (float64, bool)
	List() []string
	Query(query string) ([]*model.TimeSeries, error)
}

// NewRuleEvaluator 创建规则评估器
func NewRuleEvaluator(db TimeSeriesDB) *RuleEvaluator {
	return &RuleEvaluator{
		db:            db,
		aggFunc:       aggregation.NewAggregationFunc(db),
		rules:         make([]*model.AlertRule, 0),
		knownAlerts:   make(map[string]*model.Alert),
	}
}

// AddRule 添加告警规则
func (e *RuleEvaluator) AddRule(rule *model.AlertRule) {
	e.rules = append(e.rules, rule)
}

// RemoveRule 移除告警规则
func (e *RuleEvaluator) RemoveRule(id string) {
	for i, rule := range e.rules {
		if rule.ID == id {
			e.rules = append(e.rules[:i], e.rules[i+1:]...)
			break
		}
	}
}

// GetRules 获取所有规则
func (e *RuleEvaluator) GetRules() []*model.AlertRule {
	return e.rules
}

// Evaluate 评估所有规则
func (e *RuleEvaluator) Evaluate() ([]*model.Alert, error) {
	var firingAlerts []*model.Alert

	for _, rule := range e.rules {
		if !rule.IsEnabled() {
			continue
		}

		alerts, err := e.evaluateRule(rule)
		if err != nil {
			return firingAlerts, err
		}
		firingAlerts = append(firingAlerts, alerts...)
	}

	return firingAlerts, nil
}

// evaluateRule 评估单个规则
func (e *RuleEvaluator) evaluateRule(rule *model.AlertRule) ([]*model.Alert, error) {
	// 解析表达式
	parsed, err := parseExpr(rule.Expr)
	if err != nil {
		return nil, fmt.Errorf("rule %s: parse error: %w", rule.ID, err)
	}

	// 获取指标数据
	value, labels, err := e.getMetricValue(parsed.Metric, parsed.Labels)
	if err != nil {
		return nil, fmt.Errorf("rule %s: get metric error: %w", rule.ID, err)
	}

	// 检查阈值
	if !matchesThreshold(value, parsed.Operator, parsed.Threshold) {
		return nil, nil
	}

	// 检查持续时间
	if rule.For > 0 {
		if !e.checkDuration(rule.ID, parsed.Operator, parsed.Threshold, value, labels, rule.For) {
			return nil, nil
		}
	}

	// 创建告警
	alert := model.NewAlert(rule.ID, rule.Name, rule.Severity, labels)
	alert.SetValue(value, parsed.Threshold)
	alert.SetStatus(model.AlertStatusFiring)

	e.knownAlerts[alert.ID] = alert
	return []*model.Alert{alert}, nil
}

// getMetricValue 获取指标值
func (e *RuleEvaluator) getMetricValue(metric string, labels map[string]string) (float64, map[string]string, error) {
	// 如果传入空标签，尝试查找该指标名的最新值
	if len(labels) == 0 {
		tsList, err := e.db.Query(metric)
		if err == nil && len(tsList) > 0 {
			for _, ts := range tsList {
				if ts.Metric == metric {
					point, ok := ts.Latest()
					if ok {
						return point.Value, ts.Labels, nil
					}
				}
			}
		}
		return 0, labels, fmt.Errorf("no data for %s", metric)
	}

	value, ok := e.db.GetLatest(metric, labels)
	if !ok {
		return 0, labels, fmt.Errorf("no data for %s", metric)
	}
	return value, labels, nil
}

// checkDuration 检查持续时间条件
func (e *RuleEvaluator) checkDuration(ruleID string, operator string, threshold float64, value float64, labels map[string]string, forDuration time.Duration) bool {
	// 简化实现：检查最近 forDuration 时间内的数据是否都满足条件
	end := time.Now()
	start := end.Add(-forDuration)

	ts, err := e.db.Read(ruleID, labels, start, end)
	if err != nil {
		return false
	}

	points := ts.GetPoints()
	if len(points) == 0 {
		return false
	}

	// 检查所有点是否都满足条件
	for _, p := range points {
		if !matchesThreshold(p.Value, operator, threshold) {
			return false
		}
	}

	return true
}

// matchesThreshold 检查是否满足阈值条件
func matchesThreshold(value float64, operator string, threshold float64) bool {
	switch operator {
	case ">":
		return value > threshold
	case ">=":
		return value >= threshold
	case "<":
		return value < threshold
	case "<=":
		return value <= threshold
	case "==":
		return value == threshold
	case "!=":
		return value != threshold
	default:
		return false
	}
}

// AlertExpr 解析后的表达式
type AlertExpr struct {
	Metric   string
	Labels   map[string]string
	Operator string
	Threshold float64
}

// parseExpr 解析告警表达式
func parseExpr(expr string) (*AlertExpr, error) {
	expr = strings.TrimSpace(expr)

	// 格式: metric_name [labels] operator threshold
	// 例如: cpu_usage > 80 或 cpu_usage{host=web-01} >= 80

	parts := strings.Fields(expr)
	if len(parts) < 3 {
		return nil, fmt.Errorf("invalid expression: %s", expr)
	}

	result := &AlertExpr{
		Labels: make(map[string]string),
	}

	// 解析指标名和标签
	namePart := parts[0]
	if strings.Contains(namePart, "{") {
		// 有标签
		braceIdx := strings.Index(namePart, "{")
		result.Metric = namePart[:braceIdx]
		labelStr := namePart[braceIdx+1 : len(namePart)-1]
		result.Labels = parseLabels(labelStr)
	} else {
		result.Metric = namePart
	}

	// 解析操作符
	result.Operator = parts[1]

	// 解析阈值
	var err error
	result.Threshold, err = parseFloat(parts[2])
	if err != nil {
		return nil, fmt.Errorf("invalid threshold: %s", parts[2])
	}

	return result, nil
}

// parseLabels 解析标签字符串
func parseLabels(labelStr string) map[string]string {
	labels := make(map[string]string)
	pairs := strings.Split(labelStr, ",")
	for _, pair := range pairs {
		kv := strings.Split(pair, "=")
		if len(kv) == 2 {
			labels[strings.TrimSpace(kv[0])] = strings.TrimSpace(kv[1])
		}
	}
	return labels
}

// parseFloat 解析浮点数
func parseFloat(s string) (float64, error) {
	var result float64
	var negative bool
	var i int

	if s[0] == '-' {
		negative = true
		i = 1
	} else if s[0] == '+' {
		i = 1
	}

	for ; i < len(s); i++ {
		c := s[i]
		if c == '.' {
			i++
			divisor := 1.0
			for i < len(s) && s[i] >= '0' && s[i] <= '9' {
				result = result*10 + float64(s[i]-'0')
				divisor *= 10
				i++
			}
			result /= divisor
			break
		}
		if c >= '0' && c <= '9' {
			result = result*10 + float64(c-'0')
		}
	}

	if negative {
		result = -result
	}
	return result, nil
}

// AlertManager 告警管理器
type AlertManager struct {
	evaluator   *RuleEvaluator
	notifiers   []Notifier
	history     []*model.Alert
	maxHistory  int
	throttleMap map[string]time.Time
	throttleDur time.Duration
}

// Notifier 通知器接口
type Notifier interface {
	Notify(alert interface{}) error
	Name() string
}

// NewAlertManager 创建告警管理器
func NewAlertManager(evaluator *RuleEvaluator, maxHistory int) *AlertManager {
	return &AlertManager{
		evaluator:   evaluator,
		history:     make([]*model.Alert, 0),
		maxHistory:  maxHistory,
		throttleMap: make(map[string]time.Time),
		throttleDur: 5 * time.Minute,
	}
}

// AddNotifier 添加通知器
func (m *AlertManager) AddNotifier(n Notifier) {
	m.notifiers = append(m.notifiers, n)
}

// CheckAndNotify 检查并通知
func (m *AlertManager) CheckAndNotify() []*model.Alert {
	alerts, err := m.evaluator.Evaluate()
	if err != nil {
		return nil
	}

	now := time.Now()
	var throttledAlerts []*model.Alert
	for _, alert := range alerts {
		// 节流检查 - 使用 rule ID 作为节流键
		key := alert.RuleID
		if lastTime, ok := m.throttleMap[key]; ok {
			if now.Sub(lastTime) < m.throttleDur {
				continue
			}
		}

		// 发送通知
		for _, n := range m.notifiers {
			if err := n.Notify(alert); err != nil {
				continue
			}
		}

		m.throttleMap[key] = now
		m.history = append(m.history, alert)
		throttledAlerts = append(throttledAlerts, alert)

		// 保持历史记录限制
		if len(m.history) > m.maxHistory {
			m.history = m.history[len(m.history)-m.maxHistory:]
		}
	}

	return throttledAlerts
}

// GetHistory 获取告警历史
func (m *AlertManager) GetHistory() []*model.Alert {
	return m.history
}

// GetHistoryCount 获取历史告警数量
func (m *AlertManager) GetHistoryCount() int {
	return len(m.history)
}

// GetAggregationStats 获取聚合统计（用于告警上下文）
func (m *AlertManager) GetAggregationStats(metric string, labels map[string]string, duration time.Duration) (*aggregation.AggregationResult, error) {
	return m.evaluator.aggFunc.Aggregate(metric, labels, time.Now().Add(-duration), time.Now(), aggregation.AggAvg)
}

// FormatAlertSummary 格式化告警摘要
func FormatAlertSummary(alerts []*model.Alert) string {
	if len(alerts) == 0 {
		return "No alerts"
	}

	// 按严重程度排序
	sorted := make([]*model.Alert, len(alerts))
	copy(sorted, alerts)
	sort.Slice(sorted, func(i, j int) bool {
		return sorted[i].Severity > sorted[j].Severity
	})

	var parts []string
	for _, a := range sorted {
		parts = append(parts, fmt.Sprintf("[%s] %s: value=%.2f threshold=%.2f",
			a.Severity.String(), a.RuleName, a.Value, a.Threshold))
	}

	return strings.Join(parts, " | ")
}
