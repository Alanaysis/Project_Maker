# 03 - 技术设计

## 架构概览

```
┌─────────────────────────────────────────────────────────────────┐
│                      MiniContainer CLI                          │
│                     (cmd/minicontainer)                         │
├─────────────────────────────────────────────────────────────────┤
│                          核心包 (pkg/)                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │  container   │  │    image     │  │   network    │         │
│  │  容器管理     │  │   镜像管理   │  │   网络管理    │         │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘         │
│         │                 │                 │                   │
│  ┌──────┴───────┐  ┌──────┴───────┐  ┌──────┴───────┐         │
│  │  namespace   │  │    layer     │  │    bridge    │         │
│  │  命名空间     │  │   分层存储   │  │    网桥      │         │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘         │
│         │                 │                 │                   │
│  ┌──────┴───────┐  ┌──────┴───────┐  ┌──────┴───────┐         │
│  │   cgroup     │  │   storage    │  │    veth      │         │
│  │  资源限制     │  │   存储管理   │  │   虚拟网卡   │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
├─────────────────────────────────────────────────────────────────┤
│                      Linux Kernel                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │  Namespaces  │  │   Cgroups    │  │  Netlink     │         │
│  │  进程隔离     │  │   资源限制   │  │  网络配置    │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
└─────────────────────────────────────────────────────────────────┘
```

## 模块设计

### 1. Container 模块

#### 核心结构

```go
// ContainerConfig 容器配置
type ContainerConfig struct {
    ID         string          // 容器唯一标识
    Name       string          // 容器名称
    Image      string          // 镜像名称
    Command    []string        // 执行命令
    RootFS     string          // 根文件系统路径
    Namespaces []string        // 启用的命名空间
    Resources  *ResourceLimit  // 资源限制
    Env        []string        // 环境变量
    WorkDir    string          // 工作目录
    Hostname   string          // 主机名
    Mounts     []Mount         // 挂载点
}

// Container 容器实例
type Container struct {
    Config    *ContainerConfig
    Status    ContainerStatus
    PID       int
    CreatedAt time.Time
    StartedAt time.Time
    StoppedAt time.Time
    ExitCode  int
}
```

#### 容器状态机

```
                    ┌─────────────┐
                    │   Created   │
                    └──────┬──────┘
                           │
                           ▼
                    ┌─────────────┐
           ┌───────│   Running   │───────┐
           │       └──────┬──────┘       │
           │              │              │
           ▼              ▼              ▼
    ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
    │   Paused    │ │   Stopped   │ │    Error    │
    └─────────────┘ └─────────────┘ └─────────────┘
```

#### 核心接口

```go
// ContainerManager 容器管理器接口
type ContainerManager interface {
    Create(config *ContainerConfig) (*Container, error)
    Start(id string) error
    Stop(id string) error
    Delete(id string) error
    Get(id string) (*Container, error)
    List() []*Container
}
```

### 2. Namespace 模块

#### 支持的命名空间

| 命名空间 | 标志 | 隔离内容 |
|----------|------|----------|
| PID | CLONE_NEWPID | 进程 ID |
| Mount | CLONE_NEWNS | 挂载点 |
| UTS | CLONE_NEWUTS | 主机名 |
| IPC | CLONE_NEWIPC | 进程间通信 |
| Network | CLONE_NEWNET | 网络栈 |
| User | CLONE_NEWUSER | 用户和组 |
| Cgroup | CLONE_NEWCGROUP | Cgroup 根目录 |

#### 核心函数

```go
// SetupNamespaces 设置容器命名空间
func SetupNamespaces(config *ContainerConfig) error

// JoinNamespace 加入已存在的命名空间
func JoinNamespace(pid int, namespace string) error

// getNamespaceFlags 获取 clone 系统调用标志
func getNamespaceFlags(namespaces []string) uintptr
```

#### Mount Namespace 实现

