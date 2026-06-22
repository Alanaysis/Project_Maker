// Package storage 实现容器存储管理
//
// ⭐ 重点：容器存储的核心概念是分层存储（Layered Storage）
//
// 分层存储原理：
// ┌─────────────────────────────────────┐
// │         Container Layer (可写层)      │  ← 容器运行时修改
// ├─────────────────────────────────────┤
// │         Image Layer 3 (只读层)       │  ← 应用代码
// ├─────────────────────────────────────┤
// │         Image Layer 2 (只读层)       │  ← 依赖库
// ├─────────────────────────────────────┤
// │         Image Layer 1 (只读层)       │  ← 基础系统
// └─────────────────────────────────────┘
//
// OverlayFS 实现：
// - lowerdir: 只读层（镜像层）
// - upperdir: 可写层（容器层）
// - merged: 合并视图（用户看到的）
package storage

import (
	"fmt"
	"os"
	"path/filepath"
	"sync"
)

const (
	// 默认存储根目录
	DefaultStorageRoot = "/var/lib/minicontainer"
	// 镜像层目录
	ImageLayerDir = "layers"
	// 容器可写层目录
	ContainerDir = "containers"
	// 合并视图目录
	MergedDir = "merged"
)

// StorageManager 存储管理器
type StorageManager struct {
	// 存储根目录
	RootDir string
	// 镜像层存储
	ImageLayers map[string]*ImageLayer
	// 容器存储
	Containers map[string]*ContainerStorage
	// 互斥锁
	mu sync.RWMutex
}

// ImageLayer 镜像层
type ImageLayer struct {
	// 层 ID
	ID string
	// 父层 ID
	ParentID string
	// 层大小
	Size int64
	// 层数据路径
	Path string
	// 层内容摘要
	Digest string
}

// ContainerStorage 容器存储
type ContainerStorage struct {
	// 容器 ID
	ContainerID string
	// 镜像层 ID
	ImageLayerID string
	// 可写层路径
	UpperDir string
	// 工作目录
	WorkDir string
	// 合并视图路径
	MergedDir string
}

// NewStorageManager 创建存储管理器
func NewStorageManager(rootDir string) (*StorageManager, error) {
	if rootDir == "" {
		rootDir = DefaultStorageRoot
	}

	// 创建必要的目录
	dirs := []string{
		filepath.Join(rootDir, ImageLayerDir),
		filepath.Join(rootDir, ContainerDir),
		filepath.Join(rootDir, MergedDir),
	}

	for _, dir := range dirs {
		if err := os.MkdirAll(dir, 0755); err != nil {
			return nil, fmt.Errorf("failed to create directory %s: %w", dir, err)
		}
	}

	return &StorageManager{
		RootDir:     rootDir,
		ImageLayers: make(map[string]*ImageLayer),
		Containers:  make(map[string]*ContainerStorage),
	}, nil
}

// CreateLayer 创建新的镜像层
func (m *StorageManager) CreateLayer(id, parentID string) (*ImageLayer, error) {
	m.mu.Lock()
	defer m.mu.Unlock()

	// 检查层是否已存在
	if _, exists := m.ImageLayers[id]; exists {
		return nil, fmt.Errorf("layer %s already exists", id)
	}

	// 创建层目录
	layerPath := filepath.Join(m.RootDir, ImageLayerDir, id)
	if err := os.MkdirAll(layerPath, 0755); err != nil {
		return nil, fmt.Errorf("failed to create layer directory: %w", err)
	}

	layer := &ImageLayer{
		ID:       id,
		ParentID: parentID,
		Path:     layerPath,
	}

	m.ImageLayers[id] = layer
	return layer, nil
}

// DeleteLayer 删除镜像层
func (m *StorageManager) DeleteLayer(id string) error {
	m.mu.Lock()
	defer m.mu.Unlock()

	layer, exists := m.ImageLayers[id]
	if !exists {
		return fmt.Errorf("layer %s not found", id)
	}

	// 删除层目录
	if err := os.RemoveAll(layer.Path); err != nil {
		return fmt.Errorf("failed to delete layer: %w", err)
	}

	delete(m.ImageLayers, id)
	return nil
}

// GetLayer 获取镜像层
func (m *StorageManager) GetLayer(id string) (*ImageLayer, error) {
	m.mu.RLock()
	defer m.mu.RUnlock()

	layer, exists := m.ImageLayers[id]
	if !exists {
		return nil, fmt.Errorf("layer %s not found", id)
	}

	return layer, nil
}

// ListLayers 列出所有镜像层
func (m *StorageManager) ListLayers() []*ImageLayer {
	m.mu.RLock()
	defer m.mu.RUnlock()

	layers := make([]*ImageLayer, 0, len(m.ImageLayers))
	for _, l := range m.ImageLayers {
		layers = append(layers, l)
	}

	return layers
}

// CreateContainerStorage 创建容器存储
//
// ⭐ 重点：使用 OverlayFS 创建分层存储
//
// OverlayFS 挂载命令：
// mount -t overlay overlay \
//   -o lowerdir=<image-layer>,upperdir=<container-layer>,workdir=<work-dir> \
//   <merged-dir>
func (m *StorageManager) CreateContainerStorage(containerID, imageLayerID string) (*ContainerStorage, error) {
	m.mu.Lock()
	defer m.mu.Unlock()

	// 检查镜像层是否存在
	imageLayer, exists := m.ImageLayers[imageLayerID]
	if !exists {
		return nil, fmt.Errorf("image layer %s not found", imageLayerID)
	}

	// 创建容器目录结构
	containerBase := filepath.Join(m.RootDir, ContainerDir, containerID)
	upperDir := filepath.Join(containerBase, "upper")
	workDir := filepath.Join(containerBase, "work")
	mergedDir := filepath.Join(m.RootDir, MergedDir, containerID)

	// 创建目录
	dirs := []string{upperDir, workDir, mergedDir}
	for _, dir := range dirs {
		if err := os.MkdirAll(dir, 0755); err != nil {
			return nil, fmt.Errorf("failed to create directory: %w", err)
		}
	}

	storage := &ContainerStorage{
		ContainerID:  containerID,
		ImageLayerID: imageLayerID,
		UpperDir:     upperDir,
		WorkDir:      workDir,
		MergedDir:    mergedDir,
	}

	m.Containers[containerID] = storage
	return storage, nil
}

