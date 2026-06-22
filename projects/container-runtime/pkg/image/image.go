// Package image 实现容器镜像管理
//
// ⭐ 重点：OCI 镜像规范
//
// OCI 镜像格式：
// - manifest.json: 镜像清单
// - config.json: 镜像配置
// - layer.tar.gz: 镜像层（tar 格式）
//
// 镜像分层：
// ┌─────────────────────────────────────┐
// │           Manifest                  │
// │  ┌─────────────────────────────┐    │
// │  │     Config                  │    │
// │  │  - OS, Architecture         │    │
// │  │  - Entrypoint, Cmd         │    │
// │  │  - Env, Labels             │    │
// │  └─────────────────────────────┘    │
// │  ┌─────────────────────────────┐    │
// │  │     Layers                 │    │
// │  │  - sha256:abc123...        │    │
// │  │  - sha256:def456...        │    │
// │  └─────────────────────────────┘    │
// └─────────────────────────────────────┘
package image

import (
	"archive/tar"
	"compress/gzip"
	"encoding/json"
	"fmt"
	"io"
	"os"
	"path/filepath"
	"strings"
)

const (
	// 默认镜像存储目录
	DefaultImageDir = "/var/lib/minicontainer/images"
	// OCI 镜像媒体类型
	MediaTypeManifest = "application/vnd.oci.image.manifest.v1+json"
	MediaTypeConfig   = "application/vnd.oci.image.config.v1+json"
	MediaTypeLayer    = "application/vnd.oci.image.layer.v1.tar+gzip"
)

// Image 镜像
type Image struct {
	// 镜像 ID
	ID string `json:"id"`
	// 镜像名称
	Name string `json:"name"`
	// 镜像标签
	Tag string `json:"tag"`
	// 镜像摘要
	Digest string `json:"digest"`
	// 镜像大小
	Size int64 `json:"size"`
	// 创建时间
	CreatedAt string `json:"created_at"`
	// 镜像配置
	Config *ImageConfig `json:"config"`
	// 镜像层
	Layers []string `json:"layers"`
}

// ImageConfig 镜像配置
type ImageConfig struct {
	// 操作系统
	OS string `json:"os"`
	// 架构
	Architecture string `json:"architecture"`
	// 入口点
	Entrypoint []string `json:"entrypoint"`
	// 默认命令
	Cmd []string `json:"cmd"`
	// 环境变量
	Env []string `json:"env"`
	// 工作目录
	WorkDir string `json:"workdir"`
	// 标签
	Labels map[string]string `json:"labels"`
}

// Manifest 镜像清单
type Manifest struct {
	// 媒体类型
	MediaType string `json:"mediaType"`
	// 配置摘要
	Config Descriptor `json:"config"`
	// 层摘要列表
	Layers []Descriptor `json:"layers"`
	// 架构
	Architecture string `json:"architecture"`
	// 操作系统
	OS string `json:"os"`
}

// Descriptor 描述符
type Descriptor struct {
	// 媒体类型
	MediaType string `json:"mediaType"`
	// 大小
	Size int64 `json:"size"`
	// 摘要
	Digest string `json:"digest"`
}

// ImageManager 镜像管理器
type ImageManager struct {
	// 镜像存储目录
	ImageDir string
	// 镜像索引
	images map[string]*Image
}

// NewImageManager 创建镜像管理器
func NewImageManager(imageDir string) (*ImageManager, error) {
	if imageDir == "" {
		imageDir = DefaultImageDir
	}

	// 创建镜像目录
	if err := os.MkdirAll(imageDir, 0755); err != nil {
		return nil, fmt.Errorf("failed to create image directory: %w", err)
	}

	mgr := &ImageManager{
		ImageDir: imageDir,
		images:   make(map[string]*Image),
	}

	// 加载已存在的镜像
	if err := mgr.loadImages(); err != nil {
		fmt.Printf("Warning: failed to load images: %v\n", err)
	}

	return mgr, nil
}

