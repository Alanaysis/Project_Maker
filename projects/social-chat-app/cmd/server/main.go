package main

import (
	"database/sql"
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"os"
	"strconv"
	"time"

	"social-chat-app/internal/auth"
	"social-chat-app/internal/message"
	"social-chat-app/internal/user"
	"social-chat-app/internal/websocket"

	"github.com/gorilla/websocket"
	_ "github.com/mattn/go-sqlite3"
)

// Config 服务器配置
type Config struct {
	Port      int
	DBPath    string
	JWTSecret string
	JWTExpiry time.Duration
}

// LoadConfig 从环境变量加载配置
func LoadConfig() *Config {
	port, _ := strconv.Atoi(getEnv("CHAT_SERVER_PORT", "8080"))
	jwtExpiry, _ := time.ParseDuration(getEnv("CHAT_JWT_EXPIRY", "24h"))

	return &Config{
		Port:      port,
		DBPath:    getEnv("CHAT_DB_PATH", "./data/chat.db"),
		JWTSecret: getEnv("CHAT_JWT_SECRET", "default-secret-change-this"),
		JWTExpiry: jwtExpiry,
	}
}

func getEnv(key, defaultValue string) string {
	if value := os.Getenv(key); value != "" {
		return value
	}
	return defaultValue
}

// Server 服务器结构
type Server struct {
	config         *Config
	db             *sql.DB
	authService    *auth.AuthService
	userService    *user.Service
	messageService *message.Service
	wsManager      *websocket.Manager
	jwtManager     *auth.JWTManager
	authMiddleware *auth.Middleware
	upgrader       websocket.Upgrader
}

// NewServer 创建新的服务器
func NewServer(config *Config) (*Server, error) {
	// 初始化数据库
	db, err := initDB(config.DBPath)
	if err != nil {
		return nil, fmt.Errorf("failed to initialize database: %w", err)
	}

	// 创建存储层
	userRepo := user.NewSQLiteRepository(db)
	messageRepo := message.NewSQLiteRepository(db)

	// 创建 JWT 管理器
	jwtManager := auth.NewJWTManager(config.JWTSecret, config.JWTExpiry)

	// 创建服务层
	authService := auth.NewAuthService(jwtManager, userRepo)
	userService := user.NewService(userRepo)
	messageService := message.NewService(messageRepo)

	// 创建 WebSocket 管理器
	wsManager := websocket.NewManager(messageService, userService)

	// 创建认证中间件
	authMiddleware := auth.NewMiddleware(jwtManager)

	// WebSocket Upgrader
	upgrader := websocket.Upgrader{
		ReadBufferSize:  1024,
		WriteBufferSize: 1024,
		CheckOrigin: func(r *http.Request) bool {
			return true // 开发环境允许所有来源
		},
	}

	return &Server{
		config:         config,
		db:             db,
		authService:    authService,
		userService:    userService,
		messageService: messageService,
		wsManager:      wsManager,
		jwtManager:     jwtManager,
		authMiddleware: authMiddleware,
		upgrader:       upgrader,
	}, nil
}

// Start 启动服务器
func (s *Server) Start() error {
	// 启动 WebSocket 管理器
	go s.wsManager.Start()

	// 设置路由
	mux := http.NewServeMux()

	// 公开 API（无需认证）
	mux.HandleFunc("/api/register", s.handleRegister)
	mux.HandleFunc("/api/login", s.handleLogin)

	// WebSocket 端点
	mux.HandleFunc("/ws", s.handleWebSocket)

	// 需要认证的 API
	protectedMux := http.NewServeMux()
	protectedMux.HandleFunc("/api/user/", s.handleUser)
	protectedMux.HandleFunc("/api/users", s.handleSearchUsers)
	protectedMux.HandleFunc("/api/messages/", s.handleMessages)

	// 应用认证中间件
	mux.Handle("/api/user/", s.authMiddleware.Authenticate(protectedMux))
	mux.Handle("/api/users", s.authMiddleware.Authenticate(protectedMux))
	mux.Handle("/api/messages/", s.authMiddleware.Authenticate(protectedMux))

	addr := fmt.Sprintf(":%d", s.config.Port)
	log.Printf("Server starting on %s", addr)

	return http.ListenAndServe(addr, mux)
}

// Close 关闭服务器
func (s *Server) Close() error {
	return s.db.Close()
}

// HTTP 处理器

