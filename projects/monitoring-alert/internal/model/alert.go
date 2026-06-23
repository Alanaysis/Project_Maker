package model

import (
	"fmt"
	"sync"
	"time"
)

// AlertSeverity 告警级别
type AlertSeverity int

const (
	// SeverityInfo 信息级别
	SeverityInfo AlertSeverity = iota
	// SeverityWarning 警告级别
	SeverityWarning
	// SeverityCritical 严重级别
	SeverityCritical
)

// String 返回告警级别的字符串表示
func (s AlertSeverity) String() string {
	switch s {
	case SeverityInfo:
		return "info"
	case SeverityWarning:
		return "warning"
	case SeverityCritical:
		return "critical"
	default:
		return "unknown"
	}
}

// AlertStatus 告警状态
type AlertStatus int

const (
	// AlertStatusPending 待确认
	AlertStatusPending AlertStatus = iota
	// AlertStatusFiring 触发中
	AlertStatusFiring
	// AlertStatusResolved 已解决
	AlertStatusResolved
)

// String 返回告警状态的字符串表示
func (s AlertStatus) String() string {
	switch s {
	case AlertStatusPending:
		return "pending"
	case AlertStatusFiring:
		return "firing"
	case AlertStatusResolved:
		return "resolved"
	default:
		return "unknown"
	}
}

// Alert 告警
type Alert struct {
	mu        sync.RWMutex
	ID        string            `json:"id"`
	RuleID    string            `json:"rule_id"`
	RuleName  string            `json:"rule_name"`
	Labels    map[string]string `json:"labels"`
	Value     float64           `json:"value"`
	Threshold float64           `json:"threshold"`
	Severity  AlertSeverity     `json:"severity"`
	Status    AlertStatus       `json:"status"`
	StartsAt  time.Time         `json:"starts_at"`
	EndsAt    *time.Time        `json:"ends_at,omitempty"`
	UpdatedAt time.Time         `json:"updated_at"`
}

// NewAlert 创建新的告警
func NewAlert(ruleID, ruleName string, severity AlertSeverity, labels map[string]string) *Alert {
	now := time.Now()
	return &Alert{
		ID:        fmt.Sprintf("%s-%d", ruleID, now.UnixNano()),
		RuleID:    ruleID,
		RuleName:  ruleName,
		Labels:    labels,
		Severity:  severity,
		Status:    AlertStatusPending,
		StartsAt:  now,
		UpdatedAt: now,
	}
}

// SetStatus 设置告警状态
func (a *Alert) SetStatus(status AlertStatus) {
	a.mu.Lock()
	defer a.mu.Unlock()
	a.Status = status
	a.UpdatedAt = time.Now()
	if status == AlertStatusResolved {
		now := time.Now()
		a.EndsAt = &now
	}
}

// GetStatus 获取告警状态
func (a *Alert) GetStatus() AlertStatus {
	a.mu.RLock()
	defer a.mu.RUnlock()
	return a.Status
}

// SetValue 设置触发值和阈值
func (a *Alert) SetValue(value, threshold float64) {
	a.mu.Lock()
	defer a.mu.Unlock()
	a.Value = value
	a.Threshold = threshold
	a.UpdatedAt = time.Now()
}

// String 返回告警的字符串表示
func (a *Alert) String() string {
	a.mu.RLock()
	defer a.mu.RUnlock()
	return fmt.Sprintf("[%s] %s: %s (value=%.2f, threshold=%.2f)",
		a.Severity, a.RuleName, a.Status, a.Value, a.Threshold)
}

// AlertRule 告警规则
type AlertRule struct {
	mu          sync.RWMutex
	ID          string            `json:"id"`
	Name        string            `json:"name"`
	Expr        string            `json:"expr"`
	Severity    AlertSeverity     `json:"severity"`
	Labels      map[string]string `json:"labels"`
	Annotations map[string]string `json:"annotations"`
	For         time.Duration     `json:"for"`
	Enabled     bool              `json:"enabled"`
	CreatedAt   time.Time         `json:"created_at"`
	UpdatedAt   time.Time         `json:"updated_at"`
}

// NewAlertRule 创建新的告警规则
func NewAlertRule(id, name, expr string, severity AlertSeverity) *AlertRule {
	now := time.Now()
	return &AlertRule{
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
func (r *AlertRule) SetFor(d time.Duration) *AlertRule {
	r.mu.Lock()
	defer r.mu.Unlock()
	r.For = d
	r.UpdatedAt = time.Now()
	return r
}

// SetEnabled 设置启用状态
func (r *AlertRule) SetEnabled(enabled bool) {
	r.mu.Lock()
	defer r.mu.Unlock()
	r.Enabled = enabled
	r.UpdatedAt = time.Now()
}

// IsEnabled 检查是否启用
func (r *AlertRule) IsEnabled() bool {
	r.mu.RLock()
	defer r.mu.RUnlock()
	return r.Enabled
}
