package sync

import (
	"testing"

	"github.com/distributed-game-system/internal/game"
)

func TestInterpolatorAddSnapshot(t *testing.T) {
	interp := NewInterpolator(100, 10)

	players := map[uint32]game.PlayerState{
		1: {
			ID:       1,
			Position: game.Vector2{X: 100, Y: 100},
			Health:   100,
		},
	}

	interp.AddSnapshot(players)

	if interp.GetSnapshotCount() != 1 {
		t.Errorf("Snapshot count = %d, want 1", interp.GetSnapshotCount())
	}
}

func TestInterpolatorMultipleSnapshots(t *testing.T) {
	interp := NewInterpolator(100, 10)

	for i := 0; i < 5; i++ {
		players := map[uint32]game.PlayerState{
			1: {
				ID:       1,
				Position: game.Vector2{X: float64(i * 100), Y: 100},
				Health:   100,
			},
		}
		interp.AddSnapshot(players)
	}

	if interp.GetSnapshotCount() != 5 {
		t.Errorf("Snapshot count = %d, want 5", interp.GetSnapshotCount())
	}
}

func TestInterpolatorMaxBuffer(t *testing.T) {
	interp := NewInterpolator(100, 3) // 只保留 3 个快照

	for i := 0; i < 5; i++ {
		players := map[uint32]game.PlayerState{
			1: {
				ID:       1,
				Position: game.Vector2{X: float64(i * 100), Y: 100},
				Health:   100,
			},
		}
		interp.AddSnapshot(players)
	}

	if interp.GetSnapshotCount() != 3 {
		t.Errorf("Snapshot count = %d, want 3", interp.GetSnapshotCount())
	}
}

func TestInterpolatorInterpolate(t *testing.T) {
	interp := NewInterpolator(100, 10)

	// 添加两个快照
	players1 := map[uint32]game.PlayerState{
		1: {
			ID:       1,
			Position: game.Vector2{X: 100, Y: 100},
			Health:   100,
		},
	}
	interp.AddSnapshot(players1)

	players2 := map[uint32]game.PlayerState{
		1: {
			ID:       1,
			Position: game.Vector2{X: 200, Y: 100},
			Health:   100,
		},
	}
	interp.AddSnapshot(players2)

	// 插值应该返回一个状态
	result := interp.Interpolate(1)
	if result == nil {
		t.Fatal("Interpolate returned nil")
	}

	// 位置应该在两个快照之间
	if result.Position.X < 100 || result.Position.X > 200 {
		t.Errorf("Position X = %.1f, want between 100 and 200", result.Position.X)
	}
}

func TestInterpolatorInterpolateNotEnoughSnapshots(t *testing.T) {
	interp := NewInterpolator(100, 10)

	// 只有一个快照
	players := map[uint32]game.PlayerState{
		1: {
			ID:       1,
			Position: game.Vector2{X: 100, Y: 100},
			Health:   100,
		},
	}
	interp.AddSnapshot(players)

	// 插值应该返回最新状态
	result := interp.Interpolate(1)
	if result == nil {
		t.Fatal("Interpolate returned nil")
	}

	if result.Position.X != 100 {
		t.Errorf("Position X = %.1f, want 100", result.Position.X)
	}
}

func TestInterpolatorInterpolatePlayerNotFound(t *testing.T) {
	interp := NewInterpolator(100, 10)

	players := map[uint32]game.PlayerState{
		1: {
			ID:       1,
			Position: game.Vector2{X: 100, Y: 100},
			Health:   100,
		},
	}
	interp.AddSnapshot(players)
	interp.AddSnapshot(players)

	// 请求不存在的玩家
	result := interp.Interpolate(999)
	if result != nil {
		t.Error("Interpolate should return nil for non-existent player")
	}
}
