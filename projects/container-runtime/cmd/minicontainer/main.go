// MiniContainer - 轻量级容器运行时
//
// 这是容器运行时的命令行入口，提供以下功能：
// - run: 运行容器
// - create: 创建容器
// - start: 启动容器
// - stop: 停止容器
// - delete: 删除容器
// - ps: 列出容器
// - images: 列出镜像
// - pull: 拉取镜像
// - exec: 在容器中执行命令
// - child: 内部子进程入口（由 Start() 自动调用）
package main

import (
	"fmt"
	"os"
	"strings"

	"github.com/minicontainer/runtime/pkg/container"
	"github.com/minicontainer/runtime/pkg/image"
	"github.com/minicontainer/runtime/pkg/network"
	"github.com/minicontainer/runtime/pkg/storage"
)

const (
	// 版本号
	Version = "0.2.0"
	// 使用说明
	Usage = `MiniContainer - 轻量级容器运行时

用法:
  minicontainer <command> [options]

命令:
  run         运行容器
  create      创建容器
  start       启动容器
  stop        停止容器
  delete      删除容器
  ps          列出容器
  images      列出镜像
  pull        拉取镜像
  exec        在容器中执行命令
  version     显示版本信息
  help        显示帮助信息

示例:
  minicontainer run --name mycontainer alpine /bin/sh
  minicontainer ps
  minicontainer images
`
)

// 全局管理器实例，供 run 和 child 子命令共享
var (
	containerMgr *container.ContainerManager
	storageMgr   *storage.StorageManager
	imageMgr     *image.ImageManager
	networkMgr   *network.NetworkManager
)

func main() {
	// 检查参数
	if len(os.Args) < 2 {
		fmt.Print(Usage)
		os.Exit(1)
	}

	// 解析命令
	command := os.Args[1]
	args := os.Args[2:]

	// 执行命令
	switch command {
	case "child":
		// ⭐ 重点：这是容器子进程的入口点
		// 当 Start() 使用 /proc/self/exe child --id <id> <cmd> 启动时，
		// 新进程会进入这个分支，在隔离的 namespace 中执行用户命令
		childCommand(args)
	case "run":
		runCommand(args)
	case "create":
		createCommand(args)
	case "start":
		startCommand(args)
	case "stop":
		stopCommand(args)
	case "delete":
		deleteCommand(args)
	case "ps":
		psCommand(args)
	case "images":
		imagesCommand(args)
	case "pull":
		pullCommand(args)
	case "exec":
		execCommand(args)
	case "version":
		fmt.Printf("MiniContainer version %s\n", Version)
	case "help":
		fmt.Print(Usage)
	default:
		fmt.Fprintf(os.Stderr, "未知命令: %s\n", command)
		fmt.Print(Usage)
		os.Exit(1)
	}
}

// initManagers 初始化所有管理器
func initManagers() error {
	var err error

	containerMgr, err = container.NewContainerManager("/var/lib/minicontainer/containers")
	if err != nil {
		return fmt.Errorf("failed to create container manager: %w", err)
	}

	storageMgr, err = storage.NewStorageManager("/var/lib/minicontainer")
	if err != nil {
		return fmt.Errorf("failed to create storage manager: %w", err)
	}

	imageMgr, err = image.NewImageManager("/var/lib/minicontainer/images")
	if err != nil {
		return fmt.Errorf("failed to create image manager: %w", err)
	}

	networkMgr, err = network.NewNetworkManager("", "")
	if err != nil {
		return fmt.Errorf("failed to create network manager: %w", err)
	}

	return nil
}

