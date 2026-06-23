package tests

import (
	"testing"
	"time"

	"github.com/container-orchestrator/pkg/container"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

func TestNewContainer(t *testing.T) {
	resources := container.Resources{
		CPU:    1.0,
		Memory: 1024 * 1024 * 1024, // 1GB
		Disk:   10 * 1024 * 1024 * 1024, // 10GB
	}

	c := container.NewContainer("test-container", "nginx:latest", resources)

	assert.NotEmpty(t, c.ID)
	assert.Equal(t, "test-container", c.Name)
	assert.Equal(t, "nginx:latest", c.Image)
	assert.Equal(t, container.StatePending, c.GetState())
	assert.Equal(t, resources, c.Resources)
	assert.NotNil(t, c.Labels)
	assert.WithinDuration(t, time.Now(), c.CreatedAt, time.Second)
}

func TestContainerStateTransitions(t *testing.T) {
	c := container.NewContainer("test", "nginx:latest", container.Resources{})

	// Initial state
	assert.Equal(t, container.StatePending, c.GetState())

	// Transition to running
	c.SetState(container.StateRunning)
	assert.Equal(t, container.StateRunning, c.GetState())
	assert.NotNil(t, c.StartedAt)

	// Transition to stopped
	c.SetState(container.StateStopped)
	assert.Equal(t, container.StateStopped, c.GetState())
	assert.NotNil(t, c.StoppedAt)
}

func TestNewNode(t *testing.T) {
	resources := container.Resources{
		CPU:    4.0,
		Memory: 8 * 1024 * 1024 * 1024, // 8GB
		Disk:   100 * 1024 * 1024 * 1024, // 100GB
	}

	node := container.NewNode("node-1", "192.168.1.1", resources)

	assert.NotEmpty(t, node.ID)
	assert.Equal(t, "node-1", node.Name)
	assert.Equal(t, "192.168.1.1", node.Address)
	assert.Equal(t, resources, node.Resources)
	assert.Equal(t, container.NodeReady, node.State)
	assert.NotNil(t, node.Labels)
	assert.NotNil(t, node.Containers)
}

func TestNodeAvailableResources(t *testing.T) {
	resources := container.Resources{
		CPU:    4.0,
		Memory: 8 * 1024 * 1024 * 1024,
		Disk:   100 * 1024 * 1024 * 1024,
	}

	node := container.NewNode("node-1", "192.168.1.1", resources)

	// Initially all resources available
	available := node.AvailableResources()
	assert.Equal(t, resources, available)

	// Add container
	containerResources := container.Resources{
		CPU:    1.0,
		Memory: 1024 * 1024 * 1024,
		Disk:   10 * 1024 * 1024 * 1024,
	}
	node.AddContainer("container-1", containerResources)

	// Check available resources
	available = node.AvailableResources()
	assert.Equal(t, 3.0, available.CPU)
	assert.Equal(t, int64(7*1024*1024*1024), available.Memory)
	assert.Equal(t, int64(90*1024*1024*1024), available.Disk)
}

func TestNodeCanSchedule(t *testing.T) {
	resources := container.Resources{
		CPU:    4.0,
		Memory: 8 * 1024 * 1024 * 1024,
		Disk:   100 * 1024 * 1024 * 1024,
	}

	node := container.NewNode("node-1", "192.168.1.1", resources)

	// Small container should be schedulable
	smallContainer := container.NewContainer("small", "nginx:latest", container.Resources{
		CPU:    1.0,
		Memory: 1024 * 1024 * 1024,
		Disk:   10 * 1024 * 1024 * 1024,
	})
	assert.True(t, node.CanSchedule(smallContainer))

	// Large container should not be schedulable
	largeContainer := container.NewContainer("large", "nginx:latest", container.Resources{
		CPU:    8.0,
		Memory: 16 * 1024 * 1024 * 1024,
		Disk:   200 * 1024 * 1024 * 1024,
	})
	assert.False(t, node.CanSchedule(largeContainer))

	// Node not ready
	node.State = container.NodeNotReady
	assert.False(t, node.CanSchedule(smallContainer))
}

func TestNodeRemoveContainer(t *testing.T) {
	resources := container.Resources{
		CPU:    4.0,
		Memory: 8 * 1024 * 1024 * 1024,
		Disk:   100 * 1024 * 1024 * 1024,
	}

	node := container.NewNode("node-1", "192.168.1.1", resources)

	containerResources := container.Resources{
		CPU:    1.0,
		Memory: 1024 * 1024 * 1024,
		Disk:   10 * 1024 * 1024 * 1024,
	}

	// Add container
	node.AddContainer("container-1", containerResources)
	assert.Len(t, node.Containers, 1)

	// Remove container
	node.RemoveContainer("container-1", containerResources)
	assert.Len(t, node.Containers, 0)

	// Check resources restored
	available := node.AvailableResources()
	assert.Equal(t, resources, available)
}

func TestNewService(t *testing.T) {
	template := container.ContainerTemplate{
		Image: "nginx:latest",
		Resources: container.Resources{
			CPU:    0.5,
			Memory: 512 * 1024 * 1024,
			Disk:   5 * 1024 * 1024 * 1024,
		},
	}

	service := container.NewService("web-service", 3, template)

	assert.NotEmpty(t, service.ID)
	assert.Equal(t, "web-service", service.Name)
	assert.Equal(t, 3, service.Replicas)
	assert.Equal(t, template, service.Template)
	assert.NotNil(t, service.Labels)
	assert.NotNil(t, service.Selector)
	assert.Equal(t, container.StrategyRollingUpdate, service.Strategy.Type)
}
