package alert

import (
	"fmt"
	"strings"
	"sync"
	"time"

	"github.com/monitoring-alert/internal/model"
	"github.com/monitoring-alert/internal/storage"
)

// Operator 比较运算符
type Operator string

const (
	OpGreaterThan         Operator = ">"
	OpGreaterThanOrEqual  Operator = ">="
	OpLessThan            Operator = "<"
	OpLessThanOrEqual     Operator = "<="
	OpEqual               Operator = "=="
	OpNotEqual            Operator = "!="
)

// Condition 告警条件
type Condition struct {
	Metric   string   `json:"metric"`
	Operator Operator `json:"operator"`
	Threshold float64 `json:"threshold"`
	Duration  time.Duration `json:"duration"`
	Labels    map[string]string `json:"labels"`
}

// Evaluate 评估条件
func (c *Condition) Evaluate(value float64) bool {
	switch c.Operator {
	case OpGreaterThan:
		return value > c.Threshold
	case OpGreaterThanOrEqual:
		return value >= c.Threshold
	case OpLessThan:
		return value < c.Threshold
	case OpLessThanOrEqual:
		return value <= c.Threshold
	case OpEqual:
		return value == c.Threshold
	case OpNotEqual:
		return value != c.Threshold
	default:
		return false
	}
}

// ParseCondition 解析条件表达式
func ParseCondition(expr string) (*Condition, error) {
	// 格式: metric_name operator threshold [for duration]
	// 示例: cpu_usage > 80 for 5m
	parts := strings.Fields(expr)
	if len(parts) < 3 {
		return nil, fmt.Errorf("invalid expression: %s", expr)
	}

	cond := &Condition{
		Metric: parts[0],
		Labels: make(map[string]string),
	}

	switch parts[1] {
	case ">":
		cond.Operator = OpGreaterThan
	case ">=":
		cond.Operator = OpGreaterThanOrEqual
	case "<":
		cond.Operator = OpLessThan
	case "<=":
		cond.Operator = OpLessThanOrEqual
	case "==":
		cond.Operator = OpEqual
	case "!=":
		cond.Operator = OpNotEqual
	default:
		return nil, fmt.Errorf("unknown operator: %s", parts[1])
	}

	var threshold float64
	if _, err := fmt.Sscanf(parts[2], "%f", &threshold); err != nil {
		return nil, fmt.Errorf("invalid threshold: %s", parts[2])
	}
	cond.Threshold = threshold

	// 解析可选的 for duration
	if len(parts) >= 5 && parts[3] == "for" {
		duration, err := time.ParseDuration(parts[4])
		if err != nil {
			return nil, fmt.Errorf("invalid duration: %s", parts[4])
		}
		cond.Duration = duration
	}

	return cond, nil
}

// RuleEvaluator 规则评估器
type RuleEvaluator struct {
	mu       sync.RWMutex
	rules    map[string]*model.AlertRule
	condMap  map[string]*Condition // rule ID -> condition
	db       storage.TimeSeriesDB
	alerts   map[string]*model.Alert // alert ID -> alert
}

// NewRuleEvaluator 创建规则评估器
func NewRuleEvaluator(db storage.TimeSeriesDB) *RuleEvaluator {
	return &RuleEvaluator{
		rules:   make(map[string]*model.AlertRule),
		condMap: make(map[string]*Condition),
		db:      db,
		alerts:  make(map[string]*model.Alert),
	}
}

// AddRule 添加规则
func (e *RuleEvaluator) AddRule(rule *model.AlertRule) error {
	e.mu.Lock()
	defer e.mu.Unlock()

	cond, err := ParseCondition(rule.Expr)
	if err != nil {
		return fmt.Errorf("failed to parse rule expression: %w", err)
	}

	e.rules[rule.ID] = rule
	e.condMap[rule.ID] = cond
	return nil
}

// RemoveRule 移除规则
func (e *RuleEvaluator) RemoveRule(ruleID string) {
	e.mu.Lock()
	defer e.mu.Unlock()

	delete(e.rules, ruleID)
	delete(e.condMap, ruleID)
}

// GetRule 获取规则
func (e *RuleEvaluator) GetRule(ruleID string) (*model.AlertRule, bool) {
	e.mu.RLock()
	defer e.mu.RUnlock()
	rule, ok := e.rules[ruleID]
	return rule, ok
}

// ListRules 列出所有规则
func (e *RuleEvaluator) ListRules() []*model.AlertRule {
	e.mu.RLock()
	defer e.mu.RUnlock()

	rules := make([]*model.AlertRule, 0, len(e.rules))
	for _, rule := range e.rules {
		rules = append(rules, rule)
	}
	return rules
}

