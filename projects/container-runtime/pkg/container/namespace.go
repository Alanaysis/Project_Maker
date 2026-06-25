// Package container - Namespace 隔离实现
//
// ⭐ 重点：Linux Namespace 是容器隔离的核心技术
//
// Namespace 类型：
// - PID: 进程 ID 隔离，容器内进程从 PID 1 开始
// - Mount: 文件系统挂载点隔离
// - UTS: 主机名和域名隔离
// - IPC: 进程间通信隔离
// - Network: 网络栈隔离
// - User: 用户和组 ID 隔离
// - Cgroup: Cgroup 根目录隔离
package container

import (
	"fmt"
	"os"
	"path/filepath"
	"syscall"
	"unsafe"
)

// Namespace 类型常量
const (
	NamespacePID     = "pid"
	NamespaceMount   = "mount"
	NamespaceUTS     = "uts"
	NamespaceIPC     = "ipc"
	NamespaceNetwork = "net"
	NamespaceUser    = "user"
	NamespaceCgroup  = "cgroup"
)

// Linux 系统调用号（amd64）
const (
	SYS_SETNS      = 308
	SYS_PIVOT_ROOT = 155
)

// Mount 标志
const (
	MS_BIND        = 4096
	MS_REC         = 16384
	MS_PRIVATE     = 1 << 18
	MS_RDONLY      = 1
	MS_NOSUID      = 2
	MS_NODEV       = 4
	MS_STRICTATIME = 1 << 24
	MNT_DETACH     = 2
)

// 设备类型
const (
	S_IFCHR = 0020000
)

// GetNamespaceFlags 将 namespace 名称转换为 clone 系统调用的标志
func GetNamespaceFlags(namespaces []string) uintptr {
	var flags uintptr

	for _, ns := range namespaces {
		switch ns {
		case NamespacePID:
			flags |= syscall.CLONE_NEWPID
		case NamespaceMount:
			flags |= syscall.CLONE_NEWNS
		case NamespaceUTS:
			flags |= syscall.CLONE_NEWUTS
		case NamespaceIPC:
			flags |= syscall.CLONE_NEWIPC
		case NamespaceNetwork:
			flags |= syscall.CLONE_NEWNET
		case NamespaceUser:
			flags |= syscall.CLONE_NEWUSER
		case NamespaceCgroup:
			flags |= syscall.CLONE_NEWCGROUP
		}
	}

	return flags
}

// SetupNamespaces 在容器子进程中设置命名空间
//
// ⭐ 重点：这个函数在容器进程内部执行，设置隔离环境
// 它由 child 命令调用，此时进程已经在新的 namespace 中
func SetupNamespaces(config *ContainerConfig) error {
	// 1. 设置主机名（UTS namespace）
	if contains(config.Namespaces, NamespaceUTS) {
		if err := syscall.Sethostname([]byte(config.Hostname)); err != nil {
			return fmt.Errorf("failed to set hostname: %w", err)
		}
	}

	// 2. 设置 mount namespace
	if contains(config.Namespaces, NamespaceMount) {
		if err := setupMountNamespace(config); err != nil {
			return fmt.Errorf("failed to setup mount namespace: %w", err)
		}
	}

	// 3. 处理用户自定义挂载点
	if err := setupVolumeMounts(config); err != nil {
		return fmt.Errorf("failed to setup volume mounts: %w", err)
	}

	return nil
}

