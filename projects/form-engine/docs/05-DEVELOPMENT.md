# 开发指南

## 环境要求

- Node.js >= 16
- npm >= 8

## 快速开始

### 安装依赖

```bash
cd projects/form-engine
npm install
```

### 构建项目

```bash
npm run build
```

### 运行测试

```bash
npm test
```

### 运行示例

```bash
# 登录表单示例
npm run example:login

# 注册表单示例
npm run example:registration

# 调查问卷示例
npm run example:survey

# 条件字段示例
npm run example:conditional
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
│   ├── run.ts             # 测试运行器
│   ├── test_validator.ts  # 验证器测试
│   ├── test_form_engine.ts# 引擎测试
│   ├── test_renderer.ts   # 渲染器测试
│   └── test_edge_cases.ts # 边界测试
├── examples/               # 示例
│   ├── login-form.ts      # 登录表单
│   ├── registration-form.ts# 注册表单
│   ├── survey-form.ts     # 调查问卷
│   └── conditional-fields.ts# 条件字段
├── docs/                   # 文档
│   ├── 01-RESEARCH.md     # 调研文档
│   ├── 02-DESIGN.md       # 设计文档
│   ├── 03-IMPLEMENTATION.md# 实现记录
│   ├── 04-TESTING.md      # 测试策略
│   └── 05-DEVELOPMENT.md  # 开发指南
├── package.json            # 项目配置
├── tsconfig.json           # TypeScript 配置
├── README.md               # 项目说明
└── LEARNING_NOTES.md       # 学习笔记
```

## 开发流程

### 1. 修改类型定义

如果需要添加新的字段类型或配置项，修改 `src/types.ts`。

### 2. 更新验证器

如果需要添加新的验证规则，修改 `src/validator.ts`。

### 3. 更新引擎

如果需要添加新的功能，修改 `src/form-engine.ts`。

### 4. 更新渲染器

如果需要支持新的字段类型渲染，修改 `src/renderer.ts`。

### 5. 添加测试

为新功能添加测试用例。

### 6. 更新文档

更新相关文档。

## 使用指南

### 基本用法

```typescript
import { FormEngine, FormRenderer, rules, FormSchema } from './src';

// 1. 定义表单 Schema
const schema: FormSchema = {
  title: '用户信息',
  fields: [
    {
      name: 'username',
      type: 'text',
      label: '用户名',
      validation: [
        rules.required(),
        rules.minLength(3)
      ]
    },
    {
      name: 'email',
      type: 'email',
      label: '邮箱',
      validation: [
        rules.required(),
        rules.email()
      ]
    }
  ]
};

// 2. 创建引擎实例
const engine = new FormEngine(schema);

// 3. 注册提交回调
engine.onSubmit(async (values) => {
  console.log('提交:', values);
  // 发送到服务器...
});

// 4. 设置值
engine.setValue('username', 'alice');
engine.setValue('email', 'alice@example.com');

// 5. 验证并提交
const isValid = engine.validate();
if (isValid) {
  await engine.submit();
}

// 6. 渲染
const renderer = new FormRenderer();
const html = renderer.render(schema, engine.getState());
console.log(html.content);
```

### 条件字段

```typescript
const schema: FormSchema = {
  title: '条件表单',
  fields: [
    {
      name: 'hasAddress',
      type: 'checkbox',
      label: '有地址',
      defaultValue: false
    },
    {
      name: 'address',
      type: 'textarea',
      label: '地址',
      dependsOn: {
        field: 'hasAddress',
        value: true
      }
    }
  ]
};

const engine = new FormEngine(schema);

// address 默认不可见
console.log(engine.isFieldVisible(schema.fields[1])); // false

// 设置 hasAddress = true 后 address 可见
engine.setValue('hasAddress', true);
console.log(engine.isFieldVisible(schema.fields[1])); // true
```

### 自定义验证

```typescript
// 跨字段验证：密码确认
const schema: FormSchema = {
  title: '注册',
  fields: [
    {
      name: 'password',
      type: 'password',
      label: '密码',
      validation: [rules.required(), rules.minLength(8)]
    },
    {
      name: 'confirmPassword',
      type: 'password',
      label: '确认密码',
      validation: [
        rules.required(),
        rules.custom(
          (value, formData) => value === formData?.['password'],
          '两次密码不一致'
        )
      ]
    }
  ]
};
```

