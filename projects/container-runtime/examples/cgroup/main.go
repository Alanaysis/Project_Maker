// Cgroups 示例：资源限制演示
//
// 这个示例展示如何使用 Cgroups 限制容器资源
package main

import (
	"fmt"
	"os"

	"github.com/minicontainer/runtime/pkg/container"
)

func main() {
	fmt.Println("=== Cgroups 资源限制示例 ===")

	// 检查 cgroups 支持
	fmt.Println("\n1. 检查 cgroups 支持...")
	if container.IsCgroupSupported() {
		fmt.Println("   ✓ cgroups v2 可用")

		// 获取可用控制器
		controllers, err := container.GetAvailableControllers()
		if err != nil {
			fmt.Printf("   ✗ 获取控制器失败: %v\n", err)
		} else {
			fmt.Printf("   可用控制器: %v\n", controllers)
		}
	} else {
		fmt.Println("   ✗ cgroups v2 不可用")
		os.Exit(1)
	}

	// 创建 cgroup 管理器
	fmt.Println("\n2. 创建 cgroup 管理器...")
	containerID := "example-cgroup"
	mgr := container.NewCgroupManager(containerID)
	fmt.Printf("   cgroup 路径: %s\n", mgr.Path)

	// 设置内存限制
	fmt.Println("\n3. 设置内存限制...")
	memLimit := int64(256 * 1024 * 1024) // 256MB
	fmt.Printf("   内存限制: %d bytes (256MB)\n", memLimit)
	// 注意：实际设置需要 root 权限
	// if err := mgr.SetMemoryLimit(memLimit); err != nil {
	//     fmt.Printf("   ✗ 设置失败: %v\n", err)
	// } else {
	//     fmt.Println("   ✓ 设置成功")
	// }

	// 设置 CPU 限制
	fmt.Println("\n4. 设置 CPU 限制...")
	cpuPercent := 50
	fmt.Printf("   CPU 限制: %d%%\n", cpuPercent)
	// 注意：实际设置需要 root 权限
	// if err := mgr.SetCPULimit(cpuPercent); err != nil {
	//     fmt.Printf("   ✗ 设置失败: %v\n", err)
	// } else {
	//     fmt.Println("   ✓ 设置成功")
	// }

	// 设置进程数限制
	fmt.Println("\n5. 设置进程数限制...")
	pidsLimit := 100
	fmt.Printf("   进程数限制: %d\n", pidsLimit)
	// 注意：实际设置需要 root 权限
	// if err := mgr.SetPidsLimit(pidsLimit); err != nil {
	//     fmt.Printf("   ✗ 设置失败: %v\n", err)
	// } else {
	//     fmt.Println("   ✓ 设置成功")
	// }

	// 展示资源配置
	fmt.Println("\n6. 资源配置汇总...")
	fmt.Printf("   容器 ID: %s\n", containerID)
	fmt.Printf("   内存限制: %d MB\n", memLimit/(1024*1024))
	fmt.Printf("   CPU 限制: %d%%\n", cpuPercent)
	fmt.Printf("   进程数限制: %d\n", pidsLimit)

	// 展示 cgroup 目录结构
	fmt.Println("\n7. Cgroup 目录结构...")
	fmt.Printf("   /sys/fs/cgroup/\n")
	fmt.Printf("   └── minicontainer/\n")
	fmt.Printf("       └── %s/\n", containerID)
	fmt.Printf("           ├── cpu.max\n")
	fmt.Printf("           ├── cpu.weight\n")
	fmt.Printf("           ├── memory.max\n")
	fmt.Printf("           ├── memory.high\n")
	fmt.Printf("           ├── pids.max\n")
	fmt.Printf("           └── cgroup.procs\n")

	fmt.Println("\n=== 示例完成 ===")
	fmt.Println("\n注意: 实际设置 cgroup 需要 root 权限")
	fmt.Println("运行: sudo go run examples/cgroup/main.go")
}
