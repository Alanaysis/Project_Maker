// 网络示例：容器网络配置演示
//
// 这个示例展示容器网络的工作原理
package main

import (
	"fmt"
	"net"
)

func main() {
	fmt.Println("=== 容器网络示例 ===")

	// 1. IP 地址池演示
	fmt.Println("\n1. IP 地址池演示")
	subnet := "172.17.0.0/16"
	_, ipNet, _ := net.ParseCIDR(subnet)
	fmt.Printf("   子网: %s\n", subnet)
	fmt.Printf("   网络地址: %s\n", ipNet.IP.String())
	fmt.Printf("   掩码: %s\n", ipNet.Mask.String())

	// 计算可用 IP 数量
	maskBits, _ := ipNet.Mask.Size()
	availableIPs := 1 << (32 - maskBits)
	fmt.Printf("   可用 IP 数量: %d\n", availableIPs)

	// 2. 网关地址
	fmt.Println("\n2. 网关地址")
	gateway := make(net.IP, len(ipNet.IP))
	copy(gateway, ipNet.IP)
	gateway[len(gateway)-1]++
	fmt.Printf("   网关: %s\n", gateway.String())

	// 3. 容器 IP 分配
	fmt.Println("\n3. 容器 IP 分配")
	containerIPs := []net.IP{}
	for i := 2; i <= 5; i++ {
		ip := make(net.IP, len(ipNet.IP))
		copy(ip, ipNet.IP)
		ip[len(ip)-1] = byte(i)
		containerIPs = append(containerIPs, ip)
		fmt.Printf("   容器 %d: %s\n", i-1, ip.String())
	}

	// 4. MAC 地址生成
	fmt.Println("\n4. MAC 地址生成")
	for _, ip := range containerIPs {
		ipBytes := ip.To4()
		mac := net.HardwareAddr{0x02, 0x42, ipBytes[0], ipBytes[1], ipBytes[2], ipBytes[3]}
		fmt.Printf("   IP: %s -> MAC: %s\n", ip.String(), mac.String())
	}

	// 5. 网络架构图
	fmt.Println("\n5. 网络架构图")
	fmt.Println("   ┌─────────────────────────────────────────────────────────┐")
	fmt.Println("   │                    Host Network                         │")
	fmt.Println("   │  ┌───────────────────────────────────────────────────┐  │")
	fmt.Println("   │  │                  Linux Bridge (br0)               │  │")
	fmt.Println("   │  │         172.17.0.1/16                            │  │")
	fmt.Println("   │  └─────────┬─────────────────┬─────────────────────┘  │")
	fmt.Println("   │            │                 │                          │")
	fmt.Println("   │  ┌─────────┴─────┐ ┌────────┴──────┐                  │")
	fmt.Println("   │  │  veth-host    │ │  veth-host    │                  │")
	fmt.Println("   │  └───────────────┘ └───────────────┘                  │")
	fmt.Println("   │            │                 │                          │")
	fmt.Println("   │  ┌─────────┴─────┐ ┌────────┴──────┐                  │")
	fmt.Println("   │  │  veth-cont    │ │  veth-cont    │                  │")
	fmt.Println("   │  │  172.17.0.2   │ │  172.17.0.3   │                  │")
	fmt.Println("   │  └───────────────┘ └───────────────┘                  │")
	fmt.Println("   │      Container 1       Container 2                    │")
	fmt.Println("   └─────────────────────────────────────────────────────────┘")

	// 6. 网络配置命令
	fmt.Println("\n6. 网络配置命令")
	fmt.Println("   # 创建网桥")
	fmt.Println("   ip link add name minibr0 type bridge")
	fmt.Println("   ip addr add 172.17.0.1/16 dev minibr0")
	fmt.Println("   ip link set minibr0 up")
	fmt.Println("")
	fmt.Println("   # 创建 veth pair")
	fmt.Println("   ip link add veth-host type veth peer name veth-cont")
	fmt.Println("")
	fmt.Println("   # 将 veth 移动到容器网络命名空间")
	fmt.Println("   ip link set veth-cont netns <pid>")
	fmt.Println("")
	fmt.Println("   # 连接 veth 到网桥")
	fmt.Println("   ip link set veth-host master minibr0")
	fmt.Println("   ip link set veth-host up")
	fmt.Println("")
	fmt.Println("   # 在容器内配置网络")
	fmt.Println("   nsenter -t <pid> -n ip addr add 172.17.0.2/16 dev veth-cont")
	fmt.Println("   nsenter -t <pid> -n ip link set veth-cont up")
	fmt.Println("   nsenter -t <pid> -n ip route add default via 172.17.0.1")

	// 7. 网络调试命令
	fmt.Println("\n7. 网络调试命令")
	fmt.Println("   # 查看网桥")
	fmt.Println("   bridge link show")
	fmt.Println("")
	fmt.Println("   # 查看 veth pair")
	fmt.Println("   ip link show type veth")
	fmt.Println("")
	fmt.Println("   # 查看网络命名空间")
	fmt.Println("   ls -la /proc/<pid>/ns/net")
	fmt.Println("")
	fmt.Println("   # 进入容器网络命名空间")
	fmt.Println("   nsenter -t <pid> -n ip addr")

	fmt.Println("\n=== 示例完成 ===")
}