// childCommand 容器子进程入口
//
// ⭐ 重点：这是容器运行时的核心机制
//
// 当 Start() 调用 /proc/self/exe child --id <id> <cmd> 时：
// 1. 内核通过 clone(CLONE_NEWPID|CLONE_NEWNS|...) 创建新进程
// 2. 新进程进入这里，此时已经在新的 namespace 中
// 3. 调用 SetupNamespaces() 设置 hostname、mount namespace、pivot_root
// 4. 最后 exec 用户指定的命令
func childCommand(args []string) {
	if len(args) < 3 || args[0] != "--id" {
		fmt.Fprintf(os.Stderr, "用法: minicontainer child --id <container-id> <command> [args...]\n")
		os.Exit(1)
	}

	containerID := args[1]
	command := args[2:]

	// 加载容器配置
	configPath := fmt.Sprintf("/var/lib/minicontainer/containers/%s/config.json", containerID)
	var config container.ContainerConfig
	if err := readJSONFromFile(configPath, &config); err != nil {
		fmt.Fprintf(os.Stderr, "错误: 无法加载容器配置: %v\n", err)
		os.Exit(1)
	}

	// ⭐ 设置命名空间（在新的 namespace 中执行）
	if err := container.SetupNamespaces(&config); err != nil {
		fmt.Fprintf(os.Stderr, "错误: 无法设置命名空间: %v\n", err)
		os.Exit(1)
	}

	// 设置环境变量
	if len(config.Env) > 0 {
		for _, env := range config.Env {
			parts := strings.SplitN(env, "=", 2)
			if len(parts) == 2 {
				os.Setenv(parts[0], parts[1])
			}
		}
	}

	// 设置工作目录
	if config.WorkDir != "" {
		if err := os.Chdir(config.WorkDir); err != nil {
			fmt.Fprintf(os.Stderr, "警告: 无法切换到工作目录 %s: %v\n", config.WorkDir, err)
		}
	}

	// 执行用户命令
	if len(command) == 0 {
		command = []string{"/bin/sh"}
	}

	// 查找命令路径
	cmdPath, err := execLookPath(command[0])
	if err != nil {
		fmt.Fprintf(os.Stderr, "错误: 找不到命令 %s: %v\n", command[0], err)
		os.Exit(1)
	}

	// 替换当前进程
	if err := syscallExec(cmdPath, command, os.Environ()); err != nil {
		fmt.Fprintf(os.Stderr, "错误: 无法执行命令: %v\n", err)
		os.Exit(1)
	}
}

// readJSONFromFile 从文件读取 JSON
func readJSONFromFile(path string, data interface{}) error {
	jsonData, err := os.ReadFile(path)
	if err != nil {
		return fmt.Errorf("failed to read file: %w", err)
	}

	// 使用 encoding/json 反序列化
	return jsonUnmarshal(jsonData, data)
}

// execLookPath 查找可执行文件
func execLookPath(name string) (string, error) {
	// 如果是绝对路径，直接返回
	if strings.HasPrefix(name, "/") {
		if _, err := os.Stat(name); err != nil {
			return "", err
		}
		return name, nil
	}

	// 在 PATH 中查找
	path := os.Getenv("PATH")
	if path == "" {
		path = "/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
	}

	for _, dir := range strings.Split(path, ":") {
		fullPath := dir + "/" + name
		if _, err := os.Stat(fullPath); err == nil {
			return fullPath, nil
		}
	}

	return "", fmt.Errorf("executable file not found in $PATH: %s", name)
}

// syscallExec 使用 execve 替换当前进程
func syscallExec(path string, argv []string, envv []string) error {
	return syscallExecImpl(path, argv, envv)
}