// loadImages 加载已存在的镜像
func (m *ImageManager) loadImages() error {
	entries, err := os.ReadDir(m.ImageDir)
	if err != nil {
		return err
	}

	for _, entry := range entries {
		if !entry.IsDir() {
			continue
		}

		imageDir := filepath.Join(m.ImageDir, entry.Name())
		configPath := filepath.Join(imageDir, "config.json")

		data, err := os.ReadFile(configPath)
		if err != nil {
			continue
		}

		var image Image
		if err := json.Unmarshal(data, &image); err != nil {
			continue
		}

		m.images[image.ID] = &image
	}

	return nil
}

// Pull 从仓库拉取镜像
//
// 💡 思考：镜像拉取的过程是什么？
// 1. 解析镜像名称（registry/name:tag）
// 2. 获取认证信息
// 3. 获取镜像清单
// 4. 下载镜像层
// 5. 验证摘要
// 6. 保存到本地存储
func (m *ImageManager) Pull(name string) (*Image, error) {
	// 解析镜像名称
	registry, repo, tag := parseImageName(name)

	// 构建完整的镜像名称
	fullName := fmt.Sprintf("%s/%s:%s", registry, repo, tag)

	// 创建镜像目录
	imageDir := filepath.Join(m.ImageDir, repo)
	if err := os.MkdirAll(imageDir, 0755); err != nil {
		return nil, fmt.Errorf("failed to create image directory: %w", err)
	}

	// 模拟下载（实际实现需要 HTTP 请求）
	image := &Image{
		ID:        fmt.Sprintf("sha256:%x", len(fullName)),
		Name:      repo,
		Tag:       tag,
		Size:      0,
		CreatedAt: "2024-01-01T00:00:00Z",
		Config: &ImageConfig{
			OS:           "linux",
			Architecture: "amd64",
			Entrypoint:   []string{"/bin/sh"},
			Cmd:          []string{},
			Env:          []string{"PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"},
			WorkDir:      "/",
		},
		Layers: []string{},
	}

	// 保存镜像配置
	configPath := filepath.Join(imageDir, "config.json")
	data, err := json.MarshalIndent(image, "", "  ")
	if err != nil {
		return nil, fmt.Errorf("failed to marshal image config: %w", err)
	}

	if err := os.WriteFile(configPath, data, 0644); err != nil {
		return nil, fmt.Errorf("failed to save image config: %w", err)
	}

	m.images[image.ID] = image
	return image, nil
}

// Load 从本地文件加载镜像
func (m *ImageManager) Load(path string) (*Image, error) {
	// 打开 tar 文件
	file, err := os.Open(path)
	if err != nil {
		return nil, fmt.Errorf("failed to open image file: %w", err)
	}
	defer file.Close()

	// 读取 tar 归档
	tarReader := tar.NewReader(file)

	var manifest Manifest
	var config ImageConfig
	var layers []string

	for {
		header, err := tarReader.Next()
		if err == io.EOF {
			break
		}
		if err != nil {
			return nil, fmt.Errorf("failed to read tar: %w", err)
		}

		// 根据文件名处理
		switch header.Name {
		case "manifest.json":
			if err := json.NewDecoder(tarReader).Decode(&manifest); err != nil {
				return nil, fmt.Errorf("failed to decode manifest: %w", err)
			}
		case "config.json":
			if err := json.NewDecoder(tarReader).Decode(&config); err != nil {
				return nil, fmt.Errorf("failed to decode config: %w", err)
			}
		default:
			// 处理层文件
			if strings.HasSuffix(header.Name, "/layer.tar") {
				layerID := strings.TrimSuffix(header.Name, "/layer.tar")
				layerPath := filepath.Join(m.ImageDir, layerID+".tar.gz")

				if err := extractLayer(tarReader, layerPath); err != nil {
					return nil, fmt.Errorf("failed to extract layer: %w", err)
				}

				layers = append(layers, layerID)
			}
		}
	}

	// 创建镜像对象
	image := &Image{
		ID:        manifest.Config.Digest,
		Name:      "loaded",
		Tag:       "latest",
		Config:    &config,
		Layers:    layers,
		CreatedAt: "2024-01-01T00:00:00Z",
	}

	// 保存镜像配置
	imageDir := filepath.Join(m.ImageDir, image.ID)
	if err := os.MkdirAll(imageDir, 0755); err != nil {
		return nil, fmt.Errorf("failed to create image directory: %w", err)
	}

	configPath := filepath.Join(imageDir, "config.json")
	data, err := json.MarshalIndent(image, "", "  ")
	if err != nil {
		return nil, fmt.Errorf("failed to marshal image config: %w", err)
	}

	if err := os.WriteFile(configPath, data, 0644); err != nil {
		return nil, fmt.Errorf("failed to save image config: %w", err)
	}

	m.images[image.ID] = image
	return image, nil
}

