package message

import (
	"errors"
	"social-chat-app/pkg/models"
	"time"

	"github.com/google/uuid"
)

// Service 消息服务
type Service struct {
	repo Repository
}

// NewService 创建新的消息服务
func NewService(repo Repository) *Service {
	return &Service{repo: repo}
}

// CreateMessage 创建新消息
func (s *Service) CreateMessage(from, to, content, msgType string) (*models.Message, error) {
	if from == "" || to == "" {
		return nil, errors.New("sender and receiver are required")
	}
	if content == "" {
		return nil, errors.New("message content is required")
	}

	// 验证消息类型
	validTypes := map[string]bool{
		models.MessageTypeText:  true,
		models.MessageTypeImage: true,
		models.MessageTypeFile:  true,
	}
	if !validTypes[msgType] {
		msgType = models.MessageTypeText
	}

	msg := &models.Message{
		ID:        uuid.New().String(),
		Type:      msgType,
		From:      from,
		To:        to,
		Content:   content,
		Status:    models.MessageStatusSent,
		CreatedAt: time.Now(),
		UpdatedAt: time.Now(),
	}

	if err := s.repo.Save(msg); err != nil {
		return nil, err
	}

	return msg, nil
}

// GetByID 根据 ID 获取消息
func (s *Service) GetByID(id string) (*models.Message, error) {
	if id == "" {
		return nil, errors.New("message ID is required")
	}
	return s.repo.FindByID(id)
}

// GetConversation 获取两个用户之间的对话
func (s *Service) GetConversation(user1, user2 string, limit, offset int) ([]*models.Message, error) {
	if user1 == "" || user2 == "" {
		return nil, errors.New("both user IDs are required")
	}
	if limit <= 0 || limit > 100 {
		limit = 50
	}
	if offset < 0 {
		offset = 0
	}
	return s.repo.FindByConversation(user1, user2, limit, offset)
}

// GetUnreadMessages 获取用户的未读消息
func (s *Service) GetUnreadMessages(userID string) ([]*models.Message, error) {
	if userID == "" {
		return nil, errors.New("user ID is required")
	}
	return s.repo.FindUnread(userID)
}

// MarkAsRead 标记消息为已读
func (s *Service) MarkAsRead(messageIDs []string) error {
	if len(messageIDs) == 0 {
		return nil
	}
	return s.repo.MarkAsRead(messageIDs)
}

// SaveOfflineMessage 保存离线消息
func (s *Service) SaveOfflineMessage(msg *models.Message) error {
	if msg == nil {
		return errors.New("message is required")
	}
	return s.repo.SaveOffline(msg)
}

// GetOfflineMessages 获取用户的离线消息
func (s *Service) GetOfflineMessages(userID string) ([]*models.Message, error) {
	if userID == "" {
		return nil, errors.New("user ID is required")
	}
	return s.repo.FindOffline(userID)
}

// DeleteOfflineMessages 删除离线消息
func (s *Service) DeleteOfflineMessages(messageIDs []string) error {
	if len(messageIDs) == 0 {
		return nil
	}
	return s.repo.DeleteOffline(messageIDs)
}