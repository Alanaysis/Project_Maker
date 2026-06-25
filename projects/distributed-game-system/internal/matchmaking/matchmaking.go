package matchmaking

import (
	"errors"
	"math"
	"sort"
	"sync"
	"time"

	"github.com/distributed-game-system/internal/player"
	"github.com/distributed-game-system/internal/room"
)

var (
	ErrAlreadyInQueue  = errors.New("player already in queue")
	ErrNotInQueue      = errors.New("player not in queue")
	ErrMatchNotFound   = errors.New("match not found")
	ErrInvalidMode     = errors.New("invalid matchmaking mode")
)

// Mode represents matchmaking mode
type Mode string

const (
	ModeRandom Mode = "random"
	ModeELO    Mode = "elo"
)

// MatchRequest represents a matchmaking request
type MatchRequest struct {
	PlayerID  string    `json:"player_id"`
	Mode      Mode      `json:"mode"`
	Rating    int       `json:"rating"`
	GameType  string    `json:"game_type"`
	QueueTime time.Time `json:"queue_time"`
}

// MatchResult represents a matchmaking result
type MatchResult struct {
	RoomID  string   `json:"room_id"`
	Players []string `json:"players"`
	Mode    Mode     `json:"mode"`
}

// Matchmaker handles player matchmaking
type Matchmaker struct {
	queue      []*MatchRequest
	roomMgr    *room.RoomManager
	playerMgr  *player.PlayerManager
	mu         sync.RWMutex
	matchCh    chan *MatchResult
	stopCh     chan struct{}
}

// NewMatchmaker creates a new matchmaker
func NewMatchmaker(roomMgr *room.RoomManager, playerMgr *player.PlayerManager) *Matchmaker {
	return &Matchmaker{
		queue:     make([]*MatchRequest, 0),
		roomMgr:   roomMgr,
		playerMgr: playerMgr,
		matchCh:   make(chan *MatchResult, 100),
		stopCh:    make(chan struct{}),
	}
}

// Start starts the matchmaker
func (m *Matchmaker) Start() {
	go m.matchLoop()
}

// Stop stops the matchmaker
func (m *Matchmaker) Stop() {
	close(m.stopCh)
}

// Enqueue adds a player to the matchmaking queue
func (m *Matchmaker) Enqueue(request *MatchRequest) error {
	m.mu.Lock()
	defer m.mu.Unlock()

	// Check if player is already in queue
	for _, req := range m.queue {
		if req.PlayerID == request.PlayerID {
			return ErrAlreadyInQueue
		}
	}

	request.QueueTime = time.Now()
	m.queue = append(m.queue, request)

	// Update player status
	if p, ok := m.playerMgr.GetPlayer(request.PlayerID); ok {
		p.SetStatus(player.StatusInQueue)
	}

	return nil
}

// Dequeue removes a player from the matchmaking queue
func (m *Matchmaker) Dequeue(playerID string) error {
	m.mu.Lock()
	defer m.mu.Unlock()

	for i, req := range m.queue {
		if req.PlayerID == playerID {
			m.queue = append(m.queue[:i], m.queue[i+1:]...)
			if p, ok := m.playerMgr.GetPlayer(playerID); ok {
				p.SetStatus(player.StatusOnline)
			}
			return nil
		}
	}

	return ErrNotInQueue
}

// GetMatchResult returns the match result channel
func (m *Matchmaker) GetMatchResult() <-chan *MatchResult {
	return m.matchCh
}

// matchLoop runs the matchmaking loop
func (m *Matchmaker) matchLoop() {
	ticker := time.NewTicker(1 * time.Second)
	defer ticker.Stop()

	for {
		select {
		case <-ticker.C:
			m.processQueue()
		case <-m.stopCh:
			return
		}
	}
}

