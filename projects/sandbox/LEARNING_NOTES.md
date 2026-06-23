# 沙箱隔离 - 学习笔记

## 学习目标

1. 理解沙箱隔离的原理和必要性
2. 掌握 seccomp-bpf 系统调用过滤
3. 学会使用 rlimit 进行资源限制
4. 理解 Linux 安全机制的层级

## 核心知识点

### 1. seccomp 原理

seccomp (Secure Computing Mode) 是 Linux 内核的安全特性，用于限制进程可以执行的系统调用。

**关键概念：**
- **系统调用**：用户空间请求内核服务的接口
- **BPF**：Berkeley Packet Filter，用于编写过滤规则的字节码
- **NO_NEW_PRIVS**：防止进程通过 execve setuid 程序提升权限

**执行流程：**
```
程序代码 → glibc 封装 → 系统调用 → [seccomp BPF 过滤器] → 内核处理
```

### 2. BPF 字节码

seccomp 使用 BPF (Berkeley Packet Filter) 字节码定义过滤规则。

**基本结构：**
```c
struct sock_filter {
    __u16 code;   // 操作码
    __u8  jt;     // 条件为真时跳转
    __u8  jf;     // 条件为假时跳转
    __u32 k;      // 操作数
};
```

**核心操作码：**
- `BPF_LD | BPF_W | BPF_ABS`：从 seccomp_data 加载数据
- `BPF_JMP | BPF_JEQ`：相等比较跳转
- `BPF_RET | BPF_K`：返回指定动作

**返回值：**
- `SECCOMP_RET_ALLOW` (0x7fff0000)：允许
- `SECCOMP_RET_KILL` (0x00000000)：杀死进程
- `SECCOMP_RET_ERRNO` (0x00050000)：返回错误码
- `SECCOMP_RET_TRACE` (0x7ff00000)：通知 ptrace
- `SECCOMP_RET_LOG` (0x7ffc0000)：允许但记录
- `SECCOMP_RET_TRAP` (0x00030000)：发送 SIGSYS

### 3. 白名单 vs 黑名单

**白名单模式（默认）：**
- 只允许列出的系统调用
- 未列出的一律拒绝
- 更安全，适用于不受信任代码

**黑名单模式：**
- 阻止列出的系统调用
- 其他都允许
- 更灵活，适用于已知危险操作

### 4. 资源限制 (rlimit)

POSIX 定义的进程资源限制：

| 资源 | 说明 | 默认值 |
|------|------|--------|
| RLIMIT_FSIZE | 文件大小上限 | 无限制 |
| RLIMIT_STACK | 栈大小 | 8MB |
| RLIMIT_NOFILE | 文件描述符数 | 1024 |
| RLIMIT_NPROC | 进程数 | 4096 |
| RLIMIT_AS | 虚拟内存 | 无限制 |

### 5. 系统调用安全性

不同系统调用的风险级别：

**低风险（可安全允许）：**
- read, write, close, fstat
- getpid, getuid, getgid
- exit, exit_group

**中等风险（需要谨慎）：**
- open（可能打开敏感文件）
- mmap/mprotect（可能改变内存保护）
- ioctl（取决于设备）

**高风险（通常应阻止）：**
- fork, clone, execve（创建新进程）
- socket, connect, bind（网络访问）
- ptrace（调试其他进程）
- mount（文件系统操作）

### 6. SIGSYS 信号

当 seccomp 使用 TRAP 模式阻止系统调用时，进程收到 SIGSYS 信号。

```c
void sigsys_handler(int sig, siginfo_t *info, void *ctx) {
    int syscall_nr = info->si_syscall;
    // 可以获取被阻止的系统调用号
}
```

### 7. wait4 和 rusage

```c
struct rusage {
    struct timeval ru_utime;  // 用户态 CPU 时间
    struct timeval ru_stime;  // 内核态 CPU 时间
    long ru_maxrss;           // 峰值内存 (KB)
    // ... 其他字段
};

wait4(pid, &status, 0, &usage);
```

## 实践要点

### 1. 权限要求

- seccomp BPF 过滤器安装需要 `CAP_SYS_ADMIN` 或 `NO_NEW_PRIVS`
- 非 root 进程必须先设置 `NO_NEW_PRIVS`
- 测试通常需要 root 权限

### 2. 规则设计原则

- 最小权限：只允许必需的系统调用
- 默认拒绝：白名单模式，未列出的默认阻止
- 分层防护：seccomp + rlimit + cgroups
- 测试充分：确保目标程序能正常运行

### 3. 常见陷阱

- **遗漏必要系统调用**：程序启动时需要很多系统调用（brk, mmap, arch_prctl 等）
- **execve 忘记允许**：如果要运行外部程序，必须允许 execve
- **信号处理遗漏**：rt_sigaction, rt_sigprocmask 通常需要允许
- **线程支持**：futex 通常需要允许

### 4. strace 辅助设计

使用 strace 观察程序使用的系统调用：

```bash
# 统计系统调用
strace -c /bin/ls

# 详细跟踪
strace /bin/ls

# 只跟踪特定系统调用
strace -e trace=open,read,write /bin/ls
```

## 学习资源

- [seccomp 内核文档](https://www.kernel.org/doc/html/latest/userspace-api/seccomp_filter.html)
- [BPF 指令集参考](https://man7.org/linux/man-pages/man7/bpf-hp.7.html)
- [seccomp(2) 手册页](https://man7.org/linux/man-pages/man2/seccomp.2.html)
- [prctl(2) 手册页](https://man7.org/linux/man-pages/man2/prctl.2.html)

## 项目收获

通过本项目，学习到了：

1. **系统调用机制**：理解了用户空间和内核空间的边界
2. **BPF 字节码**：掌握了 seccomp 过滤器的编程方式
3. **安全设计**：理解了最小权限原则和纵深防御
4. **进程管理**：掌握了 fork/exec/wait 的使用
5. **资源控制**：学会了使用 rlimit 限制进程资源
