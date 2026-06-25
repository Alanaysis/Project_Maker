# 代码编辑器学习笔记

## 学习目标

1. **理解编辑器架构** - 掌握编辑器的核心组件和数据流
2. **掌握语法高亮** - 学习基于状态机的词法分析
3. **学会光标管理** - 理解光标位置计算和选择管理

## 核心概念

### 1. 编辑器架构

#### 1.1 分层设计

编辑器采用分层架构，各层职责明确：

```
┌─────────────────────────────────────┐
│         Application Layer           │  ← 编辑器实例
├─────────────────────────────────────┤
│           Core Layer                │  ← Document, Cursor
├─────────────────────────────────────┤
│          Feature Layer              │  ← Highlighter, Input
├─────────────────────────────────────┤
│          Render Layer               │  ← Canvas, Layout
└─────────────────────────────────────┘
```

**关键理解**：
- 每层只依赖下层，不依赖上层
- 核心层不依赖任何外部库
- 渲染层与业务逻辑分离

#### 1.2 数据流

```
输入 → 命令解析 → 文档修改 → 语法分析 → 渲染
  ↓         ↓          ↓          ↓        ↓
键盘     Command    Document   Tokens   Canvas
事件      执行       更新       生成      绘制
```

**关键理解**：
- 单向数据流，易于理解和调试
- 每个步骤可独立测试
- 状态变化可预测

### 2. 文档模型

#### 2.1 数据结构选择

**方案对比**：

| 方案 | 优点 | 缺点 | 适用场景 |
|------|------|------|----------|
| 字符串数组 | 简单直观 | 插入删除性能差 | 小文件 |
| 链表 | 插入删除快 | 随机访问慢 | 频繁编辑 |
| Piece Table | 内存效率高 | 实现复杂 | 大文件 |
| Rope | 平衡性能好 | 实现复杂 | 专业编辑器 |

**本项目选择**：字符串数组
- 实现简单，便于学习
- 性能满足小型编辑器需求
- 代码清晰易懂

#### 2.2 位置管理

```typescript
interface Position {
  line: number;    // 行号（从 0 开始）
  column: number;  // 列号（从 0 开始）
}
```

**关键理解**：
- 行列坐标系统
- 边界检查的重要性
- 位置转换（行列 ↔ 偏移量）

### 3. 语法高亮

#### 3.1 词法分析基础

词法分析将源代码分解为 Token：

```
源代码: const x = 42;
    ↓
Tokens: [Keyword, Identifier, Operator, Number, Punctuation]
```

#### 3.2 状态机实现

```typescript
状态机示例：
  ┌──────────┐
  │  Normal  │ ←─────────────────┐
  └────┬─────┘                   │
       │ '/'                     │ '*/'
       ↓                         │
  ┌──────────┐                   │
  │ Comment  │ ──────────────────┘
  └──────────┘
```

**关键理解**：
- 状态机处理多行上下文（如多行注释）
- 状态在行之间传递
- 正则表达式用于模式匹配

#### 3.3 Token 类型设计

```typescript
enum TokenType {
  Keyword,      // 关键字
  Identifier,   // 标识符
  String,       // 字符串
  Number,       // 数字
  Comment,      // 注释
  Operator,     // 操作符
  Punctuation,  // 标点
  Whitespace    // 空白
}
```

**关键理解**：
- Token 类型决定显示颜色
- 类型划分影响高亮准确性
- 可扩展性设计

### 4. 光标管理

#### 4.1 光标状态

```typescript
interface Cursor {
  position: Position;     // 光标位置
  selection?: Range;      // 选区（可选）
  visible: boolean;       // 闪烁状态
}
```

#### 4.2 光标移动逻辑

**左右移动**：
- 正常情况：列号 +/- 1
- 行首左移：跳到上一行末尾
- 行末右移：跳到下一行开头

**上下移动**：
- 保持列号不变
- 如果目标行更短，列号调整到行末

#### 4.3 选择管理

