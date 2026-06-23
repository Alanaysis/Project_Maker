# 沙箱隔离 (Sandbox Isolation)

一个基于 seccomp-bpf 的进程沙箱实现，支持系统调用过滤和资源限制。

## 项目概述

本项目实现了一个轻量级的进程沙箱，通过 Linux 内核的 seccomp 机制过滤系统调用，结合 POSIX rlimit 资源限制，为运行不受信任的代码提供安全隔离环境。

### 核心功能

- **seccomp BPF 过滤**：动态生成 BPF 字节码，过滤系统调用
- **白名单/黑名单模式**：灵活的过滤策略
- **资源限制**：通过 rlimit 限制文件大小、内存、进程数等
- **执行监控**：收集子进程的 CPU 时间、内存使用等统计信息

### 学习目标

- 理解沙箱隔离的原理
- 掌握 seccomp-bpf 编程
- 学会使用 rlimit 进行资源限制

## 快速开始

### 构建

```bash
cd projects/sandbox
make all
```

### 运行示例

```bash
# 基础白名单模式
./build/basic_whitelist /bin/echo "Hello from sandbox"

# 阻止网络访问
./build/block_network /bin/curl http://example.com

# 严格沙箱模式
./build/strict_sandbox /bin/cat /etc/hostname
```

### 运行测试

```bash
# 需要 root 权限
sudo make test
```

## API 参考

### 核心函数

```c
// 创建/销毁沙箱上下文
sandbox_ctx_t *sandbox_create(void);
void sandbox_destroy(sandbox_ctx_t *ctx);

// 设置工作模式
int sandbox_set_mode(sandbox_ctx_t *ctx, sandbox_mode_t mode);

// 添加系统调用规则
int sandbox_add_rule(sandbox_ctx_t *ctx, const sandbox_syscall_rule_t *rule);

// 设置资源限制
int sandbox_set_rlimits(sandbox_ctx_t *ctx, const sandbox_rlimits_t *limits);

// 执行命令
int sandbox_exec(sandbox_ctx_t *ctx, int argc, char *const argv[]);

// 等待完成并收集统计
int sandbox_wait(sandbox_ctx_t *ctx, sandbox_stats_t *stats);
```

### 使用示例

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
sandbox_exec()
    |
    ├── 子进程
    │   ├── apply_rlimits()   设置资源限制
    │   ├── apply_seccomp()   安装 BPF 过滤器
    │   └── execvp()          执行目标程序
    │
    └── 父进程
        └── wait4()           收集统计信息
```

### seccomp BPF 过滤器结构

```
┌─────────────────────────────────┐
│  验证架构 (x86_64)             │
├─────────────────────────────────┤
│  加载系统调用号                 │
├─────────────────────────────────┤
│  规则 1: 匹配 → 允许/拒绝     │
│  规则 2: 匹配 → 允许/拒绝     │
│  ...                            │
│  规则 N: 匹配 → 允许/拒绝     │
├─────────────────────────────────┤
│  默认动作                       │
└─────────────────────────────────┘
```

## 文档

- [研究笔记](docs/01-RESEARCH.md) - seccomp 和沙箱技术研究
- [系统设计](docs/02-DESIGN.md) - 架构和模块设计
- [实现细节](docs/03-IMPLEMENTATION.md) - BPF 代码生成等实现细节
- [测试策略](docs/04-TESTING.md) - 测试方法和用例
- [开发指南](docs/05-DEVELOPMENT.md) - 构建和开发工作流

## 项目结构

```
sandbox/
├── include/
│   └── sandbox.h           # 公共 API
├── src/
│   └── sandbox.c           # 核心实现
├── examples/
│   ├── basic_whitelist.c   # 基础白名单示例
│   ├── block_network.c     # 阻止网络示例
│   └── strict_sandbox.c    # 严格沙箱示例
├── tests/
│   └── test_sandbox.c      # 测试套件
├── docs/
│   ├── 01-RESEARCH.md      # 研究笔记
│   ├── 02-DESIGN.md        # 系统设计
│   ├── 03-IMPLEMENTATION.md# 实现细节
│   ├── 04-TESTING.md       # 测试策略
│   └── 05-DEVELOPMENT.md   # 开发指南
├── Makefile
└── README.md
```

## 环境要求

- Linux 内核 >= 3.17
- GCC 或 Clang
- make
- root 权限（运行 seccomp 相关功能）

## 学习资源

- [seccomp 内核文档](https://www.kernel.org/doc/html/latest/userspace-api/seccomp_filter.html)
- [seccomp(2) 手册页](https://man7.org/linux/man-pages/man2/seccomp.2.html)
- [prctl(2) 手册页](https://man7.org/linux/man-pages/man2/prctl.2.html)
- [BPF 指令集](https://man7.org/linux/man-pages/man7/bpf-hp.7.html)
