# 05 - 沙箱隔离：开发指南

## 环境要求

### Python 版本

- Python >= 3.8
- Linux 内核 >= 3.17
- root 权限（运行 seccomp 和 namespace 功能）

### C 版本

- Linux 内核 >= 3.17
- GCC 或 Clang
- make
- root 权限运行 seccomp 相关测试

## 快速开始

### Python 版本

```bash
cd projects/sandbox

# 运行代码执行沙箱
python examples/code_execution_sandbox.py -c "print('Hello')"

# 运行恶意代码分析
python examples/malware_analysis.py -c "import os; print(os.getcwd())"

# 运行测试
python tests/test_sandbox_python.py
```

### C 版本

```bash
cd projects/sandbox

# 构建所有
make all

# 运行测试（需要 sudo）
sudo make test

# 运行示例
./build/basic_whitelist /bin/echo "Hello from sandbox"
./build/block_network /usr/bin/curl http://example.com
./build/strict_sandbox /bin/echo "Strict mode"
```

## 项目结构

```
sandbox/
├── src/
│   ├── sandbox.c              # C 核心实现（seccomp BPF）
│   └── sandbox/               # Python 模块
│       ├── __init__.py
│       ├── core.py            # 沙箱核心逻辑
│       ├── syscall_filter.py  # 系统调用过滤
│       ├── resource_limits.py # 资源限制
│       ├── filesystem.py      # 文件系统隔离
│       └── namespace_isolation.py  # Namespace 隔离
├── include/
│   └── sandbox.h              # C 头文件
├── examples/
│   ├── basic_whitelist.c      # C 示例
│   ├── block_network.c        # C 示例
│   ├── strict_sandbox.c       # C 示例
│   ├── code_execution_sandbox.py  # Python 代码执行沙箱
│   └── malware_analysis.py    # Python 恶意代码分析
├── tests/
│   ├── test_sandbox.c         # C 测试
│   └── test_sandbox_python.py # Python 测试
├── docs/
│   ├── 01-RESEARCH.md         # 研究笔记
│   ├── 02-DESIGN.md           # 系统设计
│   ├── 03-IMPLEMENTATION.md   # 实现细节
│   ├── 04-TESTING.md          # 测试策略
│   └── 05-DEVELOPMENT.md      # 本文件
├── Makefile
└── README.md
```

## 开发工作流

### Python 开发

```bash
# 编辑模块
vim src/sandbox/core.py
vim src/sandbox/syscall_filter.py

# 运行测试
python tests/test_sandbox_python.py

# 运行示例
python examples/code_execution_sandbox.py -c "print('test')"
```

### C 开发

```bash
# 编辑头文件
vim include/sandbox.h

# 编辑实现
vim src/sandbox.c

# 编辑测试
vim tests/test_sandbox.c

# 构建
make clean && make all

# 测试
sudo make test
```

## 模块说明

### 1. core.py - 沙箱核心

```python
class Sandbox:
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

### 2. syscall_filter.py - 系统调用过滤

```python
class SyscallFilter:
    def set_mode(self, mode: FilterMode):
        """设置过滤模式（白名单/黑名单）"""
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

### 3. resource_limits.py - 资源限制

```python
class ResourceLimits:
    def apply(self, memory_limit_mb, cpu_time_limit_sec, ...):
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

### 4. filesystem.py - 文件系统隔离

```python
class FilesystemIsolation:
    def create_chroot_environment(self) -> str:
        """创建 chroot 环境"""
        ...

    def setup_chroot_mounts(self, chroot_dir, read_only, tmpfs):
        """设置挂载点"""
        ...

    def create_overlay_filesystem(self, lower_dir) -> str:
        """创建 overlay 文件系统"""
        ...
```

### 5. namespace_isolation.py - Namespace 隔离

```python
class NamespaceIsolation:
    def create_namespaces(self, pid_ns, net_ns, mount_ns, ...):
        """创建多个 namespace"""
        ...

    def create_isolated_process(self, cmd, ...) -> Popen:
        """创建隔离的子进程"""
        ...

    def set_hostname(self, hostname: str):
        """设置主机名"""
        ...
```

## 添加新功能

### 添加新的系统调用

在 `syscall_filter.py` 中添加：

```python
SYSCALL_TABLE = {
    # ... 现有系统调用
    "new_syscall": 123,  # 添加新系统调用
}
```

### 添加新的资源限制

在 `resource_limits.py` 中添加：

```python
RLIMIT_NEW_RESOURCE = 16  # 新资源类型

def apply(self, ..., new_limit: int = 0):
    if new_limit > 0:
        self._set(RLIMIT_NEW_RESOURCE, new_limit)
```

### 添加新的隔离机制

在 `namespace_isolation.py` 中添加：

```python
CLONE_NEWFEATURE = 0x80000000  # 新 namespace 类型

def create_feature_namespace(self):
    """创建 feature namespace"""
    self.unshare(CLONE_NEWFEATURE)
