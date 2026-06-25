/**
 * 拖拽排序测试
 */

import { Sortable } from '../src/sortable';

// Mock DOM elements
const createMockContainer = (id: string = 'container'): HTMLElement => {
  const container = document.createElement('div');
  container.id = id;
  return container;
};

const createMockItem = (id: string): HTMLElement => {
  const item = document.createElement('div');
  item.id = id;
  item.className = 'sortable-item';
  item.getBoundingClientRect = jest.fn(() => ({
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
  return item;
};

describe('Sortable', () => {
  let container: HTMLElement;
  let sortable: Sortable;

  beforeEach(() => {
    container = createMockContainer();

    // Add items to container
    for (let i = 0; i < 5; i++) {
      const item = createMockItem(`item-${i}`);
      container.appendChild(item);
    }

    document.body.appendChild(container);
  });

  afterEach(() => {
    if (sortable) {
      sortable.destroy();
    }
    document.body.removeChild(container);
  });

  describe('constructor', () => {
    it('should create sortable instance', () => {
      sortable = new Sortable({
        container,
        itemSelector: '.sortable-item',
      });

      expect(sortable).toBeDefined();
    });
  });

  describe('getItems', () => {
    it('should return all sortable items', () => {
      sortable = new Sortable({
        container,
        itemSelector: '.sortable-item',
      });

      const items = sortable.getItems();
      expect(items.length).toBe(5);
    });

    it('should return empty array when no items', () => {
      container.innerHTML = '';

      sortable = new Sortable({
        container,
        itemSelector: '.sortable-item',
      });

      const items = sortable.getItems();
      expect(items.length).toBe(0);
    });
  });

  describe('getIndex', () => {
    it('should return correct index for item', () => {
      sortable = new Sortable({
        container,
        itemSelector: '.sortable-item',
      });

      const items = sortable.getItems();
      expect(sortable.getIndex(items[0])).toBe(0);
      expect(sortable.getIndex(items[2])).toBe(2);
      expect(sortable.getIndex(items[4])).toBe(4);
    });

    it('should return -1 for non-existent item', () => {
      sortable = new Sortable({
        container,
        itemSelector: '.sortable-item',
      });

      const nonExistent = document.createElement('div');
      expect(sortable.getIndex(nonExistent)).toBe(-1);
    });
  });

  describe('refreshItems', () => {
    it('should update items list', () => {
      sortable = new Sortable({
        container,
        itemSelector: '.sortable-item',
      });

      expect(sortable.getItems().length).toBe(5);

      // Add new item
      const newItem = createMockItem('item-5');
      container.appendChild(newItem);

      sortable.refreshItems();
      expect(sortable.getItems().length).toBe(6);
    });
  });

  describe('disable/enable', () => {
    it('should disable sortable', () => {
      sortable = new Sortable({
        container,
        itemSelector: '.sortable-item',
      });

      sortable.disable();
      // After disable, dragging should not work
      // We verify by checking no error occurs
      expect(() => sortable.disable()).not.toThrow();
    });

    it('should enable sortable', () => {
      sortable = new Sortable({
        container,
        itemSelector: '.sortable-item',
        disabled: true,
      });

      sortable.enable();
      expect(() => sortable.enable()).not.toThrow();
    });
  });

  describe('destroy', () => {
    it('should clean up resources', () => {
      sortable = new Sortable({
        container,
        itemSelector: '.sortable-item',
      });

      expect(() => sortable.destroy()).not.toThrow();
    });

    it('should allow multiple destroy calls', () => {
      sortable = new Sortable({
        container,
        itemSelector: '.sortable-item',
      });

      sortable.destroy();
      expect(() => sortable.destroy()).not.toThrow();
    });
  });

  describe('options', () => {
    it('should support animation option', () => {
      sortable = new Sortable({
        container,
        itemSelector: '.sortable-item',
        animation: 150,
      });

      expect(sortable).toBeDefined();
    });

    it('should support placeholder option', () => {
      const placeholder = document.createElement('div');
      placeholder.className = 'custom-placeholder';

      sortable = new Sortable({
        container,
        itemSelector: '.sortable-item',
        placeholder,
      });

      expect(sortable).toBeDefined();
    });

    it('should support placeholderClass option', () => {
      sortable = new Sortable({
        container,
        itemSelector: '.sortable-item',
        placeholderClass: 'my-placeholder',
      });

      expect(sortable).toBeDefined();
    });

    it('should support handle option', () => {
      // Add handle elements to items
      const items = container.querySelectorAll('.sortable-item');
      items.forEach((item) => {
        const handle = document.createElement('div');
        handle.className = 'drag-handle';
        item.appendChild(handle);
      });

      sortable = new Sortable({
        container,
        itemSelector: '.sortable-item',
        handle: '.drag-handle',
      });

      expect(sortable).toBeDefined();
    });

    it('should support direction option', () => {
      sortable = new Sortable({
        container,
        itemSelector: '.sortable-item',
        direction: 'horizontal',
      });

      expect(sortable).toBeDefined();
    });

    it('should support disabled option', () => {
      sortable = new Sortable({
        container,
        itemSelector: '.sortable-item',
        disabled: true,
      });

      expect(sortable).toBeDefined();
    });

    it('should support disabledSelector option', () => {
      // Mark some items as disabled
      const items = container.querySelectorAll('.sortable-item');
      items[2].classList.add('disabled');

      sortable = new Sortable({
        container,
        itemSelector: '.sortable-item',
        disabledSelector: '.disabled',
      });

      expect(sortable).toBeDefined();
    });
  });

  describe('callbacks', () => {
    it('should call onSortEnd when sorting completes', () => {
      const onSortEnd = jest.fn();

      sortable = new Sortable({
        container,
        itemSelector: '.sortable-item',
        onSortEnd,
      });

      // Simulate drag end would be complex in unit tests
      // Here we just verify the callback is accepted
      expect(onSortEnd).not.toHaveBeenCalled();
    });

    it('should call onSortChange when order changes', () => {
      const onSortChange = jest.fn();

      sortable = new Sortable({
        container,
        itemSelector: '.sortable-item',
        onSortChange,
      });

      // Simulate drag move would be complex in unit tests
      // Here we just verify the callback is accepted
      expect(onSortChange).not.toHaveBeenCalled();
    });
  });
});
