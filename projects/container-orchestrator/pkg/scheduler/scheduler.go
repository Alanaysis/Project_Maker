package scheduler

import (
	"errors"
	"math/rand"
	"sort"
	"sync"

	"github.com/container-orchestrator/pkg/container"
)

var (
	ErrNoAvailableNode = errors.New("no available node for scheduling")
	ErrInvalidContainer = errors.New("invalid container")
)

// SchedulerStrategy represents the scheduling strategy
type SchedulerStrategy string

const (
	StrategyBinPacking   SchedulerStrategy = "bin_packing"
	StrategySpread       SchedulerStrategy = "spread"
	StrategyRoundRobin   SchedulerStrategy = "round_robin"
	StrategyRandom       SchedulerStrategy = "random"
	StrategyResourceAware SchedulerStrategy = "resource_aware"
	StrategyAffinity     SchedulerStrategy = "affinity"
)

// Scheduler handles container scheduling
type Scheduler struct {
	mu        sync.RWMutex
	nodes     map[string]*container.Node
	containers map[string]*container.Container
	strategy  SchedulerStrategy
	rrIndex   int // For round-robin strategy
}

// NewScheduler creates a new scheduler
func NewScheduler(strategy SchedulerStrategy) *Scheduler {
	return &Scheduler{
		nodes:      make(map[string]*container.Node),
		containers: make(map[string]*container.Container),
		strategy:   strategy,
	}
}

// AddNode adds a node to the scheduler
func (s *Scheduler) AddNode(node *container.Node) {
	s.mu.Lock()
	defer s.mu.Unlock()
	s.nodes[node.ID] = node
}

// RemoveNode removes a node from the scheduler
func (s *Scheduler) RemoveNode(nodeID string) {
	s.mu.Lock()
	defer s.mu.Unlock()
	delete(s.nodes, nodeID)
}

// GetNode returns a node by ID
func (s *Scheduler) GetNode(nodeID string) (*container.Node, bool) {
	s.mu.RLock()
	defer s.mu.RUnlock()
	node, ok := s.nodes[nodeID]
	return node, ok
}

// GetNodes returns all nodes
func (s *Scheduler) GetNodes() []*container.Node {
	s.mu.RLock()
	defer s.mu.RUnlock()
	nodes := make([]*container.Node, 0, len(s.nodes))
	for _, node := range s.nodes {
		nodes = append(nodes, node)
	}
	return nodes
}

// Schedule schedules a container to a node
func (s *Scheduler) Schedule(c *container.Container) (*container.Node, error) {
	s.mu.Lock()
	defer s.mu.Unlock()

	if c == nil {
		return nil, ErrInvalidContainer
	}

	// Get available nodes
	availableNodes := s.getAvailableNodes(c)
	if len(availableNodes) == 0 {
		return nil, ErrNoAvailableNode
	}

	// Select node based on strategy
	var selectedNode *container.Node
	switch s.strategy {
	case StrategyBinPacking:
		selectedNode = s.binPacking(availableNodes, c)
	case StrategySpread:
		selectedNode = s.spread(availableNodes, c)
	case StrategyRoundRobin:
		selectedNode = s.roundRobin(availableNodes)
	case StrategyRandom:
		selectedNode = s.randomSelect(availableNodes)
	case StrategyResourceAware:
		selectedNode = s.resourceAware(availableNodes, c)
	case StrategyAffinity:
		selectedNode = s.affinity(availableNodes, c)
	default:
		selectedNode = s.binPacking(availableNodes, c)
	}

	// Assign container to node
	selectedNode.AddContainer(c.ID, c.Resources)
	c.NodeID = selectedNode.ID
	s.containers[c.ID] = c

	return selectedNode, nil
}

// Unschedule removes a container from its node
func (s *Scheduler) Unschedule(containerID string) error {
	s.mu.Lock()
	defer s.mu.Unlock()

	c, ok := s.containers[containerID]
	if !ok {
		return errors.New("container not found")
	}

	node, ok := s.nodes[c.NodeID]
	if !ok {
		return errors.New("node not found")
	}

	node.RemoveContainer(containerID, c.Resources)
	delete(s.containers, containerID)
	c.NodeID = ""

	return nil
}

// GetContainer returns a container by ID
func (s *Scheduler) GetContainer(containerID string) (*container.Container, bool) {
	s.mu.RLock()
	defer s.mu.RUnlock()
	c, ok := s.containers[containerID]
	return c, ok
}

// GetContainers returns all containers
func (s *Scheduler) GetContainers() []*container.Container {
	s.mu.RLock()
	defer s.mu.RUnlock()
	containers := make([]*container.Container, 0, len(s.containers))
	for _, c := range s.containers {
		containers = append(containers, c)
	}
	return containers
}

// GetContainersByNode returns containers on a specific node
func (s *Scheduler) GetContainersByNode(nodeID string) []*container.Container {
	s.mu.RLock()
	defer s.mu.RUnlock()
	var containers []*container.Container
	for _, c := range s.containers {
		if c.NodeID == nodeID {
			containers = append(containers, c)
		}
	}
	return containers
}

