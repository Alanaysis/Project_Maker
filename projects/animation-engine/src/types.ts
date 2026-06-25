/**
 * Animation Engine Type Definitions
 *
 * Core types for the animation engine including easing functions,
 * animation configurations, and state management.
 */

/** Easing function signature: takes progress (0-1), returns eased value */
export type EasingFunction = (t: number) => number;

/** Animation playback state */
export enum AnimationState {
  IDLE = 'idle',
  RUNNING = 'running',
  PAUSED = 'paused',
  COMPLETED = 'completed',
  CANCELLED = 'cancelled'
}

/** Animation direction */
export enum AnimationDirection {
  NORMAL = 'normal',
  REVERSE = 'reverse',
  ALTERNATE = 'alternate',
  ALTERNATE_REVERSE = 'alternate_reverse'
}

/** Fill mode for when animation is not running */
export enum FillMode {
  NONE = 'none',
  FORWARDS = 'forwards',
  BACKWARDS = 'backwards',
  BOTH = 'both'
}

/** Keyframe definition */
export interface Keyframe {
  /** Progress value (0-1) */
  offset: number;
  /** CSS property values at this point */
  styles: Record<string, string | number>;
}

/** Animation configuration options */
export interface AnimationConfig {
  /** Target element or selector */
  target: HTMLElement | string;
  /** Keyframes defining the animation */
  keyframes: Keyframe[];
  /** Duration in milliseconds */
  duration: number;
  /** Delay before animation starts (ms) */
  delay?: number;
  /** Easing function or name */
  easing?: EasingFunction | string;
  /** Number of iterations (Infinity for infinite) */
  iterations?: number;
  /** Animation direction */
  direction?: AnimationDirection;
  /** Fill mode */
  fill?: FillMode;
  /** Callback when animation starts */
  onStart?: () => void;
  /** Callback on each animation frame */
  onUpdate?: (progress: number) => void;
  /** Callback when animation completes */
  onComplete?: () => void;
  /** Callback when animation is cancelled */
  onCancel?: () => void;
}

/** Tween configuration for simple property animation */
export interface TweenConfig<T extends Record<string, number>> {
  /** Starting values */
  from: T;
  /** Target values */
  to: T;
  /** Duration in milliseconds */
  duration: number;
  /** Delay before starting (ms) */
  delay?: number;
  /** Easing function or name */
  easing?: EasingFunction | string;
  /** Number of iterations */
  iterations?: number;
  /** Update callback with current values */
  onUpdate?: (values: T) => void;
  /** Completion callback */
  onComplete?: () => void;
}

/** Animation queue item */
export interface QueueItem {
  /** Unique identifier */
  id: string;
  /** Animation or tween config */
  config: AnimationConfig | TweenConfig<any>;
  /** Type of animation */
  type: 'keyframe' | 'tween';
  /** Promise resolver */
  resolve: () => void;
  /** Promise rejector */
  reject: (error: Error) => void;
}

/** Timeline animation entry */
export interface TimelineEntry {
  /** Animation start time relative to timeline */
  startTime: number;
  /** Animation duration */
  duration: number;
  /** The animation instance */
  animation: AnimationConfig;
}

/** Performance metrics */
export interface PerformanceMetrics {
  /** Frames per second */
  fps: number;
  /** Number of active animations */
  activeAnimations: number;
  /** Total frames rendered */
  totalFrames: number;
  /** Average frame time in ms */
  averageFrameTime: number;
}
