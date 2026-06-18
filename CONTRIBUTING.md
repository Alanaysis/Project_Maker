# 🤝 贡献指南 / Contributing Guide

[English](#english) | [中文](#中文)

---

## 中文

### 概述

感谢你对学习型项目工厂的关注！本文档将指导你如何参与贡献。

### 贡献方式

#### 1. 发布愿望

在 `WISHLIST.md` 中添加新的学习项目想法。

**步骤**：
1. 打开 `WISHLIST.md`
2. 按照模板格式添加新愿望
3. 提交更改

**愿望要求**：
- 一句话清晰描述项目
- 明确学习目标
- 标注技术栈
- 说明核心循环
- 提供参考项目
- 设置优先级

#### 2. 改进现有项目

对已实现的项目进行改进。

**可以改进的方面**：
- 修复 bug
- 完善文档
- 添加测试
- 优化代码
- 补充示例

**步骤**：
1. Fork 项目
2. 创建改进分支
3. 进行修改
4. 提交 Pull Request

#### 3. 完善模板

对项目模板提出改进建议。

**可以改进的方面**：
- 文档结构
- 检查清单
- 学习路径

### 愿望单格式规范

```markdown
### [项目名称]

**一句话描述**：用一句话说明这个项目是什么

**学习目标**：
- 目标1：理解 XXX
- 目标2：掌握 XXX
- 目标3：学会 XXX

**技术栈**：
- 主语言：Python/JS/Go/...
- 框架：...
- 其他：...

**核心循环**：
```
输入 → 处理 → 输出
```

**参考项目**：
- [项目A](...)
- [项目B](...)

**优先级**：P0/P1/P2

**预估时长**：X 小时
```

### 优先级说明

| 优先级 | 含义 | 实现顺序 |
|--------|------|----------|
| P0 | 核心基础，必须优先 | 最先实现 |
| P1 | 重要扩展，其次实现 | P0 完成后 |
| P2 | 高级进阶，最后实现 | P1 完成后 |

### 项目质量标准

每个项目必须满足：

1. **最小可执行**：可以一键运行
2. **文档完整**：包含所有必须的文档
3. **学习要素**：技术栈、重点难点、值得思考
4. **测试覆盖**：核心逻辑有测试
5. **示例可用**：包含可运行的示例

### 代码规范

#### Python

- 遵循 PEP 8
- 使用类型注解
- 编写文档字符串
- 保持函数简短（不超过 50 行）
- 变量命名清晰

#### JavaScript

- 遵循 ESLint 规则
- 使用 ES6+ 语法
- 添加 JSDoc 注释
- 保持模块化

### 提交规范

提交信息格式：

```
<类型>(<范围>): <描述>

<详细说明>

<关联 issue>
```

类型：
- `feat`: 新功能
- `fix`: 修复 bug
- `docs`: 文档更新
- `style`: 代码格式调整
- `refactor`: 重构
- `test`: 测试相关
- `chore`: 构建/工具相关

示例：
```
feat(http-basics): 添加 HTTP 客户端实现

- 实现 GET/POST 请求
- 添加请求头处理
- 支持 JSON 响应解析

Closes #123
```

### Pull Request 流程

1. **Fork 项目**
2. **创建分支**：`git checkout -b feature/xxx`
3. **进行修改**
4. **运行测试**：确保所有测试通过
5. **提交更改**：遵循提交规范
6. **推送分支**：`git push origin feature/xxx`
7. **创建 PR**：填写 PR 模板
8. **等待审核**
9. **合并代码**

### Issue 规范

#### Bug 报告

```markdown
## Bug 描述
[清晰描述 bug]

## 复现步骤
1. 步骤1
2. 步骤2
3. 步骤3

## 预期行为
[描述应该发生什么]

## 实际行为
[描述实际发生了什么]

## 环境信息
- OS: [操作系统]
- Python: [版本]
- 项目版本: [版本]

## 截图（如需要）
[截图]
```

#### 功能请求

```markdown
## 功能描述
[清晰描述想要的功能]

## 使用场景
[描述为什么需要这个功能]

## 建议实现
[如果有想法，描述如何实现]

## 替代方案
[描述其他可能的方案]
```

### 行为准则

- 尊重他人
- 建设性反馈
- 包容不同观点
- 专注于技术讨论

---

## English

### Overview

Thank you for your interest in the Learning Project Factory! This document will guide you on how to contribute.

### Ways to Contribute

#### 1. Post Wishes

Add new learning project ideas in `WISHLIST.md`.

**Steps**:
1. Open `WISHLIST.md`
2. Add new wish following the template format
3. Submit changes

**Wish Requirements**:
- One-line clear project description
- Clear learning goals
- Tech stack specified
- Core loop explained
- Reference projects provided
- Priority set

#### 2. Improve Existing Projects

Improve already implemented projects.

**Areas for Improvement**:
- Fix bugs
- Improve documentation
- Add tests
- Optimize code
- Add examples

**Steps**:
1. Fork the project
2. Create improvement branch
3. Make changes
4. Submit Pull Request

#### 3. Improve Templates

Suggest improvements to project templates.

**Areas for Improvement**:
- Document structure
- Checklists
- Learning paths

### Wishlist Format

```markdown
### [Project Name]

**One-line Description**: Describe this project in one sentence

**Learning Goals**:
- Goal 1: Understand XXX
- Goal 2: Master XXX
- Goal 3: Learn XXX

**Tech Stack**:
- Main Language: Python/JS/Go/...
- Framework: ...
- Others: ...

**Core Loop**:
```
Input → Process → Output
```

**Reference Projects**:
- [Project A](...)
- [Project B](...)

**Priority**: P0/P1/P2

**Estimated Time**: X hours
```

### Priority Levels

| Priority | Meaning | Implementation Order |
|----------|---------|---------------------|
| P0 | Core foundation, must be prioritized | Implement first |
| P1 | Important extension, implement next | After P0 |
| P2 | Advanced, implement last | After P1 |

### Code Standards

#### Python

- Follow PEP 8
- Use type hints
- Write docstrings
- Keep functions short (max 50 lines)
- Clear variable naming

#### JavaScript

- Follow ESLint rules
- Use ES6+ syntax
- Add JSDoc comments
- Keep modular

### Commit Convention

Commit message format:

```
<type>(<scope>): <description>

<detailed explanation>

<related issue>
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation update
- `style`: Code formatting
- `refactor`: Refactoring
- `test`: Test related
- `chore`: Build/tool related

### Pull Request Process

1. **Fork project**
2. **Create branch**: `git checkout -b feature/xxx`
3. **Make changes**
4. **Run tests**: Ensure all tests pass
5. **Commit changes**: Follow commit convention
6. **Push branch**: `git push origin feature/xxx`
7. **Create PR**: Fill PR template
8. **Wait for review**
9. **Merge code**

### Code of Conduct

- Respect others
- Constructive feedback
- Inclusive of different views
- Focus on technical discussion