func (s *Server) handleRegister(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Error(w, `{"error":"method not allowed"}`, http.StatusMethodNotAllowed)
		return
	}

	var req auth.RegisterRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, `{"error":"invalid request body"}`, http.StatusBadRequest)
		return
	}

	resp, err := s.authService.Register(&req)
	if err != nil {
		http.Error(w, fmt.Sprintf(`{"error":"%s"}`, err.Error()), http.StatusBadRequest)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusCreated)
	json.NewEncoder(w).Encode(resp)
}

func (s *Server) handleLogin(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Error(w, `{"error":"method not allowed"}`, http.StatusMethodNotAllowed)
		return
	}

	var req auth.LoginRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, `{"error":"invalid request body"}`, http.StatusBadRequest)
		return
	}

	resp, err := s.authService.Login(&req)
	if err != nil {
		http.Error(w, fmt.Sprintf(`{"error":"%s"}`, err.Error()), http.StatusUnauthorized)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(resp)
}

func (s *Server) handleWebSocket(w http.ResponseWriter, r *http.Request) {
	// 验证 Token
	claims, err := s.authMiddleware.ExtractTokenFromQuery(r)
	if err != nil {
		http.Error(w, `{"error":"unauthorized"}`, http.StatusUnauthorized)
		return
	}

	// 升级 HTTP 连接为 WebSocket
	conn, err := s.upgrader.Upgrade(w, r, nil)
	if err != nil {
		log.Printf("Failed to upgrade connection: %v", err)
		return
	}

	// 创建连接对象
	wsConn := websocket.NewConnection(claims.UserID, conn, s.wsManager)

	// 注册连接
	s.wsManager.register <- wsConn

	// 启动读写 goroutine
	go wsConn.WritePump()
	go wsConn.ReadPump()
}

func (s *Server) handleUser(w http.ResponseWriter, r *http.Request) {
	claims, ok := auth.GetClaimsFromContext(r.Context())
	if !ok {
		http.Error(w, `{"error":"unauthorized"}`, http.StatusUnauthorized)
		return
	}

	// 获取用户 ID（从 URL 路径）
	userID := r.URL.Path[len("/api/user/"):]

	switch r.Method {
	case http.MethodGet:
		// 获取用户信息
		user, err := s.userService.GetByID(userID)
		if err != nil {
			http.Error(w, `{"error":"user not found"}`, http.StatusNotFound)
			return
		}
		w.Header().Set("Content-Type", "application/json")
		json.NewEncoder(w).Encode(user)

	case http.MethodPut:
		// 更新用户信息（只能更新自己的信息）
		if claims.UserID != userID {
			http.Error(w, `{"error":"forbidden"}`, http.StatusForbidden)
			return
		}

		var req struct {
			Nickname string `json:"nickname"`
			Avatar   string `json:"avatar"`
			Email    string `json:"email"`
		}
		if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
			http.Error(w, `{"error":"invalid request body"}`, http.StatusBadRequest)
			return
		}

		user, err := s.userService.UpdateProfile(userID, req.Nickname, req.Avatar, req.Email)
		if err != nil {
			http.Error(w, fmt.Sprintf(`{"error":"%s"}`, err.Error()), http.StatusInternalServerError)
			return
		}

		w.Header().Set("Content-Type", "application/json")
		json.NewEncoder(w).Encode(user)

	default:
		http.Error(w, `{"error":"method not allowed"}`, http.StatusMethodNotAllowed)
	}
}

