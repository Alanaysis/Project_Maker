package tests

import (
	"testing"
	"time"

	"github.com/container-orchestrator/pkg/container"
	"github.com/container-orchestrator/pkg/manager"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

func TestNewManager(t *testing.T) {
	mgr := manager.NewManager()
	assert.NotNil(t, mgr)
}

func TestAddRemoveNode(t *testing.T) {
	mgr := manager.NewManager()

	// Add node
	node := mgr.AddNode("node-1", "192.168.1.1", container.Resources{
		CPU:    4.0,
		Memory: 8 * 1024 * 1024 * 1024,
		Disk:   100 * 1024 * 1024 * 1024,
	})

	assert.NotEmpty(t, node.ID)
	assert.Equal(t, "node-1", node.Name)
	assert.Equal(t, "192.168.1.1", node.Address)

	// Get node
	got, err := mgr.GetNode(node.ID)
	assert.NoError(t, err)
	assert.Equal(t, node, got)

	// Get all nodes
	nodes := mgr.GetNodes()
	assert.Len(t, nodes, 1)

	// Remove node
	err = mgr.RemoveNode(node.ID)
	assert.NoError(t, err)

	// Node should be removed
	nodes = mgr.GetNodes()
	assert.Len(t, nodes, 0)
}

func TestCreateDeleteService(t *testing.T) {
	mgr := manager.NewManager()

	// Add node
	mgr.AddNode("node-1", "192.168.1.1", container.Resources{
		CPU:    4.0,
		Memory: 8 * 1024 * 1024 * 1024,
		Disk:   100 * 1024 * 1024 * 1024,
	})

	// Create service
	template := container.ContainerTemplate{
		Image: "nginx:latest",
		Resources: container.Resources{
			CPU:    0.5,
			Memory: 512 * 1024 * 1024,
			Disk:   5 * 1024 * 1024 * 1024,
		},
	}

	service, err := mgr.CreateService("web-service", 3, template)
	assert.NoError(t, err)
	assert.NotNil(t, service)
	assert.Equal(t, "web-service", service.Name)
	assert.Equal(t, 3, service.Replicas)

	// Get service
	got, err := mgr.GetService(service.ID)
	assert.NoError(t, err)
	assert.Equal(t, service, got)

	// Get all services
	services := mgr.GetServices()
	assert.Len(t, services, 1)

	// Delete service
	err = mgr.DeleteService(service.ID)
	assert.NoError(t, err)

	// Service should be deleted
	services = mgr.GetServices()
	assert.Len(t, services, 0)
}

func TestScaleService(t *testing.T) {
	mgr := manager.NewManager()

	// Add node
	mgr.AddNode("node-1", "192.168.1.1", container.Resources{
		CPU:    8.0,
		Memory: 16 * 1024 * 1024 * 1024,
		Disk:   200 * 1024 * 1024 * 1024,
	})

	// Create service
	template := container.ContainerTemplate{
		Image: "nginx:latest",
		Resources: container.Resources{
			CPU:    0.5,
			Memory: 512 * 1024 * 1024,
			Disk:   5 * 1024 * 1024 * 1024,
		},
	}

	service, err := mgr.CreateService("web-service", 2, template)
	assert.NoError(t, err)

	// Scale up
	err = mgr.ScaleService(service.ID, 5)
	assert.NoError(t, err)

	// Wait for scaling
	time.Sleep(100 * time.Millisecond)

	// Scale down
	err = mgr.ScaleService(service.ID, 1)
	assert.NoError(t, err)
}

func TestResolveService(t *testing.T) {
	mgr := manager.NewManager()

	// Add node
	mgr.AddNode("node-1", "192.168.1.1", container.Resources{
		CPU:    4.0,
		Memory: 8 * 1024 * 1024 * 1024,
		Disk:   100 * 1024 * 1024 * 1024,
	})

	// Create service
	template := container.ContainerTemplate{
		Image: "nginx:latest",
		Resources: container.Resources{
			CPU:    0.5,
			Memory: 512 * 1024 * 1024,
			Disk:   5 * 1024 * 1024 * 1024,
		},
	}

	_, err := mgr.CreateService("web-service", 2, template)
	assert.NoError(t, err)

	// Wait for containers to be created
	time.Sleep(100 * time.Millisecond)

	// Resolve service
	endpoint, err := mgr.ResolveService("web-service")
	assert.NoError(t, err)
	assert.NotNil(t, endpoint)
	assert.NotEmpty(t, endpoint.Address)
}

func TestGetClusterStats(t *testing.T) {
	mgr := manager.NewManager()

	// Add nodes
	mgr.AddNode("node-1", "192.168.1.1", container.Resources{
		CPU:    4.0,
		Memory: 8 * 1024 * 1024 * 1024,
		Disk:   100 * 1024 * 1024 * 1024,
	})

	mgr.AddNode("node-2", "192.168.1.2", container.Resources{
		CPU:    8.0,
		Memory: 16 * 1024 * 1024 * 1024,
		Disk:   200 * 1024 * 1024 * 1024,
	})

	// Get stats
	stats := mgr.GetClusterStats()
	assert.Equal(t, 2, stats.TotalNodes)
	assert.Equal(t, 2, stats.ReadyNodes)
	assert.Equal(t, 12.0, stats.TotalCPU)
}

func TestGetHealthSummary(t *testing.T) {
	mgr := manager.NewManager()

	// Add node
	mgr.AddNode("node-1", "192.168.1.1", container.Resources{
		CPU:    4.0,
		Memory: 8 * 1024 * 1024 * 1024,
		Disk:   100 * 1024 * 1024 * 1024,
	})

	// Create service
	template := container.ContainerTemplate{
		Image: "nginx:latest",
		Resources: container.Resources{
			CPU:    0.5,
			Memory: 512 * 1024 * 1024,
			Disk:   5 * 1024 * 1024 * 1024,
		},
	}

	_, err := mgr.CreateService("web-service", 2, template)
	assert.NoError(t, err)

	// Wait for containers
	time.Sleep(100 * time.Millisecond)

	// Get health summary
	summary := mgr.GetHealthSummary()
	assert.Equal(t, 2, summary.Total)
}

func TestStartStop(t *testing.T) {
	mgr := manager.NewManager()

	// Start
	mgr.Start()

	// Add node
	mgr.AddNode("node-1", "192.168.1.1", container.Resources{
		CPU:    4.0,
		Memory: 8 * 1024 * 1024 * 1024,
		Disk:   100 * 1024 * 1024 * 1024,
	})

	// Create service
	template := container.ContainerTemplate{
		Image: "nginx:latest",
		Resources: container.Resources{
			CPU:    0.5,
			Memory: 512 * 1024 * 1024,
			Disk:   5 * 1024 * 1024 * 1024,
		},
	}

	_, err := mgr.CreateService("web-service", 2, template)
	assert.NoError(t, err)

	// Wait a bit
	time.Sleep(100 * time.Millisecond)

	// Stop
	mgr.Stop()
}
