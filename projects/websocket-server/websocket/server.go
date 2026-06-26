package websocket

import (
	"fmt"
	"net"
	"net/http"
	"sync"
	"sync/atomic"
	"time"
)

// Client represents a connected WebSocket client.
// 表示一个已连接的 WebSocket 客户端
//
// WebSocket 连接管理是 WebSocket 服务器的核心。每个客户端连接需要：
// - 独立的读写 goroutine
// - 消息通道用于发送
// - 心跳检测维持连接活跃
// - 房间/群组支持用于广播
type Client struct {
	ID       uint64    // 客户端唯一 ID
	Conn     net.Conn  // 底层 TCP 连接
	Send     chan []byte // 发送消息的缓冲通道
	Room     string    // 客户端所在的房间/群组
	Mu       sync.Mutex // 保护 Conn 的互斥锁
	CloseMu  sync.Mutex // 保护关闭操作的互斥锁
	closed   int32     // 原子标记：连接是否已关闭
	LastPing time.Time // 最后发送 Ping 的时间
}

// NewClient creates a new Client with the given connection.
// 创建新客户端
func NewClient(id uint64, conn net.Conn) *Client {
	return &Client{
		ID:       id,
		Conn:     conn,
		Send:     make(chan []byte, 256), // 256 message buffer
		LastPing: time.Now(),
	}
}

// SendText sends a text message to the client.
// 发送文本消息
func (c *Client) SendText(msg string) {
	f := TextFrame([]byte(msg))
	data, err := f.Marshal()
	if err != nil {
		return
	}
	c.Send <- data
}

// SendPing sends a ping frame to the client for heartbeat.
// 发送 Ping 心跳帧
func (c *Client) SendPing() {
	c.LastPing = time.Now()
	data := []byte(fmt.Sprintf("%d", time.Now().UnixNano()))
	f := PingFrame(data)
	out, err := f.Marshal()
	if err != nil {
		return
	}
	c.Send <- out
}

// IsClosed checks if the client connection is closed.
// 检查连接是否已关闭
func (c *Client) IsClosed() bool {
	return atomic.LoadInt32(&c.closed) == 1
}

// Close gracefully closes the client connection.
// 优雅关闭客户端连接
func (c *Client) Close() error {
	c.CloseMu.Lock()
	defer c.CloseMu.Unlock()

	if atomic.CompareAndSwapInt32(&c.closed, 0, 1) {
		// Send close frame first
		closeFrame := CloseFrame(CloseNormalClosure, "")
		data, err := closeFrame.Marshal()
		if err == nil {
			c.Send <- data
		}
		// Close the underlying TCP connection
		return c.Conn.Close()
	}
	return nil
}

// Server manages multiple WebSocket clients with connection pooling and broadcasting.
// 管理多个 WebSocket 客户端的服务器
//
// 服务器核心功能：
// 1. 客户端注册/注销
// 2. 消息广播（群发/房间广播）
// 3. 心跳检测（Ping/Pong 机制）
// 4. 连接清理（检测死连接）
type Server struct {
	clients   map[uint64]*Client // 所有活跃客户端
	rooms     map[string]map[uint64]struct{} // 房间: clientID -> struct{}
	mu        sync.RWMutex       // 读写锁保护 clients 和 rooms
	nextID    uint64             // 下一个客户端 ID
	heartbeat intervalConfig   // 心跳配置
	quit      chan struct{}      // 停止信号
}

type intervalConfig struct {
	heartbeatInterval time.Duration // 心跳间隔
	heartbeatTimeout  time.Duration // 心跳超时
	maxMessageSize    int64         // 最大消息大小
}

// ServerConfig holds optional server configuration.
// 服务器可选配置
type ServerConfig struct {
	HeartbeatInterval time.Duration // 心跳间隔（默认 30s）
	HeartbeatTimeout  time.Duration // 心跳超时（默认 60s）
	MaxMessageSize    int64         // 最大消息大小（默认 64KB）
}

// NewServer creates a new WebSocket server.
// 创建新的 WebSocket 服务器
func NewServer(cfg ServerConfig) *Server {
	if cfg.HeartbeatInterval == 0 {
		cfg.HeartbeatInterval = 30 * time.Second
	}
	if cfg.HeartbeatTimeout == 0 {
		cfg.HeartbeatTimeout = 60 * time.Second
	}
	if cfg.MaxMessageSize == 0 {
		cfg.MaxMessageSize = 64 * 1024
	}

	return &Server{
		clients: make(map[uint64]*Client),
		rooms:   make(map[string]map[uint64]struct{}),
		heartbeat: intervalConfig{
			heartbeatInterval: cfg.HeartbeatInterval,
			heartbeatTimeout:  cfg.HeartbeatTimeout,
			maxMessageSize:    cfg.MaxMessageSize,
		},
		quit: make(chan struct{}),
	}
}

