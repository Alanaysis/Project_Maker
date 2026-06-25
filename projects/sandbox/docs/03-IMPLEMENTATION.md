# 03 - 沙箱隔离：实现细节

## 1. seccomp BPF 实现

### BPF 指令结构

每条 BPF 指令 8 字节：

```python
class BPFInstruction:
    def __init__(self, code, jt, jf, k):
        self.code = code  # 操作码 (2 bytes)
        self.jt = jt      # 条件为真时跳转 (1 byte)
        self.jf = jf      # 条件为假时跳转 (1 byte)
        self.k = k        # 通用字段 (4 bytes)

    def to_bytes(self):
        return struct.pack("HBBI", self.code, self.jt, self.jf, self.k)
```

### BPF 操作码

```python
# 加载指令
BPF_LD = 0x00    # 加载
BPF_W = 0x00     # 字大小
BPF_ABS = 0x20   # 绝对偏移

# 跳转指令
BPF_JMP = 0x05   # 跳转
BPF_JEQ = 0x10   # 等于比较
BPF_K = 0x00     # 常量

# 返回指令
BPF_RET = 0x06   # 返回
```

### seccomp 返回值

```python
SECCOMP_RET_KILL = 0x00000000   # 杀死进程
SECCOMP_RET_TRAP = 0x00030000   # 发送 SIGSYS
SECCOMP_RET_ERRNO = 0x00050000  # 返回错误码
SECCOMP_RET_LOG = 0x00070000    # 允许但记录
SECCOMP_RET_ALLOW = 0x7FFF0000  # 允许
```

### BPF 程序生成算法

```python
def build_bpf_program(self):
    instructions = []

    # 1. 验证架构
    instructions.append(BPF_LD|BPF_W|BPF_ABS, 0, 0, 4)  # 加载 arch
    instructions.append(BPF_JMP|BPF_JEQ|BPF_K, 1, 0, AUDIT_ARCH_X86_64)
    instructions.append(BPF_RET|BPF_K, 0, 0, SECCOMP_RET_KILL)

    # 2. 加载系统调用号
    instructions.append(BPF_LD|BPF_W|BPF_ABS, 0, 0, 0)

    # 3. 规则匹配
    if mode == WHITELIST:
        # 白名单：匹配则跳转到 ALLOW
        for rule in allow_rules:
            instructions.append(BPF_JMP|BPF_JEQ|BPF_K, jump_to_allow, 0, rule.nr)
        instructions.append(BPF_RET|BPF_K, 0, 0, SECCOMP_RET_KILL)  # 默认拒绝
        instructions.append(BPF_RET|BPF_K, 0, 0, SECCOMP_RET_ALLOW) # 匹配允许
    else:
        # 黑名单：匹配则跳转到 KILL
        for rule in block_rules:
            instructions.append(BPF_JMP|BPF_JEQ|BPF_K, 0, jump_to_kill, rule.nr)
        instructions.append(BPF_RET|BPF_K, 0, 0, SECCOMP_RET_ALLOW) # 默认允许
        instructions.append(BPF_RET|BPF_K, 0, 0, SECCOMP_RET_KILL)  # 匹配拒绝

    return instructions
```

## 2. Namespace 隔离实现

### unshare 系统调用

```python
# Linux namespace 常量
CLONE_NEWNS = 0x00020000      # Mount namespace
CLONE_NEWUTS = 0x04000000     # UTS namespace
CLONE_NEWIPC = 0x08000000     # IPC namespace
CLONE_NEWUSER = 0x10000000    # User namespace
CLONE_NEWPID = 0x20000000     # PID namespace
CLONE_NEWNET = 0x40000000     # Network namespace

# 使用 ctypes 调用 unshare
libc = ctypes.CDLL(ctypes.util.find_library("c"))
ret = libc.unshare(CLONE_NEWPID | CLONE_NEWNET | CLONE_NEWNS)
```

### Namespace 创建流程

