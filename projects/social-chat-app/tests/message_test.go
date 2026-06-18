package tests

import (
	"social-chat-app/internal/message"
	"social-chat-app/pkg/models"
	"testing"
	"time"
)

// MockMessageRepository 模拟消息存储
type MockMessageRepository struct {
	messages        map[string]*models.Message
	offlineMessages map[string]*models.Message
}

func NewMockMessageRepository() *MockMessageRepository {
	return &MockMessageRepository{
		messages:        make(map[string]*models.Message),
		offlineMessages: make(map[string]*models.Message),
	}
}

func (m *MockMessageRepository) Save(msg *models.Message) error {
	m.messages[msg.ID] = msg
	return nil
}

func (m *MockMessageRepository) FindByID(id string) (*models.Message, error) {
	msg, ok := m.messages[id]
	if !ok {
		return nil, nil
	}
	return msg, nil
}

func (m *MockMessageRepository) FindByConversation(user1, user2 string, limit, offset int) ([]*models.Message, error) {
	var result []*models.Message
	for _, msg := range m.messages {
		if (msg.From == user1 && msg.To == user2) || (msg.From == user2 && msg.To == user1) {
			result = append(result, msg)
		}
	}
	// 简单实现：返回所有匹配的消息
	return result, nil
}

func (m *MockMessageRepository) FindUnread(userID string) ([]*models.Message, error) {
	var result []*models.Message
	for _, msg := range m.messages {
		if msg.To == userID && msg.Status != "read" {
			result = append(result, msg)
		}
	}
	return result, nil
}

func (m *MockMessageRepository) MarkAsRead(messageIDs []string) error {
	for _, id := range messageIDs {
		if msg, ok := m.messages[id]; ok {
			msg.Status = "read"
		}
	}
	return nil
}

func (m *MockMessageRepository) SaveOffline(msg *models.Message) error {
	m.offlineMessages[msg.ID] = msg
	return nil
}

func (m *MockMessageRepository) FindOffline(userID string) ([]*models.Message, error) {
	var result []*models.Message
	for _, msg := range m.offlineMessages {
		if msg.To == userID {
			result = append(result, msg)
		}
	}
	return result, nil
}

func (m *MockMessageRepository) DeleteOffline(messageIDs []string) error {
	for _, id := range messageIDs {
		delete(m.offlineMessages, id)
	}
	return nil
}

func TestMessageService_CreateMessage(t *testing.T) {
	repo := NewMockMessageRepository()
	service := message.NewService(repo)

	msg, err := service.CreateMessage("user1", "user2", "Hello!", "text")
	if err != nil {
		t.Fatalf("Failed to create message: %v", err)
	}

	if msg.ID == "" {
		t.Error("Message ID should not be empty")
	}
	if msg.From != "user1" {
		t.Errorf("Expected From 'user1', got '%s'", msg.From)
	}
	if msg.To != "user2" {
		t.Errorf("Expected To 'user2', got '%s'", msg.To)
	}
	if msg.Content != "Hello!" {
		t.Errorf("Expected Content 'Hello!', got '%s'", msg.Content)
	}
	if msg.Status != "sent" {
		t.Errorf("Expected Status 'sent', got '%s'", msg.Status)
	}
}

func TestMessageService_CreateMessageInvalidInput(t *testing.T) {
	repo := NewMockMessageRepository()
	service := message.NewService(repo)

	tests := []struct {
		name    string
		from    string
		to      string
		content string
		msgType string
	}{
		{
			name:    "empty from",
			from:    "",
			to:      "user2",
			content: "Hello!",
			msgType: "text",
		},
		{
			name:    "empty to",
			from:    "user1",
			to:      "",
			content: "Hello!",
			msgType: "text",
		},
		{
			name:    "empty content",
			from:    "user1",
			to:      "user2",
			content: "",
			msgType: "text",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			_, err := service.CreateMessage(tt.from, tt.to, tt.content, tt.msgType)
			if err == nil {
				t.Errorf("Expected error for %s", tt.name)
			}
		})
	}
}

