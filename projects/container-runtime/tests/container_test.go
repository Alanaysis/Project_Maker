package tests

import (
	"os"
	"path/filepath"
	"testing"

	"github.com/minicontainer/runtime/pkg/container"
	"github.com/minicontainer/runtime/pkg/storage"
)

// TestContainerManager 测试容器管理器
func TestContainerManager(t *testing.T) {
	// 创建临时目录
	tempDir := t.TempDir()
	containerDir := filepath.Join(tempDir, "containers")

	// 创建容器管理器
	mgr, err := container.NewContainerManager(containerDir)
	if err != nil {
		t.Fatalf("Failed to create container manager: %v", err)
	}

	// 测试创建容器
	config := &container.ContainerConfig{
		Name:    "test-container",
		Image:   "alpine",
		Command: []string{"/bin/sh"},
	}

	cont, err := mgr.Create(config)
	if err != nil {
		t.Fatalf("Failed to create container: %v", err)
	}

	// 验证容器状态
	if cont.Status != container.StatusCreated {
		t.Errorf("Expected status %v, got %v", container.StatusCreated, cont.Status)
	}

	// 验证容器 ID
	if cont.Config.ID == "" {
		t.Error("Container ID should not be empty")
	}

	// 验证容器名称
	if cont.Config.Name != "test-container" {
		t.Errorf("Expected name 'test-container', got '%s'", cont.Config.Name)
	}

	// 测试获取容器
	getCont, err := mgr.Get(cont.Config.ID)
	if err != nil {
		t.Fatalf("Failed to get container: %v", err)
	}

	if getCont.Config.ID != cont.Config.ID {
		t.Errorf("Expected ID '%s', got '%s'", cont.Config.ID, getCont.Config.ID)
	}

	// 测试按名称获取容器
	getCont, err = mgr.Get("test-container")
	if err != nil {
		t.Fatalf("Failed to get container by name: %v", err)
	}

	if getCont.Config.Name != "test-container" {
		t.Errorf("Expected name 'test-container', got '%s'", getCont.Config.Name)
	}

	// 测试列出容器
	containers := mgr.List()
	if len(containers) != 1 {
		t.Errorf("Expected 1 container, got %d", len(containers))
	}

	// 测试删除容器
	if err := mgr.Delete(cont.Config.ID); err != nil {
		t.Fatalf("Failed to delete container: %v", err)
	}

	// 验证容器已删除
	containers = mgr.List()
	if len(containers) != 0 {
		t.Errorf("Expected 0 containers, got %d", len(containers))
	}
}

// TestContainerConfig 测试容器配置
func TestContainerConfig(t *testing.T) {
	config := &container.ContainerConfig{
		Name:      "test",
		Image:     "alpine",
		Command:   []string{"/bin/sh", "-c", "echo hello"},
		Env:       []string{"PATH=/usr/bin"},
		WorkDir:   "/tmp",
		Hostname:  "test-host",
		Namespaces: []string{"pid", "mount", "uts", "ipc", "net"},
	}

	// 验证配置
	if config.Name != "test" {
		t.Errorf("Expected name 'test', got '%s'", config.Name)
	}

	if config.Image != "alpine" {
		t.Errorf("Expected image 'alpine', got '%s'", config.Image)
	}

	if len(config.Command) != 3 {
		t.Errorf("Expected 3 command args, got %d", len(config.Command))
	}

	if config.Hostname != "test-host" {
		t.Errorf("Expected hostname 'test-host', got '%s'", config.Hostname)
	}

	if len(config.Namespaces) != 5 {
		t.Errorf("Expected 5 namespaces, got %d", len(config.Namespaces))
	}
}

// TestResourceLimit 测试资源限制
func TestResourceLimit(t *testing.T) {
	resources := &container.ResourceLimit{
		MemoryLimit: 256 * 1024 * 1024, // 256MB
		CPUPercent:  50,
		CPUShares:   1024,
		PidsLimit:   100,
	}

	// 验证资源限制
	if resources.MemoryLimit != 256*1024*1024 {
		t.Errorf("Expected memory limit %d, got %d", 256*1024*1024, resources.MemoryLimit)
	}

	if resources.CPUPercent != 50 {
		t.Errorf("Expected CPU percent 50, got %d", resources.CPUPercent)
	}
}

