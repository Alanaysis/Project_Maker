package message

import (
	"database/sql"
	"fmt"
	"social-chat-app/pkg/models"
	"time"
)

// Repository 消息存储接口
type Repository interface {
	Save(msg *models.Message) error
	FindByID(id string) (*models.Message, error)
	FindByConversation(user1, user2 string, limit, offset int) ([]*models.Message, error)
	FindUnread(userID string) ([]*models.Message, error)
	MarkAsRead(messageIDs []string) error
	SaveOffline(msg *models.Message) error
	FindOffline(userID string) ([]*models.Message, error)
	DeleteOffline(messageIDs []string) error
}

// SQLiteRepository SQLite 消息存储实现
type SQLiteRepository struct {
	db *sql.DB
}

// NewSQLiteRepository 创建新的 SQLite 消息存储
func NewSQLiteRepository(db *sql.DB) *SQLiteRepository {
	return &SQLiteRepository{db: db}
}

// Save 保存消息
func (r *SQLiteRepository) Save(msg *models.Message) error {
	query := `
		INSERT INTO messages (id, type, from_user, to_user, content, status, created_at, updated_at)
		VALUES (?, ?, ?, ?, ?, ?, ?, ?)
	`
	_, err := r.db.Exec(query,
		msg.ID, msg.Type, msg.From, msg.To,
		msg.Content, msg.Status, msg.CreatedAt, msg.UpdatedAt,
	)
	if err != nil {
		return fmt.Errorf("failed to save message: %w", err)
	}
	return nil
}

// FindByID 根据 ID 查找消息
func (r *SQLiteRepository) FindByID(id string) (*models.Message, error) {
	query := `
		SELECT id, type, from_user, to_user, content, status, created_at, updated_at
		FROM messages
		WHERE id = ?
	`
	msg := &models.Message{}
	err := r.db.QueryRow(query, id).Scan(
		&msg.ID, &msg.Type, &msg.From, &msg.To,
		&msg.Content, &msg.Status, &msg.CreatedAt, &msg.UpdatedAt,
	)
	if err == sql.ErrNoRows {
		return nil, fmt.Errorf("message not found")
	}
	if err != nil {
		return nil, fmt.Errorf("failed to find message: %w", err)
	}
	return msg, nil
}

// FindByConversation 查找两个用户之间的对话
func (r *SQLiteRepository) FindByConversation(user1, user2 string, limit, offset int) ([]*models.Message, error) {
	query := `
		SELECT id, type, from_user, to_user, content, status, created_at, updated_at
		FROM messages
		WHERE (from_user = ? AND to_user = ?) OR (from_user = ? AND to_user = ?)
		ORDER BY created_at DESC
		LIMIT ? OFFSET ?
	`
	rows, err := r.db.Query(query, user1, user2, user2, user1, limit, offset)
	if err != nil {
		return nil, fmt.Errorf("failed to find conversation: %w", err)
	}
	defer rows.Close()

	var messages []*models.Message
	for rows.Next() {
		msg := &models.Message{}
		err := rows.Scan(
			&msg.ID, &msg.Type, &msg.From, &msg.To,
			&msg.Content, &msg.Status, &msg.CreatedAt, &msg.UpdatedAt,
		)
		if err != nil {
			return nil, fmt.Errorf("failed to scan message: %w", err)
		}
		messages = append(messages, msg)
	}
	return messages, nil
}

// FindUnread 查找用户的未读消息
func (r *SQLiteRepository) FindUnread(userID string) ([]*models.Message, error) {
	query := `
		SELECT id, type, from_user, to_user, content, status, created_at, updated_at
		FROM messages
		WHERE to_user = ? AND status != 'read'
		ORDER BY created_at ASC
	`
	rows, err := r.db.Query(query, userID)
	if err != nil {
		return nil, fmt.Errorf("failed to find unread messages: %w", err)
	}
	defer rows.Close()

	var messages []*models.Message
	for rows.Next() {
		msg := &models.Message{}
		err := rows.Scan(
			&msg.ID, &msg.Type, &msg.From, &msg.To,
			&msg.Content, &msg.Status, &msg.CreatedAt, &msg.UpdatedAt,
		)
		if err != nil {
			return nil, fmt.Errorf("failed to scan message: %w", err)
		}
		messages = append(messages, msg)
	}
	return messages, nil
}

// MarkAsRead 标记消息为已读
func (r *SQLiteRepository) MarkAsRead(messageIDs []string) error {
	if len(messageIDs) == 0 {
		return nil
	}

	// 构建批量更新查询
	query := "UPDATE messages SET status = 'read', updated_at = ? WHERE id IN ("
	args := []interface{}{time.Now()}

	for i, id := range messageIDs {
		if i > 0 {
			query += ", "
		}
		query += "?"
		args = append(args, id)
	}
	query += ")"

	_, err := r.db.Exec(query, args...)
	if err != nil {
		return fmt.Errorf("failed to mark messages as read: %w", err)
	}
	return nil
}

// SaveOffline 保存离线消息
func (r *SQLiteRepository) SaveOffline(msg *models.Message) error {
	query := `
		INSERT INTO offline_messages (id, from_user, to_user, content, type, created_at)
		VALUES (?, ?, ?, ?, ?, ?)
	`
	_, err := r.db.Exec(query,
		msg.ID, msg.From, msg.To,
		msg.Content, msg.Type, msg.CreatedAt,
	)
	if err != nil {
		return fmt.Errorf("failed to save offline message: %w", err)
	}
	return nil
}

// FindOffline 查找用户的离线消息
func (r *SQLiteRepository) FindOffline(userID string) ([]*models.Message, error) {
	query := `
		SELECT id, type, from_user, to_user, content, 'sent', created_at, created_at
		FROM offline_messages
		WHERE to_user = ?
		ORDER BY created_at ASC
	`
	rows, err := r.db.Query(query, userID)
	if err != nil {
		return nil, fmt.Errorf("failed to find offline messages: %w", err)
	}
	defer rows.Close()

	var messages []*models.Message
	for rows.Next() {
		msg := &models.Message{}
		err := rows.Scan(
			&msg.ID, &msg.Type, &msg.From, &msg.To,
			&msg.Content, &msg.Status, &msg.CreatedAt, &msg.UpdatedAt,
		)
		if err != nil {
			return nil, fmt.Errorf("failed to scan offline message: %w", err)
		}
		messages = append(messages, msg)
	}
	return messages, nil
}

// DeleteOffline 删除离线消息
func (r *SQLiteRepository) DeleteOffline(messageIDs []string) error {
	if len(messageIDs) == 0 {
		return nil
	}

	query := "DELETE FROM offline_messages WHERE id IN ("
	args := []interface{}{}

	for i, id := range messageIDs {
		if i > 0 {
			query += ", "
		}
		query += "?"
		args = append(args, id)
	}
	query += ")"

	_, err := r.db.Exec(query, args...)
	if err != nil {
		return fmt.Errorf("failed to delete offline messages: %w", err)
	}
	return nil
}