package prediction

import (
	"sync"

	"github.com/distributed-game-system/internal/game"
)

// ⭐ 客户端预测 (Client Prediction)
//
// 核心思想：客户端在发送输入后立即在本地模拟结果，无需等待服务器确认。
//
// 优点：
//   - 大幅降低感知延迟
//   - 提升玩家体验
//
// 缺点：
//   - 可能导致预测错误
//   - 需要服务器校正机制
//
// 时间线:
//   Client:  输入 → 预测状态 → 显示 → 收到服务器确认 → 校正
//   Server:      → 收到输入 → 计算权威状态 → 发送确认

// BufferedInput 缓冲的输入
type BufferedInput struct {
	Sequence    uint32
	Input       game.PlayerInput
	Predicted   game.PlayerState // 输入后的预测状态
	Timestamp   int64
}

// Predictor 客户端预测器
type Predictor struct {
	mu sync.Mutex

	// 输入缓冲区
	// 💡 为什么需要缓冲？
	// 保存所有未确认的输入，当收到服务器状态时可以重新应用
	inputBuffer []BufferedInput

	// 最大缓冲大小
	maxBufferSize int

	// 服务器最后确认的序列号
	lastAckSequence uint32
}

// NewPredictor 创建预测器
func NewPredictor(maxBufferSize int) *Predictor {
	return &Predictor{
		inputBuffer:   make([]BufferedInput, 0, maxBufferSize),
		maxBufferSize: maxBufferSize,
	}
}

// Predict 根据输入预测新状态
func (p *Predictor) Predict(input game.PlayerInput, currentState game.PlayerState) game.PlayerState {
	p.mu.Lock()
	defer p.mu.Unlock()

	// 预测新状态
	predicted := currentState

	// 应用移动
	if input.MoveX != 0 || input.MoveY != 0 {
		moveDir := game.Vector2{X: input.MoveX, Y: input.MoveY}
		// 归一化
		length := moveDir.Length()
		if length > 0 {
			moveDir = game.Vector2{X: moveDir.X / length, Y: moveDir.Y / length}
		}
		predicted.Velocity = moveDir.Scale(game.MoveSpeed)
		predicted.Action = game.ActionMove
	} else {
		predicted.Velocity = game.Vector2{}
		if predicted.Action == game.ActionMove {
			predicted.Action = game.ActionNone
		}
	}

	// 应用朝向
	predicted.Direction = input.ViewAngle

	// 处理攻击预测
	if input.Attack {
		predicted.Action = game.ActionAttack
	}

	// 保存到缓冲区
	buffered := BufferedInput{
		Sequence:  input.Sequence,
		Input:     input,
		Predicted: predicted,
		Timestamp: input.Timestamp,
	}

	p.inputBuffer = append(p.inputBuffer, buffered)

	// 限制缓冲区大小
	if len(p.inputBuffer) > p.maxBufferSize {
		p.inputBuffer = p.inputBuffer[1:]
	}

	return predicted
}

// AcknowledgeInputs 确认服务器已处理的输入
func (p *Predictor) AcknowledgeInputs(lastProcessedSeq uint32) {
	p.mu.Lock()
	defer p.mu.Unlock()

	p.lastAckSequence = lastProcessedSeq

	// 移除已确认的输入
	ackIndex := -1
	for i, buffered := range p.inputBuffer {
		if buffered.Sequence <= lastProcessedSeq {
			ackIndex = i
		}
	}

	if ackIndex >= 0 {
		p.inputBuffer = p.inputBuffer[ackIndex+1:]
	}
}

// GetPendingInputs 获取未确认的输入
func (p *Predictor) GetPendingInputs() []game.PlayerInput {
	p.mu.Lock()
	defer p.mu.Unlock()

	inputs := make([]game.PlayerInput, 0, len(p.inputBuffer))
	for _, buffered := range p.inputBuffer {
		inputs = append(inputs, buffered.Input)
	}
	return inputs
}

// GetLastAckSequence 获取最后确认的序列号
func (p *Predictor) GetLastAckSequence() uint32 {
	p.mu.Lock()
	defer p.mu.Unlock()
	return p.lastAckSequence
}

// GetPendingCount 获取未确认输入数量
func (p *Predictor) GetPendingCount() int {
	p.mu.Lock()
	defer p.mu.Unlock()
	return len(p.inputBuffer)
}
