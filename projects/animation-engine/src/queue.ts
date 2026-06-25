/**
 * Animation Queue
 *
 * Manages sequential and parallel animation execution.
 * Supports chaining animations, delays, and group control.
 */

import { AnimationConfig, TweenConfig } from './types';
import { Animation } from './animation';
import { Tween } from './tween';
import { generateId, now } from './utils';
import { AnimationState } from './types';

/** Queue item representing an animation task */
interface QueueTask {
  id: string;
  type: 'animation' | 'tween' | 'delay';
  config?: AnimationConfig;
  tweenConfig?: TweenConfig<any>;
  delayMs?: number;
  animation?: Animation | Tween<any>;
  resolve: () => void;
  reject: (error: Error) => void;
}

export class AnimationQueue {
  /** Queue name for debugging */
  public readonly name: string;

  /** Pending tasks */
  private queue: QueueTask[] = [];

  /** Currently executing task */
  private currentTask: QueueTask | null = null;

  /** Whether the queue is processing */
  private processing: boolean = false;

  /** Whether the queue is paused */
  private paused: boolean = false;

  /** RAF handle */
  private rafId: number = 0;

  /** Delay timeout handle */
  private delayTimeoutId: number = 0;

  /** Loop callback for animation updates */
  private boundLoop: (timestamp: number) => void;

  constructor(name: string = 'default') {
    this.name = name;
    this.boundLoop = this.loop.bind(this);
  }

  /**
   * Add a keyframe animation to the queue
   * Returns a promise that resolves when the animation completes
   */
  animate(config: AnimationConfig): Promise<void> {
    return new Promise<void>((resolve, reject) => {
      const task: QueueTask = {
        id: generateId(),
        type: 'animation',
        config,
        resolve,
        reject,
      };
      this.queue.push(task);
      this.processNext();
    });
  }

  /**
   * Add a tween to the queue
   * Returns a promise that resolves when the tween completes
   */
  tween<T extends Record<string, number>>(config: TweenConfig<T>): Promise<void> {
    return new Promise<void>((resolve, reject) => {
      const task: QueueTask = {
        id: generateId(),
        type: 'tween',
        tweenConfig: config,
        resolve,
        reject,
      };
      this.queue.push(task);
      this.processNext();
    });
  }

  /**
   * Add a delay to the queue
   */
  wait(ms: number): Promise<void> {
    return new Promise<void>((resolve, reject) => {
      const task: QueueTask = {
        id: generateId(),
        type: 'delay',
        delayMs: ms,
        resolve,
        reject,
      };
      this.queue.push(task);
      this.processNext();
    });
  }

  /**
   * Process the next task in the queue
   */
  private processNext(): void {
    if (this.processing || this.paused) return;
    if (this.queue.length === 0) return;

    this.processing = true;
    this.currentTask = this.queue.shift()!;

    if (this.currentTask.type === 'delay') {
      const delayMs = this.currentTask.delayMs || 0;
      this.delayTimeoutId = setTimeout(() => {
        if (this.currentTask) {
          this.currentTask.resolve();
        }
        this.processing = false;
        this.currentTask = null;
        this.delayTimeoutId = 0;
        this.processNext();
      }, delayMs) as unknown as number;
      return;
    }

    if (this.currentTask.type === 'animation' && this.currentTask.config) {
      const animation = new Animation(this.currentTask.config, this.currentTask.id);
      this.currentTask.animation = animation;
      animation.start();
      this.startLoop();
      return;
    }

    if (this.currentTask.type === 'tween' && this.currentTask.tweenConfig) {
      const tween = new Tween(this.currentTask.tweenConfig, this.currentTask.id);
      this.currentTask.animation = tween;
      tween.start();
      this.startLoop();
      return;
    }

    // Unknown type, skip
    this.currentTask.resolve();
    this.processing = false;
    this.currentTask = null;
    this.processNext();
  }

  /**
   * Start the animation loop
   */
  private startLoop(): void {
    if (typeof requestAnimationFrame !== 'undefined') {
      this.rafId = requestAnimationFrame(this.boundLoop);
    } else {
      // Node.js fallback
      this.rafId = setTimeout(() => this.boundLoop(now()), 16) as unknown as number;
    }
  }

  /**
   * Animation loop
   */
  private loop(timestamp: number): void {
    if (!this.currentTask || !this.currentTask.animation) return;

    const animation = this.currentTask.animation;
    const running = animation.update(timestamp);

    if (!running) {
      // Animation completed
      this.currentTask.resolve();
      this.processing = false;
      this.currentTask = null;
      this.processNext();
      return;
    }

    // Continue loop
    if (typeof requestAnimationFrame !== 'undefined') {
      this.rafId = requestAnimationFrame(this.boundLoop);
    } else {
      this.rafId = setTimeout(() => this.boundLoop(now()), 16) as unknown as number;
    }
  }

  /**
   * Pause the queue
   */
  pause(): void {
    this.paused = true;
    if (this.currentTask?.animation) {
      if (this.currentTask.animation instanceof Animation) {
        this.currentTask.animation.pause();
      } else if (this.currentTask.animation instanceof Tween) {
        this.currentTask.animation.pause();
      }
    }
  }

  /**
   * Resume the queue
   */
  resume(): void {
    this.paused = false;
    if (this.currentTask?.animation) {
      if (this.currentTask.animation instanceof Animation) {
        this.currentTask.animation.start();
      } else if (this.currentTask.animation instanceof Tween) {
        this.currentTask.animation.start();
      }
    }
    this.startLoop();
  }

  /**
   * Cancel all pending animations
   */
  cancel(): void {
    // Clear delay timeout if active
    if (this.delayTimeoutId) {
      clearTimeout(this.delayTimeoutId);
      this.delayTimeoutId = 0;
    }

    // Cancel current animation if any
    if (this.currentTask) {
      if (this.currentTask.animation) {
        if (this.currentTask.animation instanceof Animation) {
          this.currentTask.animation.cancel();
        } else if (this.currentTask.animation instanceof Tween) {
          this.currentTask.animation.cancel();
        }
      }
      this.currentTask.reject(new Error('Animation cancelled'));
    }

    // Reject all queued tasks
    for (const task of this.queue) {
      task.reject(new Error('Animation cancelled'));
    }

    this.queue = [];
    this.currentTask = null;
    this.processing = false;

    if (this.rafId) {
      if (typeof cancelAnimationFrame !== 'undefined') {
        cancelAnimationFrame(this.rafId);
      } else {
        clearTimeout(this.rafId);
      }
      this.rafId = 0;
    }
  }

  /**
   * Clear the queue (without cancelling current animation)
   */
  clear(): void {
    for (const task of this.queue) {
      task.reject(new Error('Queue cleared'));
    }
    this.queue = [];
  }

  /**
   * Get the number of pending tasks
   */
  get length(): number {
    return this.queue.length + (this.currentTask ? 1 : 0);
  }

  /**
   * Check if the queue is currently processing
   */
  get isProcessing(): boolean {
    return this.processing;
  }

  /**
   * Check if the queue is paused
   */
  get isPaused(): boolean {
    return this.paused;
  }
}
