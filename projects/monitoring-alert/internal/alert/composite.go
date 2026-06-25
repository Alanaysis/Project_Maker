package alert

import (
	"fmt"
	"strings"
	"sync"
	"time"

	"github.com/monitoring-alert/internal/model"
	"github.com/monitoring-alert/internal/storage"
)

// LogicalOperator 逻辑运算符
type LogicalOperator string

const (
	LogicalAnd LogicalOperator = "AND"
	LogicalOr  LogicalOperator = "OR"
)

// CompositeCondition 组合条件
type CompositeCondition struct {
	Conditions []Condition      `json:"conditions"`
	Operator   LogicalOperator  `json:"operator"`
}

// Evaluate 评估组合条件
func (cc *CompositeCondition) Evaluate(values []float64) bool {
	if len(values) != len(cc.Conditions) {
		return false
	}

	switch cc.Operator {
	case LogicalAnd:
		for i, cond := range cc.Conditions {
			if !cond.Evaluate(values[i]) {
				return false
			}
		}
		return true
	case LogicalOr:
		for i, cond := range cc.Conditions {
			if cond.Evaluate(values[i]) {
				return true
			}
		}
		return false
	default:
		return false
	}
}

// CompositeRule 组合告警规则
type CompositeRule struct {
	mu          sync.RWMutex
	ID          string               `json:"id"`
	Name        string               `json:"name"`
	Expr        string               `json:"expr"`
	Severity    model.AlertSeverity  `json:"severity"`
	Labels      map[string]string    `json:"labels"`
	Annotations map[string]string    `json:"annotations"`
	For         time.Duration        `json:"for"`
	Enabled     bool                 `json:"enabled"`
	CreatedAt   time.Time            `json:"created_at"`
	UpdatedAt   time.Time            `json:"updated_at"`
}

// NewCompositeRule 创建组合告警规则
func NewCompositeRule(id, name, expr string, severity model.AlertSeverity) *CompositeRule {
	now := time.Now()
	return &CompositeRule{
		ID:          id,
		Name:        name,
		Expr:        expr,
		Severity:    severity,
		Labels:      make(map[string]string),
		Annotations: make(map[string]string),
		Enabled:     true,
		CreatedAt:   now,
		UpdatedAt:   now,
	}
}

// SetFor 设置持续时间
func (r *CompositeRule) SetFor(d time.Duration) *CompositeRule {
	r.mu.Lock()
	defer r.mu.Unlock()
	r.For = d
	r.UpdatedAt = time.Now()
	return r
}

// SetEnabled 设置启用状态
func (r *CompositeRule) SetEnabled(enabled bool) {
	r.mu.Lock()
	defer r.mu.Unlock()
	r.Enabled = enabled
	r.UpdatedAt = time.Now()
}

// IsEnabled 检查是否启用
func (r *CompositeRule) IsEnabled() bool {
	r.mu.RLock()
	defer r.mu.RUnlock()
	return r.Enabled
}

// ParseCompositeCondition 解析组合条件表达式
// 格式: "metric1 > 80 AND metric2 < 50" 或 "metric1 > 80 OR metric2 > 90"
func ParseCompositeCondition(expr string) (*CompositeCondition, error) {
	// 尝试解析 AND
	if strings.Contains(expr, " AND ") {
		parts := strings.Split(expr, " AND ")
		conditions := make([]Condition, 0, len(parts))
		for _, part := range parts {
			cond, err := ParseCondition(strings.TrimSpace(part))
			if err != nil {
				return nil, fmt.Errorf("failed to parse condition '%s': %w", part, err)
			}
			conditions = append(conditions, *cond)
		}
		return &CompositeCondition{
			Conditions: conditions,
			Operator:   LogicalAnd,
		}, nil
	}

	// 尝试解析 OR
	if strings.Contains(expr, " OR ") {
		parts := strings.Split(expr, " OR ")
		conditions := make([]Condition, 0, len(parts))
		for _, part := range parts {
			cond, err := ParseCondition(strings.TrimSpace(part))
			if err != nil {
				return nil, fmt.Errorf("failed to parse condition '%s': %w", part, err)
			}
			conditions = append(conditions, *cond)
		}
		return &CompositeCondition{
			Conditions: conditions,
			Operator:   LogicalOr,
		}, nil
	}

	// 单个条件
	cond, err := ParseCondition(expr)
	if err != nil {
		return nil, err
	}
	return &CompositeCondition{
		Conditions: []Condition{*cond},
		Operator:   LogicalAnd,
	}, nil
}

