# 01 - 沙箱隔离：研究笔记

## 什么是沙箱？

沙箱（Sandbox）是一种安全机制，用于在隔离的环境中运行不受信任的代码。它限制程序可以执行的操作，防止恶意代码对系统造成损害。

### 核心概念

- **最小权限原则**：只授予程序完成任务所需的最少权限
- **纵深防御**：多层安全机制叠加
- **默认拒绝**：未明确允许的操作一律拒绝

## Linux 沙箱技术栈

### 1. seccomp (Secure Computing Mode)

seccomp 是 Linux 内核提供的系统调用过滤机制。

```
用户程序
    |
    v
glibc 封装 (如 printf, malloc)
    |
    v
系统调用 (如 write, mmap)
    |
    v
seccomp BPF 过滤器
    |
    v
内核系统调用处理
```

#### seccomp 模式

| 模式 | 说明 | 用途 |
|------|------|------|
| SECCOMP_MODE_DISABLED | 禁用 | 默认状态 |
| SECCOMP_MODE_STRICT | 严格模式 | 只允许 read/write/exit/sigreturn |
| SECCOMP_MODE_FILTER | BPF 过滤 | 自定义过滤规则（本项目使用） |

#### BPF (Berkeley Packet Filter)

seccomp 使用 BPF 字节码来定义过滤规则。每条 BPF 指令结构：

```c
struct sock_filter {
    __u16 code;   /* 操作码 */
    __u8  jt;     /* 条件为真时跳转偏移 */
    __u8  jf;     /* 条件为假时跳转偏移 */
    __u32 k;      /* 通用字段 */
};
```

关键 BPF 操作码：

- `BPF_LD | BPF_W | BPF_ABS` - 从 seccomp_data 结构加载数据
- `BPF_JMP | BPF_JEQ | K` - 等于比较
- `BPF_RET | BPF_K` - 返回指定动作

seccomp 返回值：

- `SECCOMP_RET_ALLOW` - 允许系统调用
- `SECCOMP_RET_KILL` - 杀死进程
- `SECCOMP_RET_ERRNO` - 返回错误码
- `SECCOMP_RET_TRACE` - 通知 ptrace 跟踪者
- `SECCOMP_RET_LOG` - 允许但记录日志
- `SECCOMP_RET_TRAP` - 发送 SIGSYS 信号

### 2. prctl 系统调用

```c
/* 启用 NO_NEW_PRIVS（允许非特权进程使用 seccomp） */
prctl(PR_SET_NO_NEW_PRIVS, 1, 0, 0, 0);

/* 安装 seccomp 过滤器 */
prctl(PR_SET_SECCOMP, SECCOMP_MODE_FILTER, &fprog, 0, 0);
```

### 3. 资源限制 (rlimit)

POSIX rlimit 限制进程资源使用：

| 限制 | 说明 |
|------|------|
| RLIMIT_FSIZE | 文件大小上限 |
| RLIMIT_STACK | 栈大小上限 |
| RLIMIT_NOFILE | 文件描述符数量上限 |
| RLIMIT_NPROC | 进程数量上限 |
| RLIMIT_AS | 虚拟内存大小上限 |
| RLIMIT_CPU | CPU 时间上限 |

### 4. cgroups (Control Groups)

cgroups 是 Linux 内核的资源管理机制，可限制一组进程的资源使用：

- **memory** - 内存限制
- **cpu** - CPU 使用限制
- **pids** - 进程数量限制
- **blkio** - 块 I/O 限制

#### cgroups v2

```bash
# 创建 cgroup
mkdir /sys/fs/cgroup/sandbox

# 设置内存限制
echo 104857600 > /sys/fs/cgroup/sandbox/memory.max  # 100MB

# 设置 CPU 限制
echo "100000 100000" > /sys/fs/cgroup/sandbox/cpu.max  # 100% CPU

# 设置进程数限制
echo 32 > /sys/fs/cgroup/sandbox/pids.max

# 将进程加入 cgroup
echo <pid> > /sys/fs/cgroup/sandbox/cgroup.procs
```

### 5. Linux Namespaces

Namespace 是 Linux 内核的资源隔离机制，每个 namespace 包含独立的资源视图。

| Namespace | 标志位 | 隔离内容 | 用途 |
|-----------|--------|----------|------|
| Mount | CLONE_NEWNS | 挂载点 | 独立文件系统视图 |
| UTS | CLONE_NEWUTS | 主机名 | 独立主机名 |
| IPC | CLONE_NEWIPC | IPC 资源 | 独立消息队列/信号量 |
| PID | CLONE_NEWPID | 进程 ID | 进程不可见其他进程 |
| Network | CLONE_NEWNET | 网络栈 | 独立网络接口 |
| User | CLONE_NEWUSER | 用户/组 ID | 非特权隔离 |
| Cgroup | CLONE_NEWCGROUP | cgroup 根 | 独立 cgroup 视图 |

#### unshare 系统调用

```c
#include <sched.h>

// 创建新的 namespace
unshare(CLONE_NEWPID | CLONE_NEWNET | CLONE_NEWNS);
```

#### setns 系统调用

```c
#include <sched.h>

// 进入已存在的 namespace
int fd = open("/proc/<pid>/ns/net", O_RDONLY);
setns(fd, 0);
close(fd);
```

