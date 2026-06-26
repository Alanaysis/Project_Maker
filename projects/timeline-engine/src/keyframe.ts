/**
 * Keyframe System
 *
 * Manages keyframe entries with time/value pairs,
 * providing bounds lookup and interpolation.
 */

import { KeyframeEntry, EasingFunction } from './types';
import { resolveEasing, clamp } from './easing';

export class Keyframe {
  public time: number;
  public value: number;

  constructor(time: number, value: number) {
    this.time = time;
    this.value = value;
  }

  setTime(time: number): void {
    this.time = time;
  }

  setValue(value: number): void {
    this.value = value;
  }
}

export class KeyframeTrack {
  private keyframes: Keyframe[];
  private easingFn: EasingFunction;
  private sorted: boolean;

  constructor(keyframes: KeyframeEntry[], easing?: EasingFunction | string) {
    this.keyframes = keyframes.map(kf => new Keyframe(kf.time, kf.value));
    this.easingFn = resolveEasing(easing);
    this.sorted = false;
  }

  private ensureSorted(): void {
    if (!this.sorted) {
      this.keyframes.sort((a, b) => a.time - b.time);
      this.sorted = true;
    }
  }

  getKeyframes(): Keyframe[] {
    this.ensureSorted();
    return [...this.keyframes];
  }

  getLength(): number {
    this.ensureSorted();
    return this.keyframes.length;
  }

  /**
   * Find the two keyframes that surround the given time.
   * Returns [startKeyframe, endKeyframe].
   */
  findBounds(t: number): [Keyframe, Keyframe] {
    this.ensureSorted();

    if (this.keyframes.length === 0) {
      return [new Keyframe(0, 0), new Keyframe(1, 0)];
    }

    if (this.keyframes.length === 1) {
      return [this.keyframes[0], this.keyframes[0]];
    }

    // Before first keyframe
    if (t <= this.keyframes[0].time) {
      return [this.keyframes[0], this.keyframes[1]];
    }

    // After last keyframe
    if (t >= this.keyframes[this.keyframes.length - 1].time) {
      return [
        this.keyframes[this.keyframes.length - 2],
        this.keyframes[this.keyframes.length - 1],
      ];
    }

    // Binary search for surrounding keyframes
    let lo = 0;
    let hi = this.keyframes.length - 1;

    while (lo < hi - 1) {
      const mid = Math.floor((lo + hi) / 2);
      if (this.keyframes[mid].time <= t) {
        lo = mid;
      } else {
        hi = mid;
      }
    }

    return [this.keyframes[lo], this.keyframes[hi]];
  }

  /**
   * Interpolate value at the given time.
   */
  interpolate(t: number): number {
    this.ensureSorted();

    if (this.keyframes.length === 0) {
      return 0;
    }

    if (this.keyframes.length === 1) {
      return this.keyframes[0].value;
    }

    const [start, end] = this.findBounds(t);

    const range = end.time - start.time;
    if (range === 0) {
      return start.value;
    }

    const localT = (t - start.time) / range;
    const easedT = this.easingFn(clamp(localT));

    return start.value + (end.value - start.value) * easedT;
  }

  /**
   * Update the keyframe entries.
   */
  updateKeyframes(keyframes: KeyframeEntry[]): void {
    this.keyframes = keyframes.map(kf => new Keyframe(kf.time, kf.value));
    this.sorted = false;
  }

  /**
   * Update the easing function.
   */
  updateEasing(easing: EasingFunction | string): void {
    this.easingFn = resolveEasing(easing);
  }

  /**
   * Get the total duration (max time - min time).
   */
  getDuration(): number {
    this.ensureSorted();
    if (this.keyframes.length === 0) return 0;
    return this.keyframes[this.keyframes.length - 1].time - this.keyframes[0].time;
  }
}
