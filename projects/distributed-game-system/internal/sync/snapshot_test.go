package sync

import (
	"testing"

	"github.com/distributed-game-system/internal/game"
)

func TestSnapshotManagerTakeSnapshot(t *testing.T) {
	mgr := NewSnapshotManager(100)

	players := map[uint32]game.PlayerState{
		1: {
			ID:       1,
			Position: game.Vector2{X: 100, Y: 100},
			Health:   100,
		},
	}

	snapshot := mgr.TakeSnapshot(players)

	if snapshot.Tick != 1 {
		t.Errorf("Tick = %d, want 1", snapshot.Tick)
	}

	if len(snapshot.Players) != 1 {
		t.Errorf("Players count = %d, want 1", len(snapshot.Players))
	}
}

func TestSnapshotManagerMultipleSnapshots(t *testing.T) {
	mgr := NewSnapshotManager(100)

	players := map[uint32]game.PlayerState{
		1: {
			ID:       1,
			Position: game.Vector2{X: 100, Y: 100},
			Health:   100,
		},
	}

	// 创建多个快照
	for i := 0; i < 5; i++ {
		mgr.TakeSnapshot(players)
	}

	if mgr.GetCurrentTick() != 5 {
		t.Errorf("Current tick = %d, want 5", mgr.GetCurrentTick())
	}
}

func TestSnapshotManagerGetSnapshot(t *testing.T) {
	mgr := NewSnapshotManager(100)

	players := map[uint32]game.PlayerState{
		1: {
			ID:       1,
			Position: game.Vector2{X: 100, Y: 100},
			Health:   100,
		},
	}

	mgr.TakeSnapshot(players)

	snapshot := mgr.GetSnapshot(1)
	if snapshot == nil {
		t.Fatal("GetSnapshot returned nil")
	}

	if snapshot.Tick != 1 {
		t.Errorf("Tick = %d, want 1", snapshot.Tick)
	}
}

func TestSnapshotManagerGetLatestSnapshot(t *testing.T) {
	mgr := NewSnapshotManager(100)

	players := map[uint32]game.PlayerState{
		1: {
			ID:       1,
			Position: game.Vector2{X: 100, Y: 100},
			Health:   100,
		},
	}

	mgr.TakeSnapshot(players)
	mgr.TakeSnapshot(players)

	latest := mgr.GetLatestSnapshot()
	if latest == nil {
		t.Fatal("GetLatestSnapshot returned nil")
	}

	if latest.Tick != 2 {
		t.Errorf("Tick = %d, want 2", latest.Tick)
	}
}

func TestSnapshotManagerCalculateDelta(t *testing.T) {
	mgr := NewSnapshotManager(100)

	// 快照 1
	players1 := map[uint32]game.PlayerState{
		1: {
			ID:       1,
			Position: game.Vector2{X: 100, Y: 100},
			Health:   100,
		},
	}
	mgr.TakeSnapshot(players1)

	// 快照 2（位置变化）
	players2 := map[uint32]game.PlayerState{
		1: {
			ID:       1,
			Position: game.Vector2{X: 200, Y: 100}, // X 变化了
			Health:   100,
		},
	}
	mgr.TakeSnapshot(players2)

	// 计算增量
	delta := mgr.CalculateDelta(1, 2)
	if delta == nil {
		t.Fatal("CalculateDelta returned nil")
	}

	if delta.BaseTick != 1 {
		t.Errorf("BaseTick = %d, want 1", delta.BaseTick)
	}

	if delta.Tick != 2 {
		t.Errorf("Tick = %d, want 2", delta.Tick)
	}

	if len(delta.Players) != 1 {
		t.Errorf("Delta players count = %d, want 1", len(delta.Players))
	}
}

func TestSnapshotManagerCalculateDeltaNoChange(t *testing.T) {
	mgr := NewSnapshotManager(100)

	players := map[uint32]game.PlayerState{
		1: {
			ID:       1,
			Position: game.Vector2{X: 100, Y: 100},
			Health:   100,
		},
	}

	mgr.TakeSnapshot(players)
	mgr.TakeSnapshot(players)

	// 没有变化，增量应该为空
	delta := mgr.CalculateDelta(1, 2)
	if delta == nil {
		t.Fatal("CalculateDelta returned nil")
	}

	if len(delta.Players) != 0 {
		t.Errorf("Delta players count = %d, want 0", len(delta.Players))
	}
}

func TestSnapshotManagerMaxSnapshots(t *testing.T) {
	mgr := NewSnapshotManager(3) // 只保留 3 个快照

	players := map[uint32]game.PlayerState{
		1: {
			ID:       1,
			Position: game.Vector2{X: 100, Y: 100},
			Health:   100,
		},
	}

	// 创建 5 个快照
	for i := 0; i < 5; i++ {
		mgr.TakeSnapshot(players)
	}

	// 早期的快照应该被删除
	snapshot := mgr.GetSnapshot(1)
	if snapshot != nil {
		t.Error("Old snapshot should be deleted")
	}

	// 最新的应该还在
	snapshot = mgr.GetSnapshot(5)
	if snapshot == nil {
		t.Error("Latest snapshot should exist")
	}
}
