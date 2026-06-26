/**
 * Utility Functions
 *
 * Helper functions for interpolation, mapping, and general math.
 */

/**
 * Linear interpolation between two values.
 */
export function lerp(start: number, end: number, t: number): number {
  return start + (end - start) * t;
}

/**
 * Map a value from one range to another.
 */
export function mapRange(
  value: number,
  inMin: number,
  inMax: number,
  outMin: number,
  outMax: number
): number {
  if (inMax === inMin) return outMin;
  return outMin + ((value - inMin) * (outMax - outMin)) / (inMax - inMin);
}

/**
 * Clamp a value between min and max.
 */
export function clamp(val: number, min: number = 0, max: number = 1): number {
  return Math.max(min, Math.min(max, val));
}

/**
 * Generate a unique ID.
 */
export function generateId(): string {
  return `tl_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
}

/**
 * Check if a value is within a range with tolerance.
 */
export function within(value: number, target: number, tolerance: number = 1e-6): boolean {
  return Math.abs(value - target) < tolerance;
}

/**
 * Smoothstep interpolation.
 */
export function smoothstep(edge0: number, edge1: number, x: number): number {
  const t = clamp((x - edge0) / (edge1 - edge0));
  return t * t * (3 - 2 * t);
}

/**
 * Smootherstep interpolation.
 */
export function smootherstep(edge0: number, edge1: number, x: number): number {
  const t = clamp((x - edge0) / (edge1 - edge0));
  return t * t * t * (t * (t * 6 - 15) + 10);
}
