/**
 * Easing Functions Library
 *
 * Provides a comprehensive set of easing functions for animations.
 * Each function takes a progress value t (0-1) and returns an eased value.
 *
 * Categories:
 * - Linear: No easing
 * - Quad/Cubic/Quart/Quint: Polynomial easing
 * - Sine: Trigonometric easing
 * - Expo: Exponential easing
 * - Circ: Circular easing
 * - Elastic: Elastic easing
 * - Back: Overshooting easing
 * - Bounce: Bouncing easing
 */

import { EasingFunction } from './types';

// ============================================================
// Linear
// ============================================================

export const linear: EasingFunction = (t) => t;

// ============================================================
// Quadratic (t^2)
// ============================================================

export const easeInQuad: EasingFunction = (t) => t * t;

export const easeOutQuad: EasingFunction = (t) => t * (2 - t);

export const easeInOutQuad: EasingFunction = (t) =>
  t < 0.5 ? 2 * t * t : -1 + (4 - 2 * t) * t;

// ============================================================
// Cubic (t^3)
// ============================================================

export const easeInCubic: EasingFunction = (t) => t * t * t;

export const easeOutCubic: EasingFunction = (t) => (--t) * t * t + 1;

export const easeInOutCubic: EasingFunction = (t) =>
  t < 0.5 ? 4 * t * t * t : (t - 1) * (2 * t - 2) * (2 * t - 2) + 1;

// ============================================================
// Quartic (t^4)
// ============================================================

export const easeInQuart: EasingFunction = (t) => t * t * t * t;

export const easeOutQuart: EasingFunction = (t) => 1 - (--t) * t * t * t;

export const easeInOutQuart: EasingFunction = (t) =>
  t < 0.5 ? 8 * t * t * t * t : 1 - 8 * (--t) * t * t * t;

// ============================================================
// Quintic (t^5)
// ============================================================

export const easeInQuint: EasingFunction = (t) => t * t * t * t * t;

export const easeOutQuint: EasingFunction = (t) => 1 + (--t) * t * t * t * t;

export const easeInOutQuint: EasingFunction = (t) =>
  t < 0.5 ? 16 * t * t * t * t * t : 1 + 16 * (--t) * t * t * t * t;

// ============================================================
// Sine
// ============================================================

export const easeInSine: EasingFunction = (t) =>
  1 - Math.cos((t * Math.PI) / 2);

export const easeOutSine: EasingFunction = (t) =>
  Math.sin((t * Math.PI) / 2);

export const easeInOutSine: EasingFunction = (t) =>
  -(Math.cos(Math.PI * t) - 1) / 2;

// ============================================================
// Exponential
// ============================================================

export const easeInExpo: EasingFunction = (t) =>
  t === 0 ? 0 : Math.pow(2, 10 * (t - 1));

export const easeOutExpo: EasingFunction = (t) =>
  t === 1 ? 1 : 1 - Math.pow(2, -10 * t);

export const easeInOutExpo: EasingFunction = (t) => {
  if (t === 0) return 0;
  if (t === 1) return 1;
  if (t < 0.5) return Math.pow(2, 20 * t - 10) / 2;
  return (2 - Math.pow(2, -20 * t + 10)) / 2;
};

// ============================================================
// Circular
// ============================================================

export const easeInCirc: EasingFunction = (t) =>
  1 - Math.sqrt(1 - t * t);

export const easeOutCirc: EasingFunction = (t) =>
  Math.sqrt(1 - (--t) * t);

export const easeInOutCirc: EasingFunction = (t) =>
  t < 0.5
    ? (1 - Math.sqrt(1 - 4 * t * t)) / 2
    : (Math.sqrt(1 - (2 * t - 2) * (2 * t - 2)) + 1) / 2;

// ============================================================
// Elastic
// ============================================================

const ELASTIC_AMPLITUDE = 1;
const ELASTIC_PERIOD = 0.3;

export const easeInElastic: EasingFunction = (t) => {
  if (t === 0 || t === 1) return t;
  const p = ELASTIC_PERIOD;
  const s = p / 4;
  return -(
    ELASTIC_AMPLITUDE *
    Math.pow(2, 10 * (t - 1)) *
    Math.sin(((t - 1 - s) * (2 * Math.PI)) / p)
  );
};

export const easeOutElastic: EasingFunction = (t) => {
  if (t === 0 || t === 1) return t;
  const p = ELASTIC_PERIOD;
  const s = p / 4;
  return (
    ELASTIC_AMPLITUDE *
    Math.pow(2, -10 * t) *
    Math.sin(((t - s) * (2 * Math.PI)) / p) +
    1
  );
};