```go
func setupMountNamespace(config *ContainerConfig) error {
    // 1. 重新挂载根文件系统为私有
    unix.Mount("", "/", "", unix.MS_PRIVATE|unix.MS_REC, "")

    // 2. 绑定挂载新的根文件系统
    unix.Mount(newRoot, newRoot, "", unix.MS_BIND|unix.MS_REC, "")

    // 3. 挂载 /proc, /sys, /dev
    unix.Mount("proc", procPath, "proc", 0, "")
    unix.Mount("sysfs", sysPath, "sysfs", unix.MS_RDONLY, "")
    unix.Mount("tmpfs", devPath, "tmpfs", unix.MS_NOSUID, "mode=755")

    // 4. 切换根文件系统
    unix.PivotRoot(newRoot, oldRoot)

    // 5. 卸载旧的根文件系统
    unix.Unmount("/oldroot", unix.MNT_DETACH)
}
```

### 3. Cgroups 模块

#### Cgroups v2 层级结构

```
/sys/fs/cgroup/
├── cgroup.controllers        # 可用控制器
├── cgroup.max.depth          # 最大深度
├── cgroup.procs              # 进程列表
├── minicontainer/            # 容器 cgroup
│   ├── <container-id>/
│   │   ├── cpu.max           # CPU 限制
│   │   ├── cpu.weight        # CPU 权重
│   │   ├── memory.max        # 内存限制
│   │   ├── memory.high       # 内存软限制
│   │   ├── memory.current    # 当前内存使用
│   │   ├── pids.max          # 进程数限制
│   │   ├── pids.current      # 当前进程数
│   │   ├── io.max            # I/O 限制
│   │   └── cgroup.procs      # 容器进程
│   └── ...
└── ...
```

#### 核心接口

```go
// CgroupManager cgroup 管理器
type CgroupManager struct {
    Path        string
    ContainerID string
}

// 设置资源限制
func (m *CgroupManager) SetMemoryLimit(limit int64) error
func (m *CgroupManager) SetCPULimit(percent int) error
func (m *CgroupManager) SetCPUShares(shares int) error
func (m *CgroupManager) SetPidsLimit(limit int) error

// 添加进程
func (m *CgroupManager) AddProcess(pid int) error

// 获取使用统计
func (m *CgroupManager) GetMemoryUsage() (int64, error)
func (m *CgroupManager) GetCPUUsage() (map[string]string, error)
```

#### CPU 限制实现

```go
// cpu.max 格式：$MAX $PERIOD
// 50% CPU = "50000 100000"（50ms/100ms）
func (m *CgroupManager) SetCPULimit(percent int) error {
    period := 100000  // 100ms
    quota := period * percent / 100
    cpuMax := fmt.Sprintf("%d %d", quota, period)
    return os.WriteFile(filepath.Join(m.Path, "cpu.max"), []byte(cpuMax), 0644)
}
```

### 4. Storage 模块

#### 分层存储架构

```
┌─────────────────────────────────────┐
│         Container Layer (可写层)      │
│         /var/lib/minicontainer/      │
│         containers/<id>/upper        │
├─────────────────────────────────────┤
│         Image Layer 3               │
│         /var/lib/minicontainer/      │
│         layers/layer3               │
├─────────────────────────────────────┤
│         Image Layer 2               │
│         /var/lib/minicontainer/      │
│         layers/layer2               │
├─────────────────────────────────────┤
│         Image Layer 1               │
│         /var/lib/minicontainer/      │
│         layers/layer1               │
└─────────────────────────────────────┘
```

#### OverlayFS 挂载

```go
// OverlayFS 挂载选项
// lowerdir: 只读层（镜像层）
// upperdir: 可写层（容器层）
// workdir:  工作目录
// merged:   合并视图
mount -t overlay overlay \
  -o lowerdir=<image-layer>,upperdir=<container-layer>,workdir=<work-dir> \
  <merged-dir>
```

#### 核心接口

```go
// StorageManager 存储管理器
type StorageManager struct {
    RootDir     string
    ImageLayers map[string]*ImageLayer
    Containers  map[string]*ContainerStorage
}

// 镜像层操作
func (m *StorageManager) CreateLayer(id, parentID string) (*ImageLayer, error)
func (m *StorageManager) DeleteLayer(id string) error
func (m *StorageManager) GetLayer(id string) (*ImageLayer, error)

// 容器存储操作
func (m *StorageManager) CreateContainerStorage(containerID, imageLayerID string) (*ContainerStorage, error)
func (m *StorageManager) MountContainer(containerID string) error
func (m *StorageManager) UnmountContainer(containerID string) error
func (m *StorageManager) GetRootFS(containerID string) (string, error)
```

