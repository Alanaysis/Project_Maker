# 代码编辑器实现指南

## 1. 项目初始化

### 1.1 TypeScript 配置

```json
// tsconfig.json
{
  "compilerOptions": {
    "target": "ES2020",
    "module": "commonjs",
    "lib": ["ES2020", "DOM"],
    "outDir": "./dist",
    "rootDir": "./src",
    "strict": true,
    "esModuleInterop": true,
    "declaration": true,
    "declarationMap": true,
    "sourceMap": true
  },
  "include": ["src/**/*"],
  "exclude": ["node_modules", "dist", "tests"]
}
```

### 1.2 依赖

```json
// package.json
{
  "name": "code-editor",
  "version": "1.0.0",
  "scripts": {
    "build": "tsc",
    "test": "jest",
    "dev": "ts-node src/index.ts"
  },
  "devDependencies": {
    "typescript": "^5.0.0",
    "jest": "^29.0.0",
    "ts-jest": "^29.0.0",
    "@types/jest": "^29.0.0"
  }
}
```

## 2. 核心实现

### 2.1 Document Model 实现

```typescript
// src/core/document.ts

export class DocumentModel implements Document {
  private lines: string[] = [''];

  constructor(initialContent?: string) {
    if (initialContent) {
      this.lines = initialContent.split('\n');
    }
  }

  getLine(lineNumber: number): string {
    if (lineNumber < 0 || lineNumber >= this.lines.length) {
      throw new Error(`Invalid line number: ${lineNumber}`);
    }
    return this.lines[lineNumber];
  }

  getLineCount(): number {
    return this.lines.length;
  }

  getText(): string {
    return this.lines.join('\n');
  }

  insert(position: Position, text: string): EditOperation {
    const { line, column } = position;

    // 验证位置
    if (line < 0 || line >= this.lines.length) {
      throw new Error(`Invalid position: line ${line}`);
    }

    const currentLine = this.lines[line];
    if (column < 0 || column > currentLine.length) {
      throw new Error(`Invalid position: column ${column}`);
    }

    // 处理多行插入
    const insertLines = text.split('\n');
    const before = currentLine.substring(0, column);
    const after = currentLine.substring(column);

    if (insertLines.length === 1) {
      // 单行插入
      this.lines[line] = before + text + after;
    } else {
      // 多行插入
      this.lines[line] = before + insertLines[0];
      const newLines = insertLines.slice(1);
      newLines[newLines.length - 1] += after;
      this.lines.splice(line + 1, 0, ...newLines);
    }

    // 返回操作记录（用于撤销）
    return {
      range: { start: position, end: position },
      text,
      inverse: {
        range: {
          start: position,
          end: this.positionAt(
            this.offsetAt(position) + text.length
          )
        },
        text: '',
        inverse: null as any
      }
    };
  }

  delete(range: Range): EditOperation {
    const { start, end } = range;

    // 获取被删除的文本
    const deletedText = this.getTextInRange(range);

    // 执行删除
    if (start.line === end.line) {
      // 单行删除
      const line = this.lines[start.line];
      this.lines[start.line] =
        line.substring(0, start.column) + line.substring(end.column);
    } else {
      // 多行删除
      const firstLine = this.lines[start.line].substring(0, start.column);
      const lastLine = this.lines[end.line].substring(end.column);
      this.lines.splice(
        start.line,
        end.line - start.line + 1,
        firstLine + lastLine
      );
    }

    return {
      range,
      text: deletedText,
      inverse: {
        range: { start, end: start },
        text: deletedText,
        inverse: null as any
      }
    };
  }

  positionAt(offset: number): Position {
    let remaining = offset;

    for (let line = 0; line < this.lines.length; line++) {
      const lineLength = this.lines[line].length + 1; // +1 for newline
      if (remaining < lineLength) {
        return { line, column: remaining };
      }
      remaining -= lineLength;
    }

    // 返回最后一行末尾
    const lastLine = this.lines.length - 1;
    return { line: lastLine, column: this.lines[lastLine].length };
  }

  offsetAt(position: Position): number {
    let offset = 0;

    for (let i = 0; i < position.line; i++) {
      offset += this.lines[i].length + 1;
    }

    return offset + position.column;
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
}
```

### 2.2 Cursor Manager 实现