func (s *Server) handleSearchUsers(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet {
		http.Error(w, `{"error":"method not allowed"}`, http.StatusMethodNotAllowed)
		return
	}

	query := r.URL.Query().Get("q")
	if query == "" {
		http.Error(w, `{"error":"search query is required"}`, http.StatusBadRequest)
		return
	}

	limit, _ := strconv.Atoi(r.URL.Query().Get("limit"))
	if limit <= 0 || limit > 50 {
		limit = 20
	}

	users, err := s.userService.SearchUsers(query, limit)
	if err != nil {
		http.Error(w, fmt.Sprintf(`{"error":"%s"}`, err.Error()), http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(users)
}

func (s *Server) handleMessages(w http.ResponseWriter, r *http.Request) {
	claims, ok := auth.GetClaimsFromContext(r.Context())
	if !ok {
		http.Error(w, `{"error":"unauthorized"}`, http.StatusUnauthorized)
		return
	}

	// 解析路径：/api/messages/{user_id} 或 /api/messages/unread
	path := r.URL.Path[len("/api/messages/"):]

	switch {
	case path == "unread":
		// 获取未读消息
		messages, err := s.messageService.GetUnreadMessages(claims.UserID)
		if err != nil {
			http.Error(w, fmt.Sprintf(`{"error":"%s"}`, err.Error()), http.StatusInternalServerError)
			return
		}
		w.Header().Set("Content-Type", "application/json")
		json.NewEncoder(w).Encode(messages)

	default:
		// 获取与某用户的对话历史
		if r.Method != http.MethodGet {
			http.Error(w, `{"error":"method not allowed"}`, http.StatusMethodNotAllowed)
			return
		}

		otherUserID := path
		limit, _ := strconv.Atoi(r.URL.Query().Get("limit"))
		offset, _ := strconv.Atoi(r.URL.Query().Get("offset"))

		if limit <= 0 || limit > 100 {
			limit = 50
		}
		if offset < 0 {
			offset = 0
		}

		messages, err := s.messageService.GetConversation(claims.UserID, otherUserID, limit, offset)
		if err != nil {
			http.Error(w, fmt.Sprintf(`{"error":"%s"}`, err.Error()), http.StatusInternalServerError)
			return
		}

		w.Header().Set("Content-Type", "application/json")
		json.NewEncoder(w).Encode(messages)
	}
}

// initDB 初始化数据库
func initDB(dbPath string) (*sql.DB, error) {
	// 确保数据目录存在
	// os.MkdirAll 由调用方处理

	db, err := sql.Open("sqlite3", dbPath)
	if err != nil {
		return nil, err
	}

	// 测试连接
	if err := db.Ping(); err != nil {
		return nil, err
	}

	// 创建表
	if err := createTables(db); err != nil {
		return nil, err
	}

	return db, nil
}

// createTables 创建数据库表
func createTables(db *sql.DB) error {
	queries := []string{
		`CREATE TABLE IF NOT EXISTS users (
			id VARCHAR(36) PRIMARY KEY,
			username VARCHAR(50) UNIQUE NOT NULL,
			password VARCHAR(255) NOT NULL,
			email VARCHAR(100),
			nickname VARCHAR(50),
			avatar VARCHAR(255),
			status VARCHAR(20) DEFAULT 'offline',
			created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
			updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
		)`,
		`CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)`,
		`CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)`,
		`CREATE TABLE IF NOT EXISTS messages (
			id VARCHAR(36) PRIMARY KEY,
			type VARCHAR(20) NOT NULL,
			from_user VARCHAR(36) NOT NULL,
			to_user VARCHAR(36) NOT NULL,
			content TEXT NOT NULL,
			status VARCHAR(20) DEFAULT 'sent',
			created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
			updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
		)`,
		`CREATE INDEX IF NOT EXISTS idx_messages_from ON messages(from_user)`,
		`CREATE INDEX IF NOT EXISTS idx_messages_to ON messages(to_user)`,
		`CREATE INDEX IF NOT EXISTS idx_messages_created ON messages(created_at)`,
		`CREATE INDEX IF NOT EXISTS idx_messages_conversation ON messages(from_user, to_user, created_at)`,
		`CREATE TABLE IF NOT EXISTS offline_messages (
			id VARCHAR(36) PRIMARY KEY,
			from_user VARCHAR(36) NOT NULL,
			to_user VARCHAR(36) NOT NULL,
			content TEXT NOT NULL,
			type VARCHAR(20) NOT NULL,
			created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
		)`,
		`CREATE INDEX IF NOT EXISTS idx_offline_messages_to ON offline_messages(to_user)`,
		`CREATE TABLE IF NOT EXISTS groups (
			id VARCHAR(36) PRIMARY KEY,
			name VARCHAR(50) NOT NULL,
			description TEXT,
			owner_id VARCHAR(36) NOT NULL,
			avatar VARCHAR(255),
			member_count INT DEFAULT 0,
			created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
			updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
		)`,
		`CREATE TABLE IF NOT EXISTS group_members (
			group_id VARCHAR(36) NOT NULL,
			user_id VARCHAR(36) NOT NULL,
			role VARCHAR(20) DEFAULT 'member',
			joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
			PRIMARY KEY (group_id, user_id)
		)`,
		`CREATE INDEX IF NOT EXISTS idx_group_members_user ON group_members(user_id)`,
	}

	for _, query := range queries {
		if _, err := db.Exec(query); err != nil {
			return fmt.Errorf("failed to execute query: %w", err)
		}
	}

	return nil
}

func main() {
	// 加载配置
	config := LoadConfig()

	// 创建服务器
	server, err := NewServer(config)
	if err != nil {
		log.Fatalf("Failed to create server: %v", err)
	}
	defer server.Close()

	// 启动服务器
	log.Printf("Starting Social Chat Server...")
	if err := server.Start(); err != nil {
		log.Fatalf("Server failed: %v", err)
	}
}