package game

import (
	"testing"
)

func TestNewPlayer(t *testing.T) {
	player := NewPlayer(1, "TestPlayer", Vector2{X: 100, Y: 200})

	if player.ID != 1 {
		t.Errorf("ID = %d, want 1", player.ID)
	}
	if player.Name != "TestPlayer" {
		t.Errorf("Name = %s, want TestPlayer", player.Name)
	}
	if player.Health != 100 {
		t.Errorf("Health = %d, want 100", player.Health)
	}
}

func TestPlayerGetState(t *testing.T) {
	player := NewPlayer(1, "TestPlayer", Vector2{X: 100, Y: 200})
	player.Velocity = Vector2{X: 50, Y: 0}
	player.Health = 80

	state := player.GetState()

	if state.ID != 1 {
		t.Errorf("ID = %d, want 1", state.ID)
	}
	if state.Health != 80 {
		t.Errorf("Health = %d, want 80", state.Health)
	}
}

func TestPlayerApplyInputMove(t *testing.T) {
	player := NewPlayer(1, "TestPlayer", Vector2{X: 100, Y: 100})

	input := PlayerInput{
		Sequence: 1,
		MoveX:    1.0,
		MoveY:    0.0,
	}

	player.ApplyInput(input)

	// 应该有向右的速度
	if player.Velocity.X <= 0 {
		t.Errorf("Velocity X = %.1f, want > 0", player.Velocity.X)
	}

	if player.Action != ActionMove {
		t.Errorf("Action = %d, want ActionMove", player.Action)
	}
}

func TestPlayerApplyInputAttack(t *testing.T) {
	player := NewPlayer(1, "TestPlayer", Vector2{X: 100, Y: 100})

	input := PlayerInput{
		Sequence: 1,
		Attack:   true,
	}

	player.ApplyInput(input)

	if player.Action != ActionAttack {
		t.Errorf("Action = %d, want ActionAttack", player.Action)
	}
}

func TestPlayerTakeDamage(t *testing.T) {
	player := NewPlayer(1, "TestPlayer", Vector2{X: 100, Y: 100})

	player.TakeDamage(30)

	if player.Health != 70 {
		t.Errorf("Health = %d, want 70", player.Health)
	}
}

func TestPlayerDie(t *testing.T) {
	player := NewPlayer(1, "TestPlayer", Vector2{X: 100, Y: 100})

	player.TakeDamage(100)

	if player.Health != 0 {
		t.Errorf("Health = %d, want 0", player.Health)
	}

	if player.Action != ActionDie {
		t.Errorf("Action = %d, want ActionDie", player.Action)
	}

	if player.IsAlive() {
		t.Error("Player should be dead")
	}
}

func TestPlayerIsAlive(t *testing.T) {
	player := NewPlayer(1, "TestPlayer", Vector2{X: 100, Y: 100})

	if !player.IsAlive() {
		t.Error("Player should be alive")
	}

	player.TakeDamage(100)

	if player.IsAlive() {
		t.Error("Player should be dead")
	}
}

func TestPlayerUpdate(t *testing.T) {
	player := NewPlayer(1, "TestPlayer", Vector2{X: 100, Y: 100})
	player.Velocity = Vector2{X: 100, Y: 0}

	player.Update(0.1) // 100ms

	if player.Position.X < 109 || player.Position.X > 111 {
		t.Errorf("Position X = %.1f, want ~110", player.Position.X)
	}
}
