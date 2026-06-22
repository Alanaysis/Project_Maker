// 基础示例：创建和运行容器
//
// 这个示例展示如何使用 MiniContainer 创建和运行一个简单的容器
package main

import (
	"fmt"
	"os"

	"github.com/minicontainer/runtime/pkg/container"
)

func main() {
	fmt.Println("=== MiniContainer 基础示例 ===")

	// 1. 创建容器管理器
	fmt.Println("\n1. 创建容器管理器...")
	manager, err := container.NewContainerManager("/tmp/minicontainer-example")
	if err != nil {
		fmt.Fprintf(os.Stderr, "创建管理器失败: %v\n", err)
		os.Exit(1)
	}
	fmt.Println("   容器管理器创建成功")

	// 2. 创建容器配置
	fmt.Println("\n2. 创建容器配置...")
	config := &container.ContainerConfig{
		Name:    "example-container",
		Image:   "alpine",
		Command: []string{"/bin/sh", "-c", "echo Hello from container!"},
		Hostname: "example",
		Namespaces: []string{"pid", "mount", "uts", "ipc"},
		Resources: &container.ResourceLimit{
			MemoryLimit: 256 * 1024 * 1024, // 256MB
			CPUPercent:  50,
			PidsLimit:   100,
		},
	}
	fmt.Printf("   容器名称: %s\n", config.Name)
	fmt.Printf("   镜像: %s\n", config.Image)
	fmt.Printf("   命令: %v\n", config.Command)

	// 3. 创建容器
	fmt.Println("\n3. 创建容器...")
	cont, err := manager.Create(config)
	if err != nil {
		fmt.Fprintf(os.Stderr, "创建容器失败: %v\n", err)
		os.Exit(1)
	}
	fmt.Printf("   容器创建成功: %s\n", cont.Config.ID)
	fmt.Printf("   容器状态: %s\n", cont.Status.String())

	// 4. 列出容器
	fmt.Println("\n4. 列出所有容器...")
	containers := manager.List()
	fmt.Printf("   容器数量: %d\n", len(containers))
	for _, c := range containers {
		fmt.Printf("   - %s (%s): %s\n", c.Config.Name, c.Config.ID[:8], c.Status.String())
	}

	// 5. 获取容器信息
	fmt.Println("\n5. 获取容器信息...")
	getCont, err := manager.Get(cont.Config.ID)
	if err != nil {
		fmt.Fprintf(os.Stderr, "获取容器失败: %v\n", err)
		os.Exit(1)
	}
	fmt.Printf("   容器 ID: %s\n", getCont.Config.ID)
	fmt.Printf("   容器名称: %s\n", getCont.Config.Name)
	fmt.Printf("   创建时间: %s\n", getCont.CreatedAt.Format("2006-01-02 15:04:05"))

	// 6. 删除容器
	fmt.Println("\n6. 删除容器...")
	if err := manager.Delete(cont.Config.ID); err != nil {
		fmt.Fprintf(os.Stderr, "删除容器失败: %v\n", err)
		os.Exit(1)
	}
	fmt.Println("   容器删除成功")

	// 7. 验证删除
	fmt.Println("\n7. 验证容器已删除...")
	containers = manager.List()
	fmt.Printf("   容器数量: %d\n", len(containers))

	fmt.Println("\n=== 示例完成 ===")
}
