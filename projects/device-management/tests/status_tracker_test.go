package device

import (
	"testing"
	"time"
)

func TestStatusTracker_UpdateStatus(t *testing.T) {
	tracker := NewStatusTracker(100)

	// Update status
	tracker.UpdateStatus("device-1", StatusOnline)

	status, exists := tracker.GetDeviceStatus("device-1")
	if !exists {
		t.Error("Device status should exist after update")
	}

	if status != StatusOnline {
		t.Errorf("Expected status 'online', got '%s'", status)
	}
}

func TestStatusTracker_UpdateState(t *testing.T) {
	tracker := NewStatusTracker(100)

	tracker.UpdateState("device-1", StateRunning)

	state, exists := tracker.GetDeviceState("device-1")
	if !exists {
		t.Error("Device state should exist after update")
	}

	if state != StateRunning {
		t.Errorf("Expected state 'running', got '%s'", state)
	}
}

func TestStatusTracker_RecordHeartbeat(t *testing.T) {
	tracker := NewStatusTracker(100)

	heartbeat := Heartbeat{
		DeviceID:  "device-1",
		Timestamp: time.Now(),
		Metrics: DeviceMetrics{
			CPUUsage:    25.0,
			MemoryUsage: 50.0,
			Temperature: 30.0,
		},
	}

	tracker.RecordHeartbeat(heartbeat)

	status, exists := tracker.GetDeviceStatus("device-1")
	if !exists || status != StatusOnline {
		t.Error("Device should be online after heartbeat")
	}

	history := tracker.GetMetricsHistory("device-1")
	if len(history) != 1 {
		t.Errorf("Expected 1 history entry, got %d", len(history))
	}

	if history[0].CPUUsage != 25.0 {
		t.Errorf("Expected CPU usage 25.0, got %f", history[0].CPUUsage)
	}
}

func TestStatusTracker_GetOnlineDevices(t *testing.T) {
	tracker := NewStatusTracker(100)

	tracker.UpdateStatus("device-1", StatusOnline)
	tracker.UpdateStatus("device-2", StatusOnline)
	tracker.UpdateStatus("device-3", StatusOffline)

	online := tracker.GetOnlineDevices()

	if len(online) != 2 {
		t.Errorf("Expected 2 online devices, got %d", len(online))
	}
}

func TestStatusTracker_GetDeviceSummary(t *testing.T) {
	tracker := NewStatusTracker(100)

	tracker.UpdateStatus("device-1", StatusOnline)
	tracker.UpdateState("device-1", StateRunning)

	tracker.RecordHeartbeat(Heartbeat{
		DeviceID:  "device-1",
		Timestamp: time.Now(),
		Metrics: DeviceMetrics{
			CPUUsage:    30.0,
			MemoryUsage: 40.0,
			Temperature: 25.0,
		},
	})

	summary := tracker.GetDeviceSummary()

	s, exists := summary["device-1"]
	if !exists {
		t.Fatal("Device summary should exist")
	}

	if s.Status != StatusOnline {
		t.Errorf("Expected status 'online', got '%s'", s.Status)
	}

	if s.State != StateRunning {
		t.Errorf("Expected state 'running', got '%s'", s.State)
	}
}

func TestStatusTracker_StatusEvents(t *testing.T) {
	tracker := NewStatusTracker(100)

	tracker.UpdateStatus("device-1", StatusOnline)
	tracker.UpdateStatus("device-1", StatusOffline)

	events := tracker.GetStatusEvents()

	if len(events) != 2 {
		t.Errorf("Expected 2 events, got %d", len(events))
	}
}
