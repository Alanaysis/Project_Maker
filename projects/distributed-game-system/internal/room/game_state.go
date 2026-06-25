package room

import (
	"sync"
	"time"
)

// GameState represents the state of a game
type GameState struct {
	Frame     uint64                 `json:"frame"`
	State     map[string]interface{} `json:"state"`
	Players   map[string]*PlayerState `json:"players"`
	Timestamp time.Time              `json:"timestamp"`
	mu        sync.RWMutex
}

// PlayerState represents a player's state in the game
type PlayerState struct {
	PlayerID string                 `json:"player_id"`
	X        float64                `json:"x"`
	Y        float64                `json:"y"`
	Z        float64                `json:"z"`
	Score    int                    `json:"score"`
	Health   int                    `json:"health"`
	Active   bool                   `json:"active"`
	Data     map[string]interface{} `json:"data,omitempty"`
}

// NewGameState creates a new game state
func NewGameState(playerIDs []string) *GameState {
	players := make(map[string]*PlayerState)
	for _, id := range playerIDs {
		players[id] = &PlayerState{
			PlayerID: id,
			X:        0,
			Y:        0,
			Z:        0,
			Score:    0,
			Health:   100,
			Active:   true,
			Data:     make(map[string]interface{}),
		}
	}

	return &GameState{
		Frame:     0,
		State:     make(map[string]interface{}),
		Players:   players,
		Timestamp: time.Now(),
	}
}

// UpdatePlayer updates a player's state
func (gs *GameState) UpdatePlayer(playerID string, x, y, z float64) {
	gs.mu.Lock()
	defer gs.mu.Unlock()

	if playerState, ok := gs.Players[playerID]; ok {
		playerState.X = x
		playerState.Y = y
		playerState.Z = z
	}
	gs.Frame++
	gs.Timestamp = time.Now()
}

// UpdatePlayerScore updates a player's score
func (gs *GameState) UpdatePlayerScore(playerID string, score int) {
	gs.mu.Lock()
	defer gs.mu.Unlock()

	if playerState, ok := gs.Players[playerID]; ok {
		playerState.Score = score
	}
}

// UpdatePlayerHealth updates a player's health
func (gs *GameState) UpdatePlayerHealth(playerID string, health int) {
	gs.mu.Lock()
	defer gs.mu.Unlock()

	if playerState, ok := gs.Players[playerID]; ok {
		playerState.Health = health
	}
}

// SetPlayerActive sets a player's active status
func (gs *GameState) SetPlayerActive(playerID string, active bool) {
	gs.mu.Lock()
	defer gs.mu.Unlock()

	if playerState, ok := gs.Players[playerID]; ok {
		playerState.Active = active
	}
}

// GetSnapshot returns a snapshot of the current game state
func (gs *GameState) GetSnapshot() map[string]interface{} {
	gs.mu.RLock()
	defer gs.mu.RUnlock()

	snapshot := map[string]interface{}{
		"frame":     gs.Frame,
		"timestamp": gs.Timestamp,
		"state":     gs.State,
	}

	playerStates := make(map[string]interface{})
	for id, ps := range gs.Players {
		playerStates[id] = map[string]interface{}{
			"x":      ps.X,
			"y":      ps.Y,
			"z":      ps.Z,
			"score":  ps.Score,
			"health": ps.Health,
			"active": ps.Active,
		}
	}
	snapshot["players"] = playerStates

	return snapshot
}

// GetDelta returns changes since the given frame
func (gs *GameState) GetDelta(lastFrame uint64) map[string]interface{} {
	gs.mu.RLock()
	defer gs.mu.RUnlock()

	// In a real implementation, you would track changes per frame
	// For now, return the full state as delta
	return gs.GetSnapshot()
}

// AdvanceFrame advances the game frame
func (gs *GameState) AdvanceFrame() {
	gs.mu.Lock()
	defer gs.mu.Unlock()
	gs.Frame++
	gs.Timestamp = time.Now()
}

// GetFrame returns the current frame number
func (gs *GameState) GetFrame() uint64 {
	gs.mu.RLock()
	defer gs.mu.RUnlock()
	return gs.Frame
}

// GetPlayerState returns a player's state
func (gs *GameState) GetPlayerState(playerID string) *PlayerState {
	gs.mu.RLock()
	defer gs.mu.RUnlock()
	return gs.Players[playerID]
}
