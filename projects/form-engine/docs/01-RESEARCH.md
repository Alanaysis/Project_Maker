# 表单引擎调研

## 什么是表单引擎

表单引擎是一种能够根据配置（Schema）动态生成、验证和处理表单的系统。它将表单的结构定义与渲染逻辑分离，使得表单可以通过配置文件或 API 动态创建，而无需编写重复的 UI 代码。

## 核心概念

### 1. Schema 驱动

表单引擎的核心思想是使用 Schema（模式/模式）来描述表单结构：

```typescript
const schema = {
  title: '用户信息',
  fields: [
    { name: 'username', type: 'text', label: '用户名' },
    { name: 'email', type: 'email', label: '邮箱' }
  ]
};
```

### 2. 表单生命周期

```
表单定义 → 渲染 → 用户输入 → 验证 → 提交
```

1. **定义阶段**：创建 Schema，定义字段、验证规则
2. **渲染阶段**：根据 Schema 和状态生成 UI
3. **输入阶段**：用户填写表单，触发状态更新
4. **验证阶段**：根据规则验证输入
5. **提交阶段**：验证通过后执行提交逻辑

### 3. 状态管理

表单引擎需要管理以下状态：

- **values**：字段值
- **errors**：验证错误
- **touched**：用户是否触碰过字段
- **dirty**：字段值是否被修改
- **valid**：表单整体有效性
- **submitting**：是否正在提交

## 市场分析

### 流行表单库对比

| 库 | 特点 | 优势 | 劣势 |
|---|---|---|---|
| Formik | React 生态 | 简单易用 | 依赖 React |
| React Hook Form | 性能优化 | 高性能 | 依赖 React |
| JSON Schema Form | 标准化 | Schema 标准 | 配置复杂 |
| Ant Design Form | UI 组件 | 功能完整 | 依赖 Ant Design |
| Yup/Joi | 验证库 | 强大验证 | 仅验证 |

### 表单引擎的通用架构

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

## 验证策略

### 1. 内置验证

常见的内置验证规则：
- required：必填
- minLength/maxLength：长度限制
- min/max：数值范围
- pattern：正则表达式
- email：邮箱格式

### 2. 自定义验证

允许用户定义自己的验证逻辑：
```typescript
{
  type: 'custom',
  validator: (value, formData) => value === formData.password,
  message: '密码不一致'
}
```

### 3. 异步验证

某些验证需要后端支持：
```typescript
{
  type: 'async',
  validator: async (value) => {
    const exists = await checkUsername(value);
    return !exists;
  },
  message: '用户名已存在'
}
```

### 4. 跨字段验证

验证依赖其他字段的值：
```typescript
{
  type: 'custom',
  validator: (value, formData) => {
    return value >= formData.minAge;
  }
}
```

## 渲染策略

### 1. 声明式渲染

根据 Schema 声明式生成 UI：
```typescript
renderer.render(schema, state) → HTML
```

### 2. 多格式输出

支持多种输出格式：
- HTML：用于 Web 页面
- JSON：用于 API 传输
- Text：用于调试

### 3. 条件渲染

根据条件动态显示/隐藏字段：
```typescript
{
  name: 'address',
  dependsOn: { field: 'hasAddress', value: true }
}
```

## 学习目标

通过实现表单引擎，我们将学习：

1. **表单引擎架构**：理解 Schema 驱动的设计思想
2. **表单验证**：掌握各种验证策略的实现
3. **动态渲染**：学会根据配置动态生成 UI
4. **状态管理**：理解表单状态的生命周期
5. **类型系统**：使用 TypeScript 定义强类型接口

## 参考资源

- [Formik 文档](https://formik.org/)
- [React Hook Form 文档](https://react-hook-form.com/)
- [JSON Schema 规范](https://json-schema.org/)
- [HTML 表单元素](https://developer.mozilla.org/zh-CN/docs/Web/HTML/Element/form)
