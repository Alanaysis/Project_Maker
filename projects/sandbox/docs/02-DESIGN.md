# 02 - 沙箱隔离：系统设计

## 架构概览

```
                     用户空间
                         |
                    sandbox_exec()
                         |
                    ┌────┴────┐
                    │  fork() │
                    └────┬────┘
                    ┌────┴────┐
           父进程   │         │   子进程
                    │         │
              wait4()    apply_rlimits()
                    │         │
                    │    apply_seccomp()
                    │         │
                    │    execvp(target)
                    │         │
              收集统计   执行受限程序
```

## 模块设计

### 1. 上下文管理模块

```c
sandbox_ctx_t *sandbox_create(void);    // 创建上下文
void sandbox_destroy(sandbox_ctx_t *);  // 销毁上下文
```

上下文存储：
- 工作模式（白名单/黑名单）
- 系统调用规则数组
- 资源限制配置
- 子进程 PID
- 执行统计

### 2. BPF 代码生成模块

核心函数：`build_bpf_program()`

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

白名单模式 BPF 伪代码：

```
L1: LD arch
L2: JEQ arch==X86_64 ? L4 : L3
L3: RET KILL
L4: LD syscall_nr
L5: JEQ nr==rule1 ? ALLOW : L6
L6: JEQ nr==rule2 ? ALLOW : L7
L7: JEQ nr==rule3 ? ALLOW : ...
LN: RET KILL        ; default: block
LN+1: RET ALLOW     ; matched rule
```

### 3. 系统调用过滤模块

支持两种模式：

**白名单模式**：
- 只有明确列出的系统调用被允许
- 未列出的系统调用一律阻止
- 适用于：高安全场景，不受信任代码

**黑名单模式**：
- 明确列出的系统调用被阻止
- 其他系统调用允许执行
- 适用于：低风险限制，已知危险操作过滤

### 4. 资源限制模块

通过 POSIX `setrlimit()` 实现：

```c
struct rlimit {
    rlim_t rlim_cur;  /* 当前限制（软限制） */
    rlim_t rlim_max;  /* 最大限制（硬限制） */
};
```

限制类型映射：

| sandbox_rlimits_t 字段 | rlimit 资源 | 说明 |
|------------------------|-------------|------|
| file_size_limit | RLIMIT_FSIZE | 文件最大字节数 |
| stack_size_limit | RLIMIT_STACK | 栈最大字节数 |
| open_files_limit | RLIMIT_NOFILE | 文件描述符上限 |
| pids_max | RLIMIT_NPROC | 进程数量上限 |

### 5. 监控统计模块

通过 `wait4()` + `struct rusage` 收集：

```c
sandbox_stats_t {
    pid_t child_pid;           // 子进程 PID
    int exit_status;           // 退出码
    int exit_signal;           // 终止信号
    bool exited_normally;      // 是否正常退出
    uint64_t memory_peak_bytes;// 峰值内存 (ru_maxrss)
    uint64_t cpu_time_user_us; // 用户态 CPU 时间
    uint64_t cpu_time_sys_us;  // 内核态 CPU 时间
};
```

## API 设计原则

1. **简洁**：核心 API 只有 6 个函数
2. **安全**：默认白名单模式，默认拒绝
3. **灵活**：支持白名单/黑名单/参数约束
4. **可组合**：规则可任意组合
5. **信息丰富**：详细统计和错误信息

## 执行流程详细设计

```
sandbox_exec(ctx, argc, argv)
    │
    ├── fork()
    │   ├── [子进程]
    │   │   ├── apply_rlimits()
    │   │   │   ├── setrlimit(RLIMIT_FSIZE, ...)
    │   │   │   ├── setrlimit(RLIMIT_STACK, ...)
    │   │   │   ├── setrlimit(RLIMIT_NOFILE, ...)
    │   │   │   └── setrlimit(RLIMIT_NPROC, ...)
    │   │   │
    │   │   ├── install_sigsys_handler()
    │   │   │
    │   │   ├── apply_seccomp()
    │   │   │   ├── prctl(NO_NEW_PRIVS)
    │   │   │   ├── build_bpf_program()
    │   │   │   └── prctl(SECCOMP, filter)
    │   │   │
    │   │   └── execvp(target_program)
    │   │
    │   └── [父进程]
    │       └── return (保存 child_pid)
    │
sandbox_wait(ctx, stats)
    │
    ├── wait4(child_pid, &status, 0, &usage)
    ├── 解析 status → exit_status / exit_signal
    └── 解析 usage → cpu_time / memory_peak
```

## 安全考量

1. **架构验证**：BPF 程序首先验证系统架构，防止 32 位绕过
2. **NO_NEW_PRIVS**：防止通过 setuid 程序绕过 seccomp
3. **限制顺序**：先设置 rlimit，再安装 seccomp（seccomp 不可逆）
4. **资源限制不可绕过**：rlimit 由内核强制执行
