# 贡献指南

感谢您对本项目的关注！我们欢迎任何形式的贡献。

## 如何贡献

### 1. 报告问题

如果您发现了 bug 或有功能建议，请创建一个 Issue。

**Issue 模板**：

```
## 问题描述

简要描述问题或建议

## 复现步骤

1. 步骤 1
2. 步骤 2
3. 步骤 3

## 期望行为

描述您期望的行为

## 实际行为

描述实际发生的行为

## 环境信息

- 操作系统：
- GCC 版本：
- 项目版本：

## 附加信息

其他相关信息、截图等
```

### 2. 提交代码

#### 2.1 Fork 项目

1. 访问项目主页
2. 点击 "Fork" 按钮
3. 克隆您的 Fork

```bash
git clone https://github.com/YOUR_USERNAME/firewall.git
cd firewall
```

#### 2.2 创建分支

```bash
git checkout -b feature/your-feature
```

#### 2.3 修改代码

1. 遵循代码风格
2. 添加必要的注释
3. 编写测试
4. 更新文档

#### 2.4 提交更改

```bash
git add .
git commit -m "feat: add your feature"
```

#### 2.5 推送并创建 Pull Request

```bash
git push origin feature/your-feature
```

然后访问 GitHub 创建 Pull Request。

### 3. 代码风格

#### 3.1 命名规范

- **函数名**：小写下划线，如 `packet_parse`
- **变量名**：小写下划线，如 `src_ip`
- **常量名**：大写下划线，如 `MAX_RULES`
- **类型名**：小写下划线加 `_t`，如 `packet_t`

#### 3.2 代码格式

- 使用 4 空格缩进
- 函数之间空一行
- 代码块之间空一行
- 行长度不超过 100 字符

#### 3.3 注释规范

```c
/**
 * 函数功能描述
 *
 * @param 参数1 参数说明
 * @param 参数2 参数说明
 * @return 返回值说明
 */
int function_name(int param1, int param2);
```

#### 3.4 示例

```c
/**
 * 解析 IP 地址
 *
 * 将字符串形式的 IP 地址转换为网络字节序
 *
 * @param ip_str IP 地址字符串
 * @param ip 输出的网络字节序 IP 地址
 * @return 0 成功，-1 失败
 */
int parse_ip_address(const char *ip_str, uint32_t *ip) {
    struct in_addr addr;

    if (!ip_str || !ip) {
        return -1;
    }

    if (inet_pton(AF_INET, ip_str, &addr) != 1) {
        return -1;
    }

    *ip = addr.s_addr;
    return 0;
}
```

### 4. 提交规范

使用 [Conventional Commits](https://www.conventionalcommits.org/) 规范：

```
<type>(<scope>): <subject>

<body>

<footer>
```

#### 类型

- **feat**: 新功能
- **fix**: 修复 bug
- **docs**: 文档更新
- **style**: 代码格式调整（不影响功能）
- **refactor**: 代码重构
- **perf**: 性能优化
- **test**: 测试相关
- **chore**: 构建/工具相关

#### 示例

```
feat(rules): add CIDR support

- Parse CIDR notation (e.g., 192.168.1.0/24)
- Support wildcard masks
- Add tests for CIDR parsing

Closes #123
```

### 5. 测试

#### 5.1 编写测试

每个新功能都应该有对应的测试：

```c
void test_new_feature(void) {
    TEST("new_feature");

    // 测试代码
    ASSERT(result == expected, "Description");

    TEST_SUCCESS();
}
```

#### 5.2 运行测试

```bash
# 运行所有测试
make test

# 运行单个测试
./build/test_packet
```

#### 5.3 测试覆盖率

尽量提高测试覆盖率：

```bash
# 编译时添加覆盖率选项
gcc -fprofile-arcs -ftest-coverage ...

# 运行测试后生成报告
gcov src/*.c
lcov --capture --directory . --output-file coverage.info
genhtml coverage.info --output-directory coverage
```

### 6. 文档

#### 6.1 代码文档

- 所有公开函数都需要文档注释
- 复杂算法需要解释
- 重要的设计决策需要说明

#### 6.2 用户文档

- 更新 README.md
- 更新 QUICKSTART.md
- 添加使用示例

### 7. Pull Request 检查清单

提交 PR 前，请确保：

- [ ] 代码遵循项目风格
- [ ] 添加了必要的注释
- [ ] 编写了测试
- [ ] 所有测试通过
- [ ] 更新了文档
- [ ] 提交信息符合规范
- [ ] 没有编译警告
- [ ] 没有内存泄漏

### 8. 行为准则

- 尊重他人
- 接受建设性批评
- 专注于对社区最有利的事情
- 对他人表示同理心

### 9. 联系方式

如有任何问题，请通过以下方式联系：

- 创建 Issue
- 发送邮件

### 10. 致谢

感谢所有贡献者的付出！

---

**注意**：本项目是一个学习项目，我们特别欢迎：
- 学习笔记和心得
- 代码改进建议
- 文档完善
- Bug 修复
