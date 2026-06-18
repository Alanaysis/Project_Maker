package sync

import (
	"time"

	"github.com/distributed-game-system/internal/game"
)

// Interpolator 实体插值器
// ⭐ 核心算法：在两个服务器快照之间平滑插值远程实体
type Interpolator struct {
	// 插值延迟（毫秒）
	// 💡 为什么需要插值延迟？
	// 远程实体需要在两个快照之间插值渲染，必须有一个缓冲时间
	// 通常设置为 100-200ms，太低会导致抖动，太高会导致延迟感
	interpolationDelay int64

	// 快照缓冲
	snapshots []TimestampedSnapshot
	maxBuffer int
}

// TimestampedSnapshot 带时间戳的快照
type TimestampedSnapshot struct {
	Timestamp int64
	Players   map[uint32]game.PlayerState
}

// InterpolatedState 插值后的状态
type InterpolatedState struct {
	Position game.Vector2
	Velocity game.Vector2
	Health   int32
	Action   game.Action
}

// NewInterpolator 创建插值器
func NewInterpolator(interpolationDelayMs int64, maxBuffer int) *Interpolator {
	return &Interpolator{
		interpolationDelay: interpolationDelayMs,
		snapshots:          make([]TimestampedSnapshot, 0, maxBuffer),
		maxBuffer:          maxBuffer,
	}
}

// AddSnapshot 添加快照到缓冲
func (i *Interpolator) AddSnapshot(players map[uint32]game.PlayerState) {
	now := time.Now().UnixMilli()

	snapshot := TimestampedSnapshot{
		Timestamp: now,
		Players:   players,
	}

	i.snapshots = append(i.snapshots, snapshot)

	// 限制缓冲大小
	if len(i.snapshots) > i.maxBuffer {
		i.snapshots = i.snapshots[1:]
	}
}

// Interpolate 插值指定玩家的状态
// ⭐ 核心算法：线性插值
//
// 时间线:
//   t1 -------- t_render -------- t2
//   S1 -------- S_result -------- S2
//
// 计算:
//   renderTime = now - interpolationDelay
//   alpha = (renderTime - t1) / (t2 - t1)
//   position = S1.Position * (1 - alpha) + S2.Position * alpha
func (i *Interpolator) Interpolate(playerID uint32) *InterpolatedState {
	if len(i.snapshots) < 2 {
		return nil
	}

	// 计算渲染时间（当前时间减去插值延迟）
	renderTime := time.Now().UnixMilli() - i.interpolationDelay

	// 找到包围 renderTime 的两个快照
	var prev, next *TimestampedSnapshot
	for idx := len(i.snapshots) - 1; idx >= 1; idx-- {
		if i.snapshots[idx-1].Timestamp <= renderTime && i.snapshots[idx].Timestamp >= renderTime {
			prev = &i.snapshots[idx-1]
			next = &i.snapshots[idx]
			break
		}
	}

	if prev == nil || next == nil {
		// 没有找到合适的快照对，返回最新状态
		latest := &i.snapshots[len(i.snapshots)-1]
		if state, exists := latest.Players[playerID]; exists {
			return &InterpolatedState{
				Position: state.Position,
				Velocity: state.Velocity,
				Health:   state.Health,
				Action:   state.Action,
			}
		}
		return nil
	}

	// 获取两个快照中的玩家状态
	prevState, prevExists := prev.Players[playerID]
	nextState, nextExists := next.Players[playerID]

	if !prevExists && !nextExists {
		return nil
	}

	if !prevExists {
		return &InterpolatedState{
			Position: nextState.Position,
			Velocity: nextState.Velocity,
			Health:   nextState.Health,
			Action:   nextState.Action,
		}
	}

	if !nextExists {
		return &InterpolatedState{
			Position: prevState.Position,
			Velocity: prevState.Velocity,
			Health:   prevState.Health,
			Action:   prevState.Action,
		}
	}

	// 计算插值系数
	duration := float64(next.Timestamp - prev.Timestamp)
	elapsed := float64(renderTime - prev.Timestamp)
	alpha := elapsed / duration
	if alpha < 0 {
		alpha = 0
	}
	if alpha > 1 {
		alpha = 1
	}

	// 线性插值
	return &InterpolatedState{
		Position: game.Lerp(prevState.Position, nextState.Position, alpha),
		Velocity: game.Lerp(prevState.Velocity, nextState.Velocity, alpha),
		Health:   interpolateInt(prevState.Health, nextState.Health, alpha),
		Action:   nextState.Action, // 动作不做插值，使用最新值
	}
}

// interpolateInt 整数插值
func interpolateInt(a, b int32, t float64) int32 {
	return int32(float64(a) + float64(b-a)*t)
}

// GetSnapshotCount 获取缓冲中的快照数量
func (i *Interpolator) GetSnapshotCount() int {
	return len(i.snapshots)
}
