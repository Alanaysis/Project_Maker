# 代码编辑器测试指南

## 1. 测试策略

### 1.1 测试金字塔

```
       /\
      /  \  E2E Tests
     /    \  (少量)
    /------\
   /        \  Integration Tests
  /          \  (适量)
 /------------\
/              \  Unit Tests
/______________\  (大量)
```

### 1.2 测试类型

| 类型 | 覆盖范围 | 工具 | 优先级 |
|------|----------|------|--------|
| 单元测试 | 独立函数/类 | Jest | 高 |
| 集成测试 | 模块交互 | Jest | 中 |
| 性能测试 | 渲染性能 | Benchmark | 中 |

## 2. 单元测试

### 2.1 Document Model 测试

```typescript
// tests/document.test.ts

import { DocumentModel } from '../src/core/document';

describe('DocumentModel', () => {
  let doc: DocumentModel;

  beforeEach(() => {
    doc = new DocumentModel();
  });

  describe('构造函数', () => {
    test('空文档应该有一行空内容', () => {
      expect(doc.getLineCount()).toBe(1);
      expect(doc.getLine(0)).toBe('');
    });

    test('应该正确初始化多行内容', () => {
      const doc = new DocumentModel('line1\nline2\nline3');
      expect(doc.getLineCount()).toBe(3);
      expect(doc.getLine(0)).toBe('line1');
      expect(doc.getLine(1)).toBe('line2');
      expect(doc.getLine(2)).toBe('line3');
    });
  });

  describe('insert', () => {
    test('应该在指定位置插入字符', () => {
      doc.insert({ line: 0, column: 0 }, 'hello');
      expect(doc.getLine(0)).toBe('hello');
    });

    test('应该在行中间插入字符', () => {
      doc.insert({ line: 0, column: 0 }, 'hello');
      doc.insert({ line: 0, column: 5 }, ' world');
      expect(doc.getLine(0)).toBe('hello world');
    });

    test('应该处理多行插入', () => {
      doc.insert({ line: 0, column: 0 }, 'line1\nline2');
      expect(doc.getLineCount()).toBe(2);
      expect(doc.getLine(0)).toBe('line1');
      expect(doc.getLine(1)).toBe('line2');
    });

    test('应该在行末插入新行', () => {
      doc.insert({ line: 0, column: 0 }, 'first');
      doc.insert({ line: 0, column: 5 }, '\nsecond');
      expect(doc.getLineCount()).toBe(2);
      expect(doc.getLine(1)).toBe('second');
    });

    test('应该抛出无效位置错误', () => {
      expect(() => {
        doc.insert({ line: -1, column: 0 }, 'x');
      }).toThrow('Invalid position: line -1');

      expect(() => {
        doc.insert({ line: 0, column: 1 }, 'x');
      }).toThrow('Invalid position: column 1');
    });
  });

  describe('delete', () => {
    test('应该删除指定范围的文本', () => {
      doc.insert({ line: 0, column: 0 }, 'hello world');
      doc.delete({
        start: { line: 0, column: 5 },
        end: { line: 0, column: 11 }
      });
      expect(doc.getLine(0)).toBe('hello');
    });

    test('应该处理多行删除', () => {
      doc.insert({ line: 0, column: 0 }, 'line1\nline2\nline3');
      doc.delete({
        start: { line: 0, column: 3 },
        end: { line: 2, column: 2 }
      });
      expect(doc.getLineCount()).toBe(1);
      expect(doc.getLine(0)).toBe('line3');
    });
  });

  describe('位置转换', () => {
    test('offsetAt 应该返回正确的偏移量', () => {
      doc.insert({ line: 0, column: 0 }, 'abc\ndef');
      expect(doc.offsetAt({ line: 0, column: 0 })).toBe(0);
      expect(doc.offsetAt({ line: 0, column: 3 })).toBe(3);
      expect(doc.offsetAt({ line: 1, column: 0 })).toBe(4);
      expect(doc.offsetAt({ line: 1, column: 3 })).toBe(7);
    });

    test('positionAt 应该返回正确的位置', () => {
      doc.insert({ line: 0, column: 0 }, 'abc\ndef');
      expect(doc.positionAt(0)).toEqual({ line: 0, column: 0 });
      expect(doc.positionAt(3)).toEqual({ line: 0, column: 3 });
      expect(doc.positionAt(4)).toEqual({ line: 1, column: 0 });
      expect(doc.positionAt(7)).toEqual({ line: 1, column: 3 });
    });
  });
});
```

