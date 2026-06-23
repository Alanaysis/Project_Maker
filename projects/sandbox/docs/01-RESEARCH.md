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

### 4. cgroups (Control Groups)

cgroups 是 Linux 内核的资源管理机制，可限制一组进程的资源使用：

- **memory** - 内存限制
- **cpu** - CPU 使用限制
- **pids** - 进程数量限制
- **blkio** - 块 I/O 限制

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

## 现有沙箱方案对比

| 方案 | 层级 | 复杂度 | 安全性 |
|------|------|--------|--------|
| seccomp-bpf | 系统调用 | 低 | 中 |
| Linux namespaces | 资源隔离 | 中 | 高 |
| SELinux/AppArmor | 强制访问控制 | 高 | 高 |
| Docker/containerd | 容器 | 高 | 高 |
| gVisor | 用户态内核 | 极高 | 极高 |

## 本项目范围

本项目聚焦于 seccomp-bpf 过滤，实现：

1. **BPF 程序生成**：根据规则动态生成 BPF 字节码
2. **系统调用白名单/黑名单**：灵活的过滤策略
3. **资源限制**：通过 rlimit 限制进程资源
4. **监控统计**：收集执行统计信息
