# 沙箱隔离 (Sandbox Isolation)

一个完整的进程沙箱实现，支持 seccomp BPF 系统调用过滤、Linux namespace 隔离、chroot 文件系统隔离和资源限制。

## 项目概述

本项目实现了多层次的进程沙箱隔离机制，用于在安全的环境中运行不受信任的代码。

### 核心功能

- **进程隔离**：使用 Linux namespace（PID、Network、Mount、UTS、IPC）实现进程隔离
- **文件系统隔离**：chroot 环境、只读挂载、临时文件系统
- **系统调用过滤**：seccomp BPF 动态生成，支持白名单和黑名单模式
- **资源限制**：CPU、内存、文件大小、进程数等资源限制
- **实用场景**：代码执行沙箱、恶意代码分析

### 学习目标

- 理解 Linux 沙箱隔离的原理和机制
- 掌握 seccomp BPF 编程
- 学会使用 namespace 实现进程隔离
- 了解 chroot 和文件系统隔离
- 掌握资源限制和监控技术

## 快速开始

### Python 版本

```bash
cd projects/sandbox

# 安装依赖
pip install -e .

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

# 构建
make all

# 运行示例
./build/basic_whitelist /bin/echo "Hello from sandbox"
./build/block_network /bin/curl http://example.com
./build/strict_sandbox /bin/cat /etc/hostname

# 运行测试（需要 root 权限）
sudo make test
```

## API 参考

### Python API

```python
from sandbox import Sandbox, SandboxConfig, SandboxMode, FilterMode

# 创建配置
config = SandboxConfig(
    mode=SandboxMode.FULL,
    memory_limit_mb=256,
    cpu_time_limit_sec=30,
    filter_mode=FilterMode.WHITELIST,
    enable_chroot=True,
    enable_pid_namespace=True,
    enable_net_namespace=True,
    timeout_sec=60,
)

# 创建沙箱
sandbox = Sandbox(config)

# 执行命令
result = sandbox.run(["python3", "-c", "print('Hello')"])

# 查看结果
print(result.exit_code)
print(result.stdout)
print(result.stderr)
```

### C API

```c
#include "sandbox.h"

int main() {
    sandbox_ctx_t *ctx = sandbox_create();

    // 设置白名单模式
    sandbox_set_mode(ctx, SANDBOX_MODE_WHITELIST);

    // 添加允许的系统调用
    const int *wl = sandbox_default_whitelist();
    for (int i = 0; wl[i] != -1; i++) {
        sandbox_syscall_rule_t rule = {
            .syscall_nr = wl[i],
            .allow = true
        };
        sandbox_add_rule(ctx, &rule);
    }

    // 设置资源限制
    sandbox_rlimits_t limits = {
        .file_size_limit = 10 * 1024 * 1024,  // 10 MB
        .open_files_limit = 64
    };
    sandbox_set_rlimits(ctx, &limits);

    // 执行命令
    char *argv[] = { "/bin/echo", "Hello", NULL };
    sandbox_exec(ctx, 2, argv);

    // 等待并收集统计
    sandbox_stats_t stats;
    sandbox_wait(ctx, &stats);
    sandbox_print_stats(&stats);

    sandbox_destroy(ctx);
    return 0;
}
```

## 技术架构

```
用户程序
    |
    v
sandbox.run()
    |
    ├── 创建 Namespace 隔离
    │   ├── PID namespace   进程隔离
    │   ├── Network namespace  网络隔离
    │   ├── Mount namespace    挂载隔离
    │   ├── UTS namespace      主机名隔离
    │   └── IPC namespace      IPC 隔离
    │
    ├── 创建 chroot 环境
    │   ├── 复制必要文件
    │   ├── 只读挂载
    │   └── tmpfs 挂载
    │
    ├── 应用资源限制
    │   ├── 内存限制 (RLIMIT_AS)
    │   ├── CPU 限制 (RLIMIT_CPU)
    │   ├── 文件大小限制 (RLIMIT_FSIZE)
    │   └── 进程数限制 (RLIMIT_NPROC)
    │
    ├── 安装 seccomp 过滤器
    │   ├── 构建 BPF 程序
    │   ├── 设置 NO_NEW_PRIVS
    │   └── 安装过滤器
    │
    └── 执行目标程序
        └── 收集统计信息
```

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

## 文档

- [研究笔记](docs/01-RESEARCH.md) - Linux 沙箱技术研究
- [系统设计](docs/02-DESIGN.md) - 架构和模块设计
- [实现细节](docs/03-IMPLEMENTATION.md) - 核心实现细节
- [测试策略](docs/04-TESTING.md) - 测试方法和用例
- [开发指南](docs/05-DEVELOPMENT.md) - 构建和开发工作流

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
│   ├── 01-RESEARCH.md
│   ├── 02-DESIGN.md
│   ├── 03-IMPLEMENTATION.md
│   ├── 04-TESTING.md
│   └── 05-DEVELOPMENT.md
├── Makefile
└── README.md
```

## 环境要求

### Python 版本

- Python >= 3.8
- Linux 内核 >= 3.17
- root 权限（运行 seccomp 和 namespace 功能）

### C 版本

- Linux 内核 >= 3.17
- GCC 或 Clang
- make
- root 权限（运行 seccomp 相关功能）

## 使用场景

### 1. 代码执行沙箱

在安全环境中执行不受信任的用户代码：

```python
from sandbox import Sandbox

sandbox = Sandbox(Sandbox.get_code_execution_config())
result = sandbox.run(["python3", "user_script.py"])
```

### 2. 恶意代码分析

分析可疑代码的行为：

```python
from sandbox import Sandbox

sandbox = Sandbox(Sandbox.get_malware_analysis_config())
result = sandbox.run(["sh", "suspicious_script.sh"])
```

### 3. 自定义沙箱

根据需求自定义沙箱配置：

```python
from sandbox import Sandbox, SandboxConfig, SandboxMode

config = SandboxConfig(
    mode=SandboxMode.FULL,
    memory_limit_mb=512,
    cpu_time_limit_sec=60,
    enable_chroot=True,
    enable_pid_namespace=True,
    enable_net_namespace=False,  # 允许网络访问
)
sandbox = Sandbox(config)
result = sandbox.run(["./my_program"])
```

## 学习资源

- [seccomp 内核文档](https://www.kernel.org/doc/html/latest/userspace-api/seccomp_filter.html)
- [seccomp(2) 手册页](https://man7.org/linux/man-pages/man2/seccomp.2.html)
- [namespaces(7) 手册页](https://man7.org/linux/man-pages/man7/namespaces.7.html)
- [chroot(2) 手册页](https://man7.org/linux/man-pages/man2/chroot.2.html)
- [BPF 指令集](https://man7.org/linux/man-pages/man7/bpf-hp.7.html)
