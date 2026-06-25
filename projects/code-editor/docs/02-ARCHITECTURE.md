# 代码编辑器架构设计

## 1. 整体架构

### 1.1 分层架构

```
┌──────────────────────────────────────────────────────────────┐
│                      Application Layer                       │
│                    (Editor 应用实例)                          │
├──────────────────────────────────────────────────────────────┤
│                      Core Layer                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐          │
│  │  Document   │  │   Cursor    │  │  Selection  │          │
│  │   Model     │  │  Manager    │  │   Manager   │          │
│  └─────────────┘  └─────────────┘  └─────────────┘          │
├──────────────────────────────────────────────────────────────┤
│                      Feature Layer                           │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐          │
│  │  Syntax     │  │   Input     │  │  Command    │          │
│  │ Highlighter │  │  Handler    │  │   System    │          │
│  └─────────────┘  └─────────────┘  └─────────────┘          │
├──────────────────────────────────────────────────────────────┤
│                      Render Layer                            │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐          │
│  │   Canvas    │  │   View      │  │  Layout     │          │
│  │  Renderer   │  │  Manager    │  │   Engine    │          │
│  └─────────────┘  └─────────────┘  └─────────────┘          │
└──────────────────────────────────────────────────────────────┘
```

### 1.2 模块职责

| 模块 | 职责 | 关键接口 |
|------|------|----------|
| Document | 文本存储与操作 | insert, delete, getLine |
| Cursor | 光标位置管理 | move, setPosition |
| Selection | 选区管理 | setSelection, getSelection |
| SyntaxHighlighter | 语法分析 | tokenize, highlight |
| InputHandler | 输入事件处理 | handleKey, handleIME |
| CommandSystem | 命令执行 | execute, undo, redo |
| CanvasRenderer | 画面渲染 | render, drawText |
| ViewManager | 视图状态 | scroll, viewport |

## 2. 核心数据模型

### 2.1 Document Model

```typescript
interface Document {
  // 文本内容存储
  lines: string[];

  // 基本操作
  insert(position: Position, text: string): EditOperation;
  delete(range: Range): EditOperation;
  replace(range: Range, text: string): EditOperation;

  // 查询操作
  getLine(lineNumber: number): string;
  getLineCount(): number;
  getText(): string;
  getLength(): number;

  // 位置转换
  offsetAt(position: Position): number;
  positionAt(offset: number): Position;
}
```

### 2.2 Position & Range

```typescript
interface Position {
  line: number;    // 行号，从 0 开始
  column: number;  // 列号，从 0 开始
}

interface Range {
  start: Position;
  end: Position;
}

interface EditOperation {
  range: Range;
  text: string;
  // 用于撤销/重做
  inverse: EditOperation;
}
```

### 2.3 Cursor Model

```typescript
interface Cursor {
  position: Position;
  // 可选：选区
  selection?: Range;
  // 光标可见性（闪烁状态）
  visible: boolean;
}

interface CursorManager {
  // 当前光标列表（支持多光标）
  cursors: Cursor[];

  // 主光标
  primary: Cursor;

  // 操作
  moveTo(position: Position): void;
  moveUp(lines?: number): void;
  moveDown(lines?: number): void;
  moveLeft(chars?: number): void;
  moveRight(chars?: number): void;

  // 选择
  selectTo(position: Position): void;
  selectAll(): void;
  selectLine(lineNumber: number): void;
}
```

## 3. 渲染架构

### 3.1 Canvas 渲染层次

```
┌────────────────────────────────────┐
│         Canvas Element             │
├────────────────────────────────────┤
│  Layer 1: Background               │  ← 行背景、选区
├────────────────────────────────────┤
│  Layer 2: Text Content             │  ← 代码文本
├────────────────────────────────────┤
│  Layer 3: Syntax Highlighting      │  ← 语法着色
├────────────────────────────────────┤
│  Layer 4: Cursor & Selection       │  ← 光标、选区
├────────────────────────────────────┤
│  Layer 5: Decorations              │  ← 行号、错误标记
└────────────────────────────────────┘
```