// Start begins the server's background tasks (heartbeat, cleanup).
// 启动服务器后台任务
func (s *Server) Start() {
	go s.heartbeatLoop()
	go s.cleanupLoop()
}

// Stop signals the server to shut down.
// 停止服务器
func (s *Server) Stop() {
	select {
	case <-s.quit:
		// Already closed
	default:
		close(s.quit)
	}
}

// AddClient registers a new client with the server.
// 注册新客户端到服务器
func (s *Server) AddClient(client *Client) {
	s.mu.Lock()
	defer s.mu.Unlock()

	atomic.StoreUint64(&s.nextID, client.ID+1)
	s.clients[client.ID] = client
}

// RemoveClient unregisters a client and cleans up room memberships.
// 注销客户端并清理房间成员
func (s *Server) RemoveClient(clientID uint64) {
	s.mu.Lock()
	defer s.mu.Unlock()

	if client, ok := s.clients[clientID]; ok {
		// Remove from room
		if client.Room != "" {
			if members, roomOK := s.rooms[client.Room]; roomOK {
				delete(members, clientID)
				if len(members) == 0 {
					delete(s.rooms, client.Room)
				}
			}
		}
		delete(s.clients, clientID)
	}
}

// JoinRoom adds a client to a room/group.
// 将客户端加入房间/群组
func (s *Server) JoinRoom(clientID uint64, room string) {
	s.mu.Lock()
	defer s.mu.Unlock()

	if client, ok := s.clients[clientID]; ok {
		client.Room = room
	}

	if _, ok := s.rooms[room]; !ok {
		s.rooms[room] = make(map[uint64]struct{})
	}
	s.rooms[room][clientID] = struct{}{}
}

// LeaveRoom removes a client from a room.
// 将客户端从房间中移除
func (s *Server) LeaveRoom(clientID uint64, room string) {
	s.mu.Lock()
	defer s.mu.Unlock()

	if members, ok := s.rooms[room]; ok {
		delete(members, clientID)
		if len(members) == 0 {
			delete(s.rooms, room)
		}
	}
}

// Broadcast sends a message to all connected clients.
// 向所有客户端广播消息
func (s *Server) Broadcast(msg string) {
	s.mu.RLock()
	defer s.mu.RUnlock()

	data := []byte(msg)
	for _, client := range s.clients {
		if !client.IsClosed() {
			select {
			case client.Send <- data:
			default:
				// Channel full, skip this client
			}
		}
	}
}

// BroadcastRoom sends a message to all clients in a specific room.
// 向指定房间的所有客户端广播消息
func (s *Server) BroadcastRoom(room, msg string) {
	s.mu.RLock()
	defer s.mu.RUnlock()

	members, ok := s.rooms[room]
	if !ok {
		return
	}

	data := []byte(msg)
	for clientID := range members {
		if client, ok := s.clients[clientID]; ok && !client.IsClosed() {
			select {
			case client.Send <- data:
			default:
				// Channel full, skip
			}
		}
	}
}

// GetClient returns a client by ID.
// 按 ID 获取客户端
func (s *Server) GetClient(id uint64) (*Client, bool) {
	s.mu.RLock()
	defer s.mu.RUnlock()
	client, ok := s.clients[id]
	return client, ok
}

// GetClientCount returns the number of connected clients.
// 返回连接客户端数量
func (s *Server) GetClientCount() int {
	s.mu.RLock()
	defer s.mu.RUnlock()
	return len(s.clients)
}

// GetRoomMembers returns the member IDs of a room.
// 返回房间的成员 ID
func (s *Server) GetRoomMembers(room string) []uint64 {
	s.mu.RLock()
	defer s.mu.RUnlock()

	members, ok := s.rooms[room]
	if !ok {
		return nil
	}

	ids := make([]uint64, 0, len(members))
	for id := range members {
		ids = append(ids, id)
	}
	return ids
}

