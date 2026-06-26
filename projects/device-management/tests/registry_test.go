package device

import (
	"testing"
	"time"
)

func TestRegisterDevice(t *testing.T) {
	registry := NewRegistry()

	// Test basic registration
	device, err := registry.RegisterDevice("Test Sensor", "sensor", "Test Location")
	if err != nil {
		t.Fatalf("Failed to register device: %v", err)
	}

	if device.ID == "" {
		t.Error("Device ID should not be empty")
	}

	if device.Secret == "" {
		t.Error("Device secret should not be empty")
	}

	if device.Name != "Test Sensor" {
		t.Errorf("Device name should be 'Test Sensor', got '%s'", device.Name)
	}

	if device.Type != "sensor" {
		t.Errorf("Device type should be 'sensor', got '%s'", device.Type)
	}

	if device.Status != StatusPending {
		t.Errorf("Device status should be 'pending', got '%s'", device.Status)
	}

	if device.Tags == nil {
		t.Error("Device tags should be initialized")
	}
}

func TestRegisterDeviceUniqueness(t *testing.T) {
	registry := NewRegistry()

	device1, _ := registry.RegisterDevice("Sensor 1", "sensor", "Location 1")
	device2, _ := registry.RegisterDevice("Sensor 2", "sensor", "Location 2")

	if device1.ID == device2.ID {
		t.Error("Registered devices should have unique IDs")
	}
}

func TestAuthenticate(t *testing.T) {
	registry := NewRegistry()

	device, _ := registry.RegisterDevice("Test Sensor", "sensor", "Location")

	// Valid authentication
	authenticated, err := registry.Authenticate(device.ID, device.Secret)
	if err != nil {
		t.Fatalf("Valid authentication failed: %v", err)
	}

	if authenticated.ID != device.ID {
		t.Error("Authenticated device ID should match")
	}

	// Wrong secret
	_, err = registry.Authenticate(device.ID, "wrong-secret")
	if err == nil {
		t.Error("Authentication with wrong secret should fail")
	}

	// Non-existent device
	_, err = registry.Authenticate("non-existent", "any-secret")
	if err == nil {
		t.Error("Authentication of non-existent device should fail")
	}
}

func TestActivateAndDeactivate(t *testing.T) {
	registry := NewRegistry()

	device, _ := registry.RegisterDevice("Test Sensor", "sensor", "Location")

	// Activate
	err := registry.ActivateDevice(device.ID)
	if err != nil {
		t.Fatalf("Failed to activate device: %v", err)
	}

	status, _ := registry.GetDeviceStatus(device.ID)
	if status != StatusOnline {
		t.Errorf("Device should be online after activation, got %s", status)
	}

	// Deactivate
	err = registry.DeactivateDevice(device.ID)
	if err != nil {
		t.Fatalf("Failed to deactivate device: %v", err)
	}

	status, _ = registry.GetDeviceStatus(device.ID)
	if status != StatusOffline {
		t.Errorf("Device should be offline after deactivation, got %s", status)
	}

	// Deactivate again should fail
	err = registry.DeactivateDevice(device.ID)
	if err == nil {
		t.Error("Deactivating already offline device should not error")
	}
}

func TestUnregister(t *testing.T) {
	registry := NewRegistry()

	device, _ := registry.RegisterDevice("Test Sensor", "sensor", "Location")

	err := registry.UnregisterDevice(device.ID)
	if err != nil {
		t.Fatalf("Failed to unregister device: %v", err)
	}

	_, err = registry.GetDevice(device.ID)
	if err == nil {
		t.Error("Unregistered device should not be found")
	}
}

func TestUpdateDeviceMetrics(t *testing.T) {
	registry := NewRegistry()

	device, _ := registry.RegisterDevice("Test Sensor", "sensor", "Location")
	registry.ActivateDevice(device.ID)

	metrics := DeviceMetrics{
		CPUUsage:    45.5,
		MemoryUsage: 60.0,
		Temperature: 32.5,
	}

	err := registry.UpdateDeviceMetrics(device.ID, metrics)
	if err != nil {
		t.Fatalf("Failed to update metrics: %v", err)
	}

	// Verify device is online after metrics update
	if registry.IsDeviceOnline(device.ID, 5*time.Minute) {
		// Good - device is online
	} else {
		t.Error("Device should be online after metrics update")
	}
}

func TestGetAllDevices(t *testing.T) {
	registry := NewRegistry()

	registry.RegisterDevice("Sensor 1", "sensor", "Location 1")
	registry.RegisterDevice("Sensor 2", "sensor", "Location 2")
	registry.RegisterDevice("Actuator 1", "actuator", "Location 3")

	devices := registry.GetAllDevices()

	if len(devices) != 3 {
		t.Errorf("Expected 3 devices, got %d", len(devices))
	}
}