### 2.2 Cursor Manager 测试

```typescript
// tests/cursor.test.ts

import { CursorManager } from '../src/core/cursor';
import { DocumentModel } from '../src/core/document';

describe('CursorManager', () => {
  let doc: DocumentModel;
  let cursor: CursorManager;

  beforeEach(() => {
    doc = new DocumentModel('line1\nline2\nline3');
    cursor = new CursorManager(doc);
  });

  describe('初始化', () => {
    test('应该在 (0, 0) 位置创建光标', () => {
      expect(cursor.primary.position).toEqual({ line: 0, column: 0 });
    });
  });

  describe('移动操作', () => {
    test('moveRight 应该向右移动', () => {
      cursor.moveRight();
      expect(cursor.primary.position).toEqual({ line: 0, column: 1 });
    });

    test('moveRight 应该跨行移动', () => {
      cursor.moveTo({ line: 0, column: 5 });
      cursor.moveRight();
      expect(cursor.primary.position).toEqual({ line: 1, column: 0 });
    });

    test('moveLeft 应该向左移动', () => {
      cursor.moveTo({ line: 0, column: 3 });
      cursor.moveLeft();
      expect(cursor.primary.position).toEqual({ line: 0, column: 2 });
    });

    test('moveLeft 应该跨行移动', () => {
      cursor.moveTo({ line: 1, column: 0 });
      cursor.moveLeft();
      expect(cursor.primary.position).toEqual({ line: 0, column: 5 });
    });

    test('moveDown 应该向下移动', () => {
      cursor.moveDown();
      expect(cursor.primary.position).toEqual({ line: 1, column: 0 });
    });

    test('moveUp 应该向上移动', () => {
      cursor.moveTo({ line: 2, column: 0 });
      cursor.moveUp();
      expect(cursor.primary.position).toEqual({ line: 1, column: 0 });
    });

    test('移动不应该超出文档范围', () => {
      cursor.moveTo({ line: 2, column: 5 });
      cursor.moveDown();
      expect(cursor.primary.position.line).toBe(2);

      cursor.moveTo({ line: 0, column: 0 });
      cursor.moveUp();
      expect(cursor.primary.position.line).toBe(0);
    });

    test('移动应该保持在行长度范围内', () => {
      cursor.moveTo({ line: 0, column: 3 });
      cursor.moveDown(); // line2 长度也是 5
      expect(cursor.primary.position.column).toBe(3);
    });
  });

  describe('选择操作', () => {
    test('selectTo 应该创建选区', () => {
      cursor.selectTo({ line: 0, column: 5 });
      expect(cursor.getSelection()).toEqual({
        start: { line: 0, column: 0 },
        end: { line: 0, column: 5 }
      });
    });

    test('selectAll 应该选择全部内容', () => {
      cursor.selectAll();
      expect(cursor.getSelection()).toEqual({
        start: { line: 0, column: 0 },
        end: { line: 2, column: 5 }
      });
    });

    test('moveTo 应该清除选区', () => {
      cursor.selectTo({ line: 0, column: 5 });
      cursor.moveTo({ line: 1, column: 0 });
      expect(cursor.getSelection()).toBeNull();
    });
  });

  describe('位置验证', () => {
    test('moveTo 应该修正无效位置', () => {
      cursor.moveTo({ line: -1, column: 0 });
      expect(cursor.primary.position.line).toBe(0);

      cursor.moveTo({ line: 100, column: 0 });
      expect(cursor.primary.position.line).toBe(2);

      cursor.moveTo({ line: 0, column: -1 });
      expect(cursor.primary.position.column).toBe(0);

      cursor.moveTo({ line: 0, column: 100 });
      expect(cursor.primary.position.column).toBe(5);
    });
  });
});
```

### 2.3 Syntax Highlighter 测试

```typescript
// tests/highlighter.test.ts

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
```

## 3. 集成测试

