// Cursor Manager 测试

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

    test('光标应该可见', () => {
      expect(cursor.primary.visible).toBe(true);
    });
  });

  describe('moveTo', () => {
    test('应该移动到指定位置', () => {
      cursor.moveTo({ line: 1, column: 3 });
      expect(cursor.primary.position).toEqual({ line: 1, column: 3 });
    });

    test('应该清除选区', () => {
      cursor.selectTo({ line: 0, column: 5 });
      cursor.moveTo({ line: 1, column: 0 });
      expect(cursor.getSelection()).toBeNull();
    });

    test('应该修正无效位置', () => {
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

  describe('moveRight', () => {
    test('应该向右移动', () => {
      cursor.moveRight();
      expect(cursor.primary.position).toEqual({ line: 0, column: 1 });
    });

    test('应该跨行移动', () => {
      cursor.moveTo({ line: 0, column: 5 });
      cursor.moveRight();
      expect(cursor.primary.position).toEqual({ line: 1, column: 0 });
    });

    test('应该支持多字符移动', () => {
      cursor.moveRight(3);
      expect(cursor.primary.position).toEqual({ line: 0, column: 3 });
    });
  });

  describe('moveLeft', () => {
    test('应该向左移动', () => {
      cursor.moveTo({ line: 0, column: 3 });
      cursor.moveLeft();
      expect(cursor.primary.position).toEqual({ line: 0, column: 2 });
    });

    test('应该跨行移动', () => {
      cursor.moveTo({ line: 1, column: 0 });
      cursor.moveLeft();
      expect(cursor.primary.position).toEqual({ line: 0, column: 5 });
    });
  });

  describe('moveUp', () => {
    test('应该向上移动', () => {
      cursor.moveTo({ line: 2, column: 0 });
      cursor.moveUp();
      expect(cursor.primary.position).toEqual({ line: 1, column: 0 });
    });

    test('应该保持在文档范围内', () => {
      cursor.moveTo({ line: 0, column: 0 });
      cursor.moveUp();
      expect(cursor.primary.position.line).toBe(0);
    });

    test('应该调整列位置', () => {
      cursor.moveTo({ line: 1, column: 3 });
      cursor.moveUp();
      expect(cursor.primary.position.column).toBe(3);
    });
  });

  describe('moveDown', () => {
    test('应该向下移动', () => {
      cursor.moveDown();
      expect(cursor.primary.position).toEqual({ line: 1, column: 0 });
    });

    test('应该保持在文档范围内', () => {
      cursor.moveTo({ line: 2, column: 0 });
      cursor.moveDown();
      expect(cursor.primary.position.line).toBe(2);
    });
  });

  describe('selectTo', () => {
    test('应该创建选区', () => {
      cursor.selectTo({ line: 0, column: 5 });
      expect(cursor.getSelection()).toEqual({
        start: { line: 0, column: 0 },
        end: { line: 0, column: 5 }
      });
    });

    test('应该扩展选区', () => {
      cursor.selectTo({ line: 0, column: 3 });
      cursor.selectTo({ line: 1, column: 2 });
      expect(cursor.getSelection()).toEqual({
        start: { line: 0, column: 0 },
        end: { line: 1, column: 2 }
      });
    });
  });

  describe('selectAll', () => {
    test('应该选择全部内容', () => {
      cursor.selectAll();
      expect(cursor.getSelection()).toEqual({
        start: { line: 0, column: 0 },
        end: { line: 2, column: 5 }
      });
    });
  });

  describe('selectLine', () => {
    test('应该选择指定行', () => {
      cursor.selectLine(1);
      expect(cursor.getSelection()).toEqual({
        start: { line: 1, column: 0 },
        end: { line: 1, column: 5 }
      });
    });
  });
});
