# 04 - 沙箱隔离：测试策略

## 测试层级

### 1. 单元测试 (Python)

| 测试类 | 测试内容 | 描述 |
|--------|----------|------|
| TestSandboxConfig | 配置创建 | 测试默认配置、预设配置 |
| TestSyscallFilter | 系统调用过滤 | 测试过滤器、BPF 程序构建 |
| TestResourceLimits | 资源限制 | 测试 rlimit 设置 |
| TestCgroupLimits | cgroups 限制 | 测试 cgroup 创建和配置 |
| TestFilesystemIsolation | 文件系统隔离 | 测试 chroot 环境创建 |
| TestNamespaceIsolation | Namespace 隔离 | 测试 namespace 创建 |
| TestSandboxResult | 结果对象 | 测试结果序列化 |
| TestSandboxExecution | 沙箱执行 | 测试完整执行流程 |
| TestSandboxIntegration | 集成测试 | 测试端到端功能 |

### 2. 单元测试 (C)

| 测试用例 | 描述 | 验证内容 |
|----------|------|----------|
| test_create_destroy | 创建/销毁上下文 | 内存分配正确 |
| test_create_multiple | 创建多个上下文 | 上下文独立 |
| test_set_mode | 设置工作模式 | 模式切换正确 |
| test_set_mode_null | NULL 上下文处理 | 边界条件 |
| test_add_rules | 添加规则 | 规则存储正确 |
| test_add_rule_null | NULL 上下文处理 | 边界条件 |
| test_add_too_many_rules | 超过规则上限 | 容量限制 |
| test_set_rlimits | 设置资源限制 | 限制存储正确 |
| test_syscall_name | 系统调用名称查找 | 名称映射正确 |
| test_default_whitelist | 默认白名单 | 包含安全系统调用 |
| test_exec_null | NULL 上下文 exec | 边界条件 |
| test_wait_null | NULL 上下文 wait | 边界条件 |
| test_print_stats_null | NULL 统计打印 | 不崩溃 |

### 3. 集成测试

| 测试用例 | 描述 | 预期结果 |
|----------|------|----------|
| test_whitelist_exec_echo | 白名单模式运行 echo | 正常退出，状态码 0 |
| test_whitelist_block_fork | 白名单阻止 fork | 被阻止，非零退出 |
| test_resource_limits | 资源限制生效 | echo 正常运行 |
| test_stats_collection | 统计数据收集 | PID/内存/CPU 时间正确 |
| test_simple_echo | 简单模式执行 echo | 正常执行 |
| test_timeout | 超时测试 | 进程被终止 |
| test_error_handling | 错误处理 | 优雅处理错误 |

### 4. 安全测试

| 测试用例 | 描述 | 预期结果 |
|----------|------|----------|
| 被阻止的系统调用 | 尝试被阻止的操作 | 进程被终止 |
| 资源限制突破 | 尝试超出资源限制 | 操作被拒绝 |
| 逃逸尝试 | 尝试绕过沙箱 | 失败 |
| chroot 逃逸 | 尝试逃逸 chroot | 失败 |
| namespace 逃逸 | 尝试逃逸 namespace | 失败 |

## 运行测试

### Python 测试

```bash
cd projects/sandbox

# 运行所有 Python 测试
python tests/test_sandbox_python.py

# 运行特定测试类
python -m unittest tests.test_sandbox_python.TestSandboxConfig

# 运行特定测试方法
python -m unittest tests.test_sandbox_python.TestSandboxConfig.test_default_config

# 详细输出
python tests/test_sandbox_python.py -v
```

### C 测试

```bash
cd projects/sandbox

# 编译并运行所有测试
make test

# 如果需要 sudo（seccomp 需要特定权限）
sudo make test

# 只编译测试
make build/test_sandbox

# 手动运行
sudo ./build/test_sandbox
```

## 测试用例详情

### Python 测试用例

#### TestSandboxConfig

```python
def test_default_config(self):
    """测试默认配置"""
    config = SandboxConfig()
    self.assertEqual(config.mode, SandboxMode.FULL)
    self.assertEqual(config.memory_limit_mb, 256)
    self.assertEqual(config.filter_mode, FilterMode.WHITELIST)

def test_code_execution_config(self):
    """测试代码执行配置"""
    config = Sandbox.get_code_execution_config()
    self.assertEqual(config.memory_limit_mb, 128)
    self.assertFalse(config.enable_net_namespace)

def test_malware_analysis_config(self):
    """测试恶意代码分析配置"""
    config = Sandbox.get_malware_analysis_config()
    self.assertEqual(config.filter_mode, FilterMode.BLACKLIST)
    self.assertTrue(config.log_syscalls)
```

