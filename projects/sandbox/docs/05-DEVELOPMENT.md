# 05 - 沙箱隔离：开发指南

## 环境要求

- Linux 内核 >= 3.17
- GCC 或 Clang
- make
- 需要 root 权限运行 seccomp 相关测试

## 快速开始

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
├── include/
│   └── sandbox.h           # 公共 API 头文件
├── src/
│   └── sandbox.c           # 核心实现
├── examples/
│   ├── basic_whitelist.c   # 基础白名单示例
│   ├── block_network.c     # 阻止网络访问示例
│   └── strict_sandbox.c    # 严格沙箱示例
├── tests/
│   └── test_sandbox.c      # 测试套件
├── docs/
│   ├── 01-RESEARCH.md      # 研究笔记
│   ├── 02-DESIGN.md        # 系统设计
│   ├── 03-IMPLEMENTATION.md# 实现细节
│   ├── 04-TESTING.md       # 测试策略
│   └── 05-DEVELOPMENT.md   # 本文件
├── Makefile
└── README.md
```

## 开发工作流

### 1. 修改代码

```bash
# 编辑头文件
vim include/sandbox.h

# 编辑实现
vim src/sandbox.c

# 编辑测试
vim tests/test_sandbox.c
```

### 2. 构建

```bash
make clean && make all
```

### 3. 测试

```bash
sudo make test
```

### 4. 运行示例

```bash
# 基础白名单模式
./build/basic_whitelist /bin/ls -la

# 阻止网络
./build/block_network /usr/bin/wget http://example.com

# 严格模式
./build/strict_sandbox /bin/cat /etc/hostname
```

## 常见问题

### Q: 测试失败，提示 "prctl(SECCOMP) failed: Operation not permitted"

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

A: 在 `examples/` 或测试代码中添加：

```c
sandbox_syscall_rule_t rule = {
    .syscall_nr = __NR_new_syscall,
    .allow = true,
    .description = "new_syscall"
};
sandbox_add_rule(ctx, &rule);
```

## 学习路径

1. **基础**：阅读 `docs/01-RESEARCH.md` 了解 seccomp 原理
2. **设计**：阅读 `docs/02-DESIGN.md` 了解架构
3. **实现**：阅读 `src/sandbox.c` 核心代码
4. **实践**：运行 `examples/` 中的示例
5. **测试**：阅读 `tests/test_sandbox.c` 了解用法
6. **扩展**：尝试添加参数级过滤或 cgroups 支持

## 扩展方向

### 1. 添加参数级过滤

```c
// 只允许 write(1, ...) - 只写标准输出
sandbox_arg_constraint_t arg0_eq_stdout = {
    .arg_index = 0,
    .op = SANDBOX_CMP_EQ,
    .value = 1,  // stdout
    .enabled = true
};
```

### 2. 集成 cgroups

```c
// 创建 cgroup
mkdir("/sys/fs/cgroup/memory/sandbox", 0755);
// 设置内存限制
write_file("/sys/fs/cgroup/memory/sandbox/memory.limit_in_bytes", "104857600");
// 将子进程加入 cgroup
write_file("/sys/fs/cgroup/memory/sandbox/cgroup.procs", child_pid);
```

### 3. 添加日志模式

使用 `SECCOMP_RET_LOG` 替代 `SECCOMP_RET_KILL`，允许记录但不阻止。
