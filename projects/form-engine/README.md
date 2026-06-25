# 表单引擎 (Form Engine)

动态表单引擎，支持验证和渲染。

## 概述

这是一个纯 TypeScript 实现的表单引擎，用于学习表单引擎架构、表单验证和动态渲染。

**核心特性**：
- Schema 驱动的表单定义
- 内置验证规则 + 自定义验证
- 条件字段显示/隐藏
- 多格式渲染（HTML、JSON、Text）
- 异步提交支持

## 架构

```
┌─────────────────────────────────────────────────────────┐
│                    表单引擎                               │
│                                                         │
│  ┌──────────┐    ┌──────────┐    ┌──────────────────┐  │
│  │  Schema   │───▶│  Engine  │───▶│    Renderer      │  │
│  │  定义     │    │  核心    │    │    渲染器        │  │
│  └──────────┘    └──────────┘    └──────────────────┘  │
│                       │                                 │
│                       ▼                                 │
│                 ┌──────────┐                            │
│                 │Validator │                            │
│                 │  验证器  │                            │
│                 └──────────┘                            │
└─────────────────────────────────────────────────────────┘
```

## 项目结构

```
form-engine/
├── src/                    # 源代码
│   ├── types.ts           # 类型定义
│   ├── validator.ts       # 验证器
│   ├── form-engine.ts     # 表单引擎核心
│   ├── renderer.ts        # 渲染器
│   └── index.ts           # 入口文件
├── tests/                  # 测试
├── examples/               # 示例
├── docs/                   # 文档
├── package.json
└── tsconfig.json
```

## 快速开始

### 安装

```bash
npm install
```

### 构建

```bash
npm run build
```

### 测试

```bash
npm test
```

### 运行示例

```bash
# 登录表单
npm run example:login

# 注册表单
npm run example:registration

# 调查问卷
npm run example:survey

# 条件字段
npm run example:conditional
```

## 基本用法

```typescript
import { FormEngine, FormRenderer, rules } from './src';

// 定义表单
const schema = {
  title: '登录',
  fields: [
    {
      name: 'username',
      type: 'text',
      label: '用户名',
      validation: [rules.required(), rules.minLength(3)]
    },
    {
      name: 'password',
      type: 'password',
      label: '密码',
      validation: [rules.required(), rules.minLength(6)]
    }
  ]
};

// 创建引擎
const engine = new FormEngine(schema);

// 注册提交
engine.onSubmit(async (values) => {
  console.log('提交:', values);
});

// 设置值
engine.setValue('username', 'alice');
engine.setValue('password', 'password123');

// 提交
await engine.submit();

// 渲染
const renderer = new FormRenderer();
const html = renderer.render(schema, engine.getState());
```

## 验证规则

```typescript
import { rules } from './src';

// 内置规则
rules.required('不能为空');
rules.minLength(3, '至少3个字符');
rules.maxLength(20, '最多20个字符');
rules.min(0, '不能小于0');
rules.max(100, '不能大于100');
rules.pattern(/^[a-z]+$/, '只能小写字母');
rules.email('邮箱格式不正确');

// 自定义规则
rules.custom(
  (value, formData) => value === formData.password,
  '密码不一致'
);
```

## 条件字段

```typescript
const schema = {
  fields: [
    { name: 'hasAddress', type: 'checkbox', label: '有地址' },
    {
      name: 'address',
      type: 'textarea',
      label: '地址',
      dependsOn: { field: 'hasAddress', value: true }
    }
  ]
};
```

## 文档

- [调研文档](docs/01-RESEARCH.md)
- [设计文档](docs/02-DESIGN.md)
- [实现记录](docs/03-IMPLEMENTATION.md)
- [测试策略](docs/04-TESTING.md)
- [开发指南](docs/05-DEVELOPMENT.md)
- [学习笔记](LEARNING_NOTES.md)

## 学习目标

- 理解表单引擎架构
- 掌握表单验证
- 学会动态渲染

## 技术栈

- TypeScript
- 无框架依赖
