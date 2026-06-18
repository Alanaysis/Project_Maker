package tests

import (
	"social-chat-app/internal/auth"
	"social-chat-app/pkg/models"
	"testing"
	"time"
)

// MockUserStore 模拟用户存储
type MockUserStore struct {
	users map[string]*models.User
}

func NewMockUserStore() *MockUserStore {
	return &MockUserStore{
		users: make(map[string]*models.User),
	}
}

func (m *MockUserStore) Create(user *models.User) error {
	m.users[user.ID] = user
	return nil
}

func (m *MockUserStore) FindByUsername(username string) (*models.User, error) {
	for _, user := range m.users {
		if user.Username == username {
			return user, nil
		}
	}
	return nil, nil
}

func (m *MockUserStore) FindByID(id string) (*models.User, error) {
	user, ok := m.users[id]
	if !ok {
		return nil, nil
	}
	return user, nil
}

func (m *MockUserStore) Update(user *models.User) error {
	m.users[user.ID] = user
	return nil
}

func TestJWTManager_Generate(t *testing.T) {
	manager := auth.NewJWTManager("test-secret", 24*time.Hour)

	token, err := manager.Generate("user123", "testuser", "user")
	if err != nil {
		t.Fatalf("Failed to generate token: %v", err)
	}

	if token == "" {
		t.Fatal("Token should not be empty")
	}
}

func TestJWTManager_Verify(t *testing.T) {
	manager := auth.NewJWTManager("test-secret", 24*time.Hour)

	// 生成 Token
	token, err := manager.Generate("user123", "testuser", "user")
	if err != nil {
		t.Fatalf("Failed to generate token: %v", err)
	}

	// 验证 Token
	claims, err := manager.Verify(token)
	if err != nil {
		t.Fatalf("Failed to verify token: %v", err)
	}

	if claims.UserID != "user123" {
		t.Errorf("Expected UserID 'user123', got '%s'", claims.UserID)
	}
	if claims.Username != "testuser" {
		t.Errorf("Expected Username 'testuser', got '%s'", claims.Username)
	}
}

func TestJWTManager_ExpiredToken(t *testing.T) {
	// 创建已过期的 Token
	manager := auth.NewJWTManager("test-secret", -1*time.Hour)

	token, err := manager.Generate("user123", "testuser", "user")
	if err != nil {
		t.Fatalf("Failed to generate token: %v", err)
	}

	// 验证应该失败
	_, err = manager.Verify(token)
	if err == nil {
		t.Fatal("Expected error for expired token")
	}
}

func TestJWTManager_InvalidSecret(t *testing.T) {
	manager1 := auth.NewJWTManager("secret1", 24*time.Hour)
	manager2 := auth.NewJWTManager("secret2", 24*time.Hour)

	// 用 secret1 生成 Token
	token, err := manager1.Generate("user123", "testuser", "user")
	if err != nil {
		t.Fatalf("Failed to generate token: %v", err)
	}

	// 用 secret2 验证应该失败
	_, err = manager2.Verify(token)
	if err == nil {
		t.Fatal("Expected error for invalid secret")
	}
}

func TestAuthService_Register(t *testing.T) {
	store := NewMockUserStore()
	jwtManager := auth.NewJWTManager("test-secret", 24*time.Hour)
	service := auth.NewAuthService(jwtManager, store)

	req := &auth.RegisterRequest{
		Username: "testuser",
		Password: "password123",
		Email:    "test@example.com",
	}

	resp, err := service.Register(req)
	if err != nil {
		t.Fatalf("Failed to register: %v", err)
	}

	if resp.Token == "" {
		t.Error("Token should not be empty")
	}
	if resp.User == nil {
		t.Fatal("User should not be nil")
	}
	if resp.User.Username != "testuser" {
		t.Errorf("Expected username 'testuser', got '%s'", resp.User.Username)
	}
}

func TestAuthService_RegisterDuplicateUsername(t *testing.T) {
	store := NewMockUserStore()
	jwtManager := auth.NewJWTManager("test-secret", 24*time.Hour)
	service := auth.NewAuthService(jwtManager, store)

	req := &auth.RegisterRequest{
		Username: "testuser",
		Password: "password123",
	}

	// 第一次注册应该成功
	_, err := service.Register(req)
	if err != nil {
		t.Fatalf("First registration should succeed: %v", err)
	}

	// 第二次注册应该失败
	_, err = service.Register(req)
	if err == nil {
		t.Fatal("Second registration should fail")
	}
}

func TestAuthService_RegisterInvalidInput(t *testing.T) {
	store := NewMockUserStore()
	jwtManager := auth.NewJWTManager("test-secret", 24*time.Hour)
	service := auth.NewAuthService(jwtManager, store)

	tests := []struct {
		name string
		req  *auth.RegisterRequest
	}{
		{
			name: "empty username",
			req: &auth.RegisterRequest{
				Username: "",
				Password: "password123",
			},
		},
		{
			name: "short username",
			req: &auth.RegisterRequest{
				Username: "ab",
				Password: "password123",
			},
		},
		{
			name: "empty password",
			req: &auth.RegisterRequest{
				Username: "testuser",
				Password: "",
			},
		},
		{
			name: "short password",
			req: &auth.RegisterRequest{
				Username: "testuser",
				Password: "1234567",
			},
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			_, err := service.Register(tt.req)
			if err == nil {
				t.Errorf("Expected error for %s", tt.name)
			}
		})
	}
}

func TestAuthService_Login(t *testing.T) {
	store := NewMockUserStore()
	jwtManager := auth.NewJWTManager("test-secret", 24*time.Hour)
	service := auth.NewAuthService(jwtManager, store)

	// 先注册
	registerReq := &auth.RegisterRequest{
		Username: "testuser",
		Password: "password123",
	}
	_, err := service.Register(registerReq)
	if err != nil {
		t.Fatalf("Failed to register: %v", err)
	}

	// 登录
	loginReq := &auth.LoginRequest{
		Username: "testuser",
		Password: "password123",
	}
	resp, err := service.Login(loginReq)
	if err != nil {
		t.Fatalf("Failed to login: %v", err)
	}

	if resp.Token == "" {
		t.Error("Token should not be empty")
	}
	if resp.User == nil {
		t.Fatal("User should not be nil")
	}
}

func TestAuthService_LoginWrongPassword(t *testing.T) {
	store := NewMockUserStore()
	jwtManager := auth.NewJWTManager("test-secret", 24*time.Hour)
	service := auth.NewAuthService(jwtManager, store)

	// 先注册
	registerReq := &auth.RegisterRequest{
		Username: "testuser",
		Password: "password123",
	}
	_, err := service.Register(registerReq)
	if err != nil {
		t.Fatalf("Failed to register: %v", err)
	}

	// 使用错误密码登录
	loginReq := &auth.LoginRequest{
		Username: "testuser",
		Password: "wrongpassword",
	}
	_, err = service.Login(loginReq)
	if err == nil {
		t.Fatal("Expected error for wrong password")
	}
}

func TestAuthService_LoginNonExistentUser(t *testing.T) {
	store := NewMockUserStore()
	jwtManager := auth.NewJWTManager("test-secret", 24*time.Hour)
	service := auth.NewAuthService(jwtManager, store)

	loginReq := &auth.LoginRequest{
		Username: "nonexistent",
		Password: "password123",
	}
	_, err := service.Login(loginReq)
	if err == nil {
		t.Fatal("Expected error for non-existent user")
	}
}