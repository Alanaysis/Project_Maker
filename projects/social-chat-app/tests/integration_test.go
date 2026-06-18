package tests

import (
	"bytes"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"social-chat-app/internal/auth"
	"social-chat-app/internal/message"
	"social-chat-app/internal/user"
	"social-chat-app/pkg/models"
	"testing"
	"time"
)

// TestServer 测试服务器结构
type TestServer struct {
	AuthService    *auth.AuthService
	UserService    *user.Service
	MessageService *message.Service
	JWTManager     *auth.JWTManager
}

// NewTestServer 创建测试服务器
func NewTestServer() *TestServer {
	// 创建模拟存储
	userRepo := NewMockUserRepository()
	messageRepo := NewMockMessageRepository()

	// 创建 JWT 管理器
	jwtManager := auth.NewJWTManager("test-secret", 24*time.Hour)

	// 创建服务
	authService := auth.NewAuthService(jwtManager, userRepo)
	userService := user.NewService(userRepo)
	messageService := message.NewService(messageRepo)

	return &TestServer{
		AuthService:    authService,
		UserService:    userService,
		MessageService: messageService,
		JWTManager:     jwtManager,
	}
}

func TestIntegration_RegisterAndLogin(t *testing.T) {
	server := NewTestServer()

	// 注册用户
	registerReq := &auth.RegisterRequest{
		Username: "testuser",
		Password: "password123",
		Email:    "test@example.com",
	}

	registerResp, err := server.AuthService.Register(registerReq)
	if err != nil {
		t.Fatalf("Failed to register: %v", err)
	}

	if registerResp.Token == "" {
		t.Fatal("Token should not be empty")
	}
	if registerResp.User == nil {
		t.Fatal("User should not be nil")
	}

	// 登录用户
	loginReq := &auth.LoginRequest{
		Username: "testuser",
		Password: "password123",
	}

	loginResp, err := server.AuthService.Login(loginReq)
	if err != nil {
		t.Fatalf("Failed to login: %v", err)
	}

	if loginResp.Token == "" {
		t.Fatal("Token should not be empty")
	}

	// 验证 Token
	claims, err := server.JWTManager.Verify(loginResp.Token)
	if err != nil {
		t.Fatalf("Failed to verify token: %v", err)
	}

	if claims.UserID != registerResp.User.ID {
		t.Errorf("Expected UserID '%s', got '%s'", registerResp.User.ID, claims.UserID)
	}
}

func TestIntegration_SendAndReceiveMessage(t *testing.T) {
	server := NewTestServer()

	// 注册两个用户
	user1Resp, _ := server.AuthService.Register(&auth.RegisterRequest{
		Username: "user1",
		Password: "password123",
	})
	user2Resp, _ := server.AuthService.Register(&auth.RegisterRequest{
		Username: "user2",
		Password: "password123",
	})

	// user1 发送消息给 user2
	msg, err := server.MessageService.CreateMessage(
		user1Resp.User.ID,
		user2Resp.User.ID,
		"Hello from user1!",
		"text",
	)
	if err != nil {
		t.Fatalf("Failed to create message: %v", err)
	}

	if msg.ID == "" {
		t.Fatal("Message ID should not be empty")
	}
	if msg.From != user1Resp.User.ID {
		t.Errorf("Expected From '%s', got '%s'", user1Resp.User.ID, msg.From)
	}
	if msg.To != user2Resp.User.ID {
		t.Errorf("Expected To '%s', got '%s'", user2Resp.User.ID, msg.To)
	}

	// 获取对话历史
	messages, err := server.MessageService.GetConversation(
		user1Resp.User.ID,
		user2Resp.User.ID,
		50,
		0,
	)
	if err != nil {
		t.Fatalf("Failed to get conversation: %v", err)
	}

	if len(messages) != 1 {
		t.Errorf("Expected 1 message, got %d", len(messages))
	}
}

