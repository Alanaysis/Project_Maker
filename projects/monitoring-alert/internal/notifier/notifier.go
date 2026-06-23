package notifier

import (
	"fmt"
	"sync"
	"time"

	"github.com/monitoring-alert/internal/model"
)

// LogNotifier 日志通知器
type LogNotifier struct {
	mu      sync.RWMutex
	name    string
	alerts  []*model.Alert
	maxSize int
}

// NewLogNotifier 创建日志通知器
func NewLogNotifier(maxSize int) *LogNotifier {
	return &LogNotifier{
		name:    "log",
		alerts:  make([]*model.Alert, 0),
		maxSize: maxSize,
	}
}

// Name 返回通知器名称
func (n *LogNotifier) Name() string {
	return n.name
}

// Notify 发送通知
func (n *LogNotifier) Notify(alert *model.Alert) error {
	n.mu.Lock()
	defer n.mu.Unlock()

	// 记录到日志
	fmt.Printf("[ALERT] %s: %s (value=%.2f, threshold=%.2f)\n",
		alert.Severity, alert.RuleName, alert.Value, alert.Threshold)

	// 保存到历史
	n.alerts = append(n.alerts, alert)
	if len(n.alerts) > n.maxSize {
		n.alerts = n.alerts[len(n.alerts)-n.maxSize:]
	}

	return nil
}

// GetAlerts 获取历史告警
func (n *LogNotifier) GetAlerts() []*model.Alert {
	n.mu.RLock()
	defer n.mu.RUnlock()

	result := make([]*model.Alert, len(n.alerts))
	copy(result, n.alerts)
	return result
}

// WebhookNotifier Webhook 通知器
type WebhookNotifier struct {
	mu       sync.RWMutex
	name     string
	url      string
	alerts   []*model.Alert
	maxSize  int
}

// NewWebhookNotifier 创建 Webhook 通知器
func NewWebhookNotifier(url string, maxSize int) *WebhookNotifier {
	return &WebhookNotifier{
		name:    "webhook",
		url:     url,
		alerts:  make([]*model.Alert, 0),
		maxSize: maxSize,
	}
}

// Name 返回通知器名称
func (n *WebhookNotifier) Name() string {
	return n.name
}

// Notify 发送通知
func (n *WebhookNotifier) Notify(alert *model.Alert) error {
	n.mu.Lock()
	defer n.mu.Unlock()

	// 模拟发送 webhook
	fmt.Printf("[WEBHOOK] Sending alert to %s: %s\n", n.url, alert.RuleName)

	// 保存到历史
	n.alerts = append(n.alerts, alert)
	if len(n.alerts) > n.maxSize {
		n.alerts = n.alerts[len(n.alerts)-n.maxSize:]
	}

	return nil
}

// GetAlerts 获取历史告警
func (n *WebhookNotifier) GetAlerts() []*model.Alert {
	n.mu.RLock()
	defer n.mu.RUnlock()

	result := make([]*model.Alert, len(n.alerts))
	copy(result, n.alerts)
	return result
}

// EmailNotifier 邮件通知器
type EmailNotifier struct {
	mu       sync.RWMutex
	name     string
	smtpHost string
	smtpPort int
	from     string
	to       []string
	alerts   []*model.Alert
	maxSize  int
}

// NewEmailNotifier 创建邮件通知器
func NewEmailNotifier(smtpHost string, smtpPort int, from string, to []string, maxSize int) *EmailNotifier {
	return &EmailNotifier{
		name:     "email",
		smtpHost: smtpHost,
		smtpPort: smtpPort,
		from:     from,
		to:       to,
		alerts:   make([]*model.Alert, 0),
		maxSize:  maxSize,
	}
}

// Name 返回通知器名称
func (n *EmailNotifier) Name() string {
	return n.name
}

