# 学习笔记 - 表单引擎实现

## 学到了什么

### 1. Schema 驱动设计

表单引擎的核心思想是使用 Schema（模式）来描述表单结构，而不是硬编码。这种方式有以下优势：

**声明式**：Schema 描述"是什么"而不是"怎么做"
```typescript
const schema = {
  title: '用户信息',
  fields: [
    { name: 'username', type: 'text', label: '用户名' }
  ]
};
```

**可配置**：可以从 JSON 文件或 API 加载 Schema
**可序列化**：Schema 可以保存、传输、复用

**关键理解**：Schema 驱动是一种常见的设计模式，不仅用于表单，还用于 UI 组件、API 定义等。

### 2. 表单状态管理

表单需要管理多种状态：

```typescript
interface FormState {
  values: Record<string, any>;      // 字段值
  errors: Record<string, FieldError[]>; // 错误信息
  touched: Record<string, boolean>; // 是否触碰过
  dirty: Record<string, boolean>;   // 是否修改过
  valid: boolean;                   // 整体有效性
  submitting: boolean;              // 提交中
  submitted: boolean;               // 已提交
}
```

**touched vs dirty**：
- `touched`：用户是否触碰过字段（focus 后 blur）
- `dirty`：字段值是否与初始值不同

**为什么要区分**：
- touched 用于决定是否显示错误信息
- dirty 用于决定是否显示"未保存"提示

### 3. 验证策略

表单验证有多种策略：

**即时验证**：输入时立即验证
```typescript
setValue(name, value) {
  // 更新值后立即验证
  const result = validateField(value, field.validation);
  this.state.errors[name] = result.errors;
}
```

**失焦验证**：离开字段时验证
```typescript
setTouched(name) {
  this.state.touched[name] = true;
  // 可以选择在此时验证
}
```

**提交验证**：提交时验证所有字段
```typescript
submit() {
  // 先验证所有字段
  if (!this.validate()) return false;
  // 再提交
}
```

**关键理解**：不同场景需要不同的验证时机，好的表单引擎应该支持灵活配置。

### 4. 跨字段验证

某些验证需要依赖其他字段的值：

```typescript
// 密码确认
rules.custom(
  (value, formData) => value === formData.password,
  '两次密码不一致'
)
```

**实现方式**：
- 自定义验证器接收 `formData` 参数
- 可以访问其他字段的值

**关键理解**：验证器需要有上下文感知能力。

### 5. 条件字段

字段可以根据其他字段的值动态显示/隐藏：

```typescript
{
  name: 'address',
  dependsOn: {
    field: 'hasAddress',
    value: true
  }
}
```

**实现方式**：
```typescript
isFieldVisible(field) {
  if (!field.dependsOn) return true;
  return this.state.values[field.dependsOn.field] === field.dependsOn.value;
}
```

**关键理解**：条件渲染是表单引擎的重要特性，使得表单更加灵活。

### 6. 渲染与逻辑分离

表单引擎将渲染逻辑与业务逻辑分离：

```
FormEngine  → 管理状态、验证、提交
FormRenderer → 根据状态生成 UI
```

**好处**：
- 可以有多种渲染器（HTML、JSON、Text）
- 业务逻辑可以复用
- 更容易测试

**关键理解**：关注点分离是软件设计的重要原则。

### 7. 事件系统

表单引擎通过事件系统实现解耦：

```typescript
engine.onSubmit(async (values) => {
  // 处理提交
});

engine.onStateChange((state) => {
  // 响应状态变化
});
```

**实现方式**：
- 回调函数数组
- 状态变化时通知所有监听者

**关键理解**：观察者模式是实现解耦的常用方式。

### 8. XSS 防护

渲染 HTML 时需要防止 XSS 攻击：

```typescript
function escapeHtml(str: string): string {
  return str
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}
```

**关键理解**：任何输出到 HTML 的内容都需要转义。

### 9. 异步操作支持

表单提交可能是异步操作：

```typescript
async submit(): Promise<boolean> {
  this.state.submitting = true;

  try {
    await handler(this.state.values);
    return true;
  } catch (error) {
    return false;
  } finally {
    this.state.submitting = false;
  }
}
```

**关键理解**：
- 使用 async/await 处理异步
- try/catch/finally 确保状态正确
- submitting 状态用于 UI 反馈

### 10. TypeScript 类型系统

使用 TypeScript 定义强类型接口：

```typescript
interface FieldSchema {
  name: string;
  type: FieldType;
  label: string;
  validation?: ValidationRule[];
  // ...
}
```

**好处**：
- 编译时类型检查
- IDE 自动补全
- 代码更易理解

**关键理解**：类型系统是大型项目的基础。

## 设计决策

### 1. 为什么选择无框架实现？

- 更轻量，易于理解
- 专注于核心概念
- 可以在任何环境中使用

### 2. 为什么使用规则数组？

- 灵活组合多种验证
- 每个规则有独立的错误信息
- 易于扩展新的规则类型

### 3. 为什么集中管理状态？

- 状态可预测
- 便于调试
- 易于实现状态持久化

### 4. 为什么分离渲染器？

- 支持多种输出格式
- 业务逻辑可复用
- 更容易测试

## 遇到的挑战

### 挑战 1：验证时机选择

**问题**：何时触发验证？输入时？失焦时？提交时？

**解决**：
- 输入时验证单个字段
- 提交时验证所有字段
- 可以根据需求灵活配置

### 挑战 2：条件字段验证

**问题**：隐藏的字段是否需要验证？

**解决**：
- 隐藏字段跳过验证
- 只验证可见字段

### 挑战 3：跨字段验证

**问题**：如何实现密码确认等跨字段验证？

**解决**：
- 自定义验证器接收 formData
- 可以访问其他字段的值

### 挑战 4：异步提交

**问题**：提交可能是异步操作

**解决**：
- 使用 async/await
- 添加 submitting 状态
- 正确处理错误

## 与其他实现的对比

### 对比 Formik (React)

| 特性 | Formik | 本实现 |
|------|--------|--------|
| 框架依赖 | React | 无 |
| Schema 驱动 | 否 | 是 |
| 验证 | Yup/自定义 | 内置+自定义 |
| 渲染 | JSX | HTML 字符串 |

### 对比 React Hook Form

| 特性 | React Hook Form | 本实现 |
|------|-----------------|--------|
| 性能优化 | 优秀 | 一般 |
| 学习曲线 | 中等 | 简单 |
| 功能完整 | 非常完整 | 基础功能 |

## 未来改进方向

1. **异步验证**：支持异步验证（如检查用户名是否存在）
2. **表单联动**：更复杂的字段联动逻辑
3. **国际化**：多语言错误信息支持
4. **持久化**：表单数据本地存储
5. **撤销/重做**：操作历史支持
6. **性能优化**：减少不必要的验证和渲染
7. **框架集成**：React/Vue 组件封装
8. **可视化编辑**：拖拽式表单设计器

## 总结

通过实现表单引擎，我深入理解了：

1. **Schema 驱动设计**：配置优于编码
2. **状态管理**：复杂状态的组织方式
3. **验证策略**：多种验证时机和方式
4. **渲染分离**：关注点分离的好处
5. **TypeScript**：类型系统的重要性
6. **事件系统**：观察者模式的应用

这个项目虽然功能相对简单，但涵盖了前端开发的多个核心概念，是一个很好的学习项目。
