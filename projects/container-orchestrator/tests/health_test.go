package tests

import (
	"context"
	"testing"
	"time"

	"github.com/container-orchestrator/pkg/container"
	"github.com/container-orchestrator/pkg/health"
	"github.com/stretchr/testify/assert"
)

func TestNewHealthMonitor(t *testing.T) {
	checker := health.NewHTTPHealthChecker(&mockHTTPClient{})
	monitor := health.NewHealthMonitor(checker)
	assert.NotNil(t, monitor)
}

func TestAddRemoveContainer(t *testing.T) {
	checker := health.NewHTTPHealthChecker(&mockHTTPClient{})
	monitor := health.NewHealthMonitor(checker)

	c := container.NewContainer("test", "nginx:latest", container.Resources{})

	// Add container
	monitor.AddContainer(c)

	// Get health
	result, err := monitor.GetHealth(c.ID)
	assert.NoError(t, err)
	assert.NotNil(t, result)
	assert.Equal(t, health.StateUnknown, result.State)

	// Remove container
	monitor.RemoveContainer(c.ID)

	// Get health should fail
	_, err = monitor.GetHealth(c.ID)
	assert.ErrorIs(t, err, health.ErrContainerNotFound)
}

func TestGetAllHealth(t *testing.T) {
	checker := health.NewHTTPHealthChecker(&mockHTTPClient{})
	monitor := health.NewHealthMonitor(checker)

	// Add containers
	for i := 0; i < 3; i++ {
		c := container.NewContainer("test", "nginx:latest", container.Resources{})
		monitor.AddContainer(c)
	}

	// Get all health - now includes both liveness and readiness results
	results := monitor.GetAllHealth()
	assert.Len(t, results, 6) // 3 liveness + 3 readiness
}

func TestGetSummary(t *testing.T) {
	checker := health.NewHTTPHealthChecker(&mockHTTPClient{})
	monitor := health.NewHealthMonitor(checker)

	// Add containers
	for i := 0; i < 3; i++ {
		c := container.NewContainer("test", "nginx:latest", container.Resources{})
		monitor.AddContainer(c)
	}

	// Get summary - now includes both liveness and readiness results
	summary := monitor.GetSummary()
	assert.Equal(t, 6, summary.Total) // 3 liveness + 3 readiness
	assert.Equal(t, 6, summary.Unknown)
}

func TestHealthCheck(t *testing.T) {
	checker := health.NewHTTPHealthChecker(&mockHTTPClient{})
	monitor := health.NewHealthMonitor(checker)

	// Create running container
	c := container.NewContainer("test", "nginx:latest", container.Resources{})
	c.SetState(container.StateRunning)

	monitor.AddContainer(c)

	// Set event handler
	eventCh := make(chan *health.HealthEvent, 10)
	monitor.SetEventHandler(func(event *health.HealthEvent) {
		eventCh <- event
	})

	// Start monitoring
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()
	monitor.Start(ctx, 100*time.Millisecond)

	// Wait for health check
	select {
	case event := <-eventCh:
		assert.Equal(t, health.EventContainerHealthy, event.Type)
		assert.Equal(t, c.ID, event.ContainerID)
	case <-time.After(time.Second):
		t.Fatal("timeout waiting for health check")
	}

	// Check health state
	result, err := monitor.GetHealth(c.ID)
	assert.NoError(t, err)
	assert.Equal(t, health.StateHealthy, result.State)
}

func TestHTTPHealthChecker(t *testing.T) {
	checker := health.NewHTTPHealthChecker(&mockHTTPClient{})

	// Running container
	runningContainer := container.NewContainer("test", "nginx:latest", container.Resources{})
	runningContainer.SetState(container.StateRunning)

	result, err := checker.Check(context.Background(), runningContainer)
	assert.NoError(t, err)
	assert.Equal(t, health.StateHealthy, result.State)

	// Stopped container
	stoppedContainer := container.NewContainer("test", "nginx:latest", container.Resources{})
	stoppedContainer.SetState(container.StateStopped)

	result, err = checker.Check(context.Background(), stoppedContainer)
	assert.NoError(t, err)
	assert.Equal(t, health.StateUnhealthy, result.State)
}

func TestLivenessProbe(t *testing.T) {
	checker := health.NewHTTPHealthChecker(&mockHTTPClient{})
	monitor := health.NewHealthMonitor(checker)

	// Create running container
	c := container.NewContainer("test", "nginx:latest", container.Resources{})
	c.SetState(container.StateRunning)

	monitor.AddContainer(c)

	// Start monitoring
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()
	monitor.Start(ctx, 50*time.Millisecond)

	// Wait for health check
	time.Sleep(200 * time.Millisecond)

	// Get liveness state
	result, err := monitor.GetLiveness(c.ID)
	assert.NoError(t, err)
	assert.Equal(t, health.StateHealthy, result.State)
	assert.Equal(t, health.ProbeLiveness, result.ProbeType)
}

func TestReadinessProbe(t *testing.T) {
	checker := health.NewHTTPHealthChecker(&mockHTTPClient{})
	monitor := health.NewHealthMonitor(checker)

	// Create running container
	c := container.NewContainer("test", "nginx:latest", container.Resources{})
	c.SetState(container.StateRunning)

	monitor.AddContainer(c)

	// Start monitoring
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()
	monitor.Start(ctx, 50*time.Millisecond)

	// Wait for health check
	time.Sleep(200 * time.Millisecond)

	// Get readiness state
	result, err := monitor.GetReadiness(c.ID)
	assert.NoError(t, err)
	assert.Equal(t, health.StateHealthy, result.State)
	assert.Equal(t, health.ProbeReadiness, result.ProbeType)
}

func TestReadinessNotReady(t *testing.T) {
	checker := health.NewHTTPHealthChecker(&mockHTTPClient{})
	monitor := health.NewHealthMonitor(checker)

	// Create stopped container (not ready)
	c := container.NewContainer("test", "nginx:latest", container.Resources{})
	c.SetState(container.StateStopped)

	monitor.AddContainer(c)

	// Start monitoring
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()
	monitor.Start(ctx, 50*time.Millisecond)

	// Wait for health check
	time.Sleep(200 * time.Millisecond)

	// Container should not be ready
	assert.False(t, monitor.IsReady(c.ID))
}

func TestIsReady(t *testing.T) {
	checker := health.NewHTTPHealthChecker(&mockHTTPClient{})
	monitor := health.NewHealthMonitor(checker)

	// Create running container
	c := container.NewContainer("test", "nginx:latest", container.Resources{})
	c.SetState(container.StateRunning)

	monitor.AddContainer(c)

	// Start monitoring
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()
	monitor.Start(ctx, 50*time.Millisecond)

	// Wait for health check
	time.Sleep(200 * time.Millisecond)

	// Container should be ready
	assert.True(t, monitor.IsReady(c.ID))
}

// mockHTTPClient implements HTTPClient interface
type mockHTTPClient struct{}

func (c *mockHTTPClient) Get(url string) (int, error) {
	return 200, nil
}