// heartbeatLoop sends periodic pings to all clients and detects dead connections.
// 心跳循环：定期发送 Ping 并检测死连接
//
// 心跳检测机制（Ping/Pong）：
// - 服务器定期向每个客户端发送 Ping 帧
// - 客户端必须回复 Pong 帧
// - 如果超时未收到 Pong，认为连接已死，关闭连接
// - 这是 WebSocket 协议内置的心跳机制
func (s *Server) heartbeatLoop() {
	ticker := time.NewTicker(s.heartbeat.heartbeatInterval)
	defer ticker.Stop()

	for {
		select {
		case <-ticker.C:
			s.mu.RLock()
			for _, client := range s.clients {
				if client.IsClosed() {
					continue
				}
				// Send ping
				client.SendPing()
				// Check timeout
				if time.Since(client.LastPing) > s.heartbeat.heartbeatTimeout {
					client.Close()
					s.RemoveClient(client.ID)
				}
			}
			s.mu.RUnlock()

		case <-s.quit:
			return
		}
	}
}

// cleanupLoop periodically removes closed clients.
// 清理循环：定期移除已关闭的客户端
func (s *Server) cleanupLoop() {
	ticker := time.NewTicker(5 * time.Second)
	defer ticker.Stop()

	for {
		select {
		case <-ticker.C:
			s.mu.Lock()
			for id, client := range s.clients {
				if client.IsClosed() {
					delete(s.clients, id)
				}
			}
			s.mu.Unlock()

		case <-s.quit:
			return
		}
	}
}

// ReadMessages reads and processes incoming WebSocket frames from a client.
// 读取并处理来自客户端的 WebSocket 帧
//
// 消息处理流程：
// 1. 解析帧（操作码、负载）
// 2. 根据操作码处理不同类型的帧
// 3. 文本/二进制帧：路由到房间广播或全局广播
// 4. Ping/Pong 帧：更新心跳时间戳
// 5. Close 帧：触发连接关闭
func (s *Server) ReadMessages(client *Client) {
	defer func() {
		client.Close()
		s.RemoveClient(client.ID)
	}()

	for {
		f, err := ParseFrame(client.Conn)
		if err != nil {
			return
		}

		// Check message size limit
		if int64(len(f.Payload)) > s.heartbeat.maxMessageSize {
			closeFrame := CloseFrame(CloseMessageTooBig, "message too big")
			data, _ := closeFrame.Marshal()
			client.Send <- data
			return
		}

		// Process frame by opcode
		switch f.Opcode {
		case OpcodeText:
			// Text message: handle chat/broadcast
			msg := string(f.Payload)
			if client.Room != "" {
				s.BroadcastRoom(client.Room, msg)
			} else {
				s.Broadcast(msg)
			}

		case OpcodeBinary:
			// Binary message: could be used for file transfer, game state, etc.

		case OpcodePing:
			// Ping: respond with Pong and update last ping time
			pong := PongFrame(f.Payload)
			data, _ := pong.Marshal()
			client.Send <- data
			client.LastPing = time.Now()

		case OpcodePong:
			// Pong: update last pong time (heartbeat confirmed)
			client.LastPing = time.Now()

		case OpcodeClose:
			// Close: extract code and reason
			code, reason := CloseMessage(f.Payload)
			_ = code
			_ = reason
			return

		default:
			// Unknown opcode: ignore
		}
	}
}

// WriteMessages sends queued frames to the client.
// 发送队列中的帧到客户端
func (s *Server) WriteMessages(client *Client) {
	for {
		select {
		case msg := <-client.Send:
			client.Mu.Lock()
			if client.IsClosed() {
				client.Mu.Unlock()
				return
			}
			_, err := client.Conn.Write(msg)
			client.Mu.Unlock()
			if err != nil {
				client.Close()
				s.RemoveClient(client.ID)
				return
			}
		case <-s.quit:
			return
		}
	}
}

// HandleConnection is the main handler for a new WebSocket connection.
// 处理新 WebSocket 连接的主入口
//
// 连接处理流程：
// 1. 验证 HTTP 升级请求
// 2. 发送 101 响应完成握手
// 3. 注册客户端到服务器
// 4. 启动读写 goroutine
func (s *Server) HandleConnection(w http.ResponseWriter, r *http.Request) {
	// Step 1: Verify handshake request
	key, err := VerifyHandshakeRequest(r)
	if err != nil {
		http.Error(w, "invalid handshake", http.StatusBadRequest)
		return
	}

	// Step 2: Hijack the connection
	conn, err := HijackConn(w, r)
	if err != nil {
		http.Error(w, "hijack failed", http.StatusInternalServerError)
		return
	}

	// Step 3: Send 101 Switching Protocols response
	if err := WriteHandshakeResponse(conn, key); err != nil {
		conn.Close()
		return
	}

	// Step 4: Create and register client
	id := atomic.AddUint64(&s.nextID, 1)
	client := NewClient(id, conn)
	s.AddClient(client)

	// Step 5: Start read/write goroutines
	go s.ReadMessages(client)
	go s.WriteMessages(client)
}
