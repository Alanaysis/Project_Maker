package tests

import (
	"testing"
	"time"

	"github.com/container-orchestrator/pkg/container"
	"github.com/container-orchestrator/pkg/discovery"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

func TestNewDiscovery(t *testing.T) {
	d := discovery.NewDiscovery()
	assert.NotNil(t, d)
	assert.Equal(t, 0, d.GetServiceCount())
	assert.Equal(t, 0, d.GetEndpointCount())
}

func TestRegisterService(t *testing.T) {
	d := discovery.NewDiscovery()

	service := container.NewService("web-service", 3, container.ContainerTemplate{
		Image: "nginx:latest",
	})

	err := d.RegisterService(service)
	assert.NoError(t, err)
	assert.Equal(t, 1, d.GetServiceCount())

	// Get service
	got, err := d.GetService(service.ID)
	assert.NoError(t, err)
	assert.Equal(t, service, got)

	// Get service by name
	got, err = d.GetServiceByName("web-service")
	assert.NoError(t, err)
	assert.Equal(t, service, got)
}

func TestUnregisterService(t *testing.T) {
	d := discovery.NewDiscovery()

	service := container.NewService("web-service", 3, container.ContainerTemplate{
		Image: "nginx:latest",
	})

	err := d.RegisterService(service)
	require.NoError(t, err)

	err = d.UnregisterService(service.ID)
	assert.NoError(t, err)
	assert.Equal(t, 0, d.GetServiceCount())
}

func TestRegisterEndpoint(t *testing.T) {
	d := discovery.NewDiscovery()

	service := container.NewService("web-service", 3, container.ContainerTemplate{
		Image: "nginx:latest",
	})
	err := d.RegisterService(service)
	require.NoError(t, err)

	endpoint := &discovery.Endpoint{
		ID:          "endpoint-1",
		ServiceID:   service.ID,
		ContainerID: "container-1",
		NodeID:      "node-1",
		Address:     "192.168.1.1",
		Port:        8080,
		Health:      discovery.HealthHealthy,
		Weight:      1,
	}

	err = d.RegisterEndpoint(endpoint)
	assert.NoError(t, err)
	assert.Equal(t, 1, d.GetEndpointCount())

	// Get endpoints
	endpoints, err := d.GetEndpoints(service.ID)
	assert.NoError(t, err)
	assert.Len(t, endpoints, 1)
	assert.Equal(t, endpoint, endpoints[0])
}

func TestUnregisterEndpoint(t *testing.T) {
	d := discovery.NewDiscovery()

	service := container.NewService("web-service", 3, container.ContainerTemplate{
		Image: "nginx:latest",
	})
	err := d.RegisterService(service)
	require.NoError(t, err)

	endpoint := &discovery.Endpoint{
		ID:          "endpoint-1",
		ServiceID:   service.ID,
		ContainerID: "container-1",
		NodeID:      "node-1",
		Address:     "192.168.1.1",
		Port:        8080,
		Health:      discovery.HealthHealthy,
		Weight:      1,
	}

	err = d.RegisterEndpoint(endpoint)
	require.NoError(t, err)

	err = d.UnregisterEndpoint(service.ID, endpoint.ID)
	assert.NoError(t, err)
	assert.Equal(t, 0, d.GetEndpointCount())
}

func TestGetHealthyEndpoints(t *testing.T) {
	d := discovery.NewDiscovery()

	service := container.NewService("web-service", 3, container.ContainerTemplate{
		Image: "nginx:latest",
	})
	err := d.RegisterService(service)
	require.NoError(t, err)

	// Add healthy endpoint
	healthy := &discovery.Endpoint{
		ID:          "endpoint-1",
		ServiceID:   service.ID,
		ContainerID: "container-1",
		NodeID:      "node-1",
		Address:     "192.168.1.1",
		Port:        8080,
		Health:      discovery.HealthHealthy,
		Weight:      1,
	}
	err = d.RegisterEndpoint(healthy)
	require.NoError(t, err)

	// Add unhealthy endpoint
	unhealthy := &discovery.Endpoint{
		ID:          "endpoint-2",
		ServiceID:   service.ID,
		ContainerID: "container-2",
		NodeID:      "node-2",
		Address:     "192.168.1.2",
		Port:        8080,
		Health:      discovery.HealthUnhealthy,
		Weight:      1,
	}
	err = d.RegisterEndpoint(unhealthy)
	require.NoError(t, err)

	// Get healthy endpoints
	endpoints, err := d.GetHealthyEndpoints(service.ID)
	assert.NoError(t, err)
	assert.Len(t, endpoints, 1)
	assert.Equal(t, healthy.ID, endpoints[0].ID)
}

func TestResolve(t *testing.T) {
	d := discovery.NewDiscovery()

	service := container.NewService("web-service", 3, container.ContainerTemplate{
		Image: "nginx:latest",
	})
	err := d.RegisterService(service)
	require.NoError(t, err)

	// Add endpoints
	for i := 0; i < 3; i++ {
		endpoint := &discovery.Endpoint{
			ID:          "endpoint-" + string(rune('1'+i)),
			ServiceID:   service.ID,
			ContainerID: "container-" + string(rune('1'+i)),
			NodeID:      "node-" + string(rune('1'+i)),
			Address:     "192.168.1." + string(rune('1'+i)),
			Port:        8080,
			Health:      discovery.HealthHealthy,
			Weight:      1,
			LastSeen:    time.Now(),
		}
		err = d.RegisterEndpoint(endpoint)
		require.NoError(t, err)
	}

	// Resolve
	endpoint, err := d.Resolve("web-service")
	assert.NoError(t, err)
	assert.NotNil(t, endpoint)
}

func TestWatch(t *testing.T) {
	d := discovery.NewDiscovery()

	service := container.NewService("web-service", 3, container.ContainerTemplate{
		Image: "nginx:latest",
	})
	err := d.RegisterService(service)
	require.NoError(t, err)

	// Watch for events
	ch := d.Watch(service.ID)

	// Register endpoint
	endpoint := &discovery.Endpoint{
		ID:          "endpoint-1",
		ServiceID:   service.ID,
		ContainerID: "container-1",
		NodeID:      "node-1",
		Address:     "192.168.1.1",
		Port:        8080,
		Health:      discovery.HealthHealthy,
		Weight:      1,
	}
	err = d.RegisterEndpoint(endpoint)
	require.NoError(t, err)

	// Should receive event
	select {
	case event := <-ch:
		assert.Equal(t, discovery.EventEndpointAdded, event.Type)
		assert.Equal(t, service.ID, event.ServiceID)
	case <-time.After(time.Second):
		t.Fatal("timeout waiting for event")
	}
}

func TestCleanup(t *testing.T) {
	d := discovery.NewDiscovery()

	service := container.NewService("web-service", 3, container.ContainerTemplate{
		Image: "nginx:latest",
	})
	err := d.RegisterService(service)
	require.NoError(t, err)

	// Add old unhealthy endpoint
	endpoint := &discovery.Endpoint{
		ID:          "endpoint-1",
		ServiceID:   service.ID,
		ContainerID: "container-1",
		NodeID:      "node-1",
		Address:     "192.168.1.1",
		Port:        8080,
		Health:      discovery.HealthUnhealthy,
		Weight:      1,
		LastSeen:    time.Now().Add(-15 * time.Minute),
	}
	err = d.RegisterEndpoint(endpoint)
	require.NoError(t, err)

	// Cleanup with 10 minute max age
	removed := d.Cleanup(10 * time.Minute)
	assert.Equal(t, 1, removed)
	assert.Equal(t, 0, d.GetEndpointCount())
}
