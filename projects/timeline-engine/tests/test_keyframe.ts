/**
 * Tests for keyframe system
 */

import { Keyframe, KeyframeTrack } from '../src/keyframe';
import { KeyframeEntry } from '../src/types';

describe('Keyframe', () => {
  it('should create with time and value', () => {
    const kf = new Keyframe(0.5, 100);
    expect(kf.time).toBe(0.5);
    expect(kf.value).toBe(100);
  });

  it('should update time', () => {
    const kf = new Keyframe(0.5, 100);
    kf.setTime(0.75);
    expect(kf.time).toBe(0.75);
  });

  it('should update value', () => {
    const kf = new Keyframe(0.5, 100);
    kf.setValue(200);
    expect(kf.value).toBe(200);
  });
});

describe('KeyframeTrack', () => {
  const createEntries = (pairs: [number, number][]): KeyframeEntry[] =>
    pairs.map(([time, value]) => ({ time, value }));

  describe('Constructor', () => {
    it('should create track from entries', () => {
      const entries = createEntries([[0, 0], [1, 100]]);
      const track = new KeyframeTrack(entries);
      expect(track.getLength()).toBe(2);
    });

    it('should handle single keyframe', () => {
      const entries = createEntries([[0.5, 50]]);
      const track = new KeyframeTrack(entries);
      expect(track.getLength()).toBe(1);
    });

    it('should handle empty keyframes', () => {
      const track = new KeyframeTrack([]);
      expect(track.getLength()).toBe(0);
    });
  });

  describe('Sorting', () => {
    it('should sort keyframes by time', () => {
      const entries = createEntries([
        [0.5, 50],
        [0, 0],
        [1, 100],
      ]);
      const track = new KeyframeTrack(entries);
      const kfs = track.getKeyframes();
      expect(kfs[0].time).toBe(0);
      expect(kfs[1].time).toBe(0.5);
      expect(kfs[2].time).toBe(1);
    });
  });

  describe('findBounds', () => {
    it('should find bounds for time within range', () => {
      const entries = createEntries([
        [0, 0],
        [0.5, 50],
        [1, 100],
      ]);
      const track = new KeyframeTrack(entries);
      const [start, end] = track.findBounds(0.3);
      expect(start.time).toBe(0);
      expect(end.time).toBe(0.5);
    });

    it('should handle time before first keyframe', () => {
      const entries = createEntries([
        [0.2, 20],
        [0.8, 80],
      ]);
      const track = new KeyframeTrack(entries);
      const [start, end] = track.findBounds(0);
      expect(start.time).toBe(0.2);
      expect(end.time).toBe(0.8);
    });

    it('should handle time after last keyframe', () => {
      const entries = createEntries([
        [0.2, 20],
        [0.8, 80],
      ]);
      const track = new KeyframeTrack(entries);
      const [start, end] = track.findBounds(1);
      expect(start.time).toBe(0.2);
      expect(end.time).toBe(0.8);
    });

    it('should handle single keyframe', () => {
      const entries = createEntries([[0.5, 50]]);
      const track = new KeyframeTrack(entries);
      const [start, end] = track.findBounds(0.5);
      expect(start.time).toBe(0.5);
      expect(end.time).toBe(0.5);
    });

    it('should handle empty track', () => {
      const track = new KeyframeTrack([]);
      const [start, end] = track.findBounds(0.5);
      expect(start.time).toBe(0);
      expect(end.time).toBe(1);
    });
  });

  describe('Interpolation', () => {
    it('should interpolate linearly with linear easing', () => {
      const entries = createEntries([
        [0, 0],
        [1, 100],
      ]);
      const track = new KeyframeTrack(entries, 'linear');
      expect(track.interpolate(0)).toBeCloseTo(0, 5);
      expect(track.interpolate(0.5)).toBeCloseTo(50, 5);
      expect(track.interpolate(1)).toBeCloseTo(100, 5);
    });

    it('should interpolate with easeOutCubic', () => {
      const entries = createEntries([
        [0, 0],
        [1, 100],
      ]);
      const track = new KeyframeTrack(entries, 'ease-out-cubic');
      expect(track.interpolate(0)).toBeCloseTo(0, 5);
      expect(track.interpolate(1)).toBeCloseTo(100, 5);
      // easeOutCubic at 0.5 = 0.6875
      expect(track.interpolate(0.5)).toBeCloseTo(68.75, 2);
    });

    it('should interpolate with easeInCubic', () => {
      const entries = createEntries([
        [0, 0],
        [1, 100],
      ]);
      const track = new KeyframeTrack(entries, 'ease-in-cubic');
      expect(track.interpolate(0)).toBeCloseTo(0, 5);
      expect(track.interpolate(1)).toBeCloseTo(100, 5);
      // easeInCubic at 0.5 = 0.125
      expect(track.interpolate(0.5)).toBeCloseTo(12.5, 2);
    });

    it('should handle multiple keyframes', () => {
      const entries = createEntries([
        [0, 0],
        [0.5, 50],
        [1, 100],
      ]);
      const track = new KeyframeTrack(entries, 'linear');
      expect(track.interpolate(0.25)).toBeCloseTo(25, 5);
      expect(track.interpolate(0.75)).toBeCloseTo(75, 5);
    });

    it('should return single keyframe value', () => {
      const entries = createEntries([[0.5, 42]]);
      const track = new KeyframeTrack(entries);
      expect(track.interpolate(0)).toBeCloseTo(42, 5);
      expect(track.interpolate(0.5)).toBeCloseTo(42, 5);
      expect(track.interpolate(1)).toBeCloseTo(42, 5);
    });

    it('should handle empty track', () => {
      const track = new KeyframeTrack([]);
      expect(track.interpolate(0.5)).toBeCloseTo(0, 5);
    });

    it('should clamp values for time outside range', () => {
      const entries = createEntries([
        [0.2, 20],
        [0.8, 80],
      ]);
      const track = new KeyframeTrack(entries, 'linear');
      // Time before range
      expect(track.interpolate(-0.1)).toBeCloseTo(20, 5);
      // Time after range
      expect(track.interpolate(1.1)).toBeCloseTo(80, 5);
    });
  });

  describe('getDuration', () => {
    it('should return duration', () => {
      const entries = createEntries([
        [0, 0],
        [1, 100],
      ]);
      const track = new KeyframeTrack(entries);
      expect(track.getDuration()).toBe(1);
    });

    it('should return 0 for single keyframe', () => {
      const entries = createEntries([[0.5, 50]]);
      const track = new KeyframeTrack(entries);
      expect(track.getDuration()).toBe(0);
    });

    it('should return 0 for empty track', () => {
      const track = new KeyframeTrack([]);
      expect(track.getDuration()).toBe(0);
    });
  });

  describe('updateKeyframes', () => {
    it('should update keyframes', () => {
      const entries = createEntries([
        [0, 0],
        [1, 100],
      ]);
      const track = new KeyframeTrack(entries);
      track.updateKeyframes(createEntries([
        [0, 0],
        [1, 200],
      ]));
      expect(track.interpolate(1)).toBeCloseTo(200, 5);
    });

    it('should re-sort after update', () => {
      const entries = createEntries([
        [0, 0],
        [1, 100],
      ]);
      const track = new KeyframeTrack(entries);
      track.updateKeyframes(createEntries([
        [1, 100],
        [0, 0],
      ]));
      expect(track.interpolate(0.5)).toBeCloseTo(50, 5);
    });
  });

  describe('updateEasing', () => {
    it('should update easing function', () => {
      const entries = createEntries([
        [0, 0],
        [1, 100],
      ]);
      const track = new KeyframeTrack(entries, 'linear');
      track.updateEasing('ease-in-cubic');
      const val = track.interpolate(0.5);
      expect(val).toBeCloseTo(12.5, 2);
    });

    it('should accept custom easing function', () => {
      const entries = createEntries([
        [0, 0],
        [1, 100],
      ]);
      const track = new KeyframeTrack(entries, 'linear');
      const custom = (t: number) => t * t;
      track.updateEasing(custom);
      expect(track.interpolate(0.5)).toBeCloseTo(25, 5);
    });
  });

  describe('getKeyframes', () => {
    it('should return copy of keyframes', () => {
      const entries = createEntries([
        [0, 0],
        [1, 100],
      ]);
      const track = new KeyframeTrack(entries);
      const kfs = track.getKeyframes();
      expect(kfs).toHaveLength(2);
      expect(kfs[0].time).toBe(0);
      expect(kfs[1].time).toBe(1);
    });
  });
});
