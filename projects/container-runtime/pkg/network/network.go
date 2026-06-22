// Package network 实现容器网络管理
//
// ⭐ 重点：容器网络是容器技术中最复杂的部分之一
//
// 容器网络模型：
// ┌─────────────────────────────────────────────────────────┐
// │                    Host Network                         │
// │  ┌───────────────────────────────────────────────────┐  │
// │  │                  Linux Bridge (br0)               │  │
// │  │         172.17.0.1/16                            │  │
// │  └─────────┬─────────────────┬─────────────────────┘  │
// │            │                 │                          │
// │  ┌─────────┴─────┐ ┌────────┴──────┐                  │
// │  │  veth-host    │ │  veth-host    │                  │
// │  └───────────────┘ └───────────────┘                  │
// │            │                 │                          │
// │  ┌─────────┴─────┐ ┌────────┴──────┐                  │
// │  │  veth-cont    │ │  veth-cont    │                  │
// │  │  172.17.0.2   │ │  172.17.0.3   │                  │
// │  └───────────────┘ └───────────────┘                  │
// │      Container 1       Container 2                    │
// └─────────────────────────────────────────────────────────┘
//
// 💡 思考：为什么容器网络需要这些组件？
// - veth pair: 连接容器和主机的虚拟网线
// - bridge: 连接多个容器的虚拟交换机
// - namespace: 隔离容器的网络栈
package network

import (
	"encoding/json"
	"fmt"
	"net"
	"os"
	"os/exec"
	"path/filepath"
	"sync"
)

const (
	// 默认网桥名称
	DefaultBridgeName = "minibr0"
	// 默认子网
	DefaultSubnet = "172.17.0.0/16"
	// 默认网关
	DefaultGateway = "172.17.0.1"
	// 容器网络数据目录
	NetworkDataDir = "/var/lib/minicontainer/network"
)

// NetworkManager 网络管理器
type NetworkManager struct {
	// 网桥名称
	BridgeName string
	// 子网
	Subnet *net.IPNet
	// 网关 IP
	Gateway net.IP
	// IP 地址池
	IPPool *IPPool
	// 网络配置存储
	configs map[string]*ContainerNetwork
	// 互斥锁
	mu sync.RWMutex
}

// ContainerNetwork 容器网络配置
type ContainerNetwork struct {
	// 容器 ID
	ContainerID string `json:"container_id"`
	// IP 地址
	IP net.IP `json:"ip"`
	// MAC 地址
	MAC string `json:"mac"`
	// veth pair 名称
	VethHost string `json:"veth_host"`
	VethCont string `json:"veth_cont"`
	// 网络命名空间
	NetnsPath string `json:"netns_path"`
}

// IPPool IP 地址池
type IPPool struct {
	// 子网
	Subnet *net.IPNet
	// 已分配的 IP
	Allocated map[string]bool
	// 当前 IP
	Current net.IP
	// 互斥锁
	mu sync.RWMutex
}

// NewNetworkManager 创建网络管理器
func NewNetworkManager(bridgeName, subnet string) (*NetworkManager, error) {
	if bridgeName == "" {
		bridgeName = DefaultBridgeName
	}
	if subnet == "" {
		subnet = DefaultSubnet
	}

	// 解析子网
	_, ipNet, err := net.ParseCIDR(subnet)
	if err != nil {
		return nil, fmt.Errorf("invalid subnet: %w", err)
	}

	// 计算网关 IP（子网第一个可用 IP）
	gateway := make(net.IP, len(ipNet.IP))
	copy(gateway, ipNet.IP)
	gateway[len(gateway)-1]++

	mgr := &NetworkManager{
		BridgeName: bridgeName,
		Subnet:     ipNet,
		Gateway:    gateway,
		IPPool:     NewIPPool(ipNet),
		configs:    make(map[string]*ContainerNetwork),
	}

	return mgr, nil
}

// InitNetwork 初始化网络（创建网桥）
//
// ⭐ 重点：使用 ip 命令创建和配置网桥
func (m *NetworkManager) InitNetwork() error {
	// 检查网桥是否已存在
	if _, err := exec.LookPath("ip"); err != nil {
		return fmt.Errorf("ip command not found: %w", err)
	}

	// 创建网桥
	cmd := exec.Command("ip", "link", "add", "name", m.BridgeName, "type", "bridge")
	if output, err := cmd.CombinedOutput(); err != nil {
		// 网桥可能已存在，忽略错误
		fmt.Printf("Warning: failed to create bridge: %s\n", string(output))
	}

	// 设置网桥 IP 地址
	addrStr := fmt.Sprintf("%s/%d", m.Gateway.String(), maskBits(m.Subnet.Mask))
	cmd = exec.Command("ip", "addr", "add", addrStr, "dev", m.BridgeName)
	if output, err := cmd.CombinedOutput(); err != nil {
		fmt.Printf("Warning: failed to add addr: %s\n", string(output))
	}

	// 启用网桥
	cmd = exec.Command("ip", "link", "set", m.BridgeName, "up")
	if output, err := cmd.CombinedOutput(); err != nil {
		return fmt.Errorf("failed to set bridge up: %s", string(output))
	}

	// 启用 IP 转发
	if err := os.WriteFile("/proc/sys/net/ipv4/ip_forward", []byte("1"), 0644); err != nil {
		fmt.Printf("Warning: failed to enable ip forwarding: %v\n", err)
	}

	return nil
}

