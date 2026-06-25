// Package trigger 提供流水线触发功能。
// 支持 Git Push、定时和手动触发方式。
package trigger

import (
	"context"
	"fmt"
	"log"
	"path/filepath"
	"strings"
	"sync"
	"time"
)

// TriggerType 触发类型
type TriggerType string

const (
	TriggerPush     TriggerType = "push"     // Git Push 触发
	TriggerSchedule TriggerType = "schedule" // 定时触发
	TriggerManual   TriggerType = "manual"   // 手动触发
)

// TriggerEvent 触发事件
type TriggerEvent struct {
	Type      TriggerType     `json:"type"`       // 触发类型
	Branch    string          `json:"branch"`     // 分支名
	Commit    string          `json:"commit"`     // 提交 ID
	Author    string          `json:"author"`     // 提交者
	Message   string          `json:"message"`    // 提交消息
	Timestamp time.Time       `json:"timestamp"`  // 触发时间
	Paths     []string        `json:"paths"`      // 变更的文件路径
	Metadata  map[string]string `json:"metadata"` // 元数据
}

// TriggerConfig 触发配置
type TriggerConfig struct {
	Push     *PushConfig `json:"push,omitempty"`     // Push 触发配置
	Schedule string      `json:"schedule,omitempty"` // Cron 表达式
	Manual   bool        `json:"manual,omitempty"`   // 是否允许手动触发
}

// PushConfig Push 触发配置
type PushConfig struct {
	Branches []string `json:"branches"`          // 触发的分支列表
	Paths    []string `json:"paths,omitempty"`   // 文件路径过滤
}

// TriggerFunc 触发回调函数
type TriggerFunc func(ctx context.Context, event *TriggerEvent) error

// Manager 触发管理器
type Manager struct {
	config    *TriggerConfig
	handlers  map[TriggerType][]TriggerFunc
	running   bool
	stopCh    chan struct{}
	mu        sync.RWMutex
}

// NewManager 创建触发管理器
func NewManager(config *TriggerConfig) *Manager {
	return &Manager{
		config:   config,
		handlers: make(map[TriggerType][]TriggerFunc),
		stopCh:   make(chan struct{}),
	}
}

// RegisterHandler 注册触发处理函数
func (m *Manager) RegisterHandler(triggerType TriggerType, handler TriggerFunc) {
	m.mu.Lock()
	defer m.mu.Unlock()
	m.handlers[triggerType] = append(m.handlers[triggerType], handler)
}

// Start 启动触发管理器
func (m *Manager) Start(ctx context.Context) error {
	m.mu.Lock()
	if m.running {
		m.mu.Unlock()
		return fmt.Errorf("触发管理器已在运行")
	}
	m.running = true
	m.mu.Unlock()

	// 启动定时触发
	if m.config.Schedule != "" {
		go m.startScheduler(ctx)
	}

	log.Println("触发管理器已启动")
	return nil
}

// Stop 停止触发管理器
func (m *Manager) Stop() {
	m.mu.Lock()
	defer m.mu.Unlock()

	if !m.running {
		return
	}

	close(m.stopCh)
	m.running = false
	log.Println("触发管理器已停止")
}

// TriggerManual 手动触发
func (m *Manager) TriggerManual(ctx context.Context, metadata map[string]string) error {
	if !m.config.Manual {
		return fmt.Errorf("手动触发未启用")
	}

	event := &TriggerEvent{
		Type:      TriggerManual,
		Timestamp: time.Now(),
		Metadata:  metadata,
	}

	return m.dispatch(ctx, event)
}

// TriggerPush Git Push 触发
func (m *Manager) TriggerPush(ctx context.Context, branch, commit, author, message string, paths []string) error {
	if m.config.Push == nil {
		return fmt.Errorf("Push 触发未配置")
	}

	// 检查分支是否匹配
	if !m.matchBranch(branch) {
		return fmt.Errorf("分支 %s 不在触发列表中", branch)
	}

	// 检查路径是否匹配
	if !m.matchPaths(paths) {
		return fmt.Errorf("变更路径不匹配触发条件")
	}

	event := &TriggerEvent{
		Type:      TriggerPush,
		Branch:    branch,
		Commit:    commit,
		Author:    author,
		Message:   message,
		Timestamp: time.Now(),
		Paths:     paths,
	}

	return m.dispatch(ctx, event)
}

// matchBranch 检查分支是否匹配
func (m *Manager) matchBranch(branch string) bool {
	if m.config.Push == nil || len(m.config.Push.Branches) == 0 {
		return true // 无限制
	}

	for _, b := range m.config.Push.Branches {
		if b == "*" || b == branch {
			return true
		}
		// 支持通配符
		if matched, _ := filepath.Match(b, branch); matched {
			return true
		}
	}
	return false
}

// matchPaths 检查路径是否匹配
func (m *Manager) matchPaths(paths []string) bool {
	if m.config.Push == nil || len(m.config.Push.Paths) == 0 {
		return true // 无路径限制
	}

	for _, path := range paths {
		for _, pattern := range m.config.Push.Paths {
			if strings.HasPrefix(path, strings.TrimSuffix(pattern, "/*")) {
				return true
			}
			if matched, _ := filepath.Match(pattern, path); matched {
				return true
			}
		}
	}
	return false
}

// startScheduler 启动定时调度
func (m *Manager) startScheduler(ctx context.Context) {
	// 简化的定时实现，实际应使用 cron 库
	ticker := time.NewTicker(1 * time.Hour) // 示例：每小时检查
	defer ticker.Stop()

	for {
		select {
		case <-ctx.Done():
			return
		case <-m.stopCh:
			return
		case <-ticker.C:
			event := &TriggerEvent{
				Type:      TriggerSchedule,
				Timestamp: time.Now(),
				Metadata:  map[string]string{"schedule": m.config.Schedule},
			}
			if err := m.dispatch(ctx, event); err != nil {
				log.Printf("定时触发执行失败: %v", err)
			}
		}
	}
}

// dispatch 分发触发事件
func (m *Manager) dispatch(ctx context.Context, event *TriggerEvent) error {
	m.mu.RLock()
	handlers := m.handlers[event.Type]
	m.mu.RUnlock()

	if len(handlers) == 0 {
		log.Printf("触发类型 %s 无处理函数", event.Type)
		return nil
	}

	var wg sync.WaitGroup
	errCh := make(chan error, len(handlers))

	for _, handler := range handlers {
		wg.Add(1)
		go func(h TriggerFunc) {
			defer wg.Done()
			if err := h(ctx, event); err != nil {
				errCh <- err
			}
		}(handler)
	}

	wg.Wait()
	close(errCh)

	// 收集错误
	var errs []string
	for err := range errCh {
		errs = append(errs, err.Error())
	}

	if len(errs) > 0 {
		return fmt.Errorf("触发执行错误: %s", strings.Join(errs, "; "))
	}

	return nil
}