// runCommand 运行容器
func runCommand(args []string) {
	// 解析参数
	var name string
	var memory string
	var cpu int
	var imageName string
	var command []string
	var volumes []string

	for i := 0; i < len(args); i++ {
		switch args[i] {
		case "--name":
			if i+1 < len(args) {
				name = args[i+1]
				i++
			}
		case "--memory", "-m":
			if i+1 < len(args) {
				memory = args[i+1]
				i++
			}
		case "--cpu", "-c":
			if i+1 < len(args) {
				fmt.Sscanf(args[i+1], "%d", &cpu)
				i++
			}
		case "-v", "--volume":
			if i+1 < len(args) {
				volumes = append(volumes, args[i+1])
				i++
			}
		default:
			// 第一个非选项参数是镜像，其余是命令
			if imageName == "" {
				imageName = args[i]
			} else {
				command = append(command, args[i])
			}
		}
	}

	// 验证参数
	if imageName == "" {
		fmt.Fprintf(os.Stderr, "错误: 必须指定镜像\n")
		os.Exit(1)
	}

	if len(command) == 0 {
		command = []string{"/bin/sh"}
	}

	// 解析内存限制
	memoryLimit := parseMemory(memory)

	// 初始化管理器
	if err := initManagers(); err != nil {
		fmt.Fprintf(os.Stderr, "错误: %v\n", err)
		os.Exit(1)
	}

	// 获取镜像
	img, err := imageMgr.Get(imageName)
	if err != nil {
		// 如果镜像不存在，尝试拉取
		fmt.Printf("镜像 %s 不存在，尝试拉取...\n", imageName)
		img, err = imageMgr.Pull(imageName)
		if err != nil {
			fmt.Fprintf(os.Stderr, "错误: 无法拉取镜像: %v\n", err)
			os.Exit(1)
		}
	}

	// 创建镜像层（如果不存在）
	layerID := img.ID
	if _, err := storageMgr.GetLayer(layerID); err != nil {
		// 创建镜像层
		imgDir, _ := imageMgr.GetImageDir(img.ID)
		if imgDir == "" {
			imgDir, _ = imageMgr.GetImageDir(img.Name)
		}
		if imgDir != "" {
			if err := storageMgr.CreateRootFS(layerID, imgDir); err != nil {
				fmt.Printf("警告: 无法创建镜像层: %v\n", err)
				// 创建空层作为降级
				storageMgr.CreateLayer(layerID, "")
			}
		} else {
			storageMgr.CreateLayer(layerID, "")
		}
	}

	// 生成容器 ID
	containerID := fmt.Sprintf("ctr-%x", generateTimestampID(name, imageName))

	// 创建容器存储
	_, err = storageMgr.CreateContainerStorage(containerID, layerID)
	if err != nil {
		fmt.Fprintf(os.Stderr, "错误: %v\n", err)
		os.Exit(1)
	}

	// 挂载 OverlayFS
	if err := storageMgr.MountContainer(containerID); err != nil {
		fmt.Fprintf(os.Stderr, "警告: OverlayFS 挂载失败: %v\n", err)
	}

	// 获取根文件系统路径
	rootFS, err := storageMgr.GetRootFS(containerID)
	if err != nil {
		fmt.Fprintf(os.Stderr, "错误: %v\n", err)
		os.Exit(1)
	}

	// 解析卷挂载
	mounts := parseVolumes(volumes)

	// 创建容器配置
	config := &container.ContainerConfig{
		Name:      name,
		ID:        containerID,
		Image:     imageName,
		Command:   command,
		RootFS:    rootFS,
		Resources: &container.ResourceLimit{
			MemoryLimit: memoryLimit,
			CPUPercent:  cpu,
		},
		Hostname: name,
		Mounts:   mounts,
	}

	// 创建容器
	cont, err := containerMgr.Create(config)
	if err != nil {
		fmt.Fprintf(os.Stderr, "错误: %v\n", err)
		os.Exit(1)
	}

	// 初始化网络
	if err := networkMgr.InitNetwork(); err != nil {
		fmt.Printf("警告: 网络初始化失败: %v\n", err)
	}

	// 为容器创建网络
	netConfig, err := networkMgr.CreateNetwork(cont.Config.ID)
	if err != nil {
		fmt.Printf("警告: 无法创建容器网络: %v\n", err)
	} else {
		fmt.Printf("容器网络: %s (%s)\n", netConfig.IP.String(), netConfig.MAC)
	}

	// 启动容器
	if err := containerMgr.Start(cont.Config.ID); err != nil {
		fmt.Fprintf(os.Stderr, "错误: %v\n", err)
		os.Exit(1)
	}

	// 设置容器网络（需要容器 PID）
	if netConfig != nil {
		if err := networkMgr.SetupContainerNetwork(cont.Config.ID, cont.PID); err != nil {
			fmt.Printf("警告: 容器网络设置失败: %v\n", err)
		}
	}

	fmt.Printf("容器 %s 已启动 (PID: %d)\n", cont.Config.ID, cont.PID)
}

// createCommand 创建容器
func createCommand(args []string) {
	var name string
	var imageName string
	var command []string

	for i := 0; i < len(args); i++ {
		switch args[i] {
		case "--name":
			if i+1 < len(args) {
				name = args[i+1]
				i++
			}
		default:
			if imageName == "" {
				imageName = args[i]
			} else {
				command = append(command, args[i])
			}
		}
	}

	if imageName == "" {
		fmt.Fprintf(os.Stderr, "错误: 必须指定镜像\n")
		os.Exit(1)
	}

	// 初始化管理器
	if err := initManagers(); err != nil {
		fmt.Fprintf(os.Stderr, "错误: %v\n", err)
		os.Exit(1)
	}

	// 创建容器配置
	config := &container.ContainerConfig{
		Name:    name,
		Image:   imageName,
		Command: command,
	}

	// 创建容器
	cont, err := containerMgr.Create(config)
	if err != nil {
		fmt.Fprintf(os.Stderr, "错误: %v\n", err)
		os.Exit(1)
	}

	fmt.Printf("容器 %s 已创建\n", cont.Config.ID)
}

