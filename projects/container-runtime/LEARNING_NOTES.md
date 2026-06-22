# 学习笔记

## 项目概述

**项目名称**：MiniContainer - 轻量级容器运行时

**学习目标**：
- 理解 Linux namespace 和 cgroups
- 掌握容器镜像格式和分层存储
- 学会容器网络和存储管理

**技术栈**：
- 主语言：Go
- 框架：无（从零实现）
- 其他：Linux kernel features

---

## 学习路径

### 阶段 1：基础知识

#### 1.1 Linux Namespace

**什么是 Namespace？**
Namespace 是 Linux 内核提供的资源隔离机制，让进程看到独立的系统视图。

**Namespace 类型**：
| 类型 | 标志 | 隔离内容 |
|------|------|----------|
| PID | CLONE_NEWPID | 进程 ID |
| Mount | CLONE_NEWNS | 挂载点 |
| UTS | CLONE_NEWUTS | 主机名 |
| IPC | CLONE_NEWIPC | 进程间通信 |
| Network | CLONE_NEWNET | 网络栈 |
| User | CLONE_NEWUSER | 用户和组 |
| Cgroup | CLONE_NEWCGROUP | Cgroup 根目录 |

**核心系统调用**：
```go
// 创建新进程并设置 namespace
clone(CLONE_NEWPID | CLONE_NEWNS | CLONE_NEWNET | CLONE_NEWUTS)

// 加入已存在的 namespace
setns(fd, nstype)

// 创建新的 namespace
unshare(flags)
```

**学习笔记**：
- [ ] 理解 PID namespace 的作用
- [ ] 理解 Mount namespace 的作用
- [ ] 理解 Network namespace 的作用
- [ ] 掌握 clone() 系统调用的使用
- [ ] 掌握 pivot_root() 的使用

#### 1.2 Cgroups

**什么是 Cgroups？**
Cgroups (Control Groups) 是 Linux 内核提供的资源限制机制。

**Cgroups v2 目录结构**：
```
/sys/fs/cgroup/
├── cgroup.controllers        # 可用控制器
├── cgroup.procs              # 进程列表
├── minicontainer/            # 容器 cgroup
│   ├── <container-id>/
│   │   ├── cpu.max           # CPU 限制
│   │   ├── memory.max        # 内存限制
│   │   ├── pids.max          # 进程数限制
│   │   └── cgroup.procs      # 容器进程
│   └── ...
└── ...
```

**核心概念**：
- **CPU 限制**：使用 CFS 配额（cpu.max）
- **内存限制**：设置内存上限（memory.max）
- **进程数限制**：防止 fork 炸弹（pids.max）

**学习笔记**：
- [ ] 理解 cgroups v1 和 v2 的区别
- [ ] 掌握 CPU 限制的实现
- [ ] 掌握内存限制的实现
- [ ] 理解进程数限制的作用
- [ ] 掌握 cgroup 的创建和管理

#### 1.3 容器文件系统

**分层存储**：
容器使用分层存储，底层是只读的镜像层，上层是可写的容器层。

**OverlayFS**：
```
mount -t overlay overlay \
  -o lowerdir=<image-layer>,upperdir=<container-layer>,workdir=<work-dir> \
  <merged-dir>
```

**学习笔记**：
- [ ] 理解分层存储的原理
- [ ] 掌握 OverlayFS 的使用
- [ ] 理解 pivot_root() 的作用
- [ ] 掌握容器文件系统的配置

---

### 阶段 2：核心实现

#### 2.1 容器创建

**创建流程**：
1. 解析容器配置
2. 创建容器对象
3. 创建存储层
4. 准备根文件系统
5. 返回容器 ID

**关键代码**：
```go
func (m *ContainerManager) Create(config *ContainerConfig) (*Container, error) {
    // 1. 生成容器 ID
    config.ID = generateID()

    // 2. 创建容器目录
    containerDir := filepath.Join(m.RootDir, config.ID)
    os.MkdirAll(containerDir, 0755)

    // 3. 创建容器实例
    container := &Container{
        Config:    config,
        Status:    StatusCreated,
        CreatedAt: time.Now(),
    }

    return container, nil
}
```

**学习笔记**：
- [ ] 理解容器创建的流程
- [ ] 掌握容器配置的管理
- [ ] 理解容器状态的转换

#### 2.2 容器启动

**启动流程**：
1. 创建 cgroup
2. 设置资源限制
3. 创建新进程（clone）
4. 设置 namespace
5. 配置网络
6. 切换根文件系统
7. 执行用户命令

**关键代码**：
```go
func (m *ContainerManager) Start(id string) error {
    // 1. 创建 cgroup
    setupCgroup(container.Config.ID, container.Config.Resources)

    // 2. 设置 namespace 标志
    nsFlags := getNamespaceFlags(container.Config.Namespaces)

    // 3. 创建新进程
    cmd := exec.Command("/proc/self/exe", args...)
    cmd.SysProcAttr = &syscall.SysProcAttr{
        Cloneflags: nsFlags,
    }

    // 4. 启动进程
    cmd.Start()

    return nil
}
```