// TestContainerStatus 测试容器状态
func TestContainerStatus(t *testing.T) {
	tests := []struct {
		status   container.ContainerStatus
		expected string
	}{
		{container.StatusCreated, "created"},
		{container.StatusRunning, "running"},
		{container.StatusStopped, "stopped"},
		{container.StatusPaused, "paused"},
		{container.StatusError, "error"},
	}

	for _, test := range tests {
		if test.status.String() != test.expected {
			t.Errorf("Expected status '%s', got '%s'", test.expected, test.status.String())
		}
	}
}

// TestStorageManager 测试存储管理器
func TestStorageManager(t *testing.T) {
	// 创建临时目录
	tempDir := t.TempDir()

	// 创建存储管理器
	mgr, err := storage.NewStorageManager(tempDir)
	if err != nil {
		t.Fatalf("Failed to create storage manager: %v", err)
	}

	// 测试创建层
	layer, err := mgr.CreateLayer("test-layer", "")
	if err != nil {
		t.Fatalf("Failed to create layer: %v", err)
	}

	// 验证层
	if layer.ID != "test-layer" {
		t.Errorf("Expected layer ID 'test-layer', got '%s'", layer.ID)
	}

	// 测试获取层
	getLayer, err := mgr.GetLayer("test-layer")
	if err != nil {
		t.Fatalf("Failed to get layer: %v", err)
	}

	if getLayer.ID != "test-layer" {
		t.Errorf("Expected layer ID 'test-layer', got '%s'", getLayer.ID)
	}

	// 测试列出层
	layers := mgr.ListLayers()
	if len(layers) != 1 {
		t.Errorf("Expected 1 layer, got %d", len(layers))
	}

	// 测试删除层
	if err := mgr.DeleteLayer("test-layer"); err != nil {
		t.Fatalf("Failed to delete layer: %v", err)
	}

	// 验证层已删除
	layers = mgr.ListLayers()
	if len(layers) != 0 {
		t.Errorf("Expected 0 layers, got %d", len(layers))
	}
}

// TestContainerStorage 测试容器存储
func TestContainerStorage(t *testing.T) {
	// 创建临时目录
	tempDir := t.TempDir()

	// 创建存储管理器
	mgr, err := storage.NewStorageManager(tempDir)
	if err != nil {
		t.Fatalf("Failed to create storage manager: %v", err)
	}

	// 创建镜像层
	_, err = mgr.CreateLayer("image-layer", "")
	if err != nil {
		t.Fatalf("Failed to create image layer: %v", err)
	}

	// 创建容器存储
	containerStorage, err := mgr.CreateContainerStorage("container-1", "image-layer")
	if err != nil {
		t.Fatalf("Failed to create container storage: %v", err)
	}

	// 验证容器存储
	if containerStorage.ContainerID != "container-1" {
		t.Errorf("Expected container ID 'container-1', got '%s'", containerStorage.ContainerID)
	}

	// 验证目录存在
	if _, err := os.Stat(containerStorage.UpperDir); os.IsNotExist(err) {
		t.Error("UpperDir should exist")
	}

	if _, err := os.Stat(containerStorage.WorkDir); os.IsNotExist(err) {
		t.Error("WorkDir should exist")
	}

	if _, err := os.Stat(containerStorage.MergedDir); os.IsNotExist(err) {
		t.Error("MergedDir should exist")
	}

	// 测试获取根文件系统
	rootFS, err := mgr.GetRootFS("container-1")
	if err != nil {
		t.Fatalf("Failed to get rootfs: %v", err)
	}

	if rootFS != containerStorage.MergedDir {
		t.Errorf("Expected rootfs '%s', got '%s'", containerStorage.MergedDir, rootFS)
	}

	// 测试删除容器存储
	if err := mgr.DeleteContainerStorage("container-1"); err != nil {
		t.Fatalf("Failed to delete container storage: %v", err)
	}
}