func TestIntegration_OfflineMessages(t *testing.T) {
	server := NewTestServer()

	// 注册用户
	user1Resp, _ := server.AuthService.Register(&auth.RegisterRequest{
		Username: "user1",
		Password: "password123",
	})
	user2Resp, _ := server.AuthService.Register(&auth.RegisterRequest{
		Username: "user2",
		Password: "password123",
	})

	// 创建离线消息
	offlineMsg := &models.Message{
		ID:        "offline1",
		Type:      "text",
		From:      user1Resp.User.ID,
		To:        user2Resp.User.ID,
		Content:   "Offline message",
		Status:    "sent",
		CreatedAt: time.Now(),
	}

	// 保存离线消息
	err := server.MessageService.SaveOfflineMessage(offlineMsg)
	if err != nil {
		t.Fatalf("Failed to save offline message: %v", err)
	}

	// 获取离线消息
	messages, err := server.MessageService.GetOfflineMessages(user2Resp.User.ID)
	if err != nil {
		t.Fatalf("Failed to get offline messages: %v", err)
	}

	if len(messages) != 1 {
		t.Errorf("Expected 1 offline message, got %d", len(messages))
	}

	// 删除离线消息
	err = server.MessageService.DeleteOfflineMessages([]string{"offline1"})
	if err != nil {
		t.Fatalf("Failed to delete offline messages: %v", err)
	}

	// 验证已删除
	messages, _ = server.MessageService.GetOfflineMessages(user2Resp.User.ID)
	if len(messages) != 0 {
		t.Errorf("Expected 0 offline messages, got %d", len(messages))
	}
}

func TestIntegration_UserSearch(t *testing.T) {
	server := NewTestServer()

	// 注册用户
	server.AuthService.Register(&auth.RegisterRequest{
		Username: "alice",
		Password: "password123",
	})
	server.AuthService.Register(&auth.RegisterRequest{
		Username: "bob",
		Password: "password123",
	})
	server.AuthService.Register(&auth.RegisterRequest{
		Username: "charlie",
		Password: "password123",
	})

	// 搜索用户
	users, err := server.UserService.SearchUsers("alice", 10)
	if err != nil {
		t.Fatalf("Failed to search users: %v", err)
	}

	if len(users) != 1 {
		t.Errorf("Expected 1 user, got %d", len(users))
	}

	if users[0].Username != "alice" {
		t.Errorf("Expected username 'alice', got '%s'", users[0].Username)
	}
}

func TestIntegration_UpdateProfile(t *testing.T) {
	server := NewTestServer()

	// 注册用户
	resp, _ := server.AuthService.Register(&auth.RegisterRequest{
		Username: "testuser",
		Password: "password123",
	})

	// 更新资料
	updated, err := server.UserService.UpdateProfile(
		resp.User.ID,
		"New Nickname",
		"http://avatar.com/new.jpg",
		"new@example.com",
	)
	if err != nil {
		t.Fatalf("Failed to update profile: %v", err)
	}

	if updated.Nickname != "New Nickname" {
		t.Errorf("Expected Nickname 'New Nickname', got '%s'", updated.Nickname)
	}
	if updated.Avatar != "http://avatar.com/new.jpg" {
		t.Errorf("Expected Avatar 'http://avatar.com/new.jpg', got '%s'", updated.Avatar)
	}
}

func TestIntegration_MarkAsRead(t *testing.T) {
	server := NewTestServer()

	// 注册用户
	user1Resp, _ := server.AuthService.Register(&auth.RegisterRequest{
		Username: "user1",
		Password: "password123",
	})
	user2Resp, _ := server.AuthService.Register(&auth.RegisterRequest{
		Username: "user2",
		Password: "password123",
	})

	// 发送消息
	msg, _ := server.MessageService.CreateMessage(
		user1Resp.User.ID,
		user2Resp.User.ID,
		"Hello!",
		"text",
	)

	// 标记为已读
	err := server.MessageService.MarkAsRead([]string{msg.ID})
	if err != nil {
		t.Fatalf("Failed to mark as read: %v", err)
	}

	// 验证状态
	updated, _ := server.MessageService.GetByID(msg.ID)
	if updated.Status != "read" {
		t.Errorf("Expected status 'read', got '%s'", updated.Status)
	}
}

func TestHTTP_RegisterEndpoint(t *testing.T) {
	server := NewTestServer()

	// 创建 HTTP 处理器
	handler := http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		var req auth.RegisterRequest
		json.NewDecoder(r.Body).Decode(&req)

		resp, err := server.AuthService.Register(&req)
		if err != nil {
			http.Error(w, err.Error(), http.StatusBadRequest)
			return
		}

		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusCreated)
		json.NewEncoder(w).Encode(resp)
	})

	// 发送请求
	body := `{"username":"testuser","password":"password123"}`
	req := httptest.NewRequest(http.MethodPost, "/api/register", bytes.NewBufferString(body))
	req.Header.Set("Content-Type", "application/json")
	w := httptest.NewRecorder()

	handler.ServeHTTP(w, req)

	if w.Code != http.StatusCreated {
		t.Errorf("Expected status %d, got %d", http.StatusCreated, w.Code)
	}

	var resp auth.AuthResponse
	json.Unmarshal(w.Body.Bytes(), &resp)

	if resp.Token == "" {
		t.Error("Token should not be empty")
	}
	if resp.User == nil {
		t.Fatal("User should not be nil")
	}
}