### 3.2 渲染流程

```typescript
class CanvasRenderer {
  render(state: EditorState): void {
    // 1. 清除画布
    this.clear();

    // 2. 计算可见区域
    const viewport = this.calculateViewport(state.scroll);

    // 3. 绘制背景
    this.drawBackground(viewport);

    // 4. 绘制行号
    this.drawLineNumbers(viewport);

    // 5. 绘制文本（带语法高亮）
    this.drawCode(viewport, state.tokens);

    // 6. 绘制选区
    this.drawSelections(state.selections);

    // 7. 绘制光标
    this.drawCursors(state.cursors);
  }
}
```

### 3.3 文本测量

```typescript
interface TextMetrics {
  // 字符宽度（等宽字体）
  charWidth: number;
  // 行高
  lineHeight: number;
  // 基线偏移
  baseline: number;
}

class FontMetrics {
  private cache: Map<string, TextMetrics> = new Map();

  measure(font: string, text: string): TextMetrics {
    // 使用 Canvas measureText 测量
    // 缓存结果避免重复计算
  }
}
```

## 4. 语法高亮架构

### 4.1 Token 类型

```typescript
enum TokenType {
  // 关键字
  Keyword = 'keyword',
  // 标识符
  Identifier = 'identifier',
  // 字符串
  String = 'string',
  // 数字
  Number = 'number',
  // 注释
  Comment = 'comment',
  // 操作符
  Operator = 'operator',
  // 标点符号
  Punctuation = 'punctuation',
  // 空白
  Whitespace = 'whitespace',
  // 未知
  Unknown = 'unknown'
}

interface Token {
  type: TokenType;
  value: string;
  start: number;
  end: number;
  // 所在行
  line: number;
}
```

### 4.2 状态机设计

```typescript
interface State {
  // 当前状态类型
  type: StateType;
  // 状态数据（如多行注释）
  data?: any;
}

enum StateType {
  Normal = 'normal',
  // 多行注释
  BlockComment = 'blockComment',
  // 多行字符串
  TemplateString = 'templateString',
  // JSX
  JSXTag = 'jsxTag'
}

interface StateMachine {
  // 处理一个字符，返回新状态和 token
  process(char: string, state: State): [State, Token | null];

  // 处理一行文本
  processLine(line: string, startState: State): [Token[], State];
}
```

### 4.3 增量更新策略

```typescript
interface IncrementalHighlighter {
  // 全量高亮
  highlightAll(document: Document): Token[][];

  // 增量高亮（编辑后）
  highlightRange(
    document: Document,
    startLine: number,
    endLine: number,
    previousTokens: Token[][]
  ): Token[][];

  // 获取行状态
  getStateAtLine(lineNumber: number): State;
}
```

## 5. 输入处理架构

### 5.1 事件流

```
DOM Events → Input Handler → Command Mapping → Command Execution → Document Update
     ↓              ↓               ↓                  ↓                ↓
  KeyboardEvent  KeyParser     CommandRegistry     EditOperation    Re-render
```

### 5.2 快捷键映射

```typescript
interface KeyBinding {
  key: string;           // 按键
  ctrl?: boolean;
  shift?: boolean;
  alt?: boolean;
  meta?: boolean;
  command: string;       // 命令名称
  when?: string;         // 条件表达式
}

interface CommandRegistry {
  // 注册命令
  register(command: string, handler: CommandHandler): void;

  // 执行命令
  execute(command: string, args?: any): void;

  // 绑定快捷键
  bindKey(binding: KeyBinding): void;
}
```

### 5.3 常用命令

| 命令 | 快捷键 | 功能 |
|------|--------|------|
| cursorLeft | Left | 光标左移 |
| cursorRight | Right | 光标右移 |
| cursorUp | Up | 光标上移 |
| cursorDown | Down | 光标下移 |
| selectLeft | Shift+Left | 向左选择 |
| selectRight | Shift+Right | 向右选择 |
| deleteLeft | Backspace | 删除左边字符 |
| deleteRight | Delete | 删除右边字符 |
| newline | Enter | 插入换行 |
| tab | Tab | 插入缩进 |
| undo | Ctrl+Z | 撤销 |
| redo | Ctrl+Y | 重做 |
| selectAll | Ctrl+A | 全选 |

