/**
 * Tests for AnimationClip
 */

import { AnimationClip } from '../src/animation_clip';
import { AnimationClipConfig, KeyframeEntry } from '../src/types';

describe('AnimationClip', () => {
  const createConfig = (name: string, animations: Array<{
    property: string;
    keyframes: KeyframeEntry[];
    easing?: string;
  }>, duration: number = 1000): AnimationClipConfig => ({
    name,
    animations,
    duration,
  });

  it('should create clip with name and animations', () => {
    const config = createConfig('test-clip', [
      { property: 'x', keyframes: [{ time: 0, value: 0 }, { time: 1, value: 100 }] },
      { property: 'opacity', keyframes: [{ time: 0, value: 0 }, { time: 1, value: 1 }] },
    ], 1000);

    const clip = new AnimationClip(config);
    expect(clip.getName()).toBe('test-clip');
    expect(clip.getDuration()).toBe(1000);
  });

  it('should get properties', () => {
    const config = createConfig('test-clip', [
      { property: 'x', keyframes: [{ time: 0, value: 0 }, { time: 1, value: 100 }] },
      { property: 'y', keyframes: [{ time: 0, value: 0 }, { time: 1, value: 50 }] },
    ]);

    const clip = new AnimationClip(config);
    const props = clip.getProperties();
    expect(props).toContain('x');
    expect(props).toContain('y');
  });

  it('should get value at time', () => {
    const config = createConfig('test-clip', [
      { property: 'x', keyframes: [{ time: 0, value: 0 }, { time: 1, value: 100 }] },
    ]);

    const clip = new AnimationClip(config);
    expect(clip.getValueAt('x', 0)).toBeCloseTo(0, 5);
    expect(clip.getValueAt('x', 500)).toBeCloseTo(50, 5);
    expect(clip.getValueAt('x', 1000)).toBeCloseTo(100, 5);
  });

  it('should loop at duration boundary', () => {
    const config = createConfig('test-clip', [
      { property: 'x', keyframes: [{ time: 0, value: 0 }, { time: 1, value: 100 }] },
    ]);

    const clip = new AnimationClip(config);
    // time=0 -> normalized=0 -> value=0
    expect(clip.getValueAt('x', 0)).toBeCloseTo(0, 5);
    // time=500 -> normalized=0.5 -> value=50
    expect(clip.getValueAt('x', 500)).toBeCloseTo(50, 5);
    // time=1000 -> normalized=0 (looped) -> value=0
    expect(clip.getValueAt('x', 1000)).toBeCloseTo(0, 5);
    // time=1500 -> normalized=0.5 (looped) -> value=50
    expect(clip.getValueAt('x', 1500)).toBeCloseTo(50, 5);
  });

  it('should handle unknown property', () => {
    const config = createConfig('test-clip', [
      { property: 'x', keyframes: [{ time: 0, value: 0 }, { time: 1, value: 100 }] },
    ]);

    const clip = new AnimationClip(config);
    expect(clip.getValueAt('z', 500)).toBe(0);
  });

  it('should update animation', () => {
    const config = createConfig('test-clip', [
      { property: 'x', keyframes: [{ time: 0, value: 0 }, { time: 1, value: 100 }] },
    ]);

    const clip = new AnimationClip(config);
    clip.updateAnimation('x', [
      { time: 0, value: 0 },
      { time: 1, value: 200 },
    ]);
    // time=1000 -> normalized=0 (looped) -> value=0
    expect(clip.getValueAt('x', 1000)).toBeCloseTo(0, 5);
    // time=500 -> normalized=0.5 -> value=100
    expect(clip.getValueAt('x', 500)).toBeCloseTo(100, 5);
  });

  it('should get animations map', () => {
    const config = createConfig('test-clip', [
      { property: 'x', keyframes: [{ time: 0, value: 0 }, { time: 1, value: 100 }] },
    ]);

    const clip = new AnimationClip(config);
    const anims = clip.getAnimations();
    expect(anims).toBeDefined();
    expect(anims.get('x')).toBeDefined();
  });
});
