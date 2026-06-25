package tests

import (
	"testing"
	"time"

	"github.com/distributed-game-system/internal/matchmaking"
	"github.com/distributed-game-system/internal/player"
	"github.com/distributed-game-system/internal/protocol"
	"github.com/distributed-game-system/internal/room"
)

func TestPlayerCreation(t *testing.T) {
	p := player.NewPlayer("player1", "TestPlayer")

	if p.ID != "player1" {
		t.Errorf("Expected player ID 'player1', got '%s'", p.ID)
	}

	if p.Name != "TestPlayer" {
		t.Errorf("Expected player name 'TestPlayer', got '%s'", p.Name)
	}

	if p.Rating != 1200 {
		t.Errorf("Expected default rating 1200, got %d", p.Rating)
	}

	if p.Status != player.StatusOnline {
		t.Errorf("Expected status 'online', got '%s'", p.Status)
	}
}

func TestPlayerManager(t *testing.T) {
	pm := player.NewPlayerManager()

	p1 := player.NewPlayer("player1", "Player 1")
	p2 := player.NewPlayer("player2", "Player 2")

	pm.AddPlayer(p1)
	pm.AddPlayer(p2)

	if pm.GetPlayerCount() != 2 {
		t.Errorf("Expected 2 players, got %d", pm.GetPlayerCount())
	}

	p, ok := pm.GetPlayer("player1")
	if !ok || p.Name != "Player 1" {
		t.Error("Failed to get player1")
	}

	pm.RemovePlayer("player1")
	if pm.GetPlayerCount() != 1 {
		t.Errorf("Expected 1 player after removal, got %d", pm.GetPlayerCount())
	}
}

func TestRoomCreation(t *testing.T) {
	rm := room.NewRoomManager()

	gameRoom := rm.CreateRoom("room1", "Test Room", 4, 2)

	if gameRoom.ID != "room1" {
		t.Errorf("Expected room ID 'room1', got '%s'", gameRoom.ID)
	}

	if gameRoom.MaxPlayers != 4 {
		t.Errorf("Expected max players 4, got %d", gameRoom.MaxPlayers)
	}

	if gameRoom.Status != room.StatusWaiting {
		t.Errorf("Expected status 'waiting', got '%s'", gameRoom.Status)
	}
}

func TestRoomPlayerManagement(t *testing.T) {
	gameRoom := room.NewRoom("room1", "Test Room", 4, 2)

	p1 := player.NewPlayer("player1", "Player 1")
	p2 := player.NewPlayer("player2", "Player 2")
	p3 := player.NewPlayer("player3", "Player 3")

	// Add players
	err := gameRoom.AddPlayer(p1)
	if err != nil {
		t.Errorf("Failed to add player1: %v", err)
	}

	err = gameRoom.AddPlayer(p2)
	if err != nil {
		t.Errorf("Failed to add player2: %v", err)
	}

	if gameRoom.GetPlayerCount() != 2 {
		t.Errorf("Expected 2 players, got %d", gameRoom.GetPlayerCount())
	}

	// Check if player is in room
	if !gameRoom.HasPlayer("player1") {
		t.Error("Player1 should be in room")
	}

	// Remove player
	err = gameRoom.RemovePlayer("player1")
	if err != nil {
		t.Errorf("Failed to remove player1: %v", err)
	}

	if gameRoom.HasPlayer("player1") {
		t.Error("Player1 should not be in room")
	}

	// Add third player
	gameRoom.AddPlayer(p3)
	if gameRoom.GetPlayerCount() != 2 {
		t.Errorf("Expected 2 players, got %d", gameRoom.GetPlayerCount())
	}
}

func TestRoomGameStart(t *testing.T) {
	gameRoom := room.NewRoom("room1", "Test Room", 4, 2)

	p1 := player.NewPlayer("player1", "Player 1")
	p2 := player.NewPlayer("player2", "Player 2")

	gameRoom.AddPlayer(p1)
	gameRoom.AddPlayer(p2)

	// Should be able to start
	if !gameRoom.CanStart() {
		t.Error("Game should be able to start with 2 players")
	}

	// Start game
	err := gameRoom.Start()
	if err != nil {
		t.Errorf("Failed to start game: %v", err)
	}

	if gameRoom.Status != room.StatusPlaying {
		t.Errorf("Expected status 'playing', got '%s'", gameRoom.Status)
	}

	if gameRoom.GameState == nil {
		t.Error("GameState should not be nil after game starts")
	}

	// Should not be able to start again
	err = gameRoom.Start()
	if err != room.ErrGameInProgress {
		t.Error("Should not be able to start game in progress")
	}
}

