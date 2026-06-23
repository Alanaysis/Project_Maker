package examples

import (
	"context"
	"fmt"
	"time"
)

// Calculator 计算器服务
type Calculator struct{}

// AddRequest 加法请求
type AddRequest struct {
	A int `json:"a"`
	B int `json:"b"`
}

// AddResponse 加法响应
type AddResponse struct {
	Result int `json:"result"`
}

// Add 加法
func (c *Calculator) Add(ctx context.Context, req *AddRequest, resp *AddResponse) error {
	resp.Result = req.A + req.B
	return nil
}

// MultiplyRequest 乘法请求
type MultiplyRequest struct {
	A int `json:"a"`
	B int `json:"b"`
}

// MultiplyResponse 乘法响应
type MultiplyResponse struct {
	Result int `json:"result"`
}

// Multiply 乘法
func (c *Calculator) Multiply(ctx context.Context, req *MultiplyRequest, resp *MultiplyResponse) error {
	resp.Result = req.A * req.B
	return nil
}

// UserService 用户服务
type UserService struct{}

// GetUserRequest 获取用户请求
type GetUserRequest struct {
	UserID string `json:"user_id"`
}

// GetUserResponse 获取用户响应
type GetUserResponse struct {
	UserID   string `json:"user_id"`
	Username string `json:"username"`
	Email    string `json:"email"`
}

// GetUser 获取用户
func (u *UserService) GetUser(ctx context.Context, req *GetUserRequest, resp *GetUserResponse) error {
	// 模拟数据库查询
	time.Sleep(10 * time.Millisecond)

	resp.UserID = req.UserID
	resp.Username = fmt.Sprintf("user_%s", req.UserID)
	resp.Email = fmt.Sprintf("%s@example.com", req.UserID)

	return nil
}

// ListUsersRequest 列出用户请求
type ListUsersRequest struct {
	Page     int `json:"page"`
	PageSize int `json:"page_size"`
}

// ListUsersResponse 列出用户响应
type ListUsersResponse struct {
	Users []*GetUserResponse `json:"users"`
	Total int                `json:"total"`
}

// ListUsers 列出用户
func (u *UserService) ListUsers(ctx context.Context, req *ListUsersRequest, resp *ListUsersResponse) error {
	// 模拟数据库查询
	time.Sleep(20 * time.Millisecond)

	users := make([]*GetUserResponse, 0)
	for i := 0; i < req.PageSize; i++ {
		users = append(users, &GetUserResponse{
			UserID:   fmt.Sprintf("user_%d", (req.Page-1)*req.PageSize+i+1),
			Username: fmt.Sprintf("user_%d", (req.Page-1)*req.PageSize+i+1),
			Email:    fmt.Sprintf("user_%d@example.com", (req.Page-1)*req.PageSize+i+1),
		})
	}

	resp.Users = users
	resp.Total = 100 // 模拟总数

	return nil
}
