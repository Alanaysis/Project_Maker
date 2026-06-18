package user

import (
	"errors"
	"social-chat-app/pkg/models"
)

// Service 用户服务
type Service struct {
	repo Repository
}

// NewService 创建新的用户服务
func NewService(repo Repository) *Service {
	return &Service{repo: repo}
}

// GetByID 根据 ID 获取用户
func (s *Service) GetByID(id string) (*models.User, error) {
	if id == "" {
		return nil, errors.New("user ID is required")
	}
	return s.repo.FindByID(id)
}

// GetByUsername 根据用户名获取用户
func (s *Service) GetByUsername(username string) (*models.User, error) {
	if username == "" {
		return nil, errors.New("username is required")
	}
	return s.repo.FindByUsername(username)
}

// UpdateProfile 更新用户资料
func (s *Service) UpdateProfile(id string, nickname, avatar, email string) (*models.User, error) {
	user, err := s.repo.FindByID(id)
	if err != nil {
		return nil, err
	}

	if nickname != "" {
		user.Nickname = nickname
	}
	if avatar != "" {
		user.Avatar = avatar
	}
	if email != "" {
		user.Email = email
	}

	if err := s.repo.Update(user); err != nil {
		return nil, err
	}

	return user, nil
}

// UpdateStatus 更新用户状态
func (s *Service) UpdateStatus(id string, status string) error {
	// 验证状态值
	validStatuses := map[string]bool{
		models.UserStatusOnline:  true,
		models.UserStatusOffline: true,
		models.UserStatusBusy:    true,
		models.UserStatusAway:    true,
	}

	if !validStatuses[status] {
		return errors.New("invalid status value")
	}

	return s.repo.UpdateStatus(id, status)
}

// SearchUsers 搜索用户
func (s *Service) SearchUsers(query string, limit int) ([]*models.User, error) {
	if query == "" {
		return nil, errors.New("search query is required")
	}
	if limit <= 0 || limit > 50 {
		limit = 20
	}
	return s.repo.Search(query, limit)
}