// TestMount 测试挂载点配置
func TestMount(t *testing.T) {
	mount := container.Mount{
		Source:      "/host/path",
		Destination: "/container/path",
		Type:        "bind",
		Options:     []string{"ro"},
	}

	if mount.Source != "/host/path" {
		t.Errorf("Expected source '/host/path', got '%s'", mount.Source)
	}

	if mount.Destination != "/container/path" {
		t.Errorf("Expected destination '/container/path', got '%s'", mount.Destination)
	}

	if mount.Type != "bind" {
		t.Errorf("Expected type 'bind', got '%s'", mount.Type)
	}
}

// TestContainerCreateDuplicateName 测试创建重复名称的容器
func TestContainerCreateDuplicateName(t *testing.T) {
	tempDir := t.TempDir()
	containerDir := filepath.Join(tempDir, "containers")

	mgr, err := container.NewContainerManager(containerDir)
	if err != nil {
		t.Fatalf("Failed to create container manager: %v", err)
	}

	// 创建第一个容器
	config1 := &container.ContainerConfig{
		Name:  "duplicate-name",
		Image: "alpine",
	}

	_, err = mgr.Create(config1)
	if err != nil {
		t.Fatalf("Failed to create first container: %v", err)
	}

	// 创建同名容器应该失败
	config2 := &container.ContainerConfig{
		Name:  "duplicate-name",
		Image: "ubuntu",
	}

	_, err = mgr.Create(config2)
	if err == nil {
		t.Error("Expected error when creating container with duplicate name")
	}
}

// TestContainerDeleteRunning 测试删除运行中的容器
func TestContainerDeleteRunning(t *testing.T) {
	tempDir := t.TempDir()
	containerDir := filepath.Join(tempDir, "containers")

	mgr, err := container.NewContainerManager(containerDir)
	if err != nil {
		t.Fatalf("Failed to create container manager: %v", err)
	}

	// 创建容器
	config := &container.ContainerConfig{
		Name:  "running-container",
		Image: "alpine",
	}

	cont, err := mgr.Create(config)
	if err != nil {
		t.Fatalf("Failed to create container: %v", err)
	}

	// 手动设置状态为运行中
	cont.Status = container.StatusRunning

	// 删除运行中的容器应该失败
	err = mgr.Delete(cont.Config.ID)
	if err == nil {
		t.Error("Expected error when deleting running container")
	}
}

// TestContainerGetNotFound 测试获取不存在的容器
func TestContainerGetNotFound(t *testing.T) {
	tempDir := t.TempDir()
	containerDir := filepath.Join(tempDir, "containers")

	mgr, err := container.NewContainerManager(containerDir)
	if err != nil {
		t.Fatalf("Failed to create container manager: %v", err)
	}

	_, err = mgr.Get("nonexistent")
	if err == nil {
		t.Error("Expected error when getting nonexistent container")
	}
}

// TestNamespaceFlags 测试命名空间标志
func TestNamespaceFlags(t *testing.T) {
	// 测试所有命名空间
	allNs := []string{"pid", "mount", "uts", "ipc", "net"}
	flags := container.GetNamespaceFlags(allNs)

	// 验证标志不为零
	if flags == 0 {
		t.Error("Expected non-zero flags for all namespaces")
	}
}

// TestContainerDefaults 测试容器默认值
func TestContainerDefaults(t *testing.T) {
	tempDir := t.TempDir()
	containerDir := filepath.Join(tempDir, "containers")

	mgr, err := container.NewContainerManager(containerDir)
	if err != nil {
		t.Fatalf("Failed to create container manager: %v", err)
	}

	// 创建容器（不设置默认值）
	config := &container.ContainerConfig{
		Image:   "alpine",
		Command: []string{"/bin/sh"},
	}

	cont, err := mgr.Create(config)
	if err != nil {
		t.Fatalf("Failed to create container: %v", err)
	}

	// 验证默认值已设置
	if cont.Config.Hostname == "" {
		t.Error("Expected hostname to be set")
	}

	if cont.Config.Namespaces == nil {
		t.Error("Expected namespaces to be set")
	}

	if cont.Config.Resources == nil {
		t.Error("Expected resources to be set")
	}

	// 验证默认资源限制
	if cont.Config.Resources.MemoryLimit != 256*1024*1024 {
		t.Errorf("Expected default memory limit 256MB, got %d", cont.Config.Resources.MemoryLimit)
	}
}