```typescript
// src/core/cursor.ts

export class CursorManager {
  private cursors: Cursor[] = [];
  private primaryIndex: number = 0;

  constructor(private document: DocumentModel) {
    // 初始化一个光标在 (0, 0)
    this.cursors.push({
      position: { line: 0, column: 0 },
      visible: true
    });
  }

  get primary(): Cursor {
    return this.cursors[this.primaryIndex];
  }

  moveTo(position: Position): void {
    // 验证并修正位置
    const validPosition = this.validatePosition(position);
    this.primary.position = validPosition;
    this.primary.selection = undefined;
  }

  moveUp(lines: number = 1): void {
    const { line, column } = this.primary.position;
    const newLine = Math.max(0, line - lines);
    const maxColumn = this.document.getLine(newLine).length;
    const newColumn = Math.min(column, maxColumn);

    this.moveTo({ line: newLine, column: newColumn });
  }

  moveDown(lines: number = 1): void {
    const { line, column } = this.primary.position;
    const maxLine = this.document.getLineCount() - 1;
    const newLine = Math.min(maxLine, line + lines);
    const maxColumn = this.document.getLine(newLine).length;
    const newColumn = Math.min(column, maxColumn);

    this.moveTo({ line: newLine, column: newColumn });
  }

  moveLeft(chars: number = 1): void {
    const { line, column } = this.primary.position;

    if (column >= chars) {
      this.moveTo({ line, column: column - chars });
    } else if (line > 0) {
      // 移动到上一行末尾
      const prevLine = line - 1;
      const prevColumn = this.document.getLine(prevLine).length;
      this.moveTo({ line: prevLine, column: prevColumn });
    }
  }

  moveRight(chars: number = 1): void {
    const { line, column } = this.primary.position;
    const lineLength = this.document.getLine(line).length;

    if (column + chars <= lineLength) {
      this.moveTo({ line, column: column + chars });
    } else if (line < this.document.getLineCount() - 1) {
      // 移动到下一行开头
      this.moveTo({ line: line + 1, column: 0 });
    }
  }

  selectTo(position: Position): void {
    const validPosition = this.validatePosition(position);

    if (!this.primary.selection) {
      // 开始选择
      this.primary.selection = {
        start: { ...this.primary.position },
        end: validPosition
      };
    } else {
      // 扩展选择
      this.primary.selection.end = validPosition;
    }

    this.primary.position = validPosition;
  }

  selectAll(): void {
    const lastLine = this.document.getLineCount() - 1;
    const lastColumn = this.document.getLine(lastLine).length;

    this.primary.selection = {
      start: { line: 0, column: 0 },
      end: { line: lastLine, column: lastColumn }
    };

    this.primary.position = { line: lastLine, column: lastColumn };
  }

  getSelection(): Range | null {
    return this.primary.selection || null;
  }

  private validatePosition(position: Position): Position {
    let { line, column } = position;

    // 限制行范围
    line = Math.max(0, Math.min(line, this.document.getLineCount() - 1));

    // 限制列范围
    const lineLength = this.document.getLine(line).length;
    column = Math.max(0, Math.min(column, lineLength));

    return { line, column };
  }
}
```

### 2.3 Syntax Highlighter 实现

