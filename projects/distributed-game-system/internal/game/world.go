package game

import (
	"fmt"
	"sync"
)

// World 表示游戏世界，管理所有玩家和游戏状态
type World struct {
	mu sync.RWMutex

	players map[uint32]*Player
	width   float64
	height  float64

	// 统计信息
	totalPlayersJoined uint32
}

// NewWorld 创建新的游戏世界
func NewWorld(width, height float64) *World {
	return &World{
		players: make(map[uint32]*Player),
		width:   width,
		height:  height,
	}
}

// AddPlayer 添加玩家到世界
func (w *World) AddPlayer(player *Player) error {
	w.mu.Lock()
	defer w.mu.Unlock()

	if _, exists := w.players[player.ID]; exists {
		return fmt.Errorf("player %d already exists", player.ID)
	}

	w.players[player.ID] = player
	w.totalPlayersJoined++
	return nil
}

// RemovePlayer 从世界移除玩家
func (w *World) RemovePlayer(playerID uint32) {
	w.mu.Lock()
	defer w.mu.Unlock()
	delete(w.players, playerID)
}

// GetPlayer 获取玩家
func (w *World) GetPlayer(playerID uint32) *Player {
	w.mu.RLock()
	defer w.mu.RUnlock()
	return w.players[playerID]
}

// GetAllPlayers 获取所有玩家
func (w *World) GetAllPlayers() map[uint32]*Player {
	w.mu.RLock()
	defer w.mu.RUnlock()

	result := make(map[uint32]*Player, len(w.players))
	for id, player := range w.players {
		result[id] = player
	}
	return result
}

// GetPlayerCount 获取当前玩家数量
func (w *World) GetPlayerCount() int {
	w.mu.RLock()
	defer w.mu.RUnlock()
	return len(w.players)
}

// Update 更新游戏世界
func (w *World) Update(deltaTime float64) {
	w.mu.Lock()
	defer w.mu.Unlock()

	// 更新所有玩家
	for _, player := range w.players {
		player.Update(deltaTime)
		w.clampPosition(player)
	}

	// 处理战斗
	w.processCombat()
}

// clampPosition 将玩家限制在世界边界内
func (w *World) clampPosition(player *Player) {
	if player.Position.X < 0 {
		player.Position.X = 0
		player.Velocity.X = 0
	}
	if player.Position.X > w.width {
		player.Position.X = w.width
		player.Velocity.X = 0
	}
	if player.Position.Y < 0 {
		player.Position.Y = 0
		player.Velocity.Y = 0
	}
	if player.Position.Y > w.height {
		player.Position.Y = w.height
		player.Velocity.Y = 0
	}
}

// processCombat 处理战斗逻辑
func (w *World) processCombat() {
	for _, attacker := range w.players {
		if attacker.Action != ActionAttack || !attacker.IsAlive() {
			continue
		}

		// 检查攻击范围内的目标
		for _, target := range w.players {
			if target.ID == attacker.ID || !target.IsAlive() {
				continue
			}

			distance := attacker.Position.Distance(target.Position)
			if distance <= attacker.AttackRange {
				target.TakeDamage(attacker.AttackDamage)
			}
		}
	}
}

// GetSnapshot 获取世界快照
func (w *World) GetSnapshot() map[uint32]PlayerState {
	w.mu.RLock()
	defer w.mu.RUnlock()

	snapshot := make(map[uint32]PlayerState, len(w.players))
	for id, player := range w.players {
		snapshot[id] = player.GetState()
	}
	return snapshot
}

// HandlePlayerInput 处理玩家输入
func (w *World) HandlePlayerInput(playerID uint32, input PlayerInput) error {
	w.mu.Lock()
	defer w.mu.Unlock()

	player, exists := w.players[playerID]
	if !exists {
		return fmt.Errorf("player %d not found", playerID)
	}

	player.ApplyInput(input)
	return nil
}
