package player

import (
	"sync"
	"time"
)

// Status represents player status
type Status string

const (
	StatusOnline   Status = "online"
	StatusInRoom   Status = "in_room"
	StatusInGame   Status = "in_game"
	StatusInQueue  Status = "in_queue"
	StatusOffline  Status = "offline"
)

// Player represents a game player
type Player struct {
	ID        string    `json:"id"`
	Name      string    `json:"name"`
	Rating    int       `json:"rating"`
	Status    Status    `json:"status"`
	RoomID    string    `json:"room_id,omitempty"`
	Score     int       `json:"score"`
	Wins      int       `json:"wins"`
	Losses    int       `json:"losses"`
	Draws     int       `json:"draws"`
	GamesPlayed int     `json:"games_played"`
	CreatedAt time.Time `json:"created_at"`
	LastSeen  time.Time `json:"last_seen"`
	mu        sync.RWMutex
}

// NewPlayer creates a new player
func NewPlayer(id, name string) *Player {
	now := time.Now()
	return &Player{
		ID:        id,
		Name:      name,
		Rating:    1200, // Default ELO rating
		Status:    StatusOnline,
		Score:     0,
		Wins:      0,
		Losses:    0,
		Draws:     0,
		GamesPlayed: 0,
		CreatedAt: now,
		LastSeen:  now,
	}
}

// UpdateLastSeen updates the last seen time
func (p *Player) UpdateLastSeen() {
	p.mu.Lock()
	defer p.mu.Unlock()
	p.LastSeen = time.Now()
}

// SetStatus sets the player status
func (p *Player) SetStatus(status Status) {
	p.mu.Lock()
	defer p.mu.Unlock()
	p.Status = status
}

// SetRoom sets the player's current room
func (p *Player) SetRoom(roomID string) {
	p.mu.Lock()
	defer p.mu.Unlock()
	p.RoomID = roomID
	if roomID != "" {
		p.Status = StatusInRoom
	} else {
		p.Status = StatusOnline
	}
}

// UpdateRating updates the player's ELO rating
func (p *Player) UpdateRating(newRating int) {
	p.mu.Lock()
	defer p.mu.Unlock()
	p.Rating = newRating
}

// RecordWin records a win
func (p *Player) RecordWin() {
	p.mu.Lock()
	defer p.mu.Unlock()
	p.Wins++
	p.GamesPlayed++
}

// RecordLoss records a loss
func (p *Player) RecordLoss() {
	p.mu.Lock()
	defer p.mu.Unlock()
	p.Losses++
	p.GamesPlayed++
}

// RecordDraw records a draw
func (p *Player) RecordDraw() {
	p.mu.Lock()
	defer p.mu.Unlock()
	p.Draws++
	p.GamesPlayed++
}

// GetWinRate returns the win rate
func (p *Player) GetWinRate() float64 {
	p.mu.RLock()
	defer p.mu.RUnlock()
	if p.GamesPlayed == 0 {
		return 0
	}
	return float64(p.Wins) / float64(p.GamesPlayed) * 100
}

// PlayerManager manages all players
type PlayerManager struct {
	players map[string]*Player
	mu      sync.RWMutex
}

// NewPlayerManager creates a new player manager
func NewPlayerManager() *PlayerManager {
	return &PlayerManager{
		players: make(map[string]*Player),
	}
}

// AddPlayer adds a new player
func (pm *PlayerManager) AddPlayer(player *Player) {
	pm.mu.Lock()
	defer pm.mu.Unlock()
	pm.players[player.ID] = player
}

// RemovePlayer removes a player
func (pm *PlayerManager) RemovePlayer(playerID string) {
	pm.mu.Lock()
	defer pm.mu.Unlock()
	delete(pm.players, playerID)
}

// GetPlayer returns a player by ID
func (pm *PlayerManager) GetPlayer(playerID string) (*Player, bool) {
	pm.mu.RLock()
	defer pm.mu.RUnlock()
	player, ok := pm.players[playerID]
	return player, ok
}

// GetPlayerCount returns the number of players
func (pm *PlayerManager) GetPlayerCount() int {
	pm.mu.RLock()
	defer pm.mu.RUnlock()
	return len(pm.players)
}

// GetOnlinePlayers returns all online players
func (pm *PlayerManager) GetOnlinePlayers() []*Player {
	pm.mu.RLock()
	defer pm.mu.RUnlock()

	var onlinePlayers []*Player
	for _, player := range pm.players {
		if player.Status != StatusOffline {
			onlinePlayers = append(onlinePlayers, player)
		}
	}
	return onlinePlayers
}

// UpdatePlayerRating updates a player's rating
func (pm *PlayerManager) UpdatePlayerRating(playerID string, newRating int) bool {
	pm.mu.Lock()
	defer pm.mu.Unlock()

	if player, ok := pm.players[playerID]; ok {
		player.UpdateRating(newRating)
		return true
	}
	return false
}

// GetPlayerStats returns player statistics
func (pm *PlayerManager) GetPlayerStats(playerID string) map[string]interface{} {
	pm.mu.RLock()
	defer pm.mu.RUnlock()

	if player, ok := pm.players[playerID]; ok {
		return map[string]interface{}{
			"id":          player.ID,
			"name":        player.Name,
			"rating":      player.Rating,
			"wins":        player.Wins,
			"losses":      player.Losses,
			"draws":       player.Draws,
			"games_played": player.GamesPlayed,
			"win_rate":    player.GetWinRate(),
		}
	}
	return nil
}
