package src

import (
	"fmt"
	"sync"
	"time"
)

// Player represents a connected game player
type Player struct {
	ID           string
	Name         string
	ConnectedAt  time.Time
	LastInputSeq uint32
	Latency      time.Duration // Round-trip latency estimate
	ShardID      string        // Which shard this player is assigned to
}

// PlayerState represents the authoritative game state for a player
type PlayerState struct {
	PlayerID   string
	X, Y       float64
	VelocityX  float64
	VelocityY  float64
	Health     float64
	Mana       float64
	Level      uint32
	Exp        uint32
	Gold       uint32
	Position   [3]float64 // X, Y, Z for 3D games
	Rotation   [3]float64 // Euler angles
	Buffs      []Buff
	Debuffs    []Debuff
	CreatedAt  time.Time
	UpdatedAt  time.Time
}

// Buff represents a temporary positive effect on a player
type Buff struct {
	Name      string
	Duration  time.Duration
	Remaining time.Duration
	Effect    map[string]float64
}

// Debuff represents a temporary negative effect on a player
type Debuff struct {
	Name      string
	Duration  time.Duration
	Remaining time.Duration
	Effect    map[string]float64
}

// GameState represents the authoritative state of a game session
type GameState struct {
	SessionID  string
	States     map[string]*PlayerState
	Mutex      sync.RWMutex
	CreatedAt  time.Time
	LastUpdate time.Time
	IsRunning  bool
}

// NewGameState creates a new game state instance
func NewGameState(sessionID string) *GameState {
	return &GameState{
		SessionID:  sessionID,
		States:     make(map[string]*PlayerState),
		CreatedAt:  time.Now(),
		LastUpdate: time.Now(),
		IsRunning:  true,
	}
}

// AddPlayer adds a player to the game state
func (gs *GameState) AddPlayer(state *PlayerState) {
	gs.Mutex.Lock()
	defer gs.Mutex.Unlock()
	gs.States[state.PlayerID] = state
	gs.LastUpdate = time.Now()
}

// RemovePlayer removes a player from the game state
func (gs *GameState) RemovePlayer(playerID string) {
	gs.Mutex.Lock()
	defer gs.Mutex.Unlock()
	delete(gs.States, playerID)
	gs.LastUpdate = time.Now()
}

// GetPlayerState retrieves a player's state with read lock
func (gs *GameState) GetPlayerState(playerID string) (*PlayerState, bool) {
	gs.Mutex.RLock()
	defer gs.Mutex.RUnlock()
	state, ok := gs.States[playerID]
	return state, ok
}

// UpdatePlayerState updates a player's state and returns the previous state for reconciliation
func (gs *GameState) UpdatePlayerState(playerID string, updates func(*PlayerState)) (*PlayerState, bool) {
	gs.Mutex.Lock()
	defer gs.Mutex.Unlock()
	state, ok := gs.States[playerID]
	if !ok {
		return nil, false
	}
	// Save snapshot before update for rollback capability
	prevState := *state
	updates(state)
	gs.LastUpdate = time.Now()
	return &prevState, true
}

// GetSnapshot returns a deep copy of all player states for synchronization
func (gs *GameState) GetSnapshot() map[string]*PlayerState {
	gs.Mutex.RLock()
	defer gs.Mutex.RUnlock()
	snapshot := make(map[string]*PlayerState, len(gs.States))
	for id, state := range gs.States {
		snap := *state
		snap.Buffs = make([]Buff, len(state.Buffs))
		copy(snap.Buffs, state.Buffs)
		snap.Debuffs = make([]Debuff, len(state.Debuffs))
		copy(snap.Debuffs, state.Debuffs)
		snapshot[id] = &snap
	}
	return snapshot
}

// PlayerCount returns the number of players in the game state
func (gs *GameState) PlayerCount() int {
	gs.Mutex.RLock()
	defer gs.Mutex.RUnlock()
	return len(gs.States)
}

// GameSession represents a managed game session with lifecycle control
type GameSession struct {
	SessionID string
	GameState *GameState
	Players   map[string]*Player
	Mutex     sync.RWMutex
	CreatedAt time.Time
	StartedAt time.Time
	FinishedAt time.Time
	Status    SessionStatus
}

// SessionStatus represents the lifecycle state of a game session
type SessionStatus int

const (
	SessionStatusCreated SessionStatus = iota
	SessionStatusRunning
	SessionStatusPaused
	SessionStatusFinished
	SessionStatusFailed
)

// String returns the string representation of a session status
func (s SessionStatus) String() string {
	names := []string{
		"Created",
		"Running",
		"Paused",
		"Finished",
		"Failed",
	}
	if int(s) < len(names) {
		return names[s]
	}
	return "Unknown"
}

// NewGameSession creates a new game session
func NewGameSession(sessionID string) *GameSession {
	return &GameSession{
		SessionID: sessionID,
		GameState: NewGameState(sessionID),
		Players:   make(map[string]*Player),
		CreatedAt: time.Now(),
		Status:    SessionStatusCreated,
	}
}