// CompositeEvaluator 组合规则评估器
type CompositeEvaluator struct {
	mu       sync.RWMutex
	rules    map[string]*CompositeRule
	condMap  map[string]*CompositeCondition
	db       storage.TimeSeriesDB
	alerts   map[string]*model.Alert
}

// NewCompositeEvaluator 创建组合规则评估器
func NewCompositeEvaluator(db storage.TimeSeriesDB) *CompositeEvaluator {
	return &CompositeEvaluator{
		rules:   make(map[string]*CompositeRule),
		condMap: make(map[string]*CompositeCondition),
		db:      db,
		alerts:  make(map[string]*model.Alert),
	}
}

// AddRule 添加规则
func (e *CompositeEvaluator) AddRule(rule *CompositeRule) error {
	e.mu.Lock()
	defer e.mu.Unlock()

	cond, err := ParseCompositeCondition(rule.Expr)
	if err != nil {
		return fmt.Errorf("failed to parse rule expression: %w", err)
	}

	e.rules[rule.ID] = rule
	e.condMap[rule.ID] = cond
	return nil
}

// RemoveRule 移除规则
func (e *CompositeEvaluator) RemoveRule(ruleID string) {
	e.mu.Lock()
	defer e.mu.Unlock()

	delete(e.rules, ruleID)
	delete(e.condMap, ruleID)
}

// ListRules 列出所有规则
func (e *CompositeEvaluator) ListRules() []*CompositeRule {
	e.mu.RLock()
	defer e.mu.RUnlock()

	rules := make([]*CompositeRule, 0, len(e.rules))
	for _, rule := range e.rules {
		rules = append(rules, rule)
	}
	return rules
}

// Evaluate 评估所有规则
func (e *CompositeEvaluator) Evaluate() ([]*model.Alert, error) {
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
func (e *CompositeEvaluator) evaluateRule(rule *CompositeRule, cond *CompositeCondition) (*model.Alert, error) {
	// 获取所有指标的最新值
	values := make([]float64, len(cond.Conditions))
	for i, c := range cond.Conditions {
		value, ok := e.db.GetLatest(c.Metric, c.Labels)
		if !ok {
			return nil, fmt.Errorf("metric not found: %s", c.Metric)
		}
		values[i] = value
	}

	// 评估组合条件
	if !cond.Evaluate(values) {
		return nil, nil
	}

	// 检查是否已有相同的告警
	for _, alert := range e.alerts {
		if alert.RuleID == rule.ID && alert.GetStatus() == model.AlertStatusFiring {
			return nil, nil
		}
	}

	// 创建新告警
	alert := model.NewAlert(rule.ID, rule.Name, rule.Severity, rule.Labels)
	// 使用第一个指标的值作为触发值
	alert.SetValue(values[0], cond.Conditions[0].Threshold)
	alert.SetStatus(model.AlertStatusFiring)
	return alert, nil
}

// GetActiveAlerts 获取活跃告警
func (e *CompositeEvaluator) GetActiveAlerts() []*model.Alert {
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
func (e *CompositeEvaluator) ResolveAlert(alertID string) error {
	e.mu.Lock()
	defer e.mu.Unlock()

	alert, ok := e.alerts[alertID]
	if !ok {
		return fmt.Errorf("alert not found: %s", alertID)
	}

	alert.SetStatus(model.AlertStatusResolved)
	return nil
}
