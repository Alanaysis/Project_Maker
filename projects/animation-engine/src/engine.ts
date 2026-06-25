/**
 * Animation Engine
 *
 * Core engine that manages all animations, provides the main loop,
 * and handles performance optimization through batching and scheduling.
 */

import {
  AnimationConfig,
  TweenConfig,
  PerformanceMetrics,
  AnimationState,
} from './types';
import { Animation } from './animation';
import { Tween } from './tween';
import { AnimationQueue } from './queue';
import { now, requestAnimationFramePolyfill, cancelAnimationFramePolyfill } from './utils';

export class AnimationEngine {
  /** All registered animations */
  private animations: Map<string, Animation> = new Map();

  /** All registered tweens */
  private tweens: Map<string, Tween<any>> = new Map();

  /** Named animation queues */
  private queues: Map<string, AnimationQueue> = new Map();

  /** Whether the engine is running */
  private running: boolean = false;

  /** RAF handle */
  private rafId: number = 0;

  /** Performance metrics */
  private metrics: PerformanceMetrics = {
    fps: 0,
    activeAnimations: 0,
    totalFrames: 0,
    averageFrameTime: 0,
  };

  /** Frame time history for FPS calculation */
  private frameTimeHistory: number[] = [];

  /** Last frame timestamp */
  private lastFrameTime: number = 0;

  /** FPS calculation interval */
  private fpsUpdateInterval: number = 500; // ms

  /** Last FPS calculation time */
  private lastFpsCalcTime: number = 0;

  /** Bound loop function */
  private boundLoop: (timestamp: number) => void;

  constructor() {
    this.boundLoop = this.loop.bind(this);
  }

  /**
   * Create and register a keyframe animation
   */
  animate(config: AnimationConfig): Animation {
    const animation = new Animation(config);
    this.animations.set(animation.id, animation);

    // Auto-start if engine is running
    if (this.running) {
      animation.start();
    }

    this.ensureRunning();
    return animation;
  }

  /**
   * Create and register a tween
   */
  tween<T extends Record<string, number>>(config: TweenConfig<T>): Tween<T> {
    const tween = new Tween<T>(config);
    this.tweens.set(tween.id, tween);

    if (this.running) {
      tween.start();
    }

    this.ensureRunning();
    return tween;
  }

  /**
   * Get or create a named animation queue
   */
  queue(name: string = 'default'): AnimationQueue {
    if (!this.queues.has(name)) {
      this.queues.set(name, new AnimationQueue(name));
    }
    return this.queues.get(name)!;
  }

  /**
   * Start the engine loop
   */
  start(): void {
    if (this.running) return;
    this.running = true;
    this.lastFrameTime = now();

    // Start all registered animations
    this.animations.forEach((anim) => {
      if (anim.state === AnimationState.IDLE) {
        anim.start();
      } else if (anim.state === AnimationState.PAUSED) {
        anim.start();
      }
    });

    this.tweens.forEach((tween) => {
      if (tween.state === AnimationState.IDLE) {
        tween.start();
      } else if (tween.state === AnimationState.PAUSED) {
        tween.start();
      }
    });

    this.rafId = requestAnimationFramePolyfill(this.boundLoop);
  }

  /**
   * Pause all animations
   */
  pause(): void {
    this.animations.forEach((anim) => anim.pause());
    this.tweens.forEach((tween) => tween.pause());
    this.queues.forEach((queue) => queue.pause());
  }

  /**
   * Resume all animations
   */
  resume(): void {
    this.animations.forEach((anim) => anim.start());
    this.tweens.forEach((tween) => tween.start());
    this.queues.forEach((queue) => queue.resume());
    this.ensureRunning();
  }

  /**
   * Stop the engine and cancel all animations
   */
  stop(): void {
    this.running = false;

    if (this.rafId) {
      cancelAnimationFramePolyfill(this.rafId);
      this.rafId = 0;
    }

    this.animations.forEach((anim) => anim.cancel());
    this.tweens.forEach((tween) => tween.cancel());
    this.queues.forEach((queue) => queue.cancel());

    this.animations.clear();
    this.tweens.clear();
  }

  /**
   * Remove completed animations
   */
  cleanup(): void {
    this.animations.forEach((anim, id) => {
      if (
        anim.state === AnimationState.COMPLETED ||
        anim.state === AnimationState.CANCELLED
      ) {
        this.animations.delete(id);
      }
    });

    this.tweens.forEach((tween, id) => {
      if (
        tween.state === AnimationState.COMPLETED ||
        tween.state === AnimationState.CANCELLED
      ) {
        this.tweens.delete(id);
      }
    });
  }

  /**
   * Get performance metrics
   */
  getMetrics(): PerformanceMetrics {
    return { ...this.metrics };
  }

  /**
   * Get number of active animations
   */
  get activeCount(): number {
    let count = 0;
    this.animations.forEach((anim) => {
      if (anim.state === AnimationState.RUNNING) count++;
    });
    this.tweens.forEach((tween) => {
      if (tween.state === AnimationState.RUNNING) count++;
    });
    return count;
  }

  /**
   * Get all animations
   */
  getAnimations(): Animation[] {
    return Array.from(this.animations.values());
  }

  /**
   * Get all tweens
   */
  getTweens(): Tween<any>[] {
    return Array.from(this.tweens.values());
  }

  /**
   * Ensure the engine loop is running
   */
  private ensureRunning(): void {
    if (!this.running) {
      this.start();
    }
  }

  /**
   * Main animation loop
   */
  private loop(timestamp: number): void {
    if (!this.running) return;

    // Calculate frame time
    const frameTime = timestamp - this.lastFrameTime;
    this.lastFrameTime = timestamp;

    // Update frame time history
    this.frameTimeHistory.push(frameTime);
    if (this.frameTimeHistory.length > 60) {
      this.frameTimeHistory.shift();
    }

    // Update FPS
    this.metrics.totalFrames++;
    if (timestamp - this.lastFpsCalcTime >= this.fpsUpdateInterval) {
      const avgFrameTime =
        this.frameTimeHistory.reduce((a, b) => a + b, 0) / this.frameTimeHistory.length;
      this.metrics.fps = Math.round(1000 / avgFrameTime);
      this.metrics.averageFrameTime = Math.round(avgFrameTime * 100) / 100;
      this.lastFpsCalcTime = timestamp;
    }

    // Update all animations
    let hasActive = false;

    this.animations.forEach((anim) => {
      const running = anim.update(timestamp);
      if (running) hasActive = true;
    });

    this.tweens.forEach((tween) => {
      const running = tween.update(timestamp);
      if (running) hasActive = true;
    });

    this.metrics.activeAnimations = this.activeCount;

    // Cleanup completed
    this.cleanup();

    // Continue loop if there are active animations
    if (hasActive || this.animations.size > 0 || this.tweens.size > 0) {
      this.rafId = requestAnimationFramePolyfill(this.boundLoop);
    } else {
      this.running = false;
    }
  }
}

/**
 * Create a new animation engine instance
 */
export function createEngine(): AnimationEngine {
  return new AnimationEngine();
}
