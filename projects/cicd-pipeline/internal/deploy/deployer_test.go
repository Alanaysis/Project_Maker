package deploy

import (
	"context"
	"testing"
)

func TestNewDeployer(t *testing.T) {
	d := NewDeployer()
	if d == nil {
		t.Fatal("NewDeployer 返回 nil")
	}
	if d.environments == nil {
		t.Fatal("environments 未初始化")
	}
}

func TestRegisterEnvironment(t *testing.T) {
	d := NewDeployer()

	env := &Environment{
		Name:    "staging",
		URL:     "https://staging.example.com",
		Region:  "us-east-1",
		Status:  "active",
		Version: "v1.0.0",
	}

	d.RegisterEnvironment(env)

	got, err := d.GetEnvironment("staging")
	if err != nil {
		t.Fatalf("GetEnvironment 失败: %v", err)
	}

	if got.Name != env.Name {
		t.Errorf("Name = %s, want %s", got.Name, env.Name)
	}
	if got.URL != env.URL {
		t.Errorf("URL = %s, want %s", got.URL, env.URL)
	}
}

func TestGetEnvironmentNotFound(t *testing.T) {
	d := NewDeployer()

	_, err := d.GetEnvironment("nonexistent")
	if err == nil {
		t.Error("期望返回错误，但未返回")
	}
}

func TestDeployRolling(t *testing.T) {
	d := NewDeployer()
	d.RegisterEnvironment(&Environment{
		Name:    "test",
		URL:     "https://test.example.com",
		Version: "v1.0.0",
	})

	ctx := context.Background()
	deployment, err := d.Deploy(ctx, "test", "v1.1.0", StrategyRolling)
	if err != nil {
		t.Fatalf("Deploy 失败: %v", err)
	}

	if deployment.Status != StatusSuccess {
		t.Errorf("Status = %s, want %s", deployment.Status, StatusSuccess)
	}

	// 检查环境版本已更新
	env, _ := d.GetEnvironment("test")
	if env.Version != "v1.1.0" {
		t.Errorf("Version = %s, want %s", env.Version, "v1.1.0")
	}
}

func TestDeployBlueGreen(t *testing.T) {
	d := NewDeployer()
	d.RegisterEnvironment(&Environment{
		Name:    "prod",
		URL:     "https://prod.example.com",
		Version: "v1.0.0",
	})

	ctx := context.Background()
	deployment, err := d.Deploy(ctx, "prod", "v2.0.0", StrategyBlueGreen)
	if err != nil {
		t.Fatalf("Deploy 失败: %v", err)
	}

	if deployment.Status != StatusSuccess {
		t.Errorf("Status = %s, want %s", deployment.Status, StatusSuccess)
	}
}

func TestDeployCanary(t *testing.T) {
	d := NewDeployer()
	d.RegisterEnvironment(&Environment{
		Name:    "prod",
		URL:     "https://prod.example.com",
		Version: "v1.0.0",
	})

	ctx := context.Background()
	deployment, err := d.Deploy(ctx, "prod", "v2.0.0", StrategyCanary)
	if err != nil {
		t.Fatalf("Deploy 失败: %v", err)
	}

	if deployment.Status != StatusSuccess {
		t.Errorf("Status = %s, want %s", deployment.Status, StatusSuccess)
	}
}

func TestDeployEnvironmentNotFound(t *testing.T) {
	d := NewDeployer()

	ctx := context.Background()
	_, err := d.Deploy(ctx, "nonexistent", "v1.0.0", StrategyRolling)
	if err == nil {
		t.Error("期望返回错误，但未返回")
	}
}

func TestRollback(t *testing.T) {
	d := NewDeployer()
	d.RegisterEnvironment(&Environment{
		Name:    "test",
		URL:     "https://test.example.com",
		Version: "v1.0.0",
	})

	ctx := context.Background()

	// 第一次部署
	d.Deploy(ctx, "test", "v1.1.0", StrategyRolling)

	// 第二次部署
	d.Deploy(ctx, "test", "v1.2.0", StrategyRolling)

	// 回滚
	deployment, err := d.Rollback(ctx, "test")
	if err != nil {
		t.Fatalf("Rollback 失败: %v", err)
	}

	if deployment.Status != StatusRolledBack {
		t.Errorf("Status = %s, want %s", deployment.Status, StatusRolledBack)
	}

	// 检查版本已回滚
	env, _ := d.GetEnvironment("test")
	if env.Version != "v1.1.0" {
		t.Errorf("Version = %s, want %s", env.Version, "v1.1.0")
	}
}

func TestRollbackNoVersion(t *testing.T) {
	d := NewDeployer()
	d.RegisterEnvironment(&Environment{
		Name:    "test",
		URL:     "https://test.example.com",
		Version: "v1.0.0",
	})

	ctx := context.Background()

	// 没有历史版本，回滚应失败
	_, err := d.Rollback(ctx, "test")
	if err == nil {
		t.Error("期望返回错误，但未返回")
	}
}

func TestGetDeploymentHistory(t *testing.T) {
	d := NewDeployer()
	d.RegisterEnvironment(&Environment{
		Name:    "test",
		URL:     "https://test.example.com",
		Version: "v1.0.0",
	})

	ctx := context.Background()

	// 执行多次部署
	d.Deploy(ctx, "test", "v1.1.0", StrategyRolling)
	d.Deploy(ctx, "test", "v1.2.0", StrategyRolling)
	d.Deploy(ctx, "test", "v1.3.0", StrategyRolling)

	history := d.GetDeploymentHistory("test", 2)
	if len(history) != 2 {
		t.Errorf("历史记录数 = %d, want %d", len(history), 2)
	}
}

func TestListEnvironments(t *testing.T) {
	d := NewDeployer()
	d.RegisterEnvironment(&Environment{Name: "dev"})
	d.RegisterEnvironment(&Environment{Name: "staging"})
	d.RegisterEnvironment(&Environment{Name: "prod"})

	envs := d.ListEnvironments()
	if len(envs) != 3 {
		t.Errorf("环境数 = %d, want %d", len(envs), 3)
	}
}
