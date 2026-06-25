package deploy

import (
	"fmt"
	"sync"
	"time"
)

// RollbackManager 回滚管理器
type RollbackManager struct {
	maxVersions int                    // 每个环境保留的最大版本数
	snapshots   map[string][]*Snapshot // 环境 -> 版本快照列表
	mu          sync.RWMutex
}

// Snapshot 版本快照
type Snapshot struct {
	Version   string            `json:"version"`   // 版本号
	Timestamp int64             `json:"timestamp"` // 时间戳
	Config    map[string]string `json:"config"`    // 配置快照
}

// NewRollbackManager 创建回滚管理器
func NewRollbackManager(maxVersions int) *RollbackManager {
	return &RollbackManager{
		maxVersions: maxVersions,
		snapshots:   make(map[string][]*Snapshot),
	}
}

// SaveSnapshot 保存版本快照
func (rm *RollbackManager) SaveSnapshot(envName, version string) {
	rm.mu.Lock()
	defer rm.mu.Unlock()

	snapshot := &Snapshot{
		Version:   version,
		Timestamp: time.Now().UnixNano(),
		Config:    make(map[string]string),
	}

	snapshots := rm.snapshots[envName]
	snapshots = append(snapshots, snapshot)

	// 保持最大版本数限制
	if len(snapshots) > rm.maxVersions {
		snapshots = snapshots[len(snapshots)-rm.maxVersions:]
	}

	rm.snapshots[envName] = snapshots
}

// GetPreviousVersion 获取上一个版本
func (rm *RollbackManager) GetPreviousVersion(envName string) (string, error) {
	rm.mu.RLock()
	defer rm.mu.RUnlock()

	snapshots, ok := rm.snapshots[envName]
	if !ok || len(snapshots) < 2 {
		return "", fmt.Errorf("没有可回滚的版本")
	}

	// 返回倒数第二个版本（上一个版本）
	return snapshots[len(snapshots)-2].Version, nil
}

// GetVersionHistory 获取版本历史
func (rm *RollbackManager) GetVersionHistory(envName string) []string {
	rm.mu.RLock()
	defer rm.mu.RUnlock()

	snapshots, ok := rm.snapshots[envName]
	if !ok {
		return nil
	}

	versions := make([]string, len(snapshots))
	for i, s := range snapshots {
		versions[i] = s.Version
	}
	return versions
}

// ClearHistory 清除环境的历史记录
func (rm *RollbackManager) ClearHistory(envName string) {
	rm.mu.Lock()
	defer rm.mu.Unlock()
	delete(rm.snapshots, envName)
}
