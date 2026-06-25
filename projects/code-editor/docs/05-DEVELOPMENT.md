# 代码编辑器开发指南

## 1. 开发环境

### 1.1 环境要求

- Node.js >= 16.0.0
- npm >= 8.0.0 或 yarn >= 1.22.0
- TypeScript >= 5.0.0

### 1.2 安装依赖

```bash
cd projects/code-editor
npm install
```

### 1.3 项目结构

```
code-editor/
├── src/                    # 源代码
│   ├── core/              # 核心模块
│   │   ├── document.ts    # 文档模型
│   │   ├── cursor.ts      # 光标管理
│   │   └── types.ts       # 类型定义
│   ├── highlight/         # 语法高亮
│   │   ├── syntax.ts      # 高亮器实现
│   │   └── token.ts       # Token 定义
│   ├── render/            # 渲染模块
│   │   └── canvas.ts      # Canvas 渲染器
│   ├── editor.ts          # 编辑器主类
│   └── index.ts           # 入口文件
├── tests/                 # 测试文件
│   ├── document.test.ts   # 文档测试
│   ├── cursor.test.ts     # 光标测试
│   ├── highlighter.test.ts# 高亮测试
│   └── editor.test.ts     # 编辑器测试
├── examples/              # 示例文件
│   ├── basic.html         # 基础示例
│   └── demo.ts            # 演示代码
├── docs/                  # 文档
├── package.json           # 项目配置
├── tsconfig.json          # TypeScript 配置
└── jest.config.js         # 测试配置
```

## 2. 核心模块开发

### 2.1 类型定义

```typescript
// src/core/types.ts

// 位置
export interface Position {
  line: number;
  column: number;
}

// 范围
export interface Range {
  start: Position;
  end: Position;
}

// 编辑操作
export interface EditOperation {
  range: Range;
  text: string;
  inverse: EditOperation;
}

// 光标
export interface Cursor {
  position: Position;
  selection?: Range;
  visible: boolean;
}

// Token 类型
export enum TokenType {
  Keyword = 'keyword',
  Identifier = 'identifier',
  String = 'string',
  Number = 'number',
  Comment = 'comment',
  Operator = 'operator',
  Punctuation = 'punctuation',
  Whitespace = 'whitespace',
  Unknown = 'unknown'
}

// Token
export interface Token {
  type: TokenType;
  value: string;
  start: number;
  end: number;
  line: number;
}

// 滚动位置
export interface ScrollPosition {
  top: number;
  left: number;
}

// 视口
export interface Viewport {
  topLine: number;
  bottomLine: number;
  leftColumn: number;
}

// 编辑器状态
export interface EditorState {
  document: any; // DocumentModel
  cursors: Cursor[];
  selections: Range[];
  tokens: Token[][];
  scroll: ScrollPosition;
  viewport: Viewport;
  config: any;
}

// 渲染配置
export interface RenderConfig {
  fontSize?: number;
  fontFamily?: string;
  lineHeight?: number;
  tabSize?: number;
  padding?: number;
  showLineNumbers?: boolean;
  lineNumberWidth?: number;
}

// 编辑器选项
export interface EditorOptions {
  initialContent?: string;
  renderConfig?: Partial<RenderConfig>;
}
```

### 2.2 Document Model

