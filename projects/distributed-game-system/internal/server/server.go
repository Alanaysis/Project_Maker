package server

import (
	"log"
	"net/http"
	"time"

	"github.com/distributed-game-system/internal/matchmaking"
	"github.com/distributed-game-system/internal/network"
	"github.com/distributed-game-system/internal/player"
	"github.com/distributed-game-system/internal/protocol"
	"github.com/distributed-game-system/internal/room"
	"github.com/distributed-game-system/internal/sync"
)

// GameServer is the main game server
type GameServer struct {
	hub        *network.Hub
	roomMgr    *room.RoomManager
	playerMgr  *player.PlayerManager
	matchmaker *matchmaking.Matchmaker
	syncMgr    map[string]*sync.StateSynchronizer
}

// NewGameServer creates a new game server
func NewGameServer() *GameServer {
	hub := network.NewHub()
	roomMgr := room.NewRoomManager()
	playerMgr := player.NewPlayerManager()
	matchmaker := matchmaking.NewMatchmaker(roomMgr, playerMgr)

	server := &GameServer{
		hub:        hub,
		roomMgr:    roomMgr,
		playerMgr:  playerMgr,
		matchmaker: matchmaker,
		syncMgr:    make(map[string]*sync.StateSynchronizer),
	}

	hub.SetMessageHandler(server.handleMessage)
	return server
}

// Start starts the game server
func (gs *GameServer) Start(addr string) error {
	// Start matchmaker
	gs.matchmaker.Start()

	// Start match result handler
	go gs.handleMatchResults()

	// Setup HTTP routes
	http.HandleFunc("/ws", gs.handleWebSocket)
	http.HandleFunc("/api/rooms", gs.handleRoomList)
	http.HandleFunc("/api/players", gs.handlePlayerList)
	http.HandleFunc("/api/status", gs.handleStatus)

	log.Printf("Game server starting on %s", addr)
	return http.ListenAndServe(addr, nil)
}

// handleMessage handles incoming messages
func (gs *GameServer) handleMessage(msg *protocol.Message) {
	switch msg.Type {
	case protocol.MsgTypeConnect:
		gs.handleConnect(msg)
	case protocol.MsgTypeDisconnect:
		gs.handleDisconnect(msg)
	case protocol.MsgTypeCreateRoom:
		gs.handleCreateRoom(msg)
	case protocol.MsgTypeJoinRoom:
		gs.handleJoinRoom(msg)
	case protocol.MsgTypeLeaveRoom:
		gs.handleLeaveRoom(msg)
	case protocol.MsgTypeRoomList:
		gs.handleRoomListRequest(msg)
	case protocol.MsgTypePlayerReady:
		gs.handlePlayerReady(msg)
	case protocol.MsgTypePlayerMove:
		gs.handlePlayerMove(msg)
	case protocol.MsgTypeMatchRequest:
		gs.handleMatchRequest(msg)
	case protocol.MsgTypeMatchCancel:
		gs.handleMatchCancel(msg)
	case protocol.MsgTypeFrameInput:
		gs.handleFrameInput(msg)
	default:
		log.Printf("Unknown message type: %s", msg.Type)
	}
}

// handleConnect handles player connection
func (gs *GameServer) handleConnect(msg *protocol.Message) {
	var payload protocol.ConnectPayload
	if err := msg.DecodePayload(&payload); err != nil {
		log.Printf("Error decoding connect payload: %v", err)
		return
	}

	// Create player
	p := player.NewPlayer(msg.PlayerID, payload.PlayerName)
	gs.playerMgr.AddPlayer(p)

	// Send connection confirmation
	response, _ := protocol.NewMessage(protocol.MsgTypeConnect, msg.PlayerID, "", map[string]interface{}{
		"player_id": msg.PlayerID,
		"status":    "connected",
	})
	network.EncodeAndSend(gs.hub, msg.PlayerID, response)
}

// handleDisconnect handles player disconnection
func (gs *GameServer) handleDisconnect(msg *protocol.Message) {
	// Remove from rooms
	if p, ok := gs.playerMgr.GetPlayer(msg.PlayerID); ok {
		if p.RoomID != "" {
			gs.handleLeaveRoom(msg)
		}
	}

	// Remove player
	gs.playerMgr.RemovePlayer(msg.PlayerID)
}

