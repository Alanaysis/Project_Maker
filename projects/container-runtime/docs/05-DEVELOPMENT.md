# 05 - 开发手册

## 环境搭建

### 1. 系统要求

#### 操作系统
- Linux（推荐 Ubuntu 20.04+ 或 Debian 11+）
- 内核版本 >= 4.0（支持 cgroups v2）

#### 权限要求
- root 权限（操作 namespace 和 cgroups）
- 或配置适当的 capabilities

#### 依赖软件
- Go 1.21+
- Git
- Make（可选）

### 2. 开发环境配置

#### 安装 Go

```bash
# 下载 Go
wget https://go.dev/dl/go1.21.5.linux-amd64.tar.gz

# 解压
sudo tar -C /usr/local -xzf go1.21.5.linux-amd64.tar.gz

# 配置环境变量
echo 'export PATH=$PATH:/usr/local/go/bin' >> ~/.bashrc
source ~/.bashrc

# 验证安装
go version
```

#### 配置 Go 模块

```bash
# 设置 Go 代理（国内用户）
export GOPROXY=https://goproxy.cn,direct

# 启用模块
export GO111MODULE=on
```

#### 安装依赖

```bash
# 进入项目目录
cd projects/container-runtime

# 下载依赖
go mod tidy

# 或使用 Make
make deps
```

### 3. 编译和运行

#### 编译

```bash
# 使用 Go 命令
go build -o minicontainer ./cmd/minicontainer/

# 或使用 Make
make build
```

#### 运行

```bash
# 需要 root 权限
sudo ./minicontainer run --name test alpine /bin/sh

# 或使用 Make
sudo make example
```

#### 测试

```bash
# 运行所有测试
go test ./...

# 或使用 Make
make test

# 运行特定测试
go test -v ./tests/container_test.go
```

## 项目结构

```
container-runtime/
├── cmd/
│   └── minicontainer/        # CLI 入口
│       └── main.go           # 主程序
├── pkg/
│   ├── container/            # 容器核心逻辑
│   │   ├── container.go      # 容器创建和管理
│   │   ├── namespace.go      # Namespace 隔离
│   │   ├── cgroup.go         # Cgroups 资源限制
│   │   └── helper.go         # 辅助函数
│   ├── image/                # 镜像管理
│   │   └── image.go          # 镜像操作
│   ├── network/              # 网络管理
│   │   └── network.go        # 网络配置
│   └── storage/              # 存储管理
│       └── storage.go        # 存储接口
├── docs/                     # 项目文档
│   ├── 01-RESEARCH.md        # 市场调研
│   ├── 02-REQUIREMENTS.md    # 需求分析
│   ├── 03-DESIGN.md          # 技术设计
│   ├── 04-PRODUCT.md         # 产品思维
│   └── 05-DEVELOPMENT.md     # 开发手册
├── tests/                    # 测试文件
│   ├── container_test.go     # 容器测试
│   └── image_test.go         # 镜像测试
├── examples/                 # 使用示例
├── Makefile                  # 构建脚本
├── go.mod                    # Go 模块文件
└── README.md                 # 项目说明
```

## 核心模块解析

### 1. Container 模块

#### container.go

**核心功能**：
- 容器生命周期管理
- 容器状态管理
- 容器配置管理

**关键结构体**：
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
}

// Container 容器实例
type Container struct {
    Config    *ContainerConfig
    Status    ContainerStatus
    PID       int
    CreatedAt time.Time
}
```

**关键函数**：
```go
// Create 创建容器
func (m *ContainerManager) Create(config *ContainerConfig) (*Container, error)

// Start 启动容器
func (m *ContainerManager) Start(id string) error

// Stop 停止容器
func (m *ContainerManager) Stop(id string) error
```

#### namespace.go

**核心功能**：
- Namespace 创建和管理
- Mount Namespace 配置
- 根文件系统切换

**关键技术**：
```go
// clone 系统调用标志
const (
    CLONE_NEWPID  // PID 隔离
    CLONE_NEWNS   // Mount 隔离
    CLONE_NEWUTS  // UTS 隔离
    CLONE_NEWIPC  // IPC 隔离
    CLONE_NEWNET  // Network 隔离
)

