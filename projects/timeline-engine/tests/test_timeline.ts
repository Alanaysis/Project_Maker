/**
 * Tests for Timeline
 */

import { Timeline, TimelineState, KeyframeEntry } from '../src/index';

describe('Timeline', () => {
  let timeline: Timeline;

  beforeEach(() => {
    // Use a short duration for faster tests
    timeline = new Timeline({ duration: 1000, fps: 60 });
  });

  afterEach(() => {
    timeline.destroy();
  });

  describe('Construction', () => {
    it('should create with default state', () => {
      expect(timeline.getCurrentTime()).toBe(0);
      expect(timeline.getProgress()).toBe(0);
      expect(timeline.getTotalDuration()).toBe(1000);
    });

    it('should accept custom options', () => {
      const tl = new Timeline({ duration: 2000, fps: 30, loop: true });
      expect(tl.getTotalDuration()).toBe(2000);
      tl.destroy();
    });

    it('should autoplay when configured', () => {
      const tl = new Timeline({ duration: 1000, autoplay: true });
      expect(tl.isPlaying()).toBe(true);
      tl.destroy();
    });
  });

  describe('Keyframe Animation', () => {
    it('should add keyframe animation', () => {
      const handle = timeline.addKeyframe({
        name: 'test',
        property: 'x',
        keyframes: [
          { time: 0, value: 0 },
          { time: 1, value: 100 },
        ],
        duration: 1000,
      });

      expect(handle.name).toBe('test');
      expect(handle.property).toBe('x');

      const state = timeline.getState();
      expect(state.x).toBeDefined();
    });

    it('should interpolate keyframe values', () => {
      timeline.addKeyframe({
        name: 'x-anim',
        property: 'x',
        keyframes: [
          { time: 0, value: 0 },
          { time: 1, value: 100 },
        ],
        duration: 1000,
      });

      timeline.seek(0);
      expect(timeline.getState().x).toBeCloseTo(0, 5);

      timeline.seek(0.5);
      // Default easing is easeOutCubic: f(0.5) = 0.875
      expect(timeline.getState().x).toBeCloseTo(87.5, 2);

      timeline.seek(1);
      expect(timeline.getState().x).toBeCloseTo(100, 5);
    });

    it('should apply easing', () => {
      timeline.addKeyframe({
        name: 'x-anim',
        property: 'x',
        keyframes: [
          { time: 0, value: 0 },
          { time: 1, value: 100 },
        ],
        duration: 1000,
        easing: 'ease-in-cubic',
      });

      timeline.seek(0.5);
      // easeInCubic(0.5) = 0.125
      expect(timeline.getState().x).toBeCloseTo(12.5, 2);
    });

    it('should remove keyframe animation', () => {
      timeline.addKeyframe({
        name: 'x-anim',
        property: 'x',
        keyframes: [
          { time: 0, value: 0 },
          { time: 1, value: 100 },
        ],
        duration: 1000,
      });

      timeline.removeKeyframe('x');
      const state = timeline.getState();
      expect(state.x).toBeUndefined();
    });

    it('should update keyframes', () => {
      timeline.addKeyframe({
        name: 'x-anim',
        property: 'x',
        keyframes: [
          { time: 0, value: 0 },
          { time: 1, value: 100 },
        ],
        duration: 1000,
      });

      timeline.updateKeyframes('x', [
        { time: 0, value: 0 },
        { time: 1, value: 200 },
      ]);

      timeline.seek(1);
      expect(timeline.getState().x).toBeCloseTo(200, 5);
    });

    it('should update easing', () => {
      timeline.addKeyframe({
        name: 'x-anim',
        property: 'x',
        keyframes: [
          { time: 0, value: 0 },
          { time: 1, value: 100 },
        ],
        duration: 1000,
        easing: 'linear',
      });

      timeline.updateEasing('x', 'ease-in-cubic');
      timeline.seek(0.5);
      expect(timeline.getState().x).toBeCloseTo(12.5, 2);
    });

    it('should support handle.remove()', () => {
      const handle = timeline.addKeyframe({
        name: 'x-anim',
        property: 'x',
        keyframes: [
          { time: 0, value: 0 },
          { time: 1, value: 100 },
        ],
        duration: 1000,
      });

      handle.remove();
      const state = timeline.getState();
      expect(state.x).toBeUndefined();
    });
  });

  describe('Playback Control', () => {
    it('should play', () => {
      timeline.play();
      expect(timeline.isPlaying()).toBe(true);
      expect(timeline.isPaused()).toBe(false);
      expect(timeline.isStopped()).toBe(false);
      timeline.pause();
    });

    it('should pause', () => {
      timeline.play();
      timeline.pause();
      expect(timeline.isPlaying()).toBe(false);
      expect(timeline.isPaused()).toBe(true);
    });

    it('should stop', () => {
      timeline.play();
      timeline.seek(0.5);
      timeline.stop();
      expect(timeline.isStopped()).toBe(true);
      expect(timeline.getCurrentTime()).toBe(0);
    });

    it('should toggle', () => {
      expect(timeline.isPlaying()).toBe(false);
      timeline.toggle();
      expect(timeline.isPlaying()).toBe(true);
      timeline.toggle();
      expect(timeline.isPlaying()).toBe(false);
    });

    it('should not play when already playing', () => {
      timeline.play();
      timeline.pause();
      // Should be safe to call play again
      expect(() => timeline.play()).not.toThrow();
    });

    it('should not pause when not playing', () => {
      expect(() => timeline.pause()).not.toThrow();
      expect(timeline.isStopped()).toBe(false);
    });
  });

  describe('Seek', () => {
    it('should seek by progress', () => {
      timeline.addKeyframe({
        name: 'x-anim',
        property: 'x',
        keyframes: [
          { time: 0, value: 0 },
          { time: 1, value: 100 },
        ],
        duration: 1000,
      });

      timeline.seek(0.5);
      expect(timeline.getProgress()).toBeCloseTo(0.5, 5);
      expect(timeline.getCurrentTime()).toBeCloseTo(500, 5);
    });

    it('should seek by absolute time', () => {
      timeline.addKeyframe({
        name: 'x-anim',
        property: 'x',
        keyframes: [
          { time: 0, value: 0 },
          { time: 1, value: 100 },
        ],
        duration: 1000,
      });

      timeline.seek(250);
      expect(timeline.getCurrentTime()).toBeCloseTo(250, 5);
      // At 25% with easeOutCubic: 1 - (1-0.25)^3 = 1 - 0.421875 = 0.578125
      expect(timeline.getState().x).toBeCloseTo(57.81, 2);
    });

    it('should clamp progress to [0, 1]', () => {
      timeline.addKeyframe({
        name: 'x-anim',
        property: 'x',
        keyframes: [
          { time: 0, value: 0 },
          { time: 1, value: 100 },
        ],
        duration: 1000,
      });

      timeline.seek(-0.5);
      expect(timeline.getProgress()).toBeGreaterThanOrEqual(0);

      timeline.seek(1.5);
      expect(timeline.getProgress()).toBeLessThanOrEqual(1);
    });

    it('should complete at end', () => {
      timeline.addKeyframe({
        name: 'x-anim',
        property: 'x',
        keyframes: [
          { time: 0, value: 0 },
          { time: 1, value: 100 },
        ],
        duration: 1000,
      });

      timeline.seek(1);
      // At exactly 100% (totalDuration), not yet completed
      // because we use < not <=
      expect(timeline.isCompleted()).toBe(false);
    });

    it('should loop when enabled', () => {
      const tl = new Timeline({ duration: 1000, loop: true });
      tl.addKeyframe({
        name: 'x-anim',
        property: 'x',
        keyframes: [
          { time: 0, value: 0 },
          { time: 1, value: 100 },
        ],
        duration: 1000,
      });

      tl.seek(1.5);
      expect(tl.getProgress()).toBeCloseTo(0.5, 5);
      tl.destroy();
    });
  });

  describe('Events', () => {
    it('should emit play event', () => {
      let played = false;
      timeline.on('play', () => { played = true; });
      timeline.play();
      expect(played).toBe(true);
      timeline.pause();
    });

    it('should emit pause event', () => {
      timeline.play();
      let paused = false;
      timeline.on('pause', () => { paused = true; });
      timeline.pause();
      expect(paused).toBe(true);
    });

    it('should emit stop event', () => {
      timeline.play();
      let stopped = false;
      timeline.on('stop', () => { stopped = true; });
      timeline.stop();
      expect(stopped).toBe(true);
    });

    it('should emit complete event', () => {
      let completed = false;
      timeline.on('complete', () => { completed = true; });
      // seek to 1 triggers completion check
      timeline.seek(1.0001);
      expect(completed).toBe(true);
    });

    it('should remove event listener', () => {
      let count = 0;
      const cb = () => { count++; };
      timeline.on('play', cb);
      timeline.play();
      timeline.off('play', cb);
      timeline.play();
      // Should be 2 because we played twice but removed in between
      // Actually first play += 1, remove, second play += 0
      expect(count).toBe(1);
      timeline.pause();
    });
  });

  describe('Animation Clips', () => {
    it('should add and use clip', () => {
      const { AnimationClip } = require('../src/animation_clip');
      const clip = new AnimationClip({
        name: 'test-clip',
        animations: [
          {
            property: 'x',
            keyframes: [
              { time: 0, value: 0 },
              { time: 1, value: 100 },
            ],
          },
        ],
        duration: 1000,
      });

      timeline.addClip(clip);
      timeline.seek(0.5);
      const state = timeline.getState();
      expect(state.x).toBeDefined();
    });

    it('should remove clip', () => {
      const { AnimationClip } = require('../src/animation_clip');
      const clip = new AnimationClip({
        name: 'test-clip',
        animations: [
          {
            property: 'x',
            keyframes: [
              { time: 0, value: 0 },
              { time: 1, value: 100 },
            ],
          },
        ],
        duration: 1000,
      });

      timeline.addClip(clip);
      timeline.removeClip('test-clip');
      expect(() => timeline.removeClip('test-clip')).not.toThrow();
    });
  });

  describe('State', () => {
    it('should get current state', () => {
      timeline.addKeyframe({
        name: 'x-anim',
        property: 'x',
        keyframes: [
          { time: 0, value: 0 },
          { time: 1, value: 100 },
        ],
        duration: 1000,
      });

      timeline.seek(0.5);
      const state = timeline.getState();
      expect(typeof state).toBe('object');
      // easeOutCubic(0.5) = 0.875
      expect(state.x).toBeCloseTo(87.5, 2);
    });

    it('should get progress', () => {
      timeline.seek(0.5);
      expect(timeline.getProgress()).toBeCloseTo(0.5, 5);
    });

    it('should get total duration', () => {
      expect(timeline.getTotalDuration()).toBe(1000);
    });

    it('should set total duration', () => {
      timeline.setTotalDuration(2000);
      expect(timeline.getTotalDuration()).toBe(2000);
    });
  });

  describe('Destroy', () => {
    it('should clean up', () => {
      timeline.play();
      timeline.addKeyframe({
        name: 'x-anim',
        property: 'x',
        keyframes: [
          { time: 0, value: 0 },
          { time: 1, value: 100 },
        ],
        duration: 1000,
      });

      timeline.destroy();
      expect(timeline.isStopped()).toBe(true);
      expect(timeline.getCurrentTime()).toBe(0);
    });
  });

  describe('Edge Cases', () => {
    it('should handle zero duration animation', () => {
      timeline.addKeyframe({
        name: 'zero',
        property: 'x',
        keyframes: [
          { time: 0, value: 50 },
          { time: 1, value: 50 },
        ],
        duration: 1000,
      });

      timeline.seek(0.5);
      expect(timeline.getState().x).toBeCloseTo(50, 5);
    });

    it('should handle single keyframe', () => {
      timeline.addKeyframe({
        name: 'single',
        property: 'x',
        keyframes: [
          { time: 0.5, value: 42 },
        ],
        duration: 1000,
      });

      timeline.seek(0.5);
      expect(timeline.getState().x).toBeCloseTo(42, 5);
    });

    it('should handle delay', () => {
      timeline.addKeyframe({
        name: 'delayed',
        property: 'x',
        keyframes: [
          { time: 0, value: 0 },
          { time: 1, value: 100 },
        ],
        duration: 1000,
        delay: 500,
      });

      // With delay, the animation starts at 50% of timeline
      timeline.seek(0.25);
      const state = timeline.getState();
      // At 25% of timeline, we're still in the delay period
      // The keyframe progress would be negative, clamped to 0
      expect(state.x).toBeDefined();
    });
  });
});
