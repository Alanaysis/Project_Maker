// Example: Device registration and monitoring
// This example demonstrates the core IoT device management workflow:
// 1. Register devices in the system
// 2. Simulate device heartbeats and status updates
// 3. Monitor device health and metrics
//
// Run with: go run main.go

package main

import (
	"fmt"
	"time"

	"device-management/src"
)

func main() {
	fmt.Println("=== IoT Device Management - Registration & Monitoring ===\n")

	// Step 1: Create the device registry
	// The registry is the central authority for device identity and authentication
	registry := device.NewRegistry()

	// Step 2: Register multiple devices
	// In a real IoT system, devices would register themselves via MQTT/HTTP
	fmt.Println("--- Step 1: Registering Devices ---")

	// Register a temperature sensor
	tempSensor, err := registry.RegisterDevice("Living Room Temp Sensor", "sensor", "Building A/Floor 1/Living Room")
	if err != nil {
		panic(err)
	}
	fmt.Printf("Registered: %s (ID: %s)\n", tempSensor.Name, tempSensor.ID)

	// Register a smart thermostat
	thermostat, err := registry.RegisterDevice("Smart Thermostat", "actuator", "Building A/Floor 1/Living Room")
	if err != nil {
		panic(err)
	}
	fmt.Printf("Registered: %s (ID: %s)\n", thermostat.Name, thermostat.ID)

	// Register a security camera
	camera, err := registry.RegisterDevice("Front Door Camera", "camera", "Building A/Floor 1/Entrance")
	if err != nil {
		panic(err)
	}
	fmt.Printf("Registered: %s (ID: %s)\n", camera.Name, camera.ID)

	// Register a gateway device
	gateway, err := registry.RegisterDevice("Main Gateway", "gateway", "Building A/Floor 1/Server Room")
	if err != nil {
		panic(err)
	}
	fmt.Printf("Registered: %s (ID: %s)\n", gateway.Name, gateway.ID)

	fmt.Println()

	// Step 3: Activate devices (simulating network connection)
	fmt.Println("--- Step 2: Activating Devices ---")

	// In production, activation happens when device connects to the network
	registry.ActivateDevice(tempSensor.ID)
	registry.ActivateDevice(thermostat.ID)
	registry.ActivateDevice(camera.ID)
	registry.ActivateDevice(gateway.ID)
	fmt.Println("All devices activated and connected")
	fmt.Println()

	// Step 4: Authenticate devices (simulating secure connection)
	fmt.Println("--- Step 3: Device Authentication ---")

	// Each device authenticates using its ID and secret
	devices := registry.GetAllDevices()
	for _, dev := range devices {
		// Simulate authentication
		authenticated, _ := registry.Authenticate(dev.ID, dev.Secret)
		if authenticated != nil {
			fmt.Printf("✓ %s authenticated (Status: %s)\n", authenticated.Name, authenticated.Status)
		}
	}
	fmt.Println()

	// Step 5: Simulate heartbeats (device status reporting)
	fmt.Println("--- Step 4: Simulating Heartbeats ---")

	statusTracker := device.NewStatusTracker(100)

	// Simulate periodic heartbeats from each device
	for i := 0; i < 3; i++ {
		fmt.Printf("\n--- Heartbeat cycle %d ---\n", i+1)

		// Temperature sensor heartbeat
		tempHeartbeat := device.Heartbeat{
			DeviceID:  tempSensor.ID,
			Timestamp: time.Now(),
			Metrics: device.DeviceMetrics{
				CPUUsage:    15.2 + float64(i)*2.1,
				MemoryUsage: 45.0 + float64(i)*1.5,
				Temperature: 22.5 + float64(i)*0.3,
				BatteryLevel: 95.0 - float64(i)*2.0,
				Uptime:      86400 + int64(i)*3600,
			},
		}
		statusTracker.RecordHeartbeat(tempHeartbeat)
		fmt.Printf("  Temp sensor: CPU=%.1f%%, Temp=%.1f°C, Battery=%.0f%%\n",
			tempHeartbeat.Metrics.CPUUsage, tempHeartbeat.Metrics.Temperature, tempHeartbeat.Metrics.BatteryLevel)

		// Thermostat heartbeat
		thermoHeartbeat := device.Heartbeat{
			DeviceID:  thermostat.ID,
			Timestamp: time.Now(),
			Metrics: device.DeviceMetrics{
				CPUUsage:    25.0 + float64(i)*3.0,
				MemoryUsage: 60.0 + float64(i)*1.0,
				Temperature: 24.0,
				BatteryLevel: 100.0, // Powered, no battery
				Uptime:      86400 + int64(i)*3600,
			},
		}
		statusTracker.RecordHeartbeat(thermoHeartbeat)
		fmt.Printf("  Thermostat: CPU=%.1f%%, Temp=%.1f°C\n",
			thermoHeartbeat.Metrics.CPUUsage, thermoHeartbeat.Metrics.Temperature)

		// Camera heartbeat
		cameraHeartbeat := device.Heartbeat{
			DeviceID:  camera.ID,
			Timestamp: time.Now(),
			Metrics: device.DeviceMetrics{
				CPUUsage:    55.0 + float64(i)*5.0,
				MemoryUsage: 70.0 + float64(i)*2.0,
				Temperature: 35.0 + float64(i)*1.0,
				BatteryLevel: 0, // Powered
				Uptime:      86400 + int64(i)*3600,
			},
		}
		statusTracker.RecordHeartbeat(cameraHeartbeat)
		fmt.Printf("  Camera: CPU=%.1f%%, Temp=%.1f°C, Memory=%.1f%%\n",
			cameraHeartbeat.Metrics.CPUUsage, cameraHeartbeat.Metrics.Temperature, cameraHeartbeat.Metrics.MemoryUsage)

		// Gateway heartbeat
		gatewayHeartbeat := device.Heartbeat{
			DeviceID:  gateway.ID,
			Timestamp: time.Now(),
			Metrics: device.DeviceMetrics{
				CPUUsage:    30.0 + float64(i)*4.0,
				MemoryUsage: 50.0 + float64(i)*3.0,
				Temperature: 40.0 + float64(i)*0.5,
				BatteryLevel: 0,
				Uptime:      172800 + int64(i)*3600, // Gateway has been running longer
			},
		}
		statusTracker.RecordHeartbeat(gatewayHeartbeat)
		fmt.Printf("  Gateway: CPU=%.1f%%, Temp=%.1f°C, Memory=%.1f%%\n",
			gatewayHeartbeat.Metrics.CPUUsage, gatewayHeartbeat.Metrics.Temperature, gatewayHeartbeat.Metrics.MemoryUsage)

		time.Sleep(100 * time.Millisecond)
	}
	fmt.Println()

	// Step 6: Check device health summary
	fmt.Println("--- Step 5: Device Health Summary ---")

	summary := statusTracker.GetDeviceSummary()
	for deviceID, devSummary := range summary {
		fmt.Printf("  %s: %s\n", deviceID, devSummary.String())
	}
	fmt.Println()

	// Step 7: Check online devices
	fmt.Println("--- Step 6: Online Devices ---")
	onlineDevices := statusTracker.GetOnlineDevices()
	fmt.Printf("Online devices: %d\n", len(onlineDevices))
	for _, id := range onlineDevices {
		fmt.Printf("  - %s\n", id)
	}
	fmt.Println()

	// Step 8: Demonstrate device status updates
	fmt.Println("--- Step 7: Status Changes ---")

	// Simulate a device going offline
	registry.DeactivateDevice(camera.ID)
	fmt.Printf("Camera %s deactivated (simulating disconnect)\n", camera.ID)

	// Check if camera is still online
	if registry.IsDeviceOnline(camera.ID, 5*time.Minute) {
		fmt.Println("Camera is still online")
	} else {
		fmt.Println("Camera is OFFLINE")
	}

	// Check all devices
	fmt.Println("\nFinal device status:")
	allDevices := registry.GetAllDevices()
	for _, dev := range allDevices {
		fmt.Printf("  %s: %s\n", dev.Name, dev.Status)
	}
	fmt.Println()

	fmt.Println("=== Example Complete ===")
}