**学习笔记**：
- [ ] 理解容器启动的流程
- [ ] 掌握 clone() 系统调用的使用
- [ ] 理解 namespace 的设置过程
- [ ] 掌握 cgroup 的配置方法

#### 2.3 容器停止

**停止流程**：
1. 发送 SIGTERM 信号
2. 等待容器退出
3. 如果超时，发送 SIGKILL
4. 清理 cgroup
5. 更新容器状态

**关键代码**：
```go
func (m *ContainerManager) Stop(id string) error {
    // 1. 发送 SIGTERM
    container.cmd.Process.Signal(syscall.SIGTERM)

    // 2. 等待退出
    select {
    case <-done:
        // 容器已退出
    case <-time.After(10 * time.Second):
        // 超时，强制杀死
        container.cmd.Process.Signal(syscall.SIGKILL)
    }

    // 3. 清理 cgroup
    cleanupCgroup(container.Config.ID)

    return nil
}
```

**学习笔记**：
- [ ] 理解容器停止的流程
- [ ] 掌握信号处理的方法
- [ ] 理解资源清理的重要性

---

### 阶段 3：高级特性

#### 3.1 容器网络

**网络架构**：
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

**配置步骤**：
1. 创建 Linux bridge
2. 创建 veth pair
3. 将一端放入容器网络命名空间
4. 配置容器端 IP 和路由
5. 将另一端连接到网桥

**学习笔记**：
- [ ] 理解容器网络的架构
- [ ] 掌握 veth pair 的创建
- [ ] 理解 Linux bridge 的配置
- [ ] 掌握网络命名空间的配置

#### 3.2 镜像管理

**OCI 镜像格式**：
```
manifest.json    # 镜像清单
config.json      # 镜像配置
layer.tar.gz     # 镜像层
```

**镜像拉取流程**：
1. 解析镜像名称
2. 获取认证信息
3. 获取镜像清单
4. 下载镜像层
5. 验证摘要
6. 保存到本地存储

**学习笔记**：
- [ ] 理解 OCI 镜像规范
- [ ] 掌握镜像拉取的流程
- [ ] 理解分层存储的原理
- [ ] 掌握镜像配置的管理

---

## 重点难点

### ⭐ 1. Namespace 生命周期管理

**难点**：
容器退出时，需要正确清理所有 namespace 资源，避免资源泄漏。

**解决方案**：
```go
// 异步等待容器退出
go func() {
    err := cmd.Wait()

    // 清理资源
    cleanupCgroup(container.Config.ID)

    // 更新状态
    container.Status = StatusStopped
}()
```

**学习笔记**：
- [ ] 理解 namespace 的生命周期
- [ ] 掌握资源清理的方法
- [ ] 理解异步处理的重要性

### ⭐ 2. Cgroups v1 vs v2

**难点**：
理解两种版本的差异和兼容性处理。

**区别**：
| 特性 | v1 | v2 |
|------|-----|-----|
| 层级结构 | 多层级 | 统一层级 |
| 控制器 | 独立挂载 | 统一挂载 |
| 进程归属 | 可在多个 cgroup | 只在一个 cgroup |
| 线程支持 | 有限 | 完整 |

**学习笔记**：
- [ ] 理解 v1 和 v2 的区别
- [ ] 掌握 v2 的使用方法
- [ ] 理解兼容性处理

### ⭐ 3. 网络命名空间配置

**难点**：
需要手动配置 veth pair、bridge 和 iptables 规则。

**解决方案**：
```go
// 1. 创建 veth pair
veth := &netlink.Veth{
    LinkAttrs: netlink.LinkAttrs{
        Name: "veth-host",
    },
    PeerName: "veth-cont",
}
netlink.LinkAdd(veth)

// 2. 将容器端移动到容器网络命名空间
netlink.LinkSetNsFd(peerLink, int(ns))

// 3. 将主机端连接到网桥
netlink.LinkSetMaster(hostLink, bridge)

// 4. 配置容器端 IP 和路由
netlink.AddrAdd(contLink, addr)
netlink.RouteAdd(route)
```

**学习笔记**：
- [ ] 理解 veth pair 的工作原理
- [ ] 掌握 Linux bridge 的配置
- [ ] 理解网络命名空间的配置
- [ ] 掌握路由和 iptables 的配置

### ⭐ 4. 信号处理和容器退出

**难点**：
正确转发信号到容器内进程，并处理僵尸进程。

**解决方案**：
```go
// 发送 SIGTERM 信号
container.cmd.Process.Signal(syscall.SIGTERM)

// 等待容器退出
select {
case <-done:
    // 容器已退出
case <-time.After(10 * time.Second):
    // 超时，强制杀死
    container.cmd.Process.Signal(syscall.SIGKILL)
}
```

**学习笔记**：
- [ ] 理解信号处理机制
- [ ] 掌握信号转发的方法
- [ ] 理解僵尸进程的处理

---

## 值得思考

