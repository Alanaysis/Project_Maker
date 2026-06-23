# 04 - 沙箱隔离：测试策略

## 测试层级

### 1. 单元测试

测试各个 API 函数的正确性：

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

### 2. 集成测试

测试完整的沙箱执行流程：

| 测试用例 | 描述 | 预期结果 |
|----------|------|----------|
| test_whitelist_exec_echo | 白名单模式运行 echo | 正常退出，状态码 0 |
| test_whitelist_block_fork | 白名单阻止 fork | 被阻止，非零退出 |
| test_resource_limits | 资源限制生效 | echo 正常运行 |
| test_stats_collection | 统计数据收集 | PID/内存/CPU 时间正确 |

### 3. 安全测试

验证沙箱的安全性：

| 测试用例 | 描述 | 预期结果 |
|----------|------|----------|
| 被阻止的系统调用 | 尝试被阻止的操作 | 进程被终止 |
| 资源限制突破 | 尝试超出资源限制 | 操作被拒绝 |
| 逃逸尝试 | 尝试绕过沙箱 | 失败 |

## 运行测试

```bash
# 编译并运行所有测试
make test

# 如果需要 sudo（seccomp 需要特定权限）
sudo make test

# 只编译测试
make build/test_sandbox

# 手动运行
sudo ./build/test_sandbox
```

## 测试注意事项

1. **需要 root 权限**：seccomp BPF 过滤器安装需要适当的权限
2. **内核版本**：需要 Linux >= 3.17 支持 seccomp
3. **测试隔离**：每个测试独立运行，不影响其他测试
4. **超时**：被阻止的进程会被内核杀死，不会无限等待

## 测试框架

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
