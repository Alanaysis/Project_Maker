package prediction

import (
	"testing"

	"github.com/distributed-game-system/internal/game"
)

func TestPredictorPredict(t *testing.T) {
	predictor := NewPredictor(60)

	// 初始状态
	currentState := game.PlayerState{
		ID:       1,
		Position: game.Vector2{X: 100, Y: 100},
		Velocity: game.Vector2{X: 0, Y: 0},
		Health:   100,
	}

	// 输入：向右移动
	input := game.PlayerInput{
		Sequence:  1,
		MoveX:     1.0,
		MoveY:     0.0,
		Attack:    false,
		ViewAngle: 0,
	}

	predicted := predictor.Predict(input, currentState)

	// 预测后应该有向右的速度
	if predicted.Velocity.X <= 0 {
		t.Errorf("Velocity X = %.1f, want > 0", predicted.Velocity.X)
	}

	// 缓冲区应该有 1 个输入
	if predictor.GetPendingCount() != 1 {
		t.Errorf("Pending count = %d, want 1", predictor.GetPendingCount())
	}
}

func TestPredictorMultipleInputs(t *testing.T) {
	predictor := NewPredictor(60)

	currentState := game.PlayerState{
		ID:       1,
		Position: game.Vector2{X: 100, Y: 100},
	}

	// 发送多个输入
	for i := uint32(1); i <= 5; i++ {
		input := game.PlayerInput{
			Sequence: i,
			MoveX:    1.0,
		}
		predictor.Predict(input, currentState)
	}

	if predictor.GetPendingCount() != 5 {
		t.Errorf("Pending count = %d, want 5", predictor.GetPendingCount())
	}
}

func TestPredictorAcknowledge(t *testing.T) {
	predictor := NewPredictor(60)

	currentState := game.PlayerState{
		ID:       1,
		Position: game.Vector2{X: 100, Y: 100},
	}

	// 发送 5 个输入
	for i := uint32(1); i <= 5; i++ {
		input := game.PlayerInput{
			Sequence: i,
			MoveX:    1.0,
		}
		predictor.Predict(input, currentState)
	}

	// 确认前 3 个
	predictor.AcknowledgeInputs(3)

	if predictor.GetPendingCount() != 2 {
		t.Errorf("Pending count = %d, want 2", predictor.GetPendingCount())
	}

	if predictor.GetLastAckSequence() != 3 {
		t.Errorf("Last ack sequence = %d, want 3", predictor.GetLastAckSequence())
	}
}

func TestPredictorBufferOverflow(t *testing.T) {
	predictor := NewPredictor(10) // 小缓冲区

	currentState := game.PlayerState{
		ID:       1,
		Position: game.Vector2{X: 100, Y: 100},
	}

	// 发送超过缓冲区大小的输入
	for i := uint32(1); i <= 15; i++ {
		input := game.PlayerInput{
			Sequence: i,
			MoveX:    1.0,
		}
		predictor.Predict(input, currentState)
	}

	// 应该被限制在 10
	if predictor.GetPendingCount() != 10 {
		t.Errorf("Pending count = %d, want 10", predictor.GetPendingCount())
	}
}

func TestPredictorGetPendingInputs(t *testing.T) {
	predictor := NewPredictor(60)

	currentState := game.PlayerState{
		ID:       1,
		Position: game.Vector2{X: 100, Y: 100},
	}

	// 发送 3 个输入
	for i := uint32(1); i <= 3; i++ {
		input := game.PlayerInput{
			Sequence: i,
			MoveX:    float64(i),
		}
		predictor.Predict(input, currentState)
	}

	// 获取待处理输入
	pending := predictor.GetPendingInputs()
	if len(pending) != 3 {
		t.Errorf("Pending inputs count = %d, want 3", len(pending))
	}

	// 检查序列号
	for i, input := range pending {
		if input.Sequence != uint32(i+1) {
			t.Errorf("Input %d sequence = %d, want %d", i, input.Sequence, i+1)
		}
	}
}
