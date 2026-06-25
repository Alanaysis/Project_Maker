# MiniContainer - 轻量级容器运行时

> 一个从零实现的容器运行时，帮助深入理解 Linux 容器技术的核心原理

## 项目简介

MiniContainer 是一个教育目的的轻量级容器运行时，使用 Go 语言实现。它展示了容器技术的核心概念，包括 Linux namespace 隔离、cgroups 资源限制、OverlayFS 分层存储和容器网络配置。

## 学习目标

通过本项目，你将深入理解：

1. **Linux Namespace 隔离机制** ⭐
   - PID Namespace：进程隔离，容器内进程从 PID 1 开始
   - Mount Namespace：文件系统隔离，使用 pivot_root 切换根目录
   - Network Namespace：网络隔离，独立的网络栈
   - UTS Namespace：主机名隔离
   - IPC Namespace：进程间通信隔离

2. **Cgroups 资源限制** ⭐
   - CPU 限制：使用 CFS 配额和 cpu.weight
   - 内存限制：设置 memory.max 和 memory.high
   - I/O 限制：控制磁盘读写速度
   - 进程数限制：防止 fork 炸弹

3. **容器镜像与存储**
   - OCI 镜像规范
   - OverlayFS 分层存储原理
   - 镜像层和容器可写层的管理

4. **容器网络**
   - veth pair 虚拟网络设备
   - Linux bridge 网桥
   - 网络命名空间配置
   - IP 地址池管理

## 技术栈

| 技术 | 用途 | 学习难度 |
|------|------|----------|
| Go 1.21+ | 主要开发语言 | ⭐⭐ |
| Linux Namespaces | 进程隔离 | ⭐⭐⭐⭐ |
| Cgroups v2 | 资源限制 | ⭐⭐⭐ |
| OverlayFS | 分层文件系统 | ⭐⭐⭐ |
| veth/bridge | 容器网络 | ⭐⭐⭐⭐ |

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
│   │   └── image.go          # 镜像操作（Pull/Load/Get/Delete）
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
├── examples/                 # 使用示例
├── tests/                    # 测试文件
│   ├── container_test.go     # 容器和存储测试
│   ├── image_test.go         # 镜像管理测试
│   ├── network_test.go       # 网络管理测试
│   └── cgroup_test.go        # Cgroup 资源限制测试
├── go.mod
├── Makefile
└── README.md
```

## 快速开始

### 环境要求

- Linux 内核 >= 4.0（支持 cgroups v2）
- Go 1.21+
- root 权限（操作 namespace 和 cgroups 需要）

### 编译

```bash
# 克隆项目
cd projects/container-runtime

# 编译
go build -o minicontainer ./cmd/minicontainer/

# 或使用 make
make build
```

### 使用示例

```bash
# 运行一个容器（需要 root 权限）
sudo ./minicontainer run --name mycontainer --memory 256m --cpu 50 alpine /bin/sh

# 查看运行中的容器
sudo ./minicontainer ps

# 停止容器
sudo ./minicontainer stop mycontainer

# 在运行中的容器内执行命令
sudo ./minicontainer exec mycontainer ls -la

# 挂载宿主机目录到容器
sudo ./minicontainer run -v /host/data:/container/data alpine /bin/sh
```

### 运行测试

```bash
# 运行所有测试
go test ./tests/ -v

# 运行特定测试
go test ./tests/ -run TestContainerManager -v
```

## 核心概念

### 1. 容器是什么？

容器本质上是一个受限的 Linux 进程，通过以下技术实现隔离：

- **Namespace**：让进程看到独立的系统视图
- **Cgroups**：限制进程能使用的资源
- **pivot_root**：限制进程能访问的文件系统

### 2. 容器启动流程

```
┌─────────────────────────────────────────────────────────────┐
│                    容器启动流程                               │
├─────────────────────────────────────────────────────────────┤
│  1. 创建 cgroup 并设置资源限制                               │
│  2. 使用 clone() 创建新进程，同时创建新的 namespace           │
│  3. 子进程进入 "child" 命令分支                              │
│  4. 子进程调用 SetupNamespaces()：                           │
│     - 设置 hostname (UTS namespace)                         │
│     - 设置 mount namespace (pivot_root)                     │
│     - 挂载 /proc, /sys, /dev                                │
│     - 处理用户卷挂载                                         │
│  5. 子进程 exec 用户指定的命令                               │
│  6. 父进程将子进程 PID 加入 cgroup                           │
│  7. 父进程异步等待子进程退出                                  │
└─────────────────────────────────────────────────────────────┘
```

### 3. OverlayFS 分层存储

```
┌─────────────────────────────────────┐
│         Container Layer (可写层)      │  ← 容器运行时修改
├─────────────────────────────────────┤
│         Image Layer (只读层)         │  ← 镜像内容
└─────────────────────────────────────┘
         ↓ OverlayFS 合并 ↓
