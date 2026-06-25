package room

import (
	"errors"
	"sync"
	"time"

	"github.com/distributed-game-system/internal/player"
)

var (
	ErrRoomFull       = errors.New("room is full")
	ErrPlayerNotInRoom = errors.New("player is not in room")
	ErrRoomNotFound   = errors.New("room not found")
	ErrGameInProgress = errors.New("game is in progress")
	ErrNotEnoughPlayers = errors.New("not enough players")
)

// Status represents room status
type Status string

const (
	StatusWaiting   Status = "waiting"
	StatusPlaying   Status = "playing"
	StatusFinished  Status = "finished"
)

// Room represents a game room
type Room struct {
	ID         string    `json:"id"`
	Name       string    `json:"name"`
	MaxPlayers int       `json:"max_players"`
	MinPlayers int       `json:"min_players"`
	Players    map[string]*player.Player `json:"-"`
	Status     Status    `json:"status"`
	GameState  *GameState `json:"-"`
	CreatedAt  time.Time `json:"created_at"`
	StartedAt  time.Time `json:"started_at,omitempty"`
	mu         sync.RWMutex
}

// NewRoom creates a new room
func NewRoom(id, name string, maxPlayers, minPlayers int) *Room {
	return &Room{
		ID:         id,
		Name:       name,
		MaxPlayers: maxPlayers,
		MinPlayers: minPlayers,
		Players:    make(map[string]*player.Player),
		Status:     StatusWaiting,
		CreatedAt:  time.Now(),
	}
}

// AddPlayer adds a player to the room
func (r *Room) AddPlayer(p *player.Player) error {
	r.mu.Lock()
	defer r.mu.Unlock()

	if r.Status == StatusPlaying {
		return ErrGameInProgress
	}

	if len(r.Players) >= r.MaxPlayers {
		return ErrRoomFull
	}

	r.Players[p.ID] = p
	p.SetRoom(r.ID)
	return nil
}

// RemovePlayer removes a player from the room
func (r *Room) RemovePlayer(playerID string) error {
	r.mu.Lock()
	defer r.mu.Unlock()

	if _, ok := r.Players[playerID]; !ok {
		return ErrPlayerNotInRoom
	}

	r.Players[playerID].SetRoom("")
	delete(r.Players, playerID)
	return nil
}

// GetPlayerCount returns the number of players in the room
func (r *Room) GetPlayerCount() int {
	r.mu.RLock()
	defer r.mu.RUnlock()
	return len(r.Players)
}

// GetPlayerIDs returns the list of player IDs
func (r *Room) GetPlayerIDs() []string {
	r.mu.RLock()
	defer r.mu.RUnlock()

	var ids []string
	for id := range r.Players {
		ids = append(ids, id)
	}
	return ids
}

// HasPlayer checks if a player is in the room
func (r *Room) HasPlayer(playerID string) bool {
	r.mu.RLock()
	defer r.mu.RUnlock()
	_, ok := r.Players[playerID]
	return ok
}

// CanStart checks if the game can start
func (r *Room) CanStart() bool {
	r.mu.RLock()
	defer r.mu.RUnlock()
	return len(r.Players) >= r.MinPlayers && r.Status == StatusWaiting
}

// Start starts the game in the room
func (r *Room) Start() error {
	r.mu.Lock()
	defer r.mu.Unlock()

	if r.Status == StatusPlaying {
		return ErrGameInProgress
	}

	if len(r.Players) < r.MinPlayers {
		return ErrNotEnoughPlayers
	}

	r.Status = StatusPlaying
	r.StartedAt = time.Now()
	r.GameState = NewGameState(r.GetPlayerIDsUnsafe())
	return nil
}

// End ends the game in the room
func (r *Room) End() {
	r.mu.Lock()
	defer r.mu.Unlock()
	r.Status = StatusFinished
}

// GetPlayerIDsUnsafe returns player IDs without locking (internal use)
func (r *Room) GetPlayerIDsUnsafe() []string {
	var ids []string
	for id := range r.Players {
		ids = append(ids, id)
	}
	return ids
}

// RoomManager manages all rooms
type RoomManager struct {
	rooms map[string]*Room
	mu    sync.RWMutex
}

// NewRoomManager creates a new room manager
func NewRoomManager() *RoomManager {
	return &RoomManager{
		rooms: make(map[string]*Room),
	}
}

// CreateRoom creates a new room
func (rm *RoomManager) CreateRoom(id, name string, maxPlayers, minPlayers int) *Room {
	rm.mu.Lock()
	defer rm.mu.Unlock()

	room := NewRoom(id, name, maxPlayers, minPlayers)
	rm.rooms[id] = room
	return room
}

// GetRoom returns a room by ID
func (rm *RoomManager) GetRoom(roomID string) (*Room, bool) {
	rm.mu.RLock()
	defer rm.mu.RUnlock()
	room, ok := rm.rooms[roomID]
	return room, ok
}

// DeleteRoom deletes a room
func (rm *RoomManager) DeleteRoom(roomID string) {
	rm.mu.Lock()
	defer rm.mu.Unlock()
	delete(rm.rooms, roomID)
}

// GetRoomList returns all rooms
func (rm *RoomManager) GetRoomList() []*Room {
	rm.mu.RLock()
	defer rm.mu.RUnlock()

	var rooms []*Room
	for _, room := range rm.rooms {
		rooms = append(rooms, room)
	}
	return rooms
}

// GetAvailableRooms returns rooms that are waiting for players
func (rm *RoomManager) GetAvailableRooms() []*Room {
	rm.mu.RLock()
	defer rm.mu.RUnlock()

	var availableRooms []*Room
	for _, room := range rm.rooms {
		if room.Status == StatusWaiting && room.GetPlayerCount() < room.MaxPlayers {
			availableRooms = append(availableRooms, room)
		}
	}
	return availableRooms
}

// FindRoomForPlayer finds a suitable room for a player
func (rm *RoomManager) FindRoomForPlayer() *Room {
	rm.mu.RLock()
	defer rm.mu.RUnlock()

	for _, room := range rm.rooms {
		if room.Status == StatusWaiting && room.GetPlayerCount() < room.MaxPlayers {
			return room
		}
	}
	return nil
}