func TestMessageService_GetConversation(t *testing.T) {
	repo := NewMockMessageRepository()
	service := message.NewService(repo)

	// 创建一些测试消息
	service.CreateMessage("user1", "user2", "Hello!", "text")
	service.CreateMessage("user2", "user1", "Hi there!", "text")
	service.CreateMessage("user1", "user2", "How are you?", "text")

	// 获取对话
	messages, err := service.GetConversation("user1", "user2", 50, 0)
	if err != nil {
		t.Fatalf("Failed to get conversation: %v", err)
	}

	if len(messages) != 3 {
		t.Errorf("Expected 3 messages, got %d", len(messages))
	}
}

func TestMessageService_GetUnreadMessages(t *testing.T) {
	repo := NewMockMessageRepository()
	service := message.NewService(repo)

	// 创建消息
	service.CreateMessage("user1", "user2", "Hello!", "text")
	service.CreateMessage("user1", "user2", "Are you there?", "text")
	service.CreateMessage("user2", "user1", "Hi!", "text")

	// 获取 user2 的未读消息
	messages, err := service.GetUnreadMessages("user2")
	if err != nil {
		t.Fatalf("Failed to get unread messages: %v", err)
	}

	if len(messages) != 2 {
		t.Errorf("Expected 2 unread messages, got %d", len(messages))
	}
}

func TestMessageService_MarkAsRead(t *testing.T) {
	repo := NewMockMessageRepository()
	service := message.NewService(repo)

	// 创建消息
	msg, _ := service.CreateMessage("user1", "user2", "Hello!", "text")

	// 标记为已读
	err := service.MarkAsRead([]string{msg.ID})
	if err != nil {
		t.Fatalf("Failed to mark as read: %v", err)
	}

	// 验证状态已更新
	updatedMsg, _ := service.GetByID(msg.ID)
	if updatedMsg.Status != "read" {
		t.Errorf("Expected status 'read', got '%s'", updatedMsg.Status)
	}
}

func TestMessageService_OfflineMessages(t *testing.T) {
	repo := NewMockMessageRepository()
	service := message.NewService(repo)

	// 创建离线消息
	msg := &models.Message{
		ID:        "offline1",
		Type:      "text",
		From:      "user1",
		To:        "user2",
		Content:   "Offline message",
		Status:    "sent",
		CreatedAt: time.Now(),
	}

	// 保存离线消息
	err := service.SaveOfflineMessage(msg)
	if err != nil {
		t.Fatalf("Failed to save offline message: %v", err)
	}

	// 获取离线消息
	messages, err := service.GetOfflineMessages("user2")
	if err != nil {
		t.Fatalf("Failed to get offline messages: %v", err)
	}

	if len(messages) != 1 {
		t.Errorf("Expected 1 offline message, got %d", len(messages))
	}

	// 删除离线消息
	err = service.DeleteOfflineMessages([]string{"offline1"})
	if err != nil {
		t.Fatalf("Failed to delete offline messages: %v", err)
	}

	// 验证已删除
	messages, _ = service.GetOfflineMessages("user2")
	if len(messages) != 0 {
		t.Errorf("Expected 0 offline messages, got %d", len(messages))
	}
}

func TestMessageService_GetByID(t *testing.T) {
	repo := NewMockMessageRepository()
	service := message.NewService(repo)

	// 创建消息
	created, _ := service.CreateMessage("user1", "user2", "Hello!", "text")

	// 获取消息
	found, err := service.GetByID(created.ID)
	if err != nil {
		t.Fatalf("Failed to get message: %v", err)
	}

	if found.ID != created.ID {
		t.Errorf("Expected ID '%s', got '%s'", created.ID, found.ID)
	}
}

func TestMessageService_GetByIDEmpty(t *testing.T) {
	repo := NewMockMessageRepository()
	service := message.NewService(repo)

	_, err := service.GetByID("")
	if err == nil {
		t.Fatal("Expected error for empty ID")
	}
}