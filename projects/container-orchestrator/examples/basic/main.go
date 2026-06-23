package main

import (
	"fmt"
	"time"

	"github.com/container-orchestrator/pkg/container"
	"github.com/container-orchestrator/pkg/manager"
)

func main() {
	fmt.Println("=== Container Orchestrator Basic Example ===")

	// 创建管理器
	mgr := manager.NewManager()
	mgr.Start()
	defer mgr.Stop()

	// 添加节点
	fmt.Println("\n1. Adding nodes...")
	node1 := mgr.AddNode("node-1", "192.168.1.1", container.Resources{
		CPU:    4.0,
		Memory: 8 * 1024 * 1024 * 1024,
		Disk:   100 * 1024 * 1024 * 1024,
	})
	fmt.Printf("   Added node: %s (%s)\n", node1.Name, node1.Address)

	node2 := mgr.AddNode("node-2", "192.168.1.2", container.Resources{
		CPU:    8.0,
		Memory: 16 * 1024 * 1024 * 1024,
		Disk:   200 * 1024 * 1024 * 1024,
	})
	fmt.Printf("   Added node: %s (%s)\n", node2.Name, node2.Address)

	// 创建服务
	fmt.Println("\n2. Creating service...")
	template := container.ContainerTemplate{
		Image: "nginx:latest",
		Resources: container.Resources{
			CPU:    0.5,
			Memory: 512 * 1024 * 1024,
			Disk:   5 * 1024 * 1024 * 1024,
		},
	}

	service, err := mgr.CreateService("web-service", 3, template)
	if err != nil {
		fmt.Printf("   Error creating service: %v\n", err)
		return
	}
	fmt.Printf("   Created service: %s (replicas: %d)\n", service.Name, service.Replicas)

	// 等待容器创建
	time.Sleep(100 * time.Millisecond)

	// 获取集群统计
	fmt.Println("\n3. Cluster statistics:")
	stats := mgr.GetClusterStats()
	fmt.Printf("   Total nodes: %d\n", stats.TotalNodes)
	fmt.Printf("   Ready nodes: %d\n", stats.ReadyNodes)
	fmt.Printf("   Total containers: %d\n", stats.TotalContainers)
	fmt.Printf("   Running containers: %d\n", stats.RunningContainers)

	// 扩缩容
	fmt.Println("\n4. Scaling service...")
	err = mgr.ScaleService(service.ID, 5)
	if err != nil {
		fmt.Printf("   Error scaling service: %v\n", err)
		return
	}
	fmt.Printf("   Scaled service to 5 replicas\n")

	// 等待扩缩容完成
	time.Sleep(100 * time.Millisecond)

	// 再次获取统计
	fmt.Println("\n5. Updated statistics:")
	stats = mgr.GetClusterStats()
	fmt.Printf("   Total containers: %d\n", stats.TotalContainers)
	fmt.Printf("   Running containers: %d\n", stats.RunningContainers)

	// 服务发现
	fmt.Println("\n6. Service discovery:")
	endpoint, err := mgr.ResolveService("web-service")
	if err != nil {
		fmt.Printf("   Error resolving service: %v\n", err)
		return
	}
	fmt.Printf("   Resolved endpoint: %s:%d\n", endpoint.Address, endpoint.Port)

	// 健康检查
	fmt.Println("\n7. Health status:")
	healthSummary := mgr.GetHealthSummary()
	fmt.Printf("   Total containers: %d\n", healthSummary.Total)
	fmt.Printf("   Healthy: %d\n", healthSummary.Healthy)
	fmt.Printf("   Unhealthy: %d\n", healthSummary.Unhealthy)
	fmt.Printf("   Unknown: %d\n", healthSummary.Unknown)

	fmt.Println("\n=== Example completed successfully! ===")
}
