# 贡献指南

感谢你对 Local LLM Engine 项目的关注！我们欢迎各种形式的贡献。

## 如何贡献

### 1. 报告问题

如果你发现了 bug 或有功能建议，请创建 Issue：

1. 使用清晰的标题
2. 详细描述问题或建议
3. 提供复现步骤（如果是 bug）
4. 包含环境信息

### 2. 提交代码

#### Fork 和 Clone

```bash
# Fork 项目到你的 GitHub 账号
# 然后 clone
git clone https://github.com/your-username/local-llm-engine.git
cd local-llm-engine
```

#### 创建分支

```bash
# 创建功能分支
git checkout -b feature/your-feature

# 或者修复分支
git checkout -b fix/your-fix
```

#### 提交更改

```bash
# 添加更改
git add .

# 提交（遵循提交规范）
git commit -m "feat: add your feature"

# 推送到你的 fork
git push origin feature/your-feature
```

#### 创建 Pull Request

1. 在 GitHub 上创建 Pull Request
2. 填写 PR 模板
3. 等待代码审查

### 3. 改进文档

- 修复错别字
- 添加示例
- 翻译文档
- 添加教程

### 4. 分享经验

- 写博客文章
- 制作视频教程
- 在社区分享

## 提交规范

使用 [Conventional Commits](https://www.conventionalcommits.org/) 规范：

```
<type>(<scope>): <subject>

<body>

<footer>
```

### 类型

- **feat**: 新功能
- **fix**: 修复 bug
- **docs**: 文档更新
- **style**: 代码格式（不影响功能）
- **refactor**: 重构
- **perf**: 性能优化
- **test**: 测试相关
- **chore**: 构建/工具相关

### 示例

```
feat(tokenizer): add SentencePiece support

- Implement SentencePiece tokenizer
- Add tests for SentencePiece
- Update documentation

Closes #123
```

```
fix(kv-cache): fix memory leak in PagedKVCache

- Fix page deallocation
- Add cleanup in destructor

Fixes #456
```

## 代码规范

### 命名规范

```cpp
// 类名: PascalCase
class GGUFLoader { };

// 函数名: snake_case
bool load_model(const std::string& path);

// 变量名: snake_case
uint32_t n_layers;

// 常量: UPPER_SNAKE_CASE
constexpr uint32_t MAX_CONTEXT = 2048;

// 成员变量: snake_case_ (带下划线后缀)
std::vector<float> keys_;
```

### 代码风格

- 使用 4 空格缩进
- 行长度限制 100 字符
- 使用有意义的变量名
- 添加必要的注释

### 注释规范

```cpp
/**
 * @brief 函数功能描述
 * @param param1 参数1描述
 * @param param2 参数2描述
 * @return 返回值描述
 */
int function(int param1, int param2);

// 单行注释
float rms = 0.0f;  // 计算 RMS 值
```

## 测试要求

### 单元测试

- 新功能必须有测试
- 测试覆盖率应保持在 80% 以上
- 测试应该是独立的、可重复的

### 测试示例

```cpp
TEST(FeatureTest, BasicFunctionality) {
    // 准备
    MyClass obj;
    obj.initialize();

    // 执行
    auto result = obj.do_something();

    // 验证
    ASSERT_EQ(result, expected);
}
```

## 文档要求

### 代码文档

- 所有公共 API 必须有文档
- 复杂算法需要解释
- 包含使用示例

### 用户文档

- 更新 README.md
- 添加使用示例
- 更新变更日志

## 开发流程

### 1. 设置开发环境

```bash
# 克隆项目
git clone https://github.com/your-username/local-llm-engine.git
cd local-llm-engine

# 构建
make debug

# 运行测试
make test
```

### 2. 开发新功能

```bash
# 创建分支
git checkout -b feature/new-feature

# 开发和测试
# ...

# 提交
git commit -m "feat: add new feature"

# 推送
git push origin feature/new-feature
```

### 3. 代码审查

- 至少需要一个审查者批准
- 所有测试必须通过
- 文档必须更新

### 4. 合并

- 使用 squash merge
- 删除功能分支

## 行为准则

### 我们的承诺

- 尊重所有贡献者
- 接受建设性批评
- 专注于对社区最有利的事情
- 对他人表示同理心

### 不可接受的行为

- 使用性暗示的语言或图像
- 恶意评论或人身攻击
- 公开或私下骚扰
- 未经许可发布他人私人信息

## 许可证

贡献即表示你同意你的贡献将在 [MIT License](LICENSE) 下许可。

## 问题？

如果你有任何问题，请：
1. 查看现有 Issue
2. 创建新 Issue
3. 在讨论区提问

感谢你的贡献！