### 6. chroot

chroot 改变进程的根目录，限制文件系统访问。

```c
#include <unistd.h>

// 创建新的根目录
mkdir("/tmp/sandbox", 0755);

// 复制必要文件
// ...

// 切换根目录
chroot("/tmp/sandbox");
chdir("/");
```

#### chroot 的局限性

- 不是完全安全的隔离机制
- root 进程可以逃逸 chroot
- 需要配合其他机制（seccomp、namespace）

### 7. Overlay 文件系统

Overlay 文件系统将多个目录合并为一个视图：

```bash
mount -t overlay overlay \
    -o lowerdir=/lower,upperdir=/upper,workdir=/work \
    /merged
```

- **lowerdir**：只读底层目录
- **upperdir**：可写上层目录
- **workdir**：工作目录

## x86_64 系统调用表（常用）

| 编号 | 名称 | 功能 | 风险 |
|------|------|------|------|
| 0 | read | 读取文件 | 低 |
| 1 | write | 写入文件 | 低 |
| 2 | open | 打开文件 | 中 |
| 3 | close | 关闭文件 | 低 |
| 9 | mmap | 内存映射 | 中 |
| 10 | mprotect | 修改内存保护 | 中 |
| 56 | clone | 创建进程 | 高 |
| 57 | fork | 创建进程 | 高 |
| 59 | execve | 执行程序 | 高 |
| 60 | exit | 退出进程 | 低 |
| 62 | kill | 发送信号 | 高 |
| 41 | socket | 创建套接字 | 高（网络） |
| 42 | connect | 连接 | 高（网络） |
| 231 | exit_group | 退出进程组 | 低 |
| 202 | futex | 快速用户空间互斥 | 低 |

## 现有沙箱方案对比

| 方案 | 层级 | 复杂度 | 安全性 | 说明 |
|------|------|--------|--------|------|
| seccomp-bpf | 系统调用 | 低 | 中 | 系统调用过滤 |
| Linux namespaces | 资源隔离 | 中 | 高 | 进程/网络/文件系统隔离 |
| chroot | 文件系统 | 低 | 低 | 根目录隔离 |
| SELinux/AppArmor | 强制访问控制 | 高 | 高 | 基于策略的访问控制 |
| Docker/containerd | 容器 | 高 | 高 | 完整容器化 |
| gVisor | 用户态内核 | 极高 | 极高 | 系统调用拦截 |
| Firejail | 沙箱 | 中 | 中 | 桌面应用沙箱 |

## 本项目实现

本项目实现了多层次的沙箱隔离：

1. **seccomp BPF 过滤**：根据规则动态生成 BPF 字节码
2. **Namespace 隔离**：PID、Network、Mount、UTS、IPC namespace
3. **chroot 文件系统隔离**：独立的根文件系统
4. **资源限制**：rlimit + cgroups
5. **监控统计**：收集执行统计信息

### 隔离层次

```
┌─────────────────────────────────────────┐
│  应用层                                  │
│  代码执行沙箱 / 恶意代码分析              │
├─────────────────────────────────────────┤
│  Namespace 隔离层                        │
│  PID / Network / Mount / UTS / IPC      │
├─────────────────────────────────────────┤
│  文件系统隔离层                          │
│  chroot / 只读挂载 / tmpfs / overlay    │
├─────────────────────────────────────────┤
│  系统调用过滤层                          │
│  seccomp BPF 白名单/黑名单              │
├─────────────────────────────────────────┤
│  资源限制层                              │
│  rlimit / cgroups                        │
├─────────────────────────────────────────┤
│  Linux 内核                              │
└─────────────────────────────────────────┘
```

## 安全考量

### 1. 最小权限原则

只授予程序完成任务所需的最少权限：
- 默认使用白名单模式
- 只允许必要的系统调用
- 限制资源使用

### 2. 纵深防御

多层安全机制叠加：
- seccomp 过滤系统调用
- namespace 隔离进程视图
- chroot 隔离文件系统
- rlimit 限制资源使用

### 3. 默认拒绝

未明确允许的操作一律拒绝：
- 白名单模式下，未列出的系统调用被阻止
- 未列出的文件路径不可访问
- 未授权的网络操作被阻止

### 4. 不可逆性

seccomp 一旦设置不可撤销：
- 不能移除已安装的过滤器
- 不能降低安全级别
- 只能添加更多限制

## 学习资源

- [seccomp 内核文档](https://www.kernel.org/doc/html/latest/userspace-api/seccomp_filter.html)
- [seccomp(2) 手册页](https://man7.org/linux/man-pages/man2/seccomp.2.html)
- [prctl(2) 手册页](https://man7.org/linux/man-pages/man2/prctl.2.html)
- [namespaces(7) 手册页](https://man7.org/linux/man-pages/man7/namespaces.7.html)
- [chroot(2) 手册页](https://man7.org/linux/man-pages/man2/chroot.2.html)
- [cgroups(7) 手册页](https://man7.org/linux/man-pages/man7/cgroups.7.html)
- [BPF 指令集](https://man7.org/linux/man-pages/man7/bpf-hp.7.html)
- [Linux 内核安全文档](https://www.kernel.org/doc/html/latest/security/)
