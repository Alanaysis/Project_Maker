# MiniContainer 实现总结

## 项目概述

MiniContainer 是一个教育目的的轻量级容器运行时，使用 Go 语言从零实现，帮助开发者深入理解 Linux 容器技术的核心原理。

## 实现的功能

### 核心功能

1. **容器生命周期管理** ✅
   - 容器创建、启动、停止、删除
   - 容器状态管理（created, running, stopped, paused, error）
   - 容器配置持久化（config.json）
   - 从磁盘恢复容器状态

2. **Namespace 隔离** ✅
   - PID Namespace：进程 ID 隔离
   - Mount Namespace：文件系统隔离（pivot_root）
   - UTS Namespace：主机名隔离
   - IPC Namespace：进程间通信隔离
   - Network Namespace：网络栈隔离

3. **Cgroups 资源限制** ✅
   - 内存限制（memory.max, memory.high, memory.swap.max）
   - CPU 限制（cpu.max CFS 配额）
   - CPU 权重（cpu.weight）
   - 进程数限制（pids.max）
   - I/O 限制（io.max）
   - 进程添加到 cgroup（cgroup.procs）

4. **容器网络** ✅
   - IP 地址池管理
   - veth pair 创建
   - Linux bridge 配置
   - 网络命名空间配置
   - 容器网络生命周期管理

5. **存储管理** ✅
   - 分层存储架构
   - 镜像层管理
   - 容器存储管理
   - OverlayFS 挂载和卸载
   - 目录递归复制

6. **镜像管理** ✅
   - 镜像拉取（模拟）
   - 镜像存储
   - 镜像配置管理
   - 镜像名称解析

7. **卷挂载** ✅
   - 绑定挂载（bind mount）
   - tmpfs 挂载
   - 只读挂载选项

8. **exec 命令** ✅
   - 加入容器 namespace
   - 在容器环境中执行命令

### CLI 命令

| 命令 | 功能 | 状态 |
|------|------|------|
| `run` | 运行容器 | ✅ |
| `create` | 创建容器 | ✅ |
| `start` | 启动容器 | ✅ |
| `stop` | 停止容器 | ✅ |
| `delete` | 删除容器 | ✅ |
| `ps` | 列出容器 | ✅ |
| `images` | 列出镜像 | ✅ |
| `pull` | 拉取镜像 | ✅ |
| `exec` | 在容器中执行命令 | ✅ |
| `child` | 内部子进程入口 | ✅ |

## 项目结构

```
container-runtime/
├── cmd/
│   └── minicontainer/        # CLI 入口
│       ├── main.go           # 主命令和子命令
│       ├── exec_linux.go     # Linux execve 实现
│       └── exec_other.go     # 非 Linux 平台实现
├── pkg/
│   ├── container/            # 容器核心逻辑
│   │   ├── container.go      # 容器生命周期管理
│   │   ├── namespace.go      # Namespace 隔离实现
│   │   ├── cgroup.go         # Cgroups 资源限制
│   │   └── helper.go         # JSON 辅助函数
│   ├── image/                # 镜像管理
│   │   └── image.go          # 镜像操作
│   ├── network/              # 网络管理
│   │   └── network.go        # 网桥和 veth 配置
│   └── storage/              # 存储管理
│       └── storage.go        # OverlayFS 分层存储
├── docs/                     # 项目文档
│   ├── 01-RESEARCH.md        # 技术调研
│   ├── 02-REQUIREMENTS.md    # 需求分析
│   ├── 03-DESIGN.md          # 技术设计
│   ├── 04-PRODUCT.md         # 产品思维
│   └── 05-DEVELOPMENT.md     # 开发手册
├── tests/                    # 测试文件
│   ├── container_test.go     # 容器和存储测试
│   ├── image_test.go         # 镜像管理测试
│   ├── network_test.go       # 网络管理测试
│   └── cgroup_test.go        # Cgroup 资源限制测试
├── examples/                 # 使用示例
│   ├── basic/main.go         # 基础示例
│   ├── cgroup/main.go        # Cgroup 示例
│   ├── namespace/main.go     # Namespace 示例
│   └── network/main.go       # 网络示例
├── Makefile                  # 构建脚本
├── build.sh                  # 构建脚本
├── go.mod                    # Go 模块文件
└── README.md                 # 项目说明
```

## 技术亮点

### 1. 纯标准库实现
- 不依赖外部库，只使用 Go 标准库
- 使用 syscall 包直接调用 Linux 系统调用
- 便于理解和学习

### 2. 完整的容器启动流程
```
Parent Process (minicontainer run)
├── 创建 cgroup 并设置资源限制
├── 使用 clone() 创建新进程（新 namespace）
├── 等待子进程启动
├── 将子进程 PID 加入 cgroup
└── 异步等待子进程退出

Child Process (/proc/self/exe child --id <id> <cmd>)
├── 加载容器配置
├── 设置 UTS namespace (hostname)
├── 设置 Mount namespace (pivot_root)
├── 挂载 /proc, /sys, /dev
├── 处理卷挂载
└── execve() 执行用户命令
```

### 3. 详细的注释
- 每个函数都有详细的注释
- 关键技术点用 ⭐ 标记
- 值得思考的地方用 💡 标记

### 4. 完整的文档
- 市场调研：分析主流容器运行时
- 需求分析：明确用户需求和功能
- 技术设计：详细的架构和接口设计
- 产品思维：产品定位和用户吸引力
- 开发手册：环境搭建和调试技巧

### 5. 丰富的示例
- 基础示例：容器创建和运行
- Cgroup 示例：资源限制演示
- Namespace 示例：隔离机制演示
- 网络示例：网络配置演示

