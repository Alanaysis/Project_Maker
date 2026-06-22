package auth

import (
	"context"
	"net/http"
	"strings"
)

// contextKey 是 context 值的键类型
type contextKey string

const (
	// ClaimsKey 是存储在 context 中的 Claims 键
	ClaimsKey contextKey = "claims"
)

// Middleware 认证中间件
type Middleware struct {
	jwtManager *JWTManager
}

// NewMiddleware 创建新的认证中间件
func NewMiddleware(jwtManager *JWTManager) *Middleware {
	return &Middleware{
		jwtManager: jwtManager,
	}
}

// Authenticate HTTP 认证中间件
func (m *Middleware) Authenticate(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		// 从 Header 获取 Token
		authHeader := r.Header.Get("Authorization")
		if authHeader == "" {
			http.Error(w, `{"error":"authorization header required"}`, http.StatusUnauthorized)
			return
		}

		// 解析 Bearer Token
		parts := strings.SplitN(authHeader, " ", 2)
		if len(parts) != 2 || parts[0] != "Bearer" {
			http.Error(w, `{"error":"invalid authorization header format"}`, http.StatusUnauthorized)
			return
		}

		token := parts[1]

		// 验证 Token
		claims, err := m.jwtManager.Verify(token)
		if err != nil {
			http.Error(w, `{"error":"invalid or expired token"}`, http.StatusUnauthorized)
			return
		}

		// 将 Claims 存储到 context
		ctx := context.WithValue(r.Context(), ClaimsKey, claims)
		next.ServeHTTP(w, r.WithContext(ctx))
	})
}

// ExtractTokenFromHeader 从 Authorization header 提取 Token（用于 WebSocket）
func (m *Middleware) ExtractTokenFromHeader(r *http.Request) (*Claims, error) {
	// 从 Header 获取 Token
	authHeader := r.Header.Get("Authorization")
	if authHeader == "" {
		return nil, ErrTokenRequired
	}

	// 解析 Bearer Token
	parts := strings.SplitN(authHeader, " ", 2)
	if len(parts) != 2 || parts[0] != "Bearer" {
		return nil, ErrTokenRequired
	}

	token := parts[1]
	return m.jwtManager.Verify(token)
}

// GetClaimsFromContext 从 context 获取 Claims
func GetClaimsFromContext(ctx context.Context) (*Claims, bool) {
	claims, ok := ctx.Value(ClaimsKey).(*Claims)
	return claims, ok
}

// 错误定义
var (
	ErrTokenRequired = &AuthError{Code: 401, Message: "token is required"}
)

// AuthError 认证错误
type AuthError struct {
	Code    int
	Message string
}

func (e *AuthError) Error() string {
	return e.Message
}