// startCommand 启动容器
func startCommand(args []string) {
	if len(args) == 0 {
		fmt.Fprintf(os.Stderr, "错误: 必须指定容器 ID 或名称\n")
		os.Exit(1)
	}

	containerID := args[0]

	// 初始化管理器
	if err := initManagers(); err != nil {
		fmt.Fprintf(os.Stderr, "错误: %v\n", err)
		os.Exit(1)
	}

	// 启动容器
	if err := containerMgr.Start(containerID); err != nil {
		fmt.Fprintf(os.Stderr, "错误: %v\n", err)
		os.Exit(1)
	}

	fmt.Printf("容器 %s 已启动\n", containerID)
}

// stopCommand 停止容器
func stopCommand(args []string) {
	if len(args) == 0 {
		fmt.Fprintf(os.Stderr, "错误: 必须指定容器 ID 或名称\n")
		os.Exit(1)
	}

	containerID := args[0]

	// 初始化管理器
	if err := initManagers(); err != nil {
		fmt.Fprintf(os.Stderr, "错误: %v\n", err)
		os.Exit(1)
	}

	// 停止容器
	if err := containerMgr.Stop(containerID); err != nil {
		fmt.Fprintf(os.Stderr, "错误: %v\n", err)
		os.Exit(1)
	}

	// 清理网络
	if networkMgr != nil {
		if err := networkMgr.DeleteNetwork(containerID); err != nil {
			fmt.Printf("警告: 网络清理失败: %v\n", err)
		}
	}

	// 卸载文件系统
	if storageMgr != nil {
		if err := storageMgr.UnmountContainer(containerID); err != nil {
			fmt.Printf("警告: 文件系统卸载失败: %v\n", err)
		}
	}

	fmt.Printf("容器 %s 已停止\n", containerID)
}

// deleteCommand 删除容器
func deleteCommand(args []string) {
	if len(args) == 0 {
		fmt.Fprintf(os.Stderr, "错误: 必须指定容器 ID 或名称\n")
		os.Exit(1)
	}

	containerID := args[0]

	// 初始化管理器
	if err := initManagers(); err != nil {
		fmt.Fprintf(os.Stderr, "错误: %v\n", err)
		os.Exit(1)
	}

	// 删除容器
	if err := containerMgr.Delete(containerID); err != nil {
		fmt.Fprintf(os.Stderr, "错误: %v\n", err)
		os.Exit(1)
	}

	// 清理存储
	if storageMgr != nil {
		if err := storageMgr.DeleteContainerStorage(containerID); err != nil {
			fmt.Printf("警告: 存储清理失败: %v\n", err)
		}
	}

	// 清理网络
	if networkMgr != nil {
		if err := networkMgr.DeleteNetwork(containerID); err != nil {
			fmt.Printf("警告: 网络清理失败: %v\n", err)
		}
	}

	fmt.Printf("容器 %s 已删除\n", containerID)
}

// psCommand 列出容器
func psCommand(args []string) {
	// 初始化管理器
	if err := initManagers(); err != nil {
		fmt.Fprintf(os.Stderr, "错误: %v\n", err)
		os.Exit(1)
	}

	// 列出容器
	containers := containerMgr.List()

	// 打印表头
	fmt.Printf("%-20s %-15s %-10s %-20s %-15s\n",
		"CONTAINER ID", "IMAGE", "STATUS", "CREATED", "NAME")
	fmt.Println(strings.Repeat("-", 80))

	// 打印容器信息
	for _, cont := range containers {
		name := cont.Config.Name
		if name == "" {
			if len(cont.Config.ID) >= 12 {
				name = cont.Config.ID[:12]
			} else {
				name = cont.Config.ID
			}
		}

		idDisplay := cont.Config.ID
		if len(idDisplay) > 20 {
			idDisplay = idDisplay[:20]
		}

		fmt.Printf("%-20s %-15s %-10s %-20s %-15s\n",
			idDisplay,
			cont.Config.Image,
			cont.Status.String(),
			cont.CreatedAt.Format("2006-01-02 15:04:05"),
			name)
	}
}

// imagesCommand 列出镜像
func imagesCommand(args []string) {
	// 初始化管理器
	if err := initManagers(); err != nil {
		fmt.Fprintf(os.Stderr, "错误: %v\n", err)
		os.Exit(1)
	}

	// 列出镜像
	images := imageMgr.List()

	// 打印表头
	fmt.Printf("%-20s %-15s %-10s %-20s\n",
		"IMAGE ID", "REPOSITORY", "TAG", "SIZE")
	fmt.Println(strings.Repeat("-", 65))

	// 打印镜像信息
	for _, img := range images {
		idDisplay := img.ID
		if len(idDisplay) > 20 {
			idDisplay = idDisplay[:20]
		}

		fmt.Printf("%-20s %-15s %-10s %-20d\n",
			idDisplay,
			img.Name,
			img.Tag,
			img.Size)
	}
}

