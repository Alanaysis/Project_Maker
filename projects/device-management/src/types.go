// Package device provides core types for IoT device management.
//
// In IoT systems, devices are the fundamental entities that:
// 1. Register with a central management system
// 2. Report their status (online/offline, metrics)
// 3. Receive remote commands
// 4. Accept firmware updates
//
// This package defines the core data structures used across the system.
package device

import (
	"fmt"
	"time"
)

// DeviceStatus represents the connection status of an IoT device.
// In IoT architecture, devices can be ONLINE (connected), OFFLINE (disconnected),
// or PENDING (registration in progress).
type DeviceStatus string

const (
	StatusOnline   DeviceStatus = "online"
	StatusOffline  DeviceStatus = "offline"
	StatusPending  DeviceStatus = "pending"
	StatusDisabled DeviceStatus = "disabled"
)

// DeviceState represents the operational state of a device.
// This is distinct from connection status - a device can be online but in error state.
type DeviceState string

const (
	StateIdle        DeviceState = "idle"
	StateRunning     DeviceState = "running"
	StateError       DeviceState = "error"
	StateUpdating    DeviceState = "updating"
	StateMaintenance DeviceState = "maintenance"
)

// Device represents an IoT device in the management system.
//
// IoT Device Architecture:
// Each device has a unique identity (ID), authentication credentials (Secret),
// and metadata (name, type, location, tags). The device tracks its own state
// and reports it to the management system.
type Device struct {
	ID            string        `json:"id"`             // Unique device identifier
	Secret        string        `json:"secret"`         // Authentication secret/token
	Name          string        `json:"name"`           // Human-readable device name
	Type          string        `json:"type"`           // Device type (sensor, actuator, gateway, etc.)
	Location      string        `json:"location"`       // Physical location of the device
	Tags          map[string]string `json:"tags"`       // Key-value tags for grouping and filtering
	Status        DeviceStatus  `json:"status"`         // Current connection status
	State         DeviceState   `json:"state"`          // Current operational state
	FirmwareVersion string      `json:"firmware_version"` // Current firmware version
	CreatedAt     time.Time     `json:"created_at"`     // Registration timestamp
	UpdatedAt     time.Time     `json:"updated_at"`     // Last update timestamp
	LastSeenAt    time.Time     `json:"last_seen_at"`   // Last heartbeat timestamp
	Metrics       DeviceMetrics `json:"metrics"`        // Current device metrics
}

// DeviceMetrics represents real-time metrics reported by a device.
// Metrics are crucial for monitoring device health and performance.
type DeviceMetrics struct {
	CPUUsage    float64 `json:"cpu_usage"`     // CPU usage percentage (0-100)
	MemoryUsage float64 `json:"memory_usage"`  // Memory usage percentage (0-100)
	DiskUsage   float64 `json:"disk_usage"`    // Disk usage percentage (0-100)
	Temperature float64 `json:"temperature"`   // Device temperature in Celsius
	BatteryLevel float64 `json:"battery_level"` // Battery level percentage (0-100)
	Uptime      int64   `json:"uptime"`        // Device uptime in seconds
}

// DeviceShadow represents the desired state of a device.
//
// Device Shadow (Digital Twin) Concept:
// A device shadow is a persistent JSON document that stores the desired state
// of a device. It allows applications to interact with the device even when
// it's offline. The shadow contains:
// - desired: What the application wants the device to be
// - reported: What the device actually reports
// - delta: The difference between desired and reported (what needs to change)
type DeviceShadow struct {
	DeviceID string           `json:"device_id"` // Associated device ID
	Desired  map[string]any   `json:"desired"`   // Desired state (set by applications)
	Reported map[string]any   `json:"reported"`  // Reported state (set by device)
	Updated  time.Time        `json:"updated"`   // Last shadow update timestamp
}

// RemoteCommand represents a command sent from the management system to a device.
// Commands are the primary way to control IoT devices remotely.
type RemoteCommand struct {
	ID        string    `json:"id"`         // Unique command ID
	DeviceID  string    `json:"device_id"`  // Target device ID
	Command   string    `json:"command"`    // Command type (restart, config, update, etc.)
	Payload   map[string]any `json:"payload"` // Command parameters
	Status    string    `json:"status"`     // pending, executed, failed, cancelled
	CreatedAt time.Time `json:"created_at"` // Command creation time
	ExecutedAt *time.Time `json:"executed_at"` // When command was executed (nil if pending)
}

