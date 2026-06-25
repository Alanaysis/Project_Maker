package main

import (
	"fmt"
	"time"

	"github.com/container-orchestrator/pkg/container"
	"github.com/container-orchestrator/pkg/manager"
)

func main() {
	fmt.Println("=== Microservice Deployment Example ===")
	fmt.Println("Deploying a microservice architecture with multiple services")

	// Create manager
	mgr := manager.NewManager()
	mgr.Start()
	defer mgr.Stop()

	// Step 1: Set up cluster nodes
	fmt.Println("\n1. Setting up cluster nodes...")
	nodes := setupCluster(mgr)

	// Step 2: Deploy API Gateway
	fmt.Println("\n2. Deploying API Gateway...")
	apiGateway := deployService(mgr, "api-gateway", "nginx:latest", 2, container.Resources{
		CPU:    0.5,
		Memory: 256 * 1024 * 1024,
		Disk:   1 * 1024 * 1024 * 1024,
	}, map[string]string{"tier": "frontend", "app": "api-gateway"})

	// Step 3: Deploy User Service
	fmt.Println("\n3. Deploying User Service...")
	userService := deployService(mgr, "user-service", "user-app:latest", 3, container.Resources{
		CPU:    1.0,
		Memory: 512 * 1024 * 1024,
		Disk:   2 * 1024 * 1024 * 1024,
	}, map[string]string{"tier": "backend", "app": "user-service"})

	// Step 4: Deploy Order Service
	fmt.Println("\n4. Deploying Order Service...")
	orderService := deployService(mgr, "order-service", "order-app:latest", 3, container.Resources{
		CPU:    1.0,
		Memory: 512 * 1024 * 1024,
		Disk:   2 * 1024 * 1024 * 1024,
	}, map[string]string{"tier": "backend", "app": "order-service"})

	// Step 5: Deploy Payment Service
	fmt.Println("\n5. Deploying Payment Service...")
	paymentService := deployService(mgr, "payment-service", "payment-app:latest", 2, container.Resources{
		CPU:    0.5,
		Memory: 256 * 1024 * 1024,
		Disk:   1 * 1024 * 1024 * 1024,
	}, map[string]string{"tier": "backend", "app": "payment-service", "security": "high"})

	// Step 6: Deploy Database
	fmt.Println("\n6. Deploying Database...")
	dbService := deployService(mgr, "database", "postgres:14", 1, container.Resources{
		CPU:    2.0,
		Memory: 2 * 1024 * 1024 * 1024,
		Disk:   50 * 1024 * 1024 * 1024,
	}, map[string]string{"tier": "data", "app": "database"})

	// Wait for containers to be created
	time.Sleep(200 * time.Millisecond)

	// Step 7: Show cluster status
	fmt.Println("\n7. Cluster Status:")
	showClusterStatus(mgr, nodes)

	// Step 8: Show service discovery
	fmt.Println("\n8. Service Discovery:")
	resolveService(mgr, "api-gateway")
	resolveService(mgr, "user-service")
	resolveService(mgr, "order-service")

	// Step 9: Simulate scaling
	fmt.Println("\n9. Scaling User Service (high traffic)...")
	scaleService(mgr, userService, 5)

	// Step 10: Show health status
	fmt.Println("\n10. Health Status:")
	showHealthStatus(mgr)

	// Step 11: Show all deployed services
	fmt.Println("\n11. Deployed Services:")
	showServices(mgr, []*container.Service{
		apiGateway, userService, orderService, paymentService, dbService,
	})

	fmt.Println("\n=== Microservice Deployment Example Completed! ===")
}