```typescript
interface Selection {
  start: Position;  // 选择起点
  end: Position;    // 选择终点
}
```

**关键理解**：
- 选择是连续的文本范围
- start 可能在 end 之后
- 需要规范化选择范围

### 5. Canvas 渲染

#### 5.1 渲染层次

```
Layer 1: 背景色
Layer 2: 行号
Layer 3: 代码文本
Layer 4: 选区高亮
Layer 5: 光标
```

#### 5.2 文本测量

```javascript
ctx.font = '14px Consolas';
const metrics = ctx.measureText('M');
charWidth = metrics.width;  // 等宽字体：所有字符宽度相同
```

**关键理解**：
- 等宽字体简化位置计算
- 预先测量避免重复计算
- lineHeight = fontSize * 1.5

#### 5.3 性能优化

1. **虚拟化渲染**：只绘制可见行
2. **脏区域检测**：只重绘变化区域
3. **批量绘制**：减少 Canvas API 调用

## 实现过程中的关键决策

### 1. 为什么选择 Canvas？

**优点**：
- 完全控制渲染过程
- 性能可控
- 学习价值高

**缺点**：
- 需要自己实现所有交互
- 输入法支持复杂
- 无障碍访问困难

### 2. 为什么用正则做词法分析？

**优点**：
- 实现简单
- 覆盖常见场景
- 易于扩展

**缺点**：
- 无法处理复杂语法
- 多行上下文有限

### 3. 为什么不用 AST？

- AST 需要完整解析器
- 实现复杂度高
- 性能开销大
- 对于学习项目过于复杂

## 调试技巧

### 1. 渲染调试

```javascript
// 绘制调试边框
ctx.strokeStyle = 'red';
ctx.strokeRect(x, y, width, height);

// 绘制网格
ctx.strokeStyle = 'rgba(255,255,255,0.1)';
for (let x = 0; x < canvas.width; x += charWidth) {
  ctx.beginPath();
  ctx.moveTo(x, 0);
  ctx.lineTo(x, canvas.height);
  ctx.stroke();
}
```

### 2. 事件调试

```javascript
document.addEventListener('keydown', (e) => {
  console.log('Key:', e.key, 'Code:', e.code);
  console.log('Modifiers:', {
    ctrl: e.ctrlKey,
    shift: e.shiftKey,
    alt: e.altKey
  });
});
```

### 3. 状态调试

```javascript
// 添加状态显示
function renderDebugInfo(state) {
  ctx.fillStyle = 'white';
  ctx.font = '12px monospace';
  ctx.fillText(`Line: ${cursor.line}, Col: ${cursor.col}`, 10, 20);
  ctx.fillText(`Lines: ${document.lineCount}`, 10, 35);
}
```

## 扩展方向

### 1. 功能扩展

- **查找替换**：正则表达式支持
- **代码折叠**：折叠/展开代码块
- **自动补全**：智能代码补全
- **多光标**：同时编辑多个位置

### 2. 性能优化

- **Web Worker**：后台语法分析
- **增量更新**：只重新分析修改行
- **缓存优化**：Token 缓存

### 3. 用户体验

- **主题系统**：自定义颜色主题
- **快捷键自定义**：可配置的快捷键
- **插件系统**：可扩展的插件架构

## 学习资源

1. **CodeMirror 6 源码** - 学习专业编辑器架构
2. **Writing a Code Editor** - 基础实现教程
3. **Canvas API 文档** - 渲染技术参考
4. **Prism.js** - 语法高亮算法

## 总结

通过实现这个代码编辑器，我学到了：

1. **架构设计**：分层架构的重要性，单一职责原则
2. **数据结构**：选择合适的数据结构影响性能
3. **状态管理**：不可变状态，单向数据流
4. **Canvas 渲染**：文本测量，坐标系统，性能优化
5. **语法分析**：词法分析，状态机，Token 设计
6. **光标管理**：位置计算，选择管理，边界处理

这些知识不仅适用于编辑器开发，也适用于其他复杂的 UI 应用开发。
