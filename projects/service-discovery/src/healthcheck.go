package main

import (
	"fmt"
	"net"
	"net/http"
	"sync"
	"time"
)

// HealthChecker monitors the health of service instances.
//
// Health checking is critical for service discovery because it ensures that
// traffic is only routed to healthy, operational service instances.
//
// Supported health check types:
//   - TCP: Attempts a TCP connection to the service port
//   - HTTP: Makes an HTTP request to a health endpoint
//   - Custom: Uses a user-provided check function
//
// The health checker runs in a separate goroutine and periodically
// checks all registered instances, updating their status in the registry.
type HealthChecker struct {
	mu          sync.RWMutex
	configs     map[string]HealthCheckConfig // instance ID -> health check config
	registry    *ServiceRegistry             // Reference to the service registry
	stopCh      chan struct{}                // Channel to signal the checker to stop
	stopped     chan struct{}                // Channel to signal that the checker has stopped
	isRunning   bool
}

// NewHealthChecker creates a new health checker with the given registry.
func NewHealthChecker(registry *ServiceRegistry) *HealthChecker {
	return &HealthChecker{
		configs:  make(map[string]HealthCheckConfig),
		registry: registry,
		stopCh:   make(chan struct{}),
		stopped:  make(chan struct{}),
	}
}

// Start begins the health check loop in a background goroutine.
// The loop runs indefinitely until Stop() is called.
func (hc *HealthChecker) Start() {
	hc.mu.Lock()
	if hc.isRunning {
		hc.mu.Unlock()
		return
	}
	hc.isRunning = true
	hc.mu.Unlock()

	go hc.checkLoop()
	fmt.Println("[HealthChecker] Started")
}

// Stop signals the health checker to stop and waits for it to exit.
func (hc *HealthChecker) Stop() {
	hc.mu.Lock()
	if !hc.isRunning {
		hc.mu.Unlock()
		return
	}
	hc.mu.Unlock()

	close(hc.stopCh)
	<-hc.stopped
	hc.mu.Lock()
	hc.isRunning = false
	hc.mu.Unlock()
	fmt.Println("[HealthChecker] Stopped")
}

// RegisterCheck registers a health check configuration for a service instance.
func (hc *HealthChecker) RegisterCheck(instanceID string, config HealthCheckConfig) {
	hc.mu.Lock()
	defer hc.mu.Unlock()

	hc.configs[instanceID] = config
	fmt.Printf("[HealthChecker] Registered check for %s (type=%s)\n", instanceID, config.Type)
}

// UnregisterCheck removes the health check configuration for an instance.
func (hc *HealthChecker) UnregisterCheck(instanceID string) {
	hc.mu.Lock()
	defer hc.mu.Unlock()

	delete(hc.configs, instanceID)
}

// checkLoop runs the main health check loop.
func (hc *HealthChecker) checkLoop() {
	defer close(hc.stopped)

	for instanceID, config := range hc.configs {
		if config.Interval == 0 {
			config.Interval = 10 * time.Second
		}
		if config.Timeout == 0 {
			config.Timeout = 5 * time.Second
		}
		hc.configs[instanceID] = config
	}

	ticker := hc.getMinimumTicker()
	if ticker == nil {
		return
	}

	for {
		select {
		case <-hc.stopCh:
			ticker.Stop()
			return
		case <-ticker.C:
			hc.checkAll()
		}
	}
}

// getMinimumTicker returns a ticker with the minimum interval among all checks.
func (hc *HealthChecker) getMinimumTicker() *time.Ticker {
	hc.mu.RLock()
	defer hc.mu.RUnlock()

	minInterval := time.Hour
	hasChecks := false

	for _, config := range hc.configs {
		if config.Interval < minInterval {
			minInterval = config.Interval
		}
		hasChecks = true
	}

	if !hasChecks {
		return nil
	}

	return time.NewTicker(minInterval)
}

// checkAll performs health checks on all registered instances.
func (hc *HealthChecker) checkAll() {
	hc.mu.RLock()
	configs := make(map[string]HealthCheckConfig)
	for id, config := range hc.configs {
		configs[id] = config
	}
	hc.mu.RUnlock()

	for instanceID, config := range configs {
		healthy := hc.performCheck(instanceID, config)

		// Update registry with health status
		hc.registry.UpdateHealth(instanceID, healthy)

		if healthy {
			hc.registry.RefreshInstance(instanceID)
		}
	}
}

// performCheck performs a single health check for an instance.
func (hc *HealthChecker) performCheck(instanceID string, config HealthCheckConfig) bool {
	switch config.Type {
	case HealthCheckTCP:
		return hc.checkTCP(instanceID, config)
	case HealthCheckHTTP:
		return hc.checkHTTP(instanceID, config)
	case HealthCheckCustom:
		if config.CustomChecker != nil {
			return config.CustomChecker()
		}
		return false
	default:
		return false
	}
}

// checkTCP performs a TCP health check.
// It attempts to establish a TCP connection to the service instance's port.
// A successful connection indicates the service is healthy.
func (hc *HealthChecker) checkTCP(instanceID string, config HealthCheckConfig) bool {
	instance, exists := hc.registry.GetInstance(instanceID)
	if !exists {
		return false
	}

	addr := net.JoinHostPort(instance.Address, fmt.Sprintf("%d", instance.Port))

	// Use a context with timeout for the connection
	conn, err := net.DialTimeout("tcp", addr, config.Timeout)
	if err != nil {
		fmt.Printf("[HealthCheck] TCP FAILED: %s -> %s (%v)\n", instanceID, addr, err)
		return false
	}
	defer conn.Close()

	return true
}

// checkHTTP performs an HTTP health check.
// It makes an HTTP GET request to the health endpoint of the service.
// A 2xx response indicates the service is healthy.
func (hc *HealthChecker) checkHTTP(instanceID string, config HealthCheckConfig) bool {
	instance, exists := hc.registry.GetInstance(instanceID)
	if !exists {
		return false
	}

	port := instance.Port
	if config.HTTPPort > 0 {
		port = config.HTTPPort
	}

	url := fmt.Sprintf("http://%s:%d%s", instance.Address, port, config.HTTPPath)

	client := &http.Client{
		Timeout: config.Timeout,
	}

	resp, err := client.Get(url)
	if err != nil {
		fmt.Printf("[HealthCheck] HTTP FAILED: %s -> %s (%v)\n", instanceID, url, err)
		return false
	}
	defer resp.Body.Close()

	if resp.StatusCode >= 200 && resp.StatusCode < 300 {
		return true
	}

	fmt.Printf("[HealthCheck] HTTP FAILED: %s -> %s (status=%d)\n", instanceID, url, resp.StatusCode)
	return false
}

// CheckInstance performs a one-time health check without starting the checker.
func (hc *HealthChecker) CheckInstance(instanceID string) bool {
	hc.mu.RLock()
	config, exists := hc.configs[instanceID]
	hc.mu.RUnlock()

	if !exists {
		return false
	}

	return hc.performCheck(instanceID, config)
}
