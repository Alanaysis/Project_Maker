// Document Model 测试

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
      }).toThrow('Invalid line number: -1');

      expect(() => {
        doc.insert({ line: 0, column: 1 }, 'x');
      }).toThrow('Invalid column: 1');
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
      expect(doc.getLine(0)).toBe('linne3');
    });
  });

  describe('getText', () => {
    test('应该返回完整文本', () => {
      doc.insert({ line: 0, column: 0 }, 'line1\nline2\nline3');
      expect(doc.getText()).toBe('line1\nline2\nline3');
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