// Start initializes and starts the game session
func (gs *GameSession) Start() error {
	gs.Mutex.Lock()
	defer gs.Mutex.Unlock()
	if gs.Status != SessionStatusCreated {
		return fmt.Errorf("session cannot be started: current status is %s", gs.Status)
	}
	gs.Status = SessionStatusRunning
	gs.StartedAt = time.Now()
	gs.GameState.IsRunning = true
	return nil
}

// Pause pauses the game session
func (gs *GameSession) Pause() error {
	gs.Mutex.Lock()
	defer gs.Mutex.Unlock()
	if gs.Status != SessionStatusRunning {
		return fmt.Errorf("session cannot be paused: current status is %s", gs.Status)
	}
	gs.Status = SessionStatusPaused
	gs.GameState.IsRunning = false
	return nil
}

// Resume resumes a paused game session
func (gs *GameSession) Resume() error {
	gs.Mutex.Lock()
	defer gs.Mutex.Unlock()
	if gs.Status != SessionStatusPaused {
		return fmt.Errorf("session cannot be resumed: current status is %s", gs.Status)
	}
	gs.Status = SessionStatusRunning
	gs.GameState.IsRunning = true
	return nil
}

// End gracefully ends the game session
func (gs *GameSession) End() error {
	gs.Mutex.Lock()
	defer gs.Mutex.Unlock()
	if gs.Status != SessionStatusRunning && gs.Status != SessionStatusPaused {
		return fmt.Errorf("session cannot be ended: current status is %s", gs.Status)
	}
	gs.Status = SessionStatusFinished
	gs.FinishedAt = time.Now()
	gs.GameState.IsRunning = false
	return nil
}

// AddPlayer adds a player to the session
func (gs *GameSession) AddPlayer(player *Player) error {
	gs.Mutex.Lock()
	defer gs.Mutex.Unlock()
	if gs.Status != SessionStatusRunning {
		return fmt.Errorf("cannot add player: session is not running")
	}
	if _, exists := gs.Players[player.ID]; exists {
		return fmt.Errorf("player %s already in session", player.ID)
	}
	gs.Players[player.ID] = player
	gs.GameState.AddPlayer(&PlayerState{
		PlayerID:  player.ID,
		CreatedAt: time.Now(),
		UpdatedAt: time.Now(),
		Health:    100.0,
		Mana:      100.0,
	})
	return nil
}

// RemovePlayer removes a player from the session
func (gs *GameSession) RemovePlayer(playerID string) error {
	gs.Mutex.Lock()
	defer gs.Mutex.Unlock()
	if _, exists := gs.Players[playerID]; !exists {
		return fmt.Errorf("player %s not found in session", playerID)
	}
	delete(gs.Players, playerID)
	gs.GameState.RemovePlayer(playerID)
	return nil
}

// GetPlayerCount returns the number of players in the session
func (gs *GameSession) GetPlayerCount() int {
	gs.Mutex.RLock()
	defer gs.Mutex.RUnlock()
	return len(gs.Players)
}

// GetStatus returns the current session status
func (gs *GameSession) GetStatus() SessionStatus {
	gs.Mutex.RLock()
	defer gs.Mutex.RUnlock()
	return gs.Status
}

// SessionManager manages multiple game sessions
type SessionManager struct {
	sessions map[string]*GameSession
 Mutex    sync.RWMutex
}

// NewSessionManager creates a new session manager
func NewSessionManager() *SessionManager {
	return &SessionManager{
		sessions: make(map[string]*GameSession),
	}
}

// CreateSession creates a new game session
func (sm *SessionManager) CreateSession(sessionID string) *GameSession {
	sm.Mutex.Lock()
	defer sm.Mutex.Unlock()
	session := NewGameSession(sessionID)
	sm.sessions[sessionID] = session
	return session
}

// GetSession retrieves a session by ID
func (sm *SessionManager) GetSession(sessionID string) (*GameSession, bool) {
	sm.Mutex.RLock()
	defer sm.Mutex.RUnlock()
	session, ok := sm.sessions[sessionID]
	return session, ok
}

// ListSessions returns all active sessions
func (sm *SessionManager) ListSessions() []*GameSession {
	sm.Mutex.RLock()
	defer sm.Mutex.RUnlock()
	var result []*GameSession
	for _, session := range sm.sessions {
		if session.Status == SessionStatusRunning || session.Status == SessionStatusPaused {
			result = append(result, session)
		}
	}
	return result
}

// RemoveSession removes and cleans up a session
func (sm *SessionManager) RemoveSession(sessionID string) bool {
	sm.Mutex.Lock()
	defer sm.Mutex.Unlock()
	if _, ok := sm.sessions[sessionID]; !ok {
		return false
	}
	delete(sm.sessions, sessionID)
	return true
}
