# 02 - 沙箱隔离：系统设计

## 架构概览

```
用户程序
    |
    v
sandbox.run()
    |
    ├── 创建 Namespace 隔离
    │   ├── PID namespace     进程 ID 隔离
    │   ├── Network namespace  网络隔离
    │   ├── Mount namespace    挂载点隔离
    │   ├── UTS namespace      主机名隔离
    │   └── IPC namespace      进程间通信隔离
    │
    ├── 创建 chroot 环境
    │   ├── 复制必要文件和库
    │   ├── 只读挂载系统目录
    │   └── tmpfs 挂载临时目录
    │
    ├── 应用资源限制
    │   ├── RLIMIT_AS          虚拟内存限制
    │   ├── RLIMIT_CPU         CPU 时间限制
    │   ├── RLIMIT_FSIZE       文件大小限制
    │   ├── RLIMIT_NOFILE      文件描述符限制
    │   └── RLIMIT_NPROC       进程数量限制
    │
    ├── 安装 seccomp 过滤器
    │   ├── 构建 BPF 程序
    │   ├── 设置 NO_NEW_PRIVS
    │   └── 安装 BPF 过滤器
    │
    └── 执行目标程序
        └── 收集统计信息
```

## 模块设计

### 1. Sandbox 核心模块 (core.py)

```python
class Sandbox:
    def __init__(self, config: SandboxConfig):
        ...

    def run(self, command: List[str]) -> SandboxResult:
        """在沙箱中执行命令"""
        ...

    def kill(self):
        """杀死沙箱中的进程"""
        ...
```

支持四种运行模式：
- **SIMPLE**：仅 seccomp + rlimit
- **CHROOT**：chroot + seccomp + rlimit
- **NAMESPACE**：namespace + seccomp + rlimit
- **FULL**：namespace + chroot + seccomp + rlimit

### 2. Namespace 隔离模块 (namespace_isolation.py)

使用 Linux namespace 实现进程隔离：

```python
class NamespaceIsolation:
    def create_namespaces(self,
                          pid_ns: bool = True,
                          net_ns: bool = True,
                          mount_ns: bool = True,
                          uts_ns: bool = True,
                          ipc_ns: bool = True):
        """创建多个 namespace"""
        ...

    def create_isolated_process(self, cmd: List[str], ...) -> Popen:
        """创建隔离的子进程"""
        ...
```

Namespace 类型：

| Namespace | 标志位 | 隔离内容 | 用途 |
|-----------|--------|----------|------|
| PID | CLONE_NEWPID | 进程 ID | 进程不可见其他进程 |
| Network | CLONE_NEWNET | 网络栈 | 独立网络接口 |
| Mount | CLONE_NEWNS | 挂载点 | 独立文件系统视图 |
| UTS | CLONE_NEWUTS | 主机名 | 独立主机名 |
| IPC | CLONE_NEWIPC | IPC 资源 | 独立消息队列/信号量 |

### 3. 文件系统隔离模块 (filesystem.py)

```python
class FilesystemIsolation:
    def create_chroot_environment(self) -> str:
        """创建 chroot 环境"""
        ...

    def setup_chroot_mounts(self, chroot_dir: str,
                            read_only: List[str],
                            tmpfs: List[str]):
        """设置挂载点"""
        ...

    def create_overlay_filesystem(self, lower_dir: str) -> str:
        """创建 overlay 文件系统"""
        ...
```

文件系统隔离策略：

```
┌─────────────────────────────────────────┐
│  Overlay 文件系统                        │
│  ┌───────────────────────────────────┐  │
│  │  Upper Layer (可写)               │  │
│  │  /tmp, /var/tmp                   │  │
│  ├───────────────────────────────────┤  │
│  │  Lower Layer (只读)               │  │
│  │  /usr, /lib, /bin, /sbin, /etc   │  │
│  └───────────────────────────────────┘  │
├─────────────────────────────────────────┤
│  tmpfs 挂载                              │
│  /tmp (64MB), /dev, /proc, /sys        │
├─────────────────────────────────────────┤
│  只读挂载                                │
│  /usr, /lib, /bin, /sbin               │
└─────────────────────────────────────────┘
```

### 4. 系统调用过滤模块 (syscall_filter.py)

```python
class SyscallFilter:
    def set_mode(self, mode: FilterMode):
        """设置过滤模式"""
        ...

    def add_allowed(self, syscall: str):
        """添加允许的系统调用"""
        ...

    def add_blocked(self, syscall: str):
        """添加阻止的系统调用"""
        ...

    def build_bpf_program(self) -> List[BPFInstruction]:
        """构建 BPF 程序"""
        ...

    def apply(self, mode, allowed, blocked):
        """应用 seccomp 过滤器"""
        ...
```

BPF 程序结构：

