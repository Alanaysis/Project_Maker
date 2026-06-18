package auth

import (
	"errors"
	"fmt"
	"social-chat-app/pkg/models"
	"time"

	"github.com/google/uuid"
	"golang.org/x/crypto/bcrypt"
)

// AuthService 提供用户认证服务
type AuthService struct {
	jwtManager *JWTManager
	userStore  UserStore
}

// UserStore 用户存储接口
type UserStore interface {
	Create(user *models.User) error
	FindByUsername(username string) (*models.User, error)
	FindByID(id string) (*models.User, error)
	Update(user *models.User) error
}

// NewAuthService 创建新的认证服务
func NewAuthService(jwtManager *JWTManager, userStore UserStore) *AuthService {
	return &AuthService{
		jwtManager: jwtManager,
		userStore:  userStore,
	}
}

// RegisterRequest 注册请求
type RegisterRequest struct {
	Username string `json:"username"`
	Password string `json:"password"`
	Email    string `json:"email,omitempty"`
	Nickname string `json:"nickname,omitempty"`
}

// LoginRequest 登录请求
type LoginRequest struct {
	Username string `json:"username"`
	Password string `json:"password"`
}

// AuthResponse 认证响应
type AuthResponse struct {
	Token  string       `json:"token"`
	User   *models.User `json:"user"`
}

// Register 用户注册
func (s *AuthService) Register(req *RegisterRequest) (*AuthResponse, error) {
	// 验证输入
	if err := s.validateRegisterRequest(req); err != nil {
		return nil, err
	}

	// 检查用户名是否已存在
	existingUser, _ := s.userStore.FindByUsername(req.Username)
	if existingUser != nil {
		return nil, errors.New("username already exists")
	}

	// 加密密码
	hashedPassword, err := bcrypt.GenerateFromPassword([]byte(req.Password), bcrypt.DefaultCost)
	if err != nil {
		return nil, fmt.Errorf("failed to hash password: %w", err)
	}

	// 创建用户
	user := &models.User{
		ID:        uuid.New().String(),
		Username:  req.Username,
		Password:  string(hashedPassword),
		Email:     req.Email,
		Nickname:  req.Nickname,
		Status:    models.UserStatusOffline,
		CreatedAt: time.Now(),
		UpdatedAt: time.Now(),
	}

	if user.Nickname == "" {
		user.Nickname = req.Username
	}

	if err := s.userStore.Create(user); err != nil {
		return nil, fmt.Errorf("failed to create user: %w", err)
	}

	// 生成 Token
	token, err := s.jwtManager.Generate(user.ID, user.Username, "user")
	if err != nil {
		return nil, fmt.Errorf("failed to generate token: %w", err)
	}

	return &AuthResponse{
		Token: token,
		User:  user,
	}, nil
}

// Login 用户登录
func (s *AuthService) Login(req *LoginRequest) (*AuthResponse, error) {
	// 验证输入
	if req.Username == "" || req.Password == "" {
		return nil, errors.New("username and password are required")
	}

	// 查找用户
	user, err := s.userStore.FindByUsername(req.Username)
	if err != nil {
		return nil, errors.New("invalid username or password")
	}

	// 验证密码
	if err := bcrypt.CompareHashAndPassword([]byte(user.Password), []byte(req.Password)); err != nil {
		return nil, errors.New("invalid username or password")
	}

	// 生成 Token
	token, err := s.jwtManager.Generate(user.ID, user.Username, "user")
	if err != nil {
		return nil, fmt.Errorf("failed to generate token: %w", err)
	}

	return &AuthResponse{
		Token: token,
		User:  user,
	}, nil
}

// validateRegisterRequest 验证注册请求
func (s *AuthService) validateRegisterRequest(req *RegisterRequest) error {
	if req.Username == "" {
		return errors.New("username is required")
	}
	if len(req.Username) < 3 || len(req.Username) > 20 {
		return errors.New("username must be between 3 and 20 characters")
	}
	if req.Password == "" {
		return errors.New("password is required")
	}
	if len(req.Password) < 8 {
		return errors.New("password must be at least 8 characters")
	}
	return nil
}