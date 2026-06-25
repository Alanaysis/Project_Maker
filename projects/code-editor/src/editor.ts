// 编辑器主类 - 整合所有模块

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
    // 创建 Canvas 元素
    const canvas = document.createElement('canvas');
    canvas.width = container.clientWidth || 800;
    canvas.height = container.clientHeight || 600;
    container.appendChild(canvas);

    // 初始化各模块
    this.document = new DocumentModel(options?.initialContent || '');
    this.cursorManager = new CursorManager(this.document);
    this.highlighter = new TypeScriptHighlighter();
    this.renderer = new CanvasRenderer(canvas, options?.renderConfig);

    // 绑定键盘事件
    this.bindEvents();

    // 初始渲染
    this.render();
  }

  /**
   * 绑定键盘事件
   */
  private bindEvents(): void {
    document.addEventListener('keydown', this.handleKeyDown.bind(this));
  }

  /**
   * 处理键盘事件
   */
  private handleKeyDown(e: KeyboardEvent): void {
    // 快捷键处理
    if (e.ctrlKey || e.metaKey) {
      switch (e.key) {
        case 'z':
          e.preventDefault();
          this.undo();
          return;
        case 'y':
          e.preventDefault();
          this.redo();
          return;
        case 'a':
          e.preventDefault();
          this.cursorManager.selectAll();
          this.render();
          return;
      }
    }

    // 普通按键处理
    switch (e.key) {
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
        if (e.key.length === 1 && !e.ctrlKey && !e.metaKey) {
          this.handleChar(e.key);
        }
        return;
    }

    e.preventDefault();
    this.render();
  }

  /**
   * 处理字符输入
   */
  private handleChar(char: string): void {
    const pos = this.cursorManager.primary.position;
    this.pushUndo(this.document.insert(pos, char));
    this.cursorManager.moveRight();
    this.render();
  }

  /**
   * 处理退格键
   */
  private handleBackspace(): void {
    const { line, column } = this.cursorManager.primary.position;

    if (column > 0) {
      // 删除当前行的字符
      const range = {
        start: { line, column: column - 1 },
        end: { line, column }
      };
      this.pushUndo(this.document.delete(range));
      this.cursorManager.moveLeft();
    } else if (line > 0) {
      // 合并到上一行
      const prevLen = this.document.getLine(line - 1).length;
      const range = {
        start: { line: line - 1, column: prevLen },
        end: { line, column: 0 }
      };
      this.pushUndo(this.document.delete(range));
      this.cursorManager.moveTo({ line: line - 1, column: prevLen });
    }
  }

  /**
   * 处理删除键
   */
  private handleDelete(): void {
    const { line, column } = this.cursorManager.primary.position;
    const lineLen = this.document.getLine(line).length;

    if (column < lineLen) {
      // 删除当前行的字符
      const range = {
        start: { line, column },
        end: { line, column: column + 1 }
      };
      this.pushUndo(this.document.delete(range));
    } else if (line < this.document.getLineCount() - 1) {
      // 合并下一行
      const range = {
        start: { line, column },
        end: { line: line + 1, column: 0 }
      };
      this.pushUndo(this.document.delete(range));
    }
  }

  /**
   * 处理回车键
   */
  private handleNewline(): void {
    const pos = this.cursorManager.primary.position;
    this.pushUndo(this.document.insert(pos, '\n'));
    this.cursorManager.moveTo({ line: pos.line + 1, column: 0 });
  }

  /**
   * 处理 Tab 键
   */
  private handleTab(): void {
    const pos = this.cursorManager.primary.position;
    this.pushUndo(this.document.insert(pos, '  '));
    this.cursorManager.moveRight(2);
  }

  /**
   * 添加撤销记录
   */
  private pushUndo(op: EditOperation): void {
    this.undoStack.push(op);
    this.redoStack = [];
  }

  /**
   * 撤销
   */
  undo(): void {
    const op = this.undoStack.pop();
    if (op) {
      this.document.delete(op.range);
      this.redoStack.push(op);
      this.cursorManager.moveTo(op.range.start);
      this.render();
    }
  }

  /**
   * 重做
   */
  redo(): void {
    const op = this.redoStack.pop();
    if (op) {
      this.document.insert(op.range.start, op.text);
      this.undoStack.push(op);
      this.render();
    }
  }

  /**
   * 渲染编辑器
   */
  render(): void {
    // 获取所有行
    const lines = [];
    for (let i = 0; i < this.document.getLineCount(); i++) {
      lines.push(this.document.getLine(i));
    }

    // 语法高亮
    const tokens = this.highlighter.tokenizeDocument(lines);

    // 构建状态
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

    // 渲染
    this.renderer.render(state);
  }

  /**
   * 获取编辑器内容
   */
  getContent(): string {
    return this.document.getText();
  }

  /**
   * 设置编辑器内容
   */
  setContent(content: string): void {
    this.document = new DocumentModel(content);
    this.cursorManager = new CursorManager(this.document);
    this.undoStack = [];
    this.redoStack = [];
    this.render();
  }
}