```typescript
// src/core/document.ts

import { Position, Range, EditOperation } from './types';

export class DocumentModel {
  private lines: string[];

  constructor(content: string = '') {
    this.lines = content ? content.split('\n') : [''];
  }

  getLine(lineNumber: number): string {
    this.validateLineNumber(lineNumber);
    return this.lines[lineNumber];
  }

  getLineCount(): number {
    return this.lines.length;
  }

  getText(): string {
    return this.lines.join('\n');
  }

  insert(position: Position, text: string): EditOperation {
    this.validatePosition(position);

    const { line, column } = position;
    const currentLine = this.lines[line];
    const before = currentLine.substring(0, column);
    const after = currentLine.substring(column);

    const insertLines = text.split('\n');

    if (insertLines.length === 1) {
      this.lines[line] = before + text + after;
    } else {
      this.lines[line] = before + insertLines[0];
      const middleLines = insertLines.slice(1, -1);
      const lastLine = insertLines[insertLines.length - 1] + after;
      this.lines.splice(line + 1, 0, ...middleLines, lastLine);
    }

    return this.createOperation(position, text);
  }

  delete(range: Range): EditOperation {
    const { start, end } = range;
    const deletedText = this.getTextInRange(range);

    if (start.line === end.line) {
      const line = this.lines[start.line];
      this.lines[start.line] = 
        line.substring(0, start.column) + line.substring(end.column);
    } else {
      const firstLine = this.lines[start.line].substring(0, start.column);
      const lastLine = this.lines[end.line].substring(end.column);
      this.lines.splice(start.line, end.line - start.line + 1, firstLine + lastLine);
    }

    return this.createOperation(start, deletedText);
  }

  replace(range: Range, text: string): EditOperation {
    const deletedOp = this.delete(range);
    const insertedOp = this.insert(range.start, text);
    return insertedOp;
  }

  offsetAt(position: Position): number {
    let offset = 0;
    for (let i = 0; i < position.line; i++) {
      offset += this.lines[i].length + 1;
    }
    return offset + position.column;
  }

  positionAt(offset: number): Position {
    let remaining = offset;
    for (let line = 0; line < this.lines.length; line++) {
      const lineLength = this.lines[line].length + 1;
      if (remaining < lineLength) {
        return { line, column: remaining };
      }
      remaining -= lineLength;
    }
    const lastLine = this.lines.length - 1;
    return { line: lastLine, column: this.lines[lastLine].length };
  }

  private validateLineNumber(lineNumber: number): void {
    if (lineNumber < 0 || lineNumber >= this.lines.length) {
      throw new Error(`Invalid line number: ${lineNumber}`);
    }
  }

  private validatePosition(position: Position): void {
    this.validateLineNumber(position.line);
    const lineLength = this.lines[position.line].length;
    if (position.column < 0 || position.column > lineLength) {
      throw new Error(`Invalid column: ${position.column}`);
    }
  }

  private getTextInRange(range: Range): string {
    const { start, end } = range;
    if (start.line === end.line) {
      return this.lines[start.line].substring(start.column, end.column);
    }
    const result: string[] = [];
    result.push(this.lines[start.line].substring(start.column));
    for (let i = start.line + 1; i < end.line; i++) {
      result.push(this.lines[i]);
    }
    result.push(this.lines[end.line].substring(0, end.column));
    return result.join('\n');
  }

  private createOperation(position: Position, text: string): EditOperation {
    const endPosition = this.positionAt(this.offsetAt(position) + text.length);
    return {
      range: { start: position, end: endPosition },
      text,
      inverse: {
        range: { start: position, end: position },
        text: '',
        inverse: null as any
      }
    };
  }
}
```

### 2.3 Cursor Manager

```typescript
// src/core/cursor.ts

import { Position, Range, Cursor } from './types';
import { DocumentModel } from './document';

export class CursorManager {
  private cursors: Cursor[];
  private document: DocumentModel;

  constructor(document: DocumentModel) {
    this.document = document;
    this.cursors = [{
      position: { line: 0, column: 0 },
      visible: true
    }];
  }

  get primary(): Cursor {
    return this.cursors[0];
  }

  moveTo(position: Position): void {
    const valid = this.validatePosition(position);
    this.primary.position = valid;
    this.primary.selection = undefined;
  }

  moveUp(count: number = 1): void {
    const { line, column } = this.primary.position;
    const newLine = Math.max(0, line - count);
    const maxCol = this.document.getLine(newLine).length;
    this.moveTo({ line: newLine, column: Math.min(column, maxCol) });
  }

  moveDown(count: number = 1): void {
    const { line, column } = this.primary.position;
    const maxLine = this.document.getLineCount() - 1;
    const newLine = Math.min(maxLine, line + count);
    const maxCol = this.document.getLine(newLine).length;
    this.moveTo({ line: newLine, column: Math.min(column, maxCol) });
  }

  moveLeft(count: number = 1): void {
    const { line, column } = this.primary.position;
    if (column >= count) {
      this.moveTo({ line, column: column - count });
    } else if (line > 0) {
      const prevLine = line - 1;
      this.moveTo({ line: prevLine, column: this.document.getLine(prevLine).length });
    }
  }

  moveRight(count: number = 1): void {
    const { line, column } = this.primary.position;
    const lineLen = this.document.getLine(line).length;
    if (column + count <= lineLen) {
      this.moveTo({ line, column: column + count });
    } else if (line < this.document.getLineCount() - 1) {
      this.moveTo({ line: line + 1, column: 0 });
    }
  }

  selectTo(position: Position): void {
    const valid = this.validatePosition(position);
    if (!this.primary.selection) {
      this.primary.selection = { start: { ...this.primary.position }, end: valid };
    } else {
      this.primary.selection.end = valid;
    }
    this.primary.position = valid;
  }

  selectAll(): void {
    const lastLine = this.document.getLineCount() - 1;
    const lastCol = this.document.getLine(lastLine).length;
    this.primary.selection = {
      start: { line: 0, column: 0 },
      end: { line: lastLine, column: lastCol }
    };
    this.primary.position = { line: lastLine, column: lastCol };
  }

  getSelection(): Range | null {
    return this.primary.selection || null;
  }

  private validatePosition(pos: Position): Position {
    let { line, column } = pos;
    line = Math.max(0, Math.min(line, this.document.getLineCount() - 1));
    column = Math.max(0, Math.min(column, this.document.getLine(line).length));
    return { line, column };
  }
}
```

