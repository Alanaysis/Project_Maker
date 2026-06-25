// Package container 实现容器的核心创建和管理逻辑
//
// 这个包是容器运行时的核心，负责：
// 1. 容器的创建、启动、停止、删除
// 2. 容器状态管理
// 3. 容器生命周期管理
package container

import (
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"sync"
	"syscall"
	"time"
)

// ContainerStatus 容器状态
type ContainerStatus int

const (
	StatusCreated ContainerStatus = iota
	StatusRunning
	StatusStopped
	StatusPaused
	StatusError
)

func (s ContainerStatus) String() string {
	switch s {
	case StatusCreated:
		return "created"
	case StatusRunning:
		return "running"
	case StatusStopped:
		return "stopped"
	case StatusPaused:
		return "paused"
	case StatusError:
		return "error"
	default:
		return "unknown"
	}
}

// ContainerConfig 容器配置
type ContainerConfig struct {
	// 容器名称
	Name string `json:"name"`
	// 容器 ID（自动生成）
	ID string `json:"id"`
	// 要执行的命令
	Command []string `json:"command"`
	// 镜像名称
	Image string `json:"image"`
	// 根文件系统路径
	RootFS string `json:"rootfs"`
	// Namespace 配置
	Namespaces []string `json:"namespaces"`
	// 资源限制
	Resources *ResourceLimit `json:"resources"`
	// 环境变量
	Env []string `json:"env"`
	// 工作目录
	WorkDir string `json:"workdir"`
	// 主机名
	Hostname string `json:"hostname"`
	// 是否以特权模式运行
	Privileged bool `json:"privileged"`
	// 挂载点
	Mounts []Mount `json:"mounts"`
}

// ResourceLimit 资源限制配置
type ResourceLimit struct {
	// 内存限制（字节）
	MemoryLimit int64 `json:"memory_limit"`
	// CPU 配额（百分比，0-100）
	CPUPercent int `json:"cpu_percent"`
	// CPU shares（相对权重）
	CPUShares int `json:"cpu_shares"`
	// 进程数限制
	PidsLimit int `json:"pids_limit"`
	// I/O 读取限制（字节/秒）
	IOReadBps int64 `json:"io_read_bps"`
	// I/O 写入限制（字节/秒）
	IOWriteBps int64 `json:"io_write_bps"`
}

// Mount 挂载点配置
type Mount struct {
	Source      string   `json:"source"`
	Destination string   `json:"destination"`
	Type        string   `json:"type"`
	Options     []string `json:"options"`
}

// Container 容器实例
type Container struct {
	// 容器配置
	Config *ContainerConfig
	// 容器状态
	Status ContainerStatus
	// 容器进程 PID
	PID int
	// 创建时间
	CreatedAt time.Time
	// 启动时间
	StartedAt time.Time
	// 停止时间
	StoppedAt time.Time
	// 容器根目录
	RootDir string
	// 进程句柄
	cmd *exec.Cmd
	// 互斥锁
	mu sync.RWMutex
	// 退出码
	ExitCode int
	// 确保 Wait() 只调用一次
	waitOnce sync.Once
	// Wait() 完成时关闭的 channel
	done chan struct{}
}

// ContainerManager 容器管理器
type ContainerManager struct {
	// 容器存储根目录
	RootDir string
	// 所有容器
	containers map[string]*Container
	// 互斥锁
	mu sync.RWMutex
}

// NewContainerManager 创建容器管理器
func NewContainerManager(rootDir string) (*ContainerManager, error) {
	// 确保根目录存在
	if err := os.MkdirAll(rootDir, 0755); err != nil {
		return nil, fmt.Errorf("failed to create root directory: %w", err)
	}

	mgr := &ContainerManager{
		RootDir:    rootDir,
		containers: make(map[string]*Container),
	}

	// 从磁盘恢复容器状态
	mgr.loadContainers()

	return mgr, nil
}

