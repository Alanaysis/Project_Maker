package models

import "time"

// User 表示用户模型
type User struct {
	ID        string    `json:"id" db:"id"`
	Username  string    `json:"username" db:"username"`
	Password  string    `json:"-" db:"password"` // 不序列化密码
	Email     string    `json:"email,omitempty" db:"email"`
	Nickname  string    `json:"nickname" db:"nickname"`
	Avatar    string    `json:"avatar" db:"avatar"`
	Status    string    `json:"status" db:"status"` // online, offline, busy, away
	CreatedAt time.Time `json:"created_at" db:"created_at"`
	UpdatedAt time.Time `json:"updated_at" db:"updated_at"`
}

// UserStatus 用户状态常量
const (
	UserStatusOnline  = "online"
	UserStatusOffline = "offline"
	UserStatusBusy    = "busy"
	UserStatusAway    = "away"
)