// 语法高亮器 - 基于正则的词法分析

import { Token, TokenType } from './token';

export class TypeScriptHighlighter {
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

  /**
   * 对单行进行词法分析
   */
  tokenizeLine(line: string, lineIndex: number): Token[] {
    const tokens: Token[] = [];
    let pos = 0;

    while (pos < line.length) {
      let token: Token | null = null;
      const char = line[pos];

      // 空白字符
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
          if (line[pos] === '\\') {
            pos += 2;
            continue;
          }
          if (line[pos] === quote) {
            pos++;
            break;
          }
          pos++;
        }
        token = this.createToken(TokenType.String, line, start, pos, lineIndex);
      }
      // 数字
      else if (/\d/.test(char)) {
        const start = pos;
        while (pos < line.length && /[\d.xXeE_a-fA-F]/.test(line[pos])) pos++;
        token = this.createToken(TokenType.Number, line, start, pos, lineIndex);
      }
      // 标识符或关键字
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
      // 标点符号
      else {
        token = this.createToken(TokenType.Punctuation, line, pos, pos + 1, lineIndex);
        pos++;
      }

      if (token) tokens.push(token);
    }

    return tokens;
  }

  /**
   * 对整个文档进行词法分析
   */
  tokenizeDocument(lines: string[]): Token[][] {
    return lines.map((line, i) => this.tokenizeLine(line, i));
  }

  /**
   * 创建 Token
   */
  private createToken(
    type: TokenType,
    line: string,
    start: number,
    end: number,
    lineIndex: number
  ): Token {
    return {
      type,
      value: line.substring(start, end),
      start,
      end,
      line: lineIndex
    };
  }
}