// loadContainers 从磁盘加载容器配置
func (m *ContainerManager) loadContainers() {
	entries, err := os.ReadDir(m.RootDir)
	if err != nil {
		return
	}

	for _, entry := range entries {
		if !entry.IsDir() {
			continue
		}

		containerDir := filepath.Join(m.RootDir, entry.Name())
		configPath := filepath.Join(containerDir, "config.json")

		var config ContainerConfig
		if err := readJSON(configPath, &config); err != nil {
			continue
		}

		container := &Container{
			Config:  &config,
			Status:  StatusStopped, // 从磁盘加载的容器默认为已停止
			RootDir: containerDir,
			done:    make(chan struct{}),
		}

		// 检查容器进程是否仍在运行
		if config.ID != "" {
			container.Status = StatusStopped
		}

		m.containers[config.ID] = container
	}
}

// Create 创建新容器
func (m *ContainerManager) Create(config *ContainerConfig) (*Container, error) {
	m.mu.Lock()
	defer m.mu.Unlock()

	// 生成容器 ID
	if config.ID == "" {
		config.ID = generateID()
	}

	// 检查名称是否已存在
	if config.Name != "" {
		for _, c := range m.containers {
			if c.Config.Name == config.Name {
				return nil, fmt.Errorf("container with name %s already exists", config.Name)
			}
		}
	}

	// 设置默认值
	if config.Hostname == "" {
		if len(config.ID) >= 12 {
			config.Hostname = config.ID[:12]
		} else {
			config.Hostname = config.ID
		}
	}
	if config.Namespaces == nil {
		config.Namespaces = []string{"pid", "mount", "uts", "ipc", "net"}
	}
	if config.Resources == nil {
		config.Resources = &ResourceLimit{
			MemoryLimit: 256 * 1024 * 1024, // 256MB 默认
			CPUPercent:  50,
			CPUShares:   1024,
			PidsLimit:   100,
		}
	}

	// 创建容器目录
	containerDir := filepath.Join(m.RootDir, config.ID)
	if err := os.MkdirAll(containerDir, 0755); err != nil {
		return nil, fmt.Errorf("failed to create container directory: %w", err)
	}

	// 创建容器实例
	container := &Container{
		Config:    config,
		Status:    StatusCreated,
		CreatedAt: time.Now(),
		RootDir:   containerDir,
		done:      make(chan struct{}),
	}

	// 保存容器配置
	if err := container.saveConfig(); err != nil {
		os.RemoveAll(containerDir)
		return nil, fmt.Errorf("failed to save container config: %w", err)
	}

	m.containers[config.ID] = container
	return container, nil
}

// Start 启动容器
//
// ⭐ 重点：容器启动的核心流程
// 1. 创建 cgroup 并设置资源限制
// 2. 使用 clone() 创建新进程，同时创建新的 namespace
// 3. 子进程进入 "child" 命令分支，设置文件系统隔离
// 4. 父进程将子进程 PID 加入 cgroup
// 5. 父进程异步等待子进程退出
func (m *ContainerManager) Start(id string) error {
	m.mu.RLock()
	container, exists := m.containers[id]
	m.mu.RUnlock()

	if !exists {
		return fmt.Errorf("container %s not found", id)
	}

	container.mu.Lock()
	defer container.mu.Unlock()

	if container.Status == StatusRunning {
		return fmt.Errorf("container %s is already running", id)
	}

	// 创建 cgroup 并设置资源限制
	if err := setupCgroup(container.Config.ID, container.Config.Resources); err != nil {
		return fmt.Errorf("failed to setup cgroup: %w", err)
	}

	// 准备 namespace 配置
	nsFlags := GetNamespaceFlags(container.Config.Namespaces)

	// ⭐ 构建启动命令
	// 使用 /proc/self/exe 重新执行自己，进入 "child" 子命令
	// 这样新进程会在新的 namespace 中执行
	args := []string{"child", "--id", container.Config.ID}
	args = append(args, container.Config.Command...)

	cmd := exec.Command("/proc/self/exe", args...)
	cmd.SysProcAttr = &syscall.SysProcAttr{
		Cloneflags: nsFlags,
	}

	// 设置环境变量
	cmd.Env = container.Config.Env
	if cmd.Env == nil {
		cmd.Env = os.Environ()
	}

	// 设置标准输入输出
	cmd.Stdin = os.Stdin
	cmd.Stdout = os.Stdout
	cmd.Stderr = os.Stderr

	// 保存命令引用
	container.cmd = cmd
	// 初始化 done channel
	container.done = make(chan struct{})

	// 启动进程
	if err := cmd.Start(); err != nil {
		return fmt.Errorf("failed to start container: %w", err)
	}

	container.PID = cmd.Process.Pid
	container.Status = StatusRunning
	container.StartedAt = time.Now()

	// ⭐ 将容器进程加入 cgroup（关键步骤！）
	cgroupMgr := NewCgroupManager(container.Config.ID)
	if err := cgroupMgr.AddProcess(container.PID); err != nil {
		// 非致命错误，记录警告
		fmt.Printf("Warning: failed to add process to cgroup: %v\n", err)
	}

	// 异步等待容器退出
	go func() {
		container.waitOnce.Do(func() {
			err := cmd.Wait()
			container.mu.Lock()
			defer container.mu.Unlock()

			if err != nil {
				if exitErr, ok := err.(*exec.ExitError); ok {
					container.ExitCode = exitErr.ExitCode()
				}
			}

			container.Status = StatusStopped
			container.StoppedAt = time.Now()

			// 清理 cgroup
			cleanupCgroup(container.Config.ID)
		})
		close(container.done)
	}()

	return nil
}