## 6. 状态管理

### 6.1 Editor State

```typescript
interface EditorState {
  // 文档内容
  document: Document;

  // 光标状态
  cursors: Cursor[];

  // 选区状态
  selections: Range[];

  // 语法高亮 tokens
  tokens: Token[][];

  // 滚动位置
  scroll: ScrollPosition;

  // 视口信息
  viewport: Viewport;

  // 配置
  config: EditorConfig;
}

interface ScrollPosition {
  top: number;    // 像素
  left: number;   // 像素
}

interface Viewport {
  topLine: number;      // 可见首行
  bottomLine: number;   // 可见末行
  leftColumn: number;   // 可见首列
}
```

### 6.2 状态更新

```typescript
// 不可变状态更新
function updateState(
  state: EditorState,
  changes: Partial<EditorState>
): EditorState {
  return { ...state, ...changes };
}

// 批量更新
function batchUpdate(
  state: EditorState,
  updates: Array<(state: EditorState) => EditorState>
): EditorState {
  return updates.reduce((s, update) => update(s), state);
}
```

## 7. 性能优化

### 7.1 渲染优化

1. **虚拟化渲染**
   - 只渲染可见行
   - 行级缓存
   - 脏区域检测

2. **批量绘制**
   - 减少 Canvas API 调用
   - 合并相同样式文本

3. **离屏渲染**
   - 双缓冲技术
   - 离屏 Canvas 预渲染

### 7.2 语法高亮优化

1. **增量更新**
   - 只重新分析修改行
   - 状态缓存

2. **后台处理**
   - Web Worker 分析
   - 异步高亮

### 7.3 内存优化

1. **数据结构优化**
   - 稀疏数组存储 tokens
   - 字符串池

2. **GC 优化**
   - 对象池
   - 减少临时对象

## 8. 扩展性设计

### 8.1 插件接口

```typescript
interface EditorPlugin {
  name: string;
  version: string;

  // 生命周期
  activate(editor: Editor): void;
  deactivate(): void;

  // 可选：自定义渲染
  render?(ctx: CanvasRenderingContext2D, viewport: Viewport): void;

  // 可选：自定义命令
  commands?: Record<string, CommandHandler>;

  // 可选：自定义快捷键
  keyBindings?: KeyBinding[];
}
```

### 8.2 主题系统

```typescript
interface EditorTheme {
  // 背景色
  background: string;
  // 前景色
  foreground: string;
  // 行号颜色
  lineNumbers: string;
  // 选区颜色
  selection: string;
  // 光标颜色
  cursor: string;

  // 语法高亮颜色
  syntax: {
    keyword: string;
    string: string;
    number: string;
    comment: string;
    // ...
  };
}
```

## 9. 错误处理

### 9.1 错误类型

```typescript
enum EditorErrorType {
  // 编辑操作错误
  EditError = 'editError',
  // 渲染错误
  RenderError = 'renderError',
  // 语法分析错误
  SyntaxError = 'syntaxError',
  // 输入处理错误
  InputError = 'inputError'
}

interface EditorError {
  type: EditorErrorType;
  message: string;
  line?: number;
  column?: number;
  stack?: string;
}
```

### 9.2 错误恢复

1. **渲染错误**：跳过当前帧，使用上一帧
2. **语法错误**：降级到无高亮模式
3. **输入错误**：忽略无效输入

## 10. 测试策略

### 10.1 单元测试
- Document 操作测试
- Cursor 位置计算测试
- SyntaxHighlighter 状态机测试

### 10.2 集成测试
- 输入到渲染流程测试
- 快捷键功能测试

### 10.3 性能测试
- 大文件渲染性能
- 快速输入响应
- 内存占用监控