// handleCreateRoom handles room creation
func (gs *GameServer) handleCreateRoom(msg *protocol.Message) {
	var payload protocol.RoomPayload
	if err := msg.DecodePayload(&payload); err != nil {
		log.Printf("Error decoding room payload: %v", err)
		return
	}

	// Create room
	gameRoom := gs.roomMgr.CreateRoom(payload.RoomID, payload.RoomName, payload.MaxPlayers, 2)

	// Add player to room
	if p, ok := gs.playerMgr.GetPlayer(msg.PlayerID); ok {
		gameRoom.AddPlayer(p)
		gs.hub.JoinRoom(payload.RoomID, msg.PlayerID)
	}

	// Send room info
	response, _ := protocol.NewMessage(protocol.MsgTypeRoomInfo, msg.PlayerID, payload.RoomID, &protocol.RoomPayload{
		RoomID:     gameRoom.ID,
		RoomName:   gameRoom.Name,
		MaxPlayers: gameRoom.MaxPlayers,
		Players:    gameRoom.GetPlayerIDs(),
		Status:     string(gameRoom.Status),
		CreatedAt:  gameRoom.CreatedAt,
	})
	network.EncodeAndSend(gs.hub, msg.PlayerID, response)
}

// handleJoinRoom handles player joining a room
func (gs *GameServer) handleJoinRoom(msg *protocol.Message) {
	var payload protocol.RoomPayload
	if err := msg.DecodePayload(&payload); err != nil {
		log.Printf("Error decoding room payload: %v", err)
		return
	}

	gameRoom, ok := gs.roomMgr.GetRoom(payload.RoomID)
	if !ok {
		gs.sendError(msg.PlayerID, "Room not found")
		return
	}

	// Add player to room
	if p, ok := gs.playerMgr.GetPlayer(msg.PlayerID); ok {
		if err := gameRoom.AddPlayer(p); err != nil {
			gs.sendError(msg.PlayerID, err.Error())
			return
		}
		gs.hub.JoinRoom(payload.RoomID, msg.PlayerID)
	}

	// Notify all players in room
	joinMsg, _ := protocol.NewMessage(protocol.MsgTypePlayerJoin, msg.PlayerID, payload.RoomID, map[string]interface{}{
		"player_id": msg.PlayerID,
	})
	network.EncodeAndBroadcast(gs.hub, payload.RoomID, joinMsg, "")

	// Send room info to joining player
	response, _ := protocol.NewMessage(protocol.MsgTypeRoomInfo, msg.PlayerID, payload.RoomID, &protocol.RoomPayload{
		RoomID:     gameRoom.ID,
		RoomName:   gameRoom.Name,
		MaxPlayers: gameRoom.MaxPlayers,
		Players:    gameRoom.GetPlayerIDs(),
		Status:     string(gameRoom.Status),
		CreatedAt:  gameRoom.CreatedAt,
	})
	network.EncodeAndSend(gs.hub, msg.PlayerID, response)
}

// handleLeaveRoom handles player leaving a room
func (gs *GameServer) handleLeaveRoom(msg *protocol.Message) {
	p, ok := gs.playerMgr.GetPlayer(msg.PlayerID)
	if !ok {
		return
	}

	roomID := p.RoomID
	if roomID == "" {
		return
	}

	gameRoom, ok := gs.roomMgr.GetRoom(roomID)
	if !ok {
		return
	}

	// Remove player from room
	gameRoom.RemovePlayer(msg.PlayerID)
	gs.hub.LeaveRoom(roomID, msg.PlayerID)

	// Notify remaining players
	leaveMsg, _ := protocol.NewMessage(protocol.MsgTypePlayerLeave, msg.PlayerID, roomID, map[string]interface{}{
		"player_id": msg.PlayerID,
	})
	network.EncodeAndBroadcast(gs.hub, roomID, leaveMsg, "")

	// If room is empty, delete it
	if gameRoom.GetPlayerCount() == 0 {
		gs.roomMgr.DeleteRoom(roomID)
		// Stop sync if exists
		if synchronizer, ok := gs.syncMgr[roomID]; ok {
			synchronizer.Stop()
			delete(gs.syncMgr, roomID)
		}
	}
}