// Evaluate 评估所有规则
func (e *RuleEvaluator) Evaluate() ([]*model.Alert, error) {
	e.mu.Lock()
	defer e.mu.Unlock()

	var newAlerts []*model.Alert
	for ruleID, rule := range e.rules {
		if !rule.IsEnabled() {
			continue
		}

		cond, ok := e.condMap[ruleID]
		if !ok {
			continue
		}

		alert, err := e.evaluateRule(rule, cond)
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
func (e *RuleEvaluator) evaluateRule(rule *model.AlertRule, cond *Condition) (*model.Alert, error) {
	// 获取指标的最新值
	value, ok := e.db.GetLatest(cond.Metric, cond.Labels)
	if !ok {
		return nil, fmt.Errorf("metric not found: %s", cond.Metric)
	}

	// 评估条件
	if !cond.Evaluate(value) {
		return nil, nil
	}

	// 检查是否已有相同的告警
	for _, alert := range e.alerts {
		if alert.RuleID == rule.ID && alert.GetStatus() == model.AlertStatusFiring {
			// 更新现有告警的值
			alert.SetValue(value, cond.Threshold)
			return nil, nil
		}
	}

	// 创建新告警
	alert := model.NewAlert(rule.ID, rule.Name, rule.Severity, rule.Labels)
	alert.SetValue(value, cond.Threshold)
	alert.SetStatus(model.AlertStatusFiring)
	return alert, nil
}

// GetActiveAlerts 获取活跃告警
func (e *RuleEvaluator) GetActiveAlerts() []*model.Alert {
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

// GetAlert 获取告警
func (e *RuleEvaluator) GetAlert(alertID string) (*model.Alert, bool) {
	e.mu.RLock()
	defer e.mu.RUnlock()
	alert, ok := e.alerts[alertID]
	return alert, ok
}

// ResolveAlert 解决告警
func (e *RuleEvaluator) ResolveAlert(alertID string) error {
	e.mu.Lock()
	defer e.mu.Unlock()

	alert, ok := e.alerts[alertID]
	if !ok {
		return fmt.Errorf("alert not found: %s", alertID)
	}

	alert.SetStatus(model.AlertStatusResolved)
	return nil
}

// CleanupResolvedAlerts 清理已解决的告警
func (e *RuleEvaluator) CleanupResolvedAlerts(olderThan time.Duration) int {
	e.mu.Lock()
	defer e.mu.Unlock()

	cutoff := time.Now().Add(-olderThan)
	count := 0

	for id, alert := range e.alerts {
		if alert.GetStatus() == model.AlertStatusResolved {
			if alert.EndsAt != nil && alert.EndsAt.Before(cutoff) {
				delete(e.alerts, id)
				count++
			}
		}
	}

	return count
}

// AlertManager 告警管理器
type AlertManager struct {
	mu         sync.RWMutex
	evaluator  *RuleEvaluator
	notifiers  []Notifier
	history    []*model.Alert
	maxHistory int
}

// Notifier 通知器接口
type Notifier interface {
	Name() string
	Notify(alert *model.Alert) error
}

// NewAlertManager 创建告警管理器
func NewAlertManager(evaluator *RuleEvaluator, maxHistory int) *AlertManager {
	return &AlertManager{
		evaluator:  evaluator,
		notifiers:  make([]Notifier, 0),
		history:    make([]*model.Alert, 0),
		maxHistory: maxHistory,
	}
}

// AddNotifier 添加通知器
func (m *AlertManager) AddNotifier(n Notifier) {
	m.mu.Lock()
	defer m.mu.Unlock()
	m.notifiers = append(m.notifiers, n)
}

// CheckAndNotify 检查并发送通知
func (m *AlertManager) CheckAndNotify() error {
	alerts, err := m.evaluator.Evaluate()
	if err != nil {
		return err
	}

	for _, alert := range alerts {
		// 记录历史
		m.mu.Lock()
		m.history = append(m.history, alert)
		if len(m.history) > m.maxHistory {
			m.history = m.history[len(m.history)-m.maxHistory:]
		}
		m.mu.Unlock()

		// 发送通知
		m.mu.RLock()
		for _, n := range m.notifiers {
			if err := n.Notify(alert); err != nil {
				// 记录错误但继续
				fmt.Printf("Failed to notify via %s: %v\n", n.Name(), err)
			}
		}
		m.mu.RUnlock()
	}

	return nil
}

// GetHistory 获取告警历史
func (m *AlertManager) GetHistory() []*model.Alert {
	m.mu.RLock()
	defer m.mu.RUnlock()

	result := make([]*model.Alert, len(m.history))
	copy(result, m.history)
	return result
}

// GetActiveAlerts 获取活跃告警
func (m *AlertManager) GetActiveAlerts() []*model.Alert {
	return m.evaluator.GetActiveAlerts()
}
