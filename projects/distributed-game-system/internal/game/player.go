package game

import (
	"sync"
	"time"
)

// Action 表示玩家动作类型
type Action int32

const (
	ActionNone   Action = 0
	ActionMove   Action = 1
	ActionAttack Action = 2
	ActionDie    Action = 3
)

// PlayerState 表示玩家的完整状态
type PlayerState struct {
	ID        uint32
	Position  Vector2
	Velocity  Vector2
	Health    int32
	Direction float64 // 朝向角度（弧度）
	Action    Action
	Timestamp int64
}

// PlayerInput 表示玩家的输入命令
type PlayerInput struct {
	Sequence  uint32
	Timestamp int64
	MoveX     float64
	MoveY     float64
	Attack    bool
	ViewAngle float64
}

// Player 表示游戏中的玩家实体
type Player struct {
	mu sync.RWMutex

	ID        uint32
	Name      string
	Position  Vector2
	Velocity  Vector2
	Health    int32
	MaxHealth int32
	Direction float64
	Action    Action

	// 战斗相关
	AttackDamage  int32
	AttackRange   float64
	AttackCooldown float64
	LastAttackTime int64

	// 网络相关
	LastInputSeq uint32
	RTT          float64 // 往返延迟
}

// NewPlayer 创建新玩家
func NewPlayer(id uint32, name string, startPos Vector2) *Player {
	return &Player{
		ID:             id,
		Name:           name,
		Position:       startPos,
		Health:         100,
		MaxHealth:      100,
		AttackDamage:   10,
		AttackRange:    50.0,
		AttackCooldown: 1.0, // 1秒冷却
	}
}

// GetState 获取玩家状态快照
func (p *Player) GetState() PlayerState {
	p.mu.RLock()
	defer p.mu.RUnlock()

	return PlayerState{
		ID:        p.ID,
		Position:  p.Position,
		Velocity:  p.Velocity,
		Health:    p.Health,
		Direction: p.Direction,
		Action:    p.Action,
		Timestamp: time.Now().UnixMilli(),
	}
}

// ApplyInput 应用玩家输入
func (p *Player) ApplyInput(input PlayerInput) {
	p.mu.Lock()
	defer p.mu.Unlock()

	// 更新最后处理的输入序号
	if input.Sequence > p.LastInputSeq {
		p.LastInputSeq = input.Sequence
	}

	// 处理移动输入
	if input.MoveX != 0 || input.MoveY != 0 {
		moveDir := Vector2{X: input.MoveX, Y: input.MoveY}.Normalize()
		p.Velocity = moveDir.Scale(MoveSpeed)
		p.Action = ActionMove
	} else {
		p.Velocity = Vector2{}
		if p.Action == ActionMove {
			p.Action = ActionNone
		}
	}

	// 处理朝向
	p.Direction = input.ViewAngle

	// 处理攻击输入
	if input.Attack {
		p.tryAttack()
	}
}

// tryAttack 尝试发起攻击
func (p *Player) tryAttack() {
	now := time.Now().UnixMilli()
	cooldownMs := int64(p.AttackCooldown * 1000)

	if now-p.LastAttackTime >= cooldownMs {
		p.Action = ActionAttack
		p.LastAttackTime = now
	}
}

// Update 更新玩家状态
func (p *Player) Update(deltaTime float64) {
	p.mu.Lock()
	defer p.mu.Unlock()

	// 更新位置
	p.Position = p.Position.Add(p.Velocity.Scale(deltaTime))

	// 重置攻击状态（攻击动画完成后）
	if p.Action == ActionAttack {
		// 简化处理：一帧后重置
		p.Action = ActionNone
	}
}

// TakeDamage 受到伤害
func (p *Player) TakeDamage(damage int32) {
	p.mu.Lock()
	defer p.mu.Unlock()

	p.Health -= damage
	if p.Health <= 0 {
		p.Health = 0
		p.Action = ActionDie
	}
}

// IsAlive 检查玩家是否存活
func (p *Player) IsAlive() bool {
	p.mu.RLock()
	defer p.mu.RUnlock()
	return p.Health > 0
}

// CanAttack 检查是否可以攻击
func (p *Player) CanAttack() bool {
	p.mu.RLock()
	defer p.mu.RUnlock()

	now := time.Now().UnixMilli()
	cooldownMs := int64(p.AttackCooldown * 1000)
	return now-p.LastAttackTime >= cooldownMs
}
