package tests

import (
	"net"
	"testing"

	"github.com/minicontainer/runtime/pkg/network"
)

// TestNewNetworkManager 测试创建网络管理器
func TestNewNetworkManager(t *testing.T) {
	mgr, err := network.NewNetworkManager("", "")
	if err != nil {
		t.Fatalf("Failed to create network manager: %v", err)
	}

	// 验证默认配置
	if mgr.BridgeName != network.DefaultBridgeName {
		t.Errorf("Expected bridge name '%s', got '%s'", network.DefaultBridgeName, mgr.BridgeName)
	}

	if mgr.Subnet.String() != network.DefaultSubnet {
		t.Errorf("Expected subnet '%s', got '%s'", network.DefaultSubnet, mgr.Subnet.String())
	}

	if mgr.Gateway.String() != network.DefaultGateway {
		t.Errorf("Expected gateway '%s', got '%s'", network.DefaultGateway, mgr.Gateway.String())
	}
}

// TestNewNetworkManagerCustom 测试自定义配置创建网络管理器
func TestNewNetworkManagerCustom(t *testing.T) {
	mgr, err := network.NewNetworkManager("mybridge", "10.0.0.0/24")
	if err != nil {
		t.Fatalf("Failed to create network manager: %v", err)
	}

	if mgr.BridgeName != "mybridge" {
		t.Errorf("Expected bridge name 'mybridge', got '%s'", mgr.BridgeName)
	}

	if mgr.Subnet.String() != "10.0.0.0/24" {
		t.Errorf("Expected subnet '10.0.0.0/24', got '%s'", mgr.Subnet.String())
	}

	// 网关应该是子网第一个可用 IP
	expectedGateway := "10.0.0.1"
	if mgr.Gateway.String() != expectedGateway {
		t.Errorf("Expected gateway '%s', got '%s'", expectedGateway, mgr.Gateway.String())
	}
}

// TestIPPoolAllocate 测试 IP 地址分配
func TestIPPoolAllocate(t *testing.T) {
	_, ipNet, _ := net.ParseCIDR("172.17.0.0/16")
	pool := network.NewIPPool(ipNet)

	// 分配第一个 IP（应该是 .2，跳过网关 .1）
	ip1, err := pool.Allocate()
	if err != nil {
		t.Fatalf("Failed to allocate IP: %v", err)
	}

	expectedIP1 := "172.17.0.2"
	if ip1.String() != expectedIP1 {
		t.Errorf("Expected IP '%s', got '%s'", expectedIP1, ip1.String())
	}

	// 分配第二个 IP
	ip2, err := pool.Allocate()
	if err != nil {
		t.Fatalf("Failed to allocate IP: %v", err)
	}

	expectedIP2 := "172.17.0.3"
	if ip2.String() != expectedIP2 {
		t.Errorf("Expected IP '%s', got '%s'", expectedIP2, ip2.String())
	}

	// 释放第一个 IP
	pool.Release(ip1)

	// 重新分配应该得到释放的 IP
	ip3, err := pool.Allocate()
	if err != nil {
		t.Fatalf("Failed to allocate IP: %v", err)
	}

	if ip3.String() != expectedIP1 {
		t.Errorf("Expected IP '%s' after release, got '%s'", expectedIP1, ip3.String())
	}
}

// TestCreateNetwork 测试创建容器网络
func TestCreateNetwork(t *testing.T) {
	mgr, err := network.NewNetworkManager("", "")
	if err != nil {
		t.Fatalf("Failed to create network manager: %v", err)
	}

	// 创建容器网络
	netConfig, err := mgr.CreateNetwork("test-container-123")
	if err != nil {
		t.Fatalf("Failed to create network: %v", err)
	}

	// 验证网络配置
	if netConfig.ContainerID != "test-container-123" {
		t.Errorf("Expected container ID 'test-container-123', got '%s'", netConfig.ContainerID)
	}

	if netConfig.IP == nil {
		t.Error("IP should not be nil")
	}

	if netConfig.MAC == "" {
		t.Error("MAC should not be empty")
	}

	if netConfig.VethHost == "" {
		t.Error("VethHost should not be empty")
	}

	if netConfig.VethCont == "" {
		t.Error("VethCont should not be empty")
	}

	// 获取网络配置
	getNet, err := mgr.GetNetwork("test-container-123")
	if err != nil {
		t.Fatalf("Failed to get network: %v", err)
	}

	if getNet.ContainerID != netConfig.ContainerID {
		t.Errorf("Expected container ID '%s', got '%s'", netConfig.ContainerID, getNet.ContainerID)
	}
}