func TestGameState(t *testing.T) {
	playerIDs := []string{"player1", "player2"}
	gameState := room.NewGameState(playerIDs)

	if gameState.Frame != 0 {
		t.Errorf("Expected initial frame 0, got %d", gameState.Frame)
	}

	// Update player position
	gameState.UpdatePlayer("player1", 10.0, 20.0, 30.0)

	if gameState.Frame != 1 {
		t.Errorf("Expected frame 1 after update, got %d", gameState.Frame)
	}

	playerState := gameState.GetPlayerState("player1")
	if playerState.X != 10.0 || playerState.Y != 20.0 || playerState.Z != 30.0 {
		t.Errorf("Player position incorrect: got (%f, %f, %f)", playerState.X, playerState.Y, playerState.Z)
	}

	// Get snapshot
	snapshot := gameState.GetSnapshot()
	if snapshot["frame"].(uint64) != 1 {
		t.Error("Snapshot frame incorrect")
	}
}

func TestMessageEncoding(t *testing.T) {
	payload := &protocol.PlayerMovePayload{
		X: 10.0,
		Y: 20.0,
		Z: 30.0,
	}

	msg, err := protocol.NewMessage(protocol.MsgTypePlayerMove, "player1", "room1", payload)
	if err != nil {
		t.Errorf("Failed to create message: %v", err)
	}

	if msg.Type != protocol.MsgTypePlayerMove {
		t.Errorf("Expected message type 'player_move', got '%s'", msg.Type)
	}

	// Encode
	data, err := msg.Encode()
	if err != nil {
		t.Errorf("Failed to encode message: %v", err)
	}

	// Decode
	decoded, err := protocol.DecodeMessage(data)
	if err != nil {
		t.Errorf("Failed to decode message: %v", err)
	}

	if decoded.PlayerID != "player1" {
		t.Errorf("Expected player ID 'player1', got '%s'", decoded.PlayerID)
	}

	// Decode payload
	var movePayload protocol.PlayerMovePayload
	err = decoded.DecodePayload(&movePayload)
	if err != nil {
		t.Errorf("Failed to decode payload: %v", err)
	}

	if movePayload.X != 10.0 || movePayload.Y != 20.0 || movePayload.Z != 30.0 {
		t.Errorf("Payload incorrect: got (%f, %f, %f)", movePayload.X, movePayload.Y, movePayload.Z)
	}
}

func TestMatchmakingELO(t *testing.T) {
	// Test ELO calculation
	newWinner, newLoser := matchmaking.CalculateELO(1200, 1200, 32)

	if newWinner <= 1200 {
		t.Errorf("Winner rating should increase, got %d", newWinner)
	}

	if newLoser >= 1200 {
		t.Errorf("Loser rating should decrease, got %d", newLoser)
	}

	// Test with different ratings
	newWinner, newLoser = matchmaking.CalculateELO(1400, 1000, 32)

	if newWinner <= 1400 {
		t.Errorf("Higher rated winner should still gain rating, got %d", newWinner)
	}

	if newLoser >= 1000 {
		t.Errorf("Lower rated loser should still lose rating, got %d", newLoser)
	}
}

