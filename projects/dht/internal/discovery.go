package internal

import (
	"fmt"
	"log"
	"math/big"
	"sync"
	"time"
)

// DiscoveryConfig holds configuration for node discovery
type DiscoveryConfig struct {
	BootstrapAddrs []string      // Bootstrap node addresses
	RefreshInterval time.Duration // Interval for bucket refresh
	PingInterval    time.Duration // Interval for ping checks
	MaxRetries      int           // Max retries for failed operations
}

// DefaultDiscoveryConfig returns default discovery configuration
func DefaultDiscoveryConfig() *DiscoveryConfig {
	return &DiscoveryConfig{
		BootstrapAddrs:  []string{},
		RefreshInterval: 60 * time.Second,
		PingInterval:    30 * time.Second,
		MaxRetries:      3,
	}
}

// Discovery manages node discovery and routing table maintenance
type Discovery struct {
	mu       sync.RWMutex
	node     *NetworkNode
	config   *DiscoveryConfig
	stopCh   chan struct{}
	running  bool
}

// NewDiscovery creates a new discovery manager
func NewDiscovery(node *NetworkNode, config *DiscoveryConfig) *Discovery {
	if config == nil {
		config = DefaultDiscoveryConfig()
	}
	return &Discovery{
		node:   node,
		config: config,
		stopCh: make(chan struct{}),
	}
}

// Start starts the discovery process
func (d *Discovery) Start() error {
	d.mu.Lock()
	if d.running {
		d.mu.Unlock()
		return fmt.Errorf("discovery already running")
	}
	d.running = true
	d.mu.Unlock()

	// Bootstrap if addresses provided
	if len(d.config.BootstrapAddrs) > 0 {
		if err := d.Bootstrap(); err != nil {
			log.Printf("[Discovery] Bootstrap failed: %v", err)
		}
	}

	// Start periodic refresh
	go d.refreshLoop()

	// Start periodic ping
	go d.pingLoop()

	return nil
}

// Stop stops the discovery process
func (d *Discovery) Stop() {
	d.mu.Lock()
	defer d.mu.Unlock()

	if d.running {
		close(d.stopCh)
		d.running = false
	}
}

// IsRunning returns whether discovery is running
func (d *Discovery) IsRunning() bool {
	d.mu.RLock()
	defer d.mu.RUnlock()
	return d.running
}

// Bootstrap connects to bootstrap nodes and populates routing table
func (d *Discovery) Bootstrap() error {
	for _, addr := range d.config.BootstrapAddrs {
		// Ping bootstrap node
		if err := d.node.Ping(addr); err != nil {
			log.Printf("[Discovery] Failed to ping bootstrap %s: %v", addr, err)
			continue
		}

		// Find nodes close to ourselves
		contacts, err := d.node.RemoteFindNode(addr, d.node.GetID())
		if err != nil {
			log.Printf("[Discovery] Failed to find nodes from bootstrap %s: %v", addr, err)
			continue
		}

		// Add discovered contacts to routing table
		for _, c := range contacts {
			d.node.node.RT.AddContact(c)
		}

		log.Printf("[Discovery] Bootstrapped via %s, found %d contacts", addr, len(contacts))
	}

	return nil
}

// AddBootstrapNode adds a bootstrap node address
func (d *Discovery) AddBootstrapNode(addr string) {
	d.mu.Lock()
	defer d.mu.Unlock()
	d.config.BootstrapAddrs = append(d.config.BootstrapAddrs, addr)
}

// refreshLoop periodically refreshes k-buckets
func (d *Discovery) refreshLoop() {
	ticker := time.NewTicker(d.config.RefreshInterval)
	defer ticker.Stop()

	for {
		select {
		case <-d.stopCh:
			return
		case <-ticker.C:
			d.refreshBuckets()
		}
	}
}

// refreshBuckets refreshes k-buckets by finding nodes for random IDs
func (d *Discovery) refreshBuckets() {
	// Refresh buckets that haven't been queried recently
	for i := 0; i < NumBuckets; i++ {
		// Generate random ID for this bucket
		targetID := d.randomIDForBucket(i)

		// Find closest contacts
		closest := d.node.node.FindNode(targetID)

		// Query each contact
		for _, c := range closest {
			if c.Addr == d.node.GetAddr() {
				continue
			}

			contacts, err := d.node.RemoteFindNode(c.Addr, targetID)
			if err != nil {
				continue
			}

			// Add new contacts
			for _, nc := range contacts {
				d.node.node.RT.AddContact(nc)
			}
		}
	}
}