```typescript
// tests/integration.test.ts

import { Editor } from '../src/editor';

// Mock Canvas API
const mockCtx = {
  fillRect: jest.fn(),
  fillText: jest.fn(),
  measureText: jest.fn().mockReturnValue({ width: 8 }),
  font: ''
};

const mockCanvas = {
  getContext: jest.fn().mockReturnValue(mockCtx),
  width: 800,
  height: 600
};

// Mock DOM
document.createElement = jest.fn().mockImplementation((tag) => {
  if (tag === 'canvas') return mockCanvas;
  return {};
});

describe('Editor Integration', () => {
  let editor: Editor;
  let container: HTMLElement;

  beforeEach(() => {
    container = document.createElement('div');
    jest.clearAllMocks();

    editor = new Editor(container, {
      initialContent: 'const x = 1;'
    });
  });

  describe('初始化', () => {
    test('应该创建 Canvas 元素', () => {
      expect(container.appendChild).toHaveBeenCalledWith(mockCanvas);
    });

    test('应该设置初始内容', () => {
      expect(editor.getContent()).toBe('const x = 1;');
    });
  });

  describe('内容修改', () => {
    test('setContent 应该更新内容', () => {
      editor.setContent('let y = 2;');
      expect(editor.getContent()).toBe('let y = 2;');
    });
  });

  describe('渲染', () => {
    test('应该调用 Canvas 渲染方法', () => {
      // 渲染已经被调用（初始化时）
      expect(mockCtx.fillRect).toHaveBeenCalled();
      expect(mockCtx.fillText).toHaveBeenCalled();
    });
  });
});
```

## 4. 性能测试

```typescript
// tests/performance.test.ts

import { DocumentModel } from '../src/core/document';
import { TypeScriptHighlighter } from '../src/highlight/syntax';

describe('Performance Tests', () => {
  describe('Document 操作性能', () => {
    test('大量插入操作', () => {
      const doc = new DocumentModel();
      const iterations = 10000;

      const start = performance.now();

      for (let i = 0; i < iterations; i++) {
        doc.insert({ line: 0, column: 0 }, 'x');
      }

      const duration = performance.now() - start;
      console.log(`${iterations} insertions: ${duration.toFixed(2)}ms`);

      // 应该在合理时间内完成
      expect(duration).toBeLessThan(1000);
    });

    test('大文档读取', () => {
      const lines = Array(10000).fill('test line content');
      const doc = new DocumentModel(lines.join('\n'));

      const start = performance.now();

      for (let i = 0; i < 1000; i++) {
        doc.getLine(Math.floor(Math.random() * 10000));
      }

      const duration = performance.now() - start;
      console.log(`1000 random reads from 10000 lines: ${duration.toFixed(2)}ms`);

      expect(duration).toBeLessThan(100);
    });
  });

  describe('语法高亮性能', () => {
    test('大文件高亮', () => {
      const highlighter = new TypeScriptHighlighter();
      const lines = Array(1000).fill('const x: number = 42; // comment');

      const start = performance.now();
      const tokens = highlighter.tokenizeDocument(lines);
      const duration = performance.now() - start;

      console.log(`Highlight 1000 lines: ${duration.toFixed(2)}ms`);

      expect(tokens).toHaveLength(1000);
      expect(duration).toBeLessThan(500);
    });
  });
});
```

## 5. 测试配置

```javascript
// jest.config.js
module.exports = {
  preset: 'ts-jest',
  testEnvironment: 'jsdom',
  roots: ['<rootDir>/tests'],
  testMatch: ['**/*.test.ts'],
  collectCoverageFrom: [
    'src/**/*.ts',
    '!src/**/*.d.ts'
  ],
  coverageThreshold: {
    global: {
      branches: 80,
      functions: 80,
      lines: 80,
      statements: 80
    }
  }
};
```

## 6. 运行测试

```bash
# 运行所有测试
npm test

# 运行特定测试文件
npm test -- tests/document.test.ts

# 生成覆盖率报告
npm test -- --coverage

# 监听模式
npm test -- --watch
```

## 7. 测试最佳实践

1. **测试命名**：使用清晰的描述性名称
2. **测试隔离**：每个测试独立，不依赖其他测试
3. **边界测试**：测试边界条件和错误情况
4. **性能基准**：建立性能基准，监控性能退化
5. **Mock 使用**：合理使用 Mock，避免过度 Mock
