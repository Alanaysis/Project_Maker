/**
 * Timeline Engine
 *
 * A timeline/animation engine with keyframe-based animation,
 * easing functions, and timeline management.
 *
 * @example
 * ```typescript
 * import { Timeline, Keyframe, Easing } from '@timeline-engine/core';
 *
 * const timeline = new Timeline();
 *
 * timeline.addKeyframe({
 *   property: 'x',
 *   keyframes: [
 *     { time: 0, value: 0 },
 *     { time: 1, value: 100 },
 *   ],
 *   duration: 1000,
 *   easing: Easing.easeOutCubic,
 * });
 *
 * timeline.play();
 * timeline.seek(0.5);
 * console.log(timeline.getState());
 * ```
 */

// Core classes
export { Timeline } from './timeline';
export { TimelinePlayer } from './timeline_player';
export { Keyframe, KeyframeTrack } from './keyframe';
export { AnimationClip } from './animation_clip';

// Types
export {
  EasingFunction,
  TimelineState,
  AnimationDirection,
  KeyframeEntry,
  KeyframeConfig,
  AnimationClipConfig,
  TimelineOptions,
  AnimationHandle,
  TimelineEvent,
  TimelineEventListener,
  TimelineStateOutput,
} from './types';

// Easing functions
export {
  // Linear
  linear,
  // Quadratic
  easeInQuad,
  easeOutQuad,
  easeInOutQuad,
  // Cubic
  easeInCubic,
  easeOutCubic,
  easeInOutCubic,
  // Quartic
  easeInQuart,
  easeOutQuart,
  easeInOutQuart,
  // Quintic
  easeInQuint,
  easeOutQuint,
  easeInOutQuint,
  // Sine
  easeInSine,
  easeOutSine,
  easeInOutSine,
  // Exponential
  easeInExpo,
  easeOutExpo,
  easeInOutExpo,
  // Circular
  easeInCirc,
  easeOutCirc,
  easeInOutCirc,
  // Elastic
  easeInElastic,
  easeOutElastic,
  easeInOutElastic,
  // Back
  easeInBack,
  easeOutBack,
  easeInOutBack,
  // Bounce
  easeInBounce,
  easeOutBounce,
  easeInOutBounce,
  // Utilities
  resolveEasing,
  getEasingNames,
  registerEasing,
  clamp as clampEasing,
} from './easing';

// Utility
export { lerp, mapRange } from './utils';
