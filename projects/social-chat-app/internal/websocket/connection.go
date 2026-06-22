package websocket

import (
	"encoding/json"
	"log"
	"social-chat-app/pkg/models"
	"sync"
	"time"

	"github.com/gorilla/websocket"
)

const (
	// 写入超时
	writeWait = 10 * time.Second

	// 读取超时
	pongWait = 60 * time.Second

	// 心跳间隔（必须小于 pongWait）
	pingPeriod = 30 * time.Second

	// 最大消息大小
	maxMessageSize = 512 * 1024 // 512KB
)

// Connection WebSocket 连接封装
type Connection struct {
	UserID    string
	Conn      *websocket.Conn
	Send      chan []byte
	Manager   *Manager
	CreatedAt time.Time
	LastPing  time.Time
	closeOnce sync.Once
}

// NewConnection 创建新的连接
func NewConnection(userID string, conn *websocket.Conn, manager *Manager) *Connection {
	return &Connection{
		UserID:    userID,
		Conn:      conn,
		Send:      make(chan []byte, 256),
		Manager:   manager,
		CreatedAt: time.Now(),
		LastPing:  time.Now(),
	}
}

// Close 安全关闭连接，确保 Send channel 只关闭一次
func (c *Connection) Close() {
	c.closeOnce.Do(func() {
		close(c.Send)
		c.Conn.Close()
	})
}

// ReadPump 读取消息的 goroutine
func (c *Connection) ReadPump() {
	defer func() {
		c.Manager.unregister <- c
		c.Close()
	}()

	// 设置读取限制和超时
	c.Conn.SetReadLimit(maxMessageSize)
	c.Conn.SetReadDeadline(time.Now().Add(pongWait))
	c.Conn.SetPongHandler(func(string) error {
		c.Conn.SetReadDeadline(time.Now().Add(pongWait))
		c.LastPing = time.Now()
		return nil
	})

	for {
		_, message, err := c.Conn.ReadMessage()
		if err != nil {
			if websocket.IsUnexpectedCloseError(err, websocket.CloseGoingAway, websocket.CloseNormalClosure) {
				log.Printf("WebSocket error: %v", err)
			}
			break
		}
		c.HandleMessage(message)
	}
}

// WritePump 写入消息的 goroutine
func (c *Connection) WritePump() {
	ticker := time.NewTicker(pingPeriod)
	defer func() {
		ticker.Stop()
		c.Close()
	}()

	for {
		select {
		case message, ok := <-c.Send:
			c.Conn.SetWriteDeadline(time.Now().Add(writeWait))
			if !ok {
				// 通道关闭，发送关闭消息
				c.Conn.WriteMessage(websocket.CloseMessage, []byte{})
				return
			}

			w, err := c.Conn.NextWriter(websocket.TextMessage)
			if err != nil {
				return
			}
			w.Write(message)

			// 批量发送队列中的消息
			n := len(c.Send)
			for i := 0; i < n; i++ {
				w.Write([]byte("\n"))
				w.Write(<-c.Send)
			}

			if err := w.Close(); err != nil {
				return
			}

		case <-ticker.C:
			c.Conn.SetWriteDeadline(time.Now().Add(writeWait))
			if err := c.Conn.WriteMessage(websocket.PingMessage, nil); err != nil {
				return
			}
		}
	}
}

// HandleMessage 处理接收到的消息
func (c *Connection) HandleMessage(data []byte) {
	var req models.WSRequest
	if err := json.Unmarshal(data, &req); err != nil {
		c.SendError("", 400, "invalid message format")
		return
	}

	switch req.Type {
	case models.WSTypeMessage:
		c.HandleChatMessage(req)
	case models.WSTypeTyping:
		c.HandleTyping(req)
	case models.WSTypeRead:
		c.HandleReadReceipt(req)
	case models.WSTypePing:
		c.HandlePing(req)
	default:
		c.SendError(req.ID, 400, "unknown message type")
	}
}

// HandleChatMessage 处理聊天消息
func (c *Connection) HandleChatMessage(req models.WSRequest) {
	// 解析 Payload
	payloadBytes, err := json.Marshal(req.Payload)
	if err != nil {
		c.SendError(req.ID, 400, "invalid message payload")
		return
	}

	var payload models.MessagePayload
	if err := json.Unmarshal(payloadBytes, &payload); err != nil {
		c.SendError(req.ID, 400, "invalid message payload")
		return
	}

	// 委托给 Manager 处理
	c.Manager.HandleMessage(c, req.ID, &payload)
}

// HandleTyping 处理输入状态
func (c *Connection) HandleTyping(req models.WSRequest) {
	payloadBytes, err := json.Marshal(req.Payload)
	if err != nil {
		return
	}

	var payload models.TypingPayload
	if err := json.Unmarshal(payloadBytes, &payload); err != nil {
		return
	}

	// 将输入状态转发给目标用户
	c.Manager.SendToUser(payload.To, &models.WSResponse{
		Type: models.WSTypeTyping,
		Payload: map[string]string{
			"from": c.UserID,
		},
		Timestamp: time.Now().Unix(),
	})
}

// HandleReadReceipt 处理已读回执
func (c *Connection) HandleReadReceipt(req models.WSRequest) {
	payloadBytes, err := json.Marshal(req.Payload)
	if err != nil {
		return
	}

	var payload models.ReadPayload
	if err := json.Unmarshal(payloadBytes, &payload); err != nil {
		return
	}

	// 委托给 Manager 处理
	c.Manager.HandleReadReceipt(c, &payload)
}

// HandlePing 处理心跳
func (c *Connection) HandlePing(req models.WSRequest) {
	c.SendPong(req.ID)
}

// SendMessage 发送消息
func (c *Connection) SendMessage(msg *models.WSResponse) {
	data, err := json.Marshal(msg)
	if err != nil {
		log.Printf("Failed to marshal message: %v", err)
		return
	}

	select {
	case c.Send <- data:
	default:
		// 通道已满，安全关闭连接
		c.Close()
	}
}

// SendError 发送错误消息
func (c *Connection) SendError(requestID string, code int, message string) {
	c.SendMessage(&models.WSResponse{
		Type: models.WSTypeError,
		ID:   requestID,
		Payload: models.WSError{
			Code:    code,
			Message: message,
		},
		Timestamp: time.Now().Unix(),
	})
}

// SendPong 发送 Pong 响应
func (c *Connection) SendPong(requestID string) {
	c.SendMessage(&models.WSResponse{
		Type:      models.WSTypePong,
		ID:        requestID,
		Timestamp: time.Now().Unix(),
	})
}

// SendAck 发送确认消息
func (c *Connection) SendAck(requestID string, messageID string) {
	c.SendMessage(&models.WSResponse{
		Type: models.WSTypeAck,
		ID:   requestID,
		Payload: map[string]string{
			"message_id": messageID,
		},
		Timestamp: time.Now().Unix(),
	})
}