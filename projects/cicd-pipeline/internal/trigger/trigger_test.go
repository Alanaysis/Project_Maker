package trigger

import (
	"context"
	"testing"
)

func TestNewManager(t *testing.T) {
	config := &TriggerConfig{
		Manual: true,
	}

	m := NewManager(config)
	if m == nil {
		t.Fatal("NewManager 返回 nil")
	}
}

func TestManualTrigger(t *testing.T) {
	config := &TriggerConfig{
		Manual: true,
	}

	m := NewManager(config)

	called := false
	m.RegisterHandler(TriggerManual, func(ctx context.Context, event *TriggerEvent) error {
		called = true
		return nil
	})

	ctx := context.Background()
	err := m.TriggerManual(ctx, map[string]string{"test": "value"})
	if err != nil {
		t.Fatalf("TriggerManual 失败: %v", err)
	}

	if !called {
		t.Error("处理函数未被调用")
	}
}

func TestManualTriggerDisabled(t *testing.T) {
	config := &TriggerConfig{
		Manual: false,
	}

	m := NewManager(config)

	ctx := context.Background()
	err := m.TriggerManual(ctx, nil)
	if err == nil {
		t.Error("期望返回错误，但未返回")
	}
}

func TestPushTrigger(t *testing.T) {
	config := &TriggerConfig{
		Push: &PushConfig{
			Branches: []string{"main", "develop"},
		},
	}

	m := NewManager(config)

	called := false
	m.RegisterHandler(TriggerPush, func(ctx context.Context, event *TriggerEvent) error {
		called = true
		if event.Branch != "main" {
			t.Errorf("Branch = %s, want %s", event.Branch, "main")
		}
		return nil
	})

	ctx := context.Background()
	err := m.TriggerPush(ctx, "main", "abc123", "testuser", "test commit", []string{"main.go"})
	if err != nil {
		t.Fatalf("TriggerPush 失败: %v", err)
	}

	if !called {
		t.Error("处理函数未被调用")
	}
}

func TestPushTriggerBranchNotMatch(t *testing.T) {
	config := &TriggerConfig{
		Push: &PushConfig{
			Branches: []string{"main"},
		},
	}

	m := NewManager(config)

	ctx := context.Background()
	err := m.TriggerPush(ctx, "feature/test", "abc123", "testuser", "test commit", nil)
	if err == nil {
		t.Error("期望返回错误，但未返回")
	}
}

func TestPushTriggerNoConfig(t *testing.T) {
	config := &TriggerConfig{}

	m := NewManager(config)

	ctx := context.Background()
	err := m.TriggerPush(ctx, "main", "abc123", "testuser", "test commit", nil)
	if err == nil {
		t.Error("期望返回错误，但未返回")
	}
}

func TestPushTriggerPathFilter(t *testing.T) {
	config := &TriggerConfig{
		Push: &PushConfig{
			Branches: []string{"main"},
			Paths:    []string{"src/*", "docs/*"},
		},
	}

	m := NewManager(config)

	called := false
	m.RegisterHandler(TriggerPush, func(ctx context.Context, event *TriggerEvent) error {
		called = true
		return nil
	})

	ctx := context.Background()

	// 匹配路径
	err := m.TriggerPush(ctx, "main", "abc123", "testuser", "test commit", []string{"src/main.go"})
	if err != nil {
		t.Fatalf("TriggerPush 失败: %v", err)
	}

	if !called {
		t.Error("处理函数未被调用")
	}

	// 不匹配路径
	called = false
	err = m.TriggerPush(ctx, "main", "abc123", "testuser", "test commit", []string{"README.md"})
	if err == nil {
		t.Error("期望返回错误，但未返回")
	}
}

func TestPushTriggerWildcardBranch(t *testing.T) {
	config := &TriggerConfig{
		Push: &PushConfig{
			Branches: []string{"*"},
		},
	}

	m := NewManager(config)

	called := false
	m.RegisterHandler(TriggerPush, func(ctx context.Context, event *TriggerEvent) error {
		called = true
		return nil
	})

	ctx := context.Background()
	err := m.TriggerPush(ctx, "any-branch", "abc123", "testuser", "test commit", nil)
	if err != nil {
		t.Fatalf("TriggerPush 失败: %v", err)
	}

	if !called {
		t.Error("处理函数未被调用")
	}
}

func TestRegisterMultipleHandlers(t *testing.T) {
	config := &TriggerConfig{
		Manual: true,
	}

	m := NewManager(config)

	callCount := 0
	m.RegisterHandler(TriggerManual, func(ctx context.Context, event *TriggerEvent) error {
		callCount++
		return nil
	})
	m.RegisterHandler(TriggerManual, func(ctx context.Context, event *TriggerEvent) error {
		callCount++
		return nil
	})

	ctx := context.Background()
	m.TriggerManual(ctx, nil)

	if callCount != 2 {
		t.Errorf("callCount = %d, want %d", callCount, 2)
	}
}

func TestStartStop(t *testing.T) {
	config := &TriggerConfig{
		Manual: true,
	}

	m := NewManager(config)
	ctx := context.Background()

	err := m.Start(ctx)
	if err != nil {
		t.Fatalf("Start 失败: %v", err)
	}

	// 重复启动应失败
	err = m.Start(ctx)
	if err == nil {
		t.Error("期望返回错误，但未返回")
	}

	m.Stop()

	// 停止后应可再次启动
	err = m.Start(ctx)
	if err != nil {
		t.Fatalf("Start 失败: %v", err)
	}

	m.Stop()
}
