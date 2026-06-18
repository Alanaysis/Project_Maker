package game

import (
	"testing"
)

func TestWorldAddPlayer(t *testing.T) {
	world := NewWorld(2000, 2000)
	player := NewPlayer(1, "TestPlayer", Vector2{X: 100, Y: 100})

	err := world.AddPlayer(player)
	if err != nil {
		t.Fatalf("AddPlayer failed: %v", err)
	}

	if world.GetPlayerCount() != 1 {
		t.Errorf("Player count = %d, want 1", world.GetPlayerCount())
	}
}

func TestWorldAddDuplicatePlayer(t *testing.T) {
	world := NewWorld(2000, 2000)
	player1 := NewPlayer(1, "Player1", Vector2{X: 100, Y: 100})
	player2 := NewPlayer(1, "Player2", Vector2{X: 200, Y: 200})

	world.AddPlayer(player1)
	err := world.AddPlayer(player2)

	if err == nil {
		t.Error("Expected error when adding duplicate player")
	}
}

func TestWorldRemovePlayer(t *testing.T) {
	world := NewWorld(2000, 2000)
	player := NewPlayer(1, "TestPlayer", Vector2{X: 100, Y: 100})

	world.AddPlayer(player)
	world.RemovePlayer(1)

	if world.GetPlayerCount() != 0 {
		t.Errorf("Player count = %d, want 0", world.GetPlayerCount())
	}
}

func TestWorldGetPlayer(t *testing.T) {
	world := NewWorld(2000, 2000)
	player := NewPlayer(1, "TestPlayer", Vector2{X: 100, Y: 100})

	world.AddPlayer(player)

	got := world.GetPlayer(1)
	if got == nil {
		t.Fatal("GetPlayer returned nil")
	}

	if got.ID != 1 {
		t.Errorf("Player ID = %d, want 1", got.ID)
	}
}

func TestWorldUpdate(t *testing.T) {
	world := NewWorld(2000, 2000)
	player := NewPlayer(1, "TestPlayer", Vector2{X: 100, Y: 100})
	player.Velocity = Vector2{X: 100, Y: 0} // 向右移动

	world.AddPlayer(player)

	// 更新 1 秒
	world.Update(1.0)

	got := world.GetPlayer(1)
	if got.Position.X < 199 || got.Position.X > 201 {
		t.Errorf("Position X = %.1f, want ~200", got.Position.X)
	}
}

func TestWorldBoundary(t *testing.T) {
	world := NewWorld(100, 100)
	player := NewPlayer(1, "TestPlayer", Vector2{X: 50, Y: 50})
	player.Velocity = Vector2{X: 1000, Y: 1000} // 高速移动

	world.AddPlayer(player)

	// 更新应该被边界限制
	world.Update(1.0)

	got := world.GetPlayer(1)
	if got.Position.X > 100 || got.Position.Y > 100 {
		t.Errorf("Player out of bounds: (%.1f, %.1f)", got.Position.X, got.Position.Y)
	}
}

func TestWorldCombat(t *testing.T) {
	world := NewWorld(2000, 2000)

	attacker := NewPlayer(1, "Attacker", Vector2{X: 100, Y: 100})
	attacker.Action = ActionAttack
	attacker.AttackRange = 50

	target := NewPlayer(2, "Target", Vector2{X: 120, Y: 100})
	target.Health = 100

	world.AddPlayer(attacker)
	world.AddPlayer(target)

	// 处理战斗
	world.processCombat()

	// 目标应该受到伤害
	if target.Health >= 100 {
		t.Errorf("Target health = %d, want < 100", target.Health)
	}
}

func TestWorldGetSnapshot(t *testing.T) {
	world := NewWorld(2000, 2000)

	player1 := NewPlayer(1, "Player1", Vector2{X: 100, Y: 100})
	player2 := NewPlayer(2, "Player2", Vector2{X: 200, Y: 200})

	world.AddPlayer(player1)
	world.AddPlayer(player2)

	snapshot := world.GetSnapshot()

	if len(snapshot) != 2 {
		t.Errorf("Snapshot size = %d, want 2", len(snapshot))
	}

	if _, exists := snapshot[1]; !exists {
		t.Error("Player 1 not in snapshot")
	}
	if _, exists := snapshot[2]; !exists {
		t.Error("Player 2 not in snapshot")
	}
}
