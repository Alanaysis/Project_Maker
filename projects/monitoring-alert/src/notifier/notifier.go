package notifier

import (
	"fmt"
	"sync"
	"time"
)

// Notifier 通知器接口
type Notifier interface {
	// Notify 发送通知
	Notify(alert interface{}) error
	// Name 返回通知器名称
	Name() string
}

// LogNotifier 控制台通知器
type LogNotifier struct {
	mu         sync.Mutex
	throttle   time.Duration
	lastNotify map[string]time.Time
	bufferSize int
	buffer     []string
}

// NewLogNotifier 创建控制台通知器
func NewLogNotifier(throttle time.Duration) *LogNotifier {
	return &LogNotifier{
		throttle:   throttle,
		lastNotify: make(map[string]time.Time),
		bufferSize: 100,
		buffer:     make([]string, 0),
	}
}

// Notify 发送控制台通知
func (n *LogNotifier) Notify(alert interface{}) error {
	n.mu.Lock()
	defer n.mu.Unlock()

	key := fmt.Sprintf("%T-%p", alert, alert)
	now := time.Now()

	// 节流检查
	if lastTime, ok := n.lastNotify[key]; ok {
		if now.Sub(lastTime) < n.throttle {
			return nil
		}
	}

	n.lastNotify[key] = now

	// 格式化告警信息
	var msg string
	switch a := alert.(type) {
	case interface{ String() string }:
		msg = a.String()
	case *AlertAlert:
		msg = fmt.Sprintf("[ALERT] %s: %s (value=%.2f, threshold=%.2f)",
			a.RuleName, a.Status, a.Value, a.Threshold)
	default:
		msg = fmt.Sprintf("[ALERT] %+v", alert)
	}

	// 添加到缓冲区
	n.buffer = append(n.buffer, fmt.Sprintf("[%s] %s", now.Format("15:04:05"), msg))
	if len(n.buffer) > n.bufferSize {
		n.buffer = n.buffer[len(n.buffer)-n.bufferSize:]
	}

	fmt.Println(msg)
	return nil
}

// Name 返回名称
func (n *LogNotifier) Name() string {
	return "log"
}

// GetBuffer 获取通知缓冲区
func (n *LogNotifier) GetBuffer() []string {
	n.mu.Lock()
	defer n.mu.Unlock()
	result := make([]string, len(n.buffer))
	copy(result, n.buffer)
	return result
}

// AlertAlert 用于类型断言的告警结构
type AlertAlert struct {
	RuleName string
	Status   string
	Value    float64
	Threshold float64
}

// WebhookNotifier Webhook 通知器
type WebhookNotifier struct {
	url        string
	throttle   time.Duration
	lastNotify map[string]time.Time
	mu         sync.Mutex
	bufferSize int
	buffer     []string
}

// NewWebhookNotifier 创建 Webhook 通知器
func NewWebhookNotifier(url string, throttle time.Duration) *WebhookNotifier {
	return &WebhookNotifier{
		url:        url,
		throttle:   throttle,
		lastNotify: make(map[string]time.Time),
		bufferSize: 100,
		buffer:     make([]string, 0),
	}
}

// Notify 发送 Webhook 通知
func (n *WebhookNotifier) Notify(alert interface{}) error {
	n.mu.Lock()
	defer n.mu.Unlock()

	key := fmt.Sprintf("%T-%p", alert, alert)
	now := time.Now()

	if lastTime, ok := n.lastNotify[key]; ok {
		if now.Sub(lastTime) < n.throttle {
			return nil
		}
	}

	n.lastNotify[key] = now

	var msg string
	switch a := alert.(type) {
	case interface{ String() string }:
		msg = a.String()
	default:
		msg = fmt.Sprintf("%+v", alert)
	}

	n.buffer = append(n.buffer, fmt.Sprintf("[%s] Webhook -> %s: %s",
		now.Format("15:04:05"), n.url, msg))
	if len(n.buffer) > n.bufferSize {
		n.buffer = n.buffer[len(n.buffer)-n.bufferSize:]
	}

	// 在实际实现中，这里会发送 HTTP 请求
	// http.Post(n.url, "application/json", body)
	return nil
}

// Name 返回名称
func (n *WebhookNotifier) Name() string {
	return "webhook"
}

// GetBuffer 获取通知缓冲区
func (n *WebhookNotifier) GetBuffer() []string {
	n.mu.Lock()
	defer n.mu.Unlock()
	result := make([]string, len(n.buffer))
	copy(result, n.buffer)
	return result
}

// MultiNotifier 多通道通知器
type MultiNotifier struct {
	notifiers []Notifier
}

// NewMultiNotifier 创建多通道通知器
func NewMultiNotifier(notifiers ...Notifier) *MultiNotifier {
	return &MultiNotifier{
		notifiers: notifiers,
	}
}

// Notify 发送到所有通道
func (n *MultiNotifier) Notify(alert interface{}) error {
	var lastErr error
	for _, notifier := range n.notifiers {
		if err := notifier.Notify(alert); err != nil {
			lastErr = err
		}
	}
	return lastErr
}

// Name 返回名称
func (n *MultiNotifier) Name() string {
	return "multi"
}

// ThrottledNotifier 节流通知器包装器
type ThrottledNotifier struct {
	delegate   Notifier
	throttle   time.Duration
	lastNotify map[string]time.Time
	mu         sync.Mutex
}

// NewThrottledNotifier 创建节流通知器
func NewThrottledNotifier(delegate Notifier, throttle time.Duration) *ThrottledNotifier {
	return &ThrottledNotifier{
		delegate:   delegate,
		throttle:   throttle,
		lastNotify: make(map[string]time.Time),
	}
}

// Notify 节流发送通知
func (n *ThrottledNotifier) Notify(alert interface{}) error {
	n.mu.Lock()
	defer n.mu.Unlock()

	key := fmt.Sprintf("%T-%p", alert, alert)
	now := time.Now()

	if lastTime, ok := n.lastNotify[key]; ok {
		if now.Sub(lastTime) < n.throttle {
			return nil
		}
	}

	n.lastNotify[key] = now
	return n.delegate.Notify(alert)
}

// Name 返回名称
func (n *ThrottledNotifier) Name() string {
	return "throttled(" + n.delegate.Name() + ")"
}
