package raft

import (
	"fmt"
	"log"
)

// ClusterManager manages cluster membership changes.
//
// Raft supports changing the cluster configuration (adding/removing
// servers) through a process called joint consistency.
//
// The key challenge: During a membership change, the cluster may
// temporarily have two different sets of servers. The algorithm
// must ensure safety during this transition.
//
// Raft's approach (Joint Consensus):
//   1. Transition to a joint configuration [configA, configB]
//   2. Both configurations must agree on commits
//   3. Transition to the new configuration [configB]
//
// This ensures that no committed entry is lost during the change.
type ClusterManager struct {
	// Current configuration
	currentConfig []int

	// Joint configuration during transition
	jointConfig [][2][]int

	// Cluster state
	clusterSize int
}

// NewClusterManager creates a new cluster manager.
func NewClusterManager(initialPeers map[int]string) *ClusterManager {
	config := make([]int, 0, len(initialPeers))
	for id := range initialPeers {
		config = append(config, id)
	}
	return &ClusterManager{
		currentConfig: config,
		clusterSize:   len(initialPeers),
	}
}

// AddPeer adds a new peer to the cluster.
//
// The process:
//   1. Leader creates a new configuration [current, current + newPeer]
//   2. Both configurations must agree on a leader
//   3. Once both agree, transition to the new configuration
func (cm *ClusterManager) AddPeer(peerID int) error {
	// Check if peer already exists
	for _, id := range cm.currentConfig {
		if id == peerID {
			return fmt.Errorf("peer %d already exists in cluster", peerID)
		}
	}

	// Create joint configuration
	cm.jointConfig = [][2][]int{
		{cm.currentConfig, append(append([]int{}, cm.currentConfig...), peerID)},
	}

	// Update current config
	cm.currentConfig = append(append([]int{}, cm.currentConfig...), peerID)
	cm.clusterSize++

	log.Printf("[CLUSTER] Added peer %d, new size: %d", peerID, cm.clusterSize)
	return nil
}

// RemovePeer removes a peer from the cluster.
//
// The process:
//   1. Leader creates a new configuration [current, current - peer]
//   2. Both configurations must agree on a leader
//   3. Once both agree, transition to the new configuration
func (cm *ClusterManager) RemovePeer(peerID int) error {
	// Check if peer exists
	found := false
	for _, id := range cm.currentConfig {
		if id == peerID {
			found = true
			break
		}
	}
	if !found {
		return fmt.Errorf("peer %d does not exist in cluster", peerID)
	}

	// Create joint configuration
	newConfig := make([]int, 0, len(cm.currentConfig)-1)
	for _, id := range cm.currentConfig {
		if id != peerID {
			newConfig = append(newConfig, id)
		}
	}
	cm.jointConfig = [][2][]int{
		{cm.currentConfig, newConfig},
	}

	// Update current config
	cm.currentConfig = newConfig
	cm.clusterSize--

	log.Printf("[CLUSTER] Removed peer %d, new size: %d", peerID, cm.clusterSize)
	return nil
}

// GetConfig returns the current cluster configuration.
func (cm *ClusterManager) GetConfig() []int {
	return cm.currentConfig
}

// GetClusterSize returns the current cluster size.
func (cm *ClusterManager) GetClusterSize() int {
	return cm.clusterSize
}

// HasMajority checks if the given set of peers has a majority.
func (cm *ClusterManager) HasMajority(peers []int) bool {
	majority := cm.clusterSize/2 + 1
	return len(peers) >= majority
}

// IsJoint checks if the cluster is in a joint configuration.
func (cm *ClusterManager) IsJoint() bool {
	return len(cm.jointConfig) > 0
}

// CompleteTransition completes a joint consensus transition.
func (cm *ClusterManager) CompleteTransition() {
	cm.jointConfig = nil
	log.Printf("[CLUSTER] Completed configuration transition")
}

// FormatClusterInfo formats cluster information for display.
func FormatClusterInfo(config []int, size int) string {
	return fmt.Sprintf("Cluster: size=%d, peers=%v", size, config)
}
