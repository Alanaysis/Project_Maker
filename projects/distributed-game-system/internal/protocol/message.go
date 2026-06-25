package protocol

import (
	"encoding/json"
	"time"
)

// MessageType defines the type of game messages
type MessageType string

const (
	// Connection messages
	MsgTypeConnect    MessageType = "connect"
	MsgTypeDisconnect MessageType = "disconnect"
	MsgTypeHeartbeat  MessageType = "heartbeat"

	// Room messages
	MsgTypeCreateRoom  MessageType = "create_room"
	MsgTypeJoinRoom    MessageType = "join_room"
	MsgTypeLeaveRoom   MessageType = "leave_room"
	MsgTypeRoomList    MessageType = "room_list"
	MsgTypeRoomInfo    MessageType = "room_info"

	// Player messages
	MsgTypePlayerJoin  MessageType = "player_join"
	MsgTypePlayerLeave MessageType = "player_leave"
	MsgTypePlayerReady MessageType = "player_ready"
	MsgTypePlayerMove  MessageType = "player_move"

	// Game state messages
	MsgTypeGameState    MessageType = "game_state"
	MsgTypeStateSync    MessageType = "state_sync"
	MsgTypeStateDelta   MessageType = "state_delta"
	MsgTypeFrameInput   MessageType = "frame_input"
	MsgTypeFrameSync    MessageType = "frame_sync"
	MsgTypeGameStart    MessageType = "game_start"
	MsgTypeGameEnd      MessageType = "game_end"

	// Matchmaking messages
	MsgTypeMatchRequest  MessageType = "match_request"
	MsgTypeMatchResult   MessageType = "match_result"
	MsgTypeMatchCancel   MessageType = "match_cancel"

	// Error messages
	MsgTypeError MessageType = "error"
)

// Message is the base message structure
type Message struct {
	Type      MessageType     `json:"type"`
	ID        string          `json:"id"`
	Timestamp time.Time       `json:"timestamp"`
	PlayerID  string          `json:"player_id,omitempty"`
	RoomID    string          `json:"room_id,omitempty"`
	Payload   json.RawMessage `json:"payload,omitempty"`
}

// ConnectPayload is sent when a player connects
type ConnectPayload struct {
	PlayerName string `json:"player_name"`
	Token      string `json:"token,omitempty"`
}

// RoomPayload contains room information
type RoomPayload struct {
	RoomID    string   `json:"room_id"`
	RoomName  string   `json:"room_name"`
	MaxPlayers int     `json:"max_players"`
	Players    []string `json:"players"`
	Status     string   `json:"status"`
	CreatedAt  time.Time `json:"created_at"`
}

// PlayerMovePayload contains player movement data
type PlayerMovePayload struct {
	X      float64 `json:"x"`
	Y      float64 `json:"y"`
	Z      float64 `json:"z"`
	Action string  `json:"action,omitempty"`
}

// GameStatePayload contains the full game state
type GameStatePayload struct {
	Frame     uint64                 `json:"frame"`
	State     map[string]interface{} `json:"state"`
	Timestamp time.Time              `json:"timestamp"`
}

// StateDeltaPayload contains state changes since last sync
type StateDeltaPayload struct {
	Frame     uint64                 `json:"frame"`
	Changes   map[string]interface{} `json:"changes"`
	Timestamp time.Time              `json:"timestamp"`
}

// FrameInputPayload contains player input for frame sync
type FrameInputPayload struct {
	Frame    uint64            `json:"frame"`
	PlayerID string            `json:"player_id"`
	Inputs   map[string]interface{} `json:"inputs"`
}

// MatchRequestPayload is sent when requesting a match
type MatchRequestPayload struct {
	Mode     string `json:"mode"` // "random" or "elo"
	Rating   int    `json:"rating,omitempty"`
	GameType string `json:"game_type"`
}

// MatchResultPayload contains match result
type MatchResultPayload struct {
	RoomID   string   `json:"room_id"`
	Players  []string `json:"players"`
	Mode     string   `json:"mode"`
}

// ErrorPayload contains error information
type ErrorPayload struct {
	Code    int    `json:"code"`
	Message string `json:"message"`
}

// NewMessage creates a new message
func NewMessage(msgType MessageType, playerID, roomID string, payload interface{}) (*Message, error) {
	var payloadBytes json.RawMessage
	if payload != nil {
		var err error
		payloadBytes, err = json.Marshal(payload)
		if err != nil {
			return nil, err
		}
	}

	return &Message{
		Type:      msgType,
		ID:        generateID(),
		Timestamp: time.Now(),
		PlayerID:  playerID,
		RoomID:    roomID,
		Payload:   payloadBytes,
	}, nil
}

// Encode serializes the message to JSON
func (m *Message) Encode() ([]byte, error) {
	return json.Marshal(m)
}

// DecodeMessage deserializes JSON to Message
func DecodeMessage(data []byte) (*Message, error) {
	var msg Message
	if err := json.Unmarshal(data, &msg); err != nil {
		return nil, err
	}
	return &msg, nil
}

// DecodePayload decodes the payload into the given structure
func (m *Message) DecodePayload(v interface{}) error {
	if m.Payload == nil {
		return nil
	}
	return json.Unmarshal(m.Payload, v)
}

func generateID() string {
	return time.Now().Format("20060102150405") + "-" + randomString(8)
}

func randomString(n int) string {
	const letters = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
	b := make([]byte, n)
	for i := range b {
		b[i] = letters[time.Now().UnixNano()%int64(len(letters))]
	}
	return string(b)
}
