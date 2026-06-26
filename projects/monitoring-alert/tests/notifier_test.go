package tests_test

import (
	"testing"
	"time"

	"github.com/monitoring-alert/internal/model"
	"github.com/monitoring-alert/src/notifier"
)

// TestLogNotifier 测试控制台通知器
func TestLogNotifier(t *testing.T) {
	n := notifier.NewLogNotifier(0) // 无节流

	alert := &model.Alert{
		ID:       "test-1",
		RuleID:   "cpu_high",
		RuleName: "CPU High",
		Severity: model.SeverityWarning,
		Status:   model.AlertStatusFiring,
		Value:    85.0,
		Threshold: 80.0,
	}

	err := n.Notify(alert)
	if err != nil {
		t.Fatalf("notify error: %v", err)
	}

	if n.Name() != "log" {
		t.Errorf("expected name 'log', got '%s'", n.Name())
	}
}

// TestLogNotifierThrottle 测试节流
func TestLogNotifierThrottle(t *testing.T) {
	n := notifier.NewLogNotifier(1 * time.Second)

	alert := &model.Alert{
		ID:       "test-1",
		RuleID:   "cpu_high",
		RuleName: "CPU High",
		Severity: model.SeverityWarning,
		Status:   model.AlertStatusFiring,
	}

	// 第一次通知应该通过
	err := n.Notify(alert)
	if err != nil {
		t.Fatalf("first notify error: %v", err)
	}

	// 立即第二次通知应该被节流
	err = n.Notify(alert)
	if err != nil {
		t.Fatalf("second notify error: %v", err)
	}

	// 缓冲区应该有 1 条记录
	buffer := n.GetBuffer()
	if len(buffer) != 1 {
		t.Errorf("expected 1 buffered notification, got %d", len(buffer))
	}
}

// TestLogNotifierGetBuffer 测试获取缓冲区
func TestLogNotifierGetBuffer(t *testing.T) {
	n := notifier.NewLogNotifier(0)

	alert := &model.Alert{
		ID:       "test-1",
		RuleID:   "cpu_high",
		RuleName: "CPU High",
		Severity: model.SeverityWarning,
		Status:   model.AlertStatusFiring,
	}

	n.Notify(alert)
	n.Notify(alert)

	buffer := n.GetBuffer()
	if len(buffer) != 2 {
		t.Errorf("expected 2 buffered notifications, got %d", len(buffer))
	}
}

// TestWebhookNotifier 测试 Webhook 通知器
func TestWebhookNotifier(t *testing.T) {
	n := notifier.NewWebhookNotifier("http://localhost:9090/webhook", 0)

	alert := &model.Alert{
		ID:       "test-1",
		RuleID:   "cpu_high",
		RuleName: "CPU High",
		Severity: model.SeverityCritical,
		Status:   model.AlertStatusFiring,
	}

	err := n.Notify(alert)
	if err != nil {
		t.Fatalf("notify error: %v", err)
	}

	if n.Name() != "webhook" {
		t.Errorf("expected name 'webhook', got '%s'", n.Name())
	}
}

// TestWebhookNotifierThrottle 测试 Webhook 节流
func TestWebhookNotifierThrottle(t *testing.T) {
	n := notifier.NewWebhookNotifier("http://localhost:9090/webhook", 1*time.Second)

	alert := &model.Alert{
		ID:       "test-1",
		RuleID:   "cpu_high",
		RuleName: "CPU High",
		Severity: model.SeverityWarning,
		Status:   model.AlertStatusFiring,
	}

	n.Notify(alert)
	n.Notify(alert)

	buffer := n.GetBuffer()
	if len(buffer) != 1 {
		t.Errorf("expected 1 buffered notification (throttled), got %d", len(buffer))
	}
}

// TestMultiNotifier 测试多通道通知器
func TestMultiNotifier(t *testing.T) {
	logN := notifier.NewLogNotifier(0)
	webhookN := notifier.NewWebhookNotifier("http://localhost:9090/webhook", 0)

	multi := notifier.NewMultiNotifier(logN, webhookN)

	alert := &model.Alert{
		ID:       "test-1",
		RuleID:   "cpu_high",
		RuleName: "CPU High",
		Severity: model.SeverityWarning,
		Status:   model.AlertStatusFiring,
	}

	err := multi.Notify(alert)
	if err != nil {
		t.Fatalf("notify error: %v", err)
	}

	if multi.Name() != "multi" {
		t.Errorf("expected name 'multi', got '%s'", multi.Name())
	}
}

// TestThrottledNotifier 测试节流通知器
func TestThrottledNotifier(t *testing.T) {
	logN := notifier.NewLogNotifier(0)
	throttled := notifier.NewThrottledNotifier(logN, 1*time.Second)

	alert := &model.Alert{
		ID:       "test-1",
		RuleID:   "cpu_high",
		RuleName: "CPU High",
		Severity: model.SeverityWarning,
		Status:   model.AlertStatusFiring,
	}

	throttled.Notify(alert)
	throttled.Notify(alert)

	name := throttled.Name()
	if name != "throttled(log)" {
		t.Errorf("expected name 'throttled(log)', got '%s'", name)
	}
}

// TestNotifierEmptyAlert 测试空告警
func TestNotifierEmptyAlert(t *testing.T) {
	n := notifier.NewLogNotifier(0)

	// 空告警也不应该 panic
	err := n.Notify(nil)
	// 可能返回错误，但不应该 panic
	_ = err
}

// TestLogNotifierLargeBuffer 测试大缓冲区
func TestLogNotifierLargeBuffer(t *testing.T) {
	n := notifier.NewLogNotifier(0)

	for i := 0; i < 150; i++ {
		alert := &model.Alert{
			ID:       stringRune('a', 8) + "-" + stringInt64(int64(i)),
			RuleID:   "test",
			RuleName: "Test",
			Severity: model.SeverityWarning,
			Status:   model.AlertStatusFiring,
		}
		n.Notify(alert)
	}

	buffer := n.GetBuffer()
	// 缓冲区应该有最多 100 条
	if len(buffer) > 100 {
		t.Errorf("expected max 100 buffered notifications, got %d", len(buffer))
	}
}

// TestWebhookNotifierLargeBuffer 测试大缓冲区
func TestWebhookNotifierLargeBuffer(t *testing.T) {
	n := notifier.NewWebhookNotifier("http://localhost:9090/webhook", 0)

	for i := 0; i < 150; i++ {
		alert := &model.Alert{
			ID:       "test-" + stringInt64(int64(i)),
			RuleID:   "test",
			RuleName: "Test",
			Severity: model.SeverityWarning,
			Status:   model.AlertStatusFiring,
		}
		n.Notify(alert)
	}

	buffer := n.GetBuffer()
	if len(buffer) > 100 {
		t.Errorf("expected max 100 buffered notifications, got %d", len(buffer))
	}
}

// 辅助函数
func stringRune(r rune, n int) string {
	s := make([]rune, n)
	for i := range s {
		s[i] = r
	}
	return string(s)
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