## 3. 语法高亮开发

### 3.1 Token 定义

```typescript
// src/highlight/token.ts

export enum TokenType {
  Keyword = 'keyword',
  Identifier = 'identifier',
  String = 'string',
  Number = 'number',
  Comment = 'comment',
  Operator = 'operator',
  Punctuation = 'punctuation',
  Whitespace = 'whitespace',
  Unknown = 'unknown'
}

export interface Token {
  type: TokenType;
  value: string;
  start: number;
  end: number;
  line: number;
}
```

### 3.2 高亮器实现

```typescript
// src/highlight/syntax.ts

import { Token, TokenType } from './token';

export class TypeScriptHighlighter {
  private keywords = new Set([
    'abstract', 'as', 'async', 'await', 'break', 'case', 'catch', 'class',
    'const', 'continue', 'debugger', 'default', 'delete', 'do', 'else',
    'enum', 'export', 'extends', 'false', 'finally', 'for', 'from',
    'function', 'get', 'if', 'implements', 'import', 'in', 'instanceof',
    'interface', 'let', 'module', 'namespace', 'new', 'null', 'of',
    'package', 'private', 'protected', 'public', 'readonly', 'return',
    'set', 'static', 'super', 'switch', 'this', 'throw', 'true', 'try',
    'type', 'typeof', 'undefined', 'var', 'void', 'while', 'with', 'yield'
  ]);

  tokenizeLine(line: string, lineIndex: number): Token[] {
    const tokens: Token[] = [];
    let pos = 0;

    while (pos < line.length) {
      let token: Token | null = null;
      const char = line[pos];

      // 空白
      if (/\s/.test(char)) {
        const start = pos;
        while (pos < line.length && /\s/.test(line[pos])) pos++;
        token = this.createToken(TokenType.Whitespace, line, start, pos, lineIndex);
      }
      // 单行注释
      else if (char === '/' && line[pos + 1] === '/') {
        token = this.createToken(TokenType.Comment, line, pos, line.length, lineIndex);
        pos = line.length;
      }
      // 多行注释开始
      else if (char === '/' && line[pos + 1] === '*') {
        const start = pos;
        pos += 2;
        while (pos < line.length && !(line[pos] === '*' && line[pos + 1] === '/')) pos++;
        pos += 2;
        token = this.createToken(TokenType.Comment, line, start, pos, lineIndex);
      }
      // 字符串
      else if (char === '"' || char === "'" || char === '`') {
        const quote = char;
        const start = pos;
        pos++;
        while (pos < line.length) {
          if (line[pos] === '\\') { pos += 2; continue; }
          if (line[pos] === quote) { pos++; break; }
          pos++;
        }
        token = this.createToken(TokenType.String, line, start, pos, lineIndex);
      }
      // 数字
      else if (/\d/.test(char)) {
        const start = pos;
        while (pos < line.length && /[\d.xXeE_]/.test(line[pos])) pos++;
        token = this.createToken(TokenType.Number, line, start, pos, lineIndex);
      }
      // 标识符/关键字
      else if (/[a-zA-Z_$]/.test(char)) {
        const start = pos;
        while (pos < line.length && /[a-zA-Z0-9_$]/.test(line[pos])) pos++;
        const value = line.substring(start, pos);
        const type = this.keywords.has(value) ? TokenType.Keyword : TokenType.Identifier;
        token = this.createToken(type, line, start, pos, lineIndex);
      }
      // 操作符
      else if ('+-*/%=<>!&|^~?:'.includes(char)) {
        const start = pos;
        while (pos < line.length && '+-*/%=<>!&|^~?:'.includes(line[pos])) pos++;
        token = this.createToken(TokenType.Operator, line, start, pos, lineIndex);
      }
      // 标点
      else {
        token = this.createToken(TokenType.Punctuation, line, pos, pos + 1, lineIndex);
        pos++;
      }

      if (token) tokens.push(token);
    }

    return tokens;
  }

  tokenizeDocument(lines: string[]): Token[][] {
    return lines.map((line, i) => this.tokenizeLine(line, i));
  }

  private createToken(
    type: TokenType, line: string, start: number, end: number, lineIndex: number
  ): Token {
    return { type, value: line.substring(start, end), start, end, line: lineIndex };
  }
}
```

## 4. 渲染开发

```typescript
// src/render/canvas.ts

