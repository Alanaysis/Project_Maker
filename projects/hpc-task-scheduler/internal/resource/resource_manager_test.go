package resource

import (
	"testing"

	"github.com/hpc-scheduler/internal/config"
	"github.com/hpc-scheduler/pkg/models"
)

func TestAllocate(t *testing.T) {
	cfg := config.ResourceConfig{
		TotalCPU:      8,
		TotalMemoryMB: 16384,
	}
	rm := NewResourceManager(cfg)

	req := models.ResourceRequest{
		CPU:      2,
		MemoryMB: 1024,
	}

	err := rm.Allocate("task1", req)
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}

	// 检查资源已分配
	used := rm.GetUsed()
	if used.CPU != 2 {
		t.Errorf("expected CPU 2, got %d", used.CPU)
	}
	if used.MemoryMB != 1024 {
		t.Errorf("expected Memory 1024, got %d", used.MemoryMB)
	}
}

func TestAllocateInsufficientCPU(t *testing.T) {
	cfg := config.ResourceConfig{
		TotalCPU:      4,
		TotalMemoryMB: 16384,
	}
	rm := NewResourceManager(cfg)

	// 分配所有 CPU
	req1 := models.ResourceRequest{CPU: 4, MemoryMB: 1024}
	rm.Allocate("task1", req1)

	// 尝试分配更多 CPU
	req2 := models.ResourceRequest{CPU: 1, MemoryMB: 512}
	err := rm.Allocate("task2", req2)
	if err == nil {
		t.Error("expected error for insufficient CPU")
	}
}

func TestAllocateInsufficientMemory(t *testing.T) {
	cfg := config.ResourceConfig{
		TotalCPU:      8,
		TotalMemoryMB: 2048,
	}
	rm := NewResourceManager(cfg)

	// 分配所有内存
	req1 := models.ResourceRequest{CPU: 2, MemoryMB: 2048}
	rm.Allocate("task1", req1)

	// 尝试分配更多内存
	req2 := models.ResourceRequest{CPU: 1, MemoryMB: 512}
	err := rm.Allocate("task2", req2)
	if err == nil {
		t.Error("expected error for insufficient memory")
	}
}

func TestRelease(t *testing.T) {
	cfg := config.ResourceConfig{
		TotalCPU:      8,
		TotalMemoryMB: 16384,
	}
	rm := NewResourceManager(cfg)

	req := models.ResourceRequest{CPU: 4, MemoryMB: 4096}
	rm.Allocate("task1", req)

	// 释放资源
	err := rm.Release("task1")
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}

	used := rm.GetUsed()
	if used.CPU != 0 {
		t.Errorf("expected CPU 0, got %d", used.CPU)
	}
	if used.MemoryMB != 0 {
		t.Errorf("expected Memory 0, got %d", used.MemoryMB)
	}
}

func TestReleaseNonexistent(t *testing.T) {
	cfg := config.ResourceConfig{
		TotalCPU:      8,
		TotalMemoryMB: 16384,
	}
	rm := NewResourceManager(cfg)

	err := rm.Release("nonexistent")
	if err == nil {
		t.Error("expected error for nonexistent allocation")
	}
}

func TestCheckAvailable(t *testing.T) {
	cfg := config.ResourceConfig{
		TotalCPU:      8,
		TotalMemoryMB: 16384,
	}
	rm := NewResourceManager(cfg)

	// 应该有足够资源
	req := models.ResourceRequest{CPU: 4, MemoryMB: 8192}
	if !rm.CheckAvailable(req) {
		t.Error("expected resources to be available")
	}

	// 分配一些资源
	rm.Allocate("task1", models.ResourceRequest{CPU: 6, MemoryMB: 12288})

	// 现在应该不够了
	if rm.CheckAvailable(req) {
		t.Error("expected resources to be unavailable")
	}
}

func TestGetAvailable(t *testing.T) {
	cfg := config.ResourceConfig{
		TotalCPU:      8,
		TotalMemoryMB: 16384,
	}
	rm := NewResourceManager(cfg)

	rm.Allocate("task1", models.ResourceRequest{CPU: 3, MemoryMB: 4096})

	avail := rm.GetAvailable()
	if avail.CPU != 5 {
		t.Errorf("expected CPU 5, got %d", avail.CPU)
	}
	if avail.MemoryMB != 12288 {
		t.Errorf("expected Memory 12288, got %d", avail.MemoryMB)
	}
}

func TestGetClusterInfo(t *testing.T) {
	cfg := config.ResourceConfig{
		TotalCPU:      8,
		TotalMemoryMB: 16384,
	}
	rm := NewResourceManager(cfg)

	info := rm.GetClusterInfo()
	if info.TotalNodes != 1 {
		t.Errorf("expected 1 node, got %d", info.TotalNodes)
	}
	if info.TotalResources.CPU != 8 {
		t.Errorf("expected CPU 8, got %d", info.TotalResources.CPU)
	}
}

func TestMultipleAllocations(t *testing.T) {
	cfg := config.ResourceConfig{
		TotalCPU:      8,
		TotalMemoryMB: 16384,
	}
	rm := NewResourceManager(cfg)

	// 多次分配
	tasks := []struct {
		id  string
		req models.ResourceRequest
	}{
		{"task1", models.ResourceRequest{CPU: 2, MemoryMB: 2048}},
		{"task2", models.ResourceRequest{CPU: 3, MemoryMB: 4096}},
		{"task3", models.ResourceRequest{CPU: 1, MemoryMB: 1024}},
	}

	for _, t := range tasks {
		err := rm.Allocate(t.id, t.req)
		if err != nil {
			t.Fatalf("unexpected error allocating %s: %v", t.id, err)
		}
	}

	used := rm.GetUsed()
	if used.CPU != 6 {
		t.Errorf("expected CPU 6, got %d", used.CPU)
	}
	if used.MemoryMB != 7168 {
		t.Errorf("expected Memory 7168, got %d", used.MemoryMB)
	}

	// 释放一个
	rm.Release("task2")

	used = rm.GetUsed()
	if used.CPU != 3 {
		t.Errorf("expected CPU 3 after release, got %d", used.CPU)
	}
}
