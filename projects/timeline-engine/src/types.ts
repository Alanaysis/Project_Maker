/**
 * Timeline Engine - Type Definitions
 *
 * Core types for the timeline animation engine including easing functions,
 * keyframe definitions, timeline states, and animation configurations.
 */

/** Easing function: takes progress (0-1), returns eased progress (0-1) */
export type EasingFunction = (t: number) => number;

/** Timeline playback state */
export enum TimelineState {
  IDLE = 'idle',
  PLAYING = 'playing',
  PAUSED = 'paused',
  STOPPED = 'stopped',
  COMPLETED = 'completed',
}

/** Animation direction */
export enum AnimationDirection {
  NORMAL = 'normal',
  REVERSE = 'reverse',
}

/** Keyframe definition with time and value */
export interface KeyframeEntry {
  time: number;
  value: number;
}

/** Configuration for a keyframe animation */
export interface KeyframeConfig {
  name: string;
  property: string;
  keyframes: KeyframeEntry[];
  duration?: number;
  easing?: EasingFunction | string;
  delay?: number;
}

/** Animation clip: reusable set of keyframe animations */
export interface AnimationClipConfig {
  name: string;
  animations: KeyframeConfig[];
  duration: number;
}

/** Timeline options */
export interface TimelineOptions {
  duration?: number;
  fps?: number;
  loop?: boolean;
  autoplay?: boolean;
}

/** Animation handle for controlling a registered animation */
export interface AnimationHandle {
  name: string;
  property: string;
  remove(): void;
  updateKeyframes(keyframes: KeyframeEntry[]): void;
  updateEasing(easing: EasingFunction | string): void;
}

/** Event types for timeline events */
export type TimelineEvent = 'play' | 'pause' | 'stop' | 'complete' | 'frame';

/** Event listener callback */
export type TimelineEventListener = (data?: any) => void;

/** Computed timeline state */
export interface TimelineStateOutput {
  [property: string]: number;
}
