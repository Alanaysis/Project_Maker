// 光标管理器 - 管理光标位置和选择

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

  /**
   * 获取主光标
   */
  get primary(): Cursor {
    return this.cursors[0];
  }

  /**
   * 移动光标到指定位置
   */
  moveTo(position: Position): void {
    const valid = this.validatePosition(position);
    this.primary.position = valid;
    this.primary.selection = undefined;
  }

  /**
   * 光标上移
   */
  moveUp(count: number = 1): void {
    const { line, column } = this.primary.position;
    const newLine = Math.max(0, line - count);
    const maxCol = this.document.getLine(newLine).length;
    this.moveTo({ line: newLine, column: Math.min(column, maxCol) });
  }

  /**
   * 光标下移
   */
  moveDown(count: number = 1): void {
    const { line, column } = this.primary.position;
    const maxLine = this.document.getLineCount() - 1;
    const newLine = Math.min(maxLine, line + count);
    const maxCol = this.document.getLine(newLine).length;
    this.moveTo({ line: newLine, column: Math.min(column, maxCol) });
  }

  /**
   * 光标左移
   */
  moveLeft(count: number = 1): void {
    const { line, column } = this.primary.position;
    if (column >= count) {
      this.moveTo({ line, column: column - count });
    } else if (line > 0) {
      const prevLine = line - 1;
      this.moveTo({ line: prevLine, column: this.document.getLine(prevLine).length });
    }
  }

  /**
   * 光标右移
   */
  moveRight(count: number = 1): void {
    const { line, column } = this.primary.position;
    const lineLen = this.document.getLine(line).length;
    if (column + count <= lineLen) {
      this.moveTo({ line, column: column + count });
    } else if (line < this.document.getLineCount() - 1) {
      this.moveTo({ line: line + 1, column: 0 });
    }
  }

  /**
   * 选择到指定位置
   */
  selectTo(position: Position): void {
    const valid = this.validatePosition(position);
    if (!this.primary.selection) {
      this.primary.selection = { start: { ...this.primary.position }, end: valid };
    } else {
      this.primary.selection.end = valid;
    }
    this.primary.position = valid;
  }

  /**
   * 全选
   */
  selectAll(): void {
    const lastLine = this.document.getLineCount() - 1;
    const lastCol = this.document.getLine(lastLine).length;
    this.primary.selection = {
      start: { line: 0, column: 0 },
      end: { line: lastLine, column: lastCol }
    };
    this.primary.position = { line: lastLine, column: lastCol };
  }

  /**
   * 选择当前行
   */
  selectLine(lineNumber: number): void {
    const lineLen = this.document.getLine(lineNumber).length;
    this.primary.selection = {
      start: { line: lineNumber, column: 0 },
      end: { line: lineNumber, column: lineLen }
    };
    this.primary.position = { line: lineNumber, column: lineLen };
  }

  /**
   * 获取当前选区
   */
  getSelection(): Range | null {
    return this.primary.selection || null;
  }

  /**
   * 验证并修正位置
   */
  private validatePosition(pos: Position): Position {
    let { line, column } = pos;
    line = Math.max(0, Math.min(line, this.document.getLineCount() - 1));
    column = Math.max(0, Math.min(column, this.document.getLine(line).length));
    return { line, column };
  }
}