#### TestSyscallFilter

```python
def test_syscall_table(self):
    """测试系统调用表"""
    self.assertIn("read", SYSCALL_TABLE)
    self.assertEqual(SYSCALL_TABLE["read"], 0)

def test_build_bpf_whitelist(self):
    """测试构建白名单 BPF 程序"""
    f = SyscallFilter()
    f.set_mode(FilterMode.WHITELIST)
    f.add_allowed("read")
    f.add_allowed("write")
    bpf = f.build_bpf_program()
    self.assertGreater(len(bpf), 0)

def test_build_bpf_blacklist(self):
    """测试构建黑名单 BPF 程序"""
    f = SyscallFilter()
    f.set_mode(FilterMode.BLACKLIST)
    f.add_blocked("fork")
    bpf = f.build_bpf_program()
    self.assertGreater(len(bpf), 0)
```

#### TestSandboxExecution

```python
def test_simple_echo(self):
    """测试简单 echo 命令"""
    config = SandboxConfig(
        mode=SandboxMode.SIMPLE,
        command=["echo", "hello"],
        timeout_sec=5,
    )
    sandbox = Sandbox(config)
    result = sandbox.run()
    self.assertIsNotNone(result)

def test_timeout(self):
    """测试超时"""
    config = SandboxConfig(
        mode=SandboxMode.SIMPLE,
        command=["sleep", "10"],
        timeout_sec=1,
    )
    sandbox = Sandbox(config)
    result = sandbox.run()
    self.assertTrue(result.timed_out)
```

## 测试注意事项

1. **需要 root 权限**：seccomp BPF 过滤器安装和 namespace 操作需要适当的权限
2. **内核版本**：需要 Linux >= 3.17 支持 seccomp
3. **测试隔离**：每个测试独立运行，不影响其他测试
4. **超时**：被阻止的进程会被内核杀死，不会无限等待
5. **清理**：测试会自动清理临时文件和 chroot 环境

## 测试框架

### Python 测试框架

使用标准库 `unittest`：

```python
import unittest

class TestSandbox(unittest.TestCase):
    def test_example(self):
        """测试示例"""
        self.assertEqual(1 + 1, 2)

    def setUp(self):
        """测试前准备"""
        pass

    def tearDown(self):
        """测试后清理"""
        pass
```

### C 测试框架

使用轻量级自定义测试框架，无外部依赖：

```c
static int tests_run = 0;
static int tests_passed = 0;
static int tests_failed = 0;

#define TEST_START(name)  /* 开始测试 */
#define TEST_PASS()       /* 测试通过 */
#define TEST_FAIL(msg)    /* 测试失败 */
#define ASSERT(cond, msg) /* 断言 */
```

测试输出格式：

```
[TEST 1] create and destroy sandbox ... PASS
[TEST 2] create multiple sandboxes ... PASS
...
=== Results ===
Total:  18
Passed: 18
Failed: 0
```

## 覆盖率目标

- API 函数覆盖率：100%
- 边界条件覆盖：NULL 指针、空数组、超限
- 错误路径覆盖：fork 失败、exec 失败、wait 失败
- 安全覆盖：各种逃逸尝试

## 持续集成

建议的 CI 流程：

```yaml
test:
  script:
    # Python 测试
    - python tests/test_sandbox_python.py
    # C 测试
    - make all
    - sudo make test
```

## 测试数据

### 测试脚本

创建测试用的脚本文件：

```python
# test_script.py
print("Hello from sandbox")
import os
print(f"PID: {os.getpid()}")
```

```bash
# test_script.sh
#!/bin/bash
echo "Hello from sandbox"
whoami
```

### 恶意测试代码

用于安全测试的代码：

```python
# 尝试文件系统访问
import os
try:
    os.listdir("/etc/shadow")
except PermissionError:
    print("Access denied")

# 尝试网络访问
import socket
try:
    s = socket.socket()
    s.connect(("example.com", 80))
except:
    print("Network blocked")
```