// pingLoop periodically pings contacts to check liveness
func (d *Discovery) pingLoop() {
	ticker := time.NewTicker(d.config.PingInterval)
	defer ticker.Stop()

	for {
		select {
		case <-d.stopCh:
			return
		case <-ticker.C:
			d.pingContacts()
		}
	}
}

// pingContacts pings all contacts in the routing table
func (d *Discovery) pingContacts() {
	contacts := d.node.node.FindNode(d.node.GetID())
	for _, c := range contacts {
		if c.Addr == d.node.GetAddr() {
			continue
		}

		if err := d.node.Ping(c.Addr); err != nil {
			// Contact is unreachable, could remove from routing table
			// For now, just log
			log.Printf("[Discovery] Contact %s unreachable: %v", c.Addr, err)
		}
	}
}

// randomIDForBucket generates a random ID in the range of a specific bucket
func (d *Discovery) randomIDForBucket(bucketIdx int) *big.Int {
	// Generate random ID in the bucket's range
	bucketStart := new(big.Int).Lsh(big.NewInt(1), uint(bucketIdx))
	bucketEnd := new(big.Int).Lsh(big.NewInt(1), uint(bucketIdx+1))

	diff := new(big.Int).Sub(bucketEnd, bucketStart)
	offset := new(big.Int).SetInt64(time.Now().UnixNano() % diff.Int64())

	return new(big.Int).Add(bucketStart, offset)
}

// NodeManager manages multiple DHT nodes in a single process
type NodeManager struct {
	mu      sync.RWMutex
	nodes   map[string]*NetworkNode
	primary *NetworkNode
}

// NewNodeManager creates a new node manager
func NewNodeManager() *NodeManager {
	return &NodeManager{
		nodes: make(map[string]*NetworkNode),
	}
}

// CreateNode creates and starts a new DHT node
func (nm *NodeManager) CreateNode(addr string) (*NetworkNode, error) {
	nm.mu.Lock()
	defer nm.mu.Unlock()

	if _, exists := nm.nodes[addr]; exists {
		return nil, fmt.Errorf("node %s already exists", addr)
	}

	node := NewNetworkNode(addr)
	if err := node.Start(); err != nil {
		return nil, fmt.Errorf("failed to start node: %v", err)
	}

	nm.nodes[addr] = node

	// Set as primary if first node
	if nm.primary == nil {
		nm.primary = node
	}

	return node, nil
}

// GetNode returns a node by address
func (nm *NodeManager) GetNode(addr string) *NetworkNode {
	nm.mu.RLock()
	defer nm.mu.RUnlock()
	return nm.nodes[addr]
}

// GetPrimary returns the primary node
func (nm *NodeManager) GetPrimary() *NetworkNode {
	nm.mu.RLock()
	defer nm.mu.RUnlock()
	return nm.primary
}

// RemoveNode stops and removes a node
func (nm *NodeManager) RemoveNode(addr string) error {
	nm.mu.Lock()
	defer nm.mu.Unlock()

	node, exists := nm.nodes[addr]
	if !exists {
		return fmt.Errorf("node %s not found", addr)
	}

	if err := node.Stop(); err != nil {
		return fmt.Errorf("failed to stop node: %v", err)
	}

	delete(nm.nodes, addr)

	// Update primary if needed
	if nm.primary == node {
		nm.primary = nil
		for _, n := range nm.nodes {
			nm.primary = n
			break
		}
	}

	return nil
}

// StopAll stops all nodes
func (nm *NodeManager) StopAll() {
	nm.mu.Lock()
	defer nm.mu.Unlock()

	for addr, node := range nm.nodes {
		if err := node.Stop(); err != nil {
			log.Printf("Failed to stop node %s: %v", addr, err)
		}
	}

	nm.nodes = make(map[string]*NetworkNode)
	nm.primary = nil
}

// NodeCount returns the number of managed nodes
func (nm *NodeManager) NodeCount() int {
	nm.mu.RLock()
	defer nm.mu.RUnlock()
	return len(nm.nodes)
}