import { EditorState, RenderConfig, Token, TokenType } from '../core/types';

export class CanvasRenderer {
  private ctx: CanvasRenderingContext2D;
  private config: Required<RenderConfig>;
  private charWidth: number = 0;
  private lineHeight: number = 0;

  constructor(private canvas: HTMLCanvasElement, config?: Partial<RenderConfig>) {
    this.ctx = canvas.getContext('2d')!;
    this.config = {
      fontSize: 14,
      fontFamily: 'Consolas, Monaco, monospace',
      lineHeight: 1.5,
      tabSize: 4,
      padding: 10,
      showLineNumbers: true,
      lineNumberWidth: 50,
      ...config
    };
    this.measureFont();
  }

  render(state: EditorState): void {
    const { ctx, canvas, config } = this;

    // 清除
    ctx.fillStyle = '#1e1e1e';
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    ctx.font = `${config.fontSize}px ${config.fontFamily}`;

    const { tokens, cursors, selections, scroll } = state;
    const startLine = Math.floor(scroll.top / this.lineHeight);
    const visibleLines = Math.ceil(canvas.height / this.lineHeight);
    const endLine = Math.min(startLine + visibleLines, tokens.length);

    // 行号背景
    if (config.showLineNumbers) {
      ctx.fillStyle = '#252526';
      ctx.fillRect(0, 0, config.lineNumberWidth, canvas.height);
    }

    // 绘制行
    for (let i = startLine; i < endLine; i++) {
      const y = (i - startLine) * this.lineHeight + config.padding;

      // 行号
      if (config.showLineNumbers) {
        ctx.fillStyle = '#858585';
        ctx.textAlign = 'right';
        ctx.fillText(String(i + 1), config.lineNumberWidth - 10, y + config.fontSize);
        ctx.textAlign = 'left';
      }

      // 代码
      let x = config.lineNumberWidth + config.padding;
      for (const token of tokens[i] || []) {
        ctx.fillStyle = this.getTokenColor(token.type);
        ctx.fillText(token.value, x, y + config.fontSize);
        x += token.value.length * this.charWidth;
      }
    }

    // 选区
    for (const sel of selections) {
      this.drawSelection(sel, startLine, scroll);
    }

    // 光标
    for (const cursor of cursors) {
      if (cursor.visible) this.drawCursor(cursor, startLine, scroll);
    }
  }

  private drawSelection(sel: any, startLine: number, scroll: any): void {
    this.ctx.fillStyle = 'rgba(38, 79, 120, 0.5)';
    for (let i = sel.start.line; i <= sel.end.line; i++) {
      if (i < startLine) continue;
      const y = (i - startLine) * this.lineHeight + this.config.padding;
      const startCol = i === sel.start.line ? sel.start.column : 0;
      const endCol = i === sel.end.line ? sel.end.column : 100;
      const x = this.config.lineNumberWidth + this.config.padding + startCol * this.charWidth;
      this.ctx.fillRect(x, y, (endCol - startCol) * this.charWidth, this.lineHeight);
    }
  }

  private drawCursor(cursor: any, startLine: number, scroll: any): void {
    if (cursor.position.line < startLine) return;
    const x = this.config.lineNumberWidth + this.config.padding + cursor.position.column * this.charWidth;
    const y = (cursor.position.line - startLine) * this.lineHeight + this.config.padding;
    this.ctx.fillStyle = '#aeafad';
    this.ctx.fillRect(x, y, 2, this.lineHeight);
  }