// setupMountNamespace 设置挂载命名空间
//
// ⭐ 重点：这是容器文件系统隔离的关键
//
// 步骤：
// 1. 重新挂载根文件系统为私有，防止挂载传播
// 2. 绑定挂载新的根文件系统
// 3. 挂载 /proc, /sys, /dev
// 4. 创建设备节点
// 5. 使用 pivot_root 切换根文件系统
// 6. 卸载旧的根文件系统
func setupMountNamespace(config *ContainerConfig) error {
	// 获取新的根文件系统路径
	newRoot := config.RootFS
	if newRoot == "" {
		newRoot = filepath.Join("/var/lib/minicontainer/merged", config.ID)
	}

	// 确保新根目录存在
	if err := os.MkdirAll(newRoot, 0755); err != nil {
		return fmt.Errorf("failed to create rootfs: %w", err)
	}

	// 重新挂载根文件系统为私有，防止挂载传播
	if err := mount("", "/", "", MS_PRIVATE|MS_REC, ""); err != nil {
		return fmt.Errorf("failed to make root private: %w", err)
	}

	// 挂载新的根文件系统（绑定挂载）
	if err := mount(newRoot, newRoot, "", MS_BIND|MS_REC, ""); err != nil {
		return fmt.Errorf("failed to bind mount rootfs: %w", err)
	}

	// 创建必要的目录
	dirs := []string{"proc", "sys", "dev", "tmp", "oldroot"}
	for _, dir := range dirs {
		path := filepath.Join(newRoot, dir)
		if err := os.MkdirAll(path, 0755); err != nil {
			return fmt.Errorf("failed to create %s: %w", dir, err)
		}
	}

	// 挂载 /proc（容器内进程信息）
	procPath := filepath.Join(newRoot, "proc")
	if err := mount("proc", procPath, "proc", 0, ""); err != nil {
		return fmt.Errorf("failed to mount proc: %w", err)
	}

	// 挂载 /sys（内核信息）
	sysPath := filepath.Join(newRoot, "sys")
	if err := mount("sysfs", sysPath, "sysfs", MS_RDONLY, ""); err != nil {
		// sysfs 挂载可能失败，忽略
		fmt.Printf("Warning: failed to mount sysfs: %v\n", err)
	}

	// 挂载 /dev（设备文件）
	devPath := filepath.Join(newRoot, "dev")
	if err := mount("tmpfs", devPath, "tmpfs", MS_NOSUID|MS_STRICTATIME, "mode=755"); err != nil {
		return fmt.Errorf("failed to mount dev: %w", err)
	}

	// 创建必要的设备节点
	if err := createDevNodes(devPath); err != nil {
		return fmt.Errorf("failed to create dev nodes: %w", err)
	}

	// 切换根文件系统（pivot_root）
	oldRoot := filepath.Join(newRoot, "oldroot")
	if err := pivotRoot(newRoot, oldRoot); err != nil {
		return fmt.Errorf("failed to pivot_root: %w", err)
	}

	// 切换到新的根目录
	if err := os.Chdir("/"); err != nil {
		return fmt.Errorf("failed to chdir: %w", err)
	}

	// 卸载旧的根文件系统
	if err := unmount("/oldroot", MNT_DETACH); err != nil {
		return fmt.Errorf("failed to unmount oldroot: %w", err)
	}

	// 删除旧根目录
	if err := os.Remove("/oldroot"); err != nil {
		// 忽略错误
	}

	return nil
}

// setupVolumeMounts 设置用户自定义的卷挂载
//
// ⭐ 重点：卷挂载允许容器访问宿主机的目录
// 这是容器持久化存储和数据共享的基础
func setupVolumeMounts(config *ContainerConfig) error {
	for _, m := range config.Mounts {
		// 确保容器内的挂载点存在
		if err := os.MkdirAll(m.Destination, 0755); err != nil {
			return fmt.Errorf("failed to create mount point %s: %w", m.Destination, err)
		}

		// 根据挂载类型处理
		switch m.Type {
		case "bind":
			// 绑定挂载：将宿主机目录挂载到容器内
			flags := uintptr(MS_BIND | MS_REC)
			for _, opt := range m.Options {
				switch opt {
				case "ro":
					flags |= uintptr(MS_RDONLY)
				}
			}
			if err := mount(m.Source, m.Destination, "", flags, ""); err != nil {
				return fmt.Errorf("failed to bind mount %s -> %s: %w",
					m.Source, m.Destination, err)
			}
		case "tmpfs":
			// tmpfs 挂载：内存文件系统
			if err := mount("tmpfs", m.Destination, "tmpfs", uintptr(MS_NOSUID|MS_NODEV), ""); err != nil {
				return fmt.Errorf("failed to mount tmpfs on %s: %w", m.Destination, err)
			}
		default:
			// 默认为绑定挂载
			if err := mount(m.Source, m.Destination, "", uintptr(MS_BIND|MS_REC), ""); err != nil {
				return fmt.Errorf("failed to mount %s -> %s: %w",
					m.Source, m.Destination, err)
			}
		}
	}

	return nil
}

// createDevNodes 创建必要的设备节点
func createDevNodes(devPath string) error {
	devices := []struct {
		name string
		mode uint32
		dev  int
	}{
		{"null", S_IFCHR | 0666, int(mkdev(1, 3))},
		{"zero", S_IFCHR | 0666, int(mkdev(1, 5))},
		{"random", S_IFCHR | 0666, int(mkdev(1, 8))},
		{"urandom", S_IFCHR | 0666, int(mkdev(1, 9))},
		{"tty", S_IFCHR | 0666, int(mkdev(5, 0))},
	}

	for _, d := range devices {
		path := filepath.Join(devPath, d.name)
		if err := syscall.Mknod(path, d.mode, d.dev); err != nil && !os.IsExist(err) {
			return fmt.Errorf("failed to create %s: %w", d.name, err)
		}
	}

	// 创建符号链接
	symlinks := []struct {
		old string
		new string
	}{
		{"/proc/self/fd", filepath.Join(devPath, "fd")},
		{"/proc/self/fd/0", filepath.Join(devPath, "stdin")},
		{"/proc/self/fd/1", filepath.Join(devPath, "stdout")},
		{"/proc/self/fd/2", filepath.Join(devPath, "stderr")},
	}

	for _, s := range symlinks {
		if err := os.Symlink(s.old, s.new); err != nil && !os.IsExist(err) {
			return fmt.Errorf("failed to create symlink %s: %w", s.new, err)
		}
	}

	return nil
}

