// Package container - Cgroups 资源限制实现
//
// ⭐ 重点：Cgroups (Control Groups) 是 Linux 内核提供的资源限制机制
//
// Cgroups v2 (统一层级) 目录结构：
// /sys/fs/cgroup/
// ├── minicontainer/
// │   ├── <container-id>/
// │   │   ├── cpu.max        # CPU 限制
// │   │   ├── memory.max     # 内存限制
// │   │   ├── pids.max       # 进程数限制
// │   │   ├── io.max         # I/O 限制
// │   │   └── cgroup.procs   # 进程列表
// │   └── ...
// └── ...
package container

import (
	"fmt"
	"os"
	"path/filepath"
	"strconv"
	"strings"
)

// CgroupBasePath cgroups v2 根路径
const CgroupBasePath = "/sys/fs/cgroup"

// CgroupManager cgroup 管理器
type CgroupManager struct {
	// cgroup 路径
	Path string
	// 容器 ID
	ContainerID string
}

// NewCgroupManager 创建 cgroup 管理器
func NewCgroupManager(containerID string) *CgroupManager {
	return &CgroupManager{
		Path:        filepath.Join(CgroupBasePath, "minicontainer", containerID),
		ContainerID: containerID,
	}
}

// setupCgroup 设置容器的 cgroup
//
// ⭐ 重点：这是资源限制的核心实现
func setupCgroup(containerID string, resources *ResourceLimit) error {
	if resources == nil {
		return nil
	}

	mgr := NewCgroupManager(containerID)

	// 创建 cgroup 目录
	if err := os.MkdirAll(mgr.Path, 0755); err != nil {
		return fmt.Errorf("failed to create cgroup: %w", err)
	}

	// 设置内存限制
	if resources.MemoryLimit > 0 {
		if err := mgr.SetMemoryLimit(resources.MemoryLimit); err != nil {
			return fmt.Errorf("failed to set memory limit: %w", err)
		}
	}

	// 设置 CPU 限制
	if resources.CPUPercent > 0 {
		if err := mgr.SetCPULimit(resources.CPUPercent); err != nil {
			return fmt.Errorf("failed to set CPU limit: %w", err)
		}
	}

	// 设置 CPU shares
	if resources.CPUShares > 0 {
		if err := mgr.SetCPUShares(resources.CPUShares); err != nil {
			return fmt.Errorf("failed to set CPU shares: %w", err)
		}
	}

	// 设置进程数限制
	if resources.PidsLimit > 0 {
		if err := mgr.SetPidsLimit(resources.PidsLimit); err != nil {
			return fmt.Errorf("failed to set pids limit: %w", err)
		}
	}

	// 设置 I/O 限制
	if resources.IOReadBps > 0 {
		if err := mgr.SetIOReadBps(resources.IOReadBps); err != nil {
			return fmt.Errorf("failed to set IO read limit: %w", err)
		}
	}

	if resources.IOWriteBps > 0 {
		if err := mgr.SetIOWriteBps(resources.IOWriteBps); err != nil {
			return fmt.Errorf("failed to set IO write limit: %w", err)
		}
	}

	return nil
}

// cleanupCgroup 清理容器的 cgroup
func cleanupCgroup(containerID string) error {
	mgr := NewCgroupManager(containerID)
	return os.RemoveAll(mgr.Path)
}

// SetMemoryLimit 设置内存限制
//
// 💡 思考：内存限制的单位是什么？
// - memory.max 接受字节数
// - 可以使用 "256M", "1G" 等格式（但在写入时需要转换为字节）
func (m *CgroupManager) SetMemoryLimit(limit int64) error {
	// 设置内存最大值
	memoryMaxPath := filepath.Join(m.Path, "memory.max")
	if err := os.WriteFile(memoryMaxPath, []byte(strconv.FormatInt(limit, 10)), 0644); err != nil {
		return fmt.Errorf("failed to write memory.max: %w", err)
	}

	// 设置内存软限制（90% 的硬限制）
	softLimit := int64(float64(limit) * 0.9)
	memoryHighPath := filepath.Join(m.Path, "memory.high")
	if err := os.WriteFile(memoryHighPath, []byte(strconv.FormatInt(softLimit, 10)), 0644); err != nil {
		// memory.high 可能不存在，忽略错误
		fmt.Printf("Warning: failed to set memory.high: %v\n", err)
	}

	// 启用 swap 限制（与内存限制相同，即禁止使用 swap）
	swapMaxPath := filepath.Join(m.Path, "memory.swap.max")
	if err := os.WriteFile(swapMaxPath, []byte("0"), 0644); err != nil {
		// memory.swap.max 可能不存在，忽略错误
		fmt.Printf("Warning: failed to set memory.swap.max: %v\n", err)
	}

	return nil
}

// SetCPULimit 设置 CPU 限制（使用 CFS 配额）
//
// ⭐ 重点：CPU 限制使用 CFS (Completely Fair Scheduler) 配额
//
// cpu.max 格式：$MAX $PERIOD
// - $MAX: 在 $PERIOD 时间内可以使用的 CPU 时间（微秒）
// - $PERIOD: 时间周期（微秒）
//
// 例如：50% CPU 限制 = "50000 100000"
func (m *CgroupManager) SetCPULimit(percent int) error {
	if percent < 0 || percent > 100 {
		return fmt.Errorf("CPU percent must be between 0 and 100")
	}

	// 计算 CFS 配额
	period := 100000 // 100ms 周期
	quota := period * percent / 100

	// 格式化为 "quota period"
	cpuMax := fmt.Sprintf("%d %d", quota, period)

	cpuMaxPath := filepath.Join(m.Path, "cpu.max")
	if err := os.WriteFile(cpuMaxPath, []byte(cpuMax), 0644); err != nil {
		return fmt.Errorf("failed to write cpu.max: %w", err)
	}

	return nil
}

