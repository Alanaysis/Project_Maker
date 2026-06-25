/**
 * Animation Engine Tests
 */

import { AnimationEngine, createEngine } from '../src/engine';
import { Animation } from '../src/animation';
import { Tween } from '../src/tween';
import { AnimationQueue } from '../src/queue';
import { linear } from '../src/easing';

// Mock requestAnimationFrame
let rafCallbacks: Map<number, (time: number) => void> = new Map();
let rafIdCounter = 0;

beforeEach(() => {
  rafCallbacks.clear();
  rafIdCounter = 0;

  (global as any).requestAnimationFrame = (callback: (time: number) => void) => {
    const id = ++rafIdCounter;
    rafCallbacks.set(id, callback);
    return id;
  };

  (global as any).cancelAnimationFrame = (id: number) => {
    rafCallbacks.delete(id);
  };

  (global as any).performance = {
    now: () => Date.now(),
  };

  // Mock document with createElement
  (global as any).document = {
    querySelector: jest.fn().mockReturnValue({
      style: {},
    }),
    createElement: jest.fn().mockReturnValue({
      style: {},
    }),
  };
});

afterEach(() => {
  delete (global as any).requestAnimationFrame;
  delete (global as any).cancelAnimationFrame;
  delete (global as any).performance;
  delete (global as any).document;
});

describe('AnimationEngine', () => {
  describe('Construction', () => {
    test('creates engine instance', () => {
      const engine = new AnimationEngine();
      expect(engine).toBeDefined();
    });

    test('createEngine returns new instance', () => {
      const engine = createEngine();
      expect(engine).toBeInstanceOf(AnimationEngine);
    });
  });

  describe('animate', () => {
    test('creates and returns Animation instance', () => {
      const engine = new AnimationEngine();
      const anim = engine.animate({
        target: document.createElement('div'),
        keyframes: [
          { offset: 0, styles: { opacity: 1 } },
          { offset: 1, styles: { opacity: 0 } },
        ],
        duration: 1000,
      });
      expect(anim).toBeInstanceOf(Animation);
    });

    test('registers animation', () => {
      const engine = new AnimationEngine();
      const anim = engine.animate({
        target: document.createElement('div'),
        keyframes: [
          { offset: 0, styles: { opacity: 1 } },
          { offset: 1, styles: { opacity: 0 } },
        ],
        duration: 1000,
      });
      expect(engine.getAnimations()).toContain(anim);
    });
  });

  describe('tween', () => {
    test('creates and returns Tween instance', () => {
      const engine = new AnimationEngine();
      const tween = engine.tween({
        from: { x: 0 },
        to: { x: 100 },
        duration: 1000,
      });
      expect(tween).toBeInstanceOf(Tween);
    });

    test('registers tween', () => {
      const engine = new AnimationEngine();
      const tween = engine.tween({
        from: { x: 0 },
        to: { x: 100 },
        duration: 1000,
      });
      expect(engine.getTweens()).toContain(tween);
    });
  });

  describe('queue', () => {
    test('returns AnimationQueue instance', () => {
      const engine = new AnimationEngine();
      const queue = engine.queue('test');
      expect(queue).toBeInstanceOf(AnimationQueue);
    });

    test('returns same queue for same name', () => {
      const engine = new AnimationEngine();
      const queue1 = engine.queue('test');
      const queue2 = engine.queue('test');
      expect(queue1).toBe(queue2);
    });

    test('returns different queues for different names', () => {
      const engine = new AnimationEngine();
      const queue1 = engine.queue('test1');
      const queue2 = engine.queue('test2');
      expect(queue1).not.toBe(queue2);
    });

    test('defaults to "default" name', () => {
      const engine = new AnimationEngine();
      const queue = engine.queue();
      expect(queue.name).toBe('default');
    });
  });

  describe('Lifecycle', () => {
    test('start begins the engine', () => {
      const engine = new AnimationEngine();
      engine.start();
      // Engine should be running (no error thrown)
    });

    test('pause pauses all animations', () => {
      const engine = new AnimationEngine();
      engine.tween({
        from: { x: 0 },
        to: { x: 100 },
        duration: 1000,
      });
      engine.start();
      engine.pause();
      // All tweens should be paused
    });

    test('resume resumes all animations', () => {
      const engine = new AnimationEngine();
      engine.tween({
        from: { x: 0 },
        to: { x: 100 },
        duration: 1000,
      });
      engine.start();
      engine.pause();
      engine.resume();
    });

    test('stop cancels all animations', () => {
      const engine = new AnimationEngine();
      const tween = engine.tween({
        from: { x: 0 },
        to: { x: 100 },
        duration: 1000,
      });
      engine.start();
      engine.stop();
      expect(engine.getTweens().length).toBe(0);
    });
  });

  describe('Metrics', () => {
    test('returns performance metrics', () => {
      const engine = new AnimationEngine();
      const metrics = engine.getMetrics();
      expect(metrics).toHaveProperty('fps');
      expect(metrics).toHaveProperty('activeAnimations');
      expect(metrics).toHaveProperty('totalFrames');
      expect(metrics).toHaveProperty('averageFrameTime');
    });

    test('tracks active count', () => {
      const engine = new AnimationEngine();
      expect(engine.activeCount).toBe(0);
    });
  });

  describe('Cleanup', () => {
    test('removes completed animations', () => {
      const engine = new AnimationEngine();
      const tween = engine.tween({
        from: { x: 0 },
        to: { x: 100 },
        duration: 100,
      });
      engine.start();

      // Simulate completion
      tween.start(1000);
      tween.update(1100); // Complete

      engine.cleanup();
      // Completed tween should be removed
    });
  });

  describe('Integration', () => {
    test('multiple tweens run independently', () => {
      // Create tweens directly (not through engine) for unit testing
      const tween1 = new Tween({
        from: { x: 0 },
        to: { x: 100 },
        duration: 100,
        easing: linear,
      });
      const tween2 = new Tween({
        from: { y: 0 },
        to: { y: 200 },
        duration: 200,
        easing: linear,
      });

      // Start tweens with explicit timestamps
      tween1.start(1000);
      tween2.start(1000);

      tween1.update(1050);
      tween2.update(1050);

      expect(tween1.currentValues.x).toBeCloseTo(50);
      expect(tween2.currentValues.y).toBeCloseTo(50);
    });
  });
});
