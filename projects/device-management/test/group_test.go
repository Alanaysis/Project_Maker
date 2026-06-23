package test

import (
	"testing"

	"github.com/yourusername/device-management/internal/device"
	"github.com/yourusername/device-management/internal/group"
)

func TestCreateGroup(t *testing.T) {
	dm := device.NewDeviceManager()
	gm := group.NewGroupManager(dm)

	// 测试创建分组
	grp, err := gm.CreateGroup("办公室传感器", "办公室内的所有传感器设备")
	if err != nil {
		t.Fatalf("创建分组失败: %v", err)
	}

	if grp.Name != "办公室传感器" {
		t.Errorf("分组名称错误: got %s, want %s", grp.Name, "办公室传感器")
	}

	if grp.Description != "办公室内的所有传感器设备" {
		t.Errorf("分组描述错误: got %s, want %s", grp.Description, "办公室内的所有传感器设备")
	}

	if len(grp.DeviceIDs) != 0 {
		t.Errorf("初始设备数量应该为0: got %d", len(grp.DeviceIDs))
	}
}

func TestGetGroup(t *testing.T) {
	dm := device.NewDeviceManager()
	gm := group.NewGroupManager(dm)

	// 先创建一个分组
	grp, _ := gm.CreateGroup("测试分组", "测试描述")

	// 测试获取分组
	got, err := gm.GetGroup(grp.ID)
	if err != nil {
		t.Fatalf("获取分组失败: %v", err)
	}

	if got.ID != grp.ID {
		t.Errorf("分组ID不匹配: got %s, want %s", got.ID, grp.ID)
	}

	// 测试获取不存在的分组
	_, err = gm.GetGroup("non-existent-id")
	if err == nil {
		t.Error("应该返回错误")
	}
}

func TestListGroups(t *testing.T) {
	dm := device.NewDeviceManager()
	gm := group.NewGroupManager(dm)

	// 创建多个分组
	gm.CreateGroup("分组1", "描述1")
	gm.CreateGroup("分组2", "描述2")
	gm.CreateGroup("分组3", "描述3")

	// 测试列出分组
	groups := gm.ListGroups()
	if len(groups) != 3 {
		t.Errorf("分组数量错误: got %d, want %d", len(groups), 3)
	}
}

func TestAddDeviceToGroup(t *testing.T) {
	dm := device.NewDeviceManager()
	gm := group.NewGroupManager(dm)

	// 创建设备和分组
	dev, _ := dm.RegisterDevice("温度传感器", "sensor", nil)
	grp, _ := gm.CreateGroup("传感器组", "所有传感器")

	// 测试添加设备到分组
	err := gm.AddDeviceToGroup(grp.ID, dev.ID)
	if err != nil {
		t.Fatalf("添加设备到分组失败: %v", err)
	}

	// 验证设备已添加
	group, _ := gm.GetGroup(grp.ID)
	if len(group.DeviceIDs) != 1 {
		t.Errorf("分组设备数量错误: got %d, want %d", len(group.DeviceIDs), 1)
	}

	if group.DeviceIDs[0] != dev.ID {
		t.Errorf("分组设备ID不匹配: got %s, want %s", group.DeviceIDs[0], dev.ID)
	}

	// 测试重复添加
	err = gm.AddDeviceToGroup(grp.ID, dev.ID)
	if err == nil {
		t.Error("应该返回错误")
	}
}

func TestRemoveDeviceFromGroup(t *testing.T) {
	dm := device.NewDeviceManager()
	gm := group.NewGroupManager(dm)

	// 创建设备和分组
	dev, _ := dm.RegisterDevice("传感器", "sensor", nil)
	grp, _ := gm.CreateGroup("测试组", "测试")

	// 先添加设备
	gm.AddDeviceToGroup(grp.ID, dev.ID)

	// 测试移除设备
	err := gm.RemoveDeviceFromGroup(grp.ID, dev.ID)
	if err != nil {
		t.Fatalf("移除设备失败: %v", err)
	}

	// 验证设备已移除
	group, _ := gm.GetGroup(grp.ID)
	if len(group.DeviceIDs) != 0 {
		t.Errorf("分组设备数量应该为0: got %d", len(group.DeviceIDs))
	}

	// 测试移除不存在的设备
	err = gm.RemoveDeviceFromGroup(grp.ID, dev.ID)
	if err == nil {
		t.Error("应该返回错误")
	}
}

func TestGetGroupDevices(t *testing.T) {
	dm := device.NewDeviceManager()
	gm := group.NewGroupManager(dm)

	// 创建多个设备和分组
	dev1, _ := dm.RegisterDevice("设备1", "sensor", nil)
	dev2, _ := dm.RegisterDevice("设备2", "sensor", nil)
	dev3, _ := dm.RegisterDevice("设备3", "actuator", nil)

	grp, _ := gm.CreateGroup("混合组", "混合设备")

	// 添加设备到分组
	gm.AddDeviceToGroup(grp.ID, dev1.ID)
	gm.AddDeviceToGroup(grp.ID, dev2.ID)
	gm.AddDeviceToGroup(grp.ID, dev3.ID)

	// 测试获取分组设备
	devices, err := gm.GetGroupDevices(grp.ID)
	if err != nil {
		t.Fatalf("获取分组设备失败: %v", err)
	}

	if len(devices) != 3 {
		t.Errorf("设备数量错误: got %d, want %d", len(devices), 3)
	}
}

func TestDeleteGroup(t *testing.T) {
	dm := device.NewDeviceManager()
	gm := group.NewGroupManager(dm)

	// 创建分组
	grp, _ := gm.CreateGroup("临时分组", "临时")

	// 测试删除分组
	err := gm.DeleteGroup(grp.ID)
	if err != nil {
		t.Fatalf("删除分组失败: %v", err)
	}

	// 验证删除
	_, err = gm.GetGroup(grp.ID)
	if err == nil {
		t.Error("分组应该已被删除")
	}

	// 测试删除不存在的分组
	err = gm.DeleteGroup("non-existent-id")
	if err == nil {
		t.Error("应该返回错误")
	}
}
