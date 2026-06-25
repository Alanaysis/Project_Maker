/**
 * Tween Class Tests
 */

import { Tween } from '../src/tween';
import { AnimationState } from '../src/types';
import { linear } from '../src/easing';

describe('Tween', () => {
  const createConfig = (overrides = {}) => ({
    from: { x: 0, y: 0 },
    to: { x: 100, y: 200 },
    duration: 1000,
    easing: linear,
    ...overrides,
  });

  describe('Construction', () => {
    test('creates tween with default ID', () => {
      const tween = new Tween(createConfig());
      expect(tween.id).toBeDefined();
      expect(typeof tween.id).toBe('string');
    });

    test('creates tween with custom ID', () => {
      const tween = new Tween(createConfig(), 'custom-id');
      expect(tween.id).toBe('custom-id');
    });

    test('starts in IDLE state', () => {
      const tween = new Tween(createConfig());
      expect(tween.state).toBe(AnimationState.IDLE);
    });

    test('initializes currentValues from "from"', () => {
      const tween = new Tween(createConfig());
      expect(tween.currentValues).toEqual({ x: 0, y: 0 });
    });
  });

  describe('State transitions', () => {
    test('transitions to RUNNING on start', () => {
      const tween = new Tween(createConfig());
      tween.start(1000);
      expect(tween.state).toBe(AnimationState.RUNNING);
    });

    test('transitions to PAUSED on pause', () => {
      const tween = new Tween(createConfig());
      tween.start(1000);
      tween.pause();
      expect(tween.state).toBe(AnimationState.PAUSED);
    });

    test('transitions to CANCELLED on cancel', () => {
      const tween = new Tween(createConfig());
      tween.start(1000);
      tween.cancel();
      expect(tween.state).toBe(AnimationState.CANCELLED);
    });

    test('transitions to COMPLETED when done', () => {
      const tween = new Tween(createConfig({ duration: 100 }));
      tween.start(1000);
      tween.update(1100);
      expect(tween.state).toBe(AnimationState.COMPLETED);
    });
  });

  describe('Update', () => {
    test('interpolates values correctly at 50%', () => {
      const tween = new Tween(createConfig({
        from: { x: 0 },
        to: { x: 100 },
        duration: 100,
        easing: linear,
      }));
      tween.start(1000);
      tween.update(1050);
      expect(tween.currentValues.x).toBeCloseTo(50);
    });

    test('interpolates values correctly at 0%', () => {
      const tween = new Tween(createConfig({
        from: { x: 0 },
        to: { x: 100 },
        duration: 100,
        easing: linear,
      }));
      tween.start(1000);
      tween.update(1000);
      expect(tween.currentValues.x).toBeCloseTo(0);
    });

    test('interpolates values correctly at 100%', () => {
      const tween = new Tween(createConfig({
        from: { x: 0 },
        to: { x: 100 },
        duration: 100,
        easing: linear,
      }));
      tween.start(1000);
      tween.update(1100);
      expect(tween.currentValues.x).toBeCloseTo(100);
    });

    test('interpolates multiple properties', () => {
      const tween = new Tween(createConfig({
        from: { x: 0, y: 0 },
        to: { x: 100, y: 200 },
        duration: 100,
        easing: linear,
      }));
      tween.start(1000);
      tween.update(1050);
      expect(tween.currentValues.x).toBeCloseTo(50);
      expect(tween.currentValues.y).toBeCloseTo(100);
    });

    test('returns true while running', () => {
      const tween = new Tween(createConfig({ duration: 100 }));
      tween.start(1000);
      expect(tween.update(1050)).toBe(true);
    });

    test('returns false when completed', () => {
      const tween = new Tween(createConfig({ duration: 100 }));
      tween.start(1000);
      expect(tween.update(1100)).toBe(false);
    });

    test('does not update when IDLE', () => {
      const tween = new Tween(createConfig());
      tween.update(1500);
      expect(tween.currentValues).toEqual({ x: 0, y: 0 });
    });
  });

  describe('Callbacks', () => {
    test('calls onUpdate with current values', () => {
      const onUpdate = jest.fn();
      const tween = new Tween(createConfig({
        from: { x: 0 },
        to: { x: 100 },
        duration: 100,
        onUpdate,
      }));
      tween.start(1000);
      tween.update(1050);
      expect(onUpdate).toHaveBeenCalledWith(expect.objectContaining({ x: 50 }));
    });

    test('calls onComplete when finished', () => {
      const onComplete = jest.fn();
      const tween = new Tween(createConfig({
        duration: 100,
        onComplete,
      }));
      tween.start(1000);
      tween.update(1100);
      expect(onComplete).toHaveBeenCalledTimes(1);
    });
  });

  describe('Easing', () => {
    test('applies easing function', () => {
      // Use easeInQuad: t^2
      const tween = new Tween(createConfig({
        from: { x: 0 },
        to: { x: 100 },
        duration: 100,
        easing: (t: number) => t * t, // easeInQuad
      }));
      tween.start(1000);
      tween.update(1050); // 50% raw progress
      // easeInQuad(0.5) = 0.25, so x should be 25
      expect(tween.currentValues.x).toBeCloseTo(25);
    });
  });

  describe('Delay', () => {
    test('respects delay', () => {
      const onUpdate = jest.fn();
      const tween = new Tween(createConfig({
        duration: 100,
        delay: 50,
        onUpdate,
      }));
      tween.start(1000);
      tween.update(1025); // Still in delay
      expect(onUpdate).not.toHaveBeenCalled();
      tween.update(1075); // Past delay
      expect(onUpdate).toHaveBeenCalled();
    });
  });

  describe('Negative values', () => {
    test('interpolates negative values', () => {
      const tween = new Tween(createConfig({
        from: { x: -100 },
        to: { x: 100 },
        duration: 100,
        easing: linear,
      }));
      tween.start(1000);
      tween.update(1050);
      expect(tween.currentValues.x).toBeCloseTo(0);
    });
  });
});
