package tests

import (
	"social-chat-app/internal/user"
	"social-chat-app/pkg/models"
	"testing"
	"time"
)

// MockUserRepository 模拟用户存储
type MockUserRepository struct {
	users map[string]*models.User
}

func NewMockUserRepository() *MockUserRepository {
	return &MockUserRepository{
		users: make(map[string]*models.User),
	}
}

func (m *MockUserRepository) Create(u *models.User) error {
	m.users[u.ID] = u
	return nil
}

func (m *MockUserRepository) FindByID(id string) (*models.User, error) {
	u, ok := m.users[id]
	if !ok {
		return nil, nil
	}
	return u, nil
}

func (m *MockUserRepository) FindByUsername(username string) (*models.User, error) {
	for _, u := range m.users {
		if u.Username == username {
			return u, nil
		}
	}
	return nil, nil
}

func (m *MockUserRepository) Update(u *models.User) error {
	m.users[u.ID] = u
	return nil
}

func (m *MockUserRepository) UpdateStatus(id string, status string) error {
	if u, ok := m.users[id]; ok {
		u.Status = status
	}
	return nil
}

func (m *MockUserRepository) Search(query string, limit int) ([]*models.User, error) {
	var result []*models.User
	for _, u := range m.users {
		if contains(u.Username, query) || contains(u.Nickname, query) {
			result = append(result, u)
			if len(result) >= limit {
				break
			}
		}
	}
	return result, nil
}

func contains(s, substr string) bool {
	return len(s) >= len(substr) && (s == substr || len(substr) == 0)
}

func TestUserService_GetByID(t *testing.T) {
	repo := NewMockUserRepository()
	service := user.NewService(repo)

	// 创建测试用户
	testUser := &models.User{
		ID:        "user123",
		Username:  "testuser",
		Nickname:  "Test User",
		Status:    "offline",
		CreatedAt: time.Now(),
		UpdatedAt: time.Now(),
	}
	repo.Create(testUser)

	// 获取用户
	found, err := service.GetByID("user123")
	if err != nil {
		t.Fatalf("Failed to get user: %v", err)
	}

	if found.ID != "user123" {
		t.Errorf("Expected ID 'user123', got '%s'", found.ID)
	}
	if found.Username != "testuser" {
		t.Errorf("Expected Username 'testuser', got '%s'", found.Username)
	}
}

func TestUserService_GetByIDEmpty(t *testing.T) {
	repo := NewMockUserRepository()
	service := user.NewService(repo)

	_, err := service.GetByID("")
	if err == nil {
		t.Fatal("Expected error for empty ID")
	}
}

func TestUserService_GetByUsername(t *testing.T) {
	repo := NewMockUserRepository()
	service := user.NewService(repo)

	// 创建测试用户
	testUser := &models.User{
		ID:        "user123",
		Username:  "testuser",
		Nickname:  "Test User",
		Status:    "offline",
		CreatedAt: time.Now(),
		UpdatedAt: time.Now(),
	}
	repo.Create(testUser)

	// 获取用户
	found, err := service.GetByUsername("testuser")
	if err != nil {
		t.Fatalf("Failed to get user: %v", err)
	}

	if found.ID != "user123" {
		t.Errorf("Expected ID 'user123', got '%s'", found.ID)
	}
}

func TestUserService_UpdateProfile(t *testing.T) {
	repo := NewMockUserRepository()
	service := user.NewService(repo)

	// 创建测试用户
	testUser := &models.User{
		ID:        "user123",
		Username:  "testuser",
		Nickname:  "Old Nickname",
		Email:     "old@example.com",
		Status:    "offline",
		CreatedAt: time.Now(),
		UpdatedAt: time.Now(),
	}
	repo.Create(testUser)

	// 更新资料
	updated, err := service.UpdateProfile("user123", "New Nickname", "http://avatar.com/new.jpg", "new@example.com")
	if err != nil {
		t.Fatalf("Failed to update profile: %v", err)
	}

	if updated.Nickname != "New Nickname" {
		t.Errorf("Expected Nickname 'New Nickname', got '%s'", updated.Nickname)
	}
	if updated.Avatar != "http://avatar.com/new.jpg" {
		t.Errorf("Expected Avatar 'http://avatar.com/new.jpg', got '%s'", updated.Avatar)
	}
	if updated.Email != "new@example.com" {
		t.Errorf("Expected Email 'new@example.com', got '%s'", updated.Email)
	}
}

func TestUserService_UpdateStatus(t *testing.T) {
	repo := NewMockUserRepository()
	service := user.NewService(repo)

	// 创建测试用户
	testUser := &models.User{
		ID:        "user123",
		Username:  "testuser",
		Status:    "offline",
		CreatedAt: time.Now(),
		UpdatedAt: time.Now(),
	}
	repo.Create(testUser)

	// 更新状态
	err := service.UpdateStatus("user123", "online")
	if err != nil {
		t.Fatalf("Failed to update status: %v", err)
	}

	// 验证状态
	found, _ := repo.FindByID("user123")
	if found.Status != "online" {
		t.Errorf("Expected status 'online', got '%s'", found.Status)
	}
}

func TestUserService_UpdateStatusInvalid(t *testing.T) {
	repo := NewMockUserRepository()
	service := user.NewService(repo)

	// 创建测试用户
	testUser := &models.User{
		ID:        "user123",
		Username:  "testuser",
		Status:    "offline",
		CreatedAt: time.Now(),
		UpdatedAt: time.Now(),
	}
	repo.Create(testUser)

	// 尝试更新为无效状态
	err := service.UpdateStatus("user123", "invalid")
	if err == nil {
		t.Fatal("Expected error for invalid status")
	}
}

func TestUserService_SearchUsers(t *testing.T) {
	repo := NewMockUserRepository()
	service := user.NewService(repo)

	// 创建测试用户
	users := []*models.User{
		{ID: "user1", Username: "alice", Nickname: "Alice Smith", Status: "online", CreatedAt: time.Now(), UpdatedAt: time.Now()},
		{ID: "user2", Username: "bob", Nickname: "Bob Jones", Status: "offline", CreatedAt: time.Now(), UpdatedAt: time.Now()},
		{ID: "user3", Username: "charlie", Nickname: "Charlie Brown", Status: "online", CreatedAt: time.Now(), UpdatedAt: time.Now()},
	}
	for _, u := range users {
		repo.Create(u)
	}

	// 搜索用户
	results, err := service.SearchUsers("alice", 10)
	if err != nil {
		t.Fatalf("Failed to search users: %v", err)
	}

	if len(results) != 1 {
		t.Errorf("Expected 1 result, got %d", len(results))
	}
}

func TestUserService_SearchUsersEmptyQuery(t *testing.T) {
	repo := NewMockUserRepository()
	service := user.NewService(repo)

	_, err := service.SearchUsers("", 10)
	if err == nil {
		t.Fatal("Expected error for empty query")
	}
}