func setupCluster(mgr *manager.Manager) []*container.Node {
	nodes := []*container.Node{}

	// Frontend nodes
	node1 := mgr.AddNode("frontend-node-1", "10.0.1.1", container.Resources{
		CPU:    4.0,
		Memory: 8 * 1024 * 1024 * 1024,
		Disk:   100 * 1024 * 1024 * 1024,
	})
	node1.Labels = map[string]string{"tier": "frontend", "zone": "us-east-1a"}
	nodes = append(nodes, node1)
	fmt.Printf("   Added: %s (%s) - Frontend\n", node1.Name, node1.Address)

	// Backend nodes
	node2 := mgr.AddNode("backend-node-1", "10.0.2.1", container.Resources{
		CPU:    8.0,
		Memory: 16 * 1024 * 1024 * 1024,
		Disk:   200 * 1024 * 1024 * 1024,
	})
	node2.Labels = map[string]string{"tier": "backend", "zone": "us-east-1b"}
	nodes = append(nodes, node2)
	fmt.Printf("   Added: %s (%s) - Backend\n", node2.Name, node2.Address)

	node3 := mgr.AddNode("backend-node-2", "10.0.2.2", container.Resources{
		CPU:    8.0,
		Memory: 16 * 1024 * 1024 * 1024,
		Disk:   200 * 1024 * 1024 * 1024,
	})
	node3.Labels = map[string]string{"tier": "backend", "zone": "us-east-1c"}
	nodes = append(nodes, node3)
	fmt.Printf("   Added: %s (%s) - Backend\n", node3.Name, node3.Address)

	// Data node
	node4 := mgr.AddNode("data-node-1", "10.0.3.1", container.Resources{
		CPU:    16.0,
		Memory: 64 * 1024 * 1024 * 1024,
		Disk:   1000 * 1024 * 1024 * 1024,
	})
	node4.Labels = map[string]string{"tier": "data", "zone": "us-east-1a"}
	nodes = append(nodes, node4)
	fmt.Printf("   Added: %s (%s) - Data\n", node4.Name, node4.Address)

	return nodes
}

func deployService(mgr *manager.Manager, name, image string, replicas int, resources container.Resources, labels map[string]string) *container.Service {
	template := container.ContainerTemplate{
		Image:     image,
		Labels:    labels,
		Resources: resources,
		HealthCheck: &container.HealthCheck{
			Interval:    10 * time.Second,
			Timeout:     5 * time.Second,
			Retries:     3,
			StartPeriod: 30 * time.Second,
		},
	}

	service, err := mgr.CreateService(name, replicas, template)
	if err != nil {
		fmt.Printf("   Error deploying %s: %v\n", name, err)
		return nil
	}
	fmt.Printf("   Deployed: %s (replicas: %d, image: %s)\n", name, replicas, image)
	return service
}

func showClusterStatus(mgr *manager.Manager, nodes []*container.Node) {
	stats := mgr.GetClusterStats()
	fmt.Printf("   Total Nodes: %d\n", stats.TotalNodes)
	fmt.Printf("   Ready Nodes: %d\n", stats.ReadyNodes)
	fmt.Printf("   Total Containers: %d\n", stats.TotalContainers)
	fmt.Printf("   Running Containers: %d\n", stats.RunningContainers)
	fmt.Printf("   Total CPU: %.1f cores\n", stats.TotalCPU)
	fmt.Printf("   Used CPU: %.1f cores\n", stats.UsedCPU)
	fmt.Printf("   CPU Utilization: %.1f%%\n", (stats.UsedCPU/stats.TotalCPU)*100)
}

func resolveService(mgr *manager.Manager, name string) {
	endpoint, err := mgr.ResolveService(name)
	if err != nil {
		fmt.Printf("   %s: %v\n", name, err)
		return
	}
	fmt.Printf("   %s -> %s:%d\n", name, endpoint.Address, endpoint.Port)
}

func scaleService(mgr *manager.Manager, service *container.Service, replicas int) {
	if service == nil {
		return
	}
	err := mgr.ScaleService(service.ID, replicas)
	if err != nil {
		fmt.Printf("   Error scaling: %v\n", err)
		return
	}
	fmt.Printf("   Scaled to %d replicas\n", replicas)

	// Also demonstrate custom metrics scaling
	fmt.Println("   Setting up auto-scaling with custom metrics...")
	// In a real system, you would update metrics like:
	// scaler.UpdateMetrics(serviceID, &scaler.ServiceMetrics{
	//     CPUUsage: 0.9,
	//     CustomMetrics: map[string]float64{
	//         "requests_per_second": 1000,
	//         "queue_length": 500,
	//     },
	// })
}

func showHealthStatus(mgr *manager.Manager) {
	summary := mgr.GetHealthSummary()
	fmt.Printf("   Total Containers: %d\n", summary.Total)
	fmt.Printf("   Healthy: %d\n", summary.Healthy)
	fmt.Printf("   Unhealthy: %d\n", summary.Unhealthy)
	fmt.Printf("   Unknown: %d\n", summary.Unknown)
	fmt.Printf("   Starting: %d\n", summary.Starting)
}

func showServices(mgr *manager.Manager, services []*container.Service) {
	for _, svc := range services {
		if svc == nil {
			continue
		}
		fmt.Printf("   - %s (ID: %s, Replicas: %d)\n", svc.Name, svc.ID[:8], svc.Replicas)
	}
}
