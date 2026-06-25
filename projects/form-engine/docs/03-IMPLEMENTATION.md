# 实现记录

## 实现步骤

### 第一步：类型定义

首先定义所有需要的类型接口，这是整个项目的基础。

**文件**: `src/types.ts`

主要类型：
- `FieldType`：字段类型枚举
- `FieldSchema`：字段定义接口
- `FormSchema`：表单定义接口
- `FormState`：表单状态接口
- `ValidationRule`：验证规则接口

### 第二步：验证器实现

实现验证规则系统，支持内置验证和自定义验证。

**文件**: `src/validator.ts`

核心功能：
- `validateField()`：验证单个字段
- `validateForm()`：验证整个表单
- `rules`：验证规则工厂函数

实现要点：
1. 内置验证器使用策略模式
2. 自定义验证器通过函数注入
3. 支持跨字段验证（通过 formData 参数）

### 第三步：表单引擎实现

实现表单的核心业务逻辑。

**文件**: `src/form-engine.ts`

核心功能：
1. **状态初始化**：根据 Schema 创建初始状态
2. **值管理**：setValue/getValue/getValues
3. **验证**：单字段验证 + 全表单验证
4. **提交**：异步提交支持
5. **重置**：恢复初始状态
6. **事件系统**：onSubmit/onStateChange

实现要点：
1. 状态使用不可变模式管理
2. 验证在每次 setValue 时自动触发
3. 提交前自动执行全表单验证
4. 支持异步提交处理器

### 第四步：渲染器实现

实现将 Schema 和状态渲染为 HTML。

**文件**: `src/renderer.ts`

核心功能：
1. `render()`：渲染为 HTML
2. `renderAsText()`：渲染为纯文本
3. `renderAsJson()`：渲染为 JSON

实现要点：
1. HTML 转义防止 XSS
2. 支持所有字段类型
3. 错误信息条件显示
4. 条件字段支持

## 关键实现细节

### 1. 状态管理

```typescript
// 状态结构
state = {
  values: {},    // 字段值
  errors: {},    // 错误信息
  touched: {},   // 是否触碰
  dirty: {},     // 是否修改
  valid: true,   // 整体有效
  submitting: false,
  submitted: false
};

// 更新值时自动验证
setValue(name, value) {
  this.state.values[name] = value;
  this.state.touched[name] = true;
  this.state.dirty[name] = true;

  // 验证字段
  const result = validateField(value, field.validation, this.state.values);
  this.state.errors[name] = result.errors;

  // 更新整体有效性
  this.state.valid = Object.values(this.state.errors)
    .every(errs => errs.length === 0);
}
```

### 2. 条件字段

```typescript
// 字段依赖配置
{
  name: 'address',
  dependsOn: {
    field: 'hasAddress',
    value: true
  }
}

// 可见性判断
isFieldVisible(field) {
  if (field.hidden) return false;
  if (!field.dependsOn) return true;

  return this.state.values[field.dependsOn.field] === field.dependsOn.value;
}
```

### 3. 验证规则工厂

```typescript
// 规则工厂函数
rules = {
  required(message) {
    return { type: 'required', message };
  },
  minLength(min, message) {
    return { type: 'minLength', value: min, message };
  },
  custom(validator, message) {
    return { type: 'custom', message, validator };
  }
};

// 使用示例
validation: [
  rules.required('不能为空'),
  rules.minLength(3, '至少3个字符'),
  rules.custom(v => v === pwd, '密码不一致')
]
```

### 4. XSS 防护

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

### 5. 异步提交

```typescript
async submit(): Promise<boolean> {
  // 验证
  if (!this.validate()) return false;

  this.state.submitting = true;

  try {
    for (const handler of this.submitHandlers) {
      await handler(this.state.values);
    }
    return true;
  } catch (error) {
    console.error('Submit error:', error);
    return false;
  } finally {
    this.state.submitting = false;
  }
}
```

## 遇到的问题与解决方案

### 问题 1：验证时机

**问题**：何时触发验证？

**解决方案**：
- 输入时验证单个字段
- 提交时验证所有字段
- 失焦时可选择性验证

### 问题 2：条件字段验证

**问题**：隐藏字段是否需要验证？

**解决方案**：
- 隐藏字段跳过验证
- `validateForm()` 只验证可见字段

### 问题 3：跨字段验证

**问题**：如何实现密码确认等跨字段验证？

**解决方案**：
- 自定义验证器接收 formData 参数
- 可以访问其他字段的值

```typescript
rules.custom(
  (value, formData) => value === formData.password,
  '密码不一致'
)
```

### 问题 4：默认值处理

**问题**：不同字段类型需要不同的默认值。

**解决方案**：
- 优先使用 Schema 中的 defaultValue
- 否则根据类型推断默认值

```typescript
getDefaultValue(field) {
  switch (field.type) {
    case 'checkbox': return false;
    case 'number': return 0;
    default: return '';
  }
}
```

## 性能考虑

### 1. 状态更新

- 只更新变化的字段
- 避免不必要的重新渲染

### 2. 验证优化

- 输入时只验证当前字段
- 提交时验证所有字段

### 3. 渲染优化

- 只渲染可见字段
- 缓存渲染结果

## 后续优化方向

1. **异步验证**：支持异步验证（如检查用户名是否存在）
2. **表单联动**：字段之间的联动更复杂
3. **国际化**：错误信息多语言支持
4. **自定义渲染器**：支持自定义字段渲染
5. **表单持久化**：支持本地存储
6. **撤销/重做**：表单操作历史
