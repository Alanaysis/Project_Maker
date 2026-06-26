package device

import (
	"testing"
)

func TestGroupManager_CreateGroup(t *testing.T) {
	gm := NewGroupManager()

	group := gm.CreateGroup("Test Group", "", nil)

	if group.ID == "" {
		t.Error("Group ID should not be empty")
	}

	if group.Name != "Test Group" {
		t.Errorf("Group name should be 'Test Group', got '%s'", group.Name)
	}
}

func TestGroupManager_AddDeviceToGroup(t *testing.T) {
	gm := NewGroupManager()

	group := gm.CreateGroup("Test Group", "", nil)

	err := gm.AddDeviceToGroup(group.ID, "device-1")
	if err != nil {
		t.Fatalf("Failed to add device to group: %v", err)
	}

	devices, err := gm.GetDevicesInGroup(group.ID)
	if err != nil {
		t.Fatalf("Failed to get devices in group: %v", err)
	}

	if len(devices) != 1 {
		t.Errorf("Expected 1 device in group, got %d", len(devices))
	}

	if devices[0] != "device-1" {
		t.Errorf("Expected device 'device-1', got '%s'", devices[0])
	}
}

func TestGroupManager_RemoveDeviceFromGroup(t *testing.T) {
	gm := NewGroupManager()

	group := gm.CreateGroup("Test Group", "", nil)

	gm.AddDeviceToGroup(group.ID, "device-1")

	err := gm.RemoveDeviceFromGroup(group.ID, "device-1")
	if err != nil {
		t.Fatalf("Failed to remove device from group: %v", err)
	}

	devices, err := gm.GetDevicesInGroup(group.ID)
	if err != nil {
		t.Fatalf("Failed to get devices in group: %v", err)
	}

	if len(devices) != 0 {
		t.Errorf("Expected 0 devices in group, got %d", len(devices))
	}
}

func TestGroupManager_GetDeviceGroup(t *testing.T) {
	gm := NewGroupManager()

	group := gm.CreateGroup("Test Group", "", nil)

	gm.AddDeviceToGroup(group.ID, "device-1")

	groupID, err := gm.GetDeviceGroup("device-1")
	if err != nil {
		t.Fatalf("Failed to get device group: %v", err)
	}

	if groupID != group.ID {
		t.Errorf("Expected group ID '%s', got '%s'", group.ID, groupID)
	}
}

func TestGroupManager_GetGroupsByTag(t *testing.T) {
	gm := NewGroupManager()

	gm.CreateGroup("Group A", "", map[string]string{"env": "production"})
	groupB := gm.CreateGroup("Group B", "", map[string]string{"env": "staging"})
	gm.CreateGroup("Group C", "", map[string]string{"env": "production"})

	groups := gm.GetGroupsByTag("env", "production")

	if len(groups) != 2 {
		t.Errorf("Expected 2 groups with env=production, got %d", len(groups))
	}

	// Verify group B is not included
	for _, g := range groups {
		if g.ID == groupB.ID {
			t.Error("Group B should not be in production groups")
		}
	}
}

func TestGroupManager_GetGroupHierarchy(t *testing.T) {
	gm := NewGroupManager()

	parent := gm.CreateGroup("Parent Group", "", nil)
	child := gm.CreateGroup("Child Group", parent.ID, nil)

	hierarchy := gm.GetGroupHierarchy(child.ID)

	if len(hierarchy) != 2 {
		t.Errorf("Expected hierarchy of length 2, got %d", len(hierarchy))
	}

	// First should be child, second should be parent
	if hierarchy[0].ID != child.ID {
		t.Error("First in hierarchy should be the child group")
	}

	if hierarchy[1].ID != parent.ID {
		t.Error("Second in hierarchy should be the parent group")
	}
}

func TestGroupManager_GetAllGroups(t *testing.T) {
	gm := NewGroupManager()

	gm.CreateGroup("Group 1", "", nil)
	gm.CreateGroup("Group 2", "", nil)

	groups := gm.GetAllGroups()

	if len(groups) != 2 {
		t.Errorf("Expected 2 groups, got %d", len(groups))
	}
}
