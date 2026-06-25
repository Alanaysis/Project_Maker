// Canvas 渲染器 - 负责将编辑器状态渲染到 Canvas

import { EditorState, RenderConfig, Token, TokenType, Range, Cursor, ScrollPosition } from '../core/types';

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

  /**
   * 渲染编辑器状态
   */
  render(state: EditorState): void {
    const { ctx, canvas, config } = this;

    // 清除画布
    ctx.fillStyle = '#1e1e1e';
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    // 设置字体
    ctx.font = `${config.fontSize}px ${config.fontFamily}`;

    const { tokens, cursors, selections, scroll } = state;

    // 计算可见行范围
    const startLine = Math.floor(scroll.top / this.lineHeight);
    const visibleLines = Math.ceil(canvas.height / this.lineHeight);
    const endLine = Math.min(startLine + visibleLines, tokens.length);

    // 绘制行号背景
    if (config.showLineNumbers) {
      ctx.fillStyle = '#252526';
      ctx.fillRect(0, 0, config.lineNumberWidth, canvas.height);
    }

    // 绘制每一行
    for (let i = startLine; i < endLine; i++) {
      const y = (i - startLine) * this.lineHeight + config.padding;

      // 绘制行号
      if (config.showLineNumbers) {
        ctx.fillStyle = '#858585';
        ctx.textAlign = 'right';
        ctx.fillText(String(i + 1), config.lineNumberWidth - 10, y + config.fontSize);
        ctx.textAlign = 'left';
      }

      // 绘制代码
      let x = config.lineNumberWidth + config.padding;
      for (const token of tokens[i] || []) {
        ctx.fillStyle = this.getTokenColor(token.type);
        ctx.fillText(token.value, x, y + config.fontSize);
        x += token.value.length * this.charWidth;
      }
    }

    // 绘制选区
    for (const sel of selections) {
      this.drawSelection(sel, startLine, scroll);
    }

    // 绘制光标
    for (const cursor of cursors) {
      if (cursor.visible) {
        this.drawCursor(cursor, startLine, scroll);
      }
    }
  }

  /**
   * 绘制选区
   */
  private drawSelection(sel: Range, startLine: number, scroll: ScrollPosition): void {
    const { ctx } = this;
    ctx.fillStyle = 'rgba(38, 79, 120, 0.5)';

    for (let i = sel.start.line; i <= sel.end.line; i++) {
      if (i < startLine) continue;

      const y = (i - startLine) * this.lineHeight + this.config.padding;
      const startCol = i === sel.start.line ? sel.start.column : 0;
      const endCol = i === sel.end.line ? sel.end.column : 100;
      const x = this.config.lineNumberWidth + this.config.padding + startCol * this.charWidth;

      ctx.fillRect(x, y, (endCol - startCol) * this.charWidth, this.lineHeight);
    }
  }

  /**
   * 绘制光标
   */
  private drawCursor(cursor: Cursor, startLine: number, scroll: ScrollPosition): void {
    if (cursor.position.line < startLine) return;

    const x = this.config.lineNumberWidth + this.config.padding + cursor.position.column * this.charWidth;
    const y = (cursor.position.line - startLine) * this.lineHeight + this.config.padding;

    this.ctx.fillStyle = '#aeafad';
    this.ctx.fillRect(x, y, 2, this.lineHeight);
  }

  /**
   * 获取 Token 颜色
   */
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

  /**
   * 测量字体尺寸
   */
  private measureFont(): void {
    this.ctx.font = `${this.config.fontSize}px ${this.config.fontFamily}`;
    const metrics = this.ctx.measureText('M');
    this.charWidth = metrics.width;
    this.lineHeight = this.config.fontSize * this.config.lineHeight;
  }
}
