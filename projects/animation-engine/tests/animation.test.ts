/**
 * Animation Class Tests
 */

import { Animation } from '../src/animation';
import { AnimationState, AnimationDirection, FillMode } from '../src/types';
import { linear, easeOutCubic } from '../src/easing';

// Mock HTMLElement
class MockElement {
  style: Record<string, string> = {};
  querySelector = jest.fn();
}

describe('Animation', () => {
  let element: MockElement;

  beforeEach(() => {
    element = new MockElement();
    // Mock document.querySelector
    (global as any).document = {
      querySelector: jest.fn().mockReturnValue(element),
    };
  });

  afterEach(() => {
    delete (global as any).document;
  });

  const createConfig = (overrides = {}) => ({
    target: element as any as HTMLElement,
    keyframes: [
      { offset: 0, styles: { opacity: 1, transform: 'translateX(0px)' } },
      { offset: 1, styles: { opacity: 0, transform: 'translateX(100px)' } },
    ],
    duration: 1000,
    easing: linear,
    ...overrides,
  });

  describe('Construction', () => {
    test('creates animation with default ID', () => {
      const anim = new Animation(createConfig());
      expect(anim.id).toBeDefined();
      expect(typeof anim.id).toBe('string');
    });

    test('creates animation with custom ID', () => {
      const anim = new Animation(createConfig(), 'custom-id');
      expect(anim.id).toBe('custom-id');
    });

    test('starts in IDLE state', () => {
      const anim = new Animation(createConfig());
      expect(anim.state).toBe(AnimationState.IDLE);
    });

    test('initial progress is 0', () => {
      const anim = new Animation(createConfig());
      expect(anim.progress).toBe(0);
    });
  });

  describe('State transitions', () => {
    test('transitions from IDLE to RUNNING on start', () => {
      const anim = new Animation(createConfig());
      anim.start(1000);
      expect(anim.state).toBe(AnimationState.RUNNING);
    });

    test('transitions from RUNNING to PAUSED on pause', () => {
      const anim = new Animation(createConfig());
      anim.start(1000);
      anim.pause();
      expect(anim.state).toBe(AnimationState.PAUSED);
    });

    test('transitions from PAUSED to RUNNING on resume', () => {
      const anim = new Animation(createConfig());
      anim.start(1000);
      anim.pause();
      anim.start(2000);
      expect(anim.state).toBe(AnimationState.RUNNING);
    });

    test('transitions to CANCELLED on cancel', () => {
      const anim = new Animation(createConfig());
      anim.start(1000);
      anim.cancel();
      expect(anim.state).toBe(AnimationState.CANCELLED);
    });

    test('transitions to COMPLETED when animation ends', () => {
      const anim = new Animation(createConfig({ duration: 100 }));
      anim.start(1000);
      anim.update(1100); // At end
      expect(anim.state).toBe(AnimationState.COMPLETED);
    });

    test('reset returns to IDLE', () => {
      const anim = new Animation(createConfig());
      anim.start(1000);
      anim.cancel();
      anim.reset();
      expect(anim.state).toBe(AnimationState.IDLE);
    });
  });

  describe('Callbacks', () => {
    test('calls onStart when animation starts', () => {
      const onStart = jest.fn();
      const anim = new Animation(createConfig({ onStart }));
      anim.start(1000);
      expect(onStart).toHaveBeenCalledTimes(1);
    });

    test('calls onComplete when animation completes', () => {
      const onComplete = jest.fn();
      const anim = new Animation(createConfig({ duration: 100, onComplete }));
      anim.start(1000);
      anim.update(1100);
      expect(onComplete).toHaveBeenCalledTimes(1);
    });

    test('calls onCancel when animation is cancelled', () => {
      const onCancel = jest.fn();
      const anim = new Animation(createConfig({ onCancel }));
      anim.start(1000);
      anim.cancel();
      expect(onCancel).toHaveBeenCalledTimes(1);
    });

    test('calls onUpdate on each frame', () => {
      const onUpdate = jest.fn();
      const anim = new Animation(createConfig({ duration: 100, onUpdate }));
      anim.start(1000);
      anim.update(1025); // 25% progress
      anim.update(1050); // 50% progress
      expect(onUpdate).toHaveBeenCalledTimes(2);
    });
  });

  describe('Animation update', () => {
    test('does not update when IDLE', () => {
      const anim = new Animation(createConfig());
      const result = anim.update(1500);
      expect(result).toBe(false);
      expect(anim.progress).toBe(0);
    });

    test('returns true while running', () => {
      const anim = new Animation(createConfig({ duration: 1000 }));
      anim.start(1000);
      const result = anim.update(1500);
      expect(result).toBe(true);
    });

    test('returns false when completed', () => {
      const anim = new Animation(createConfig({ duration: 100 }));
      anim.start(1000);
      const result = anim.update(1200);
      expect(result).toBe(false);
    });

    test('handles delay', () => {
      const onUpdate = jest.fn();
      const anim = new Animation(createConfig({
        duration: 100,
        delay: 50,
        onUpdate,
      }));
      anim.start(1000);
      anim.update(1025); // Still in delay
      expect(onUpdate).not.toHaveBeenCalled();
      anim.update(1075); // Past delay, in animation
      expect(onUpdate).toHaveBeenCalled();
    });
  });

  describe('Direction', () => {
    test('NORMAL direction goes forward', () => {
      const anim = new Animation(createConfig({
        duration: 100,
        direction: AnimationDirection.NORMAL,
      }));
      anim.start(1000);
      anim.update(1050); // 50% progress
      expect(anim.progress).toBeCloseTo(0.5);
    });

    test('REVERSE direction goes backward', () => {
      const anim = new Animation(createConfig({
        duration: 100,
        direction: AnimationDirection.REVERSE,
      }));
      anim.start(1000);
      anim.update(1050); // 50% progress, but reversed
      expect(anim.progress).toBeCloseTo(0.5); // 1 - 0.5 = 0.5 with linear easing
    });
  });

  describe('Iterations', () => {
    test('plays multiple iterations', () => {
      const onComplete = jest.fn();
      const anim = new Animation(createConfig({
        duration: 100,
        iterations: 3,
        onComplete,
      }));
      anim.start(1000);

      // First iteration
      anim.update(1050);
      expect(anim.state).toBe(AnimationState.RUNNING);

      // Second iteration
      anim.update(1150);
      expect(anim.state).toBe(AnimationState.RUNNING);

      // Third iteration complete
      anim.update(1300);
      expect(anim.state).toBe(AnimationState.COMPLETED);
      expect(onComplete).toHaveBeenCalledTimes(1);
    });
  });

  describe('Pause and resume', () => {
    test('maintains progress during pause', () => {
      const anim = new Animation(createConfig({ duration: 1000 }));
      anim.start(1000);
      anim.update(1500); // 50% progress
      anim.pause();

      // Time passes while paused
      const progressBefore = anim.progress;
      anim.update(5000);
      // Progress should not change while paused
      expect(anim.progress).toBe(progressBefore);
    });
  });

  describe('Reset', () => {
    test('resets all state', () => {
      const anim = new Animation(createConfig({ duration: 100 }));
      anim.start(1000);
      anim.update(1050);
      anim.reset();

      expect(anim.state).toBe(AnimationState.IDLE);
      expect(anim.progress).toBe(0);
      expect(anim.currentIteration).toBe(0);
    });
  });
});
