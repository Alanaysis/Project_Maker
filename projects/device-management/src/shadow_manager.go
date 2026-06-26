package device

import (
	"fmt"
	"sync"
	"time"
)

// ShadowManager manages device shadows (digital twins).
//
// Device Shadow Concept:
// A device shadow is a persistent JSON document that represents the desired state
// of a device. It enables:
//
// 1. Decoupled communication: Applications can set desired state even when device is offline
// 2. State reconciliation: System tracks difference between desired and reported state
// 3. Command queuing: Commands are stored in shadow until device reconnects
//
// Shadow Structure:
// {
//   "state": {
//     "desired": { ... },    // What the application wants
//     "reported": { ... },   // What the device reports
//     "delta": { ... }       // Difference (desired - reported)
//   }
// }
type ShadowManager struct {
	mu         sync.RWMutex
	shadows    map[string]*DeviceShadow  // Device ID -> Shadow
}

// NewShadowManager creates a new shadow manager.
func NewShadowManager() *ShadowManager {
	return &ShadowManager{
		shadows: make(map[string]*DeviceShadow),
	}
}

// GetOrCreateShadow returns the shadow for a device, creating one if it doesn't exist.
func (sm *ShadowManager) GetOrCreateShadow(deviceID string) *DeviceShadow {
	sm.mu.Lock()
	defer sm.mu.Unlock()

	shadow, exists := sm.shadows[deviceID]
	if !exists {
		shadow = &DeviceShadow{
			DeviceID: deviceID,
			Desired:  make(map[string]any),
			Reported: make(map[string]any),
			Updated:  time.Now(),
		}
		sm.shadows[deviceID] = shadow
	}

	// Return a copy to prevent concurrent modification
	shadowCopy := *shadow
	shadowCopy.Desired = make(map[string]any)
	for k, v := range sm.shadows[deviceID].Desired {
		shadowCopy.Desired[k] = v
	}
	shadowCopy.Reported = make(map[string]any)
	for k, v := range sm.shadows[deviceID].Reported {
		shadowCopy.Reported[k] = v
	}

	return &shadowCopy
}

// SetDesiredState sets the desired state for a device's shadow.
// This represents what the application wants the device to be.
func (sm *ShadowManager) SetDesiredState(deviceID string, state map[string]any) error {
	sm.mu.Lock()
	defer sm.mu.Unlock()

	shadow, exists := sm.shadows[deviceID]
	if !exists {
		return fmt.Errorf("shadow not found for device: %s", deviceID)
	}

	shadow.Desired = state
	shadow.Updated = time.Now()

	return nil
}

// UpdateReportedState updates the reported state from a device.
// This represents what the device actually reports.
func (sm *ShadowManager) UpdateReportedState(deviceID string, state map[string]any) error {
	sm.mu.Lock()
	defer sm.mu.Unlock()

	shadow, exists := sm.shadows[deviceID]
	if !exists {
		return fmt.Errorf("shadow not found for device: %s", deviceID)
	}

	shadow.Reported = state
	shadow.Updated = time.Now()

	return nil
}

// GetDelta returns the difference between desired and reported state.
// The delta represents what changes need to be made to the device.
func (sm *ShadowManager) GetDelta(deviceID string) (map[string]any, error) {
	sm.mu.RLock()
	defer sm.mu.RUnlock()

	shadow, exists := sm.shadows[deviceID]
	if !exists {
		return nil, fmt.Errorf("shadow not found for device: %s", deviceID)
	}

	delta := make(map[string]any)
	for key, desiredVal := range shadow.Desired {
		reportedVal, hasReported := shadow.Reported[key]
		if !hasReported || desiredVal != reportedVal {
			delta[key] = desiredVal
		}
	}

	return delta, nil
}

// GetShadow returns the full shadow for a device.
func (sm *ShadowManager) GetShadow(deviceID string) (*DeviceShadow, error) {
	sm.mu.RLock()
	defer sm.mu.RUnlock()

	shadow, exists := sm.shadows[deviceID]
	if !exists {
		return nil, fmt.Errorf("shadow not found for device: %s", deviceID)
	}

	shadowCopy := *shadow
	shadowCopy.Desired = make(map[string]any)
	for k, v := range shadow.Desired {
		shadowCopy.Desired[k] = v
	}
	shadowCopy.Reported = make(map[string]any)
	for k, v := range shadow.Reported {
		shadowCopy.Reported[k] = v
	}

	return &shadowCopy, nil
}

// GetAllShadows returns all device shadows.
func (sm *ShadowManager) GetAllShadows() map[string]*DeviceShadow {
	sm.mu.RLock()
	defer sm.mu.RUnlock()

	shadows := make(map[string]*DeviceShadow)
	for deviceID, shadow := range sm.shadows {
		shadowCopy := *shadow
		shadowCopy.Desired = make(map[string]any)
		for k, v := range shadow.Desired {
			shadowCopy.Desired[k] = v
		}
		shadowCopy.Reported = make(map[string]any)
		for k, v := range shadow.Reported {
			shadowCopy.Reported[k] = v
		}
		shadows[deviceID] = &shadowCopy
	}
	return shadows
}

// ClearShadow removes the shadow for a device.
func (sm *ShadowManager) ClearShadow(deviceID string) error {
	sm.mu.Lock()
	defer sm.mu.Unlock()

	if _, exists := sm.shadows[deviceID]; !exists {
		return fmt.Errorf("shadow not found for device: %s", deviceID)
	}

	delete(sm.shadows, deviceID)
	return nil
}
