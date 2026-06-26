package device

import (
	"fmt"
	"sync"
	"time"
)

// GroupManager manages device groups and hierarchical organization.
//
// Device Grouping in IoT:
// Devices are organized into groups for:
// - Batch operations (update all devices in a group)
// - Hierarchical organization (sites -> buildings -> rooms -> devices)
// - Filtering and querying (get all sensors in building A)
// - Access control (different teams manage different groups)
type GroupManager struct {
	mu        sync.RWMutex
	groups    map[string]*Group       // Group ID -> Group
	byDevice  map[string]string       // Device ID -> Group ID (for reverse lookup)
}

// NewGroupManager creates a new group manager.
func NewGroupManager() *GroupManager {
	return &GroupManager{
		groups:   make(map[string]*Group),
		byDevice: make(map[string]string),
	}
}

// CreateGroup creates a new device group.
func (gm *GroupManager) CreateGroup(name, parentID string, tags map[string]string) *Group {
	gm.mu.Lock()
	defer gm.mu.Unlock()

	group := &Group{
		ID:        generateGroupID(name),
		Name:      name,
		ParentID:  parentID,
		Devices:   make([]string, 0),
		Tags:      tags,
		CreatedAt: time.Now(),
	}

	gm.groups[group.ID] = group
	return group
}

// AddDeviceToGroup adds a device to a group.
func (gm *GroupManager) AddDeviceToGroup(groupID, deviceID string) error {
	gm.mu.Lock()
	defer gm.mu.Unlock()

	group, exists := gm.groups[groupID]
	if !exists {
		return fmt.Errorf("group not found: %s", groupID)
	}

	// Check if device is already in this group
	for _, id := range group.Devices {
		if id == deviceID {
			return fmt.Errorf("device %s is already in group %s", deviceID, groupID)
		}
	}

	group.Devices = append(group.Devices, deviceID)
	gm.byDevice[deviceID] = groupID
	return nil
}

// RemoveDeviceFromGroup removes a device from a group.
func (gm *GroupManager) RemoveDeviceFromGroup(groupID, deviceID string) error {
	gm.mu.Lock()
	defer gm.mu.Unlock()

	group, exists := gm.groups[groupID]
	if !exists {
		return fmt.Errorf("group not found: %s", groupID)
	}

	for i, id := range group.Devices {
		if id == deviceID {
			group.Devices = append(group.Devices[:i], group.Devices[i+1:]...)
			delete(gm.byDevice, deviceID)
			return nil
		}
	}

	return fmt.Errorf("device %s not found in group %s", deviceID, groupID)
}

// GetDevicesInGroup returns all device IDs in a group.
func (gm *GroupManager) GetDevicesInGroup(groupID string) ([]string, error) {
	gm.mu.RLock()
	defer gm.mu.RUnlock()

	group, exists := gm.groups[groupID]
	if !exists {
		return nil, fmt.Errorf("group not found: %s", groupID)
	}

	devices := make([]string, len(group.Devices))
	copy(devices, group.Devices)
	return devices, nil
}

// GetDeviceGroup returns the group ID for a device.
func (gm *GroupManager) GetDeviceGroup(deviceID string) (string, error) {
	gm.mu.RLock()
	defer gm.mu.RUnlock()

	groupID, exists := gm.byDevice[deviceID]
	if !exists {
		return "", fmt.Errorf("device %s is not in any group", deviceID)
	}

	return groupID, nil
}

// GetGroupsByTag returns all groups matching the given tag key-value pair.
func (gm *GroupManager) GetGroupsByTag(key, value string) []*Group {
	gm.mu.RLock()
	defer gm.mu.RUnlock()

	var matching []*Group
	for _, group := range gm.groups {
		if group.Tags != nil {
			if group.Tags[key] == value {
				groupCopy := *group
				matching = append(matching, &groupCopy)
			}
		}
	}
	return matching
}

// GetGroupsByDeviceTag returns groups where any device has the given tag.
// This enables filtering devices by their tags across groups.
func (gm *GroupManager) GetGroupsByDeviceTag(devices map[string]Device, key, value string) []string {
	gm.mu.RLock()
	defer gm.mu.RUnlock()

	var groupIDs []string
	for groupID, group := range gm.groups {
		for _, deviceID := range group.Devices {
			if dev, exists := devices[deviceID]; exists {
				if dev.Tags != nil && dev.Tags[key] == value {
					groupIDs = append(groupIDs, groupID)
					break
				}
			}
		}
	}
	return groupIDs
}

// GetGroupHierarchy returns the parent chain for a group (for hierarchical navigation).
func (gm *GroupManager) GetGroupHierarchy(groupID string) []*Group {
	gm.mu.RLock()
	defer gm.mu.RUnlock()

	var hierarchy []*Group
	currentID := groupID

	for currentID != "" {
		group, exists := gm.groups[currentID]
		if !exists {
			break
		}

		groupCopy := *group
		hierarchy = append(hierarchy, &groupCopy)
		currentID = group.ParentID
	}

	return hierarchy
}

// GetAllGroups returns all groups.
func (gm *GroupManager) GetAllGroups() []*Group {
	gm.mu.RLock()
	defer gm.mu.RUnlock()

	groups := make([]*Group, 0, len(gm.groups))
	for _, group := range gm.groups {
		groupCopy := *group
		groups = append(groups, &groupCopy)
	}
	return groups
}

// generateGroupID creates a group ID from its name.
func generateGroupID(name string) string {
	// In production, use UUID. For learning, use a simple hash.
	return fmt.Sprintf("grp-%s", name)
}
