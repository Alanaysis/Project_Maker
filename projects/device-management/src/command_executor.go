package device

import (
	"fmt"
	"sync"
	"time"
)

// CommandExecutor manages remote command execution for devices.
//
// Remote Command Architecture:
// Commands flow from the management system to devices through:
// 1. Command creation (with payload/parameters)
// 2. Command queueing and dispatch
// 3. Device execution
// 4. Result reporting back
//
// Commands are critical for IoT device lifecycle management:
// - Configuration updates (change device settings)
// - Software/firmware updates
// - Device restart/reboot
// - Diagnostics and debugging
type CommandExecutor struct {
	mu          sync.RWMutex
	commands    map[string]*RemoteCommand  // Command ID -> Command
	byDevice    map[string][]string        // Device ID -> Command IDs
	commandSeq  int                        // Sequence counter for unique IDs
}

// NewCommandExecutor creates a new command executor.
func NewCommandExecutor() *CommandExecutor {
	return &CommandExecutor{
		commands: make(map[string]*RemoteCommand),
		byDevice: make(map[string][]string),
	}
}

// CreateCommand creates a new remote command for a device.
func (ce *CommandExecutor) CreateCommand(deviceID, commandType string, payload map[string]any) *RemoteCommand {
	ce.mu.Lock()
	defer ce.mu.Unlock()

	ce.commandSeq++
	cmd := &RemoteCommand{
		ID:        fmt.Sprintf("cmd-%d", ce.commandSeq),
		DeviceID:  deviceID,
		Command:   commandType,
		Payload:   payload,
		Status:    "pending",
		CreatedAt: time.Now(),
	}

	ce.commands[cmd.ID] = cmd
	ce.byDevice[deviceID] = append(ce.byDevice[deviceID], cmd.ID)

	return cmd
}

// ExecuteCommand simulates device execution of a command.
// In a real system, this would send the command over MQTT/HTTP to the device.
func (ce *CommandExecutor) ExecuteCommand(commandID string) error {
	ce.mu.Lock()
	defer ce.mu.Unlock()

	cmd, exists := ce.commands[commandID]
	if !exists {
		return fmt.Errorf("command not found: %s", commandID)
	}

	if cmd.Status != "pending" {
		return fmt.Errorf("command %s is already %s", commandID, cmd.Status)
	}

	// Simulate command execution
	cmd.Status = "executed"
	now := time.Now()
	cmd.ExecutedAt = &now

	return nil
}

// FailCommand marks a command as failed.
func (ce *CommandExecutor) FailCommand(commandID, reason string) error {
	ce.mu.Lock()
	defer ce.mu.Unlock()

	cmd, exists := ce.commands[commandID]
	if !exists {
		return fmt.Errorf("command not found: %s", commandID)
	}

	cmd.Status = "failed"
	cmd.Payload["error"] = reason

	return nil
}

// CancelCommand cancels a pending command.
func (ce *CommandExecutor) CancelCommand(commandID string) error {
	ce.mu.Lock()
	defer ce.mu.Unlock()

	cmd, exists := ce.commands[commandID]
	if !exists {
		return fmt.Errorf("command not found: %s", commandID)
	}

	if cmd.Status != "pending" {
		return fmt.Errorf("cannot cancel command %s with status %s", commandID, cmd.Status)
	}

	cmd.Status = "cancelled"
	return nil
}

// GetCommand retrieves a command by ID.
func (ce *CommandExecutor) GetCommand(commandID string) (*RemoteCommand, error) {
	ce.mu.RLock()
	defer ce.mu.RUnlock()

	cmd, exists := ce.commands[commandID]
	if !exists {
		return nil, fmt.Errorf("command not found: %s", commandID)
	}

	cmdCopy := *cmd
	return &cmdCopy, nil
}

// GetDeviceCommands returns all commands for a device.
func (ce *CommandExecutor) GetDeviceCommands(deviceID string) []*RemoteCommand {
	ce.mu.RLock()
	defer ce.mu.RUnlock()

	commandIDs, exists := ce.byDevice[deviceID]
	if !exists {
		return nil
	}

	commands := make([]*RemoteCommand, 0, len(commandIDs))
	for _, id := range commandIDs {
		if cmd, ok := ce.commands[id]; ok {
			cmdCopy := *cmd
			commands = append(commands, &cmdCopy)
		}
	}
	return commands
}

// GetPendingCommands returns all pending commands across all devices.
func (ce *CommandExecutor) GetPendingCommands() []*RemoteCommand {
	ce.mu.RLock()
	defer ce.mu.RUnlock()

	var pending []*RemoteCommand
	for _, cmd := range ce.commands {
		if cmd.Status == "pending" {
			cmdCopy := *cmd
			pending = append(pending, &cmdCopy)
		}
	}
	return pending
}

// ExecuteBatchCommands executes commands for multiple devices.
// This is useful for maintenance windows where many devices need updates.
func (ce *CommandExecutor) ExecuteBatchCommands(deviceCommands map[string][]string) map[string]string {
	ce.mu.Lock()
	defer ce.mu.Unlock()

	results := make(map[string]string)

	for deviceID, commandIDs := range deviceCommands {
		executed := 0
		for _, cmdID := range commandIDs {
			cmd, exists := ce.commands[cmdID]
			if !exists {
				results[cmdID] = fmt.Sprintf("device %s: command not found", deviceID)
				continue
			}
			if cmd.Status != "pending" {
				results[cmdID] = fmt.Sprintf("device %s: command already %s", deviceID, cmd.Status)
				continue
			}

			cmd.Status = "executed"
			now := time.Now()
			cmd.ExecutedAt = &now
			executed++
		}
		results[deviceID] = fmt.Sprintf("executed %d/%d commands", executed, len(commandIDs))
	}

	return results
}
