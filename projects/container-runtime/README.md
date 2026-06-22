# MiniContainer - 轻量级容器运行时

> 一个从零实现的容器运行时，帮助深入理解 Linux 容器技术的核心原理

## 项目简介

MiniContainer 是一个教育目的的轻量级容器运行时，使用 Go 语言实现。它展示了容器技术的核心概念，包括 Linux namespace 隔离、cgroups 资源限制、文件系统管理和网络配置。

## 学习目标

通过本项目，你将深入理解：

1. **Linux Namespace 隔离机制** ⭐
   - PID Namespace：进程隔离
   - Mount Namespace：文件系统隔离
   - Network Namespace：网络隔离
   - UTS Namespace：主机名隔离
   - IPC Namespace：进程间通信隔离

2. **Cgroups 资源限制** ⭐
   - CPU 限制：使用 CPU shares 和 CFS 配额
   - 内存限制：设置内存使用上限
   - I/O 限制：控制磁盘读写速度

3. **容器镜像格式**
   - OCI 镜像规范
   - 分层存储原理
   - 镜像拉取和解压

4. **容器网络**
   - veth pair 虚拟网络设备
   - Linux bridge 网桥
   - 网络命名空间配置

## 技术栈

| 技术 | 用途 | 学习难度 |
|------|------|----------|
| Go 1.21+ | 主要开发语言 | ⭐⭐ |
| Linux Namespaces | 进程隔离 | ⭐⭐⭐⭐ |
| Cgroups v2 | 资源限制 | ⭐⭐⭐ |
| OverlayFS | 分层文件系统 | ⭐⭐⭐ |
| Netlink/veth | 容器网络 | ⭐⭐⭐⭐ |

## 项目结构

```
container-runtime/
├── cmd/
│   └── minicontainer/        # CLI 入口
│       └── main.go
├── pkg/
│   ├── container/            # 容器核心逻辑
│   │   ├── container.go      # 容器创建和管理
│   │   ├── namespace.go      # Namespace 隔离
│   │   ├── cgroup.go         # Cgroups 资源限制
│   │   └── exec.go           # 进程执行
│   ├── image/                # 镜像管理
│   │   ├── image.go          # 镜像操作
│   │   └── layer.go          # 分层存储
│   ├── network/              # 网络管理
│   │   ├── network.go        # 网络配置
│   │   └── bridge.go         # 网桥管理
│   └── storage/              # 存储管理
│       ├── storage.go        # 存储接口
│       └── overlay.go        # OverlayFS 实现
├── docs/                     # 项目文档
├── examples/                 # 使用示例
├── tests/                    # 测试文件
├── go.mod
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
```

## 核心概念

### 1. 容器是什么？

容器本质上是一个受限的 Linux 进程，通过以下技术实现隔离：

- **Namespace**：让进程看到独立的系统视图
- **Cgroups**：限制进程能使用的资源
- **Chroot/pivot_root**：限制进程能访问的文件系统

### 2. 容器 vs 虚拟机

| 特性 | 容器 | 虚拟机 |
|------|------|--------|
| 隔离级别 | 进程级 | 硬件级 |
| 启动时间 | 毫秒 | 秒/分钟 |
| 资源占用 | 极少 | 较多 |
| 性能 | 接近原生 | 有损耗 |

### 3. 核心系统调用

```go
// 创建新 namespace
clone(CLONE_NEWPID | CLONE_NEWNS | CLONE_NEWNET | CLONE_NEWUTS)

// 设置 cgroups
echo "256M" > /sys/fs/cgroups/minicontainer/<id>/memory.max

// 切换根文件系统
pivot_root(new_root, put_old)
```

## ⭐ 重点难点

### 1. Namespace 生命周期管理
容器退出时，需要正确清理所有 namespace 资源，避免资源泄漏。

### 2. Cgroups v1 vs v2
理解两种版本的差异和兼容性处理是实现的关键难点。

### 3. 网络命名空间配置
需要手动配置 veth pair、bridge 和 iptables 规则。

### 4. 信号处理和容器退出
正确转发信号到容器内进程，并处理僵尸进程。

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
- [Understanding Docker Container Internals](https://www.youtube.com/watch?v=sK5i-N34im8)

## 许可证

MIT License

---

**注意**：本项目仅用于学习目的，不建议在生产环境使用。生产环境请使用成熟的容器运行时如 containerd、CRI-O 或 Podman。