// pivot_root 切换根文件系统
func setupMountNamespace(config *ContainerConfig) error {
    // 1. 重新挂载根文件系统为私有
    unix.Mount("", "/", "", unix.MS_PRIVATE|unix.MS_REC, "")

    // 2. 绑定挂载新的根文件系统
    unix.Mount(newRoot, newRoot, "", unix.MS_BIND|unix.MS_REC, "")

    // 3. 切换根文件系统
    unix.PivotRoot(newRoot, oldRoot)
}
```

#### cgroup.go

**核心功能**：
- Cgroups v2 管理
- 资源限制设置
- 资源使用统计

**关键技术**：
```go
// Cgroups v2 目录结构
/sys/fs/cgroup/
├── minicontainer/
│   ├── <container-id>/
│   │   ├── cpu.max        # CPU 限制
│   │   ├── memory.max     # 内存限制
│   │   ├── pids.max       # 进程数限制
│   │   └── cgroup.procs   # 进程列表

// 设置内存限制
func (m *CgroupManager) SetMemoryLimit(limit int64) error {
    memoryMaxPath := filepath.Join(m.Path, "memory.max")
    return os.WriteFile(memoryMaxPath, []byte(strconv.FormatInt(limit, 10)), 0644)
}
```

### 2. Image 模块

#### image.go

**核心功能**：
- 镜像拉取和存储
- 镜像配置管理
- 镜像层管理

**关键技术**：
```go
// OCI 镜像格式
type Image struct {
    ID        string        // 镜像 ID
    Name      string        // 镜像名称
    Tag       string        // 镜像标签
    Config    *ImageConfig  // 镜像配置
    Layers    []string      // 镜像层
}

type ImageConfig struct {
    OS           string   // 操作系统
    Architecture string   // 架构
    Entrypoint   []string // 入口点
    Cmd          []string // 默认命令
    Env          []string // 环境变量
}
```

### 3. Network 模块

#### network.go

**核心功能**：
- 网络命名空间配置
- veth pair 创建
- Linux bridge 管理

**关键技术**：
```go
// 网络架构
┌─────────────────────────────────────────┐
│              Linux Bridge               │
│              172.17.0.1/16              │
└───────────┬─────────────────┬───────────┘
            │                 │
    ┌───────┴───────┐ ┌───────┴───────┐
    │   veth-host   │ │   veth-host   │
    └───────────────┘ └───────────────┘
            │                 │
    ┌───────┴───────┐ ┌───────┴───────┐
    │   veth-cont   │ │   veth-cont   │
    │   172.17.0.2  │ │   172.17.0.3  │
    └───────────────┘ └───────────────┘
        Container 1       Container 2
```

### 4. Storage 模块

#### storage.go

**核心功能**：
- 分层存储管理
- OverlayFS 配置
- 容器文件系统

**关键技术**：
```go
// OverlayFS 挂载
mount -t overlay overlay \
  -o lowerdir=<image-layer>,upperdir=<container-layer>,workdir=<work-dir> \
  <merged-dir>

// 分层结构
┌─────────────────────────────────────┐
│         Container Layer (可写层)      │
├─────────────────────────────────────┤
│         Image Layer 2 (只读层)       │
├─────────────────────────────────────┤
│         Image Layer 1 (只读层)       │
└─────────────────────────────────────┘
```

## 调试技巧

### 1. 日志调试

```go
// 添加详细日志
log.Printf("Creating container with ID: %s", config.ID)
log.Printf("Setting memory limit: %d bytes", resources.MemoryLimit)
```

### 2. 系统调用跟踪

```bash
# 使用 strace 跟踪系统调用
strace -f ./minicontainer run alpine /bin/sh

