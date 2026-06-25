/**
 * Tween Class
 *
 * Simplified animation for numeric property interpolation.
 * More efficient than keyframe animations for simple property changes.
 */

import { TweenConfig, EasingFunction } from './types';
import { resolveEasing } from './easing';
import { lerp, now } from './utils';
import { AnimationState } from './types';

export class Tween<T extends Record<string, number>> {
  /** Unique tween ID */
  public readonly id: string;

  /** Current state */
  public state: AnimationState = AnimationState.IDLE;

  /** Current progress (0-1) */
  public progress: number = 0;

  /** Current interpolated values */
  public currentValues: T;

  /** Configuration */
  private config: TweenConfig<T>;

  /** Resolved easing function */
  private easingFn: EasingFunction;

  /** Start timestamp */
  private startTime: number = 0;

  /** Pause timestamp */
  private pauseTime: number = 0;

  /** Accumulated pause duration */
  private pauseDuration: number = 0;

  /** Current iteration */
  private currentIteration: number = 0;

  /** Property keys for iteration */
  private keys: (keyof T)[];

  constructor(config: TweenConfig<T>, id?: string) {
    this.id = id || `tween_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    this.config = { ...config };
    this.easingFn = resolveEasing(config.easing);
    this.currentValues = { ...config.from };
    this.keys = Object.keys(config.from) as (keyof T)[];
  }

  /**
   * Start the tween
   */
  start(timestamp?: number): void {
    if (this.state === AnimationState.RUNNING) return;

    const ts = timestamp ?? now();

    if (this.state === AnimationState.PAUSED) {
      this.pauseDuration += ts - this.pauseTime;
      this.state = AnimationState.RUNNING;
      return;
    }

    this.startTime = ts;
    this.pauseDuration = 0;
    this.currentIteration = 0;
    this.state = AnimationState.RUNNING;
  }

  /**
   * Pause the tween
   */
  pause(): void {
    if (this.state !== AnimationState.RUNNING) return;
    this.pauseTime = now();
    this.state = AnimationState.PAUSED;
  }

  /**
   * Cancel the tween
   */
  cancel(): void {
    this.state = AnimationState.CANCELLED;
  }

  /**
   * Update the tween
   * @returns true if still running
   */
  update(timestamp: number): boolean {
    if (this.state !== AnimationState.RUNNING) {
      return this.state === AnimationState.PAUSED;
    }

    const { duration, delay = 0, iterations = 1 } = this.config;
    const elapsed = timestamp - this.startTime - this.pauseDuration;

    // Handle delay
    if (elapsed < delay) {
      return true;
    }

    const activeTime = elapsed - delay;
    const totalDuration = duration * iterations;

    // Check completion
    if (activeTime >= totalDuration) {
      this.progress = 1;
      this.updateValues(1);
      this.config.onUpdate?.({ ...this.currentValues });
      this.state = AnimationState.COMPLETED;
      this.config.onComplete?.();
      return false;
    }

    // Calculate progress
    this.currentIteration = Math.floor(activeTime / duration);
    const iterationTime = activeTime - this.currentIteration * duration;
    let rawProgress = Math.min(Math.max(iterationTime / duration, 0), 1);

    // Apply easing
    const easedProgress = this.easingFn(rawProgress);
    this.progress = easedProgress;

    // Update values
    this.updateValues(easedProgress);
    this.config.onUpdate?.({ ...this.currentValues });

    return true;
  }

  /**
   * Update current values based on progress
   */
  private updateValues(t: number): void {
    const { from, to } = this.config;
    for (const key of this.keys) {
      (this.currentValues as any)[key] = lerp(from[key], to[key], t);
    }
  }
}
