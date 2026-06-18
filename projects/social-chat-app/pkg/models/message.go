package models

import "time"

// Message 表示消息模型
type Message struct {
	ID        string    `json:"id" db:"id"`
	Type      string    `json:"type" db:"type"` // text, image, file
	From      string    `json:"from" db:"from_user"`
	To        string    `json:"to" db:"to_user"`
	Content   string    `json:"content" db:"content"`
	Status    string    `json:"status" db:"status"` // sent, delivered, read
	CreatedAt time.Time `json:"created_at" db:"created_at"`
	UpdatedAt time.Time `json:"updated_at" db:"updated_at"`
}

// MessageType 消息类型常量
const (
	MessageTypeText  = "text"
	MessageTypeImage = "image"
	MessageTypeFile  = "file"
)

// MessageStatus 消息状态常量
const (
	MessageStatusSent      = "sent"
	MessageStatusDelivered = "delivered"
	MessageStatusRead      = "read"
)