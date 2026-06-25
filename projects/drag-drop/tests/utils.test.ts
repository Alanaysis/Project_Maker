/**
 * 工具函数测试
 */

import {
  getDistance,
  isPointInRect,
  generateId,
  throttle,
  debounce,
  validateFileType,
  validateFileSize,
  formatFileSize,
  EventBus,
} from '../src/utils';
import { Position, Rect } from '../src/types';

describe('Utils', () => {
  describe('getDistance', () => {
    it('should calculate distance between two points', () => {
      const p1: Position = { x: 0, y: 0 };
      const p2: Position = { x: 3, y: 4 };
      expect(getDistance(p1, p2)).toBe(5);
    });

    it('should return 0 for same points', () => {
      const p1: Position = { x: 5, y: 5 };
      const p2: Position = { x: 5, y: 5 };
      expect(getDistance(p1, p2)).toBe(0);
    });

    it('should handle negative coordinates', () => {
      const p1: Position = { x: -1, y: -1 };
      const p2: Position = { x: 2, y: 3 };
      expect(getDistance(p1, p2)).toBe(5);
    });
  });

  describe('isPointInRect', () => {
    const rect: Rect = { x: 0, y: 0, width: 100, height: 100 };

    it('should return true for point inside rect', () => {
      const point: Position = { x: 50, y: 50 };
      expect(isPointInRect(point, rect)).toBe(true);
    });

    it('should return true for point on edge', () => {
      const point: Position = { x: 0, y: 0 };
      expect(isPointInRect(point, rect)).toBe(true);
    });

    it('should return false for point outside rect', () => {
      const point: Position = { x: 150, y: 50 };
      expect(isPointInRect(point, rect)).toBe(false);
    });

    it('should return false for point on opposite side', () => {
      const point: Position = { x: -10, y: 50 };
      expect(isPointInRect(point, rect)).toBe(false);
    });
  });

  describe('generateId', () => {
    it('should generate id with default prefix', () => {
      const id = generateId();
      expect(id).toMatch(/^dd_/);
    });

    it('should generate id with custom prefix', () => {
      const id = generateId('test');
      expect(id).toMatch(/^test_/);
    });

    it('should generate unique ids', () => {
      const id1 = generateId();
      const id2 = generateId();
      expect(id1).not.toBe(id2);
    });
  });

  describe('throttle', () => {
    beforeEach(() => {
      jest.useFakeTimers();
    });

    afterEach(() => {
      jest.useRealTimers();
    });

    it('should throttle function calls', () => {
      const fn = jest.fn();
      const throttled = throttle(fn, 100);

      throttled();
      throttled();
      throttled();

      expect(fn).toHaveBeenCalledTimes(1);
    });

    it('should call function again after delay', () => {
      const fn = jest.fn();
      const throttled = throttle(fn, 100);

      throttled();
      jest.advanceTimersByTime(150);
      throttled();

      expect(fn).toHaveBeenCalledTimes(2);
    });
  });

  describe('debounce', () => {
    beforeEach(() => {
      jest.useFakeTimers();
    });

    afterEach(() => {
      jest.useRealTimers();
    });

    it('should debounce function calls', () => {
      const fn = jest.fn();
      const debounced = debounce(fn, 100);

      debounced();
      debounced();
      debounced();

      expect(fn).not.toHaveBeenCalled();

      jest.advanceTimersByTime(150);
      expect(fn).toHaveBeenCalledTimes(1);
    });

    it('should reset timer on new call', () => {
      const fn = jest.fn();
      const debounced = debounce(fn, 100);

      debounced();
      jest.advanceTimersByTime(50);
      debounced();
      jest.advanceTimersByTime(50);
      debounced();
      jest.advanceTimersByTime(150);

      expect(fn).toHaveBeenCalledTimes(1);
    });
  });

  describe('validateFileType', () => {
    const createFile = (type: string, name: string = 'test'): File => {
      return new File([''], name, { type });
    };

    it('should accept all files when accept is empty', () => {
      const file = createFile('image/png');
      expect(validateFileType(file, [])).toBe(true);
    });

    it('should accept matching MIME type', () => {
      const file = createFile('image/png');
      expect(validateFileType(file, ['image/png'])).toBe(true);
    });

    it('should reject non-matching MIME type', () => {
      const file = createFile('image/png');
      expect(validateFileType(file, ['image/jpeg'])).toBe(false);
    });

    it('should accept wildcard MIME type', () => {
      const file = createFile('image/png');
      expect(validateFileType(file, ['image/*'])).toBe(true);
    });

    it('should accept matching extension', () => {
      const file = createFile('', 'test.png');
      expect(validateFileType(file, ['.png'])).toBe(true);
    });

    it('should reject non-matching extension', () => {
      const file = createFile('', 'test.png');
      expect(validateFileType(file, ['.jpg'])).toBe(false);
    });
  });

  describe('validateFileSize', () => {
    it('should accept file within size limit', () => {
      const file = new File([new ArrayBuffer(100)], 'test');
      expect(validateFileSize(file, 200)).toBe(true);
    });

    it('should reject file exceeding size limit', () => {
      const file = new File([new ArrayBuffer(200)], 'test');
      expect(validateFileSize(file, 100)).toBe(false);
    });

    it('should accept file at exact size limit', () => {
      const file = new File([new ArrayBuffer(100)], 'test');
      expect(validateFileSize(file, 100)).toBe(true);
    });
  });

  describe('formatFileSize', () => {
    it('should format bytes', () => {
      expect(formatFileSize(100)).toBe('100.00 B');
    });

    it('should format kilobytes', () => {
      expect(formatFileSize(1024)).toBe('1.00 KB');
    });

    it('should format megabytes', () => {
      expect(formatFileSize(1024 * 1024)).toBe('1.00 MB');
    });

    it('should format gigabytes', () => {
      expect(formatFileSize(1024 * 1024 * 1024)).toBe('1.00 GB');
    });

    it('should return 0 B for 0 bytes', () => {
      expect(formatFileSize(0)).toBe('0 B');
    });
  });

  describe('EventBus', () => {
    type TestEvents = {
      test: { value: number };
      other: { name: string };
      [key: string]: unknown;
    };

    it('should emit and receive events', () => {
      const bus = new EventBus<TestEvents>();
      const handler = jest.fn();

      bus.on('test', handler);
      bus.emit('test', { value: 42 });

      expect(handler).toHaveBeenCalledWith({ value: 42 });
    });

    it('should support multiple listeners', () => {
      const bus = new EventBus<TestEvents>();
      const handler1 = jest.fn();
      const handler2 = jest.fn();

      bus.on('test', handler1);
      bus.on('test', handler2);
      bus.emit('test', { value: 42 });

      expect(handler1).toHaveBeenCalledWith({ value: 42 });
      expect(handler2).toHaveBeenCalledWith({ value: 42 });
    });

    it('should remove listener', () => {
      const bus = new EventBus<TestEvents>();
      const handler = jest.fn();

      const remove = bus.on('test', handler);
      remove();

      bus.emit('test', { value: 42 });
      expect(handler).not.toHaveBeenCalled();
    });

    it('should not call handler for different event', () => {
      const bus = new EventBus<TestEvents>();
      const handler = jest.fn();

      bus.on('test', handler);
      bus.emit('other', { name: 'test' });

      expect(handler).not.toHaveBeenCalled();
    });

    it('should clear all listeners', () => {
      const bus = new EventBus<TestEvents>();
      const handler = jest.fn();

      bus.on('test', handler);
      bus.clear();

      bus.emit('test', { value: 42 });
      expect(handler).not.toHaveBeenCalled();
    });
  });
});