```typescript
// src/highlight/syntax.ts

export class TypeScriptHighlighter implements SyntaxHighlighter {
  private stateStack: State[] = [];

  // TypeScript 关键字
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
    let position = 0;
    let state = this.stateStack[lineIndex] || { type: StateType.Normal };

    while (position < line.length) {
      const char = line[position];
      let token: Token | null = null;

      // 空白字符
      if (/\s/.test(char)) {
        const start = position;
        while (position < line.length && /\s/.test(line[position])) {
          position++;
        }
        token = {
          type: TokenType.Whitespace,
          value: line.substring(start, position),
          start,
          end: position,
          line: lineIndex
        };
      }
      // 单行注释
      else if (char === '/' && line[position + 1] === '/') {
        token = {
          type: TokenType.Comment,
          value: line.substring(position),
          start: position,
          end: line.length,
          line: lineIndex
        };
        position = line.length;
      }
      // 多行注释开始
      else if (char === '/' && line[position + 1] === '*') {
        const start = position;
        position += 2;

        while (position < line.length) {
          if (line[position] === '*' && line[position + 1] === '/') {
            position += 2;
            break;
          }
          position++;
        }

        token = {
          type: TokenType.Comment,
          value: line.substring(start, position),
          start,
          end: position,
          line: lineIndex
        };
      }
      // 字符串
      else if (char === '"' || char === "'" || char === '`') {
        const quote = char;
        const start = position;
        position++;

        while (position < line.length) {
          if (line[position] === '\\') {
            position += 2;
            continue;
          }
          if (line[position] === quote) {
            position++;
            break;
          }
          position++;
        }

        token = {
          type: TokenType.String,
          value: line.substring(start, position),
          start,
          end: position,
          line: lineIndex
        };
      }
      // 数字
      else if (/\d/.test(char)) {
        const start = position;
        while (position < line.length && /[\d.xXeE_]/.test(line[position])) {
          position++;
        }
        token = {
          type: TokenType.Number,
          value: line.substring(start, position),
          start,
          end: position,
          line: lineIndex
        };
      }
      // 标识符或关键字
      else if (/[a-zA-Z_$]/.test(char)) {
        const start = position;
        while (position < line.length && /[a-zA-Z0-9_$]/.test(line[position])) {
          position++;
        }
        const value = line.substring(start, position);
        token = {
          type: this.keywords.has(value) ? TokenType.Keyword : TokenType.Identifier,
          value,
          start,
          end: position,
          line: lineIndex
        };
      }
      // 操作符
      else if ('+-*/%=<>!&|^~?:'.includes(char)) {
        const start = position;
        position++;
        // 处理多字符操作符
        while (position < line.length && '+-*/%=<>!&|^~?:'.includes(line[position])) {
          position++;
        }
        token = {
          type: TokenType.Operator,
          value: line.substring(start, position),
          start,
          end: position,
          line: lineIndex
        };
      }
      // 标点符号
      else {
        token = {
          type: TokenType.Punctuation,
          value: char,
          start: position,
          end: position + 1,
          line: lineIndex
        };
        position++;
      }

      if (token) {
        tokens.push(token);
      }
    }

    return tokens;
  }

  tokenizeDocument(lines: string[]): Token[][] {
    return lines.map((line, index) => this.tokenizeLine(line, index));
  }
}
```

### 2.4 Canvas Renderer 实现

```typescript
// src/render/canvas.ts

export class CanvasRenderer {
  private ctx: CanvasRenderingContext2D;
  private fontMetrics: TextMetrics;

  // 默认配置
  private config: Required<RenderConfig> = {
    fontSize: 14,
    fontFamily: 'Consolas, Monaco, monospace',
    lineHeight: 1.5,
    tabSize: 4,
    padding: 10,
    showLineNumbers: true,
    lineNumberWidth: 50
  };

  constructor(
    private canvas: HTMLCanvasElement,
    config?: Partial<RenderConfig>
  ) {
    this.ctx = canvas.getContext('2d')!;
    this.config = { ...this.config, ...config };
    this.fontMetrics = this.measureFont();
  }

  render(state: EditorState): void {
    const { ctx, canvas, config } = this;

    // 清除画布
    ctx.fillStyle = '#1e1e1e';
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    // 设置字体
    ctx.font = `${config.fontSize}px ${config.fontFamily}`;

    const { document, cursors, selections, tokens, scroll } = state;
    const { charWidth, lineHeight } = this.fontMetrics;

    // 计算可见行范围
    const startLine = Math.floor(scroll.top / lineHeight);
    const visibleLines = Math.ceil(canvas.height / lineHeight);
    const endLine = Math.min(
      startLine + visibleLines,
      document.getLineCount()
    );

    // 绘制行号背景
    if (config.showLineNumbers) {
      ctx.fillStyle = '#252526';
      ctx.fillRect(0, 0, config.lineNumberWidth, canvas.height);
    }

    // 绘制每一行
    for (let i = startLine; i < endLine; i++) {
      const y = (i - startLine) * lineHeight + config.padding;
      const lineTokens = tokens[i] || [];

      // 绘制行号
      if (config.showLineNumbers) {
        ctx.fillStyle = '#858585';
        ctx.textAlign = 'right';
        ctx.fillText(
          String(i + 1),
          config.lineNumberWidth - 10,
          y + config.fontSize
        );
        ctx.textAlign = 'left';
      }

      // 绘制代码
      let x = config.lineNumberWidth + config.padding;
      for (const token of lineTokens) {
        ctx.fillStyle = this.getTokenColor(token.type);
        ctx.fillText(token.value, x, y + config.fontSize);
        x += token.value.length * charWidth;
      }
    }

    // 绘制选区
    for (const selection of selections) {
      this.drawSelection(selection, startLine, scroll);
    }

    // 绘制光标
    for (const cursor of cursors) {
      if (cursor.visible) {
        this.drawCursor(cursor, startLine, scroll);
      }
    }
  }