// pullCommand 拉取镜像
func pullCommand(args []string) {
	if len(args) == 0 {
		fmt.Fprintf(os.Stderr, "错误: 必须指定镜像名称\n")
		os.Exit(1)
	}

	imageName := args[0]

	// 初始化管理器
	if err := initManagers(); err != nil {
		fmt.Fprintf(os.Stderr, "错误: %v\n", err)
		os.Exit(1)
	}

	// 拉取镜像
	fmt.Printf("正在拉取镜像 %s...\n", imageName)
	img, err := imageMgr.Pull(imageName)
	if err != nil {
		fmt.Fprintf(os.Stderr, "错误: %v\n", err)
		os.Exit(1)
	}

	fmt.Printf("镜像 %s 拉取成功\n", img.ID)
}

// execCommand 在运行中的容器内执行命令
//
// ⭐ 重点：exec 的实现原理
// 1. 获取目标容器的 PID
// 2. 使用 setns() 加入容器的所有 namespace
// 3. 在容器的 namespace 中 fork 并执行新命令
func execCommand(args []string) {
	if len(args) < 2 {
		fmt.Fprintf(os.Stderr, "用法: minicontainer exec <container-id> <command> [args...]\n")
		os.Exit(1)
	}

	containerID := args[0]
	command := args[1:]

	// 初始化管理器
	if err := initManagers(); err != nil {
		fmt.Fprintf(os.Stderr, "错误: %v\n", err)
		os.Exit(1)
	}

	// 获取容器
	cont, err := containerMgr.Get(containerID)
	if err != nil {
		fmt.Fprintf(os.Stderr, "错误: %v\n", err)
		os.Exit(1)
	}

	// 检查容器状态
	if cont.Status != container.StatusRunning {
		fmt.Fprintf(os.Stderr, "错误: 容器 %s 未运行\n", containerID)
		os.Exit(1)
	}

	fmt.Printf("在容器 %s 中执行: %s\n", containerID, strings.Join(command, " "))

	// ⭐ 加入容器的所有 namespace
 namespaces := []string{"pid", "mount", "uts", "ipc", "net"}
	for _, ns := range namespaces {
		if err := container.JoinNamespace(cont.PID, ns); err != nil {
			fmt.Printf("警告: 无法加入 %s namespace: %v\n", ns, err)
		}
	}

	// 在容器 namespace 中执行命令
	cmdPath, err := execLookPath(command[0])
	if err != nil {
		fmt.Fprintf(os.Stderr, "错误: 找不到命令 %s: %v\n", command[0], err)
		os.Exit(1)
	}

	if err := syscallExec(cmdPath, command, os.Environ()); err != nil {
		fmt.Fprintf(os.Stderr, "错误: 无法执行命令: %v\n", err)
		os.Exit(1)
	}
}

// parseMemory 解析内存限制字符串
func parseMemory(memory string) int64 {
	if memory == "" {
		return 256 * 1024 * 1024 // 默认 256MB
	}

	// 移除空格
	memory = strings.TrimSpace(memory)

	// 解析数字和单位
	var value int64
	var unit string

	fmt.Sscanf(memory, "%d%s", &value, &unit)

	// 根据单位转换
	switch strings.ToLower(unit) {
	case "k", "kb":
		return value * 1024
	case "m", "mb":
		return value * 1024 * 1024
	case "g", "gb":
		return value * 1024 * 1024 * 1024
	default:
		// 默认为字节
		return value
	}
}

// parseVolumes 解析卷挂载参数
//
// 格式: /host/path:/container/path[:options]
func parseVolumes(volumes []string) []container.Mount {
	var mounts []container.Mount

	for _, v := range volumes {
		parts := strings.SplitN(v, ":", 3)
		if len(parts) < 2 {
			continue
		}

		mount := container.Mount{
			Source:      parts[0],
			Destination: parts[1],
			Type:        "bind",
		}

		if len(parts) > 2 {
			mount.Options = strings.Split(parts[2], ",")
		}

		mounts = append(mounts, mount)
	}

	return mounts
}

// generateTimestampID 生成基于时间戳的 ID
func generateTimestampID(parts ...string) uint64 {
	var hash uint64
	for _, p := range parts {
		for _, c := range p {
			hash = hash*31 + uint64(c)
		}
	}
	return hash
}

// jsonUnmarshal 反序列化 JSON
func jsonUnmarshal(data []byte, v interface{}) error {
	// 使用标准库的 JSON 解析
	return jsonUnmarshalImpl(data, v)
}
