package resource

import (
	"fmt"
	"sync"

	"github.com/hpc-scheduler/internal/config"
	"github.com/hpc-scheduler/pkg/models"
)

// ResourceManager 资源管理器
// ⭐ 重点：资源管理是 HPC 调度系统的核心
// 负责跟踪和分配集群资源(CPU、内存)
type ResourceManager struct {
	mu sync.RWMutex

	// 总资源
	totalCPU      int
	totalMemoryMB int

	// 已分配资源
	usedCPU      int
	usedMemoryMB int

	// 资源分配映射: taskID -> ResourceRequest
	allocations map[string]models.ResourceRequest

	// 节点管理
	nodes map[string]*models.Node
}

// NewResourceManager 创建资源管理器
func NewResourceManager(cfg config.ResourceConfig) *ResourceManager {
	rm := &ResourceManager{
		totalCPU:      cfg.TotalCPU,
		totalMemoryMB: cfg.TotalMemoryMB,
		allocations:   make(map[string]models.ResourceRequest),
		nodes:         make(map[string]*models.Node),
	}

	// 创建默认节点
	rm.nodes["local"] = &models.Node{
		ID:       "local",
		Hostname: "localhost",
		TotalResources: models.ResourceRequest{
			CPU:      cfg.TotalCPU,
			MemoryMB: cfg.TotalMemoryMB,
		},
		State: models.NodeStateIdle,
	}

	return rm
}

// Allocate 分配资源给任务
// ⭐ 重点：原子性分配，要么全部成功，要么全部失败
func (rm *ResourceManager) Allocate(taskID string, req models.ResourceRequest) error {
	rm.mu.Lock()
	defer rm.mu.Unlock()

	// 检查是否有足够资源
	if rm.usedCPU+req.CPU > rm.totalCPU {
		return fmt.Errorf("insufficient CPU: available %d, requested %d",
			rm.totalCPU-rm.usedCPU, req.CPU)
	}
	if rm.usedMemoryMB+req.MemoryMB > rm.totalMemoryMB {
		return fmt.Errorf("insufficient memory: available %dMB, requested %dMB",
			rm.totalMemoryMB-rm.usedMemoryMB, req.MemoryMB)
	}

	// 分配资源
	rm.usedCPU += req.CPU
	rm.usedMemoryMB += req.MemoryMB
	rm.allocations[taskID] = req

	// 更新节点状态
	rm.updateNodeState()

	return nil
}

// Release 释放任务占用的资源
func (rm *ResourceManager) Release(taskID string) error {
	rm.mu.Lock()
	defer rm.mu.Unlock()

	req, ok := rm.allocations[taskID]
	if !ok {
		return fmt.Errorf("no allocation found for task: %s", taskID)
	}

	rm.usedCPU -= req.CPU
	rm.usedMemoryMB -= req.MemoryMB
	delete(rm.allocations, taskID)

	// 更新节点状态
	rm.updateNodeState()

	return nil
}

// CheckAvailable 检查是否有足够资源
func (rm *ResourceManager) CheckAvailable(req models.ResourceRequest) bool {
	rm.mu.RLock()
	defer rm.mu.RUnlock()

	return rm.usedCPU+req.CPU <= rm.totalCPU &&
		rm.usedMemoryMB+req.MemoryMB <= rm.totalMemoryMB
}

// GetAvailable 获取可用资源
func (rm *ResourceManager) GetAvailable() models.ResourceRequest {
	rm.mu.RLock()
	defer rm.mu.RUnlock()

	return models.ResourceRequest{
		CPU:      rm.totalCPU - rm.usedCPU,
		MemoryMB: rm.totalMemoryMB - rm.usedMemoryMB,
	}
}

// GetTotal 获取总资源
func (rm *ResourceManager) GetTotal() models.ResourceRequest {
	return models.ResourceRequest{
		CPU:      rm.totalCPU,
		MemoryMB: rm.totalMemoryMB,
	}
}

// GetUsed 获取已用资源
func (rm *ResourceManager) GetUsed() models.ResourceRequest {
	rm.mu.RLock()
	defer rm.mu.RUnlock()

	return models.ResourceRequest{
		CPU:      rm.usedCPU,
		MemoryMB: rm.usedMemoryMB,
	}
}

// GetClusterInfo 获取集群信息
func (rm *ResourceManager) GetClusterInfo() *models.ClusterInfo {
	rm.mu.RLock()
	defer rm.mu.RUnlock()

	return &models.ClusterInfo{
		TotalNodes: len(rm.nodes),
		TotalResources: models.ResourceRequest{
			CPU:      rm.totalCPU,
			MemoryMB: rm.totalMemoryMB,
		},
		UsedResources: models.ResourceRequest{
			CPU:      rm.usedCPU,
			MemoryMB: rm.usedMemoryMB,
		},
	}
}

// GetAllocation 获取任务的资源分配
func (rm *ResourceManager) GetAllocation(taskID string) (models.ResourceRequest, error) {
	rm.mu.RLock()
	defer rm.mu.RUnlock()

	req, ok := rm.allocations[taskID]
	if !ok {
		return models.ResourceRequest{}, fmt.Errorf("no allocation found for task: %s", taskID)
	}
	return req, nil
}

// updateNodeState 更新节点状态
func (rm *ResourceManager) updateNodeState() {
	node := rm.nodes["local"]
	if node == nil {
		return
	}

	node.UsedResources = models.ResourceRequest{
		CPU:      rm.usedCPU,
		MemoryMB: rm.usedMemoryMB,
	}

	if rm.usedCPU == 0 && rm.usedMemoryMB == 0 {
		node.State = models.NodeStateIdle
	} else if rm.usedCPU >= rm.totalCPU || rm.usedMemoryMB >= rm.totalMemoryMB {
		node.State = models.NodeStateBusy
	} else {
		node.State = models.NodeStateIdle
	}
}

// GetNode 获取节点信息
func (rm *ResourceManager) GetNode(nodeID string) (*models.Node, error) {
	rm.mu.RLock()
	defer rm.mu.RUnlock()

	node, ok := rm.nodes[nodeID]
	if !ok {
		return nil, fmt.Errorf("node not found: %s", nodeID)
	}
	return node, nil
}

// GetAllNodes 获取所有节点
func (rm *ResourceManager) GetAllNodes() []*models.Node {
	rm.mu.RLock()
	defer rm.mu.RUnlock()

	nodes := make([]*models.Node, 0, len(rm.nodes))
	for _, node := range rm.nodes {
		nodes = append(nodes, node)
	}
	return nodes
}
