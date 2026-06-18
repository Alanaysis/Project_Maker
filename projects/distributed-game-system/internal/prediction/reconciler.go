package prediction

import (
	"sync"

	"github.com/distributed-game-system/internal/game"
)

// ⭐ 服务器校正 (Server Reconciliation)
//
// 核心问题：客户端预测可能与服务器权威状态不一致。
//
// 解决方案：当收到服务器状态时，从该状态重新应用所有未确认的输入。
//
// 时间线:
//   Client:  输入1 → 预测1 → 输入2 → 预测2 → 收到服务器确认(基于输入1)
//                ↓
//   校正:    以服务器状态为起点，重新应用输入2，得到校正后的状态
//
// 💡 关键点：
//   - 只重新应用未确认的输入
//   - 平滑过渡避免突变
//   - 使用序列号匹配输入

// Reconciler 服务器校正器
type Reconciler struct {
	mu sync.Mutex

	// 校正平滑系数 (0-1)
	// 💡 为什么需要平滑？
	// 直接跳到校正后的状态会导致画面突变
	// 平滑过渡让玩家感觉不到校正
	correctionSmoothing float64

	// 上一次校正的目标状态
	lastCorrection *game.PlayerState
}

// NewReconciler 创建校正器
func NewReconciler(smoothing float64) *Reconciler {
	if smoothing <= 0 || smoothing > 1 {
		smoothing = 0.1 // 默认 10% 平滑
	}
	return &Reconciler{
		correctionSmoothing: smoothing,
	}
}

// Reconcile 服务器校正
//
// 算法步骤：
// 1. 收到服务器权威状态 S_server
// 2. 移除已确认的输入
// 3. 从 S_server 开始，重新应用所有未确认的输入
// 4. 得到校正后的状态 S_corrected
// 5. 平滑过渡到 S_corrected
//
// 参数：
//   - serverState: 服务器权威状态
//   - pendingInputs: 未确认的输入列表
//   - currentState: 当前客户端状态（用于平滑）
//
// 返回：
//   - 校正后的状态
func (r *Reconciler) Reconcile(
	serverState game.PlayerState,
	pendingInputs []game.PlayerInput,
	currentState game.PlayerState,
) game.PlayerState {
	r.mu.Lock()
	defer r.mu.Unlock()

	// 从服务器状态开始
	reconciled := serverState

	// 重新应用所有未确认的输入
	for _, input := range pendingInputs {
		reconciled = r.applyInput(input, reconciled)
	}

	// 平滑过渡
	// 💡 避免突变的关键：只校正一小部分
	result := r.smoothTransition(currentState, reconciled)

	r.lastCorrection = &reconciled
	return result
}

// applyInput 应用单个输入到状态
func (r *Reconciler) applyInput(input game.PlayerInput, state game.PlayerState) game.PlayerState {
	result := state

	// 应用移动
	if input.MoveX != 0 || input.MoveY != 0 {
		moveDir := game.Vector2{X: input.MoveX, Y: input.MoveY}
		length := moveDir.Length()
		if length > 0 {
			moveDir = game.Vector2{X: moveDir.X / length, Y: moveDir.Y / length}
		}
		result.Velocity = moveDir.Scale(game.MoveSpeed)
	} else {
		result.Velocity = game.Vector2{}
	}

	// 应用朝向
	result.Direction = input.ViewAngle

	return result
}

// smoothTransition 平滑过渡
func (r *Reconciler) smoothTransition(current, target game.PlayerState) game.PlayerState {
	// 💡 平滑策略：线性插值
	// newPos = current * (1 - smoothing) + target * smoothing
	// 这样可以避免突然的位置跳变

	result := target

	// 位置平滑
	result.Position = game.Vector2{
		X: current.Position.X + (target.Position.X-current.Position.X)*r.correctionSmoothing,
		Y: current.Position.Y + (target.Position.Y-current.Position.Y)*r.correctionSmoothing,
	}

	// 速度平滑
	result.Velocity = game.Vector2{
		X: current.Velocity.X + (target.Velocity.X-current.Velocity.X)*r.correctionSmoothing,
		Y: current.Velocity.Y + (target.Velocity.Y-current.Velocity.Y)*r.correctionSmoothing,
	}

	return result
}

// GetCorrectionSmoothing 获取校正平滑系数
func (r *Reconciler) GetCorrectionSmoothing() float64 {
	r.mu.Lock()
	defer r.mu.Unlock()
	return r.correctionSmoothing
}

// SetCorrectionSmoothing 设置校正平滑系数
func (r *Reconciler) SetCorrectionSmoothing(smoothing float64) {
	r.mu.Lock()
	defer r.mu.Unlock()
	if smoothing > 0 && smoothing <= 1 {
		r.correctionSmoothing = smoothing
	}
}
