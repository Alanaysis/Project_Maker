package alert

import (
	"fmt"
	"strings"

	"github.com/monitoring-alert/internal/model"
)

// CompositeEvaluator 组合告警评估器
type CompositeEvaluator struct {
	db       TimeSeriesDB
	rules    []*CompositeRule
}

// NewCompositeEvaluator 创建组合告警评估器
func NewCompositeEvaluator(db TimeSeriesDB) *CompositeEvaluator {
	return &CompositeEvaluator{
		db:  db,
		rules: make([]*CompositeRule, 0),
	}
}

// AddRule 添加组合规则
func (e *CompositeEvaluator) AddRule(rule *CompositeRule) {
	e.rules = append(e.rules, rule)
}

// Evaluate 评估所有组合规则
func (e *CompositeEvaluator) Evaluate() ([]*model.Alert, error) {
	var alerts []*model.Alert

	for _, rule := range e.rules {
		if !rule.Enabled {
			continue
		}

		alert, err := e.evaluateComposite(rule)
		if err != nil {
			continue
		}
		if alert != nil {
			alerts = append(alerts, alert)
		}
	}

	return alerts, nil
}

// evaluateComposite 评估组合规则
func (e *CompositeEvaluator) evaluateComposite(rule *CompositeRule) (*model.Alert, error) {
	// 解析组合表达式
	conditions, err := parseCompositeExpr(rule.Expr)
	if err != nil {
		return nil, fmt.Errorf("parse error: %w", err)
	}

	// 评估每个条件
	var results []bool
	var details []string

	for _, cond := range conditions {
		var value float64
		var ok bool

		if len(cond.Labels) > 0 {
			value, ok = e.db.GetLatest(cond.Metric, cond.Labels)
		} else {
			// 没有指定标签，通过 Query 查找
			tsList, err := e.db.Query(cond.Metric)
			if err != nil || len(tsList) == 0 {
				details = append(details, fmt.Sprintf("%s: no data", cond.Metric))
				results = append(results, false)
				continue
			}
			ok = false
			for _, ts := range tsList {
				if ts.Metric == cond.Metric {
					if p, o := ts.Latest(); o {
						value = p.Value
						ok = o
						break
					}
				}
			}
		}

		if !ok {
			details = append(details, fmt.Sprintf("%s: no data", cond.Metric))
			results = append(results, false)
			continue
		}

		fired := matchesThreshold(value, cond.Operator, cond.Threshold)
		results = append(results, fired)
		details = append(details, fmt.Sprintf("%s %.2f %s %.2f",
			cond.Metric, value, cond.Operator, cond.Threshold))
	}

	// 根据逻辑运算符组合结果
	var finalResult bool
	switch rule.Operator {
	case "AND":
		finalResult = true
		for _, r := range results {
			if !r {
				finalResult = false
				break
			}
		}
	case "OR":
		finalResult = false
		for _, r := range results {
			if r {
				finalResult = true
				break
			}
		}
	}

	if finalResult {
		alert := model.NewAlert(rule.ID, rule.Name, rule.Severity, map[string]string{
			"conditions": strings.Join(details, "; "),
		})
		alert.SetValue(float64(len(results)), float64(len(conditions)))
		alert.SetStatus(model.AlertStatusFiring)
		return alert, nil
	}

	return nil, nil
}

// CompositeCondition 组合条件
type CompositeCondition struct {
	Metric   string
	Labels   map[string]string
	Operator string
	Threshold float64
}

// CompositeRule 组合告警规则
type CompositeRule struct {
	ID        string
	Name      string
	Expr      string
	Operator  string // AND / OR
	Severity  model.AlertSeverity
	Enabled   bool
}

// NewCompositeRule 创建组合告警规则
func NewCompositeRule(id, name, expr string, severity model.AlertSeverity) *CompositeRule {
	// 自动推断运算符
	operator := "AND"
	if strings.Contains(expr, " OR ") {
		operator = "OR"
	}

	return &CompositeRule{
		ID:       id,
		Name:     name,
		Expr:     expr,
		Operator: operator,
		Severity: severity,
		Enabled:  true,
	}
}

// parseCompositeExpr 解析组合表达式
func parseCompositeExpr(expr string) ([]*CompositeCondition, error) {
	// 按 AND/OR 分割
	var conditions []*CompositeCondition

	// 先尝试按 OR 分割
	orParts := strings.Split(expr, " OR ")
	if len(orParts) > 1 {
		for _, part := range orParts {
			conds, err := parseCompositeExpr(part)
			if err != nil {
				return nil, err
			}
			conditions = append(conditions, conds...)
		}
		return conditions, nil
	}

	// 按 AND 分割
	andParts := strings.Split(expr, " AND ")
	for _, part := range andParts {
		part = strings.TrimSpace(part)
		if part == "" {
			continue
		}
		cond, err := parseExpr(part)
		if err != nil {
			return nil, err
		}
		conditions = append(conditions, &CompositeCondition{
			Metric:    cond.Metric,
			Labels:    cond.Labels,
			Operator:  cond.Operator,
			Threshold: cond.Threshold,
		})
	}

	return conditions, nil
}