// Notify 发送通知
func (n *EmailNotifier) Notify(alert *model.Alert) error {
	n.mu.Lock()
	defer n.mu.Unlock()

	// 模拟发送邮件
	fmt.Printf("[EMAIL] Sending alert to %v: %s\n", n.to, alert.RuleName)

	// 保存到历史
	n.alerts = append(n.alerts, alert)
	if len(n.alerts) > n.maxSize {
		n.alerts = n.alerts[len(n.alerts)-n.maxSize:]
	}

	return nil
}

// GetAlerts 获取历史告警
func (n *EmailNotifier) GetAlerts() []*model.Alert {
	n.mu.RLock()
	defer n.mu.RUnlock()

	result := make([]*model.Alert, len(n.alerts))
	copy(result, n.alerts)
	return result
}

// SlackNotifier Slack 通知器
type SlackNotifier struct {
	mu       sync.RWMutex
	name     string
	webhook  string
	channel  string
	alerts   []*model.Alert
	maxSize  int
}

// NewSlackNotifier 创建 Slack 通知器
func NewSlackNotifier(webhook, channel string, maxSize int) *SlackNotifier {
	return &SlackNotifier{
		name:    "slack",
		webhook: webhook,
		channel: channel,
		alerts:  make([]*model.Alert, 0),
		maxSize: maxSize,
	}
}

// Name 返回通知器名称
func (n *SlackNotifier) Name() string {
	return n.name
}

// Notify 发送通知
func (n *SlackNotifier) Notify(alert *model.Alert) error {
	n.mu.Lock()
	defer n.mu.Unlock()

	// 模拟发送 Slack 消息
	fmt.Printf("[SLACK] Sending alert to channel %s: %s\n", n.channel, alert.RuleName)

	// 保存到历史
	n.alerts = append(n.alerts, alert)
	if len(n.alerts) > n.maxSize {
		n.alerts = n.alerts[len(n.alerts)-n.maxSize:]
	}

	return nil
}

// GetAlerts 获取历史告警
func (n *SlackNotifier) GetAlerts() []*model.Alert {
	n.mu.RLock()
	defer n.mu.RUnlock()

	result := make([]*model.Alert, len(n.alerts))
	copy(result, n.alerts)
	return result
}

// MultiNotifier 多通道通知器
type MultiNotifier struct {
	mu        sync.RWMutex
	name      string
	notifiers []Notifier
}

// NewMultiNotifier 创建多通道通知器
func NewMultiNotifier(notifiers ...Notifier) *MultiNotifier {
	return &MultiNotifier{
		name:      "multi",
		notifiers: notifiers,
	}
}

// Name 返回通知器名称
func (n *MultiNotifier) Name() string {
	return n.name
}

// Notify 发送通知
func (n *MultiNotifier) Notify(alert *model.Alert) error {
	n.mu.RLock()
	defer n.mu.RUnlock()

	var lastErr error
	for _, notifier := range n.notifiers {
		if err := notifier.Notify(alert); err != nil {
			lastErr = err
		}
	}
	return lastErr
}

// ThrottledNotifier 节流通知器
type ThrottledNotifier struct {
	mu           sync.RWMutex
	name         string
	notifier     Notifier
	interval     time.Duration
	lastNotify   map[string]time.Time
}

// NewThrottledNotifier 创建节流通知器
func NewThrottledNotifier(notifier Notifier, interval time.Duration) *ThrottledNotifier {
	return &ThrottledNotifier{
		name:       "throttled",
		notifier:   notifier,
		interval:   interval,
		lastNotify: make(map[string]time.Time),
	}
}

// Name 返回通知器名称
func (n *ThrottledNotifier) Name() string {
	return n.name
}

// Notify 发送通知
func (n *ThrottledNotifier) Notify(alert *model.Alert) error {
	n.mu.Lock()
	defer n.mu.Unlock()

	// 检查是否可以发送
	key := fmt.Sprintf("%s:%s", alert.RuleID, alert.Severity)
	lastTime, exists := n.lastNotify[key]
	if exists && time.Since(lastTime) < n.interval {
		return nil // 节流
	}

	// 发送通知
	err := n.notifier.Notify(alert)
	if err == nil {
		n.lastNotify[key] = time.Now()
	}
	return err
}
