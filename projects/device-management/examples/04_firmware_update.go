// Example: Firmware update simulation
// This example demonstrates the firmware update lifecycle for IoT devices:
// 1. Create firmware update operations
// 2. Simulate download and installation progress
// 3. Handle update failures and rollbacks
// 4. Batch update multiple devices
//
// Run with: go run main.go

package main

import (
	"fmt"
	"time"

	"device-management/src"
)

func main() {
	fmt.Println("=== IoT Device Management - Firmware Update Simulation ===\n")

	// Create registry and firmware manager
	registry := device.NewRegistry()
	firmwareManager := device.NewFirmwareManager()

	// Register devices that need firmware updates
	sensor1, _ := registry.RegisterDevice("Temp Sensor A1", "sensor", "Building A/Floor 1")
	sensor2, _ := registry.RegisterDevice("Temp Sensor A2", "sensor", "Building A/Floor 2")
	sensor3, _ := registry.RegisterDevice("Temp Sensor B1", "sensor", "Building B/Floor 1")
	thermostat, _ := registry.RegisterDevice("Smart Thermostat", "actuator", "Building A/Floor 1")

	// Activate all devices
	registry.ActivateDevice(sensor1.ID)
	registry.ActivateDevice(sensor2.ID)
	registry.ActivateDevice(sensor3.ID)
	registry.ActivateDevice(thermostat.ID)

	fmt.Println("--- Registered Devices ---")
	fmt.Printf("  1. %s (current FW: %s)\n", sensor1.Name, sensor1.FirmwareVersion)
	fmt.Printf("  2. %s (current FW: %s)\n", sensor2.Name, sensor2.FirmwareVersion)
	fmt.Printf("  3. %s (current FW: %s)\n", sensor3.Name, sensor3.FirmwareVersion)
	fmt.Printf("  4. %s (current FW: %s)\n", thermostat.Name, thermostat.FirmwareVersion)
	fmt.Println()

	// Example 1: Single device firmware update
	fmt.Println("--- Example 1: Single Device Firmware Update ---")

	update1 := firmwareManager.CreateFirmwareUpdate(
		sensor1.ID,
		"2.1.0",
		"https://fw.example.com/sensor-v2.1.0.bin",
		"sha256:a1b2c3d4e5f6",
		1024*512, // 512KB
	)

	fmt.Printf("Created update: %s\n", update1.ID)
	fmt.Printf("  Device: %s\n", update1.DeviceID)
	fmt.Printf("  Version: %s -> 2.1.0\n", sensor1.FirmwareVersion)
	fmt.Printf("  URL: %s\n", update1.URL)
	fmt.Printf("  Size: %d bytes (%.1f KB)\n", update1.Size, float64(update1.Size)/1024)
	fmt.Printf("  Checksum: %s\n", update1.Checksum)
	fmt.Printf("  Status: %s\n\n", update1.Status)

	// Simulate download progress
	fmt.Println("Simulating download...")
	firmwareManager.StartDownload(update1.ID)
	fmt.Printf("  Status: downloading, Progress: %.0f%%\n", update1.Progress)

	for progress := 25.0; progress <= 100.0; progress += 25.0 {
		firmwareManager.UpdateProgress(update1.ID, progress)
		fmt.Printf("  Progress: %.0f%%\n", progress)
		time.Sleep(50 * time.Millisecond)
	}

	// Simulate installation
	fmt.Println("Starting installation...")
	firmwareManager.UpdateProgress(update1.ID, 100.0)
	fmt.Printf("  Download complete, starting installation...\n")

	// Simulate installation progress
	for progress := 25.0; progress <= 100.0; progress += 50.0 {
		firmwareManager.UpdateProgress(update1.ID, progress)
		fmt.Printf("  Install progress: %.0f%%\n", progress)
		time.Sleep(50 * time.Millisecond)
	}

	firmwareManager.CompleteUpdate(update1.ID)
	fmt.Printf("  Update %s completed!\n", update1.ID)
	fmt.Println()

	// Example 2: Firmware update with failure
	fmt.Println("--- Example 2: Failed Firmware Update ---")

	update2 := firmwareManager.CreateFirmwareUpdate(
		sensor2.ID,
		"2.1.0",
		"https://fw.example.com/sensor-v2.1.0.bin",
		"sha256:a1b2c3d4e5f6",
		1024*512,
	)

	fmt.Printf("Created update: %s for %s\n", update2.ID, sensor2.Name)

	firmwareManager.StartDownload(update2.ID)
	fmt.Printf("  Status: downloading\n")

	// Simulate download failure
	firmwareManager.FailUpdate(update2.ID, "checksum verification failed")
	fmt.Printf("  Status: failed - checksum verification failed\n")
	fmt.Println()

	// Example 3: Batch firmware update (staged rollout)
	fmt.Println("--- Example 3: Batch Firmware Update (Staged Rollout) ---")

	// First, update a small subset of devices (canary deployment)
	fmt.Println("Stage 1: Canary deployment (1 device)")
	canaryResults := firmwareManager.BatchUpdate(
		map[string]string{
			sensor3.ID: "2.1.0",
		},
		"https://fw.example.com/sensor-v2.1.0.bin",
		"sha256:a1b2c3d4e5f6",
		1024*512,
	)

	for deviceID, result := range canaryResults {
		fmt.Printf("  %s: %s\n", deviceID, result)
	}
	fmt.Println()

	// Simulate canary verification
	fmt.Println("Verifying canary device...")
	time.Sleep(100 * time.Millisecond)
	fmt.Println("  Canary device OK - proceeding with full rollout")
	fmt.Println()

	// Full rollout to remaining devices
	fmt.Println("Stage 2: Full rollout")
	fullResults := firmwareManager.BatchUpdate(
		map[string]string{
			sensor1.ID:     "2.1.0",
			sensor2.ID:     "2.1.0",
			thermostat.ID:  "1.5.0",
		},
		"https://fw.example.com/release-v2.1.0.bin",
		"sha256:a1b2c3d4e5f6",
		1024*512,
	)

	for deviceID, result := range fullResults {
		fmt.Printf("  %s: %s\n", deviceID, result)
	}
	fmt.Println()

	// Example 4: Check update status
	fmt.Println("--- Example 4: Update Status Check ---")

	updates := firmwareManager.GetDeviceUpdates(sensor1.ID)
	fmt.Printf("Firmware updates for %s: %d\n", sensor1.ID, len(updates))
	for _, update := range updates {
		fmt.Printf("  - %s: version %s, status %s, progress %.0f%%\n",
			update.ID, update.Version, update.Status, update.Progress)
		if update.CompletedAt != nil {
			fmt.Printf("    Completed at: %s\n", update.CompletedAt.Format(time.RFC3339))
		}
	}
	fmt.Println()

	// Check all pending updates
	pendingUpdates := firmwareManager.GetPendingUpdates()
	fmt.Printf("Pending updates: %d\n", len(pendingUpdates))
	for _, update := range pendingUpdates {
		fmt.Printf("  - Device %s: version %s\n", update.DeviceID, update.Version)
	}
	fmt.Println()

	// Example 5: Firmware version tracking
	fmt.Println("--- Example 5: Firmware Version Tracking ---")

	fmt.Println("Current firmware versions:")
	allDevices := registry.GetAllDevices()
	for _, dev := range allDevices {
		fmt.Printf("  - %s: %s\n", dev.Name, dev.FirmwareVersion)
	}
	fmt.Println()

	fmt.Println("=== Example Complete ===")
}