  private getTokenColor(type: string): string {
    const colors: Record<string, string> = {
      keyword: '#569cd6',
      identifier: '#d4d4d4',
      string: '#ce9178',
      number: '#b5cea8',
      comment: '#6a9955',
      operator: '#d4d4d4',
      punctuation: '#d4d4d4',
      whitespace: 'transparent',
      unknown: '#d4d4d4'
    };
    return colors[type] || '#d4d4d4';
  }

  private measureFont(): void {
    this.ctx.font = `${this.config.fontSize}px ${this.config.fontFamily}`;
    const metrics = this.ctx.measureText('M');
    this.charWidth = metrics.width;
    this.lineHeight = this.config.fontSize * this.config.lineHeight;
  }
}
```

## 5. 编辑器主类

```typescript
// src/editor.ts

import { DocumentModel } from './core/document';
import { CursorManager } from './core/cursor';
import { TypeScriptHighlighter } from './highlight/syntax';
import { CanvasRenderer } from './render/canvas';
import { EditorOptions, EditorState, EditOperation } from './core/types';

export class Editor {
  private document: DocumentModel;
  private cursorManager: CursorManager;
  private highlighter: TypeScriptHighlighter;
  private renderer: CanvasRenderer;
  private undoStack: EditOperation[] = [];
  private redoStack: EditOperation[] = [];

  constructor(container: HTMLElement, options?: EditorOptions) {
    const canvas = document.createElement('canvas');
    canvas.width = container.clientWidth || 800;
    canvas.height = container.clientHeight || 600;
    container.appendChild(canvas);

    this.document = new DocumentModel(options?.initialContent || '');
    this.cursorManager = new CursorManager(this.document);
    this.highlighter = new TypeScriptHighlighter();
    this.renderer = new CanvasRenderer(canvas, options?.renderConfig);

    this.bindEvents();
    this.render();
  }

  private bindEvents(): void {
    document.addEventListener('keydown', this.handleKeyDown.bind(this));
  }

  private handleKeyDown(e: KeyboardEvent): void {
    if (e.ctrlKey || e.metaKey) {
      switch (e.key) {
        case 'z': e.preventDefault(); this.undo(); return;
        case 'y': e.preventDefault(); this.redo(); return;
        case 'a': e.preventDefault(); this.cursorManager.selectAll(); this.render(); return;
      }
    }

    switch (e.key) {
      case 'ArrowLeft': this.cursorManager.moveLeft(); break;
      case 'ArrowRight': this.cursorManager.moveRight(); break;
      case 'ArrowUp': this.cursorManager.moveUp(); break;
      case 'ArrowDown': this.cursorManager.moveDown(); break;
      case 'Backspace': this.handleBackspace(); break;
      case 'Delete': this.handleDelete(); break;
      case 'Enter': this.handleNewline(); break;
      case 'Tab': this.handleTab(); break;
      default:
        if (e.key.length === 1 && !e.ctrlKey && !e.metaKey) {
          this.handleChar(e.key);
        }
        return;
    }
    e.preventDefault();
    this.render();
  }

  private handleChar(char: string): void {
    const pos = this.cursorManager.primary.position;
    this.pushUndo(this.document.insert(pos, char));
    this.cursorManager.moveRight();
    this.render();
  }

  private handleBackspace(): void {
    const { line, column } = this.cursorManager.primary.position;
    if (column > 0) {
      this.pushUndo(this.document.delete({ start: { line, column: column - 1 }, end: { line, column } }));
      this.cursorManager.moveLeft();
    } else if (line > 0) {
      const prevLen = this.document.getLine(line - 1).length;
      this.pushUndo(this.document.delete({ start: { line: line - 1, column: prevLen }, end: { line, column: 0 } }));
      this.cursorManager.moveTo({ line: line - 1, column: prevLen });
    }
  }

  private handleDelete(): void {
    const { line, column } = this.cursorManager.primary.position;
    const lineLen = this.document.getLine(line).length;
    if (column < lineLen) {
      this.pushUndo(this.document.delete({ start: { line, column }, end: { line, column: column + 1 } }));
    } else if (line < this.document.getLineCount() - 1) {
      this.pushUndo(this.document.delete({ start: { line, column }, end: { line: line + 1, column: 0 } }));
    }
  }

  private handleNewline(): void {
    const pos = this.cursorManager.primary.position;
    this.pushUndo(this.document.insert(pos, '\n'));
    this.cursorManager.moveTo({ line: pos.line + 1, column: 0 });
  }