  private drawSelection(
    selection: Range,
    startLine: number,
    scroll: ScrollPosition
  ): void {
    const { ctx } = this;
    const { charWidth, lineHeight } = this.fontMetrics;
    const { config } = this;

    ctx.fillStyle = 'rgba(38, 79, 120, 0.5)';

    for (let i = selection.start.line; i <= selection.end.line; i++) {
      if (i < startLine) continue;

      const y = (i - startLine) * lineHeight + config.padding;
      let x = config.lineNumberWidth + config.padding;

      let startCol = 0;
      let endCol = this.document.getLine(i).length;

      if (i === selection.start.line) {
        startCol = selection.start.column;
      }
      if (i === selection.end.line) {
        endCol = selection.end.column;
      }

      x += startCol * charWidth;
      const width = (endCol - startCol) * charWidth;

      ctx.fillRect(x, y, width, lineHeight);
    }
  }

  private drawCursor(
    cursor: Cursor,
    startLine: number,
    scroll: ScrollPosition
  ): void {
    const { ctx } = this;
    const { charWidth, lineHeight } = this.fontMetrics;
    const { config } = this;

    const { line, column } = cursor.position;

    if (line < startLine) return;

    const x = config.lineNumberWidth + config.padding + column * charWidth;
    const y = (line - startLine) * lineHeight + config.padding;

    // 光标闪烁效果
    ctx.fillStyle = '#aeafad';
    ctx.fillRect(x, y, 2, lineHeight);
  }

  private getTokenColor(type: TokenType): string {
    const colors: Record<TokenType, string> = {
      [TokenType.Keyword]: '#569cd6',
      [TokenType.Identifier]: '#d4d4d4',
      [TokenType.String]: '#ce9178',
      [TokenType.Number]: '#b5cea8',
      [TokenType.Comment]: '#6a9955',
      [TokenType.Operator]: '#d4d4d4',
      [TokenType.Punctuation]: '#d4d4d4',
      [TokenType.Whitespace]: 'transparent',
      [TokenType.Unknown]: '#d4d4d4'
    };
    return colors[type] || '#d4d4d4';
  }

  private measureFont(): TextMetrics {
    const { ctx, config } = this;
    ctx.font = `${config.fontSize}px ${config.fontFamily}`;

    const metrics = ctx.measureText('M');
    return {
      charWidth: metrics.width,
      lineHeight: config.fontSize * config.lineHeight,
      baseline: metrics.actualBoundingBoxAscent || config.fontSize * 0.8
    };
  }
}
```

## 3. 编辑器主类

```typescript
// src/editor.ts

export class Editor {
  private document: DocumentModel;
  private cursorManager: CursorManager;
  private highlighter: TypeScriptHighlighter;
  private renderer: CanvasRenderer;
  private undoStack: EditOperation[] = [];
  private redoStack: EditOperation[] = [];

  constructor(container: HTMLElement, options?: EditorOptions) {
    // 创建 Canvas
    const canvas = document.createElement('canvas');
    container.appendChild(canvas);

    // 初始化各模块
    this.document = new DocumentModel(options?.initialContent);
    this.cursorManager = new CursorManager(this.document);
    this.highlighter = new TypeScriptHighlighter();
    this.renderer = new CanvasRenderer(canvas, options?.renderConfig);

    // 绑定事件
    this.bindEvents();

    // 初始渲染
    this.render();
  }

  private bindEvents(): void {
    // 键盘事件
    document.addEventListener('keydown', this.handleKeyDown.bind(this));

    // 焦点事件
    document.addEventListener('focus', () => this.render());
  }

