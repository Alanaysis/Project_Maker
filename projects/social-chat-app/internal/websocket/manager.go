package websocket

import (
	"log"
	"social-chat-app/internal/message"
	"social-chat-app/internal/user"
	"social-chat-app/pkg/models"
	"sync"
	"time"
)

// Manager WebSocket 连接管理器
type Manager struct {
	mu              sync.RWMutex
	connections     map[string]*Connection // userID -> Connection
	messageService  *message.Service
	userService     *user.Service
	register        chan *Connection
	unregister      chan *Connection
	broadcast       chan []byte
}

// NewManager 创建新的连接管理器
func NewManager(messageService *message.Service, userService *user.Service) *Manager {
	return &Manager{
		connections:     make(map[string]*Connection),
		messageService:  messageService,
		userService:     userService,
		register:        make(chan *Connection),
		unregister:      make(chan *Connection),
		broadcast:       make(chan []byte),
	}
}

// Start 启动连接管理器
func (m *Manager) Start() {
	for {
		select {
		case conn := <-m.register:
			m.registerConnection(conn)

		case conn := <-m.unregister:
			m.unregisterConnection(conn)

		case message := <-m.broadcast:
			m.broadcastMessage(message)
		}
	}
}

// registerConnection 注册新连接
func (m *Manager) registerConnection(conn *Connection) {
	m.mu.Lock()
	defer m.mu.Unlock()

	// 如果用户已有连接，安全关闭旧连接
	if oldConn, ok := m.connections[conn.UserID]; ok {
		oldConn.Close()
	}

	m.connections[conn.UserID] = conn
	log.Printf("User %s connected", conn.UserID)

	// 更新用户状态为在线
	if err := m.userService.UpdateStatus(conn.UserID, models.UserStatusOnline); err != nil {
		log.Printf("Failed to update user status: %v", err)
	}

	// 同步离线消息
	go m.syncOfflineMessages(conn.UserID)
}

// unregisterConnection 注销连接
func (m *Manager) unregisterConnection(conn *Connection) {
	m.mu.Lock()
	defer m.mu.Unlock()

	if _, ok := m.connections[conn.UserID]; ok {
		delete(m.connections, conn.UserID)
		conn.Close()
		log.Printf("User %s disconnected", conn.UserID)

		// 更新用户状态为离线
		if err := m.userService.UpdateStatus(conn.UserID, models.UserStatusOffline); err != nil {
			log.Printf("Failed to update user status: %v", err)
		}
	}
}

// broadcastMessage 广播消息
func (m *Manager) broadcastMessage(message []byte) {
	m.mu.RLock()
	defer m.mu.RUnlock()

	for _, conn := range m.connections {
		select {
		case conn.Send <- message:
		default:
			conn.Close()
			delete(m.connections, conn.UserID)
		}
	}
}

// RegisterConnection 注册新连接（供外部包调用）
func (m *Manager) RegisterConnection(conn *Connection) {
	m.register <- conn
}

// GetConnection 获取用户的连接
func (m *Manager) GetConnection(userID string) (*Connection, bool) {
	m.mu.RLock()
	defer m.mu.RUnlock()

	conn, ok := m.connections[userID]
	return conn, ok
}

// GetOnlineCount 获取在线用户数
func (m *Manager) GetOnlineCount() int {
	m.mu.RLock()
	defer m.mu.RUnlock()

	return len(m.connections)
}

// SendToUser 发送消息给指定用户
func (m *Manager) SendToUser(userID string, msg *models.WSResponse) {
	conn, ok := m.GetConnection(userID)
	if !ok {
		return
	}
	conn.SendMessage(msg)
}

// HandleMessage 处理聊天消息
func (m *Manager) HandleMessage(sender *Connection, requestID string, payload *models.MessagePayload) {
	// 创建消息
	msg, err := m.messageService.CreateMessage(
		sender.UserID,
		payload.To,
		payload.Content,
		payload.MsgType,
	)
	if err != nil {
		sender.SendError(requestID, 500, "failed to create message")
		return
	}

	// 发送确认给发送者
	sender.SendAck(requestID, msg.ID)

	// 构建接收方消息
	receiverMsg := &models.WSResponse{
		Type: models.WSTypeMessage,
		ID:   msg.ID,
		Payload: map[string]interface{}{
			"id":        msg.ID,
			"from":      msg.From,
			"content":   msg.Content,
			"type":      msg.Type,
			"created_at": msg.CreatedAt.Unix(),
		},
		Timestamp: time.Now().Unix(),
	}

	// 查找接收方连接
	receiverConn, ok := m.GetConnection(payload.To)
	if ok {
		// 在线：直接推送
		receiverConn.SendMessage(receiverMsg)

		// 更新消息状态为已送达
		msg.Status = models.MessageStatusDelivered
	} else {
		// 离线：存储为离线消息
		if err := m.messageService.SaveOfflineMessage(msg); err != nil {
			log.Printf("Failed to save offline message: %v", err)
		}
	}
}

// HandleReadReceipt 处理已读回执
func (m *Manager) HandleReadReceipt(sender *Connection, payload *models.ReadPayload) {
	// 获取消息信息
	msg, err := m.messageService.GetByID(payload.MessageID)
	if err != nil {
		sender.SendError("", 404, "message not found")
		return
	}

	// 验证权限（只有接收者可以标记已读）
	if msg.To != sender.UserID {
		sender.SendError("", 403, "not authorized")
		return
	}

	// 标记消息为已读
	if err := m.messageService.MarkAsRead([]string{payload.MessageID}); err != nil {
		sender.SendError("", 500, "failed to mark message as read")
		return
	}

	// 通知发送者消息已读
	senderConn, ok := m.GetConnection(msg.From)
	if ok {
		senderConn.SendMessage(&models.WSResponse{
			Type: models.WSTypeRead,
			Payload: map[string]string{
				"message_id": payload.MessageID,
				"read_by":    sender.UserID,
			},
			Timestamp: time.Now().Unix(),
		})
	}
}

// syncOfflineMessages 同步离线消息
func (m *Manager) syncOfflineMessages(userID string) {
	messages, err := m.messageService.GetOfflineMessages(userID)
	if err != nil {
		log.Printf("Failed to get offline messages: %v", err)
		return
	}

	if len(messages) == 0 {
		return
	}

	// 发送离线消息
	var messageIDs []string
	for _, msg := range messages {
		m.SendToUser(userID, &models.WSResponse{
			Type: models.WSTypeMessage,
			ID:   msg.ID,
			Payload: map[string]interface{}{
				"id":        msg.ID,
				"from":      msg.From,
				"content":   msg.Content,
				"type":      msg.Type,
				"created_at": msg.CreatedAt.Unix(),
				"offline":   true,
			},
			Timestamp: time.Now().Unix(),
		})
		messageIDs = append(messageIDs, msg.ID)
	}

	// 删除已发送的离线消息
	if err := m.messageService.DeleteOfflineMessages(messageIDs); err != nil {
		log.Printf("Failed to delete offline messages: %v", err)
	}

	log.Printf("Synced %d offline messages for user %s", len(messages), userID)
}