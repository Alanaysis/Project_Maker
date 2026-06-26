package device

import (
	"crypto/rand"
	"crypto/sha256"
	"encoding/hex"
	"fmt"
	"sync"
	"time"
)

// Registry manages device registration and authentication.
//
// Device Registration Process:
// 1. Device sends registration request with unique identity
// 2. Registry validates and creates device record
// 3. Registry generates authentication credentials (secret/token)
// 4. Device stores credentials for future authentication
//
// This is the first step in the IoT device management core loop:
// Device Registration -> Status Reporting -> Remote Control -> Firmware Update
type Registry struct {
	mu       sync.RWMutex
	devices  map[string]*Device  // deviceID -> Device
	bySecret map[string]string   // secret -> deviceID (for auth lookup)
}

// NewRegistry creates a new device registry.
func NewRegistry() *Registry {
	return &Registry{
		devices:  make(map[string]*Device),
		bySecret: make(map[string]string),
	}
}

// RegisterDevice registers a new device in the system.
//
// Registration generates:
// - A unique device ID (if not provided)
// - An authentication secret (randomly generated)
// - Initial device record with pending status
func (r *Registry) RegisterDevice(name, devType, location string) (*Device, error) {
	r.mu.Lock()
	defer r.mu.Unlock()

	// Generate unique device ID
	deviceID := generateDeviceID(devType)

	// Generate authentication secret (256-bit random token)
	secret := generateSecret()

	// Create the device record
	device := &Device{
		ID:            deviceID,
		Secret:        secret,
		Name:          name,
		Type:          devType,
		Location:      location,
		Tags:          make(map[string]string),
		Status:        StatusPending,
		State:         StateIdle,
		FirmwareVersion: "0.0.1",
		CreatedAt:     time.Now(),
		UpdatedAt:     time.Now(),
		LastSeenAt:    time.Time{},
		Metrics:       DeviceMetrics{},
	}

	// Store device and create auth index
	r.devices[deviceID] = device
	r.bySecret[secret] = deviceID

	return device, nil
}

// Authenticate verifies a device's credentials.
//
// Authentication Process:
// 1. Device presents its ID and secret
// 2. Registry looks up the secret and verifies it matches
// 3. If valid, returns the device record; otherwise returns error
//
// In production systems, this would use TLS certificates or JWT tokens.
func (r *Registry) Authenticate(deviceID, secret string) (*Device, error) {
	r.mu.RLock()
	defer r.mu.RUnlock()

	// Check if device exists
	device, exists := r.devices[deviceID]
	if !exists {
		return nil, fmt.Errorf("device not found: %s", deviceID)
	}

	// Verify secret matches
	if device.Secret != secret {
		return nil, fmt.Errorf("authentication failed for device: %s", deviceID)
	}

	// Check if device is disabled
	if device.Status == StatusDisabled {
		return nil, fmt.Errorf("device %s is disabled", deviceID)
	}

	// Return a copy to prevent concurrent modification
	devCopy := *device
	return &devCopy, nil
}

// ActivateDevice activates a pending device, changing its status to online.
func (r *Registry) ActivateDevice(deviceID string) error {
	r.mu.Lock()
	defer r.mu.Unlock()

	device, exists := r.devices[deviceID]
	if !exists {
		return fmt.Errorf("device not found: %s", deviceID)
	}

	if device.Status != StatusPending {
		return fmt.Errorf("device %s is not in pending state", deviceID)
	}

	device.Status = StatusOnline
	device.UpdatedAt = time.Now()
	return nil
}

// DeactivateDevice deactivates a device, changing its status to offline.
func (r *Registry) DeactivateDevice(deviceID string) error {
	r.mu.Lock()
	defer r.mu.Unlock()

	device, exists := r.devices[deviceID]
	if !exists {
		return fmt.Errorf("device not found: %s", deviceID)
	}

	device.Status = StatusOffline
	device.UpdatedAt = time.Now()
	return nil
}

// UnregisterDevice removes a device from the registry.
func (r *Registry) UnregisterDevice(deviceID string) error {
	r.mu.Lock()
	defer r.mu.Unlock()

	device, exists := r.devices[deviceID]
	if !exists {
		return fmt.Errorf("device not found: %s", deviceID)
	}

	// Remove from auth index
	delete(r.bySecret, device.Secret)
	// Remove device
	delete(r.devices, deviceID)
	return nil
}

// GetDevice retrieves a device by its ID.
func (r *Registry) GetDevice(deviceID string) (*Device, error) {
	r.mu.RLock()
	defer r.mu.RUnlock()

	device, exists := r.devices[deviceID]
	if !exists {
		return nil, fmt.Errorf("device not found: %s", deviceID)
	}

	devCopy := *device
	return &devCopy, nil
}

// GetAllDevices returns all registered devices.
func (r *Registry) GetAllDevices() []*Device {
	r.mu.RLock()
	defer r.mu.RUnlock()

	devices := make([]*Device, 0, len(r.devices))
	for _, device := range r.devices {
		devCopy := *device
		devices = append(devices, &devCopy)
	}
	return devices
}

// UpdateDeviceMetrics updates the metrics for a device after receiving a heartbeat.
func (r *Registry) UpdateDeviceMetrics(deviceID string, metrics DeviceMetrics) error {
	r.mu.Lock()
	defer r.mu.Unlock()

	device, exists := r.devices[deviceID]
	if !exists {
		return fmt.Errorf("device not found: %s", deviceID)
	}

	device.Metrics = metrics
	device.LastSeenAt = time.Now()
	device.UpdatedAt = time.Now()

	// If device was offline and now reports metrics, mark as online
	if device.Status == StatusOffline {
		device.Status = StatusOnline
	}

	return nil
}

// IsDeviceOnline checks if a device has sent a heartbeat within the timeout period.
func (r *Registry) IsDeviceOnline(deviceID string, timeout time.Duration) bool {
	r.mu.RLock()
	defer r.mu.RUnlock()

	device, exists := r.devices[deviceID]
	if !exists {
		return false
	}

	// Device must be marked online
	if device.Status != StatusOnline {
		return false
	}

	// Check if heartbeat is within timeout
	if device.LastSeenAt.IsZero() {
		return false
	}

	return time.Since(device.LastSeenAt) <= timeout
}

// generateDeviceID creates a unique device ID based on type prefix.
func generateDeviceID(devType string) string {
	// Generate 16 random bytes for uniqueness
	bytes := make([]byte, 16)
	rand.Read(bytes)
	hash := sha256.Sum256(bytes)
	shortID := hex.EncodeToString(hash[:8])

	// Format: type-xxxxxx (e.g., sensor-a1b2c3)
	return fmt.Sprintf("%s-%s", devType, shortID)
}

// generateSecret creates a 32-byte random authentication secret.
func generateSecret() string {
	bytes := make([]byte, 32)
	rand.Read(bytes)
	return hex.EncodeToString(bytes)
}