  private handleKeyDown(event: KeyboardEvent): void {
    // 快捷键处理
    if (event.ctrlKey || event.metaKey) {
      switch (event.key) {
        case 'z':
          event.preventDefault();
          this.undo();
          return;
        case 'y':
          event.preventDefault();
          this.redo();
          return;
        case 'a':
          event.preventDefault();
          this.cursorManager.selectAll();
          this.render();
          return;
      }
    }

    // 普通按键处理
    switch (event.key) {
      case 'ArrowLeft':
        this.cursorManager.moveLeft();
        break;
      case 'ArrowRight':
        this.cursorManager.moveRight();
        break;
      case 'ArrowUp':
        this.cursorManager.moveUp();
        break;
      case 'ArrowDown':
        this.cursorManager.moveDown();
        break;
      case 'Backspace':
        this.handleBackspace();
        break;
      case 'Delete':
        this.handleDelete();
        break;
      case 'Enter':
        this.handleNewline();
        break;
      case 'Tab':
        this.handleTab();
        break;
      default:
        if (event.key.length === 1 && !event.ctrlKey && !event.metaKey) {
          this.handleCharInput(event.key);
        }
        return;
    }

    event.preventDefault();
    this.render();
  }

  private handleCharInput(char: string): void {
    const position = this.cursorManager.primary.position;
    const operation = this.document.insert(position, char);
    this.pushUndo(operation);
    this.cursorManager.moveRight();
  }

  private handleBackspace(): void {
    const { line, column } = this.cursorManager.primary.position;

    if (column > 0) {
      const range: Range = {
        start: { line, column: column - 1 },
        end: { line, column }
      };
      const operation = this.document.delete(range);
      this.pushUndo(operation);
      this.cursorManager.moveLeft();
    } else if (line > 0) {
      const prevLineLength = this.document.getLine(line - 1).length;
      const range: Range = {
        start: { line: line - 1, column: prevLineLength },
        end: { line, column: 0 }
      };
      const operation = this.document.delete(range);
      this.pushUndo(operation);
      this.cursorManager.moveTo({ line: line - 1, column: prevLineLength });
    }
  }

  private handleNewline(): void {
    const position = this.cursorManager.primary.position;
    const operation = this.document.insert(position, '\n');
    this.pushUndo(operation);
    this.cursorManager.moveTo({ line: position.line + 1, column: 0 });
  }

  private handleTab(): void {
    const position = this.cursorManager.primary.position;
    const operation = this.document.insert(position, '  ');
    this.pushUndo(operation);
    this.cursorManager.moveRight(2);
  }

  private pushUndo(operation: EditOperation): void {
    this.undoStack.push(operation);
    this.redoStack = [];
  }

  undo(): void {
    const operation = this.undoStack.pop();
    if (operation) {
      this.document.delete(operation.range);
      this.redoStack.push(operation);
      this.cursorManager.moveTo(operation.range.start);
      this.render();
    }
  }

  redo(): void {
    const operation = this.redoStack.pop();
    if (operation) {
      this.document.insert(operation.range.start, operation.text);
      this.undoStack.push(operation);
      this.render();
    }
  }

  private render(): void {
    const lines = [];
    for (let i = 0; i < this.document.getLineCount(); i++) {
      lines.push(this.document.getLine(i));
    }

    const tokens = this.highlighter.tokenizeDocument(lines);

    const state: EditorState = {
      document: this.document,
      cursors: [this.cursorManager.primary],
      selections: this.cursorManager.getSelection()
        ? [this.cursorManager.getSelection()!]
        : [],
      tokens,
      scroll: { top: 0, left: 0 },
      viewport: {
        topLine: 0,
        bottomLine: this.document.getLineCount(),
        leftColumn: 0
      },
      config: {}
    };

    this.renderer.render(state);
  }

  // 公开 API
  getContent(): string {
    return this.document.getText();
  }

  setContent(content: string): void {
    this.document = new DocumentModel(content);
    this.cursorManager = new CursorManager(this.document);
    this.render();
  }
}
```

## 4. 使用示例

```html
<!-- examples/basic.html -->
<!DOCTYPE html>
<html>
<head>
  <title>Code Editor</title>
  <style>
    body {
      margin: 0;
      padding: 20px;
      background: #1e1e1e;
    }
    #editor {
      width: 800px;
      height: 600px;
      border: 1px solid #333;
    }
  </style>
</head>
<body>
  <div id="editor"></div>
  <script src="../dist/editor.js"></script>
  <script>
    const editor = new Editor(document.getElementById('editor'), {
      initialContent: '// Hello World\nfunction greet(name) {\n  console.log(`Hello, ${name}!`);\n}\n\ngreet("TypeScript");'
    });
  </script>
</body>
</html>
```