# 过滤特定系统调用
strace -e trace=clone,mount,pivot_root ./minicontainer run alpine /bin/sh
```

### 3. Cgroups 调试

```bash
# 查看 cgroup 状态
cat /sys/fs/cgroup/minicontainer/<id>/memory.current
cat /sys/fs/cgroup/minicontainer/<id>/cpu.stat

# 查看进程 cgroup
cat /proc/<pid>/cgroup
```

### 4. Namespace 调试

```bash
# 查看进程 namespace
ls -la /proc/<pid>/ns/

# 查看 namespace 信息
nsenter -t <pid> -p -m -n
```

### 5. 网络调试

```bash
# 查看网桥
brctl show

# 查看 veth pair
ip link show type veth

# 查看网络命名空间
ip netns list

# 进入网络命名空间
ip netns exec <namespace> ip addr
```

## 常见问题

### 1. 权限问题

**问题**：运行时提示权限不足

**解决**：
```bash
# 使用 sudo
sudo ./minicontainer run alpine /bin/sh

# 或配置 capabilities
sudo setcap cap_sys_admin,cap_net_admin+ep ./minicontainer
```

### 2. Cgroups 问题

**问题**：cgroup 目录不存在

**解决**：
```bash
# 检查 cgroup 版本
mount -t cgroup2

# 创建 cgroup 目录
sudo mkdir -p /sys/fs/cgroup/minicontainer
```

### 3. 网络问题

**问题**：容器无法访问网络

**解决**：
```bash
# 检查 IP 转发
cat /proc/sys/net/ipv4/ip_forward

# 启用 IP 转发
echo 1 | sudo tee /proc/sys/net/ipv4/ip_forward

# 检查 iptables 规则
sudo iptables -L -n
```

### 4. 文件系统问题

**问题**：pivot_root 失败

**解决**：
```bash
# 检查挂载传播
mount --make-rprivate /

# 检查根文件系统
ls -la /var/lib/minicontainer/rootfs/
```

## 最佳实践

### 1. 代码风格

- 遵循 Go 代码规范
- 使用有意义的变量名
- 添加清晰的注释

### 2. 错误处理

- 检查所有错误返回
- 提供有用的错误信息
- 清理失败的资源

### 3. 测试策略

- 单元测试覆盖核心功能
- 集成测试验证完整流程
- 性能测试确保性能要求

### 4. 文档维护

- 及时更新文档
- 添加使用示例
- 记录设计决策

## 扩展开发

### 1. 添加新功能

```go
// 1. 定义接口
type NewFeature interface {
    DoSomething() error
}

// 2. 实现功能
type newFeatureImpl struct {
    // 配置
}

func (f *newFeatureImpl) DoSomething() error {
    // 实现
}

// 3. 集成到容器
func (c *Container) UseFeature() error {
    feature := &newFeatureImpl{}
    return feature.DoSomething()
}
```

### 2. 修改现有功能

```go
// 1. 理解现有实现
func (m *ContainerManager) Start(id string) error {
    // 现有逻辑
}

// 2. 添加新逻辑
func (m *ContainerManager) Start(id string) error {
    // 现有逻辑

    // 新增逻辑
    if err := newFeature(); err != nil {
        return err
    }

    // 继续现有逻辑
}
```

### 3. 调试新功能

```go
// 添加调试日志
log.Printf("New feature: input=%v", input)

// 添加错误检查
if err != nil {
    log.Printf("New feature error: %v", err)
    return err
}
```

## 总结

本开发手册提供了 MiniContainer 项目的完整开发指南，包括：

1. **环境搭建**：从零配置开发环境
2. **项目结构**：理解代码组织方式
3. **核心模块**：深入理解各模块实现
4. **调试技巧**：快速定位和解决问题
5. **最佳实践**：编写高质量代码
6. **扩展开发**：添加新功能

通过本手册，开发者可以快速上手项目开发，深入理解容器技术的实现原理。