export const easeInOutElastic: EasingFunction = (t) => {
  if (t === 0 || t === 1) return t;
  const p = ELASTIC_PERIOD * 1.5;
  const s = p / 4;
  if (t < 0.5) {
    return (
      -0.5 *
      ELASTIC_AMPLITUDE *
      Math.pow(2, 20 * t - 10) *
      Math.sin(((20 * t - 11.125) * (2 * Math.PI)) / p)
    );
  }
  return (
    ELASTIC_AMPLITUDE *
    Math.pow(2, -20 * t + 10) *
    Math.sin(((20 * t - 11.125) * (2 * Math.PI)) / p) *
    0.5 +
    1
  );
};

// ============================================================
// Back
// ============================================================

const BACK_OVERSHOOT = 1.70158;

export const easeInBack: EasingFunction = (t) =>
  t * t * ((BACK_OVERSHOOT + 1) * t - BACK_OVERSHOOT);

export const easeOutBack: EasingFunction = (t) => {
  const s = BACK_OVERSHOOT;
  return (t -= 1) * t * ((s + 1) * t + s) + 1;
};

export const easeInOutBack: EasingFunction = (t) => {
  const s = BACK_OVERSHOOT * 1.525;
  if ((t *= 2) < 1) {
    return 0.5 * (t * t * ((s + 1) * t - s));
  }
  return 0.5 * ((t -= 2) * t * ((s + 1) * t + s) + 2);
};

// ============================================================
// Bounce
// ============================================================

const bounceOut: EasingFunction = (t) => {
  const n1 = 7.5625;
  const d1 = 2.75;

  if (t < 1 / d1) {
    return n1 * t * t;
  } else if (t < 2 / d1) {
    return n1 * (t -= 1.5 / d1) * t + 0.75;
  } else if (t < 2.5 / d1) {
    return n1 * (t -= 2.25 / d1) * t + 0.9375;
  } else {
    return n1 * (t -= 2.625 / d1) * t + 0.984375;
  }
};

export const easeOutBounce: EasingFunction = bounceOut;

export const easeInBounce: EasingFunction = (t) => 1 - bounceOut(1 - t);

export const easeInOutBounce: EasingFunction = (t) =>
  t < 0.5
    ? (1 - bounceOut(1 - 2 * t)) / 2
    : (1 + bounceOut(2 * t - 1)) / 2;

// ============================================================
// Easing Registry
// ============================================================

/** Map of all named easing functions */
const easingMap: Record<string, EasingFunction> = {
  'linear': linear,
  'ease-in-quad': easeInQuad,
  'ease-out-quad': easeOutQuad,
  'ease-in-out-quad': easeInOutQuad,
  'ease-in-cubic': easeInCubic,
  'ease-out-cubic': easeOutCubic,
  'ease-in-out-cubic': easeInOutCubic,
  'ease-in-quart': easeInQuart,
  'ease-out-quart': easeOutQuart,
  'ease-in-out-quart': easeInOutQuart,
  'ease-in-quint': easeInQuint,
  'ease-out-quint': easeOutQuint,
  'ease-in-out-quint': easeInOutQuint,
  'ease-in-sine': easeInSine,
  'ease-out-sine': easeOutSine,
  'ease-in-out-sine': easeInOutSine,
  'ease-in-expo': easeInExpo,
  'ease-out-expo': easeOutExpo,
  'ease-in-out-expo': easeInOutExpo,
  'ease-in-circ': easeInCirc,
  'ease-out-circ': easeOutCirc,
  'ease-in-out-circ': easeInOutCirc,
  'ease-in-elastic': easeInElastic,
  'ease-out-elastic': easeOutElastic,
  'ease-in-out-elastic': easeInOutElastic,
  'ease-in-back': easeInBack,
  'ease-out-back': easeOutBack,
  'ease-in-out-back': easeInOutBack,
  'ease-in-bounce': easeInBounce,
  'ease-out-bounce': easeOutBounce,
  'ease-in-out-bounce': easeInOutBounce,
};

/**
 * Resolve an easing function by name or return the function directly
 */
export function resolveEasing(easing: EasingFunction | string | undefined): EasingFunction {
  if (easing === undefined) {
    return easeOutCubic;
  }
  if (typeof easing === 'function') {
    return easing;
  }
  const fn = easingMap[easing];
  if (!fn) {
    console.warn(`Unknown easing function: "${easing}", falling back to easeOutCubic`);
    return easeOutCubic;
  }
  return fn;
}

/**
 * Get list of all available easing function names
 */
export function getEasingNames(): string[] {
  return Object.keys(easingMap);
}

/**
 * Register a custom easing function
 */
export function registerEasing(name: string, fn: EasingFunction): void {
  easingMap[name] = fn;
}
