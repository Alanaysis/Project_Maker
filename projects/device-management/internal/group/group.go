package group

import (
	"fmt"
	"sync"
	"time"

	"github.com/yourusername/device-management/internal/device"
)

// Group 设备分组
type Group struct {
	ID          string    `json:"id"`
	Name        string    `json:"name"`
	Description string    `json:"description"`
	DeviceIDs   []string  `json:"device_ids"`
	CreatedAt   time.Time `json:"created_at"`
	UpdatedAt   time.Time `json:"updated_at"`
}

// GroupManager 分组管理器
type GroupManager struct {
	mu     sync.RWMutex
	groups map[string]*Group
	dm     *device.DeviceManager
}

// NewGroupManager 创建分组管理器
func NewGroupManager(dm *device.DeviceManager) *GroupManager {
	return &GroupManager{
		groups: make(map[string]*Group),
		dm:     dm,
	}
}

// CreateGroup 创建分组
func (gm *GroupManager) CreateGroup(name, description string) (*Group, error) {
	gm.mu.Lock()
	defer gm.mu.Unlock()

	groupID := fmt.Sprintf("GRP-%d", time.Now().UnixNano())

	group := &Group{
		ID:          groupID,
		Name:        name,
		Description: description,
		DeviceIDs:   make([]string, 0),
		CreatedAt:   time.Now(),
		UpdatedAt:   time.Now(),
	}

	gm.groups[groupID] = group
	return group, nil
}

// GetGroup 获取分组
func (gm *GroupManager) GetGroup(groupID string) (*Group, error) {
	gm.mu.RLock()
	defer gm.mu.RUnlock()

	group, exists := gm.groups[groupID]
	if !exists {
		return nil, fmt.Errorf("分组不存在: %s", groupID)
	}

	return group, nil
}

// ListGroups 列出所有分组
func (gm *GroupManager) ListGroups() []*Group {
	gm.mu.RLock()
	defer gm.mu.RUnlock()

	groups := make([]*Group, 0, len(gm.groups))
	for _, group := range gm.groups {
		groups = append(groups, group)
	}

	return groups
}

// AddDeviceToGroup 添加设备到分组
func (gm *GroupManager) AddDeviceToGroup(groupID, deviceID string) error {
	gm.mu.Lock()
	defer gm.mu.Unlock()

	group, exists := gm.groups[groupID]
	if !exists {
		return fmt.Errorf("分组不存在: %s", groupID)
	}

	// 检查设备是否存在
	_, err := gm.dm.GetDevice(deviceID)
	if err != nil {
		return fmt.Errorf("设备不存在: %s", deviceID)
	}

	// 检查设备是否已在分组中
	for _, id := range group.DeviceIDs {
		if id == deviceID {
			return fmt.Errorf("设备已在分组中: %s", deviceID)
		}
	}

	group.DeviceIDs = append(group.DeviceIDs, deviceID)
	group.UpdatedAt = time.Now()

	return nil
}

// RemoveDeviceFromGroup 从分组移除设备
func (gm *GroupManager) RemoveDeviceFromGroup(groupID, deviceID string) error {
	gm.mu.Lock()
	defer gm.mu.Unlock()

	group, exists := gm.groups[groupID]
	if !exists {
		return fmt.Errorf("分组不存在: %s", groupID)
	}

	for i, id := range group.DeviceIDs {
		if id == deviceID {
			group.DeviceIDs = append(group.DeviceIDs[:i], group.DeviceIDs[i+1:]...)
			group.UpdatedAt = time.Now()
			return nil
		}
	}

	return fmt.Errorf("设备不在分组中: %s", deviceID)
}

// GetGroupDevices 获取分组内的所有设备
func (gm *GroupManager) GetGroupDevices(groupID string) ([]*device.Device, error) {
	gm.mu.RLock()
	defer gm.mu.RUnlock()

	group, exists := gm.groups[groupID]
	if !exists {
		return nil, fmt.Errorf("分组不存在: %s", groupID)
	}

	devices := make([]*device.Device, 0)
	for _, deviceID := range group.DeviceIDs {
		d, err := gm.dm.GetDevice(deviceID)
		if err == nil {
			devices = append(devices, d)
		}
	}

	return devices, nil
}

// DeleteGroup 删除分组
func (gm *GroupManager) DeleteGroup(groupID string) error {
	gm.mu.Lock()
	defer gm.mu.Unlock()

	if _, exists := gm.groups[groupID]; !exists {
		return fmt.Errorf("分组不存在: %s", groupID)
	}

	delete(gm.groups, groupID)
	return nil
}
