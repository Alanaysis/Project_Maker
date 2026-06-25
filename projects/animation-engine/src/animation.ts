/**
 * Animation Class
 *
 * Represents a single animation with keyframes, easing, and state management.
 * Handles the core animation loop: time calculation -> easing -> interpolation -> apply.
 */

import {
  AnimationConfig,
  AnimationState,
  AnimationDirection,
  FillMode,
  Keyframe,
  EasingFunction,
} from './types';
import { resolveEasing } from './easing';
import { interpolateStyle, applyStyles, now } from './utils';

export class Animation {
  /** Unique animation ID */
  public readonly id: string;

  /** Current animation state */
  public state: AnimationState = AnimationState.IDLE;

  /** Current progress (0-1) within current iteration */
  public progress: number = 0;

  /** Current iteration number */
  public currentIteration: number = 0;

  /** Total elapsed time in ms */
  private elapsed: number = 0;

  /** Start timestamp */
  private startTime: number = 0;

  /** Pause timestamp */
  private pauseTime: number = 0;

  /** Accumulated pause duration */
  private pauseDuration: number = 0;

  /** Configuration */
  private config: AnimationConfig;

  /** Resolved easing function */
  private easingFn: EasingFunction;

  /** Resolved target element */
  private element: HTMLElement | null = null;

  /** Cached sorted keyframes */
  private sortedKeyframes: Keyframe[];

