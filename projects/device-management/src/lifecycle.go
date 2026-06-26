package device

import (
	"fmt"
	"sync"
	"time"
)

// LifecycleManager manages the full lifecycle of IoT devices.
//
// IoT Device Lifecycle:
// Every IoT device goes through distinct lifecycle stages:
//
//   registered    - Device identity created, credentials generated
//       |
//       v
//   activated     - Device connected to network, authenticated
//       |
//       v
//   running       - Device actively reporting metrics and receiving commands
//       |
//       v
//   disabled      - Device temporarily disabled (maintenance, troubleshooting)
//       |
//       v
//   retired       - Device permanently removed from the system
//
// Understanding and managing this lifecycle is crucial for:
// - Device provisioning at scale
// - Maintenance window management
// - Secure device decommissioning
// - Audit and compliance tracking
type LifecycleManager struct {
	mu           sync.RWMutex
	lifecycles   map[string]*DeviceLifecycle  // Device ID -> Lifecycle
}

// NewLifecycleManager creates a new lifecycle manager.
func NewLifecycleManager() *LifecycleManager {
	return &LifecycleManager{
		lifecycles: make(map[string]*DeviceLifecycle),
	}
}

// Register registers a new device in the lifecycle system.
func (lm *LifecycleManager) Register(deviceID string) {
	lm.mu.Lock()
	defer lm.mu.Unlock()

	lm.lifecycles[deviceID] = &DeviceLifecycle{
		DeviceID:     deviceID,
		CurrentState: LifecycleRegistered,
		Transitions: []StateTransition{
			{
				From:      "",
				To:        LifecycleRegistered,
				Timestamp: time.Now(),
				Reason:    "device registration",
			},
		},
	}
}

// Transition transitions a device to a new lifecycle state.
func (lm *LifecycleManager) Transition(deviceID string, toState LifecycleState, reason string) error {
	lm.mu.Lock()
	defer lm.mu.Unlock()

	lifecycle, exists := lm.lifecycles[deviceID]
	if !exists {
		return fmt.Errorf("device %s not in lifecycle system", deviceID)
	}

	currentState := lifecycle.CurrentState
	if err := lifecycle.ValidateTransition(currentState, toState); err != nil {
		return err
	}

	lifecycle.RecordTransition(currentState, toState, reason)
	lifecycle.CurrentState = toState
	return nil
}

// GetCurrentState returns the current lifecycle state of a device.
func (lm *LifecycleManager) GetCurrentState(deviceID string) (LifecycleState, error) {
	lm.mu.RLock()
	defer lm.mu.RUnlock()

	lifecycle, exists := lm.lifecycles[deviceID]
	if !exists {
		return "", fmt.Errorf("device %s not in lifecycle system", deviceID)
	}

	return lifecycle.CurrentState, nil
}

// GetHistory returns the full transition history for a device.
func (lm *LifecycleManager) GetHistory(deviceID string) ([]StateTransition, error) {
	lm.mu.RLock()
	defer lm.mu.RUnlock()

	lifecycle, exists := lm.lifecycles[deviceID]
	if !exists {
		return nil, fmt.Errorf("device %s not in lifecycle system", deviceID)
	}

	history := make([]StateTransition, len(lifecycle.Transitions))
	copy(history, lifecycle.Transitions)
	return history, nil
}

// CanTransition checks if a transition is valid without performing it.
func (lm *LifecycleManager) CanTransition(deviceID string, toState LifecycleState) (bool, error) {
	lm.mu.RLock()
	defer lm.mu.RUnlock()

	lifecycle, exists := lm.lifecycles[deviceID]
	if !exists {
		return false, fmt.Errorf("device %s not in lifecycle system", deviceID)
	}

	return lifecycle.ValidateTransition(lifecycle.CurrentState, toState) == nil, nil
}

// GetAllStates returns the current state of all managed devices.
func (lm *LifecycleManager) GetAllStates() map[string]LifecycleState {
	lm.mu.RLock()
	defer lm.mu.RUnlock()

	states := make(map[string]LifecycleState)
	for deviceID, lifecycle := range lm.lifecycles {
		states[deviceID] = lifecycle.CurrentState
	}
	return states
}

// IsTerminalState checks if a lifecycle state is terminal (no further transitions allowed).
func IsTerminalState(state LifecycleState) bool {
	return state == LifecycleRetired
}
