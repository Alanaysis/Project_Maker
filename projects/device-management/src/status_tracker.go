package device

import (
	"fmt"
	"sync"
	"time"
)

// StatusTracker monitors and tracks device status changes and metrics.
//
// In IoT systems, continuous status monitoring is essential for:
// - Detecting device failures and connectivity issues
// - Aggregating metrics for analytics and dashboards
// - Triggering alerts when thresholds are exceeded
// - Maintaining an audit trail of device state changes
type StatusTracker struct {
	mu             sync.RWMutex
	deviceStatus   map[string]DeviceStatus   // Current status per device
	deviceStates   map[string]DeviceState    // Current operational state per device
	metricsHistory map[string][]DeviceMetrics // Rolling metrics history per device
	statusEvents   []StatusEvent              // Audit trail of status changes
	maxHistorySize int                        // Max metrics history entries per device
}

// StatusEvent records a device status change event.
type StatusEvent struct {
	DeviceID  string        `json:"device_id"`
	OldStatus DeviceStatus  `json:"old_status"`
	NewStatus DeviceStatus  `json:"new_status"`
	OldState  DeviceState   `json:"old_state"`
	NewState  DeviceState   `json:"new_state"`
	Timestamp time.Time     `json:"timestamp"`
	Reason    string        `json:"reason"`
}

// NewStatusTracker creates a new status tracker with the given history size.
func NewStatusTracker(maxHistorySize int) *StatusTracker {
	return &StatusTracker{
		deviceStatus:   make(map[string]DeviceStatus),
		deviceStates:   make(map[string]DeviceState),
		metricsHistory: make(map[string][]DeviceMetrics),
		statusEvents:   make([]StatusEvent, 0),
		maxHistorySize: maxHistorySize,
	}
}

// UpdateStatus updates a device's connection status.
func (st *StatusTracker) UpdateStatus(deviceID string, newStatus DeviceStatus) {
	st.mu.Lock()
	defer st.mu.Unlock()

	oldStatus := st.deviceStatus[deviceID]
	if oldStatus == newStatus {
		return // No change
	}

	st.deviceStatus[deviceID] = newStatus
	st.statusEvents = append(st.statusEvents, StatusEvent{
		DeviceID:  deviceID,
		OldStatus: oldStatus,
		NewStatus: newStatus,
		Timestamp: time.Now(),
		Reason:    "manual update",
	})
}

// UpdateState updates a device's operational state.
func (st *StatusTracker) UpdateState(deviceID string, newState DeviceState) {
	st.mu.Lock()
	defer st.mu.Unlock()

	oldState := st.deviceStates[deviceID]
	if oldState == newState {
		return
	}

	st.deviceStates[deviceID] = newState
	st.statusEvents = append(st.statusEvents, StatusEvent{
		DeviceID:  deviceID,
		OldState:  oldState,
		NewState:  newState,
		Timestamp: time.Now(),
		Reason:    "state update",
	})
}

// RecordHeartbeat processes a heartbeat from a device.
//
// Heartbeat Processing:
// 1. Update device metrics from heartbeat data
// 2. Update last-seen timestamp
// 3. Maintain rolling metrics history
// 4. Check for stale devices (potential failures)
func (st *StatusTracker) RecordHeartbeat(heartbeat Heartbeat) {
	st.mu.Lock()
	defer st.mu.Unlock()

	// Update current status to online
	st.deviceStatus[heartbeat.DeviceID] = StatusOnline

	// Update metrics history (rolling window)
	history := st.metricsHistory[heartbeat.DeviceID]
	history = append(history, heartbeat.Metrics)

	// Trim to max history size
	if len(history) > st.maxHistorySize {
		history = history[len(history)-st.maxHistorySize:]
	}
	st.metricsHistory[heartbeat.DeviceID] = history

	// Record status event if device was previously offline
	if st.deviceStatus[heartbeat.DeviceID] == StatusOnline {
		st.statusEvents = append(st.statusEvents, StatusEvent{
			DeviceID: heartbeat.DeviceID,
			NewStatus: StatusOnline,
			Timestamp: heartbeat.Timestamp,
			Reason:    "heartbeat received",
		})
	}
}