  private handleTab(): void {
    const pos = this.cursorManager.primary.position;
    this.pushUndo(this.document.insert(pos, '  '));
    this.cursorManager.moveRight(2);
  }

  private pushUndo(op: EditOperation): void {
    this.undoStack.push(op);
    this.redoStack = [];
  }

  undo(): void {
    const op = this.undoStack.pop();
    if (op) {
      this.document.delete(op.range);
      this.redoStack.push(op);
      this.cursorManager.moveTo(op.range.start);
      this.render();
    }
  }

  redo(): void {
    const op = this.redoStack.pop();
    if (op) {
      this.document.insert(op.range.start, op.text);
      this.undoStack.push(op);
      this.render();
    }
  }

  render(): void {
    const lines = [];
    for (let i = 0; i < this.document.getLineCount(); i++) {
      lines.push(this.document.getLine(i));
    }

    const state: EditorState = {
      document: this.document,
      cursors: [this.cursorManager.primary],
      selections: this.cursorManager.getSelection() ? [this.cursorManager.getSelection()!] : [],
      tokens: this.highlighter.tokenizeDocument(lines),
      scroll: { top: 0, left: 0 },
      viewport: { topLine: 0, bottomLine: this.document.getLineCount(), leftColumn: 0 },
      config: {}
    };

    this.renderer.render(state);
  }

  getContent(): string {
    return this.document.getText();
  }

  setContent(content: string): void {
    this.document = new DocumentModel(content);
    this.cursorManager = new CursorManager(this.document);
    this.undoStack = [];
    this.redoStack = [];
    this.render();
  }
}
```

## 6. 入口文件

```typescript
// src/index.ts

export { Editor } from './editor';
export { DocumentModel } from './core/document';
export { CursorManager } from './core/cursor';
export { TypeScriptHighlighter } from './highlight/syntax';
export { CanvasRenderer } from './render/canvas';
export * from './core/types';
```

## 7. 构建与运行

```bash
# 编译 TypeScript
npm run build

# 运行测试
npm test

# 开发模式（监听文件变化）
npm run dev

# 构建生产版本
npm run build -- --mode production
```

## 8. 示例文件

```html
<!-- examples/basic.html -->
<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <title>Code Editor Demo</title>
  <style>
    body { margin: 0; padding: 20px; background: #1e1e1e; font-family: sans-serif; }
    h1 { color: #d4d4d4; margin-bottom: 10px; }
    #editor { width: 900px; height: 600px; border: 1px solid #333; }
    .info { color: #858585; margin-top: 10px; font-size: 14px; }
  </style>
</head>
<body>
  <h1>Code Editor</h1>
  <div id="editor"></div>
  <div class="info">
    快捷键: Ctrl+Z (撤销) | Ctrl+Y (重做) | Ctrl+A (全选)
  </div>
  <script src="../dist/index.js"></script>
  <script>
    const editor = new Editor(document.getElementById('editor'), {
      initialContent: `// TypeScript Code Editor
// 一个基于 Canvas 的代码编辑器

interface User {
  id: number;
  name: string;
  email: string;
}

function greet(user: User): string {
  return \`Hello, \${user.name}!\`;
}

const users: User[] = [
  { id: 1, name: "Alice", email: "alice@example.com" },
  { id: 2, name: "Bob", email: "bob@example.com" },
];

// 遍历用户并打印问候
for (const user of users) {
  console.log(greet(user));
}

// 计算斐波那契数列
function fibonacci(n: number): number {
  if (n <= 1) return n;
  return fibonacci(n - 1) + fibonacci(n - 2);
}

console.log("Fibonacci(10) =", fibonacci(10));`
    });
  </script>
</body>
</html>
```

## 9. 开发注意事项

1. **Canvas 性能**：避免每帧重绘整个画布，使用脏区域检测
2. **内存管理**：及时释放不用的对象，避免内存泄漏
3. **浏览器兼容**：测试主流浏览器（Chrome、Firefox、Safari）
4. **输入法支持**：预留 IME 事件处理接口
5. **可访问性**：提供键盘导航和屏幕阅读器支持

## 10. 未来扩展

1. **多文件支持**：标签页切换
2. **查找替换**：正则表达式支持
3. **代码折叠**：折叠/展开代码块
4. **自动补全**：智能代码补全
5. **主题系统**：自定义主题颜色
6. **插件系统**：可扩展的插件架构
