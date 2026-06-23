// Package healthcheck implements active health checking for registered services.
// It periodically probes services and updates their status in the store.
package healthcheck

import (
	"context"
	"fmt"
	"log"
	"net"
	"net/http"
	"sync"
	"time"

	"github.com/anthropic/service-discovery/internal/registry"
	"github.com/anthropic/service-discovery/internal/store"
)

// CheckType defines the type of health check to perform.
type CheckType int

const (
	CheckTCP  CheckType = iota // TCP connection check
	CheckHTTP                  // HTTP endpoint check
)

// Config holds configuration for the health checker.
type Config struct {
	// Interval is how often to check services.
	Interval time.Duration

	// Timeout is the maximum time to wait for a check response.
	Timeout time.Duration

	// Type is the type of health check to perform.
	Type CheckType

	// HTTPPath is the path to use for HTTP health checks.
	HTTPPath string
}

// DefaultConfig returns a Config with sensible defaults.
func DefaultConfig() Config {
	return Config{
		Interval: 5 * time.Second,
		Timeout:  2 * time.Second,
		Type:     CheckTCP,
		HTTPPath: "/health",
	}
}

// CheckResult contains the result of a health check.
type CheckResult struct {
	ServiceID string
	Healthy   bool
	Error     error
	Latency   time.Duration
}

// Checker performs health checks on registered services.
type Checker struct {
	store    store.Store
	config   Config
	mu       sync.RWMutex
	results  map[string]*CheckResult
	stopCh   chan struct{}
}

// New creates a new health Checker.
func New(s store.Store, config Config) *Checker {
	return &Checker{
		store:   s,
		config:  config,
		results: make(map[string]*CheckResult),
		stopCh:  make(chan struct{}),
	}
}

// Start begins the health checking loop. It watches for service changes
// and periodically checks all registered services.
func (c *Checker) Start(ctx context.Context) error {
	// Start watching for service changes
	watchCh, err := c.store.Watch(ctx, "/services/")
	if err != nil {
		return fmt.Errorf("start watch: %w", err)
	}

	// Start periodic check
	ticker := time.NewTicker(c.config.Interval)
	defer ticker.Stop()

	log.Printf("[healthcheck] started with interval %s, timeout %s", c.config.Interval, c.config.Timeout)

	for {
		select {
		case <-ctx.Done():
			return nil
		case <-c.stopCh:
			return nil
		case event, ok := <-watchCh:
			if !ok {
				return nil
			}
			c.handleEvent(ctx, event)
		case <-ticker.C:
			c.checkAll(ctx)
		}
	}
}

// Stop stops the health checker.
func (c *Checker) Stop() {
	close(c.stopCh)
}

// GetResult returns the last health check result for a service.
func (c *Checker) GetResult(serviceID string) (*CheckResult, bool) {
	c.mu.RLock()
	defer c.mu.RUnlock()
	result, ok := c.results[serviceID]
	return result, ok
}

// GetAllResults returns all health check results.
func (c *Checker) GetAllResults() map[string]*CheckResult {
	c.mu.RLock()
	defer c.mu.RUnlock()
	results := make(map[string]*CheckResult, len(c.results))
	for k, v := range c.results {
		results[k] = v
	}
	return results
}

// handleEvent processes a store event to track new/removed services.
func (c *Checker) handleEvent(ctx context.Context, event store.Event) {
	switch event.Type {
	case store.EventPut:
		svc, err := registry.UnmarshalService(event.Value)
		if err != nil {
			log.Printf("[healthcheck] failed to unmarshal service: %v", err)
			return
		}
		// Perform immediate check on new service
		result := c.check(ctx, svc)
		c.mu.Lock()
		c.results[svc.ID] = result
		c.mu.Unlock()
	case store.EventDelete:
		// Extract service ID from key
		// Key format: /services/{name}/{id}
		id := extractIDFromKey(event.Key)
		if id != "" {
			c.mu.Lock()
			delete(c.results, id)
			c.mu.Unlock()
		}
	}
}

// checkAll checks all registered services.
func (c *Checker) checkAll(ctx context.Context) {
	services, err := c.listServices(ctx)
	if err != nil {
		log.Printf("[healthcheck] failed to list services: %v", err)
		return
	}

	var wg sync.WaitGroup
	for _, svc := range services {
		wg.Add(1)
		go func(s *registry.Service) {
			defer wg.Done()
			result := c.check(ctx, s)
			c.mu.Lock()
			c.results[s.ID] = result
			c.mu.Unlock()

			if !result.Healthy {
				log.Printf("[healthcheck] service %s (%s) is unhealthy: %v", s.Name, s.Endpoint(), result.Error)
			}
		}(svc)
	}
	wg.Wait()
}

// check performs a health check on a single service.
func (c *Checker) check(ctx context.Context, svc *registry.Service) *CheckResult {
	start := time.Now()

	var healthy bool
	var err error

	switch c.config.Type {
	case CheckTCP:
		healthy, err = c.checkTCP(ctx, svc)
	case CheckHTTP:
		healthy, err = c.checkHTTP(ctx, svc)
	}

	latency := time.Since(start)

	return &CheckResult{
		ServiceID: svc.ID,
		Healthy:   healthy,
		Error:     err,
		Latency:   latency,
	}
}

// checkTCP performs a TCP connection check.
func (c *Checker) checkTCP(ctx context.Context, svc *registry.Service) (bool, error) {
	addr := svc.Endpoint()
	timeout := c.config.Timeout

	conn, err := net.DialTimeout("tcp", addr, timeout)
	if err != nil {
		return false, fmt.Errorf("tcp dial failed: %w", err)
	}
	conn.Close()
	return true, nil
}

// checkHTTP performs an HTTP health check.
func (c *Checker) checkHTTP(ctx context.Context, svc *registry.Service) (bool, error) {
	url := fmt.Sprintf("http://%s%s", svc.Endpoint(), c.config.HTTPPath)

	client := &http.Client{Timeout: c.config.Timeout}
	req, err := http.NewRequestWithContext(ctx, "GET", url, nil)
	if err != nil {
		return false, fmt.Errorf("create request: %w", err)
	}

	resp, err := client.Do(req)
	if err != nil {
		return false, fmt.Errorf("http request failed: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode >= 200 && resp.StatusCode < 300 {
		return true, nil
	}
	return false, fmt.Errorf("unhealthy status code: %d", resp.StatusCode)
}

// listServices lists all services from the store.
func (c *Checker) listServices(ctx context.Context) ([]*registry.Service, error) {
	data, err := c.store.List(ctx, "/services/")
	if err != nil {
		return nil, err
	}

	var services []*registry.Service
	for _, v := range data {
		svc, err := registry.UnmarshalService(v)
		if err != nil {
			continue
		}
		services = append(services, svc)
	}
	return services, nil
}

// extractIDFromKey extracts the service ID from a key like /services/{name}/{id}.
func extractIDFromKey(key string) string {
	// Simple extraction: find the last segment after the last /
	for i := len(key) - 1; i >= 0; i-- {
		if key[i] == '/' {
			return key[i+1:]
		}
	}
	return ""
}