// Stop 停止容器
func (m *ContainerManager) Stop(id string) error {
	m.mu.RLock()
	container, exists := m.containers[id]
	m.mu.RUnlock()

	if !exists {
		return fmt.Errorf("container %s not found", id)
	}

	container.mu.Lock()
	defer container.mu.Unlock()

	if container.Status != StatusRunning {
		return fmt.Errorf("container %s is not running", id)
	}

	// 发送 SIGTERM 信号
	if err := container.cmd.Process.Signal(syscall.SIGTERM); err != nil {
		// 如果 SIGTERM 失败，使用 SIGKILL
		if err := container.cmd.Process.Signal(syscall.SIGKILL); err != nil {
			return fmt.Errorf("failed to kill container: %w", err)
		}
	}

	// 等待容器退出（最多 10 秒）
	select {
	case <-container.done:
		// 容器已退出
	case <-time.After(10 * time.Second):
		// 超时，强制杀死
		container.cmd.Process.Signal(syscall.SIGKILL)
		<-container.done
	}

	return nil
}

// Delete 删除容器
func (m *ContainerManager) Delete(id string) error {
	m.mu.Lock()
	defer m.mu.Unlock()

	container, exists := m.containers[id]
	if !exists {
		return fmt.Errorf("container %s not found", id)
	}

	container.mu.RLock()
	status := container.Status
	container.mu.RUnlock()

	if status == StatusRunning {
		return fmt.Errorf("cannot delete running container %s", id)
	}

	// 删除容器目录
	if err := os.RemoveAll(container.RootDir); err != nil {
		return fmt.Errorf("failed to remove container directory: %w", err)
	}

	delete(m.containers, id)
	return nil
}

// Get 获取容器信息
func (m *ContainerManager) Get(id string) (*Container, error) {
	m.mu.RLock()
	defer m.mu.RUnlock()

	// 先按 ID 查找
	if container, exists := m.containers[id]; exists {
		return container, nil
	}

	// 按名称查找
	for _, container := range m.containers {
		if container.Config.Name == id {
			return container, nil
		}
	}

	return nil, fmt.Errorf("container %s not found", id)
}

// List 列出所有容器
func (m *ContainerManager) List() []*Container {
	m.mu.RLock()
	defer m.mu.RUnlock()

	containers := make([]*Container, 0, len(m.containers))
	for _, c := range m.containers {
		containers = append(containers, c)
	}

	return containers
}

// saveConfig 保存容器配置到文件
func (c *Container) saveConfig() error {
	configPath := filepath.Join(c.RootDir, "config.json")
	return writeJSON(configPath, c.Config)
}

// generateID 生成唯一容器 ID
func generateID() string {
	return fmt.Sprintf("%x", time.Now().UnixNano())
}