// handleRoomListRequest handles room list request
func (gs *GameServer) handleRoomListRequest(msg *protocol.Message) {
	rooms := gs.roomMgr.GetRoomList()
	var roomList []protocol.RoomPayload
	for _, r := range rooms {
		roomList = append(roomList, protocol.RoomPayload{
			RoomID:     r.ID,
			RoomName:   r.Name,
			MaxPlayers: r.MaxPlayers,
			Players:    r.GetPlayerIDs(),
			Status:     string(r.Status),
			CreatedAt:  r.CreatedAt,
		})
	}

	response, _ := protocol.NewMessage(protocol.MsgTypeRoomList, msg.PlayerID, "", roomList)
	network.EncodeAndSend(gs.hub, msg.PlayerID, response)
}

// handlePlayerReady handles player ready status
func (gs *GameServer) handlePlayerReady(msg *protocol.Message) {
	p, ok := gs.playerMgr.GetPlayer(msg.PlayerID)
	if !ok || p.RoomID == "" {
		return
	}

	gameRoom, ok := gs.roomMgr.GetRoom(p.RoomID)
	if !ok {
		return
	}

	// Check if game can start
	if gameRoom.CanStart() {
		// Start game
		if err := gameRoom.Start(); err != nil {
			gs.sendError(msg.PlayerID, err.Error())
			return
		}

		// Create state synchronizer
		synchronizer := sync.NewStateSynchronizer(gameRoom.ID, gameRoom.GameState, sync.SyncModeFrame)
		gs.syncMgr[gameRoom.ID] = synchronizer

		// Start sync
		broadcastFunc := func(m *protocol.Message) {
			network.EncodeAndBroadcast(gs.hub, gameRoom.ID, m, "")
		}
		synchronizer.Start(broadcastFunc)

		// Notify all players
		startMsg, _ := protocol.NewMessage(protocol.MsgTypeGameStart, "", gameRoom.ID, map[string]interface{}{
			"room_id": gameRoom.ID,
			"players": gameRoom.GetPlayerIDs(),
		})
		network.EncodeAndBroadcast(gs.hub, gameRoom.ID, startMsg, "")
	}
}

// handlePlayerMove handles player movement
func (gs *GameServer) handlePlayerMove(msg *protocol.Message) {
	var payload protocol.PlayerMovePayload
	if err := msg.DecodePayload(&payload); err != nil {
		log.Printf("Error decoding move payload: %v", err)
		return
	}

	p, ok := gs.playerMgr.GetPlayer(msg.PlayerID)
	if !ok || p.RoomID == "" {
		return
	}

	gameRoom, ok := gs.roomMgr.GetRoom(p.RoomID)
	if !ok || gameRoom.GameState == nil {
		return
	}

	// Update game state
	gameRoom.GameState.UpdatePlayer(msg.PlayerID, payload.X, payload.Y, payload.Z)

	// Broadcast to other players
	moveMsg, _ := protocol.NewMessage(protocol.MsgTypePlayerMove, msg.PlayerID, p.RoomID, &payload)
	network.EncodeAndBroadcast(gs.hub, p.RoomID, moveMsg, msg.PlayerID)
}

// handleMatchRequest handles matchmaking request
func (gs *GameServer) handleMatchRequest(msg *protocol.Message) {
	var payload protocol.MatchRequestPayload
	if err := msg.DecodePayload(&payload); err != nil {
		log.Printf("Error decoding match payload: %v", err)
		return
	}

	// Get player rating
	rating := 1200 // Default rating
	if p, ok := gs.playerMgr.GetPlayer(msg.PlayerID); ok {
		rating = p.Rating
	}

	request := &matchmaking.MatchRequest{
		PlayerID: msg.PlayerID,
		Mode:     matchmaking.Mode(payload.Mode),
		Rating:   rating,
		GameType: payload.GameType,
	}

	if err := gs.matchmaker.Enqueue(request); err != nil {
		gs.sendError(msg.PlayerID, err.Error())
		return
	}

	// Send queue confirmation
	response, _ := protocol.NewMessage(protocol.MsgTypeMatchRequest, msg.PlayerID, "", map[string]interface{}{
		"status": "queued",
		"mode":   payload.Mode,
	})
	network.EncodeAndSend(gs.hub, msg.PlayerID, response)
}