```
┌─────────────────────────────────┐
│  Load architecture              │  验证 x86_64
│  Check arch == AUDIT_ARCH_X86_64│
│  If mismatch → KILL             │
├─────────────────────────────────┤
│  Load syscall number            │  从 seccomp_data 加载
├─────────────────────────────────┤
│  Rule 1: compare → jump/allow   │  逐条规则匹配
│  Rule 2: compare → jump/allow   │
│  ...                            │
│  Rule N: compare → jump/allow   │
├─────────────────────────────────┤
│  Default action                 │  白名单→KILL, 黑名单→ALLOW
├─────────────────────────────────┤
│  ALLOW                          │
└─────────────────────────────────┘
```

### 5. 资源限制模块 (resource_limits.py)

```python
class ResourceLimits:
    def apply(self,
              memory_limit_mb: int,
              cpu_time_limit_sec: int,
              file_size_limit_mb: int,
              open_files_limit: int,
              process_limit: int):
        """应用资源限制"""
        ...

class CgroupLimits:
    def set_memory_limit(self, limit_bytes: int):
        """设置 cgroup 内存限制"""
        ...

    def set_cpu_limit(self, quota_us: int, period_us: int):
        """设置 cgroup CPU 限制"""
        ...
```

资源限制类型：

| 资源 | rlimit | cgroups | 说明 |
|------|--------|---------|------|
| 内存 | RLIMIT_AS | memory.max | 虚拟内存限制 |
| CPU | RLIMIT_CPU | cpu.max | CPU 时间限制 |
| 文件大小 | RLIMIT_FSIZE | - | 文件最大字节数 |
| 进程数 | RLIMIT_NPROC | pids.max | 进程数量限制 |
| 文件描述符 | RLIMIT_NOFILE | - | 打开文件数量 |

## 执行流程

### 完整模式执行流程

```
sandbox.run(command)
    │
    ├── 创建 chroot 环境
    │   ├── 创建临时目录
    │   ├── 创建目录结构
    │   ├── 复制必要文件
    │   └── 设置挂载点
    │
    ├── fork()
    │   ├── [子进程]
    │   │   ├── 创建 namespace
    │   │   │   ├── unshare(CLONE_NEWPID)
    │   │   │   ├── unshare(CLONE_NEWNET)
    │   │   │   ├── unshare(CLONE_NEWNS)
    │   │   │   ├── unshare(CLONE_NEWUTS)
    │   │   │   └── unshare(CLONE_NEWIPC)
    │   │   │
    │   │   ├── 设置主机名
    │   │   ├── 配置网络 (loopback)
    │   │   │
    │   │   ├── chroot(chroot_dir)
    │   │   │
    │   │   ├── 应用资源限制
    │   │   │   ├── setrlimit(RLIMIT_AS, ...)
    │   │   │   ├── setrlimit(RLIMIT_CPU, ...)
    │   │   │   ├── setrlimit(RLIMIT_FSIZE, ...)
    │   │   │   ├── setrlimit(RLIMIT_NOFILE, ...)
    │   │   │   └── setrlimit(RLIMIT_NPROC, ...)
    │   │   │
    │   │   ├── 安装 seccomp 过滤器
    │   │   │   ├── prctl(NO_NEW_PRIVS)
    │   │   │   └── prctl(SECCOMP, filter)
    │   │   │
    │   │   └── execvp(command)
    │   │
    │   └── [父进程]
    │       └── 等待子进程
    │
    ├── 收集统计信息
    └── 清理 chroot 环境
```

## 安全考量

### 1. 多层防御

```
┌─────────────────────────────────────────┐
│  Layer 5: 应用层限制                     │
│  超时、输出捕获、行为分析               │
├─────────────────────────────────────────┤
│  Layer 4: Namespace 隔离                │
│  PID, Network, Mount, UTS, IPC          │
├─────────────────────────────────────────┤
│  Layer 3: 文件系统隔离                   │
│  chroot, 只读挂载, tmpfs                │
├─────────────────────────────────────────┤
│  Layer 2: 系统调用过滤                   │
│  seccomp BPF 白名单/黑名单              │
├─────────────────────────────────────────┤
│  Layer 1: 资源限制                       │
│  rlimit, cgroups                         │
├─────────────────────────────────────────┤
│  Layer 0: Linux 内核                     │
└─────────────────────────────────────────┘
```

### 2. 安全原则

- **最小权限原则**：只授予完成任务所需的最少权限
- **默认拒绝**：未明确允许的操作一律拒绝
- **纵深防御**：多层安全机制叠加
- **不可逆性**：seccomp 一旦设置不可撤销

### 3. 架构验证

BPF 程序首先验证系统架构，防止 32 位绕过：

```
LD arch
JEQ arch==X86_64 ? continue : KILL
```

### 4. NO_NEW_PRIVS

防止通过 setuid 程序绕过 seccomp：

```c
prctl(PR_SET_NO_NEW_PRIVS, 1, 0, 0, 0);
```

## API 设计原则

1. **简洁**：核心 API 简单易用
2. **安全**：默认安全配置
3. **灵活**：支持多种隔离模式和配置
4. **可组合**：模块可独立使用或组合使用
5. **信息丰富**：详细统计和错误信息
