# 表单引擎设计

## 架构设计

### 整体架构

```
┌─────────────────────────────────────────────────────────────────┐
│                       表单引擎 (Form Engine)                     │
│                                                                 │
│  ┌──────────────┐   ┌──────────────┐   ┌──────────────────┐   │
│  │   FormSchema  │──▶│  FormEngine   │──▶│  FormRenderer    │   │
│  │   (定义层)    │   │  (逻辑层)     │   │  (渲染层)        │   │
│  └──────────────┘   └──────────────┘   └──────────────────┘   │
│                            │                     │              │
│                            ▼                     ▼              │
│                     ┌──────────────┐     ┌──────────────┐      │
│                     │  Validator   │     │  HTML/JSON   │      │
│                     │  (验证层)    │     │  Output      │      │
│                     └──────────────┘     └──────────────┘      │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                    FormState (状态层)                      │  │
│  │  values | errors | touched | dirty | valid | submitting  │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

### 核心模块

#### 1. 类型定义 (types.ts)

定义所有接口和类型：

```
FieldType        - 字段类型枚举
FieldOption      - 选项配置
ValidationRule   - 验证规则
FieldSchema      - 字段定义
FormSchema       - 表单定义
FieldState       - 字段状态
FormState        - 表单状态
```

#### 2. 验证器 (validator.ts)

负责表单验证：

```
validateField()  - 验证单个字段
validateForm()   - 验证整个表单
rules            - 验证规则工厂函数
```

#### 3. 表单引擎 (form-engine.ts)

核心业务逻辑：

```
FormEngine 类
├── 构造函数：初始化 Schema 和状态
├── 状态管理：getValue/setValue/getState
├── 验证：validate()
├── 提交：submit()
├── 重置：reset()
└── 事件：onSubmit/onStateChange
```

#### 4. 渲染器 (renderer.ts)

将 Schema 和状态渲染为 UI：

```
FormRenderer 类
├── render()       - 渲染为 HTML
├── renderAsText() - 渲染为纯文本
└── renderAsJson() - 渲染为 JSON
```

## 数据流

### 表单数据流

```
用户输入
    │
    ▼
┌─────────┐     ┌───────────┐     ┌──────────┐
│ setValue │────▶│ validate  │────▶│ update   │
│          │     │ (单字段)  │     │ state    │
└─────────┘     └───────────┘     └──────────┘
                                        │
                                        ▼
                                   ┌──────────┐
                                   │ notify   │
                                   │ callbacks│
                                   └──────────┘
```

### 提交流程

```
用户点击提交
    │
    ▼
┌─────────┐     ┌───────────┐     ┌──────────┐
│ submit() │────▶│ validate  │────▶│ handler  │
│          │     │ (全表单)  │     │ callbacks│
└─────────┘     └───────────┘     └──────────┘
    │                                   │
    │                                   ▼
    │                              ┌──────────┐
    │                              │ async    │
    │                              │ operation│
    │                              └──────────┘
    │                                   │
    ▼                                   ▼
  状态更新                           完成/错误
```

## 类型设计

### FieldSchema

```typescript
interface FieldSchema {
  name: string;           // 字段名（唯一标识）
  type: FieldType;        // 字段类型
  label: string;          // 显示标签
  placeholder?: string;   // 占位文本
  defaultValue?: any;     // 默认值
  options?: FieldOption[]; // 选项（select/radio）
  validation?: ValidationRule[]; // 验证规则
  disabled?: boolean;     // 是否禁用
  hidden?: boolean;       // 是否隐藏
  dependsOn?: {           // 条件依赖
    field: string;
    value: any;
  };
}
```

### FormState

```typescript
interface FormState {
  values: Record<string, any>;         // 字段值
  errors: Record<string, FieldError[]>;// 错误信息
  touched: Record<string, boolean>;    // 是否触碰
  dirty: Record<string, boolean>;      // 是否修改
  valid: boolean;                      // 整体有效性
  submitting: boolean;                 // 提交中
  submitted: boolean;                  // 已提交
}
```

## 验证设计

### 验证规则链

```typescript
const rules = {
  required(message),
  minLength(min, message),
  maxLength(max, message),
  min(min, message),
  max(max, message),
  pattern(regex, message),
  email(message),
  custom(validator, message)
};
```

### 验证执行流程

```
validateField(value, rules, formData)
    │
    ├─ 遍历 rules
    │   ├─ 如果是 custom 类型
    │   │   └─ 调用 rule.validator(value, formData)
    │   └─ 否则
    │       └─ 调用内置验证器
    │
    └─ 返回 { valid, errors[] }
```

## 渲染设计

### HTML 渲染结构

```html
<form class="form-engine">
  <h2 class="form-title">表单标题</h2>
  <p class="form-description">描述</p>

  <div class="form-fields">
    <div class="form-field" data-field-name="username">
      <label class="field-label" for="field-username">用户名</label>
      <input type="text" id="field-username" name="username" />
      <span class="field-description">帮助文本</span>
      <div class="field-errors">
        <span class="error-message">错误信息</span>
      </div>
    </div>
    <!-- 更多字段... -->
  </div>

  <div class="form-actions">
    <button type="submit" class="btn btn-submit">提交</button>
    <button type="reset" class="btn btn-reset">重置</button>
  </div>
</form>
```

### 条件渲染

```typescript
isFieldVisible(field: FieldSchema): boolean {
  if (field.hidden) return false;
  if (!field.dependsOn) return true;

  const dependentValue = state.values[field.dependsOn.field];
  return dependentValue === field.dependsOn.value;
}
```

## 接口设计

### FormEngine 公共 API

```typescript
class FormEngine {
  // 构造
  constructor(schema: FormSchema);

  // 状态访问
  getSchema(): FormSchema;
  getState(): FormState;
  getValue(name: string): any;
  getValues(): Record<string, any>;
  getFieldState(name: string): FieldState | null;

  // 状态修改
  setValue(name: string, value: any): void;
  setTouched(name: string): void;

  // 表单操作
  validate(): boolean;
  submit(): Promise<boolean>;
  reset(): void;

  // 事件注册
  onSubmit(handler: SubmitHandler): void;
  onStateChange(callback: StateChangeCallback): void;

  // 渲染辅助
  getHandlers(): FormHandlers;
  isFieldVisible(field: FieldSchema): boolean;
  getVisibleFields(): FieldSchema[];
}
```

### FormRenderer 公共 API

```typescript
class FormRenderer {
  render(schema: FormSchema, state: FormState): RenderResult;
  renderAsText(schema: FormSchema, state: FormState): RenderResult;
  renderAsJson(schema: FormSchema, state: FormState): RenderResult;
}
```

## 设计决策

### 1. 无框架依赖

选择纯 TypeScript 实现，不依赖任何 UI 框架：
- 更轻量
- 更容易理解核心概念
- 可以在任何环境中使用

### 2. Schema 驱动

使用 Schema 定义表单结构：
- 声明式，易于理解
- 可以从 JSON 配置加载
- 便于序列化和传输

### 3. 状态集中管理

所有状态集中在 FormState 中：
- 状态可预测
- 便于调试
- 易于实现时间旅行

### 4. 验证规则组合

使用规则数组而非单一验证函数：
- 灵活组合
- 复用性高
- 错误信息清晰
