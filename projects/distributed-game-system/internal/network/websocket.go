package network

import (
	"encoding/json"
	"log"
	"net/http"
	"sync"
	"time"

	"github.com/gorilla/websocket"
	"github.com/distributed-game-system/internal/protocol"
)

const (
	// Time allowed to write a message to the peer
	writeWait = 10 * time.Second

	// Time allowed to read the next pong message from the peer
	pongWait = 60 * time.Second

	// Send pings to peer with this period. Must be less than pongWait
	pingPeriod = (pongWait * 9) / 10

	// Maximum message size allowed from peer
	maxMessageSize = 4096
)

var upgrader = websocket.Upgrader{
	ReadBufferSize:  1024,
	WriteBufferSize: 1024,
	CheckOrigin: func(r *http.Request) bool {
		return true // Allow all origins for development
	},
}

// Connection represents a WebSocket connection
type Connection struct {
	conn     *websocket.Conn
	send     chan []byte
	playerID string
	mu       sync.RWMutex
	closed   bool
}

// NewConnection creates a new WebSocket connection
func NewConnection(conn *websocket.Conn, playerID string) *Connection {
	return &Connection{
		conn:     conn,
		send:     make(chan []byte, 256),
		playerID: playerID,
	}
}

// GetPlayerID returns the player ID
func (c *Connection) GetPlayerID() string {
	return c.playerID
}

// ReadPump pumps messages from the websocket connection to the hub
func (c *Connection) ReadPump(hub *Hub, messageHandler func(*protocol.Message)) {
	defer func() {
		hub.Unregister(c)
		c.conn.Close()
	}()

	c.conn.SetReadLimit(maxMessageSize)
	c.conn.SetReadDeadline(time.Now().Add(pongWait))
	c.conn.SetPongHandler(func(string) error {
		c.conn.SetReadDeadline(time.Now().Add(pongWait))
		return nil
	})

	for {
		_, message, err := c.conn.ReadMessage()
		if err != nil {
			if websocket.IsUnexpectedCloseError(err, websocket.CloseGoingAway, websocket.CloseAbnormalClosure) {
				log.Printf("WebSocket error: %v", err)
			}
			break
		}

		msg, err := protocol.DecodeMessage(message)
		if err != nil {
			log.Printf("Error decoding message: %v", err)
			continue
		}

		// Handle heartbeat
		if msg.Type == protocol.MsgTypeHeartbeat {
			heartbeatMsg, _ := protocol.NewMessage(protocol.MsgTypeHeartbeat, c.playerID, "", nil)
			data, _ := heartbeatMsg.Encode()
			c.Send(data)
			continue
		}

		if messageHandler != nil {
			messageHandler(msg)
		}
	}
}

// WritePump pumps messages from the hub to the websocket connection
func (c *Connection) WritePump() {
	ticker := time.NewTicker(pingPeriod)
	defer func() {
		ticker.Stop()
		c.conn.Close()
	}()

	for {
		select {
		case message, ok := <-c.send:
			c.conn.SetWriteDeadline(time.Now().Add(writeWait))
			if !ok {
				c.conn.WriteMessage(websocket.CloseMessage, []byte{})
				return
			}

			w, err := c.conn.NextWriter(websocket.TextMessage)
			if err != nil {
				return
			}
			w.Write(message)

			// Add queued messages to the current message
			n := len(c.send)
			for i := 0; i < n; i++ {
				w.Write([]byte("\n"))
				w.Write(<-c.send)
			}

			if err := w.Close(); err != nil {
				return
			}

		case <-ticker.C:
			c.conn.SetWriteDeadline(time.Now().Add(writeWait))
			if err := c.conn.WriteMessage(websocket.PingMessage, nil); err != nil {
				return
			}
		}
	}
}

// Send sends a message to the connection
func (c *Connection) Send(message []byte) {
	c.mu.RLock()
	defer c.mu.RUnlock()
	if c.closed {
		return
	}
	select {
	case c.send <- message:
	default:
		// Channel full, connection likely dead
		c.Close()
	}
}

// Close closes the connection
func (c *Connection) Close() {
	c.mu.Lock()
	defer c.mu.Unlock()
	if !c.closed {
		c.closed = true
		close(c.send)
	}
}