// SetCPUShares 设置 CPU shares（相对权重）
//
// 💡 思考：shares 和 quota 的区别是什么？
// - shares: 相对权重，当系统繁忙时按比例分配 CPU
// - quota: 绝对限制，无论系统是否繁忙都限制 CPU 使用
func (m *CgroupManager) SetCPUShares(shares int) error {
	// Cgroups v2 使用 cpu.weight（范围 1-10000）
	// 将 shares（0-1024）映射到 weight（1-10000）
	weight := shares * 10000 / 1024
	if weight < 1 {
		weight = 1
	}

	cpuWeightPath := filepath.Join(m.Path, "cpu.weight")
	if err := os.WriteFile(cpuWeightPath, []byte(strconv.Itoa(weight)), 0644); err != nil {
		return fmt.Errorf("failed to write cpu.weight: %w", err)
	}

	return nil
}

// SetPidsLimit 设置进程数限制
//
// 💡 思考：为什么要限制进程数？
// - 防止 fork 炸弹
// - 防止资源耗尽
func (m *CgroupManager) SetPidsLimit(limit int) error {
	pidsMaxPath := filepath.Join(m.Path, "pids.max")
	if err := os.WriteFile(pidsMaxPath, []byte(strconv.Itoa(limit)), 0644); err != nil {
		return fmt.Errorf("failed to write pids.max: %w", err)
	}

	return nil
}

// SetIOReadBps 设置 I/O 读取限制（字节/秒）
func (m *CgroupManager) SetIOReadBps(bps int64) error {
	// io.max 格式：MAJOR:MINOR rbps=VALUE wbps=VALUE
	// 这里假设使用 /dev/sda (8:0)
	ioMaxPath := filepath.Join(m.Path, "io.max")
	value := fmt.Sprintf("8:0 rbps=%d", bps)
	if err := os.WriteFile(ioMaxPath, []byte(value), 0644); err != nil {
		return fmt.Errorf("failed to write io.max: %w", err)
	}

	return nil
}

// SetIOWriteBps 设置 I/O 写入限制（字节/秒）
func (m *CgroupManager) SetIOWriteBps(bps int64) error {
	ioMaxPath := filepath.Join(m.Path, "io.max")
	value := fmt.Sprintf("8:0 wbps=%d", bps)
	if err := os.WriteFile(ioMaxPath, []byte(value), 0644); err != nil {
		return fmt.Errorf("failed to write io.max: %w", err)
	}

	return nil
}

// AddProcess 将进程添加到 cgroup
func (m *CgroupManager) AddProcess(pid int) error {
	procsPath := filepath.Join(m.Path, "cgroup.procs")
	if err := os.WriteFile(procsPath, []byte(strconv.Itoa(pid)), 0644); err != nil {
		return fmt.Errorf("failed to add process to cgroup: %w", err)
	}

	return nil
}

// GetMemoryUsage 获取当前内存使用量
func (m *CgroupManager) GetMemoryUsage() (int64, error) {
	memoryCurrentPath := filepath.Join(m.Path, "memory.current")
	data, err := os.ReadFile(memoryCurrentPath)
	if err != nil {
		return 0, fmt.Errorf("failed to read memory.current: %w", err)
	}

	usage, err := strconv.ParseInt(strings.TrimSpace(string(data)), 10, 64)
	if err != nil {
		return 0, fmt.Errorf("failed to parse memory usage: %w", err)
	}

	return usage, nil
}

// GetCPUUsage 获取 CPU 使用统计
func (m *CgroupManager) GetCPUUsage() (map[string]string, error) {
	cpuStatPath := filepath.Join(m.Path, "cpu.stat")
	data, err := os.ReadFile(cpuStatPath)
	if err != nil {
		return nil, fmt.Errorf("failed to read cpu.stat: %w", err)
	}

	stats := make(map[string]string)
	lines := strings.Split(string(data), "\n")
	for _, line := range lines {
		parts := strings.SplitN(line, " ", 2)
		if len(parts) == 2 {
			stats[parts[0]] = parts[1]
		}
	}

	return stats, nil
}

// GetPidsCount 获取当前进程数
func (m *CgroupManager) GetPidsCount() (int, error) {
	pidsCurrentPath := filepath.Join(m.Path, "pids.current")
	data, err := os.ReadFile(pidsCurrentPath)
	if err != nil {
		return 0, fmt.Errorf("failed to read pids.current: %w", err)
	}

	count, err := strconv.Atoi(strings.TrimSpace(string(data)))
	if err != nil {
		return 0, fmt.Errorf("failed to parse pids count: %w", err)
	}

	return count, nil
}

// IsSupported 检查 cgroups v2 是否可用
func IsCgroupSupported() bool {
	// 检查 cgroup 目录是否存在
	_, err := os.Stat(CgroupBasePath)
	if err != nil {
		return false
	}

	// 检查是否是 cgroups v2
	controllersPath := filepath.Join(CgroupBasePath, "cgroup.controllers")
	_, err = os.ReadFile(controllersPath)
	return err == nil
}

// GetAvailableControllers 获取可用的 cgroup 控制器
func GetAvailableControllers() ([]string, error) {
	controllersPath := filepath.Join(CgroupBasePath, "cgroup.controllers")
	data, err := os.ReadFile(controllersPath)
	if err != nil {
		return nil, fmt.Errorf("failed to read cgroup.controllers: %w", err)
	}

	controllers := strings.Fields(string(data))
	return controllers, nil
}
