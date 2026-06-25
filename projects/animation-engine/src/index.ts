/**
 * Animation Engine
 *
 * A CSS/JS animation engine with easing functions, animation queue,
 * and performance optimization.
 *
 * @example
 * ```typescript
 * import { AnimationEngine, easeOutBounce } from 'animation-engine';
 *
 * const engine = new AnimationEngine();
 *
 * // Keyframe animation
 * engine.animate({
 *   target: '#box',
 *   keyframes: [
 *     { offset: 0, styles: { transform: 'translateX(0px)', opacity: 1 } },
 *     { offset: 1, styles: { transform: 'translateX(200px)', opacity: 0.5 } },
 *   ],
 *   duration: 1000,
 *   easing: easeOutBounce,
 *   iterations: 3,
 * });
 *
 * // Simple tween
 * engine.tween({
 *   from: { x: 0, y: 0 },
 *   to: { x: 200, y: 100 },
 *   duration: 500,
 *   onUpdate: (values) => console.log(values),
 * });
 *
 * // Animation queue
 * const queue = engine.queue('myQueue');
 * await queue.animate({ ... });
 * await queue.wait(500);
 * await queue.animate({ ... });
 * ```
 */

// Core classes
export { AnimationEngine, createEngine } from './engine';
export { Animation } from './animation';
export { Tween } from './tween';
export { AnimationQueue } from './queue';

// Types
export {
  EasingFunction,
  AnimationState,
  AnimationDirection,
  FillMode,
  Keyframe,
  AnimationConfig,
  TweenConfig,
  QueueItem,
  TimelineEntry,
  PerformanceMetrics,
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
} from './easing';

// Utility functions
export {
  lerp,
  clamp,
  mapRange,
  parseNumericValue,
  interpolateNumeric,
  parseColor,
  interpolateColor,
  interpolateStyle,
  applyStyles,
  generateId,
  now,
} from './utils';
