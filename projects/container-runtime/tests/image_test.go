package tests

import (
	"path/filepath"
	"testing"

	"github.com/minicontainer/runtime/pkg/image"
)

// TestImageManager 测试镜像管理器
func TestImageManager(t *testing.T) {
	// 创建临时目录
	tempDir := t.TempDir()
	imageDir := filepath.Join(tempDir, "images")

	// 创建镜像管理器
	mgr, err := image.NewImageManager(imageDir)
	if err != nil {
		t.Fatalf("Failed to create image manager: %v", err)
	}

	// 测试拉取镜像
	img, err := mgr.Pull("alpine:latest")
	if err != nil {
		t.Fatalf("Failed to pull image: %v", err)
	}

	// 验证镜像
	if img.Name != "alpine" {
		t.Errorf("Expected image name 'alpine', got '%s'", img.Name)
	}

	if img.Tag != "latest" {
		t.Errorf("Expected tag 'latest', got '%s'", img.Tag)
	}

	// 测试获取镜像
	getImg, err := mgr.Get(img.ID)
	if err != nil {
		t.Fatalf("Failed to get image: %v", err)
	}

	if getImg.ID != img.ID {
		t.Errorf("Expected image ID '%s', got '%s'", img.ID, getImg.ID)
	}

	// 测试按名称获取镜像
	getImg, err = mgr.Get("alpine")
	if err != nil {
		t.Fatalf("Failed to get image by name: %v", err)
	}

	if getImg.Name != "alpine" {
		t.Errorf("Expected image name 'alpine', got '%s'", getImg.Name)
	}

	// 测试列出镜像
	images := mgr.List()
	if len(images) != 1 {
		t.Errorf("Expected 1 image, got %d", len(images))
	}

	// 测试删除镜像
	if err := mgr.Delete(img.ID); err != nil {
		t.Fatalf("Failed to delete image: %v", err)
	}

	// 验证镜像已删除
	images = mgr.List()
	if len(images) != 0 {
		t.Errorf("Expected 0 images, got %d", len(images))
	}
}

// TestImageConfig 测试镜像配置
func TestImageConfig(t *testing.T) {
	config := &image.ImageConfig{
		OS:           "linux",
		Architecture: "amd64",
		Entrypoint:   []string{"/bin/sh"},
		Cmd:          []string{"-c", "echo hello"},
		Env:          []string{"PATH=/usr/bin"},
		WorkDir:      "/tmp",
		Labels: map[string]string{
			"maintainer": "test",
		},
	}

	// 验证配置
	if config.OS != "linux" {
		t.Errorf("Expected OS 'linux', got '%s'", config.OS)
	}

	if config.Architecture != "amd64" {
		t.Errorf("Expected architecture 'amd64', got '%s'", config.Architecture)
	}

	if len(config.Entrypoint) != 1 {
		t.Errorf("Expected 1 entrypoint, got %d", len(config.Entrypoint))
	}

	if config.WorkDir != "/tmp" {
		t.Errorf("Expected workdir '/tmp', got '%s'", config.WorkDir)
	}
}

// TestManifest 测试镜像清单
func TestManifest(t *testing.T) {
	manifest := image.Manifest{
		MediaType: image.MediaTypeManifest,
		Config: image.Descriptor{
			MediaType: image.MediaTypeConfig,
			Size:      1024,
			Digest:    "sha256:abc123",
		},
		Layers: []image.Descriptor{
			{
				MediaType: image.MediaTypeLayer,
				Size:      1024 * 1024,
				Digest:    "sha256:layer1",
			},
		},
		Architecture: "amd64",
		OS:           "linux",
	}

	// 验证清单
	if manifest.MediaType != image.MediaTypeManifest {
		t.Errorf("Expected media type '%s', got '%s'", image.MediaTypeManifest, manifest.MediaType)
	}

	if len(manifest.Layers) != 1 {
		t.Errorf("Expected 1 layer, got %d", len(manifest.Layers))
	}
}
