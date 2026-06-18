package user

import (
	"database/sql"
	"fmt"
	"social-chat-app/pkg/models"
	"time"
)

// Repository 用户存储接口
type Repository interface {
	Create(user *models.User) error
	FindByID(id string) (*models.User, error)
	FindByUsername(username string) (*models.User, error)
	Update(user *models.User) error
	UpdateStatus(id string, status string) error
	Search(query string, limit int) ([]*models.User, error)
}

// SQLiteRepository SQLite 用户存储实现
type SQLiteRepository struct {
	db *sql.DB
}

// NewSQLiteRepository 创建新的 SQLite 用户存储
func NewSQLiteRepository(db *sql.DB) *SQLiteRepository {
	return &SQLiteRepository{db: db}
}

// Create 创建新用户
func (r *SQLiteRepository) Create(user *models.User) error {
	query := `
		INSERT INTO users (id, username, password, email, nickname, avatar, status, created_at, updated_at)
		VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
	`
	_, err := r.db.Exec(query,
		user.ID, user.Username, user.Password,
		user.Email, user.Nickname, user.Avatar,
		user.Status, user.CreatedAt, user.UpdatedAt,
	)
	if err != nil {
		return fmt.Errorf("failed to create user: %w", err)
	}
	return nil
}

// FindByID 根据 ID 查找用户
func (r *SQLiteRepository) FindByID(id string) (*models.User, error) {
	query := `
		SELECT id, username, password, email, nickname, avatar, status, created_at, updated_at
		FROM users
		WHERE id = ?
	`
	user := &models.User{}
	err := r.db.QueryRow(query, id).Scan(
		&user.ID, &user.Username, &user.Password,
		&user.Email, &user.Nickname, &user.Avatar,
		&user.Status, &user.CreatedAt, &user.UpdatedAt,
	)
	if err == sql.ErrNoRows {
		return nil, fmt.Errorf("user not found")
	}
	if err != nil {
		return nil, fmt.Errorf("failed to find user: %w", err)
	}
	return user, nil
}

// FindByUsername 根据用户名查找用户
func (r *SQLiteRepository) FindByUsername(username string) (*models.User, error) {
	query := `
		SELECT id, username, password, email, nickname, avatar, status, created_at, updated_at
		FROM users
		WHERE username = ?
	`
	user := &models.User{}
	err := r.db.QueryRow(query, username).Scan(
		&user.ID, &user.Username, &user.Password,
		&user.Email, &user.Nickname, &user.Avatar,
		&user.Status, &user.CreatedAt, &user.UpdatedAt,
	)
	if err == sql.ErrNoRows {
		return nil, fmt.Errorf("user not found")
	}
	if err != nil {
		return nil, fmt.Errorf("failed to find user: %w", err)
	}
	return user, nil
}

// Update 更新用户信息
func (r *SQLiteRepository) Update(user *models.User) error {
	query := `
		UPDATE users
		SET nickname = ?, avatar = ?, email = ?, updated_at = ?
		WHERE id = ?
	`
	user.UpdatedAt = time.Now()
	_, err := r.db.Exec(query,
		user.Nickname, user.Avatar, user.Email,
		user.UpdatedAt, user.ID,
	)
	if err != nil {
		return fmt.Errorf("failed to update user: %w", err)
	}
	return nil
}

// UpdateStatus 更新用户状态
func (r *SQLiteRepository) UpdateStatus(id string, status string) error {
	query := `
		UPDATE users
		SET status = ?, updated_at = ?
		WHERE id = ?
	`
	_, err := r.db.Exec(query, status, time.Now(), id)
	if err != nil {
		return fmt.Errorf("failed to update user status: %w", err)
	}
	return nil
}

// Search 搜索用户
func (r *SQLiteRepository) Search(query string, limit int) ([]*models.User, error) {
	sqlQuery := `
		SELECT id, username, nickname, avatar, status
		FROM users
		WHERE username LIKE ? OR nickname LIKE ?
		LIMIT ?
	`
	searchPattern := "%" + query + "%"
	rows, err := r.db.Query(sqlQuery, searchPattern, searchPattern, limit)
	if err != nil {
		return nil, fmt.Errorf("failed to search users: %w", err)
	}
	defer rows.Close()

	var users []*models.User
	for rows.Next() {
		user := &models.User{}
		err := rows.Scan(&user.ID, &user.Username, &user.Nickname, &user.Avatar, &user.Status)
		if err != nil {
			return nil, fmt.Errorf("failed to scan user: %w", err)
		}
		users = append(users, user)
	}
	return users, nil
}