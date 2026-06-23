package tests

import (
	"testing"

	"github.com/container-orchestrator/pkg/container"
	"github.com/container-orchestrator/pkg/scheduler"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

func TestNewScheduler(t *testing.T) {
	s := scheduler.NewScheduler(scheduler.StrategyBinPacking)
	assert.NotNil(t, s)
}

func TestAddRemoveNode(t *testing.T) {
	s := scheduler.NewScheduler(scheduler.StrategyBinPacking)

	node := container.NewNode("node-1", "192.168.1.1", container.Resources{
		CPU:    4.0,
		Memory: 8 * 1024 * 1024 * 1024,
		Disk:   100 * 1024 * 1024 * 1024,
	})

	s.AddNode(node)

	// Get node
	got, ok := s.GetNode(node.ID)
	assert.True(t, ok)
	assert.Equal(t, node, got)

	// Get all nodes
	nodes := s.GetNodes()
	assert.Len(t, nodes, 1)

	// Remove node
	s.RemoveNode(node.ID)
	nodes = s.GetNodes()
	assert.Len(t, nodes, 0)
}

func TestScheduleContainer(t *testing.T) {
	s := scheduler.NewScheduler(scheduler.StrategyBinPacking)

	// Add nodes
	node1 := container.NewNode("node-1", "192.168.1.1", container.Resources{
		CPU:    4.0,
		Memory: 8 * 1024 * 1024 * 1024,
		Disk:   100 * 1024 * 1024 * 1024,
	})
	node2 := container.NewNode("node-2", "192.168.1.2", container.Resources{
		CPU:    4.0,
		Memory: 8 * 1024 * 1024 * 1024,
		Disk:   100 * 1024 * 1024 * 1024,
	})

	s.AddNode(node1)
	s.AddNode(node2)

	// Schedule container
	c := container.NewContainer("test", "nginx:latest", container.Resources{
		CPU:    1.0,
		Memory: 1024 * 1024 * 1024,
		Disk:   10 * 1024 * 1024 * 1024,
	})

	node, err := s.Schedule(c)
	require.NoError(t, err)
	assert.NotNil(t, node)
	assert.Equal(t, node.ID, c.NodeID)

	// Get container
	got, ok := s.GetContainer(c.ID)
	assert.True(t, ok)
	assert.Equal(t, c, got)

	// Get containers
	containers := s.GetContainers()
	assert.Len(t, containers, 1)
}

func TestScheduleNoAvailableNode(t *testing.T) {
	s := scheduler.NewScheduler(scheduler.StrategyBinPacking)

	// No nodes added
	c := container.NewContainer("test", "nginx:latest", container.Resources{
		CPU:    1.0,
		Memory: 1024 * 1024 * 1024,
		Disk:   10 * 1024 * 1024 * 1024,
	})

	_, err := s.Schedule(c)
	assert.ErrorIs(t, err, scheduler.ErrNoAvailableNode)
}

func TestScheduleInsufficientResources(t *testing.T) {
	s := scheduler.NewScheduler(scheduler.StrategyBinPacking)

	// Add small node
	node := container.NewNode("node-1", "192.168.1.1", container.Resources{
		CPU:    1.0,
		Memory: 1024 * 1024 * 1024,
		Disk:   10 * 1024 * 1024 * 1024,
	})
	s.AddNode(node)

	// Try to schedule large container
	c := container.NewContainer("test", "nginx:latest", container.Resources{
		CPU:    4.0,
		Memory: 8 * 1024 * 1024 * 1024,
		Disk:   100 * 1024 * 1024 * 1024,
	})

	_, err := s.Schedule(c)
	assert.ErrorIs(t, err, scheduler.ErrNoAvailableNode)
}

func TestUnscheduleContainer(t *testing.T) {
	s := scheduler.NewScheduler(scheduler.StrategyBinPacking)

	node := container.NewNode("node-1", "192.168.1.1", container.Resources{
		CPU:    4.0,
		Memory: 8 * 1024 * 1024 * 1024,
		Disk:   100 * 1024 * 1024 * 1024,
	})
	s.AddNode(node)

	c := container.NewContainer("test", "nginx:latest", container.Resources{
		CPU:    1.0,
		Memory: 1024 * 1024 * 1024,
		Disk:   10 * 1024 * 1024 * 1024,
	})

	_, err := s.Schedule(c)
	require.NoError(t, err)

	// Unschedule
	err = s.Unschedule(c.ID)
	assert.NoError(t, err)

	// Container should be removed
	_, ok := s.GetContainer(c.ID)
	assert.False(t, ok)
}

func TestBinPackingStrategy(t *testing.T) {
	s := scheduler.NewScheduler(scheduler.StrategyBinPacking)

	// Add nodes with different resources
	node1 := container.NewNode("node-1", "192.168.1.1", container.Resources{
		CPU:    4.0,
		Memory: 8 * 1024 * 1024 * 1024,
		Disk:   100 * 1024 * 1024 * 1024,
	})
	node2 := container.NewNode("node-2", "192.168.1.2", container.Resources{
		CPU:    8.0,
		Memory: 16 * 1024 * 1024 * 1024,
		Disk:   200 * 1024 * 1024 * 1024,
	})

	s.AddNode(node1)
	s.AddNode(node2)

	// Schedule container - should go to node1 (less resources)
	c := container.NewContainer("test", "nginx:latest", container.Resources{
		CPU:    1.0,
		Memory: 1024 * 1024 * 1024,
		Disk:   10 * 1024 * 1024 * 1024,
	})

	node, err := s.Schedule(c)
	require.NoError(t, err)
	assert.Equal(t, node1.ID, node.ID)
}

func TestSpreadStrategy(t *testing.T) {
	s := scheduler.NewScheduler(scheduler.StrategySpread)

	// Add nodes
	node1 := container.NewNode("node-1", "192.168.1.1", container.Resources{
		CPU:    4.0,
		Memory: 8 * 1024 * 1024 * 1024,
		Disk:   100 * 1024 * 1024 * 1024,
	})
	node2 := container.NewNode("node-2", "192.168.1.2", container.Resources{
		CPU:    4.0,
		Memory: 8 * 1024 * 1024 * 1024,
		Disk:   100 * 1024 * 1024 * 1024,
	})

	s.AddNode(node1)
	s.AddNode(node2)

	// Schedule first container
	c1 := container.NewContainer("test-1", "nginx:latest", container.Resources{
		CPU:    1.0,
		Memory: 1024 * 1024 * 1024,
		Disk:   10 * 1024 * 1024 * 1024,
	})

	node, err := s.Schedule(c1)
	require.NoError(t, err)

	// Schedule second container - should go to the other node
	c2 := container.NewContainer("test-2", "nginx:latest", container.Resources{
		CPU:    1.0,
		Memory: 1024 * 1024 * 1024,
		Disk:   10 * 1024 * 1024 * 1024,
	})

	node2Selected, err := s.Schedule(c2)
	require.NoError(t, err)
	assert.NotEqual(t, node.ID, node2Selected.ID)
}

func TestGetClusterStats(t *testing.T) {
	s := scheduler.NewScheduler(scheduler.StrategyBinPacking)

	// Add node
	node := container.NewNode("node-1", "192.168.1.1", container.Resources{
		CPU:    4.0,
		Memory: 8 * 1024 * 1024 * 1024,
		Disk:   100 * 1024 * 1024 * 1024,
	})
	s.AddNode(node)

	// Schedule container
	c := container.NewContainer("test", "nginx:latest", container.Resources{
		CPU:    1.0,
		Memory: 1024 * 1024 * 1024,
		Disk:   10 * 1024 * 1024 * 1024,
	})
	c.SetState(container.StateRunning)
	_, err := s.Schedule(c)
	require.NoError(t, err)

	// Get stats
	stats := s.GetClusterStats()
	assert.Equal(t, 1, stats.TotalNodes)
	assert.Equal(t, 1, stats.ReadyNodes)
	assert.Equal(t, 1, stats.TotalContainers)
	assert.Equal(t, 1, stats.RunningContainers)
	assert.Equal(t, 4.0, stats.TotalCPU)
	assert.Equal(t, 1.0, stats.UsedCPU)
}

func TestGetContainersByNode(t *testing.T) {
	s := scheduler.NewScheduler(scheduler.StrategyBinPacking)

	node1 := container.NewNode("node-1", "192.168.1.1", container.Resources{
		CPU:    4.0,
		Memory: 8 * 1024 * 1024 * 1024,
		Disk:   100 * 1024 * 1024 * 1024,
	})
	node2 := container.NewNode("node-2", "192.168.1.2", container.Resources{
		CPU:    4.0,
		Memory: 8 * 1024 * 1024 * 1024,
		Disk:   100 * 1024 * 1024 * 1024,
	})

	s.AddNode(node1)
	s.AddNode(node2)

	// Schedule containers
	for i := 0; i < 3; i++ {
		c := container.NewContainer("test", "nginx:latest", container.Resources{
			CPU:    1.0,
			Memory: 1024 * 1024 * 1024,
			Disk:   10 * 1024 * 1024 * 1024,
		})
		_, err := s.Schedule(c)
		require.NoError(t, err)
	}

	// Get containers by node
	containers1 := s.GetContainersByNode(node1.ID)
	containers2 := s.GetContainersByNode(node2.ID)

	assert.Len(t, containers1, 3) // Bin packing packs to first node
	assert.Len(t, containers2, 0)
}