// processQueue processes the matchmaking queue
func (m *Matchmaker) processQueue() {
	m.mu.Lock()
	defer m.mu.Unlock()

	if len(m.queue) < 2 {
		return
	}

	// Group requests by game type
	gameTypeGroups := make(map[string][]*MatchRequest)
	for _, req := range m.queue {
		gameTypeGroups[req.GameType] = append(gameTypeGroups[req.GameType], req)
	}

	for gameType, requests := range gameTypeGroups {
		if len(requests) < 2 {
			continue
		}

		// Try to match players
		matches := m.matchPlayers(requests)
		for _, match := range matches {
			// Remove matched players from queue
			for _, playerID := range match.Players {
				for i, req := range m.queue {
					if req.PlayerID == playerID {
						m.queue = append(m.queue[:i], m.queue[i+1:]...)
						break
					}
				}
			}

			// Create room for the match
			roomID := "match-" + gameType + "-" + time.Now().Format("20060102150405")
			gameRoom := m.roomMgr.CreateRoom(roomID, "Match Game", len(match.Players), len(match.Players))

			// Add players to room
			for _, playerID := range match.Players {
				if p, ok := m.playerMgr.GetPlayer(playerID); ok {
					gameRoom.AddPlayer(p)
				}
			}

			match.RoomID = roomID

			// Send match result
			select {
			case m.matchCh <- match:
			default:
				// Channel full, skip
			}
		}
	}
}

// matchPlayers matches players based on mode
func (m *Matchmaker) matchPlayers(requests []*MatchRequest) []*MatchResult {
	if len(requests) < 2 {
		return nil
	}

	// Check mode of first request (assume all same mode for simplicity)
	mode := requests[0].Mode

	switch mode {
	case ModeRandom:
		return m.matchRandom(requests)
	case ModeELO:
		return m.matchELO(requests)
	default:
		return nil
	}
}

// matchRandom matches players randomly
func (m *Matchmaker) matchRandom(requests []*MatchRequest) []*MatchResult {
	var results []*MatchResult

	// Simple random matching - pair players in order
	for i := 0; i < len(requests)-1; i += 2 {
		result := &MatchResult{
			Players: []string{requests[i].PlayerID, requests[i+1].PlayerID},
			Mode:    ModeRandom,
		}
		results = append(results, result)
	}

	return results
}

// matchELO matches players based on ELO rating
func (m *Matchmaker) matchELO(requests []*MatchRequest) []*MatchResult {
	var results []*MatchResult

	// Sort by rating
	sort.Slice(requests, func(i, j int) bool {
		return requests[i].Rating < requests[j].Rating
	})

	// Match players with closest ratings
	matched := make(map[string]bool)

	for i := 0; i < len(requests); i++ {
		if matched[requests[i].PlayerID] {
			continue
		}

		bestMatch := -1
		bestDiff := math.MaxInt32

		for j := i + 1; j < len(requests); j++ {
			if matched[requests[j].PlayerID] {
				continue
			}

			diff := abs(requests[i].Rating - requests[j].Rating)
			queueTimeDiff := requests[j].QueueTime.Sub(requests[i].QueueTime).Seconds()

			// Consider both rating difference and queue time
			// Allow larger rating differences for players who waited longer
			maxDiff := 100 + int(queueTimeDiff*10)

			if diff < bestDiff && diff <= maxDiff {
				bestDiff = diff
				bestMatch = j
			}
		}

		if bestMatch != -1 {
			result := &MatchResult{
				Players: []string{requests[i].PlayerID, requests[bestMatch].PlayerID},
				Mode:    ModeELO,
			}
			results = append(results, result)
			matched[requests[i].PlayerID] = true
			matched[requests[bestMatch].PlayerID] = true
		}
	}

	return results
}

// GetQueueSize returns the current queue size
func (m *Matchmaker) GetQueueSize() int {
	m.mu.RLock()
	defer m.mu.RUnlock()
	return len(m.queue)
}

// GetQueueStatus returns the queue status
func (m *Matchmaker) GetQueueStatus() map[string]interface{} {
	m.mu.RLock()
	defer m.mu.RUnlock()

	modeCounts := make(map[Mode]int)
	for _, req := range m.queue {
		modeCounts[req.Mode]++
	}

	return map[string]interface{}{
		"total": len(m.queue),
		"modes": modeCounts,
	}
}

func abs(x int) int {
	if x < 0 {
		return -x
	}
	return x
}

// CalculateELO calculates new ELO ratings
func CalculateELO(winnerRating, loserRating int, kFactor float64) (int, int) {
	// Expected scores
	expectedWinner := 1.0 / (1.0 + math.Pow(10, float64(loserRating-winnerRating)/400.0))
	expectedLoser := 1.0 / (1.0 + math.Pow(10, float64(winnerRating-loserRating)/400.0))

	// New ratings
	newWinner := float64(winnerRating) + kFactor*(1.0-expectedWinner)
	newLoser := float64(loserRating) + kFactor*(0.0-expectedLoser)

	return int(newWinner), int(newLoser)
}
