// Example: Device grouping and filtering
// This example demonstrates how to organize devices into groups and filter them:
// 1. Create hierarchical device groups
// 2. Add/remove devices from groups
// 3. Filter devices by tags
// 4. Navigate group hierarchy
//
// Run with: go run main.go

package main

import (
	"fmt"

	"device-management/src"
)

func main() {
	fmt.Println("=== IoT Device Management - Grouping & Filtering ===\n")

	// Create registry and group manager
	registry := device.NewRegistry()
	groupManager := device.NewGroupManager()

	// Register devices
	sensor1, _ := registry.RegisterDevice("Temp Sensor A1", "sensor", "Building A/Floor 1")
	sensor2, _ := registry.RegisterDevice("Temp Sensor A2", "sensor", "Building A/Floor 2")
	sensor3, _ := registry.RegisterDevice("Temp Sensor B1", "sensor", "Building B/Floor 1")
	actuator1, _ := registry.RegisterDevice("HVAC A", "actuator", "Building A/Floor 1")
	actuator2, _ := registry.RegisterDevice("HVAC B", "actuator", "Building B/Floor 1")
	camera1, _ := registry.RegisterDevice("Camera A1", "camera", "Building A/Entrance")
	camera2, _ := registry.RegisterDevice("Camera B1", "camera", "Building B/Entrance")

	// Activate all devices
	registry.ActivateDevice(sensor1.ID)
	registry.ActivateDevice(sensor2.ID)
	registry.ActivateDevice(sensor3.ID)
	registry.ActivateDevice(actuator1.ID)
	registry.ActivateDevice(actuator2.ID)
	registry.ActivateDevice(camera1.ID)
	registry.ActivateDevice(camera2.ID)

	// Store devices for tag-based filtering
	devices := map[string]device.Device{
		sensor1.ID: *sensor1,
		sensor2.ID: *sensor2,
		sensor3.ID: *sensor3,
		actuator1.ID: *actuator1,
		actuator2.ID: *actuator2,
		camera1.ID: *camera1,
		camera2.ID: *camera2,
	}

	// Add tags to devices
	sensor1.Tags["zone"] = "floor1"
	sensor1.Tags["building"] = "A"
	sensor2.Tags["zone"] = "floor2"
	sensor2.Tags["building"] = "A"
	sensor3.Tags["zone"] = "floor1"
	sensor3.Tags["building"] = "B"
	actuator1.Tags["zone"] = "floor1"
	actuator1.Tags["building"] = "A"
	actuator2.Tags["zone"] = "floor1"
	actuator2.Tags["building"] = "B"
	camera1.Tags["zone"] = "entrance"
	camera1.Tags["building"] = "A"
	camera2.Tags["zone"] = "entrance"
	camera2.Tags["building"] = "B"

	// Step 1: Create hierarchical groups
	fmt.Println("--- Step 1: Creating Device Groups ---")

	// Create top-level building groups
	buildingAGroup := groupManager.CreateGroup("Building A", "", map[string]string{
		"type": "building",
	})
	buildingBGroup := groupManager.CreateGroup("Building B", "", map[string]string{
		"type": "building",
	})

	// Create sub-groups (floors)
	floor1A := groupManager.CreateGroup("Floor 1 - Building A", buildingAGroup.ID, map[string]string{
		"type": "floor",
	})
	floor2A := groupManager.CreateGroup("Floor 2 - Building A", buildingAGroup.ID, map[string]string{
		"type": "floor",
	})

	// Create device-type groups
	sensorGroup := groupManager.CreateGroup("All Sensors", "", map[string]string{
		"type": "device-type",
	})
	cameraGroup := groupManager.CreateGroup("All Cameras", "", map[string]string{
		"type": "device-type",
	})

	fmt.Printf("Created groups:\n")
	fmt.Printf("  - %s (parent: %s)\n", buildingAGroup.Name, buildStr(buildingAGroup.ParentID))
	fmt.Printf("  - %s (parent: %s)\n", buildingBGroup.Name, buildStr(buildingBGroup.ParentID))
	fmt.Printf("  - %s (parent: %s)\n", floor1A.Name, buildStr(floor1A.ParentID))
	fmt.Printf("  - %s (parent: %s)\n", floor2A.Name, buildStr(floor2A.ParentID))
	fmt.Printf("  - %s (parent: %s)\n", sensorGroup.Name, buildStr(sensorGroup.ParentID))
	fmt.Printf("  - %s (parent: %s)\n", cameraGroup.Name, buildStr(cameraGroup.ParentID))
	fmt.Println()

	// Step 2: Add devices to groups
	fmt.Println("--- Step 2: Adding Devices to Groups ---")

	// Add to building groups
	groupManager.AddDeviceToGroup(buildingAGroup.ID, sensor1.ID)
	groupManager.AddDeviceToGroup(buildingAGroup.ID, sensor2.ID)
	groupManager.AddDeviceToGroup(buildingAGroup.ID, actuator1.ID)
	groupManager.AddDeviceToGroup(buildingAGroup.ID, camera1.ID)
	groupManager.AddDeviceToGroup(buildingBGroup.ID, sensor3.ID)
	groupManager.AddDeviceToGroup(buildingBGroup.ID, actuator2.ID)
	groupManager.AddDeviceToGroup(buildingBGroup.ID, camera2.ID)

	// Add to floor groups
	groupManager.AddDeviceToGroup(floor1A.ID, sensor1.ID)
	groupManager.AddDeviceToGroup(floor1A.ID, actuator1.ID)
	groupManager.AddDeviceToGroup(floor2A.ID, sensor2.ID)

	// Add to device-type groups
	groupManager.AddDeviceToGroup(sensorGroup.ID, sensor1.ID)
	groupManager.AddDeviceToGroup(sensorGroup.ID, sensor2.ID)
	groupManager.AddDeviceToGroup(sensorGroup.ID, sensor3.ID)
	groupManager.AddDeviceToGroup(cameraGroup.ID, camera1.ID)
	groupManager.AddDeviceToGroup(cameraGroup.ID, camera2.ID)

	fmt.Println("Devices added to groups successfully")
	fmt.Println()

	// Step 3: Query groups
	fmt.Println("--- Step 3: Querying Groups ---")

	// Get devices in Building A
	buildingADevices, _ := groupManager.GetDevicesInGroup(buildingAGroup.ID)
	fmt.Printf("Devices in %s: %d\n", buildingAGroup.Name, len(buildingADevices))
	for _, id := range buildingADevices {
		if dev, ok := devices[id]; ok {
			fmt.Printf("  - %s (%s)\n", dev.Name, dev.Type)
		}
	}
	fmt.Println()

	// Get devices in Floor 1 - Building A
	floor1Devices, _ := groupManager.GetDevicesInGroup(floor1A.ID)
	fmt.Printf("Devices in %s: %d\n", floor1A.Name, len(floor1Devices))
	for _, id := range floor1Devices {
		if dev, ok := devices[id]; ok {
			fmt.Printf("  - %s (%s)\n", dev.Name, dev.Type)
		}
	}
	fmt.Println()

	// Get devices in sensor group
	sensorDevices, _ := groupManager.GetDevicesInGroup(sensorGroup.ID)
	fmt.Printf("Devices in %s: %d\n", sensorGroup.Name, len(sensorDevices))
	for _, id := range sensorDevices {
		if dev, ok := devices[id]; ok {
			fmt.Printf("  - %s (%s, building=%s, zone=%s)\n", dev.Name, dev.Type, dev.Tags["building"], dev.Tags["zone"])
		}
	}
	fmt.Println()

	// Step 4: Filter by tags
	fmt.Println("--- Step 4: Filtering by Tags ---")

	// Find all groups containing devices tagged with building=A
	groupsA := groupManager.GetGroupsByDeviceTag(devices, "building", "A")
	fmt.Printf("Groups with devices in building A: %d\n", len(groupsA))
	for _, gid := range groupsA {
		fmt.Printf("  - %s\n", gid)
	}
	fmt.Println()

	// Find all groups containing devices tagged with zone=floor1
	groupsFloor1 := groupManager.GetGroupsByDeviceTag(devices, "zone", "floor1")
	fmt.Printf("Groups with devices in floor1: %d\n", len(groupsFloor1))
	for _, gid := range groupsFloor1 {
		fmt.Printf("  - %s\n", gid)
	}
	fmt.Println()

	// Step 5: Navigate group hierarchy
	fmt.Println("--- Step 5: Group Hierarchy ---")

	hierarchy := groupManager.GetGroupHierarchy(floor1A.ID)
	fmt.Printf("Hierarchy for '%s':\n", floor1A.Name)
	for i, g := range hierarchy {
		indent := ""
		for j := 0; j < i; j++ {
			indent += "  "
		}
		fmt.Printf("  %s%s (parent: %s)\n", indent, g.Name, buildStr(g.ParentID))
	}
	fmt.Println()

	// Step 6: Remove device from group
	fmt.Println("--- Step 6: Remove Device from Group ---")

	groupManager.RemoveDeviceFromGroup(floor2A.ID, sensor2.ID)
	remainingDevices, _ := groupManager.GetDevicesInGroup(floor2A.ID)
	fmt.Printf("After removing sensor2 from %s: %d devices\n", floor2A.Name, len(remainingDevices))
	fmt.Println()

	// Step 7: List all groups
	fmt.Println("--- Step 7: All Groups ---")
	allGroups := groupManager.GetAllGroups()
	fmt.Printf("Total groups: %d\n", len(allGroups))
	for _, g := range allGroups {
		fmt.Printf("  - %s (%d devices)\n", g.Name, len(g.Devices))
	}
	fmt.Println()

	fmt.Println("=== Example Complete ===")
}

func buildStr(id string) string {
	if id == "" {
		return "<root>"
	}
	return id
}