// Hub maintains the set of active connections
type Hub struct {
	connections    map[string]*Connection
	rooms          map[string]map[string]*Connection // roomID -> playerID -> connection
	mu             sync.RWMutex
	messageHandler func(*protocol.Message)
}

// NewHub creates a new Hub
func NewHub() *Hub {
	return &Hub{
		connections: make(map[string]*Connection),
		rooms:       make(map[string]map[string]*Connection),
	}
}

// SetMessageHandler sets the message handler function
func (h *Hub) SetMessageHandler(handler func(*protocol.Message)) {
	h.messageHandler = handler
}

// Register registers a new connection
func (h *Hub) Register(conn *Connection) {
	h.mu.Lock()
	defer h.mu.Unlock()
	h.connections[conn.GetPlayerID()] = conn
	log.Printf("Player %s connected", conn.GetPlayerID())
}

// Unregister removes a connection
func (h *Hub) Unregister(conn *Connection) {
	h.mu.Lock()
	defer h.mu.Unlock()

	playerID := conn.GetPlayerID()
	delete(h.connections, playerID)

	// Remove from all rooms
	for roomID, players := range h.rooms {
		delete(players, playerID)
		if len(players) == 0 {
			delete(h.rooms, roomID)
		}
	}

	log.Printf("Player %s disconnected", playerID)
}

// JoinRoom adds a connection to a room
func (h *Hub) JoinRoom(roomID, playerID string) {
	h.mu.Lock()
	defer h.mu.Unlock()

	if _, ok := h.rooms[roomID]; !ok {
		h.rooms[roomID] = make(map[string]*Connection)
	}

	if conn, ok := h.connections[playerID]; ok {
		h.rooms[roomID][playerID] = conn
	}
}

// LeaveRoom removes a connection from a room
func (h *Hub) LeaveRoom(roomID, playerID string) {
	h.mu.Lock()
	defer h.mu.Unlock()

	if players, ok := h.rooms[roomID]; ok {
		delete(players, playerID)
		if len(players) == 0 {
			delete(h.rooms, roomID)
		}
	}
}

// BroadcastToRoom sends a message to all connections in a room
func (h *Hub) BroadcastToRoom(roomID string, message []byte, excludePlayer string) {
	h.mu.RLock()
	defer h.mu.RUnlock()

	if players, ok := h.rooms[roomID]; ok {
		for playerID, conn := range players {
			if playerID != excludePlayer {
				conn.Send(message)
			}
		}
	}
}

// SendToPlayer sends a message to a specific player
func (h *Hub) SendToPlayer(playerID string, message []byte) {
	h.mu.RLock()
	defer h.mu.RUnlock()

	if conn, ok := h.connections[playerID]; ok {
		conn.Send(message)
	}
}

// GetRoomPlayers returns the list of players in a room
func (h *Hub) GetRoomPlayers(roomID string) []string {
	h.mu.RLock()
	defer h.mu.RUnlock()

	var players []string
	if roomPlayers, ok := h.rooms[roomID]; ok {
		for playerID := range roomPlayers {
			players = append(players, playerID)
		}
	}
	return players
}

// GetConnectionCount returns the number of active connections
func (h *Hub) GetConnectionCount() int {
	h.mu.RLock()
	defer h.mu.RUnlock()
	return len(h.connections)
}

// HandleWebSocket handles WebSocket upgrade and connection setup
func HandleWebSocket(hub *Hub, w http.ResponseWriter, r *http.Request, playerID string) {
	conn, err := upgrader.Upgrade(w, r, nil)
	if err != nil {
		log.Printf("WebSocket upgrade error: %v", err)
		return
	}

	connection := NewConnection(conn, playerID)
	hub.Register(connection)

	go connection.WritePump()
	go connection.ReadPump(hub, hub.messageHandler)
}

// EncodeAndSend encodes a message and sends it to a player
func EncodeAndSend(hub *Hub, playerID string, msg *protocol.Message) error {
	data, err := msg.Encode()
	if err != nil {
		return err
	}
	hub.SendToPlayer(playerID, data)
	return nil
}

// EncodeAndBroadcast encodes a message and broadcasts it to a room
func EncodeAndBroadcast(hub *Hub, roomID string, msg *protocol.Message, excludePlayer string) error {
	data, err := msg.Encode()
	if err != nil {
		return err
	}
	hub.BroadcastToRoom(roomID, data, excludePlayer)
	return nil
}