// getAvailableNodes returns nodes that can schedule the container
func (s *Scheduler) getAvailableNodes(c *container.Container) []*container.Node {
	var available []*container.Node
	for _, node := range s.nodes {
		if node.CanSchedule(c) {
			available = append(available, node)
		}
	}
	return available
}

// binPacking selects the node with most available resources (pack tightly)
func (s *Scheduler) binPacking(nodes []*container.Node, c *container.Container) *container.Node {
	sort.Slice(nodes, func(i, j int) bool {
		resI := nodes[i].AvailableResources()
		resJ := nodes[j].AvailableResources()
		// Sort by least available resources (pack tightly)
		return resI.CPU < resJ.CPU
	})
	return nodes[0]
}

// spread selects the node with least containers (spread evenly)
func (s *Scheduler) spread(nodes []*container.Node, c *container.Container) *container.Node {
	sort.Slice(nodes, func(i, j int) bool {
		return len(nodes[i].Containers) < len(nodes[j].Containers)
	})
	return nodes[0]
}

// roundRobin selects nodes in round-robin fashion
func (s *Scheduler) roundRobin(nodes []*container.Node) *container.Node {
	if len(nodes) == 0 {
		return nil
	}
	selected := nodes[s.rrIndex%len(nodes)]
	s.rrIndex++
	return selected
}

// randomSelect selects a node randomly
func (s *Scheduler) randomSelect(nodes []*container.Node) *container.Node {
	if len(nodes) == 0 {
		return nil
	}
	return nodes[rand.Intn(len(nodes))]
}

// resourceAware selects the node with the most available resources relative to the container's needs
func (s *Scheduler) resourceAware(nodes []*container.Node, c *container.Container) *container.Node {
	if len(nodes) == 0 {
		return nil
	}
	// Score each node based on resource fit
	type nodeScore struct {
		node  *container.Node
		score float64
	}
	scores := make([]nodeScore, 0, len(nodes))
	for _, node := range nodes {
		avail := node.AvailableResources()
		// Score: higher is better - considers how well the container fits
		cpuRatio := avail.CPU / (c.Resources.CPU + 0.001)
		memRatio := float64(avail.Memory) / float64(c.Resources.Memory+1)
		// Prefer nodes where resources are balanced relative to demand
		score := (cpuRatio + memRatio) / 2.0
		scores = append(scores, nodeScore{node: node, score: score})
	}
	sort.Slice(scores, func(i, j int) bool {
		return scores[i].score > scores[j].score
	})
	return scores[0].node
}

// affinity selects nodes based on label affinity with the container
func (s *Scheduler) affinity(nodes []*container.Node, c *container.Container) *container.Node {
	if len(nodes) == 0 {
		return nil
	}
	// Score nodes based on label matching with container labels
	type nodeScore struct {
		node  *container.Node
		score int
	}
	scores := make([]nodeScore, 0, len(nodes))
	for _, node := range nodes {
		score := 0
		for k, v := range c.Labels {
			if nodeVal, ok := node.Labels[k]; ok && nodeVal == v {
				score++
			}
		}
		scores = append(scores, nodeScore{node: node, score: score})
	}
	sort.Slice(scores, func(i, j int) bool {
		return scores[i].score > scores[j].score
	})
	// If no affinity match, fall back to spread
	if scores[0].score == 0 {
		return s.spread(nodes, c)
	}
	return scores[0].node
}

// GetClusterStats returns cluster statistics
func (s *Scheduler) GetClusterStats() ClusterStats {
	s.mu.RLock()
	defer s.mu.RUnlock()

	stats := ClusterStats{
		TotalNodes: len(s.nodes),
		TotalContainers: len(s.containers),
	}

	for _, node := range s.nodes {
		stats.TotalCPU += node.Resources.CPU
		stats.UsedCPU += node.Used.CPU
		stats.TotalMemory += node.Resources.Memory
		stats.UsedMemory += node.Used.Memory

		if node.State == container.NodeReady {
			stats.ReadyNodes++
		}
	}

	for _, c := range s.containers {
		switch c.GetState() {
		case container.StateRunning:
			stats.RunningContainers++
		case container.StatePending:
			stats.PendingContainers++
		case container.StateFailed:
			stats.FailedContainers++
		}
	}

	return stats
}

// ClusterStats represents cluster statistics
type ClusterStats struct {
	TotalNodes       int     `json:"total_nodes"`
	ReadyNodes       int     `json:"ready_nodes"`
	TotalContainers  int     `json:"total_containers"`
	RunningContainers int    `json:"running_containers"`
	PendingContainers int    `json:"pending_containers"`
	FailedContainers  int    `json:"failed_containers"`
	TotalCPU         float64 `json:"total_cpu"`
	UsedCPU          float64 `json:"used_cpu"`
	TotalMemory      int64   `json:"total_memory"`
	UsedMemory       int64   `json:"used_memory"`
}
