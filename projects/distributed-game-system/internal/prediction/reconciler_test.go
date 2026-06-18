package prediction

import (
	"math"
	"testing"

	"github.com/distributed-game-system/internal/game"
)

func TestReconcilerBasic(t *testing.T) {
	reconciler := NewReconciler(0.1)

	// 服务器权威状态
	serverState := game.PlayerState{
		ID:       1,
		Position: game.Vector2{X: 100, Y: 100},
		Velocity: game.Vector2{X: 0, Y: 0},
		Health:   100,
	}

	// 没有待处理输入
	pendingInputs := []game.PlayerInput{}

	// 当前状态
	currentState := game.PlayerState{
		ID:       1,
		Position: game.Vector2{X: 150, Y: 100}, // 客户端预测了更远的位置
		Velocity: game.Vector2{X: 100, Y: 0},
	}

	// 校正
	result := reconciler.Reconcile(serverState, pendingInputs, currentState)

	// 结果应该在当前状态和服务器状态之间（平滑）
	if result.Position.X < 100 || result.Position.X > 150 {
		t.Errorf("Position X = %.1f, want between 100 and 150", result.Position.X)
	}
}

func TestReconcilerWithPendingInputs(t *testing.T) {
	reconciler := NewReconciler(1.0) // 完全校正

	// 服务器状态（基于输入 1）
	serverState := game.PlayerState{
		ID:       1,
		Position: game.Vector2{X: 200, Y: 100},
		Velocity: game.Vector2{X: 100, Y: 0},
	}

	// 未确认的输入 2
	pendingInputs := []game.PlayerInput{
		{
			Sequence: 2,
			MoveX:    1.0,
			MoveY:    0.0,
		},
	}

	// 当前状态
	currentState := game.PlayerState{
		ID:       1,
		Position: game.Vector2{X: 350, Y: 100},
	}

	// 校正
	result := reconciler.Reconcile(serverState, pendingInputs, currentState)

	// 应该应用了待处理输入
	// 服务器状态 + 输入2的效果
	if result.Velocity.X <= 0 {
		t.Errorf("Velocity X = %.1f, want > 0 (input should be applied)", result.Velocity.X)
	}
}

func TestReconcilerSmoothing(t *testing.T) {
	// 测试不同的平滑系数
	testCases := []struct {
		smoothing float64
		name      string
	}{
		{0.1, "low"},
		{0.5, "medium"},
		{1.0, "high"},
	}

	for _, tc := range testCases {
		t.Run(tc.name, func(t *testing.T) {
			reconciler := NewReconciler(tc.smoothing)

			serverState := game.PlayerState{
				ID:       1,
				Position: game.Vector2{X: 100, Y: 100},
			}

			currentState := game.PlayerState{
				ID:       1,
				Position: game.Vector2{X: 200, Y: 100},
			}

			result := reconciler.Reconcile(serverState, []game.PlayerInput{}, currentState)

			// 计算期望位置
			expectedX := 200.0 + (100.0-200.0)*tc.smoothing
			if math.Abs(result.Position.X-expectedX) > 1.0 {
				t.Errorf("Position X = %.1f, want %.1f", result.Position.X, expectedX)
			}
		})
	}
}

func TestReconcilerSetSmoothing(t *testing.T) {
	reconciler := NewReconciler(0.1)

	// 设置新值
	reconciler.SetCorrectionSmoothing(0.5)
	if reconciler.GetCorrectionSmoothing() != 0.5 {
		t.Errorf("Smoothing = %.1f, want 0.5", reconciler.GetCorrectionSmoothing())
	}

	// 无效值应该被忽略
	reconciler.SetCorrectionSmoothing(1.5)
	if reconciler.GetCorrectionSmoothing() != 0.5 {
		t.Errorf("Smoothing = %.1f, want 0.5 (invalid value should be ignored)", reconciler.GetCorrectionSmoothing())
	}

	reconciler.SetCorrectionSmoothing(-0.1)
	if reconciler.GetCorrectionSmoothing() != 0.5 {
		t.Errorf("Smoothing = %.1f, want 0.5 (invalid value should be ignored)", reconciler.GetCorrectionSmoothing())
	}
}