### 💡 1. 为什么 Docker 选择用 Go 而不是 C 实现？

**思考**：
- Go 有垃圾回收，减少内存泄漏风险
- Go 的并发模型适合容器管理
- Go 的标准库丰富，减少依赖
- Go 的编译速度快，便于开发
- Go 的跨平台支持好

**学习笔记**：
- [ ] 理解语言选择的考虑因素
- [ ] 掌握 Go 的优势和劣势
- [ ] 理解容器运行时的需求

### 💡 2. OCI 标准化对容器生态有什么意义？

**思考**：
- 统一了容器格式和运行时接口
- 促进了容器技术的互操作性
- 推动了容器生态的发展
- 降低了厂商锁定的风险

**学习笔记**：
- [ ] 理解 OCI 标准的内容
- [ ] 掌握 OCI 的实现方式
- [ ] 理解标准化的意义

### 💡 3. 容器逃逸是如何发生的？如何防御？

**思考**：
- 内核漏洞利用
- 配置错误（特权容器）
- 卷挂载不当
- 网络配置问题

**防御措施**：
- 使用非特权容器
- 限制 capabilities
- 使用 seccomp 过滤
- 定期更新内核

**学习笔记**：
- [ ] 理解容器逃逸的原理
- [ ] 掌握防御措施
- [ ] 理解安全最佳实践

### 💡 4. cgroups v2 相比 v1 有什么改进？

**思考**：
- 统一层级结构，简化管理
- 支持线程级控制
- 改进资源分配算法
- 更好的资源统计

**学习笔记**：
- [ ] 理解 v1 的问题
- [ ] 掌握 v2 的改进
- [ ] 理解迁移策略

### 💡 5. 如何实现容器的热迁移？

**思考**：
- 使用 CRIU (Checkpoint/Restore In Userspace)
- 保存容器状态
- 传输到目标主机
- 恢复容器状态

**学习笔记**：
- [ ] 理解热迁移的原理
- [ ] 掌握 CRIU 的使用
- [ ] 理解状态保存和恢复

---

## 实践记录

### 实验 1：运行第一个容器

**目标**：运行一个简单的容器，观察行为

**步骤**：
1. 编译项目
2. 运行容器
3. 观察容器行为
4. 查看系统状态

**结果**：
```
$ sudo ./minicontainer run --name test alpine /bin/sh
容器 abc123 已启动

# 在容器内
/ # ps aux
PID   USER     TIME  COMMAND
    1 root      0:00 /bin/sh
    2 root      0:00 ps aux

/ # hostname
test

/ # exit
```

**学习笔记**：
- [ ] 观察 PID namespace 的隔离效果
- [ ] 观察 UTS namespace 的隔离效果
- [ ] 理解容器退出的处理

### 实验 2：限制容器资源

**目标**：限制容器的 CPU 和内存使用

**步骤**：
1. 创建资源限制配置
2. 运行容器
3. 查看 cgroup 状态
4. 测试资源限制

**结果**：
```
$ sudo ./minicontainer run --name test --memory 256m --cpu 50 alpine /bin/sh

# 查看 cgroup 状态
$ cat /sys/fs/cgroup/minicontainer/<id>/memory.max
268435456

$ cat /sys/fs/cgroup/minicontainer/<id>/cpu.max
50000 100000
```

**学习笔记**：
- [ ] 观察内存限制的效果
- [ ] 观察 CPU 限制的效果
- [ ] 理解 cgroup 的配置

### 实验 3：配置容器网络

**目标**：配置容器网络，实现网络隔离

**步骤**：
1. 创建网络配置
2. 运行容器
3. 查看网络状态
4. 测试网络连接

**结果**：
```
$ sudo ./minicontainer run --name test alpine /bin/sh

# 查看网络状态
/ # ip addr
1: lo: <LOOPBACK,UP,LOWER_UP> mtu 65536 qdisc noqueue state UNKNOWN
    inet 127.0.0.1/8 scope host lo
2: eth0@if10: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc noqueue state UP
    inet 172.17.0.2/16 scope global eth0

/ # ping 172.17.0.1
PING 172.17.0.1 (172.17.0.1): 56 data bytes
64 bytes from 172.17.0.1: seq=0 ttl=64 time=0.123 ms
```

**学习笔记**：
- [ ] 观察网络命名空间的隔离效果
- [ ] 理解 veth pair 的工作原理
- [ ] 掌握网络配置的方法

---

## 总结

通过 MiniContainer 项目的学习，我深入理解了：

1. **Linux Namespace**：进程隔离的核心机制
2. **Cgroups**：资源限制的核心机制
3. **容器文件系统**：分层存储和 OverlayFS
4. **容器网络**：veth pair 和 Linux bridge
5. **容器生命周期**：创建、启动、停止、删除

这些知识为深入学习容器技术打下了坚实的基础。

---

**下一步学习计划**：
- [ ] 阅读 OCI 规范文档
- [ ] 研究 runc 源码
- [ ] 学习 containerd 架构
- [ ] 了解 Kubernetes 容器运行时接口