```

## 常见问题

### Q: Python 测试失败，提示 "prctl(SECCOMP) failed: Operation not permitted"

A: 需要 root 权限。使用 `sudo python tests/test_sandbox_python.py`。

### Q: C 测试失败，提示 "prctl(SECCOMP) failed: Operation not permitted"

A: 需要 root 权限或设置 `kernel.yama.ptrace_scope=0`。使用 `sudo make test`。

### Q: 被沙箱阻止的程序显示 "Killed" 而不是友好的错误信息

A: 这是正常行为。seccomp 使用 KILL 模式直接终止进程，不产生 SIGSYS。如需友好信息，需改用 TRAP 模式。

### Q: 如何查看某个程序使用了哪些系统调用？

A: 使用 `strace` 工具：

```bash
strace -c /bin/echo test
```

这将显示所有系统调用及其调用次数，帮助你设计白名单。

### Q: 如何添加新的系统调用到白名单？

A: 在 Python 中：

```python
sandbox.config.allowed_syscalls.append("new_syscall")
```

在 C 中：

```c
sandbox_syscall_rule_t rule = {
    .syscall_nr = __NR_new_syscall,
    .allow = true,
    .description = "new_syscall"
};
sandbox_add_rule(ctx, &rule);
```

### Q: chroot 环境中的程序找不到库文件

A: 确保 `_copy_essential_files` 正确复制了所有依赖库。可以手动检查：

```bash
ldd /path/to/binary
```

然后将缺失的库复制到 chroot 环境中。

## 学习路径

1. **基础**：阅读 `docs/01-RESEARCH.md` 了解沙箱原理
2. **设计**：阅读 `docs/02-DESIGN.md` 了解架构
3. **实现**：阅读 `src/sandbox/` Python 模块代码
4. **实践**：运行 `examples/` 中的示例
5. **测试**：阅读 `tests/` 了解用法
6. **扩展**：尝试添加新的隔离机制或资源限制

## 扩展方向

### 1. 添加参数级过滤

```python
# 只允许 write(1, ...) - 只写标准输出
class ArgConstraint:
    def __init__(self, arg_index, op, value):
        self.arg_index = arg_index
        self.op = op
        self.value = value
```

### 2. 集成 cgroups v2

```python
# 创建 cgroup
os.makedirs("/sys/fs/cgroup/sandbox", exist_ok=True)

# 设置内存限制
with open("/sys/fs/cgroup/sandbox/memory.max", "w") as f:
    f.write("104857600")  # 100MB

# 将子进程加入 cgroup
with open("/sys/fs/cgroup/sandbox/cgroup.procs", "w") as f:
    f.write(str(child_pid))
```

### 3. 添加系统调用日志

使用 `SECCOMP_RET_LOG` 替代 `SECCOMP_RET_KILL`，允许记录但不阻止：

```python
SECCOMP_RET_LOG = 0x00070000

# 在 BPF 程序中使用
instructions.append(BPF_RET | BPF_K, 0, 0, SECCOMP_RET_LOG)
```

### 4. 网络隔离增强

```python
# 创建 veth 对连接到桥接网络
subprocess.run(["ip", "link", "add", "veth0", "type", "veth", "peer", "name", "veth1"])
subprocess.run(["ip", "link", "set", "veth1", "netns", str(child_pid)])
```

### 5. 资源监控增强

```python
# 使用 cgroups 监控资源使用
def get_memory_usage(self):
    with open(f"{self.path}/memory.current", "r") as f:
        return int(f.read().strip())

def get_cpu_usage(self):
    with open(f"{self.path}/cpu.stat", "r") as f:
        for line in f:
            if line.startswith("usage_usec"):
                return int(line.split()[1])
    return 0
```

## 性能优化

### 1. BPF 程序优化

- 减少规则数量
- 使用跳转表优化匹配
- 合并相似规则

### 2. chroot 环境优化

- 使用 overlay 文件系统
- 预构建 chroot 模板
- 缓存常用文件

### 3. Namespace 优化

- 复用 namespace
- 延迟创建不使用的 namespace
- 使用 user namespace 减少权限需求

## 调试技巧

### 1. 查看 seccomp 过滤器

```bash
# 查看进程的 seccomp 状态
cat /proc/<pid>/status | grep Seccomp

# 查看 seccomp 过滤器
cat /proc/<pid>/filters
```

### 2. 查看 namespace

```bash
# 查看进程的 namespace
ls -la /proc/<pid>/ns/

# 查看 namespace 详情
nsenter -t <pid> -n ip addr
```

### 3. 查看资源限制

```bash
# 查看进程的资源限制
cat /proc/<pid>/limits

# 查看 cgroup 限制
cat /sys/fs/cgroup/<name>/memory.max
cat /sys/fs/cgroup/<name>/cpu.max
```

### 4. strace 调试

```bash
# 跟踪系统调用
strace -f -e trace=network python script.py

# 统计系统调用
strace -c python script.py
```
