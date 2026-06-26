package device

import (
	"testing"
)

func TestShadowManager_GetOrCreateShadow(t *testing.T) {
	sm := NewShadowManager()

	shadow := sm.GetOrCreateShadow("device-1")

	if shadow.DeviceID != "device-1" {
		t.Errorf("Expected device ID 'device-1', got '%s'", shadow.DeviceID)
	}

	if shadow.Desired == nil {
		t.Error("Desired state should be initialized")
	}

	if shadow.Reported == nil {
		t.Error("Reported state should be initialized")
	}
}

func TestShadowManager_SetDesiredState(t *testing.T) {
	sm := NewShadowManager()

	sm.GetOrCreateShadow("device-1")

	err := sm.SetDesiredState("device-1", map[string]any{
		"power": "on",
		"brightness": 80,
	})
	if err != nil {
		t.Fatalf("Failed to set desired state: %v", err)
	}

	shadow, _ := sm.GetShadow("device-1")

	if shadow.Desired["power"] != "on" {
		t.Error("Desired power should be 'on'")
	}

	if shadow.Desired["brightness"].(int) != 80 {
		t.Errorf("Desired brightness should be 80, got %v", shadow.Desired["brightness"])
	}
}

func TestShadowManager_UpdateReportedState(t *testing.T) {
	sm := NewShadowManager()

	sm.GetOrCreateShadow("device-1")

	err := sm.UpdateReportedState("device-1", map[string]any{
		"power": "on",
		"brightness": 100,
	})
	if err != nil {
		t.Fatalf("Failed to update reported state: %v", err)
	}

	shadow, _ := sm.GetShadow("device-1")

	if shadow.Reported["power"] != "on" {
		t.Error("Reported power should be 'on'")
	}

	if shadow.Reported["brightness"].(int) != 100 {
		t.Errorf("Reported brightness should be 100, got %v", shadow.Reported["brightness"])
	}
}

func TestShadowManager_GetDelta(t *testing.T) {
	sm := NewShadowManager()

	sm.GetOrCreateShadow("device-1")

	sm.SetDesiredState("device-1", map[string]any{
		"power": "on",
		"brightness": 80,
	})

	sm.UpdateReportedState("device-1", map[string]any{
		"power": "on",
		"brightness": 100,
	})

	delta, err := sm.GetDelta("device-1")
	if err != nil {
		t.Fatalf("Failed to get delta: %v", err)
	}

	// power should not be in delta (desired == reported)
	if _, exists := delta["power"]; exists {
		t.Error("Power should not be in delta (values match)")
	}

	// brightness should be in delta (desired != reported)
	if _, exists := delta["brightness"]; !exists {
		t.Error("Brightness should be in delta (values differ)")
	}
}

func TestShadowManager_ClearShadow(t *testing.T) {
	sm := NewShadowManager()

	sm.GetOrCreateShadow("device-1")

	err := sm.ClearShadow("device-1")
	if err != nil {
		t.Fatalf("Failed to clear shadow: %v", err)
	}

	_, err = sm.GetShadow("device-1")
	if err == nil {
		t.Error("Shadow should not exist after clearing")
	}
}

func TestShadowManager_GetAllShadows(t *testing.T) {
	sm := NewShadowManager()

	sm.GetOrCreateShadow("device-1")
	sm.GetOrCreateShadow("device-2")

	shadows := sm.GetAllShadows()

	if len(shadows) != 2 {
		t.Errorf("Expected 2 shadows, got %d", len(shadows))
	}
}
