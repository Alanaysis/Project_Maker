package test

import (
	"testing"

	"github.com/monitoring-alert/internal/model"
	"github.com/monitoring-alert/internal/notifier"
	"github.com/stretchr/testify/assert"
)

func TestLogNotifierCreation(t *testing.T) {
	n := notifier.NewLogNotifier(100)
	assert.NotNil(t, n)
	assert.Equal(t, "log", n.Name())
}

func TestLogNotifierNotify(t *testing.T) {
	n := notifier.NewLogNotifier(100)

	alert := model.NewAlert("rule1", "CPU High", model.SeverityWarning, nil)
	alert.SetValue(85.5, 80.0)
	alert.SetStatus(model.AlertStatusFiring)

	err := n.Notify(alert)
	assert.NoError(t, err)

	alerts := n.GetAlerts()
	assert.Equal(t, 1, len(alerts))
	assert.Equal(t, "rule1", alerts[0].RuleID)
}

func TestLogNotifierMaxSize(t *testing.T) {
	n := notifier.NewLogNotifier(3)

	for i := 0; i < 5; i++ {
		alert := model.NewAlert("rule1", "CPU High", model.SeverityWarning, nil)
		alert.SetValue(float64(i), 80.0)
		alert.SetStatus(model.AlertStatusFiring)

		err := n.Notify(alert)
		assert.NoError(t, err)
	}

	alerts := n.GetAlerts()
	assert.Equal(t, 3, len(alerts))
}

func TestWebhookNotifierCreation(t *testing.T) {
	n := notifier.NewWebhookNotifier("http://localhost:8080/webhook", 100)
	assert.NotNil(t, n)
	assert.Equal(t, "webhook", n.Name())
}

func TestWebhookNotifierNotify(t *testing.T) {
	n := notifier.NewWebhookNotifier("http://localhost:8080/webhook", 100)

	alert := model.NewAlert("rule1", "CPU High", model.SeverityWarning, nil)
	alert.SetValue(85.5, 80.0)
	alert.SetStatus(model.AlertStatusFiring)

	err := n.Notify(alert)
	assert.NoError(t, err)

	alerts := n.GetAlerts()
	assert.Equal(t, 1, len(alerts))
}

func TestEmailNotifierCreation(t *testing.T) {
	n := notifier.NewEmailNotifier("smtp.example.com", 587, "alert@example.com", []string{"user@example.com"}, 100)
	assert.NotNil(t, n)
	assert.Equal(t, "email", n.Name())
}

func TestEmailNotifierNotify(t *testing.T) {
	n := notifier.NewEmailNotifier("smtp.example.com", 587, "alert@example.com", []string{"user@example.com"}, 100)

	alert := model.NewAlert("rule1", "CPU High", model.SeverityWarning, nil)
	alert.SetValue(85.5, 80.0)
	alert.SetStatus(model.AlertStatusFiring)

	err := n.Notify(alert)
	assert.NoError(t, err)

	alerts := n.GetAlerts()
	assert.Equal(t, 1, len(alerts))
}

func TestSlackNotifierCreation(t *testing.T) {
	n := notifier.NewSlackNotifier("https://hooks.slack.com/xxx", "#alerts", 100)
	assert.NotNil(t, n)
	assert.Equal(t, "slack", n.Name())
}

func TestSlackNotifierNotify(t *testing.T) {
	n := notifier.NewSlackNotifier("https://hooks.slack.com/xxx", "#alerts", 100)

	alert := model.NewAlert("rule1", "CPU High", model.SeverityWarning, nil)
	alert.SetValue(85.5, 80.0)
	alert.SetStatus(model.AlertStatusFiring)

	err := n.Notify(alert)
	assert.NoError(t, err)

	alerts := n.GetAlerts()
	assert.Equal(t, 1, len(alerts))
}

func TestMultiNotifierCreation(t *testing.T) {
	logNotifier := notifier.NewLogNotifier(100)
	webhookNotifier := notifier.NewWebhookNotifier("http://localhost:8080/webhook", 100)

	n := notifier.NewMultiNotifier(logNotifier, webhookNotifier)
	assert.NotNil(t, n)
	assert.Equal(t, "multi", n.Name())
}

func TestMultiNotifierNotify(t *testing.T) {
	logNotifier := notifier.NewLogNotifier(100)
	webhookNotifier := notifier.NewWebhookNotifier("http://localhost:8080/webhook", 100)

	n := notifier.NewMultiNotifier(logNotifier, webhookNotifier)

	alert := model.NewAlert("rule1", "CPU High", model.SeverityWarning, nil)
	alert.SetValue(85.5, 80.0)
	alert.SetStatus(model.AlertStatusFiring)

	err := n.Notify(alert)
	assert.NoError(t, err)

	// 验证两个通知器都收到了通知
	logAlerts := logNotifier.GetAlerts()
	webhookAlerts := webhookNotifier.GetAlerts()
	assert.Equal(t, 1, len(logAlerts))
	assert.Equal(t, 1, len(webhookAlerts))
}

func TestThrottledNotifierCreation(t *testing.T) {
	logNotifier := notifier.NewLogNotifier(100)
	n := notifier.NewThrottledNotifier(logNotifier, 5)
	assert.NotNil(t, n)
	assert.Equal(t, "throttled", n.Name())
}

func TestThrottledNotifierNotify(t *testing.T) {
	logNotifier := notifier.NewLogNotifier(100)
	n := notifier.NewThrottledNotifier(logNotifier, 1<<30) // 非常大的间隔，模拟节流

	alert := model.NewAlert("rule1", "CPU High", model.SeverityWarning, nil)
	alert.SetValue(85.5, 80.0)
	alert.SetStatus(model.AlertStatusFiring)

	// 第一次通知应该成功
	err := n.Notify(alert)
	assert.NoError(t, err)

	// 第二次通知应该被节流
	err = n.Notify(alert)
	assert.NoError(t, err)

	// 验证只有一次通知被发送
	logAlerts := logNotifier.GetAlerts()
	assert.Equal(t, 1, len(logAlerts))
}