// NewIPPool 创建 IP 地址池
func NewIPPool(subnet *net.IPNet) *IPPool {
	return &IPPool{
		Subnet:    subnet,
		Allocated: make(map[string]bool),
		Current:   make(net.IP, len(subnet.IP)),
	}
}

// Allocate 分配 IP 地址
func (p *IPPool) Allocate() (net.IP, error) {
	p.mu.Lock()
	defer p.mu.Unlock()

	// 从子网的第 2 个 IP 开始分配（跳过网关）
	ip := make(net.IP, len(p.Subnet.IP))
	copy(ip, p.Subnet.IP)
	ip[len(ip)-1] += 2 // 从 .2 开始

	for {
		ipStr := ip.String()

		// 检查是否在子网内
		if !p.Subnet.Contains(ip) {
			return nil, fmt.Errorf("no available IPs in pool")
		}

		// 检查是否已分配
		if !p.Allocated[ipStr] {
			p.Allocated[ipStr] = true
			return ip, nil
		}

		// 递增 IP
		incrementIP(ip)
	}
}

// Release 释放 IP 地址
func (p *IPPool) Release(ip net.IP) {
	p.mu.Lock()
	defer p.mu.Unlock()

	delete(p.Allocated, ip.String())
}

// incrementIP 递增 IP 地址
func incrementIP(ip net.IP) {
	for i := len(ip) - 1; i >= 0; i-- {
		ip[i]++
		if ip[i] > 0 {
			break
		}
	}
}

// CreateNetwork 为容器创建网络
func (m *NetworkManager) CreateNetwork(containerID string) (*ContainerNetwork, error) {
	m.mu.Lock()
	defer m.mu.Unlock()

	// 分配 IP 地址
	ip, err := m.IPPool.Allocate()
	if err != nil {
		return nil, fmt.Errorf("failed to allocate IP: %w", err)
	}

	// 生成 veth pair 名称
	vethHost := fmt.Sprintf("veth-%s", containerID[:min(8, len(containerID))])
	vethCont := "eth0"

	// 生成 MAC 地址
	mac := generateMAC(ip)

	network := &ContainerNetwork{
		ContainerID: containerID,
		IP:          ip,
		MAC:         mac.String(),
		VethHost:    vethHost,
		VethCont:    vethCont,
	}

	m.configs[containerID] = network
	return network, nil
}

// SetupContainerNetwork 设置容器网络
//
// ⭐ 重点：使用 ip 命令配置容器网络
//
// 步骤：
// 1. 创建 veth pair
// 2. 将一端放入容器网络命名空间
// 3. 配置容器端 IP 和路由
// 4. 将另一端连接到网桥
func (m *NetworkManager) SetupContainerNetwork(containerID string, pid int) error {
	m.mu.RLock()
	network, exists := m.configs[containerID]
	m.mu.RUnlock()

	if !exists {
		return fmt.Errorf("network not found for container %s", containerID)
	}

	// 1. 创建 veth pair
	cmd := exec.Command("ip", "link", "add", network.VethHost, "type", "veth", "peer", "name", network.VethCont)
	if output, err := cmd.CombinedOutput(); err != nil {
		return fmt.Errorf("failed to create veth pair: %s", string(output))
	}

	// 2. 将容器端 veth 移动到容器网络命名空间
	cmd = exec.Command("ip", "link", "set", network.VethCont, "netns", fmt.Sprintf("%d", pid))
	if output, err := cmd.CombinedOutput(); err != nil {
		return fmt.Errorf("failed to move veth to namespace: %s", string(output))
	}

	// 3. 将主机端 veth 连接到网桥
	cmd = exec.Command("ip", "link", "set", network.VethHost, "master", m.BridgeName)
	if output, err := cmd.CombinedOutput(); err != nil {
		return fmt.Errorf("failed to connect veth to bridge: %s", string(output))
	}

	// 4. 启用主机端 veth
	cmd = exec.Command("ip", "link", "set", network.VethHost, "up")
	if output, err := cmd.CombinedOutput(); err != nil {
		return fmt.Errorf("failed to set host veth up: %s", string(output))
	}

	// 5. 在容器网络命名空间中配置网络
	if err := m.configureContainerNetwork(pid, network); err != nil {
		return fmt.Errorf("failed to configure container network: %w", err)
	}

	return nil
}