┌─────────────────────────────────────┐
│         Merged View (合并视图)        │  ← 容器看到的文件系统
└─────────────────────────────────────┘
```

### 4. 容器网络架构

```
┌─────────────────────────────────────────────────────────┐
│                    Host Network                         │
│  ┌───────────────────────────────────────────────────┐  │
│  │                  Linux Bridge (br0)               │  │
│  │         172.17.0.1/16                            │  │
│  └─────────┬─────────────────┬─────────────────────┘  │
│            │                 │                          │
│  ┌─────────┴─────┐ ┌────────┴──────┐                  │
│  │  veth-host    │ │  veth-host    │                  │
│  └───────────────┘ └───────────────┘                  │
│            │                 │                          │
│  ┌─────────┴─────┐ ┌────────┴──────┐                  │
│  │  veth-cont    │ │  veth-cont    │                  │
│  │  172.17.0.2   │ │  172.17.0.3   │                  │
│  └───────────────┘ └───────────────┘                  │
│      Container 1       Container 2                    │
└─────────────────────────────────────────────────────────┘
```

## ⭐ 重点难点

### 1. child 进程重新执行机制

容器使用 `/proc/self/exe child --id <id> <cmd>` 重新执行自己。这是容器运行时的核心技巧：
- `clone()` 创建新进程时会设置新的 namespace
- 新进程通过 `child` 子命令进入，在隔离环境中执行
- 最后使用 `execve()` 替换为用户命令

### 2. pivot_root vs chroot

`pivot_root` 比 `chroot` 更安全：
- `chroot` 只改变文件系统根目录，进程仍可访问宿主机资源
- `pivot_root` 完全切换根文件系统，配合 mount namespace 实现完全隔离

### 3. Cgroups v2 资源控制

Cgroups v2 使用统一层级，所有控制器在同一个目录树下：
- `memory.max`：内存硬限制
- `cpu.max`：CPU 配额（quota period）
- `pids.max`：进程数限制

### 4. OverlayFS 挂载

OverlayFS 将多个目录合并为一个视图：
- `lowerdir`：只读层（镜像层）
- `upperdir`：可写层（容器层）
- `workdir`：OverlayFS 内部工作目录
- `merged`：最终合并视图

## 💡 值得思考

1. **为什么 Docker 选择用 Go 而不是 C 实现？**
2. **OCI 标准化对容器生态有什么意义？**
3. **容器逃逸是如何发生的？如何防御？**
4. **cgroups v2 相比 v1 有什么改进？**
5. **如何实现容器的热迁移？**

## 参考资源

### 官方文档
- [OCI Runtime Specification](https://github.com/opencontainers/runtime-spec)
- [Linux Namespaces Man Pages](https://man7.org/linux/man-pages/man7/namespaces.7.html)
- [Cgroups v2 Documentation](https://www.kernel.org/doc/Documentation/cgroup-v2.txt)

### 开源项目
- [runc](https://github.com/opencontainers/runc) - OCI 参考实现
- [containerd](https://github.com/containerd/containerd) - 容器运行时
- [crun](https://github.com/containers/crun) - C 语言实现的轻量级运行时

### 学习资源
- [Linux Container from Scratch](https://medium.com/@sstelfox/linux-containers-from-scratch-a7759075be24)
- [Build Your Own Container](https://ericchiang.github.io/post/containers-from-scratch/)

## 许可证

MIT License

---

**注意**：本项目仅用于学习目的，不建议在生产环境使用。生产环境请使用成熟的容器运行时如 containerd、CRI-O 或 Podman。