// FirmwareUpdate represents a firmware update operation.
// Firmware updates are critical for IoT device lifecycle management.
type FirmwareUpdate struct {
	ID            string    `json:"id"`            // Update operation ID
	DeviceID      string    `json:"device_id"`     // Target device ID
	Version       string    `json:"version"`       // New firmware version
	URL           string    `json:"url"`           // Firmware download URL
	Size          int64     `json:"size"`          // Firmware size in bytes
	Checksum      string    `json:"checksum"`      // SHA256 checksum for integrity verification
	Status        string    `json:"status"`        // pending, downloading, installing, completed, failed
	Progress      float64   `json:"progress"`      // Update progress (0-100)
	CreatedAt     time.Time `json:"created_at"`    // Update creation time
	CompletedAt   *time.Time `json:"completed_at"` // Update completion time
}

// Heartbeat represents a device heartbeat message.
// Heartbeats are used to determine device online status and detect failures.
type Heartbeat struct {
	DeviceID  string             `json:"device_id"`  // Device that sent the heartbeat
	Timestamp time.Time          `json:"timestamp"`  // Heartbeat timestamp
	Metrics   DeviceMetrics      `json:"metrics"`    // Current metrics
	Extra     map[string]any     `json:"extra"`      // Additional data
}

// Group represents a logical grouping of devices.
// Groups enable batch operations and hierarchical organization.
type Group struct {
	ID        string            `json:"id"`         // Group ID
	Name      string            `json:"name"`       // Group name
	ParentID  string            `json:"parent_id"`  // Parent group ID (for hierarchy)
	Devices   []string          `json:"devices"`    // Device IDs in this group
	Tags      map[string]string `json:"tags"`       // Group tags
	CreatedAt time.Time         `json:"created_at"` // Creation time
}

// LifecycleState represents the lifecycle stage of a device.
// Understanding device lifecycle is key to IoT system design.
type LifecycleState string

const (
	LifecycleRegistered  LifecycleState = "registered"  // Device registered but not activated
	LifecycleActivated   LifecycleState = "activated"   // Device activated and ready
	LifecycleRunning     LifecycleState = "running"     // Device actively reporting
	LifecycleDisabled    LifecycleState = "disabled"    // Device temporarily disabled
	LifecycleRetired     LifecycleState = "retired"     // Device permanently removed
)

// DeviceLifecycle manages the lifecycle transitions of a device.
//
// Lifecycle States:
// registered -> activated -> running -> disabled -> retired
//                    |-> (running) <-|
//
// State transitions must follow allowed paths to prevent invalid states.
type DeviceLifecycle struct {
	DeviceID     string         `json:"device_id"`
	CurrentState LifecycleState `json:"current_state"`
	Transitions  []StateTransition `json:"transitions"`
}

// StateTransition records a single state change.
type StateTransition struct {
	From      LifecycleState `json:"from"`
	To        LifecycleState `json:"to"`
	Timestamp time.Time      `json:"timestamp"`
	Reason    string         `json:"reason"`
}

// Validate checks if a lifecycle transition is allowed.
// Valid transitions:
// - registered -> activated
// - activated -> running
// - running -> disabled
// - disabled -> activated (re-activation)
// - running -> retired
// - disabled -> retired
func (dl *DeviceLifecycle) ValidateTransition(from, to LifecycleState) error {
	validTransitions := map[LifecycleState][]LifecycleState{
		LifecycleRegistered: {LifecycleActivated},
		LifecycleActivated:  {LifecycleRunning},
		LifecycleRunning:    {LifecycleDisabled, LifecycleRetired},
		LifecycleDisabled:   {LifecycleActivated, LifecycleRetired},
		LifecycleRetired:    {}, // Terminal state
	}

	allowed := validTransitions[from]
	for _, a := range allowed {
		if a == to {
			return nil
		}
	}
	return fmt.Errorf("invalid lifecycle transition: %s -> %s", from, to)
}

// RecordTransition records a state transition in the lifecycle history.
func (dl *DeviceLifecycle) RecordTransition(from, to LifecycleState, reason string) {
	dl.Transitions = append(dl.Transitions, StateTransition{
		From:      from,
		To:        to,
		Timestamp: time.Now(),
		Reason:    reason,
	})
}