// Get 获取镜像
func (m *ImageManager) Get(idOrName string) (*Image, error) {
	// 先按 ID 查找
	if image, exists := m.images[idOrName]; exists {
		return image, nil
	}

	// 按名称查找
	for _, image := range m.images {
		if image.Name == idOrName || image.Name+":"+image.Tag == idOrName {
			return image, nil
		}
	}

	return nil, fmt.Errorf("image %s not found", idOrName)
}

// List 列出所有镜像
func (m *ImageManager) List() []*Image {
	images := make([]*Image, 0, len(m.images))
	for _, img := range m.images {
		images = append(images, img)
	}
	return images
}

// Delete 删除镜像
func (m *ImageManager) Delete(id string) error {
	image, exists := m.images[id]
	if !exists {
		return fmt.Errorf("image %s not found", id)
	}

	// 删除镜像目录
	imageDir := filepath.Join(m.ImageDir, image.Name)
	if err := os.RemoveAll(imageDir); err != nil {
		return fmt.Errorf("failed to delete image: %w", err)
	}

	delete(m.images, id)
	return nil
}

// extractLayer 提取镜像层
func extractLayer(reader io.Reader, destPath string) error {
	// 创建目标文件
	file, err := os.Create(destPath)
	if err != nil {
		return fmt.Errorf("failed to create layer file: %w", err)
	}
	defer file.Close()

	// 使用 gzip 压缩
	gzipWriter := gzip.NewWriter(file)
	defer gzipWriter.Close()

	// 复制数据
	if _, err := io.Copy(gzipWriter, reader); err != nil {
		return fmt.Errorf("failed to write layer: %w", err)
	}

	return nil
}

// parseImageName 解析镜像名称
//
// 💡 思考：镜像名称的格式是什么？
// - registry/repository:tag
// - 例如：docker.io/library/alpine:latest
// - 简写：alpine（默认 docker.io/library/alpine:latest）
func parseImageName(name string) (registry, repo, tag string) {
	// 默认值
	registry = "docker.io"
	repo = name
	tag = "latest"

	// 解析标签
	if idx := strings.LastIndex(name, ":"); idx != -1 {
		tag = name[idx+1:]
		name = name[:idx]
	}

	// 解析仓库
	parts := strings.SplitN(name, "/", 2)
	if len(parts) == 2 {
		// 检查是否是 registry
		if strings.Contains(parts[0], ".") || strings.Contains(parts[0], ":") {
			registry = parts[0]
			repo = parts[1]
		} else {
			repo = name
		}
	}

	return registry, repo, tag
}

// GetImageDir 获取镜像层目录
func (m *ImageManager) GetImageDir(imageID string) (string, error) {
	image, exists := m.images[imageID]
	if !exists {
		return "", fmt.Errorf("image %s not found", imageID)
	}

	return filepath.Join(m.ImageDir, image.Name), nil
}