### 状态监听

```typescript
const engine = new FormEngine(schema);

// 监听状态变更
engine.onStateChange((state) => {
  console.log('状态变更:', state);
});

// 监听提交
engine.onSubmit(async (values) => {
  console.log('提交:', values);
});
```

### 多格式渲染

```typescript
const renderer = new FormRenderer();
const engine = new FormEngine(schema);

// HTML
const html = renderer.render(schema, engine.getState());

// JSON
const json = renderer.renderAsJson(schema, engine.getState());

// 纯文本
const text = renderer.renderAsText(schema, engine.getState());
```

## API 参考

### FormEngine

#### 构造函数

```typescript
new FormEngine(schema: FormSchema)
```

#### 方法

| 方法 | 返回值 | 说明 |
|------|--------|------|
| `getSchema()` | `FormSchema` | 获取表单 Schema |
| `getState()` | `FormState` | 获取表单状态 |
| `getValue(name)` | `any` | 获取字段值 |
| `getValues()` | `Record<string, any>` | 获取所有值 |
| `getFieldState(name)` | `FieldState \| null` | 获取字段状态 |
| `setValue(name, value)` | `void` | 设置字段值 |
| `setTouched(name)` | `void` | 标记字段已触碰 |
| `validate()` | `boolean` | 验证表单 |
| `submit()` | `Promise<boolean>` | 提交表单 |
| `reset()` | `void` | 重置表单 |
| `onSubmit(handler)` | `void` | 注册提交回调 |
| `onStateChange(callback)` | `void` | 注册状态回调 |
| `getHandlers()` | `FormHandlers` | 获取事件处理器 |
| `isFieldVisible(field)` | `boolean` | 字段是否可见 |
| `getVisibleFields()` | `FieldSchema[]` | 获取可见字段 |

### FormRenderer

#### 方法

| 方法 | 返回值 | 说明 |
|------|--------|------|
| `render(schema, state)` | `RenderResult` | 渲染为 HTML |
| `renderAsText(schema, state)` | `RenderResult` | 渲染为文本 |
| `renderAsJson(schema, state)` | `RenderResult` | 渲染为 JSON |

### rules

| 函数 | 参数 | 说明 |
|------|------|------|
| `required(message?)` | 可选错误信息 | 必填验证 |
| `minLength(min, message?)` | 最小长度 | 长度验证 |
| `maxLength(max, message?)` | 最大长度 | 长度验证 |
| `min(min, message?)` | 最小值 | 范围验证 |
| `max(max, message?)` | 最大值 | 范围验证 |
| `pattern(regex, message)` | 正则表达式 | 模式验证 |
| `email(message?)` | 可选错误信息 | 邮箱验证 |
| `custom(validator, message)` | 验证函数 | 自定义验证 |

## 常见问题

### Q: 如何添加新的字段类型？

1. 在 `types.ts` 中添加新的 `FieldType`
2. 在 `renderer.ts` 中添加对应的渲染方法
3. 在 `validator.ts` 中添加默认值处理

### Q: 如何实现异步验证？

当前版本不支持内置异步验证，但可以在提交处理器中实现：

```typescript
engine.onSubmit(async (values) => {
  const exists = await checkUsername(values.username);
  if (exists) {
    throw new Error('用户名已存在');
  }
});
```

### Q: 如何自定义渲染？

可以通过继承 `FormRenderer` 并重写渲染方法：

```typescript
class CustomRenderer extends FormRenderer {
  renderField(field, state) {
    // 自定义渲染逻辑
  }
}
```

## 扩展方向

1. **React/Vue 组件**：将引擎封装为框架组件
2. **可视化编辑器**：拖拽式表单设计器
3. **模板系统**：支持表单模板
4. **国际化**：多语言错误信息
5. **主题系统**：自定义样式
6. **表单联动**：更复杂的字段联动
7. **异步验证**：内置异步验证支持
8. **表单持久化**：本地存储
