package sync

import (
	"sync"
	"time"

	"github.com/distributed-game-system/internal/protocol"
	"github.com/distributed-game-system/internal/room"
)

// SyncMode represents the synchronization mode
type SyncMode string

const (
	SyncModeSnapshot SyncMode = "snapshot" // Full state sync
	SyncModeDelta    SyncMode = "delta"    // Delta sync
	SyncModeFrame    SyncMode = "frame"    // Frame sync
)

// StateSynchronizer handles game state synchronization
type StateSynchronizer struct {
	roomID       string
	gameState    *room.GameState
	mode         SyncMode
	syncInterval time.Duration
	lastSync     time.Time
	lastFrame    uint64
	stopCh       chan struct{}
	mu           sync.RWMutex
}

// NewStateSynchronizer creates a new state synchronizer
func NewStateSynchronizer(roomID string, gameState *room.GameState, mode SyncMode) *StateSynchronizer {
	return &StateSynchronizer{
		roomID:       roomID,
		gameState:    gameState,
		mode:         mode,
		syncInterval: 50 * time.Millisecond, // 20 FPS sync rate
		stopCh:       make(chan struct{}),
	}
}

// SetSyncInterval sets the synchronization interval
func (ss *StateSynchronizer) SetSyncInterval(interval time.Duration) {
	ss.mu.Lock()
	defer ss.mu.Unlock()
	ss.syncInterval = interval
}

// Start starts the synchronization loop
func (ss *StateSynchronizer) Start(broadcastFunc func(*protocol.Message)) {
	go ss.syncLoop(broadcastFunc)
}

// Stop stops the synchronization loop
func (ss *StateSynchronizer) Stop() {
	close(ss.stopCh)
}

// syncLoop runs the synchronization loop
func (ss *StateSynchronizer) syncLoop(broadcastFunc func(*protocol.Message)) {
	ticker := time.NewTicker(ss.syncInterval)
	defer ticker.Stop()

	for {
		select {
		case <-ticker.C:
			ss.sync(broadcastFunc)
		case <-ss.stopCh:
			return
		}
	}
}

// sync performs a single synchronization step
func (ss *StateSynchronizer) sync(broadcastFunc func(*protocol.Message)) {
	ss.mu.Lock()
	defer ss.mu.Unlock()

	switch ss.mode {
	case SyncModeSnapshot:
		ss.syncSnapshot(broadcastFunc)
	case SyncModeDelta:
		ss.syncDelta(broadcastFunc)
	case SyncModeFrame:
		ss.syncFrame(broadcastFunc)
	}

	ss.lastSync = time.Now()
}

// syncSnapshot sends full state snapshot
func (ss *StateSynchronizer) syncSnapshot(broadcastFunc func(*protocol.Message)) {
	snapshot := ss.gameState.GetSnapshot()

	payload := &protocol.GameStatePayload{
		Frame:     ss.gameState.GetFrame(),
		State:     snapshot,
		Timestamp: time.Now(),
	}

	msg, err := protocol.NewMessage(protocol.MsgTypeGameState, "", ss.roomID, payload)
	if err != nil {
		return
	}

	broadcastFunc(msg)
}

// syncDelta sends state delta
func (ss *StateSynchronizer) syncDelta(broadcastFunc func(*protocol.Message)) {
	currentFrame := ss.gameState.GetFrame()
	if currentFrame <= ss.lastFrame {
		return
	}

	delta := ss.gameState.GetDelta(ss.lastFrame)

	payload := &protocol.StateDeltaPayload{
		Frame:     currentFrame,
		Changes:   delta,
		Timestamp: time.Now(),
	}

	msg, err := protocol.NewMessage(protocol.MsgTypeStateDelta, "", ss.roomID, payload)
	if err != nil {
		return
	}

	broadcastFunc(msg)
	ss.lastFrame = currentFrame
}

// syncFrame sends frame sync data
func (ss *StateSynchronizer) syncFrame(broadcastFunc func(*protocol.Message)) {
	currentFrame := ss.gameState.GetFrame()

	payload := &protocol.GameStatePayload{
		Frame:     currentFrame,
		State:     ss.gameState.GetSnapshot(),
		Timestamp: time.Now(),
	}

	msg, err := protocol.NewMessage(protocol.MsgTypeFrameSync, "", ss.roomID, payload)
	if err != nil {
		return
	}

	broadcastFunc(msg)
}

// ProcessInput processes a player input for frame sync
func (ss *StateSynchronizer) ProcessInput(input *protocol.FrameInputPayload) {
	ss.mu.Lock()
	defer ss.mu.Unlock()

	// Update player state based on input
	if playerState := ss.gameState.GetPlayerState(input.PlayerID); playerState != nil {
		if x, ok := input.Inputs["x"].(float64); ok {
			playerState.X = x
		}
		if y, ok := input.Inputs["y"].(float64); ok {
			playerState.Y = y
		}
		if z, ok := input.Inputs["z"].(float64); ok {
			playerState.Z = z
		}
	}
}

// GetSyncMode returns the current sync mode
func (ss *StateSynchronizer) GetSyncMode() SyncMode {
	ss.mu.RLock()
	defer ss.mu.RUnlock()
	return ss.mode
}

// SetSyncMode sets the sync mode
func (ss *StateSynchronizer) SetSyncMode(mode SyncMode) {
	ss.mu.Lock()
	defer ss.mu.Unlock()
	ss.mode = mode
}