```python
def create_isolated_process(self, cmd, pid_ns=True, net_ns=True, ...):
    def child_setup():
        # 构建 flags
        flags = 0
        if pid_ns: flags |= CLONE_NEWPID
        if net_ns: flags |= CLONE_NEWNET
        if mount_ns: flags |= CLONE_NEWNS
        if uts_ns: flags |= CLONE_NEWUTS
        if ipc_ns: flags |= CLONE_NEWIPC

        # 创建 namespace
        self.unshare(flags)

        # 配置 namespace
        if uts_ns:
            self.set_hostname("sandbox")
        if net_ns:
            self.setup_loopback()

    # 使用 Popen 的 preexec_fn
    proc = subprocess.Popen(cmd, preexec_fn=child_setup)
    return proc
```

## 3. chroot 实现

### 创建 chroot 环境

```python
def create_chroot_environment(self):
    chroot_dir = tempfile.mkdtemp(prefix="sandbox_chroot_")

    # 创建目录结构
    dirs = ["bin", "sbin", "lib", "lib64", "usr", "etc",
            "tmp", "var", "proc", "sys", "dev"]
    for d in dirs:
        os.makedirs(os.path.join(chroot_dir, d), exist_ok=True)

    # 复制必要文件
    self._copy_essential_files(chroot_dir)

    return chroot_dir
```

### 复制文件和依赖

```python
def _copy_with_deps(self, src, chroot_dir):
    # 复制文件本身
    dst = os.path.join(chroot_dir, src.lstrip("/"))
    shutil.copy2(src, dst)

    # 获取并复制依赖库
    result = subprocess.run(["ldd", src], capture_output=True, text=True)
    for line in result.stdout.splitlines():
        if "=>" in line:
            lib_path = line.split("=>")[1].strip().split()[0]
            if os.path.exists(lib_path):
                lib_dst = os.path.join(chroot_dir, lib_path.lstrip("/"))
                shutil.copy2(lib_path, lib_dst)
```

### 挂载设置

```python
def setup_chroot_mounts(self, chroot_dir, read_only, tmpfs):
    # 只读挂载
    for path in read_only:
        target = os.path.join(chroot_dir, path.lstrip("/"))
        subprocess.run(["mount", "--bind", path, target])
        subprocess.run(["mount", "-o", "remount,ro", target])

    # tmpfs 挂载
    for path in tmpfs:
        target = os.path.join(chroot_dir, path.lstrip("/"))
        subprocess.run(["mount", "-t", "tmpfs", "-o", "size=64m", "tmpfs", target])
```

## 4. 资源限制实现

### rlimit 设置

```python
def apply(self, memory_limit_mb, cpu_time_limit_sec, ...):
    libc = ctypes.CDLL(ctypes.util.find_library("c"))

    # 内存限制
    if memory_limit_mb > 0:
        rl = rlimit_struct()
        rl.rlim_cur = memory_limit_mb * 1024 * 1024
        rl.rlim_max = rl.rlim_cur
        libc.setrlimit(RLIMIT_AS, ctypes.byref(rl))

    # CPU 限制
    if cpu_time_limit_sec > 0:
        rl = rlimit_struct()
        rl.rlim_cur = cpu_time_limit_sec
        rl.rlim_max = rl.rlim_cur
        libc.setrlimit(RLIMIT_CPU, ctypes.byref(rl))
```

### cgroups 设置

```python
class CgroupLimits:
    def set_memory_limit(self, limit_bytes):
        # cgroups v2
        with open(f"{self.path}/memory.max", "w") as f:
            f.write(str(limit_bytes))

    def set_cpu_limit(self, quota_us, period_us=100000):
        # cgroups v2
        with open(f"{self.path}/cpu.max", "w") as f:
            f.write(f"{quota_us} {period_us}")
```

## 5. 系统调用表

### x86_64 常用系统调用

```python
SYSCALL_TABLE = {
    "read": 0,
    "write": 1,
    "open": 2,
    "close": 3,
    "stat": 4,
    "fstat": 5,
    "mmap": 9,
    "mprotect": 10,
    "munmap": 11,
    "brk": 12,
    "clone": 56,
    "fork": 57,
    "execve": 59,
    "exit": 60,
    "kill": 62,
    "socket": 41,
    "connect": 42,
    # ... 更多系统调用
}
```

### 默认白名单

```python
DEFAULT_WHITELIST = [
    "read", "write", "close", "stat", "fstat",
    "mmap", "mprotect", "munmap", "brk",
    "access", "dup", "dup2", "getpid", "getuid",
    "exit", "exit_group", "futex", "clock_gettime",
    # ... 更多安全系统调用
]
```

