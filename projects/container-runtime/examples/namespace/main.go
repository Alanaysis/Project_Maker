// Namespace 示例：进程隔离演示
//
// 这个示例展示 Linux Namespace 的隔离效果
package main

import (
	"fmt"
	"os"
	"syscall"
)

func main() {
	fmt.Println("=== Namespace 隔离示例 ===")

	// 1. PID Namespace
	fmt.Println("\n1. PID Namespace 隔离")
	fmt.Println("   PID Namespace 让容器内的进程从 PID 1 开始")
	fmt.Println("   容器内看不到宿主机的进程")
	fmt.Printf("   当前进程 PID: %d\n", os.Getpid())

	// 2. UTS Namespace
	fmt.Println("\n2. UTS Namespace 隔离")
	fmt.Println("   UTS Namespace 让容器有独立的主机名")
	hostname, _ := os.Hostname()
	fmt.Printf("   当前主机名: %s\n", hostname)
	fmt.Println("   容器可以设置自己的主机名")

	// 3. Mount Namespace
	fmt.Println("\n3. Mount Namespace 隔离")
	fmt.Println("   Mount Namespace 让容器有独立的文件系统视图")
	fmt.Println("   容器看不到宿主机的挂载点")
	fmt.Println("   容器有自己的 /proc, /sys, /dev")

	// 4. Network Namespace
	fmt.Println("\n4. Network Namespace 隔离")
	fmt.Println("   Network Namespace 让容器有独立的网络栈")
	fmt.Println("   容器有自己的 IP 地址、路由表、iptables 规则")

	// 5. IPC Namespace
	fmt.Println("\n5. IPC Namespace 隔离")
	fmt.Println("   IPC Namespace 让容器有独立的进程间通信")
	fmt.Println("   容器之间不能通过 IPC 通信")

	// 6. 展示 clone 标志
	fmt.Println("\n6. clone() 系统调用标志")
	flags := map[string]uintptr{
		"CLONE_NEWPID":     syscall.CLONE_NEWPID,
		"CLONE_NEWNS":      syscall.CLONE_NEWNS,
		"CLONE_NEWUTS":     syscall.CLONE_NEWUTS,
		"CLONE_NEWIPC":     syscall.CLONE_NEWIPC,
		"CLONE_NEWNET":     syscall.CLONE_NEWNET,
		"CLONE_NEWUSER":    syscall.CLONE_NEWUSER,
		"CLONE_NEWCGROUP":  syscall.CLONE_NEWCGROUP,
	}

	for name, flag := range flags {
		fmt.Printf("   %-20s = %d\n", name, flag)
	}

	// 7. 展示容器启动流程
	fmt.Println("\n7. 容器启动流程")
	fmt.Println("   1. 调用 clone() 创建新进程")
	fmt.Println("   2. 设置 namespace 标志")
	fmt.Println("   3. 在新进程中设置隔离环境")
	fmt.Println("   4. 切换根文件系统 (pivot_root)")
	fmt.Println("   5. 执行用户命令")

	// 8. 展示系统调用
	fmt.Println("\n8. 关键系统调用")
	fmt.Println("   clone()     - 创建新进程并设置 namespace")
	fmt.Println("   setns()     - 加入已存在的 namespace")
	fmt.Println("   unshare()   - 创建新的 namespace")
	fmt.Println("   pivot_root() - 切换根文件系统")
	fmt.Println("   mount()     - 挂载文件系统")

	// 9. 展示 /proc 文件系统
	fmt.Println("\n9. /proc 文件系统")
	fmt.Println("   /proc/<pid>/ns/ - 进程的 namespace 信息")
	fmt.Println("   /proc/<pid>/cgroup - 进程的 cgroup 信息")
	fmt.Println("   /proc/<pid>/mountinfo - 进程的挂载信息")

	// 10. 展示实际应用
	fmt.Println("\n10. 实际应用")
	fmt.Println("   Docker 使用 namespace 实现容器隔离")
	fmt.Println("   Kubernetes 使用 namespace 实现 Pod 隔离")
	fmt.Println("   LXC 使用 namespace 实现系统容器")

	fmt.Println("\n=== 示例完成 ===")
	fmt.Println("\n注意: 完整的 namespace 演示需要 root 权限")
	fmt.Println("运行: sudo go run examples/namespace/main.go")
}
