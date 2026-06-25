/**
 * Animation Queue Tests
 */

import { AnimationQueue } from '../src/queue';

// Use fake timers for all tests in this file
beforeEach(() => {
  jest.useFakeTimers();

  (global as any).requestAnimationFrame = (callback: (time: number) => void) => {
    return setTimeout(() => callback(Date.now()), 16) as unknown as number;
  };

  (global as any).cancelAnimationFrame = (id: number) => {
    clearTimeout(id);
  };

  // Mock document for Animation class
  (global as any).document = {
    querySelector: jest.fn().mockReturnValue({
      style: {},
    }),
  };
});

afterEach(() => {
  jest.useRealTimers();
  delete (global as any).requestAnimationFrame;
  delete (global as any).cancelAnimationFrame;
  delete (global as any).document;
});

describe('AnimationQueue', () => {
  describe('Construction', () => {
    test('creates queue with default name', () => {
      const queue = new AnimationQueue();
      expect(queue.name).toBe('default');
    });

    test('creates queue with custom name', () => {
      const queue = new AnimationQueue('myQueue');
      expect(queue.name).toBe('myQueue');
    });

    test('starts with zero length', () => {
      const queue = new AnimationQueue();
      expect(queue.length).toBe(0);
    });

    test('starts idle', () => {
      const queue = new AnimationQueue();
      expect(queue.isProcessing).toBe(false);
      expect(queue.isPaused).toBe(false);
    });
  });

  describe('Delay (wait)', () => {
    test('resolves after delay', async () => {
      const queue = new AnimationQueue();
      const promise = queue.wait(100);

      jest.advanceTimersByTime(100);
      await promise;
    });

    test('increases queue length', () => {
      const queue = new AnimationQueue();
      queue.wait(100);
      expect(queue.length).toBeGreaterThan(0);
    });
  });

  describe('Cancel', () => {
    test('rejects pending tasks', async () => {
      const queue = new AnimationQueue();
      const promise = queue.wait(10000);

      // Suppress unhandled rejection from cancel
      promise.catch(() => {});

      // Cancel should reject the task
      queue.cancel();

      await expect(promise).rejects.toThrow('Animation cancelled');
    });

    test('resets queue length', () => {
      const queue = new AnimationQueue();
      const p1 = queue.wait(100);
      const p2 = queue.wait(200);
      p1.catch(() => {});
      p2.catch(() => {});
      queue.cancel();
      expect(queue.length).toBe(0);
    });
  });

  describe('Clear', () => {
    test('rejects queued tasks', async () => {
      const queue = new AnimationQueue();
      // First item starts processing, second stays in queue
      const p1 = queue.wait(10000);
      const p2 = queue.wait(10000);

      // Suppress rejections
      p1.catch(() => {});

      // p2 should be in the queue (not processing yet)
      queue.clear();

      // p2 should be rejected since it was in the queue
      await expect(p2).rejects.toThrow('Queue cleared');

      // Clean up p1
      queue.cancel();
    });
  });

  describe('Pause and Resume', () => {
    test('pauses the queue', () => {
      const queue = new AnimationQueue();
      queue.pause();
      expect(queue.isPaused).toBe(true);
    });

    test('resumes the queue', () => {
      const queue = new AnimationQueue();
      queue.pause();
      queue.resume();
      expect(queue.isPaused).toBe(false);
    });
  });

  describe('Sequential execution', () => {
    test('executes delays sequentially', async () => {
      const queue = new AnimationQueue();
      const order: number[] = [];

      const p1 = queue.wait(100).then(() => order.push(1));
      const p2 = queue.wait(100).then(() => order.push(2));
      const p3 = queue.wait(100).then(() => order.push(3));

      // First wait starts immediately, advance to complete it
      jest.advanceTimersByTime(100);
      await p1;

      // Second wait starts after first completes
      jest.advanceTimersByTime(100);
      await p2;

      // Third wait starts after second completes
      jest.advanceTimersByTime(100);
      await p3;

      expect(order).toEqual([1, 2, 3]);
    });
  });

  describe('Mixed operations', () => {
    test('supports chaining wait operations', async () => {
      const queue = new AnimationQueue();
      const results: string[] = [];

      const p1 = queue.wait(50).then(() => results.push('first'));
      const p2 = queue.wait(50).then(() => results.push('second'));

      jest.advanceTimersByTime(50);
      await p1;
      jest.advanceTimersByTime(50);
      await p2;

      expect(results).toEqual(['first', 'second']);
    });
  });
});