func TestMatchmakerQueue(t *testing.T) {
	rm := room.NewRoomManager()
	pm := player.NewPlayerManager()
	mm := matchmaking.NewMatchmaker(rm, pm)

	// Add players
	p1 := player.NewPlayer("player1", "Player 1")
	p2 := player.NewPlayer("player2", "Player 2")
	pm.AddPlayer(p1)
	pm.AddPlayer(p2)

	// Enqueue
	req1 := &matchmaking.MatchRequest{
		PlayerID: "player1",
		Mode:     matchmaking.ModeELO,
		Rating:   1200,
		GameType: "ranked",
	}

	req2 := &matchmaking.MatchRequest{
		PlayerID: "player2",
		Mode:     matchmaking.ModeELO,
		Rating:   1250,
		GameType: "ranked",
	}

	err := mm.Enqueue(req1)
	if err != nil {
		t.Errorf("Failed to enqueue player1: %v", err)
	}

	err = mm.Enqueue(req2)
	if err != nil {
		t.Errorf("Failed to enqueue player2: %v", err)
	}

	if mm.GetQueueSize() != 2 {
		t.Errorf("Expected queue size 2, got %d", mm.GetQueueSize())
	}

	// Try to enqueue again (should fail)
	err = mm.Enqueue(req1)
	if err != matchmaking.ErrAlreadyInQueue {
		t.Error("Should not be able to enqueue player already in queue")
	}

	// Dequeue
	err = mm.Dequeue("player1")
	if err != nil {
		t.Errorf("Failed to dequeue player1: %v", err)
	}

	if mm.GetQueueSize() != 1 {
		t.Errorf("Expected queue size 1 after dequeue, got %d", mm.GetQueueSize())
	}
}

func TestPlayerStats(t *testing.T) {
	p := player.NewPlayer("player1", "Player 1")

	// Record games
	p.RecordWin()
	p.RecordWin()
	p.RecordLoss()

	if p.Wins != 2 {
		t.Errorf("Expected 2 wins, got %d", p.Wins)
	}

	if p.Losses != 1 {
		t.Errorf("Expected 1 loss, got %d", p.Losses)
	}

	if p.GamesPlayed != 3 {
		t.Errorf("Expected 3 games played, got %d", p.GamesPlayed)
	}

	winRate := p.GetWinRate()
	if winRate < 66.0 || winRate > 67.0 {
		t.Errorf("Expected win rate ~66.67%%, got %f%%", winRate)
	}
}

func TestRoomFullError(t *testing.T) {
	gameRoom := room.NewRoom("room1", "Test Room", 2, 2)

	p1 := player.NewPlayer("player1", "Player 1")
	p2 := player.NewPlayer("player2", "Player 2")
	p3 := player.NewPlayer("player3", "Player 3")

	gameRoom.AddPlayer(p1)
	gameRoom.AddPlayer(p2)

	// Room should be full
	err := gameRoom.AddPlayer(p3)
	if err != room.ErrRoomFull {
		t.Error("Should return error when room is full")
	}
}

func TestPlayerStatusTransitions(t *testing.T) {
	p := player.NewPlayer("player1", "Player 1")

	if p.Status != player.StatusOnline {
		t.Errorf("Initial status should be online, got %s", p.Status)
	}

	p.SetRoom("room1")
	if p.Status != player.StatusInRoom {
		t.Errorf("Status should be in_room after joining room, got %s", p.Status)
	}

	p.SetRoom("")
	if p.Status != player.StatusOnline {
		t.Errorf("Status should be online after leaving room, got %s", p.Status)
	}

	p.SetStatus(player.StatusInGame)
	if p.Status != player.StatusInGame {
		t.Errorf("Status should be in_game, got %s", p.Status)
	}
}

func TestStateSynchronizerModes(t *testing.T) {
	playerIDs := []string{"player1", "player2"}
	gameState := room.NewGameState(playerIDs)

	// Test different sync modes
	modes := []sync.SyncMode{sync.SyncModeSnapshot, sync.SyncModeDelta, sync.SyncModeFrame}

	for _, mode := range modes {
		synchronizer := sync.NewStateSynchronizer("room1", gameState, mode)
		if synchronizer.GetSyncMode() != mode {
			t.Errorf("Expected sync mode %s, got %s", mode, synchronizer.GetSyncMode())
		}
	}
}

func TestConcurrentAccess(t *testing.T) {
	pm := player.NewPlayerManager()

	// Concurrent add/remove
	done := make(chan bool, 100)

	for i := 0; i < 50; i++ {
		go func(id int) {
			p := player.NewPlayer("player"+string(rune(id)), "Player")
			pm.AddPlayer(p)
			done <- true
		}(i)
	}

	for i := 0; i < 50; i++ {
		<-done
	}

	// Concurrent read
	for i := 0; i < 50; i++ {
		go func() {
			pm.GetPlayerCount()
			pm.GetOnlinePlayers()
			done <- true
		}()
	}

	for i := 0; i < 50; i++ {
		<-done
	}
}