// TestListNetworks 测试列出网络
func TestListNetworks(t *testing.T) {
	mgr, err := network.NewNetworkManager("", "")
	if err != nil {
		t.Fatalf("Failed to create network manager: %v", err)
	}

	// 创建多个容器网络
	mgr.CreateNetwork("container-1")
	mgr.CreateNetwork("container-2")
	mgr.CreateNetwork("container-3")

	// 列出网络
	networks := mgr.ListNetworks()
	if len(networks) != 3 {
		t.Errorf("Expected 3 networks, got %d", len(networks))
	}
}

// TestDeleteNetwork 测试删除网络
func TestDeleteNetwork(t *testing.T) {
	mgr, err := network.NewNetworkManager("", "")
	if err != nil {
		t.Fatalf("Failed to create network manager: %v", err)
	}

	// 创建网络
	mgr.CreateNetwork("container-1")

	// 删除网络
	if err := mgr.DeleteNetwork("container-1"); err != nil {
		t.Fatalf("Failed to delete network: %v", err)
	}

	// 验证网络已删除
	_, err = mgr.GetNetwork("container-1")
	if err == nil {
		t.Error("Expected error when getting deleted network")
	}
}

// TestGetNetworkNotFound 测试获取不存在的网络
func TestGetNetworkNotFound(t *testing.T) {
	mgr, err := network.NewNetworkManager("", "")
	if err != nil {
		t.Fatalf("Failed to create network manager: %v", err)
	}

	_, err = mgr.GetNetwork("nonexistent")
	if err == nil {
		t.Error("Expected error when getting nonexistent network")
	}
}

// TestMultipleIPAllocation 测试多次 IP 分配
func TestMultipleIPAllocation(t *testing.T) {
	_, ipNet, _ := net.ParseCIDR("10.0.0.0/24")
	pool := network.NewIPPool(ipNet)

	// 分配多个 IP
	allocated := make(map[string]bool)
	for i := 0; i < 10; i++ {
		ip, err := pool.Allocate()
		if err != nil {
			t.Fatalf("Failed to allocate IP %d: %v", i, err)
		}

		ipStr := ip.String()
		if allocated[ipStr] {
			t.Errorf("IP %s already allocated", ipStr)
		}
		allocated[ipStr] = true
	}

	// 验证分配了 10 个不同的 IP
	if len(allocated) != 10 {
		t.Errorf("Expected 10 unique IPs, got %d", len(allocated))
	}
}

// TestNetworkConfig 测试网络配置结构
func TestNetworkConfig(t *testing.T) {
	netConfig := &network.ContainerNetwork{
		ContainerID: "test-container",
		IP:          net.ParseIP("172.17.0.2"),
		MAC:         "02:42:ac:11:00:02",
		VethHost:    "veth-test-cont",
		VethCont:    "eth0",
	}

	if netConfig.ContainerID != "test-container" {
		t.Errorf("Expected container ID 'test-container', got '%s'", netConfig.ContainerID)
	}

	if netConfig.IP.String() != "172.17.0.2" {
		t.Errorf("Expected IP '172.17.0.2', got '%s'", netConfig.IP.String())
	}

	if netConfig.VethCont != "eth0" {
		t.Errorf("Expected VethCont 'eth0', got '%s'", netConfig.VethCont)
	}
}