### 默认黑名单

```python
DEFAULT_BLACKLIST = [
    "fork", "vfork", "clone", "execve",  # 进程创建
    "kill", "tgkill",                      # 信号发送
    "mount", "umount2", "pivot_root",      # 挂载操作
    "reboot", "kexec_load",                # 系统操作
    "ptrace",                              # 调试
    "process_vm_readv", "process_vm_writev", # 内存访问
]
```

## 6. C 语言实现细节

### BPF 程序生成

```c
// 指令构造宏
#define BPF_STMT(code, k) \
    ((struct sock_filter) { code, 0, 0, k })

#define BPF_JUMP(code, k, jt, jf) \
    ((struct sock_filter) { code, jt, jf, k })

// 白名单 BPF 代码生成
prog[0] = BPF_STMT(BPF_LD|BPF_W|BPF_ABS, offsetof(seccomp_data, arch));
prog[1] = BPF_JUMP(BPF_JMP|BPF_JEQ, AUDIT_ARCH_X86_64, 1, 0);
prog[2] = BPF_STMT(BPF_RET|BPF_K, SECCOMP_RET_KILL);
prog[3] = BPF_STMT(BPF_LD|BPF_W|BPF_ABS, offsetof(seccomp_data, nr));
// ... 规则匹配
prog[last-1] = BPF_STMT(BPF_RET|BPF_K, SECCOMP_RET_KILL);   // 默认拒绝
prog[last]   = BPF_STMT(BPF_RET|BPF_K, SECCOMP_RET_ALLOW);  // 匹配允许
```

### seccomp 安装

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

### fork/exec 模型

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

### wait4 收集统计

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

## 7. 预设配置

### 代码执行沙箱

```python
config = SandboxConfig(
    mode=SandboxMode.FULL,
    memory_limit_mb=128,          # 128MB 内存
    cpu_time_limit_sec=10,        # 10 秒 CPU 时间
    file_size_limit_mb=10,        # 10MB 文件大小
    open_files_limit=32,          # 32 个文件描述符
    process_limit=4,              # 4 个进程
    filter_mode=FilterMode.WHITELIST,
    enable_chroot=True,
    enable_pid_namespace=True,
    enable_net_namespace=False,   # 不允许网络
    timeout_sec=15,
    read_only_mounts=["/usr", "/lib", "/lib64", "/bin", "/sbin"],
    tmpfs_mounts=["/tmp", "/var/tmp"],
)
```

### 恶意代码分析

```python
config = SandboxConfig(
    mode=SandboxMode.FULL,
    memory_limit_mb=512,          # 512MB 内存
    cpu_time_limit_sec=60,        # 60 秒 CPU 时间
    file_size_limit_mb=50,        # 50MB 文件大小
    open_files_limit=128,         # 128 个文件描述符
    process_limit=32,             # 32 个进程
    filter_mode=FilterMode.BLACKLIST,
    blocked_syscalls=["reboot", "kexec_load", "mount", ...],
    enable_chroot=True,
    enable_pid_namespace=True,
    enable_net_namespace=True,    # 允许网络（监控）
    log_syscalls=True,            # 记录系统调用
    timeout_sec=120,
)
```

## 8. 编译要求

### Python 版本

- Python >= 3.8
- Linux 内核 >= 3.17
- root 权限（运行 seccomp 和 namespace 功能）

### C 版本

- Linux 内核 >= 3.17
- GCC + 标准 C 库
- 需要 `linux/seccomp.h`、`linux/filter.h` 头文件
- 需要 `linux/audit.h` 获取架构常量

```bash
gcc -Wall -Wextra -D_GNU_SOURCE -Iinclude src/sandbox.c examples/basic_whitelist.c -o basic_whitelist
```

## 9. 限制与已知问题

1. **架构绑定**：BPF 程序硬编码了 x86_64 架构检查，不支持其他架构
2. **规则数量上限**：C 版本最多 64 条规则，Python 版本无限制
3. **chroot 限制**：chroot 不是完全安全的隔离，需要配合其他机制
4. **权限要求**：seccomp 和 namespace 操作需要 root 权限
5. **资源清理**：需要确保 chroot 环境和挂载点被正确清理