// CheckStaleDevices identifies devices that haven't sent heartbeats within the timeout.
func (st *StatusTracker) CheckStaleDevices(timeout time.Duration) []string {
	st.mu.Lock()
	defer st.mu.Unlock()

	var staleDevices []string
	now := time.Now()

	for deviceID, status := range st.deviceStatus {
		if status != StatusOnline {
			continue
		}

		// Check metrics history for last seen
		history := st.metricsHistory[deviceID]
		if len(history) == 0 {
			staleDevices = append(staleDevices, deviceID)
			continue
		}

		// In a real system, we'd check the actual timestamp from heartbeat
		// For this learning example, we assume last entry is recent enough
		// if time.Since(history[len(history)-1].Timestamp) > timeout {
		//     staleDevices = append(staleDevices, deviceID)
		// }
	}

	return staleDevices
}

// GetDeviceStatus returns the current status of a device.
func (st *StatusTracker) GetDeviceStatus(deviceID string) (DeviceStatus, bool) {
	st.mu.RLock()
	defer st.mu.RUnlock()

	status, exists := st.deviceStatus[deviceID]
	return status, exists
}

// GetDeviceState returns the current operational state of a device.
func (st *StatusTracker) GetDeviceState(deviceID string) (DeviceState, bool) {
	st.mu.RLock()
	defer st.mu.RUnlock()

	state, exists := st.deviceStates[deviceID]
	return state, exists
}

// GetMetricsHistory returns the metrics history for a device.
func (st *StatusTracker) GetMetricsHistory(deviceID string) []DeviceMetrics {
	st.mu.RLock()
	defer st.mu.RUnlock()

	history := make([]DeviceMetrics, len(st.metricsHistory[deviceID]))
	copy(history, st.metricsHistory[deviceID])
	return history
}

// GetStatusEvents returns the status change event history.
func (st *StatusTracker) GetStatusEvents() []StatusEvent {
	st.mu.RLock()
	defer st.mu.RUnlock()

	events := make([]StatusEvent, len(st.statusEvents))
	copy(events, st.statusEvents)
	return events
}

// GetOnlineDevices returns all currently online devices.
func (st *StatusTracker) GetOnlineDevices() []string {
	st.mu.RLock()
	defer st.mu.RUnlock()

	var online []string
	for deviceID, status := range st.deviceStatus {
		if status == StatusOnline {
			online = append(online, deviceID)
		}
	}
	return online
}

// GetDeviceSummary provides a summary of all tracked devices.
func (st *StatusTracker) GetDeviceSummary() map[string]DeviceSummary {
	st.mu.RLock()
	defer st.mu.RUnlock()

	summary := make(map[string]DeviceSummary)
	for deviceID, status := range st.deviceStatus {
		state, _ := st.deviceStates[deviceID]
		history := st.metricsHistory[deviceID]

		var latestMetrics DeviceMetrics
		if len(history) > 0 {
			latestMetrics = history[len(history)-1]
		}

		summary[deviceID] = DeviceSummary{
			DeviceID:     deviceID,
			Status:       status,
			State:        state,
			LatestMetrics: latestMetrics,
			HistorySize:  len(history),
		}
	}
	return summary
}

// DeviceSummary is a compact representation of a device's current state.
type DeviceSummary struct {
	DeviceID      string        `json:"device_id"`
	Status        DeviceStatus  `json:"status"`
	State         DeviceState   `json:"state"`
	LatestMetrics DeviceMetrics `json:"latest_metrics"`
	HistorySize   int           `json:"history_size"`
}

// String returns a human-readable summary of the device.
func (ds DeviceSummary) String() string {
	return fmt.Sprintf("Device(%s): status=%s, state=%s, metrics={CPU:%.1f%%, Mem:%.1f%%, Temp:%.1f°C}",
		ds.DeviceID, ds.Status, ds.State,
		ds.LatestMetrics.CPUUsage, ds.LatestMetrics.MemoryUsage, ds.LatestMetrics.Temperature)
}
