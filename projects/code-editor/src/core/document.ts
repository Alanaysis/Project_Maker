// 文档模型 - 管理文本内容和编辑操作

import { Position, Range, EditOperation } from './types';

export class DocumentModel {
  private lines: string[];

  constructor(content: string = '') {
    this.lines = content ? content.split('\n') : [''];
  }

  /**
   * 获取指定行内容
   */
  getLine(lineNumber: number): string {
    this.validateLineNumber(lineNumber);
    return this.lines[lineNumber];
  }

  /**
   * 获取总行数
   */
  getLineCount(): number {
    return this.lines.length;
  }

  /**
   * 获取全部文本
   */
  getText(): string {
    return this.lines.join('\n');
  }

  /**
   * 在指定位置插入文本
   */
  insert(position: Position, text: string): EditOperation {
    this.validatePosition(position);

    const { line, column } = position;
    const currentLine = this.lines[line];
    const before = currentLine.substring(0, column);
    const after = currentLine.substring(column);

    const insertLines = text.split('\n');

    if (insertLines.length === 1) {
      // 单行插入
      this.lines[line] = before + text + after;
    } else {
      // 多行插入
      this.lines[line] = before + insertLines[0];
      const middleLines = insertLines.slice(1, -1);
      const lastLine = insertLines[insertLines.length - 1] + after;
      this.lines.splice(line + 1, 0, ...middleLines, lastLine);
    }

    return this.createOperation(position, text);
  }

  /**
   * 删除指定范围的文本
   */
  delete(range: Range): EditOperation {
    const { start, end } = range;
    const deletedText = this.getTextInRange(range);

    if (start.line === end.line) {
      // 单行删除
      const line = this.lines[start.line];
      this.lines[start.line] =
        line.substring(0, start.column) + line.substring(end.column);
    } else {
      // 多行删除
      const firstLine = this.lines[start.line].substring(0, start.column);
      const lastLine = this.lines[end.line].substring(end.column);
      this.lines.splice(start.line, end.line - start.line + 1, firstLine + lastLine);
    }

    return this.createOperation(start, deletedText);
  }

  /**
   * 替换指定范围的文本
   */
  replace(range: Range, text: string): EditOperation {
    this.delete(range);
    return this.insert(range.start, text);
  }

  /**
   * 位置转偏移量
   */
  offsetAt(position: Position): number {
    let offset = 0;
    for (let i = 0; i < position.line; i++) {
      offset += this.lines[i].length + 1; // +1 for newline
    }
    return offset + position.column;
  }

  /**
   * 偏移量转位置
   */
  positionAt(offset: number): Position {
    let remaining = offset;
    for (let line = 0; line < this.lines.length; line++) {
      const lineLength = this.lines[line].length + 1;
      if (remaining < lineLength) {
        return { line, column: remaining };
      }
      remaining -= lineLength;
    }
    // 返回最后一行末尾
    const lastLine = this.lines.length - 1;
    return { line: lastLine, column: this.lines[lastLine].length };
  }

  /**
   * 验证行号
   */
  private validateLineNumber(lineNumber: number): void {
    if (lineNumber < 0 || lineNumber >= this.lines.length) {
      throw new Error(`Invalid line number: ${lineNumber}`);
    }
  }

  /**
   * 验证位置
   */
  private validatePosition(position: Position): void {
    this.validateLineNumber(position.line);
    const lineLength = this.lines[position.line].length;
    if (position.column < 0 || position.column > lineLength) {
      throw new Error(`Invalid column: ${position.column}`);
    }
  }

  /**
   * 获取指定范围的文本
   */
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

  /**
   * 创建编辑操作记录
   */
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