### 5. Network 模块

#### 网络架构

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

#### 核心接口

```go
// NetworkManager 网络管理器
type NetworkManager struct {
    BridgeName string
    Subnet     *net.IPNet
    Gateway    net.IP
    IPPool     *IPPool
}

// 网络操作
func (m *NetworkManager) CreateNetwork(containerID string) (*ContainerNetwork, error)
func (m *NetworkManager) SetupContainerNetwork(containerID string, pid int) error
func (m *NetworkManager) DeleteNetwork(containerID string) error

// IP 池操作
func (p *IPPool) Allocate() (net.IP, error)
func (p *IPPool) Release(ip net.IP)
```

## 数据流

### 容器创建流程

```
1. 用户请求
   ↓
2. 解析配置
   ↓
3. 创建容器对象
   ↓
4. 创建存储层
   ↓
5. 准备根文件系统
   ↓
6. 返回容器 ID
```

### 容器启动流程

```
1. 用户请求启动
   ↓
2. 创建 cgroup
   ↓
3. 设置资源限制
   ↓
4. 创建新进程（clone）
   ↓
5. 设置 namespace
   │
   ├─→ PID namespace
   ├─→ Mount namespace
   ├─→ UTS namespace
   ├─→ IPC namespace
   └─→ Network namespace
   ↓
6. 配置网络
   │
   ├─→ 创建 veth pair
   ├─→ 连接网桥
   └─→ 配置 IP
   ↓
7. 切换根文件系统
   │
   ├─→ pivot_root
   └─→ 卸载旧根
   ↓
8. 执行用户命令
   ↓
9. 等待容器退出
   ↓
10. 清理资源
```

## 错误处理

### 错误类型

```go
// 容器错误类型
type ContainerError struct {
    Code    ErrorCode
    Message string
    Cause   error
}

// 错误码
const (
    ErrContainerNotFound ErrorCode = iota
    ErrContainerAlreadyExists
    ErrContainerRunning
    ErrContainerNotRunning
    ErrNamespaceSetupFailed
    ErrCgroupSetupFailed
    ErrNetworkSetupFailed
    ErrStorageSetupFailed
)
```

### 错误恢复

```go
// 容器启动失败时的清理
func (m *ContainerManager) Start(id string) error {
    // 1. 创建 cgroup
    if err := setupCgroup(...); err != nil {
        return err
    }

    // 2. 启动进程
    if err := cmd.Start(); err != nil {
        cleanupCgroup(...)  // 清理 cgroup
        return err
    }

    // 3. 异步等待退出
    go func() {
        cmd.Wait()
        cleanupCgroup(...)  // 清理 cgroup
    }()

    return nil
}
```

## 性能优化

### 1. 启动优化
- 预创建 namespace
- 缓存 cgroup 配置
- 并行化初始化

### 2. 内存优化
- 复用缓冲区
- 延迟初始化
- 及时释放资源

### 3. 网络优化
- 连接池
- 批量操作
- 异步配置

## 安全考虑

### 1. 权限控制
- 最小权限原则
- Capabilities 限制
- Seccomp 过滤

### 2. 资源限制
- 防止资源耗尽
- 防止逃逸攻击
- 防止信息泄露

### 3. 输入验证
- 参数校验
- 路径检查
- 格式验证

## 扩展点

### 1. 存储驱动
- 支持多种存储后端
- 可插拔的存储接口

### 2. 网络插件
- 支持 CNI 插件
- 可扩展的网络模式

### 3. 日志驱动
- 支持多种日志格式
- 可配置的日志级别

## 总结

MiniContainer 的设计遵循以下原则：

1. **模块化**：清晰的模块边界，便于理解和扩展
2. **简单性**：核心功能简单实现，避免过度设计
3. **可学习性**：代码清晰，注释完整，便于学习
4. **可扩展性**：预留扩展点，支持后续增强

通过这个设计，用户可以深入理解容器技术的各个组件，为学习更复杂的容器系统打下基础。