// configureContainerNetwork 在容器网络命名空间中配置网络
//
// ⭐ 重点：使用 nsenter 进入容器网络命名空间
func (m *NetworkManager) configureContainerNetwork(pid int, network *ContainerNetwork) error {
	addrStr := fmt.Sprintf("%s/%d", network.IP.String(), maskBits(m.Subnet.Mask))

	// 使用 nsenter 进入容器网络命名空间并配置网络
	commands := []struct {
		name string
		args []string
	}{
		// 设置容器端 IP 地址
		{"nsenter", []string{"-t", fmt.Sprintf("%d", pid), "-n", "ip", "addr", "add", addrStr, "dev", network.VethCont}},
		// 启用容器端 veth
		{"nsenter", []string{"-t", fmt.Sprintf("%d", pid), "-n", "ip", "link", "set", network.VethCont, "up"}},
		// 启用回环接口
		{"nsenter", []string{"-t", fmt.Sprintf("%d", pid), "-n", "ip", "link", "set", "lo", "up"}},
		// 添加默认路由
		{"nsenter", []string{"-t", fmt.Sprintf("%d", pid), "-n", "ip", "route", "add", "default", "via", m.Gateway.String()}},
	}

	for _, cmd := range commands {
		c := exec.Command(cmd.name, cmd.args...)
		if output, err := c.CombinedOutput(); err != nil {
			return fmt.Errorf("failed to %s: %s", cmd.name, string(output))
		}
	}

	return nil
}

// DeleteNetwork 删除容器网络
func (m *NetworkManager) DeleteNetwork(containerID string) error {
	m.mu.Lock()
	defer m.mu.Unlock()

	network, exists := m.configs[containerID]
	if !exists {
		return nil
	}

	// 删除 veth pair
	cmd := exec.Command("ip", "link", "delete", network.VethHost)
	cmd.CombinedOutput() // 忽略错误

	// 释放 IP 地址
	m.IPPool.Release(network.IP)

	delete(m.configs, containerID)
	return nil
}

// GetNetwork 获取容器网络配置
func (m *NetworkManager) GetNetwork(containerID string) (*ContainerNetwork, error) {
	m.mu.RLock()
	defer m.mu.RUnlock()

	network, exists := m.configs[containerID]
	if !exists {
		return nil, fmt.Errorf("network not found for container %s", containerID)
	}

	return network, nil
}

// ListNetworks 列出所有网络配置
func (m *NetworkManager) ListNetworks() []*ContainerNetwork {
	m.mu.RLock()
	defer m.mu.RUnlock()

	networks := make([]*ContainerNetwork, 0, len(m.configs))
	for _, n := range m.configs {
		networks = append(networks, n)
	}

	return networks
}

// generateMAC 根据 IP 生成 MAC 地址
func generateMAC(ip net.IP) net.HardwareAddr {
	// 使用 IP 地址的最后 4 字节生成 MAC
	ipBytes := ip.To4()
	if ipBytes == nil {
		return nil
	}

	mac := net.HardwareAddr{0x02, 0x42, ipBytes[0], ipBytes[1], ipBytes[2], ipBytes[3]}
	return mac
}

// SaveConfigs 保存网络配置到文件
func (m *NetworkManager) SaveConfigs() error {
	m.mu.RLock()
	defer m.mu.RUnlock()

	// 确保目录存在
	if err := os.MkdirAll(NetworkDataDir, 0755); err != nil {
		return fmt.Errorf("failed to create data dir: %w", err)
	}

	// 保存每个容器的网络配置
	for id, network := range m.configs {
		configPath := filepath.Join(NetworkDataDir, id+".json")
		data, err := json.MarshalIndent(network, "", "  ")
		if err != nil {
			return fmt.Errorf("failed to marshal config: %w", err)
		}
		if err := os.WriteFile(configPath, data, 0644); err != nil {
			return fmt.Errorf("failed to save config for %s: %w", id, err)
		}
	}

	return nil
}

// LoadConfigs 从文件加载网络配置
func (m *NetworkManager) LoadConfigs() error {
	// 确保目录存在
	if err := os.MkdirAll(NetworkDataDir, 0755); err != nil {
		return fmt.Errorf("failed to create data dir: %w", err)
	}

	// 读取所有配置文件
	files, err := filepath.Glob(filepath.Join(NetworkDataDir, "*.json"))
	if err != nil {
		return fmt.Errorf("failed to list configs: %w", err)
	}

	for _, file := range files {
		data, err := os.ReadFile(file)
		if err != nil {
			fmt.Printf("Warning: failed to read config %s: %v\n", file, err)
			continue
		}

		var network ContainerNetwork
		if err := json.Unmarshal(data, &network); err != nil {
			fmt.Printf("Warning: failed to parse config %s: %v\n", file, err)
			continue
		}

		m.configs[network.ContainerID] = &network
	}

	return nil
}

// maskBits 计算掩码位数
func maskBits(mask net.IPMask) int {
	bits := 0
	for _, b := range mask {
		for b > 0 {
			bits++
			b &= b - 1
		}
	}
	return bits
}

// min 返回两个整数中较小的一个
func min(a, b int) int {
	if a < b {
		return a
	}
	return b
}
