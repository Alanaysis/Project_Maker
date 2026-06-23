package device

import (
	"fmt"
	"sync"
	"time"
)

// DeviceStatus 设备状态
type DeviceStatus string

const (
	StatusOnline  DeviceStatus = "online"
	StatusOffline DeviceStatus = "offline"
	StatusUpgrading DeviceStatus = "upgrading"
)

// Device 设备实体
type Device struct {
	ID        string            `json:"id"`
	Name      string            `json:"name"`
	Type      string            `json:"type"`
	Status    DeviceStatus      `json:"status"`
	GroupID   string            `json:"group_id,omitempty"`
	LastSeen  time.Time         `json:"last_seen"`
	CreatedAt time.Time         `json:"created_at"`
	Metadata  map[string]string `json:"metadata,omitempty"`
	// 设备状态数据
	Battery    int    `json:"battery"`    // 电量 0-100
	Signal     int    `json:"signal"`     // 信号强度 0-100
	Firmware   string `json:"firmware"`   // 固件版本
	IPAddress  string `json:"ip_address"` // IP地址
}

// DeviceManager 设备管理器
type DeviceManager struct {
	mu      sync.RWMutex
	devices map[string]*Device
	// 设备事件通知
	eventChan chan *DeviceEvent
}

// DeviceEvent 设备事件
type DeviceEvent struct {
	Type      string    `json:"type"`
	DeviceID  string    `json:"device_id"`
	Timestamp time.Time `json:"timestamp"`
	Data      interface{} `json:"data,omitempty"`
}

// NewDeviceManager 创建设备管理器
func NewDeviceManager() *DeviceManager {
	return &DeviceManager{
		devices:   make(map[string]*Device),
		eventChan: make(chan *DeviceEvent, 100),
	}
}

// RegisterDevice 注册设备
func (dm *DeviceManager) RegisterDevice(name, deviceType string, metadata map[string]string) (*Device, error) {
	dm.mu.Lock()
	defer dm.mu.Unlock()

	deviceID := generateDeviceID()

	// 检查设备ID是否已存在
	if _, exists := dm.devices[deviceID]; exists {
		return nil, fmt.Errorf("设备ID已存在: %s", deviceID)
	}

	now := time.Now()
	device := &Device{
		ID:        deviceID,
		Name:      name,
		Type:      deviceType,
		Status:    StatusOnline,
		LastSeen:  now,
		CreatedAt: now,
		Metadata:  metadata,
		Battery:   100,
		Signal:    100,
	}

	dm.devices[deviceID] = device

	// 发送注册事件
	dm.eventChan <- &DeviceEvent{
		Type:      "device_registered",
		DeviceID:  deviceID,
		Timestamp: now,
		Data:      device,
	}

	return device, nil
}

// GetDevice 获取设备信息
func (dm *DeviceManager) GetDevice(deviceID string) (*Device, error) {
	dm.mu.RLock()
	defer dm.mu.RUnlock()

	device, exists := dm.devices[deviceID]
	if !exists {
		return nil, fmt.Errorf("设备不存在: %s", deviceID)
	}

	return device, nil
}

// ListDevices 列出所有设备
func (dm *DeviceManager) ListDevices() []*Device {
	dm.mu.RLock()
	defer dm.mu.RUnlock()

	devices := make([]*Device, 0, len(dm.devices))
	for _, device := range dm.devices {
		devices = append(devices, device)
	}

	return devices
}

// UpdateDeviceStatus 更新设备状态
func (dm *DeviceManager) UpdateDeviceStatus(deviceID string, battery, signal int, firmware, ipAddress string) error {
	dm.mu.Lock()
	defer dm.mu.Unlock()

	device, exists := dm.devices[deviceID]
	if !exists {
		return fmt.Errorf("设备不存在: %s", deviceID)
	}

	device.Battery = battery
	device.Signal = signal
	device.Firmware = firmware
	device.IPAddress = ipAddress
	device.LastSeen = time.Now()

	// 发送状态更新事件
	dm.eventChan <- &DeviceEvent{
		Type:      "status_updated",
		DeviceID:  deviceID,
		Timestamp: time.Now(),
		Data: map[string]interface{}{
			"battery":  battery,
			"signal":   signal,
			"firmware": firmware,
		},
	}

	return nil
}

// SetDeviceOnline 设置设备在线
func (dm *DeviceManager) SetDeviceOnline(deviceID string) error {
	dm.mu.Lock()
	defer dm.mu.Unlock()

	device, exists := dm.devices[deviceID]
	if !exists {
		return fmt.Errorf("设备不存在: %s", deviceID)
	}

	device.Status = StatusOnline
	device.LastSeen = time.Now()

	return nil
}

// SetDeviceOffline 设置设备离线
func (dm *DeviceManager) SetDeviceOffline(deviceID string) error {
	dm.mu.Lock()
	defer dm.mu.Unlock()

	device, exists := dm.devices[deviceID]
	if !exists {
		return fmt.Errorf("设备不存在: %s", deviceID)
	}

	device.Status = StatusOffline
	device.LastSeen = time.Now()

	return nil
}

// DeleteDevice 删除设备
func (dm *DeviceManager) DeleteDevice(deviceID string) error {
	dm.mu.Lock()
	defer dm.mu.Unlock()

	if _, exists := dm.devices[deviceID]; !exists {
		return fmt.Errorf("设备不存在: %s", deviceID)
	}

	delete(dm.devices, deviceID)

	// 发送删除事件
	dm.eventChan <- &DeviceEvent{
		Type:      "device_deleted",
		DeviceID:  deviceID,
		Timestamp: time.Now(),
	}

	return nil
}

// GetEventChannel 获取事件通道
func (dm *DeviceManager) GetEventChannel() <-chan *DeviceEvent {
	return dm.eventChan
}

// generateDeviceID 生成设备ID
func generateDeviceID() string {
	return fmt.Sprintf("DEV-%d", time.Now().UnixNano())
}
