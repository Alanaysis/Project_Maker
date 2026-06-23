package test

import (
	"testing"

	"github.com/yourusername/device-management/internal/device"
)

func TestRegisterDevice(t *testing.T) {
	dm := device.NewDeviceManager()

	// 测试注册设备
	metadata := map[string]string{"location": "office"}
	dev, err := dm.RegisterDevice("温度传感器", "sensor", metadata)
	if err != nil {
		t.Fatalf("注册设备失败: %v", err)
	}

	if dev.Name != "温度传感器" {
		t.Errorf("设备名称错误: got %s, want %s", dev.Name, "温度传感器")
	}

	if dev.Type != "sensor" {
		t.Errorf("设备类型错误: got %s, want %s", dev.Type, "sensor")
	}

	if dev.Status != device.StatusOnline {
		t.Errorf("设备状态错误: got %s, want %s", dev.Status, device.StatusOnline)
	}
}

func TestGetDevice(t *testing.T) {
	dm := device.NewDeviceManager()

	// 先注册一个设备
	dev, _ := dm.RegisterDevice("湿度传感器", "sensor", nil)

	// 测试获取设备
	got, err := dm.GetDevice(dev.ID)
	if err != nil {
		t.Fatalf("获取设备失败: %v", err)
	}

	if got.ID != dev.ID {
		t.Errorf("设备ID不匹配: got %s, want %s", got.ID, dev.ID)
	}

	// 测试获取不存在的设备
	_, err = dm.GetDevice("non-existent-id")
	if err == nil {
		t.Error("应该返回错误")
	}
}

func TestListDevices(t *testing.T) {
	dm := device.NewDeviceManager()

	// 注册多个设备
	dm.RegisterDevice("设备1", "sensor", nil)
	dm.RegisterDevice("设备2", "actuator", nil)
	dm.RegisterDevice("设备3", "gateway", nil)

	// 测试列出设备
	devices := dm.ListDevices()
	if len(devices) != 3 {
		t.Errorf("设备数量错误: got %d, want %d", len(devices), 3)
	}
}

func TestUpdateDeviceStatus(t *testing.T) {
	dm := device.NewDeviceManager()

	// 先注册一个设备
	dev, _ := dm.RegisterDevice("传感器", "sensor", nil)

	// 测试更新状态
	err := dm.UpdateDeviceStatus(dev.ID, 80, 90, "v1.0", "192.168.1.100")
	if err != nil {
		t.Fatalf("更新设备状态失败: %v", err)
	}

	// 验证更新
	updated, _ := dm.GetDevice(dev.ID)
	if updated.Battery != 80 {
		t.Errorf("电量错误: got %d, want %d", updated.Battery, 80)
	}

	if updated.Signal != 90 {
		t.Errorf("信号强度错误: got %d, want %d", updated.Signal, 90)
	}

	if updated.Firmware != "v1.0" {
		t.Errorf("固件版本错误: got %s, want %s", updated.Firmware, "v1.0")
	}

	// 测试更新不存在的设备
	err = dm.UpdateDeviceStatus("non-existent-id", 50, 50, "v1.0", "192.168.1.1")
	if err == nil {
		t.Error("应该返回错误")
	}
}

func TestSetDeviceOnlineOffline(t *testing.T) {
	dm := device.NewDeviceManager()

	// 先注册一个设备
	dev, _ := dm.RegisterDevice("设备", "sensor", nil)

	// 测试设置离线
	err := dm.SetDeviceOffline(dev.ID)
	if err != nil {
		t.Fatalf("设置设备离线失败: %v", err)
	}

	offline, _ := dm.GetDevice(dev.ID)
	if offline.Status != device.StatusOffline {
		t.Errorf("设备状态错误: got %s, want %s", offline.Status, device.StatusOffline)
	}

	// 测试设置在线
	err = dm.SetDeviceOnline(dev.ID)
	if err != nil {
		t.Fatalf("设置设备在线失败: %v", err)
	}

	online, _ := dm.GetDevice(dev.ID)
	if online.Status != device.StatusOnline {
		t.Errorf("设备状态错误: got %s, want %s", online.Status, device.StatusOnline)
	}
}

func TestDeleteDevice(t *testing.T) {
	dm := device.NewDeviceManager()

	// 先注册一个设备
	dev, _ := dm.RegisterDevice("临时设备", "sensor", nil)

	// 测试删除设备
	err := dm.DeleteDevice(dev.ID)
	if err != nil {
		t.Fatalf("删除设备失败: %v", err)
	}

	// 验证删除
	_, err = dm.GetDevice(dev.ID)
	if err == nil {
		t.Error("设备应该已被删除")
	}

	// 测试删除不存在的设备
	err = dm.DeleteDevice("non-existent-id")
	if err == nil {
		t.Error("应该返回错误")
	}
}

func TestDeviceEvents(t *testing.T) {
	dm := device.NewDeviceManager()

	// 注册设备触发事件
	dev, _ := dm.RegisterDevice("事件测试设备", "sensor", nil)

	// 获取事件
	eventChan := dm.GetEventChannel()

	// 应该有一个注册事件
	event := <-eventChan
	if event.Type != "device_registered" {
		t.Errorf("事件类型错误: got %s, want %s", event.Type, "device_registered")
	}

	if event.DeviceID != dev.ID {
		t.Errorf("事件设备ID错误: got %s, want %s", event.DeviceID, dev.ID)
	}
}