  constructor(config: AnimationConfig, id?: string) {
    this.id = id || `anim_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    this.config = { ...config };
    this.easingFn = resolveEasing(config.easing);
    this.sortedKeyframes = [...config.keyframes].sort((a, b) => a.offset - b.offset);
  }

  /**
   * Resolve the target element
   */
  private resolveTarget(): HTMLElement | null {
    if (this.element) return this.element;

    const target = this.config.target;
    if (typeof target === 'string') {
      this.element = document.querySelector(target) as HTMLElement;
    } else {
      this.element = target;
    }
    return this.element;
  }

  /**
   * Start the animation
   */
  start(timestamp?: number): void {
    if (this.state === AnimationState.RUNNING) return;

    const ts = timestamp ?? now();

    if (this.state === AnimationState.PAUSED) {
      // Resume from pause
      this.pauseDuration += ts - this.pauseTime;
      this.state = AnimationState.RUNNING;
      return;
    }

    this.startTime = ts;
    this.pauseDuration = 0;
    this.elapsed = 0;
    this.progress = 0;
    this.currentIteration = 0;
    this.state = AnimationState.RUNNING;

    this.config.onStart?.();
  }

  /**
   * Pause the animation
   */
  pause(): void {
    if (this.state !== AnimationState.RUNNING) return;
    this.pauseTime = now();
    this.state = AnimationState.PAUSED;
  }

  /**
   * Cancel the animation
   */
  cancel(): void {
    this.state = AnimationState.CANCELLED;
    this.config.onCancel?.();
  }

  /**
   * Reset the animation to initial state
   */
  reset(): void {
    this.state = AnimationState.IDLE;
    this.elapsed = 0;
    this.progress = 0;
    this.currentIteration = 0;
    this.startTime = 0;
    this.pauseDuration = 0;
    this.element = null;
  }

  /**
   * Update the animation for the current frame
   * @param timestamp Current timestamp from requestAnimationFrame
   * @returns true if animation is still running, false if completed
   */
  update(timestamp: number): boolean {
    if (this.state !== AnimationState.RUNNING) {
      return this.state === AnimationState.PAUSED;
    }

    const { duration, delay = 0, iterations = 1, direction = AnimationDirection.NORMAL, fill = FillMode.NONE } = this.config;

    // Calculate elapsed time (excluding pauses)
    this.elapsed = timestamp - this.startTime - this.pauseDuration;

    // Handle delay
    if (this.elapsed < delay) {
      if (fill === FillMode.BACKWARDS || fill === FillMode.BOTH) {
        this.applyAtProgress(0, direction);
      }
      return true;
    }

    const activeTime = this.elapsed - delay;
    const totalDuration = duration * iterations;

    // Check if animation is complete
    if (activeTime >= totalDuration) {
      this.currentIteration = iterations === Infinity ? 0 : iterations - 1;
      this.progress = 1;

      // Apply final frame
      const effectiveDirection = this.getEffectiveDirection(direction, this.currentIteration);
      const easedProgress = effectiveDirection === AnimationDirection.REVERSE
        ? this.easingFn(0)
        : this.easingFn(1);
      this.applyAtProgress(effectiveDirection === AnimationDirection.REVERSE ? 0 : 1, direction);

      this.config.onUpdate?.(1);
      this.state = AnimationState.COMPLETED;
      this.config.onComplete?.();
      return false;
    }

    // Calculate current iteration
    this.currentIteration = Math.floor(activeTime / duration);
    if (iterations !== Infinity && this.currentIteration >= iterations) {
      this.currentIteration = iterations - 1;
    }

    // Calculate progress within current iteration
    const iterationTime = activeTime - this.currentIteration * duration;
    let rawProgress = iterationTime / duration;
    rawProgress = Math.min(Math.max(rawProgress, 0), 1);

    // Apply direction
    const effectiveDirection = this.getEffectiveDirection(direction, this.currentIteration);
    let directedProgress = rawProgress;
    if (effectiveDirection === AnimationDirection.REVERSE) {
      directedProgress = 1 - rawProgress;
    }

    // Apply easing
    const easedProgress = this.easingFn(directedProgress);

    // Store progress
    this.progress = easedProgress;

    // Apply styles
    this.applyAtProgress(easedProgress, direction);
    this.config.onUpdate?.(easedProgress);

    return true;
  }

  /**
   * Get effective direction for current iteration
   */
  private getEffectiveDirection(
    direction: AnimationDirection,
    iteration: number
  ): AnimationDirection {
    switch (direction) {
      case AnimationDirection.ALTERNATE:
        return iteration % 2 === 0 ? AnimationDirection.NORMAL : AnimationDirection.REVERSE;
      case AnimationDirection.ALTERNATE_REVERSE:
        return iteration % 2 === 0 ? AnimationDirection.REVERSE : AnimationDirection.NORMAL;
      default:
        return direction;
    }
  }

  /**
   * Apply interpolated styles at given progress
   */
  private applyAtProgress(progress: number, _direction: AnimationDirection): void {
    const element = this.resolveTarget();
    if (!element) return;

    const keyframes = this.sortedKeyframes;
    if (keyframes.length === 0) return;

    // Find surrounding keyframes
    let startFrame = keyframes[0];
    let endFrame = keyframes[keyframes.length - 1];

    for (let i = 0; i < keyframes.length - 1; i++) {
      if (progress >= keyframes[i].offset && progress <= keyframes[i + 1].offset) {
        startFrame = keyframes[i];
        endFrame = keyframes[i + 1];
        break;
      }
    }

    // Calculate local progress between the two keyframes
    const range = endFrame.offset - startFrame.offset;
    const localProgress = range === 0 ? 0 : (progress - startFrame.offset) / range;

    // Interpolate all properties
    const styles: Record<string, string | number> = {};
    const allKeys = new Set([
      ...Object.keys(startFrame.styles),
      ...Object.keys(endFrame.styles),
    ]);

    for (const key of allKeys) {
      const startVal = startFrame.styles[key];
      const endVal = endFrame.styles[key];

      if (startVal !== undefined && endVal !== undefined) {
        styles[key] = interpolateStyle(startVal, endVal, localProgress);
      } else if (startVal !== undefined) {
        styles[key] = startVal;
      } else {
        styles[key] = endVal;
      }
    }

    applyStyles(element, styles);
  }
}
