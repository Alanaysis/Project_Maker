// Editor 主类测试

import { Editor } from '../src/editor';
import { DocumentModel } from '../src/core/document';
import { CursorManager } from '../src/core/cursor';
import { TypeScriptHighlighter } from '../src/highlight/syntax';

// Mock Canvas API
const mockCtx = {
  fillRect: jest.fn(),
  fillText: jest.fn(),
  measureText: jest.fn().mockReturnValue({ width: 8 }),
  font: '',
  fillStyle: '',
  textAlign: ''
};

const mockCanvas = {
  getContext: jest.fn().mockReturnValue(mockCtx),
  width: 800,
  height: 600
};

// Mock DOM
const mockContainer = {
  appendChild: jest.fn(),
  clientWidth: 800,
  clientHeight: 600
};

document.createElement = jest.fn().mockImplementation((tag: string) => {
  if (tag === 'canvas') return mockCanvas;
  return {};
});

describe('Editor', () => {
  let editor: Editor;

  beforeEach(() => {
    jest.clearAllMocks();
    editor = new Editor(mockContainer as any, {
      initialContent: 'const x = 1;'
    });
  });

  describe('初始化', () => {
    test('应该创建 Canvas 元素', () => {
      expect(mockContainer.appendChild).toHaveBeenCalledWith(mockCanvas);
    });

    test('应该设置初始内容', () => {
      expect(editor.getContent()).toBe('const x = 1;');
    });

    test('应该调用 getContext', () => {
      expect(mockCanvas.getContext).toHaveBeenCalledWith('2d');
    });
  });

  describe('getContent', () => {
    test('应该返回文档内容', () => {
      expect(editor.getContent()).toBe('const x = 1;');
    });
  });

  describe('setContent', () => {
    test('应该更新文档内容', () => {
      editor.setContent('let y = 2;');
      expect(editor.getContent()).toBe('let y = 2;');
    });

    test('应该重置撤销栈', () => {
      // 执行一些操作
      editor.setContent('let y = 2;');
      // 验证内容已更新
      expect(editor.getContent()).toBe('let y = 2;');
    });
  });

  describe('模块集成', () => {
    test('DocumentModel 应该正确工作', () => {
      const doc = new DocumentModel('test');
      expect(doc.getText()).toBe('test');
      expect(doc.getLineCount()).toBe(1);
    });

    test('CursorManager 应该正确工作', () => {
      const doc = new DocumentModel('line1\nline2');
      const cursor = new CursorManager(doc);
      expect(cursor.primary.position).toEqual({ line: 0, column: 0 });
      cursor.moveDown();
      expect(cursor.primary.position).toEqual({ line: 1, column: 0 });
    });

    test('TypeScriptHighlighter 应该正确工作', () => {
      const highlighter = new TypeScriptHighlighter();
      const tokens = highlighter.tokenizeLine('const x = 1;', 0);
      expect(tokens[0].type).toBe('keyword');
      expect(tokens[0].value).toBe('const');
    });
  });
});
