# 测试策略

## 测试架构

```
tests/
├── run.ts               # 测试运行器
├── test_validator.ts    # 验证器测试
├── test_form_engine.ts  # 表单引擎测试
├── test_renderer.ts     # 渲染器测试
└── test_edge_cases.ts   # 边界情况测试
```

## 测试覆盖

### 1. 验证器测试 (test_validator.ts)

#### 内置验证规则

| 规则 | 测试用例 | 预期结果 |
|------|----------|----------|
| required | 空字符串 | invalid |
| required | 非空字符串 | valid |
| required | null | invalid |
| required | undefined | invalid |
| required | 空数组 | invalid |
| required | 非空数组 | valid |
| minLength | 长度不足 | invalid |
| minLength | 长度足够 | valid |
| maxLength | 长度超出 | invalid |
| maxLength | 长度未超出 | valid |
| min | 值过小 | invalid |
| min | 值足够 | valid |
| max | 值过大 | invalid |
| max | 值未超出 | valid |
| pattern | 匹配正则 | valid |
| pattern | 不匹配正则 | invalid |
| email | 有效邮箱 | valid |
| email | 无效邮箱 | invalid |

#### 组合规则

- 多规则组合验证
- 错误数量正确性

#### 自定义验证器

- 自定义函数验证
- 跨字段验证

#### validateForm

- 多字段验证
- 隐藏字段跳过

### 2. 表单引擎测试 (test_form_engine.ts)

#### 初始化

- 默认值设置
- 初始状态正确性

#### 值管理

- setValue 更新值
- getValue 获取值
- getValues 获取所有值
- touched 状态更新
- dirty 状态更新

#### 验证

- 单字段验证触发
- 表单整体有效性更新
- 验证错误正确记录

#### 提交

- 有效表单提交成功
- 无效表单提交失败
- 异步提交支持
- 提交回调执行
- 提交失败处理

#### 重置

- 值重置
- 状态重置

#### 事件系统

- onStateChange 回调
- onSubmit 回调

#### 渲染辅助

- getHandlers 返回正确处理器
- handlers.onChange 工作正常
- handlers.onReset 工作正常

### 3. 渲染器测试 (test_renderer.ts)

#### HTML 渲染

- 表单标签生成
- 标题渲染
- 描述渲染
- 提交/重置按钮

#### 字段渲染

- text 输入框
- email 输入框
- password 输入框
- number 输入框
- textarea 文本域
- select 下拉框
- checkbox 复选框
- radio 单选按钮

#### 选项渲染

- select 选项
- radio 选项

#### 属性渲染

- placeholder
- disabled
- field description

#### 错误显示

- 错误信息渲染
- 错误样式类

#### 条件渲染

- 隐藏字段不渲染

#### 其他格式

- 纯文本渲染
- JSON 渲染

#### 安全性

- XSS 防护测试

### 4. 边界情况测试 (test_edge_cases.ts)

#### 空表单

- 无字段表单初始化
- 无字段表单渲染

#### 条件字段

- 条件显示/隐藏
- 字段可见性判断

#### 禁用字段

- disabled 属性处理

#### 自定义验证

- 跨字段验证

#### 多次提交

- 重复提交处理

#### 异步提交

- 异步操作支持

#### 提交失败

- 错误处理
- 状态恢复

#### 不存在的字段

- setValue 安全处理
- getFieldState 安全处理

#### 数值验证

- 边界值测试

#### 模式验证

- 字符串形式正则

#### 空渲染

- 无字段渲染

## 测试工具

### 断言函数

```typescript
function assert(condition: boolean, message: string): void {
  if (condition) {
    passed++;
    console.log(`  PASS: ${message}`);
  } else {
    failed++;
    console.error(`  FAIL: ${message}`);
  }
}

function assertEqual(actual: any, expected: any, message: string): void {
  if (actual === expected) {
    passed++;
    console.log(`  PASS: ${message}`);
  } else {
    failed++;
    console.error(`  FAIL: ${message} (expected: ${JSON.stringify(expected)}, got: ${JSON.stringify(actual)})`);
  }
}
```

### 测试运行器

```typescript
// tests/run.ts
import { testValidator } from './test_validator';
import { testFormEngine } from './test_form_engine';
import { testRenderer } from './test_renderer';
import { testEdgeCases } from './test_edge_cases';

console.log('=== Form Engine Tests ===');

testValidator();
testFormEngine();
testRenderer();
testEdgeCases();

console.log('\n=== Test Summary ===');
```

## 运行测试

```bash
# 安装依赖
npm install

# 运行所有测试
npm test

# 构建项目
npm run build
```

## 测试结果示例

```
=== Form Engine Tests ===

--- validator tests ---
  PASS: required: empty string is invalid
  PASS: required: non-empty string is valid
  PASS: minLength: "ab" < 3 is invalid
  ...
  Validator tests: 30 passed, 0 failed

--- form engine tests ---
  PASS: init: username default value
  PASS: setValue: value is updated
  ...
  Form engine tests: 20 passed, 0 failed

--- renderer tests ---
  PASS: render: format is html
  PASS: render: contains form tag
  ...
  Renderer tests: 15 passed, 0 failed

--- edge case tests ---
  PASS: empty form: valid by default
  PASS: conditional: address hidden when hasAddress=false
  ...
  Edge case tests: 12 passed, 0 failed

=== Test Summary ===
All test suites completed.
```

## 测试最佳实践

### 1. 测试命名

使用描述性的测试名称：
```typescript
assertEqual(validateField('', [rule]).valid, false, 'required: empty string is invalid');
```

### 2. 测试隔离

每个测试用例独立：
```typescript
// 每个测试块独立作用域
{
  const engine = new FormEngine(schema);
  // ... 测试逻辑
}
```

### 3. 边界覆盖

测试边界值和异常情况：
- 空值
- 极大值
- 无效类型
- 不存在的字段

### 4. 错误验证

验证错误信息正确：
```typescript
const result = validateField('', [rules.required('不能为空')]);
assertEqual(result.errors[0].message, '不能为空', 'error message is correct');
```