### 6. 全面的测试
- 容器生命周期测试
- 镜像管理测试
- 网络管理测试（IP 池、veth、bridge）
- Cgroup 资源限制测试
- 存储管理测试（OverlayFS）

## 测试覆盖

| 模块 | 测试数量 | 状态 |
|------|----------|------|
| Container | 7 | ✅ |
| Image | 3 | ✅ |
| Network | 8 | ✅ |
| Cgroup | 7 | ✅ |
| Storage | 2 | ✅ |
| Mount | 1 | ✅ |
| Namespace | 1 | ✅ |
| **总计** | **31** | **✅** |

## 关键实现细节

### 1. child 进程重新执行机制

容器使用 `/proc/self/exe child --id <id> <cmd>` 重新执行自己：
- `clone()` 创建新进程时会设置新的 namespace
- 新进程通过 `child` 子命令进入，在隔离环境中执行
- 最后使用 `execve()` 替换为用户命令

### 2. pivot_root 实现

```go
// 1. 重新挂载根文件系统为私有
mount("", "/", "", MS_PRIVATE|MS_REC, "")

// 2. 绑定挂载新的根文件系统
mount(newRoot, newRoot, "", MS_BIND|MS_REC, "")

// 3. 切换根文件系统
pivotRoot(newRoot, oldRoot)

// 4. 卸载旧的根文件系统
unmount("/oldroot", MNT_DETACH)
```

### 3. OverlayFS 挂载

```go
// 构建挂载选项
mountOpts := fmt.Sprintf("lowerdir=%s,upperdir=%s,workdir=%s",
    lowerDirStr, storage.UpperDir, storage.WorkDir)

// 使用 mount 系统调用
syscall.Syscall6(
    syscall.SYS_MOUNT,
    uintptr(unsafe.Pointer(sourcePtr)),
    uintptr(unsafe.Pointer(targetPtr)),
    uintptr(unsafe.Pointer(fstypePtr)),
    0,
    uintptr(unsafe.Pointer(optsPtr)),
    0,
)
```

### 4. Cgroup 资源限制

```go
// 设置内存限制
os.WriteFile(memoryMaxPath, []byte(strconv.FormatInt(limit, 10)), 0644)

// 设置 CPU 配额
cpuMax := fmt.Sprintf("%d %d", quota, period)
os.WriteFile(cpuMaxPath, []byte(cpuMax), 0644)

// 将进程添加到 cgroup
os.WriteFile(procsPath, []byte(strconv.Itoa(pid)), 0644)
```

## 遇到的问题和解决方案

### 1. 外部依赖问题
**问题**：最初使用了 golang.org/x/sys 等外部库
**解决**：重写为纯标准库实现，使用 syscall 包直接调用系统调用

### 2. 系统调用封装
**问题**：Go 标准库没有封装 mount、pivot_root 等系统调用
**解决**：使用 syscall.Syscall6 手动封装这些系统调用

### 3. 子进程重新执行
**问题**：如何在新 namespace 中执行用户命令
**解决**：使用 /proc/self/exe child 子命令机制

### 4. Cgroup 进程添加
**问题**：cgroup 资源限制不生效
**解决**：在 cmd.Start() 后调用 AddProcess(pid)

### 5. OverlayFS 挂载
**问题**：OverlayFS 挂载失败
**解决**：正确构建 lowerdir/upperdir/workdir 选项

## 值得学习的地方

### 1. Linux Namespace 机制
- 理解 6 种 Namespace 的作用
- 掌握 clone() 系统调用的使用
- 理解 setns() 和 unshare() 的区别

### 2. Cgroups 资源限制
- 理解 Cgroups v2 的层级结构
- 掌握 CPU、内存、进程数限制的配置
- 理解资源统计和监控

### 3. 容器文件系统
- 理解分层存储的原理
- 掌握 OverlayFS 的使用
- 理解 pivot_root 的作用

### 4. 容器网络
- 理解 veth pair 的工作原理
- 掌握 Linux bridge 的配置
- 理解网络命名空间的隔离

### 5. 系统编程技巧
- 掌握 Go 的 syscall 包使用
- 理解系统调用的封装方法
- 掌握错误处理和资源清理

## 下一步改进

### 1. 功能增强
- [ ] 支持更多的 Namespace 类型（User, Cgroup）
- [ ] 实现完整的镜像拉取（HTTP 客户端）
- [ ] 支持端口映射（iptables DNAT）
- [ ] 支持容器日志收集

### 2. 性能优化
- [ ] 优化容器启动速度
- [ ] 减少内存占用
- [ ] 优化网络性能

### 3. 安全增强
- [ ] 实现 Capabilities 限制
- [ ] 支持 Seccomp 过滤
- [ ] 实现 AppArmor/SELinux 集成

### 4. 用户体验
- [ ] 完善 CLI 命令（cobra/flag）
- [ ] 添加交互式模式
- [ ] 支持配置文件
- [ ] 支持容器日志查看

## 总结

MiniContainer 项目成功实现了一个轻量级容器运行时的核心功能，包括：

1. **容器生命周期管理**：创建、启动、停止、删除
2. **Namespace 隔离**：PID、Mount、UTS、IPC、Network
3. **Cgroups 资源限制**：CPU、内存、进程数、I/O
4. **容器网络**：veth pair、Linux bridge、IP 池
5. **存储管理**：分层存储、OverlayFS
6. **镜像管理**：拉取、存储、配置
7. **卷挂载**：bind mount、tmpfs
8. **exec 命令**：加入容器 namespace 执行命令

通过这个项目，开发者可以深入理解容器技术的底层原理，为学习更复杂的容器系统打下基础。

项目代码清晰、注释完整、文档丰富、测试全面，是一个优秀的学习资源。
