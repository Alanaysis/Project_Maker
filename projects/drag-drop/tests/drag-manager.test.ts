/**
 * 拖拽管理器测试
 */

import { DragManager } from '../src/drag-manager';
import { DragState, DragEventData } from '../src/types';

// Mock DOM elements
const createMockElement = (id: string = 'test'): HTMLElement => {
  const element = document.createElement('div');
  element.id = id;
  element.getBoundingClientRect = jest.fn(() => ({
    x: 0,
    y: 0,
    width: 100,
    height: 50,
    top: 0,
    right: 100,
    bottom: 50,
    left: 0,
    toJSON: () => ({}),
  }));
  return element;
};

describe('DragManager', () => {
  let manager: DragManager;

  beforeEach(() => {
    manager = new DragManager();
  });

  afterEach(() => {
    manager.destroy();
  });

  describe('getState', () => {
    it('should return IDLE initially', () => {
      expect(manager.getState()).toBe(DragState.IDLE);
    });
  });

  describe('getCurrentElement', () => {
    it('should return null initially', () => {
      expect(manager.getCurrentElement()).toBeNull();
    });
  });

  describe('makeDraggable', () => {
    it('should return remove function', () => {
      const element = createMockElement();
      const remove = manager.makeDraggable(element);
      expect(typeof remove).toBe('function');
    });

    it('should add event listeners to element', () => {
      const element = createMockElement();
      const addEventListenerSpy = jest.spyOn(element, 'addEventListener');

      manager.makeDraggable(element);

      expect(addEventListenerSpy).toHaveBeenCalledWith('mousedown', expect.any(Function));
      expect(addEventListenerSpy).toHaveBeenCalledWith('touchstart', expect.any(Function), expect.any(Object));
    });

    it('should remove event listeners when remove function is called', () => {
      const element = createMockElement();
      const removeEventListenerSpy = jest.spyOn(element, 'removeEventListener');

      const remove = manager.makeDraggable(element);
      remove();

      expect(removeEventListenerSpy).toHaveBeenCalledWith('mousedown', expect.any(Function));
      expect(removeEventListenerSpy).toHaveBeenCalledWith('touchstart', expect.any(Function));
    });
  });

  describe('registerDropTarget', () => {
    it('should return remove function', () => {
      const element = createMockElement('target');
      const remove = manager.registerDropTarget(element);
      expect(typeof remove).toBe('function');
    });

    it('should allow unregistering drop target', () => {
      const element = createMockElement('target');
      const remove = manager.registerDropTarget(element);

      remove();

      // After removal, the target should not be registered
      // We can verify this indirectly by checking that no error occurs
      expect(() => remove()).not.toThrow();
    });
  });

  describe('on/off', () => {
    it('should subscribe to events', () => {
      const handler = jest.fn();
      const remove = manager.on('dragstart', handler);

      expect(typeof remove).toBe('function');
    });

    it('should unsubscribe from events', () => {
      const handler = jest.fn();
      manager.on('dragstart', handler);
      manager.off('dragstart', handler);

      // Handler should not be called after unsubscribe
      // We verify by checking no error occurs
      expect(() => manager.off('dragstart', handler)).not.toThrow();
    });
  });

  describe('destroy', () => {
    it('should clean up resources', () => {
      const element = createMockElement();
      manager.makeDraggable(element);

      expect(() => manager.destroy()).not.toThrow();
    });

    it('should reset state', () => {
      manager.destroy();
      expect(manager.getState()).toBe(DragState.IDLE);
      expect(manager.getCurrentElement()).toBeNull();
    });
  });
});
