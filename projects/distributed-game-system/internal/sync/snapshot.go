package sync

import (
	"sync"
	"time"

	"github.com/distributed-game-system/internal/game"
)

// SnapshotManager 管理世界状态快照
type SnapshotManager struct {
	mu sync.RWMutex

	snapshots    []WorldSnapshot
	maxSnapshots int
	currentTick  uint32
}

// WorldSnapshot 世界快照
type WorldSnapshot struct {
	Tick      uint32
	Timestamp int64
	Players   map[uint32]game.PlayerState
}

// PlayerDelta 玩家状态增量
type PlayerDelta struct {
	ID       uint32
	Position *game.Vector2
	Velocity *game.Vector2
	Health   *int32
	Action   *game.Action
}

// DeltaSnapshot 增量快照
type DeltaSnapshot struct {
	BaseTick uint32
	Tick     uint32
	Players  map[uint32]PlayerDelta
}

// NewSnapshotManager 创建快照管理器
func NewSnapshotManager(maxSnapshots int) *SnapshotManager {
	return &SnapshotManager{
		snapshots:    make([]WorldSnapshot, 0, maxSnapshots),
		maxSnapshots: maxSnapshots,
	}
}

// TakeSnapshot 创建世界快照
func (m *SnapshotManager) TakeSnapshot(players map[uint32]game.PlayerState) WorldSnapshot {
	m.mu.Lock()
	defer m.mu.Unlock()

	m.currentTick++

	snapshot := WorldSnapshot{
		Tick:      m.currentTick,
		Timestamp: time.Now().UnixMilli(),
		Players:   players,
	}

	// 保存快照
	m.snapshots = append(m.snapshots, snapshot)

	// 限制快照数量
	if len(m.snapshots) > m.maxSnapshots {
		m.snapshots = m.snapshots[1:]
	}

	return snapshot
}

// GetSnapshot 获取指定帧的快照
func (m *SnapshotManager) GetSnapshot(tick uint32) *WorldSnapshot {
	m.mu.RLock()
	defer m.mu.RUnlock()

	for i := len(m.snapshots) - 1; i >= 0; i-- {
		if m.snapshots[i].Tick == tick {
			return &m.snapshots[i]
		}
	}
	return nil
}

// GetLatestSnapshot 获取最新快照
func (m *SnapshotManager) GetLatestSnapshot() *WorldSnapshot {
	m.mu.RLock()
	defer m.mu.RUnlock()

	if len(m.snapshots) == 0 {
		return nil
	}
	return &m.snapshots[len(m.snapshots)-1]
}

// GetPreviousSnapshot 获取上一个快照（用于插值）
func (m *SnapshotManager) GetPreviousSnapshot(currentTick uint32) *WorldSnapshot {
	m.mu.RLock()
	defer m.mu.RUnlock()

	for i := len(m.snapshots) - 1; i >= 0; i-- {
		if m.snapshots[i].Tick < currentTick {
			return &m.snapshots[i]
		}
	}
	return nil
}

// CalculateDelta 计算两个快照之间的增量
func (m *SnapshotManager) CalculateDelta(baseTick, currentTick uint32) *DeltaSnapshot {
	m.mu.RLock()
	defer m.mu.RUnlock()

	base := m.findSnapshot(baseTick)
	current := m.findSnapshot(currentTick)

	if base == nil || current == nil {
		return nil
	}

	delta := &DeltaSnapshot{
		BaseTick: baseTick,
		Tick:     currentTick,
		Players:  make(map[uint32]PlayerDelta),
	}

	// 检查每个玩家的变化
	for id, currState := range current.Players {
		baseState, exists := base.Players[id]

		if !exists {
			// 新玩家
			delta.Players[id] = PlayerDelta{
			ID:       id,
			Position: &currState.Position,
			Velocity: &currState.Velocity,
			Health:   &currState.Health,
			Action:   &currState.Action,
		}
			continue
		}

		// 检查是否有变化
		d := PlayerDelta{ID: id}
		changed := false

		if !baseState.Position.Equals(currState.Position, 0.01) {
			d.Position = &currState.Position
			changed = true
		}
		if !baseState.Velocity.Equals(currState.Velocity, 0.01) {
			d.Velocity = &currState.Velocity
			changed = true
		}
		if baseState.Health != currState.Health {
			d.Health = &currState.Health
			changed = true
		}
		if baseState.Action != currState.Action {
			d.Action = &currState.Action
			changed = true
		}

		if changed {
			delta.Players[id] = d
		}
	}

	return delta
}

// findSnapshot 查找指定帧的快照
func (m *SnapshotManager) findSnapshot(tick uint32) *WorldSnapshot {
	for i := len(m.snapshots) - 1; i >= 0; i-- {
		if m.snapshots[i].Tick == tick {
			return &m.snapshots[i]
		}
	}
	return nil
}

// GetCurrentTick 获取当前帧号
func (m *SnapshotManager) GetCurrentTick() uint32 {
	m.mu.RLock()
	defer m.mu.RUnlock()
	return m.currentTick
}
