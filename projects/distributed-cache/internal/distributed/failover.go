package distributed

import (
	"log"
	"sync"
	"time"
)

// FailoverManager handles node failures and recovery
type FailoverManager struct {
	mu             sync.RWMutex
	node           *Node
	config         FailoverConfig
	failedNodes    map[string]*FailedNode
	recoveryCh     chan string
	stopCh         chan struct{}
	wg             sync.WaitGroup
	onFailover     func(nodeID string)
	onRecovery     func(nodeID string)
}

// FailoverConfig holds failover configuration
type FailoverConfig struct {
	HealthCheckInterval time.Duration
	FailureThreshold    int
	RecoveryInterval    time.Duration
	MaxRetries          int
}

// FailedNode represents a failed node
type FailedNode struct {
	ID            string
	FailedAt      time.Time
	RetryCount    int
	LastRetry     time.Time
	OriginalState NodeState
}

// DefaultFailoverConfig returns default failover configuration
func DefaultFailoverConfig() FailoverConfig {
	return FailoverConfig{
		HealthCheckInterval: 5 * time.Second,
		FailureThreshold:    3,
		RecoveryInterval:    30 * time.Second,
		MaxRetries:          5,
	}
}

// NewFailoverManager creates a new failover manager
func NewFailoverManager(node *Node, config FailoverConfig) *FailoverManager {
	fm := &FailoverManager{
		node:        node,
		config:      config,
		failedNodes: make(map[string]*FailedNode),
		recoveryCh:  make(chan string, 100),
		stopCh:      make(chan struct{}),
	}

	// Start monitoring
	fm.wg.Add(2)
	go fm.healthMonitor()
	go fm.recoveryWorker()

	return fm
}

// SetFailoverCallback sets the callback for failover events
func (fm *FailoverManager) SetFailoverCallback(callback func(nodeID string)) {
	fm.mu.Lock()
	defer fm.mu.Unlock()
	fm.onFailover = callback
}

// SetRecoveryCallback sets the callback for recovery events
func (fm *FailoverManager) SetRecoveryCallback(callback func(nodeID string)) {
	fm.mu.Lock()
	defer fm.mu.Unlock()
	fm.onRecovery = callback
}

// healthMonitor monitors peer health
func (fm *FailoverManager) healthMonitor() {
	defer fm.wg.Done()
	ticker := time.NewTicker(fm.config.HealthCheckInterval)
	defer ticker.Stop()

	consecutiveFailures := make(map[string]int)

	for {
		select {
		case <-ticker.C:
			fm.mu.RLock()
			peers := make(map[string]*PeerNode)
			for k, v := range fm.node.peers {
				peers[k] = v
			}
			fm.mu.RUnlock()

			for id, peer := range peers {
				if peer.Client == nil {
					continue
				}

				if err := peer.Client.Ping(); err != nil {
					consecutiveFailures[id]++
					if consecutiveFailures[id] >= fm.config.FailureThreshold {
						fm.handleFailure(id)
						delete(consecutiveFailures, id)
					}
				} else {
					consecutiveFailures[id] = 0
					fm.handleRecovery(id)
				}
			}
		case <-fm.stopCh:
			return
		}
	}
}

// handleFailure handles a node failure
func (fm *FailoverManager) handleFailure(nodeID string) {
	fm.mu.Lock()
	defer fm.mu.Unlock()

	// Check if already marked as failed
	if _, exists := fm.failedNodes[nodeID]; exists {
		return
	}

	log.Printf("Node %s detected as failed", nodeID)

	// Mark as failed
	fm.failedNodes[nodeID] = &FailedNode{
		ID:            nodeID,
		FailedAt:      time.Now(),
		OriginalState: NodeStateRunning,
	}

	// Update peer state
	if peer, exists := fm.node.peers[nodeID]; exists {
		peer.State = NodeStateDown
	}

	// Trigger failover callback
	if fm.onFailover != nil {
		go fm.onFailover(nodeID)
	}

	// Start recovery attempts
	fm.recoveryCh <- nodeID
}

// handleRecovery handles a node recovery
func (fm *FailoverManager) handleRecovery(nodeID string) {
	fm.mu.Lock()
	defer fm.mu.Unlock()

	// Check if was failed
	if failedNode, exists := fm.failedNodes[nodeID]; exists {
		log.Printf("Node %s recovered after %d retries", nodeID, failedNode.RetryCount)
		delete(fm.failedNodes, nodeID)

		// Update peer state
		if peer, exists := fm.node.peers[nodeID]; exists {
			peer.State = NodeStateRunning
			peer.LastSeen = time.Now()
		}

		// Trigger recovery callback
		if fm.onRecovery != nil {
			go fm.onRecovery(nodeID)
		}
	}
}

// recoveryWorker attempts to recover failed nodes
func (fm *FailoverManager) recoveryWorker() {
	defer fm.wg.Done()

	for {
		select {
		case nodeID := <-fm.recoveryCh:
			fm.attemptRecovery(nodeID)
		case <-fm.stopCh:
			return
		}
	}
}

func (fm *FailoverManager) attemptRecovery(nodeID string) {
	ticker := time.NewTicker(fm.config.RecoveryInterval)
	defer ticker.Stop()

	for {
		select {
		case <-ticker.C:
			fm.mu.Lock()
			failedNode, exists := fm.failedNodes[nodeID]
			if !exists {
				fm.mu.Unlock()
				return
			}

			if failedNode.RetryCount >= fm.config.MaxRetries {
				log.Printf("Max retries reached for node %s", nodeID)
				fm.mu.Unlock()
				return
			}

			failedNode.RetryCount++
			failedNode.LastRetry = time.Now()
			fm.mu.Unlock()

			// Try to connect
			peer, exists := fm.node.peers[nodeID]
			if !exists || peer.Client == nil {
				continue
			}

			if err := peer.Client.Ping(); err == nil {
				fm.handleRecovery(nodeID)
				return
			}

			log.Printf("Recovery attempt %d for node %s failed", failedNode.RetryCount, nodeID)

		case <-fm.stopCh:
			return
		}
	}
}

// GetFailedNodes returns all failed nodes
func (fm *FailoverManager) GetFailedNodes() map[string]*FailedNode {
	fm.mu.RLock()
	defer fm.mu.RUnlock()
	result := make(map[string]*FailedNode)
	for k, v := range fm.failedNodes {
		result[k] = v
	}
	return result
}

// IsNodeHealthy checks if a node is healthy
func (fm *FailoverManager) IsNodeHealthy(nodeID string) bool {
	fm.mu.RLock()
	defer fm.mu.RUnlock()
	_, failed := fm.failedNodes[nodeID]
	return !failed
}

// Stop stops the failover manager
func (fm *FailoverManager) Stop() {
	close(fm.stopCh)
	fm.wg.Wait()
}
