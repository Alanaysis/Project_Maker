/**
 * Tests for TimelinePlayer
 */

import { TimelinePlayer } from '../src/timeline_player';
import { KeyframeEntry } from '../src/types';

describe('TimelinePlayer', () => {
  let player: TimelinePlayer;

  beforeEach(() => {
    player = new TimelinePlayer();
    player.setTotalDuration(1000);
  });

  it('should start at zero time', () => {
    expect(player.getCurrentTime()).toBe(0);
  });

  it('should get total duration', () => {
    expect(player.getTotalDuration()).toBe(1000);
  });

  it('should set total duration', () => {
    player.setTotalDuration(2000);
    expect(player.getTotalDuration()).toBe(2000);
  });

  it('should compute state at time 0', () => {
    player.addKeyframeAnimation({
      name: 'test',
      property: 'x',
      keyframes: [{ time: 0, value: 0 }, { time: 1, value: 100 }],
      duration: 1000,
    });

    const state = player.compute(0);
    expect(state.x).toBeCloseTo(0, 5);
  });

  it('should compute state at time 500', () => {
    player.addKeyframeAnimation({
      name: 'test',
      property: 'x',
      keyframes: [{ time: 0, value: 0 }, { time: 1, value: 100 }],
      duration: 1000,
    });

    const state = player.compute(500);
    expect(state.x).toBeCloseTo(50, 5);
  });

  it('should compute state at time 1000', () => {
    player.addKeyframeAnimation({
      name: 'test',
      property: 'x',
      keyframes: [{ time: 0, value: 0 }, { time: 1, value: 100 }],
      duration: 1000,
    });

    const state = player.compute(1000);
    expect(state.x).toBeCloseTo(100, 5);
  });

  it('should compute multiple properties', () => {
    player.addKeyframeAnimation({
      name: 'x-anim',
      property: 'x',
      keyframes: [{ time: 0, value: 0 }, { time: 1, value: 100 }],
      duration: 1000,
    });

    player.addKeyframeAnimation({
      name: 'y-anim',
      property: 'y',
      keyframes: [{ time: 0, value: 0 }, { time: 1, value: 50 }],
      duration: 1000,
    });

    const state = player.compute(500);
    expect(state.x).toBeCloseTo(50, 5);
    expect(state.y).toBeCloseTo(25, 5);
  });

  it('should apply easing', () => {
    player.addKeyframeAnimation({
      name: 'test',
      property: 'x',
      keyframes: [{ time: 0, value: 0 }, { time: 1, value: 100 }],
      duration: 1000,
      easing: 'ease-in-cubic',
    });

    const state = player.compute(500);
    // easeInCubic(0.5) = 0.125, so value = 12.5
    expect(state.x).toBeCloseTo(12.5, 2);
  });

  it('should remove keyframe animation', () => {
    player.addKeyframeAnimation({
      name: 'test',
      property: 'x',
      keyframes: [{ time: 0, value: 0 }, { time: 1, value: 100 }],
      duration: 1000,
    });

    player.removeKeyframeAnimation('x');
    const state = player.compute(500);
    expect(state.x).toBeUndefined();
  });

  it('should reset', () => {
    player.addKeyframeAnimation({
      name: 'test',
      property: 'x',
      keyframes: [{ time: 0, value: 0 }, { time: 1, value: 100 }],
      duration: 1000,
    });

    player.compute(500);
    player.reset();
    expect(player.getCurrentTime()).toBe(0);
  });

  it('should handle clips', () => {
    // This tests that the method exists and doesn't throw
    // Full clip integration is tested in test_timeline.ts
    expect(() => {
      player.addClip({
        getName: () => 'test-clip',
        getDuration: () => 1000,
        getProperties: () => ['x'],
        getValueAt: (prop: string, time: number) => time / 10,
      } as any);
    }).not.toThrow();
  });

  it('should remove clip', () => {
    expect(() => {
      player.removeClip('nonexistent');
    }).not.toThrow();
  });
});
