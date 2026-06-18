package models

import "time"

// Group 表示群组模型
type Group struct {
	ID          string    `json:"id" db:"id"`
	Name        string    `json:"name" db:"name"`
	Description string    `json:"description" db:"description"`
	OwnerID     string    `json:"owner_id" db:"owner_id"`
	Avatar      string    `json:"avatar" db:"avatar"`
	MemberCount int       `json:"member_count" db:"member_count"`
	CreatedAt   time.Time `json:"created_at" db:"created_at"`
	UpdatedAt   time.Time `json:"updated_at" db:"updated_at"`
}

// GroupMember 表示群组成员
type GroupMember struct {
	GroupID  string    `json:"group_id" db:"group_id"`
	UserID   string    `json:"user_id" db:"user_id"`
	Role     string    `json:"role" db:"role"` // owner, admin, member
	JoinedAt time.Time `json:"joined_at" db:"joined_at"`
}

// GroupRole 群组角色常量
const (
	GroupRoleOwner  = "owner"
	GroupRoleAdmin  = "admin"
	GroupRoleMember = "member"
)