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
	Version = "0.1.0"
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

// runCommand 运行容器
func runCommand(args []string) {
	// 解析参数
	var name string
	var memory string
	var cpu int
	var image string
	var command []string

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
		default:
			// 第一个非选项参数是镜像，其余是命令
			if image == "" {
				image = args[i]
			} else {
				command = append(command, args[i])
			}
		}
	}

	// 验证参数
	if image == "" {
		fmt.Fprintf(os.Stderr, "错误: 必须指定镜像\n")
		os.Exit(1)
	}

	if len(command) == 0 {
		command = []string{"/bin/sh"}
	}

	// 解析内存限制
	memoryLimit := parseMemory(memory)

	// 创建容器管理器
	containerMgr, err := container.NewContainerManager("/var/lib/minicontainer/containers")
	if err != nil {
		fmt.Fprintf(os.Stderr, "错误: %v\n", err)
		os.Exit(1)
	}

	// 创建存储管理器
	storageMgr, err := storage.NewStorageManager("/var/lib/minicontainer")
	if err != nil {
		fmt.Fprintf(os.Stderr, "错误: %v\n", err)
		os.Exit(1)
	}

	// 创建镜像管理器
	imageMgr, err := image.NewImageManager("/var/lib/minicontainer/images")
	if err != nil {
		fmt.Fprintf(os.Stderr, "错误: %v\n", err)
		os.Exit(1)
	}

	// 获取镜像
	img, err := imageMgr.Get(image)
	if err != nil {
		// 如果镜像不存在，尝试拉取
		fmt.Printf("镜像 %s 不存在，尝试拉取...\n", image)
		img, err = imageMgr.Pull(image)
		if err != nil {
			fmt.Fprintf(os.Stderr, "错误: 无法拉取镜像: %v\n", err)
			os.Exit(1)
		}
	}

	// 创建容器存储
	containerID := fmt.Sprintf("container-%x", len(name)+len(image))
	_, err = storageMgr.CreateContainerStorage(containerID, img.ID)
	if err != nil {
		fmt.Fprintf(os.Stderr, "错误: %v\n", err)
		os.Exit(1)
	}

	// 获取根文件系统路径
	rootFS, err := storageMgr.GetRootFS(containerID)
	if err != nil {
		fmt.Fprintf(os.Stderr, "错误: %v\n", err)
		os.Exit(1)
	}

	// 创建容器配置
	config := &container.ContainerConfig{
		Name:    name,
		Image:   image,
		Command: command,
		RootFS:  rootFS,
		Resources: &container.ResourceLimit{
			MemoryLimit: memoryLimit,
			CPUPercent:  cpu,
		},
		Hostname: name,
	}

	// 创建容器
	cont, err := containerMgr.Create(config)
	if err != nil {
		fmt.Fprintf(os.Stderr, "错误: %v\n", err)
		os.Exit(1)
	}

	// 启动容器
	if err := containerMgr.Start(cont.Config.ID); err != nil {
		fmt.Fprintf(os.Stderr, "错误: %v\n", err)
		os.Exit(1)
	}

	fmt.Printf("容器 %s 已启动\n", cont.Config.ID)
}

// createCommand 创建容器
func createCommand(args []string) {
	var name string
	var image string
	var command []string

	for i := 0; i < len(args); i++ {
		switch args[i] {
		case "--name":
			if i+1 < len(args) {
				name = args[i+1]
				i++
			}
		default:
			if image == "" {
				image = args[i]
			} else {
				command = append(command, args[i])
			}
		}
	}

	if image == "" {
		fmt.Fprintf(os.Stderr, "错误: 必须指定镜像\n")
		os.Exit(1)
	}

	// 创建容器管理器
	containerMgr, err := container.NewContainerManager("/var/lib/minicontainer/containers")
	if err != nil {
		fmt.Fprintf(os.Stderr, "错误: %v\n", err)
		os.Exit(1)
	}

	// 创建容器配置
	config := &container.ContainerConfig{
		Name:    name,
		Image:   image,
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

	// 创建容器管理器
	containerMgr, err := container.NewContainerManager("/var/lib/minicontainer/containers")
	if err != nil {
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

	// 创建容器管理器
	containerMgr, err := container.NewContainerManager("/var/lib/minicontainer/containers")
	if err != nil {
		fmt.Fprintf(os.Stderr, "错误: %v\n", err)
		os.Exit(1)
	}

	// 停止容器
	if err := containerMgr.Stop(containerID); err != nil {
		fmt.Fprintf(os.Stderr, "错误: %v\n", err)
		os.Exit(1)
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

	// 创建容器管理器
	containerMgr, err := container.NewContainerManager("/var/lib/minicontainer/containers")
	if err != nil {
		fmt.Fprintf(os.Stderr, "错误: %v\n", err)
		os.Exit(1)
	}

	// 删除容器
	if err := containerMgr.Delete(containerID); err != nil {
		fmt.Fprintf(os.Stderr, "错误: %v\n", err)
		os.Exit(1)
	}

	fmt.Printf("容器 %s 已删除\n", containerID)
}

// psCommand 列出容器
func psCommand(args []string) {
	// 创建容器管理器
	containerMgr, err := container.NewContainerManager("/var/lib/minicontainer/containers")
	if err != nil {
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
			name = cont.Config.ID[:12]
		}

		fmt.Printf("%-20s %-15s %-10s %-20s %-15s\n",
			cont.Config.ID[:20],
			cont.Config.Image,
			cont.Status.String(),
			cont.CreatedAt.Format("2006-01-02 15:04:05"),
			name)
	}
}

// imagesCommand 列出镜像
func imagesCommand(args []string) {
	// 创建镜像管理器
	imageMgr, err := image.NewImageManager("/var/lib/minicontainer/images")
	if err != nil {
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
		fmt.Printf("%-20s %-15s %-10s %-20d\n",
			img.ID[:20],
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

	// 创建镜像管理器
	imageMgr, err := image.NewImageManager("/var/lib/minicontainer/images")
	if err != nil {
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

// execCommand 在容器中执行命令
func execCommand(args []string) {
	if len(args) < 2 {
		fmt.Fprintf(os.Stderr, "用法: minicontainer exec <container-id> <command> [args...]\n")
		os.Exit(1)
	}

	containerID := args[0]
	command := args[1:]

	// 创建容器管理器
	containerMgr, err := container.NewContainerManager("/var/lib/minicontainer/containers")
	if err != nil {
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

	// 执行命令
	fmt.Printf("在容器 %s 中执行: %s\n", containerID, strings.Join(command, " "))

	// 注意：这里只是演示，实际实现需要加入容器的 namespace
	_ = command
}

// parseMemory 解析内存限制字符串
//
// 💡 思考：如何支持不同的内存单位？
// - 256M, 256MB, 256m
// - 1G, 1GB, 1g
// - 1024K, 1024KB, 1024k
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
