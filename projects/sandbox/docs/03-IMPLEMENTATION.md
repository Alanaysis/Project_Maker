# 03 - 沙箱隔离：实现细节

## BPF 程序生成

### 指令构造宏

```c
/* 普通指令 */
#define BPF_STMT(code, k) \
    ((struct sock_filter) { code, 0, 0, k })

/* 条件跳转指令 */
#define BPF_JUMP(code, k, jt, jf) \
    ((struct sock_filter) { code, jt, jf, k })
```

### 白名单 BPF 代码生成

```c
// 1. 加载架构验证
prog[0] = BPF_STMT(BPF_LD|BPF_W|BPF_ABS, offsetof(seccomp_data, arch));
prog[1] = BPF_JUMP(BPF_JMP|BPF_JEQ, AUDIT_ARCH_X86_64, 1, 0);
prog[2] = BPF_STMT(BPF_RET|BPF_K, SECCOMP_RET_KILL);

// 2. 加载系统调用号
prog[3] = BPF_STMT(BPF_LD|BPF_W|BPF_ABS, offsetof(seccomp_data, nr));

// 3. 规则匹配（跳转到 ALLOW 或下一个规则）
prog[4] = BPF_JUMP(BPF_JMP|BPF_JEQ, __NR_read, N, 0);  // N = 到 ALLOW 的距离
prog[5] = BPF_JUMP(BPF_JMP|BPF_JEQ, __NR_write, N-1, 0);
// ...

// 4. 默认动作 + ALLOW
prog[last-1] = BPF_STMT(BPF_RET|BPF_K, SECCOMP_RET_KILL);   // 默认拒绝
prog[last]   = BPF_STMT(BPF_RET|BPF_K, SECCOMP_RET_ALLOW);  // 匹配允许
```

### 跳转距离计算

白名单模式下，允许规则需要跳转到末尾的 ALLOW 指令：

```
jump_distance = total_rules - current_rule_index + 1
```

## seccomp 安装

```c
static int apply_seccomp(sandbox_ctx_t *ctx) {
    struct sock_filter *prog = build_bpf_program(ctx, &len);
    struct sock_fprog fprog = { .len = len, .filter = prog };

    // 必须先设置 NO_NEW_PRIVS
    prctl(PR_SET_NO_NEW_PRIVS, 1, 0, 0, 0);

    // 安装过滤器
    prctl(PR_SET_SECCOMP, SECCOMP_MODE_FILTER, &fprog, 0, 0);

    free(prog);
    return 0;
}
```

### NO_NEW_PRIVS 的必要性

没有 NO_NEW_PRIVS，非 root 进程无法使用 seccomp。即使有 root 权限，也建议设置此标志，防止 setuid 程序绕过过滤。

## SIGSYS 信号处理

当 seccomp 使用 TRAP 或 KILL 模式时，被阻止的系统调用会产生 SIGSYS 信号。我们可以安装信号处理器来提供更友好的错误信息：

```c
static void sigsys_handler(int sig, siginfo_t *info, void *ucontext) {
    int syscall_nr = info->si_syscall;
    fprintf(stderr, "[SANDBOX BLOCKED] syscall: %s (%d)\n",
            sandbox_syscall_name(syscall_nr), syscall_nr);
    _exit(128 + sig);
}
```

## 资源限制实现

```c
static int apply_rlimits(sandbox_ctx_t *ctx) {
    if (lim->file_size_limit > 0) {
        struct rlimit rl = {
            .rlim_cur = lim->file_size_limit,
            .rlim_max = lim->file_size_limit
        };
        setrlimit(RLIMIT_FSIZE, &rl);
    }
    // 类似地设置其他限制...
}
```

## fork/exec 模型

```c
int sandbox_exec(sandbox_ctx_t *ctx, int argc, char *const argv[]) {
    pid_t pid = fork();

    if (pid == 0) {
        // 子进程：应用限制 → 安装 seccomp → exec
        apply_rlimits(ctx);
        apply_seccomp(ctx);
        execvp(argv[0], argv);
        _exit(127);
    }

    // 父进程：保存子进程 PID
    ctx->child_pid = pid;
    return 0;
}
```

## wait4 收集统计

```c
int sandbox_wait(sandbox_ctx_t *ctx, sandbox_stats_t *stats) {
    int status;
    struct rusage usage;

    wait4(ctx->child_pid, &status, 0, &usage);

    // CPU 时间
    stats->cpu_time_user_us = usage.ru_utime.tv_sec * 1000000 + usage.ru_utime.tv_usec;
    stats->cpu_time_sys_us  = usage.ru_stime.tv_sec * 1000000 + usage.ru_stime.tv_usec;

    // 峰值内存 (ru_maxrss 单位是 KB)
    stats->memory_peak_bytes = usage.ru_maxrss * 1024;

    // 退出状态
    if (WIFEXITED(status)) {
        stats->exited_normally = true;
        stats->exit_status = WEXITSTATUS(status);
    } else if (WIFSIGNALED(status)) {
        stats->exited_normally = false;
        stats->exit_signal = WTERMSIG(status);
    }
}
```

## 编译要求

- Linux 内核 >= 3.17（seccomp 支持）
- GCC + 标准 C 库
- 需要 `linux/seccomp.h`、`linux/filter.h` 头文件
- 需要 `linux/audit.h` 获取架构常量

```bash
gcc -Wall -Wextra -D_GNU_SOURCE -Iinclude src/sandbox.c examples/basic_whitelist.c -o basic_whitelist
```

## 限制与已知问题

1. **架构绑定**：BPF 程序硬编码了 x86_64 架构检查，不支持其他架构
2. **规则数量上限**：最多 64 条规则，受 BPF 指令数限制
3. **无参数过滤**：当前版本只按系统调用号过滤，不支持参数级过滤
4. **无 cgroups**：当前只用 rlimit，未实现 cgroups 资源限制
5. **无命名空间隔离**：未使用 Linux namespaces
