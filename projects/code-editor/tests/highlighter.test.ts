// Syntax Highlighter 测试

import { TypeScriptHighlighter } from '../src/highlight/syntax';
import { TokenType } from '../src/highlight/token';

describe('TypeScriptHighlighter', () => {
  let highlighter: TypeScriptHighlighter;

  beforeEach(() => {
    highlighter = new TypeScriptHighlighter();
  });

  describe('关键字识别', () => {
    test('应该识别 TypeScript 关键字', () => {
      const tokens = highlighter.tokenizeLine('const let var function class', 0);
      expect(tokens).toHaveLength(9); // 5 关键字 + 4 空格
      expect(tokens[0].type).toBe(TokenType.Keyword);
      expect(tokens[0].value).toBe('const');
      expect(tokens[2].type).toBe(TokenType.Keyword);
      expect(tokens[2].value).toBe('let');
    });

    test('应该识别所有关键字', () => {
      const keywords = ['if', 'else', 'for', 'while', 'return', 'import', 'export'];
      for (const kw of keywords) {
        const tokens = highlighter.tokenizeLine(kw, 0);
        expect(tokens[0].type).toBe(TokenType.Keyword);
      }
    });
  });

  describe('字符串识别', () => {
    test('应该识别双引号字符串', () => {
      const tokens = highlighter.tokenizeLine('const s = "hello";', 0);
      const stringToken = tokens.find(t => t.type === TokenType.String);
      expect(stringToken).toBeDefined();
      expect(stringToken?.value).toBe('"hello"');
    });

    test('应该识别单引号字符串', () => {
      const tokens = highlighter.tokenizeLine("const s = 'world';", 0);
      const stringToken = tokens.find(t => t.type === TokenType.String);
      expect(stringToken).toBeDefined();
      expect(stringToken?.value).toBe("'world'");
    });

    test('应该识别模板字符串', () => {
      const tokens = highlighter.tokenizeLine('const s = `template`;', 0);
      const stringToken = tokens.find(t => t.type === TokenType.String);
      expect(stringToken).toBeDefined();
      expect(stringToken?.value).toBe('`template`');
    });

    test('应该处理转义字符', () => {
      const tokens = highlighter.tokenizeLine('const s = "hello\\"world";', 0);
      const stringToken = tokens.find(t => t.type === TokenType.String);
      expect(stringToken?.value).toBe('"hello\\"world"');
    });
  });

  describe('数字识别', () => {
    test('应该识别整数', () => {
      const tokens = highlighter.tokenizeLine('const n = 42;', 0);
      const numberToken = tokens.find(t => t.type === TokenType.Number);
      expect(numberToken?.value).toBe('42');
    });

    test('应该识别浮点数', () => {
      const tokens = highlighter.tokenizeLine('const n = 3.14;', 0);
      const numberToken = tokens.find(t => t.type === TokenType.Number);
      expect(numberToken?.value).toBe('3.14');
    });

    test('应该识别十六进制数', () => {
      const tokens = highlighter.tokenizeLine('const n = 0xFF;', 0);
      const numberToken = tokens.find(t => t.type === TokenType.Number);
      expect(numberToken?.value).toBe('0xFF');
    });
  });

  describe('注释识别', () => {
    test('应该识别单行注释', () => {
      const tokens = highlighter.tokenizeLine('// comment', 0);
      expect(tokens[0].type).toBe(TokenType.Comment);
      expect(tokens[0].value).toBe('// comment');
    });

    test('应该识别行内注释', () => {
      const tokens = highlighter.tokenizeLine('code // comment', 0);
      const commentToken = tokens.find(t => t.type === TokenType.Comment);
      expect(commentToken?.value).toBe('// comment');
    });
  });

  describe('操作符识别', () => {
    test('应该识别单字符操作符', () => {
      const tokens = highlighter.tokenizeLine('a + b', 0);
      const opToken = tokens.find(t => t.type === TokenType.Operator);
      expect(opToken?.value).toBe('+');
    });

    test('应该识别多字符操作符', () => {
      const tokens = highlighter.tokenizeLine('a === b', 0);
      const opToken = tokens.find(t => t.type === TokenType.Operator);
      expect(opToken?.value).toBe('===');
    });
  });

  describe('标识符识别', () => {
    test('应该识别普通标识符', () => {
      const tokens = highlighter.tokenizeLine('myVariable', 0);
      expect(tokens[0].type).toBe(TokenType.Identifier);
      expect(tokens[0].value).toBe('myVariable');
    });

    test('应该识别带下划线的标识符', () => {
      const tokens = highlighter.tokenizeLine('_private', 0);
      expect(tokens[0].type).toBe(TokenType.Identifier);
      expect(tokens[0].value).toBe('_private');
    });
  });

  describe('完整代码行', () => {
    test('应该正确高亮函数定义', () => {
      const line = 'function greet(name: string): void {';
      const tokens = highlighter.tokenizeLine(line, 0);

      const keywords = tokens.filter(t => t.type === TokenType.Keyword);
      expect(keywords.map(k => k.value)).toEqual(['function', 'void']);

      const identifiers = tokens.filter(t => t.type === TokenType.Identifier);
      expect(identifiers.map(i => i.value)).toEqual(['greet', 'name', 'string']);
    });

    test('应该正确高亮变量声明', () => {
      const line = 'const x: number = 42;';
      const tokens = highlighter.tokenizeLine(line, 0);

      expect(tokens[0].type).toBe(TokenType.Keyword);
      expect(tokens[0].value).toBe('const');

      const numberToken = tokens.find(t => t.type === TokenType.Number);
      expect(numberToken?.value).toBe('42');
    });
  });

  describe('多行文档', () => {
    test('应该正确处理多行代码', () => {
      const lines = [
        'function add(a: number, b: number) {',
        '  return a + b;',
        '}'
      ];

      const allTokens = highlighter.tokenizeDocument(lines);

      expect(allTokens).toHaveLength(3);
      expect(allTokens[0][0].type).toBe(TokenType.Keyword);
      expect(allTokens[0][0].value).toBe('function');
    });
  });
});
