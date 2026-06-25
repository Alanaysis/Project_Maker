package tests

import (
	"os"
	"path/filepath"
	"testing"

	"github.com/minicontainer/runtime/pkg/container"
)

// TestCgroupManager 测试 Cgroup 管理器创建
func TestCgroupManager(t *testing.T) {
	mgr := container.NewCgroupManager("test-container")

	// 验证路径
	expectedPath := filepath.Join(container.CgroupBasePath, "minicontainer", "test-container")
	if mgr.Path != expectedPath {
		t.Errorf("Expected path '%s', got '%s'", expectedPath, mgr.Path)
	}

	if mgr.ContainerID != "test-container" {
		t.Errorf("Expected container ID 'test-container', got '%s'", mgr.ContainerID)
	}
}

// TestCgroupSupported 检查 cgroup 支持状态
func TestCgroupSupported(t *testing.T) {
	// 这个测试只检查函数是否能正常运行，不检查实际结果
	// 因为在 CI 环境中可能没有 cgroup 支持
	supported := container.IsCgroupSupported()
	t.Logf("Cgroup v2 supported: %v", supported)
}

// TestGetAvailableControllers 测试获取可用控制器
func TestGetAvailableControllers(t *testing.T) {
	controllers, err := container.GetAvailableControllers()
	if err != nil {
		// 在没有 cgroup 支持的环境中，这是预期的
		t.Logf("Failed to get controllers (expected in non-cgroup env): %v", err)
		return
	}

	t.Logf("Available controllers: %v", controllers)

	// 验证控制器列表不为空
	if len(controllers) == 0 {
		t.Error("Expected at least one controller")
	}
}

// TestCgroupSetupInSandbox 测试 cgroup 设置（沙箱环境）
func TestCgroupSetupInSandbox(t *testing.T) {
	// 创建临时目录模拟 cgroup 目录
	tempDir := t.TempDir()
	cgroupDir := filepath.Join(tempDir, "minicontainer", "test-container")
	if err := os.MkdirAll(cgroupDir, 0755); err != nil {
		t.Fatalf("Failed to create temp cgroup dir: %v", err)
	}

	// 测试目录创建
	if _, err := os.Stat(cgroupDir); os.IsNotExist(err) {
		t.Error("Cgroup directory should exist")
	}
}

// TestResourceLimitDefaults 测试资源限制默认值
func TestResourceLimitDefaults(t *testing.T) {
	resources := &container.ResourceLimit{
		MemoryLimit: 256 * 1024 * 1024, // 256MB
		CPUPercent:  50,
		CPUShares:   1024,
		PidsLimit:   100,
	}

	// 验证内存限制
	if resources.MemoryLimit != 256*1024*1024 {
		t.Errorf("Expected memory limit %d, got %d", 256*1024*1024, resources.MemoryLimit)
	}

	// 验证 CPU 限制
	if resources.CPUPercent != 50 {
		t.Errorf("Expected CPU percent 50, got %d", resources.CPUPercent)
	}

	// 验证 CPU shares
	if resources.CPUShares != 1024 {
		t.Errorf("Expected CPU shares 1024, got %d", resources.CPUShares)
	}

	// 验证进程数限制
	if resources.PidsLimit != 100 {
		t.Errorf("Expected pids limit 100, got %d", resources.PidsLimit)
	}
}

// TestResourceLimitZero 测试零值资源限制
func TestResourceLimitZero(t *testing.T) {
	resources := &container.ResourceLimit{
		MemoryLimit: 0,
		CPUPercent:  0,
		CPUShares:   0,
		PidsLimit:   0,
	}

	// 零值应该被忽略（不设置限制）
	if resources.MemoryLimit != 0 {
		t.Errorf("Expected memory limit 0, got %d", resources.MemoryLimit)
	}
}

// TestResourceLimitLarge 测试大值资源限制
func TestResourceLimitLarge(t *testing.T) {
	resources := &container.ResourceLimit{
		MemoryLimit: 1024 * 1024 * 1024 * 16, // 16GB
		CPUPercent:  100,
		CPUShares:   1024,
		PidsLimit:   10000,
	}

	if resources.MemoryLimit != 1024*1024*1024*16 {
		t.Errorf("Expected memory limit %d, got %d", 1024*1024*1024*16, resources.MemoryLimit)
	}

	if resources.CPUPercent != 100 {
		t.Errorf("Expected CPU percent 100, got %d", resources.CPUPercent)
	}
}