// handleMatchCancel handles match cancellation
func (gs *GameServer) handleMatchCancel(msg *protocol.Message) {
	if err := gs.matchmaker.Dequeue(msg.PlayerID); err != nil {
		gs.sendError(msg.PlayerID, err.Error())
		return
	}

	response, _ := protocol.NewMessage(protocol.MsgTypeMatchCancel, msg.PlayerID, "", map[string]interface{}{
		"status": "cancelled",
	})
	network.EncodeAndSend(gs.hub, msg.PlayerID, response)
}

// handleFrameInput handles frame input for frame sync
func (gs *GameServer) handleFrameInput(msg *protocol.Message) {
	var payload protocol.FrameInputPayload
	if err := msg.DecodePayload(&payload); err != nil {
		log.Printf("Error decoding frame input: %v", err)
		return
	}

	p, ok := gs.playerMgr.GetPlayer(msg.PlayerID)
	if !ok || p.RoomID == "" {
		return
	}

	if synchronizer, ok := gs.syncMgr[p.RoomID]; ok {
		synchronizer.ProcessInput(&payload)
	}
}

// handleMatchResults handles match results from matchmaker
func (gs *GameServer) handleMatchResults() {
	for result := range gs.matchmaker.GetMatchResult() {
		// Notify all matched players
		for _, playerID := range result.Players {
			msg, _ := protocol.NewMessage(protocol.MsgTypeMatchResult, playerID, result.RoomID, &protocol.MatchResultPayload{
				RoomID:  result.RoomID,
				Players: result.Players,
				Mode:    string(result.Mode),
			})
			network.EncodeAndSend(gs.hub, playerID, msg)
		}
	}
}

// handleWebSocket handles WebSocket connections
func (gs *GameServer) handleWebSocket(w http.ResponseWriter, r *http.Request) {
	playerID := r.URL.Query().Get("player_id")
	if playerID == "" {
		http.Error(w, "player_id required", http.StatusBadRequest)
		return
	}

	network.HandleWebSocket(gs.hub, w, r, playerID)
}

// handleRoomList handles HTTP room list request
func (gs *GameServer) handleRoomList(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	rooms := gs.roomMgr.GetRoomList()
	var roomList []map[string]interface{}
	for _, r := range rooms {
		roomList = append(roomList, map[string]interface{}{
			"id":          r.ID,
			"name":        r.Name,
			"max_players": r.MaxPlayers,
			"players":     r.GetPlayerIDs(),
			"status":      string(r.Status),
		})
	}
	// Simple JSON encoding
	w.Write([]byte("["))
	for i, r := range roomList {
		if i > 0 {
			w.Write([]byte(","))
		}
		w.Write([]byte(`{"id":"` + r["id"].(string) + `","name":"` + r["name"].(string) + `","status":"` + r["status"].(string) + `"}`))
	}
	w.Write([]byte("]"))
}

// handlePlayerList handles HTTP player list request
func (gs *GameServer) handlePlayerList(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	players := gs.playerMgr.GetOnlinePlayers()
	w.Write([]byte("["))
	for i, p := range players {
		if i > 0 {
			w.Write([]byte(","))
		}
		w.Write([]byte(`{"id":"` + p.ID + `","name":"` + p.Name + `","rating":` + string(rune(p.Rating)) + `}`))
	}
	w.Write([]byte("]"))
}

// handleStatus handles HTTP status request
func (gs *GameServer) handleStatus(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	status := map[string]interface{}{
		"connections": gs.hub.GetConnectionCount(),
		"rooms":       len(gs.roomMgr.GetRoomList()),
		"players":     gs.playerMgr.GetPlayerCount(),
		"queue":       gs.matchmaker.GetQueueStatus(),
		"uptime":      time.Now().Format(time.RFC3339),
	}
	_ = status
	w.Write([]byte(`{"status":"running"}`))
}

// sendError sends an error message to a player
func (gs *GameServer) sendError(playerID, message string) {
	errMsg, _ := protocol.NewMessage(protocol.MsgTypeError, playerID, "", &protocol.ErrorPayload{
		Code:    400,
		Message: message,
	})
	network.EncodeAndSend(gs.hub, playerID, errMsg)
}