// JoinNamespace 加入已存在的命名空间
//
// ⭐ 重点：这是 exec 命令的核心机制
// 通过 setns() 加入容器的 namespace，然后在容器环境中执行命令
func JoinNamespace(pid int, namespace string) error {
	nsPath := fmt.Sprintf("/proc/%d/ns/%s", pid, namespace)

	// 打开 namespace 文件
	nsFile, err := os.Open(nsPath)
	if err != nil {
		return fmt.Errorf("failed to open namespace: %w", err)
	}
	defer nsFile.Close()

	// 使用 setns 系统调用加入命名空间
	if err := setns(int(nsFile.Fd()), getNamespaceType(namespace)); err != nil {
		return fmt.Errorf("failed to join namespace: %w", err)
	}

	return nil
}

// getNamespaceType 获取 namespace 类型标志
func getNamespaceType(namespace string) int {
	switch namespace {
	case NamespacePID:
		return syscall.CLONE_NEWPID
	case NamespaceMount:
		return syscall.CLONE_NEWNS
	case NamespaceUTS:
		return syscall.CLONE_NEWUTS
	case NamespaceIPC:
		return syscall.CLONE_NEWIPC
	case NamespaceNetwork:
		return syscall.CLONE_NEWNET
	case NamespaceUser:
		return syscall.CLONE_NEWUSER
	case NamespaceCgroup:
		return syscall.CLONE_NEWCGROUP
	default:
		return 0
	}
}

// contains 检查切片是否包含指定字符串
func contains(slice []string, item string) bool {
	for _, s := range slice {
		if s == item {
			return true
		}
	}
	return false
}

// mount 封装 mount 系统调用
func mount(source, target, fstype string, flags uintptr, data string) error {
	sourcePtr, err := syscall.BytePtrFromString(source)
	if err != nil {
		return err
	}
	targetPtr, err := syscall.BytePtrFromString(target)
	if err != nil {
		return err
	}
	fstypePtr, err := syscall.BytePtrFromString(fstype)
	if err != nil {
		return err
	}
	dataPtr, err := syscall.BytePtrFromString(data)
	if err != nil {
		return err
	}

	_, _, errno := syscall.Syscall6(
		syscall.SYS_MOUNT,
		uintptr(unsafe.Pointer(sourcePtr)),
		uintptr(unsafe.Pointer(targetPtr)),
		uintptr(unsafe.Pointer(fstypePtr)),
		flags,
		uintptr(unsafe.Pointer(dataPtr)),
		0,
	)

	if errno != 0 {
		return errno
	}
	return nil
}

// unmount 封装 umount2 系统调用
func unmount(target string, flags int) error {
	targetPtr, err := syscall.BytePtrFromString(target)
	if err != nil {
		return err
	}

	_, _, errno := syscall.Syscall(
		syscall.SYS_UMOUNT2,
		uintptr(unsafe.Pointer(targetPtr)),
		uintptr(flags),
		0,
	)

	if errno != 0 {
		return errno
	}
	return nil
}

// pivotRoot 封装 pivot_root 系统调用
func pivotRoot(newRoot, putOld string) error {
	newRootPtr, err := syscall.BytePtrFromString(newRoot)
	if err != nil {
		return err
	}
	putOldPtr, err := syscall.BytePtrFromString(putOld)
	if err != nil {
		return err
	}

	_, _, errno := syscall.Syscall(
		SYS_PIVOT_ROOT,
		uintptr(unsafe.Pointer(newRootPtr)),
		uintptr(unsafe.Pointer(putOldPtr)),
		0,
	)

	if errno != 0 {
		return errno
	}
	return nil
}

// setns 封装 setns 系统调用
func setns(fd int, nstype int) error {
	_, _, errno := syscall.Syscall(
		SYS_SETNS,
		uintptr(fd),
		uintptr(nstype),
		0,
	)

	if errno != 0 {
		return errno
	}
	return nil
}

// mkdev 创建设备号
func mkdev(major, minor uint32) uint32 {
	return (major << 20) | minor
}
