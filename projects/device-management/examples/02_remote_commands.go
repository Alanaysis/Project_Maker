// Example: Remote command execution
// This example demonstrates how to send and execute remote commands on IoT devices:
// 1. Create commands for devices
// 2. Execute commands (simulating device response)
// 3. Handle command failures
// 4. Batch execute commands across multiple devices
//
// Run with: go run main.go

package main

import (
	"fmt"
	"time"

	"device-management/src"
)

func main() {
	fmt.Println("=== IoT Device Management - Remote Command Execution ===\n")

	// Create registry and register devices
	registry := device.NewRegistry()
	commandExecutor := device.NewCommandExecutor()

	// Register devices
	sensor1, _ := registry.RegisterDevice("Temperature Sensor 1", "sensor", "Building A/Floor 1")
	sensor2, _ := registry.RegisterDevice("Temperature Sensor 2", "sensor", "Building A/Floor 2")
	actuator1, _ := registry.RegisterDevice("HVAC Controller", "actuator", "Building A/Basement")

	// Activate all devices
	registry.ActivateDevice(sensor1.ID)
	registry.ActivateDevice(sensor2.ID)
	registry.ActivateDevice(actuator1.ID)

	fmt.Println("--- Registered Devices ---")
	fmt.Printf("  1. %s (%s)\n", sensor1.Name, sensor1.ID)
	fmt.Printf("  2. %s (%s)\n", sensor2.Name, sensor2.ID)
	fmt.Printf("  3. %s (%s)\n", actuator1.Name, actuator1.ID)
	fmt.Println()

	// Example 1: Configuration update command
	fmt.Println("--- Example 1: Configuration Update ---")

	configCmd := commandExecutor.CreateCommand(sensor1.ID, "config_update", map[string]any{
		"sampling_rate": 5,        // Sample every 5 seconds
		"threshold_min": 10.0,      // Min temperature threshold
		"threshold_max": 35.0,      // Max temperature threshold
		"report_interval": 60,       // Report every 60 seconds
	})

	fmt.Printf("Created command: %s for device %s\n", configCmd.ID, configCmd.DeviceID)
	fmt.Printf("Command type: %s\n", configCmd.Command)
	fmt.Printf("Payload: %+v\n", configCmd.Payload)
	fmt.Printf("Status: %s\n\n", configCmd.Status)

	// Execute the command
	err := commandExecutor.ExecuteCommand(configCmd.ID)
	if err != nil {
		fmt.Printf("Error executing command: %v\n", err)
	} else {
		cmd, _ := commandExecutor.GetCommand(configCmd.ID)
		fmt.Printf("Command %s executed at %s\n", cmd.ID, cmd.ExecutedAt.Format(time.RFC3339))
	}
	fmt.Println()

	// Example 2: Device restart command
	fmt.Println("--- Example 2: Device Restart ---")

	restartCmd := commandExecutor.CreateCommand(actuator1.ID, "restart", map[string]any{
		"delay": 5,         // Wait 5 seconds before restarting
		"save_state": true,  // Save current state before restart
	})

	fmt.Printf("Created restart command: %s\n", restartCmd.ID)

	// Simulate command failure
	err = commandExecutor.FailCommand(restartCmd.ID, "device not responding")
	if err != nil {
		fmt.Printf("Error failing command: %v\n", err)
	} else {
		cmd, _ := commandExecutor.GetCommand(restartCmd.ID)
		fmt.Printf("Command %s failed: %v\n", cmd.ID, cmd.Payload["error"])
	}
	fmt.Println()

	// Example 3: Firmware update command
	fmt.Println("--- Example 3: Firmware Update Command ---")

	fwCmd := commandExecutor.CreateCommand(sensor2.ID, "firmware_update", map[string]any{
		"url":      "https://fw.example.com/sensor-v2.1.0.bin",
		"checksum": "sha256:abc123def456",
		"version":  "2.1.0",
	})

	fmt.Printf("Created firmware update command: %s\n", fwCmd.ID)
	fmt.Printf("Firmware URL: %v\n", fwCmd.Payload["url"])
	fmt.Printf("Checksum: %v\n", fwCmd.Payload["checksum"])

	// Execute firmware update
	err = commandExecutor.ExecuteCommand(fwCmd.ID)
	if err != nil {
		fmt.Printf("Error: %v\n", err)
	} else {
		cmd, _ := commandExecutor.GetCommand(fwCmd.ID)
		fmt.Printf("Firmware update command %s executed\n", cmd.ID)
	}
	fmt.Println()

	// Example 4: Batch command execution
	fmt.Println("--- Example 4: Batch Command Execution ---")

	// Get pending commands for reference
	pendingCmds := commandExecutor.GetPendingCommands()
	fmt.Printf("Pending commands before batch: %d\n", len(pendingCmds))

	// Create batch commands for maintenance window
	// All sensors get a configuration update simultaneously
	sensorConfigCmd := commandExecutor.CreateCommand(sensor1.ID, "config_update", map[string]any{
		"power_mode": "low",
	})
	sensor2ConfigCmd := commandExecutor.CreateCommand(sensor2.ID, "config_update", map[string]any{
		"power_mode": "low",
	})

	// Batch execute across devices
	batchResults := commandExecutor.ExecuteBatchCommands(map[string][]string{
		sensor1.ID: {sensorConfigCmd.ID},
		sensor2.ID: {sensor2ConfigCmd.ID},
	})

	fmt.Println("Batch execution results:")
	for deviceID, result := range batchResults {
		fmt.Printf("  Device %s: %s\n", deviceID, result)
	}
	fmt.Println()

	// Example 5: Command history for a device
	fmt.Println("--- Example 5: Command History ---")

	sensor1Cmds := commandExecutor.GetDeviceCommands(sensor1.ID)
	fmt.Printf("Commands for %s: %d total\n", sensor1.ID, len(sensor1Cmds))
	for _, cmd := range sensor1Cmds {
		fmt.Printf("  - %s: %s (%s)\n", cmd.ID, cmd.Command, cmd.Status)
		if cmd.ExecutedAt != nil {
			fmt.Printf("    Executed at: %s\n", cmd.ExecutedAt.Format(time.RFC3339))
		}
	}
	fmt.Println()

	// Example 6: Command cancellation
	fmt.Println("--- Example 6: Command Cancellation ---")

	cancelCmd := commandExecutor.CreateCommand(sensor2.ID, "reboot", map[string]any{
		"immediate": false,
	})
	fmt.Printf("Created command: %s\n", cancelCmd.ID)

	// Cancel the command before execution
	err = commandExecutor.CancelCommand(cancelCmd.ID)
	if err != nil {
		fmt.Printf("Error cancelling command: %v\n", err)
	} else {
		cmd, _ := commandExecutor.GetCommand(cancelCmd.ID)
		fmt.Printf("Command %s cancelled\n", cmd.ID)
	}
	fmt.Println()

	fmt.Println("=== Example Complete ===")
}