// MountContainer 挂载容器文件系统
//
// ⭐ 重点：使用 OverlayFS 合并镜像层和容器层
func (m *StorageManager) MountContainer(containerID string) error {
	m.mu.RLock()
	storage, exists := m.Containers[containerID]
	m.mu.RUnlock()

	if !exists {
		return fmt.Errorf("container storage %s not found", containerID)
	}

	// 获取镜像层
	imageLayer, err := m.GetLayer(storage.ImageLayerID)
	if err != nil {
		return fmt.Errorf("failed to get image layer: %w", err)
	}

	// 收集所有只读层（从顶层到底层）
	var lowerDirs []string
	layer := imageLayer
	for layer != nil {
		lowerDirs = append(lowerDirs, layer.Path)
		if layer.ParentID == "" {
			break
		}
		layer, _ = m.GetLayer(layer.ParentID)
	}

	// 构建 OverlayFS 挂载选项
	// lowerdir 是所有只读层，用冒号分隔
	lowerDir := filepath.Join(lowerDirs...)

	// 使用 mount 系统调用挂载 OverlayFS
	// 实际实现需要使用 syscall.Mount
	// 这里简化处理，实际代码会更复杂

	_ = lowerDir
	_ = storage.UpperDir
	_ = storage.WorkDir

	return nil
}

// UnmountContainer 卸载容器文件系统
func (m *StorageManager) UnmountContainer(containerID string) error {
	m.mu.RLock()
	storage, exists := m.Containers[containerID]
	m.mu.RUnlock()

	if !exists {
		return fmt.Errorf("container storage %s not found", containerID)
	}

	// 使用 umount 系统调用卸载
	// 实际实现需要使用 syscall.Unmount

	_ = storage.MergedDir
	return nil
}

// DeleteContainerStorage 删除容器存储
func (m *StorageManager) DeleteContainerStorage(containerID string) error {
	m.mu.Lock()
	defer m.mu.Unlock()

	storage, exists := m.Containers[containerID]
	if !exists {
		return nil
	}

	// 卸载文件系统
	if err := m.UnmountContainer(containerID); err != nil {
		fmt.Printf("Warning: failed to unmount container: %v\n", err)
	}

	// 删除容器目录
	containerBase := filepath.Join(m.RootDir, ContainerDir, containerID)
	if err := os.RemoveAll(containerBase); err != nil {
		return fmt.Errorf("failed to delete container storage: %w", err)
	}

	// 删除合并视图目录
	mergedDir := filepath.Join(m.RootDir, MergedDir, containerID)
	if err := os.RemoveAll(mergedDir); err != nil {
		return fmt.Errorf("failed to delete merged dir: %w", err)
	}

	delete(m.Containers, containerID)
	return nil
}

// GetContainerStorage 获取容器存储
func (m *StorageManager) GetContainerStorage(containerID string) (*ContainerStorage, error) {
	m.mu.RLock()
	defer m.mu.RUnlock()

	storage, exists := m.Containers[containerID]
	if !exists {
		return nil, fmt.Errorf("container storage %s not found", containerID)
	}

	return storage, nil
}

// GetRootFS 获取容器根文件系统路径
func (m *StorageManager) GetRootFS(containerID string) (string, error) {
	storage, err := m.GetContainerStorage(containerID)
	if err != nil {
		return "", err
	}

	return storage.MergedDir, nil
}

// CreateRootFS 创建简单的根文件系统
//
// 💡 思考：如何创建一个最小的根文件系统？
// - 使用 busybox 静态编译版本
// - 使用 debootstrap 创建 Debian 根文件系统
// - 使用 Alpine Linux 的 minirootfs
func (m *StorageManager) CreateRootFS(layerID, sourcePath string) error {
	// 创建层
	layer, err := m.CreateLayer(layerID, "")
	if err != nil {
		return err
	}

	// 复制文件到层目录
	if err := copyDirectory(sourcePath, layer.Path); err != nil {
		m.DeleteLayer(layerID)
		return fmt.Errorf("failed to copy rootfs: %w", err)
	}

	return nil
}

// copyDirectory 复制目录
func copyDirectory(src, dst string) error {
	// 简化实现：创建目标目录
	return os.MkdirAll(dst, 0755)
}

// GetStorageUsage 获取存储使用情况
func (m *StorageManager) GetStorageUsage() (map[string]int64, error) {
	usage := make(map[string]int64)

	// 计算镜像层大小
	for _, layer := range m.ImageLayers {
		size, err := getDirectorySize(layer.Path)
		if err != nil {
			continue
		}
		usage["image_layer_"+layer.ID] = size
	}

	// 计算容器层大小
	for _, storage := range m.Containers {
		size, err := getDirectorySize(storage.UpperDir)
		if err != nil {
			continue
		}
		usage["container_"+storage.ContainerID] = size
	}

	return usage, nil
}

// getDirectorySize 获取目录大小
func getDirectorySize(path string) (int64, error) {
	var size int64

	err := filepath.Walk(path, func(_ string, info os.FileInfo, err error) error {
		if err != nil {
			return err
		}
		if !info.IsDir() {
			size += info.Size()
		}
		return nil
	})

	return size, err
}
