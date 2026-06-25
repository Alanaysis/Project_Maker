/**
 * Utility Functions
 *
 * Helper functions for animation interpolation, color parsing,
 * style application, and DOM manipulation.
 */

/**
 * Linear interpolation between two values
 */
export function lerp(start: number, end: number, t: number): number {
  return start + (end - start) * t;
}

/**
 * Clamp a value between min and max
 */
export function clamp(value: number, min: number, max: number): number {
  return Math.min(Math.max(value, min), max);
}

/**
 * Map a value from one range to another
 */
export function mapRange(
  value: number,
  inMin: number,
  inMax: number,
  outMin: number,
  outMax: number
): number {
  return outMin + ((value - inMin) * (outMax - outMin)) / (inMax - inMin);
}

/**
 * Parse a CSS numeric value (e.g., "100px" -> { value: 100, unit: "px" })
 */
export function parseNumericValue(value: string | number): {
  value: number;
  unit: string;
} {
  if (typeof value === 'number') {
    return { value, unit: '' };
  }
  const match = String(value).match(/^(-?[\d.]+)(.*)$/);
  if (match) {
    return { value: parseFloat(match[1]), unit: match[2] || '' };
  }
  return { value: 0, unit: '' };
}

/**
 * Interpolate between two CSS numeric values
 */
export function interpolateNumeric(
  start: string | number,
  end: string | number,
  t: number
): string {
  const s = parseNumericValue(start);
  const e = parseNumericValue(end);
  const result = lerp(s.value, e.value, t);

  if (s.unit || e.unit) {
    return `${result}${s.unit || e.unit}`;
  }
  return String(result);
}

/** RGB color representation */
interface RGBColor {
  r: number;
  g: number;
  b: number;
  a: number;
}

/**
 * Parse a color string to RGB values
 * Supports: hex (#rgb, #rrggbb, #rrggbbaa), rgb(), rgba()
 */
export function parseColor(color: string): RGBColor {
  // Hex format
  const hexMatch = color.match(/^#([0-9a-f]{3,8})$/i);
  if (hexMatch) {
    let hex = hexMatch[1];
    if (hex.length === 3) {
      hex = hex[0] + hex[0] + hex[1] + hex[1] + hex[2] + hex[2];
    }
    if (hex.length === 6) {
      hex += 'ff';
    }
    return {
      r: parseInt(hex.slice(0, 2), 16),
      g: parseInt(hex.slice(2, 4), 16),
      b: parseInt(hex.slice(4, 6), 16),
      a: parseInt(hex.slice(6, 8), 16) / 255,
    };
  }

  // rgb/rgba format
  const rgbMatch = color.match(
    /^rgba?\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*(?:,\s*([\d.]+))?\s*\)$/
  );
  if (rgbMatch) {
    return {
      r: parseInt(rgbMatch[1]),
      g: parseInt(rgbMatch[2]),
      b: parseInt(rgbMatch[3]),
      a: rgbMatch[4] !== undefined ? parseFloat(rgbMatch[4]) : 1,
    };
  }

  // Default to black
  return { r: 0, g: 0, b: 0, a: 1 };
}

/**
 * Interpolate between two colors
 */
export function interpolateColor(start: string, end: string, t: number): string {
  const s = parseColor(start);
  const e = parseColor(end);

  const r = Math.round(lerp(s.r, e.r, t));
  const g = Math.round(lerp(s.g, e.g, t));
  const b = Math.round(lerp(s.b, e.b, t));
  const a = lerp(s.a, e.a, t);

  if (a < 1) {
    return `rgba(${r}, ${g}, ${b}, ${a.toFixed(2)})`;
  }
  return `rgb(${r}, ${g}, ${b})`;
}

/**
 * Check if a value is a color string
 */
export function isColor(value: string): boolean {
  return (
    /^#([0-9a-f]{3,8})$/i.test(value) ||
    /^rgba?\(/.test(value)
  );
}

/**
 * Interpolate between two style values
 * Automatically detects numeric, color, or other values
 */
export function interpolateStyle(
  start: string | number,
  end: string | number,
  t: number
): string | number {
  // If both are numbers, simple lerp
  if (typeof start === 'number' && typeof end === 'number') {
    return lerp(start, end, t);
  }

  const startStr = String(start);
  const endStr = String(end);

  // Color interpolation
  if (isColor(startStr) && isColor(endStr)) {
    return interpolateColor(startStr, endStr, t);
  }

  // Numeric with units
  const startNum = parseNumericValue(startStr);
  const endNum = parseNumericValue(endStr);
  if (startNum.unit || endNum.unit) {
    return interpolateNumeric(startStr, endStr, t);
  }

  // Try numeric parse
  if (!isNaN(Number(startStr)) && !isNaN(Number(endStr))) {
    return lerp(Number(startStr), Number(endStr), t);
  }

  // Can't interpolate, snap at midpoint
  return t < 0.5 ? startStr : endStr;
}

/**
 * Apply styles to an element
 */
export function applyStyles(
  element: HTMLElement,
  styles: Record<string, string | number>
): void {
  for (const [key, value] of Object.entries(styles)) {
    if (key in element.style) {
      (element.style as any)[key] = typeof value === 'number' ? `${value}` : value;
    }
  }
}

/**
 * Generate a unique ID
 */
export function generateId(): string {
  return `anim_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
}

/**
 * High-resolution timestamp
 */
export function now(): number {
  if (typeof performance !== 'undefined' && performance.now) {
    return performance.now();
  }
  return Date.now();
}

/**
 * requestAnimationFrame polyfill/wrapper
 * Returns a handle that can be passed to cancelAnimationFrame
 */
export function requestAnimationFramePolyfill(callback: (time: number) => void): number {
  if (typeof requestAnimationFrame !== 'undefined') {
    return requestAnimationFrame(callback);
  }
  // Fallback for Node.js environment (tests)
  return setTimeout(() => callback(now()), 16) as unknown as number;
}

/**
 * cancelAnimationFrame polyfill/wrapper
 */
export function cancelAnimationFramePolyfill(handle: number): void {
  if (typeof cancelAnimationFrame !== 'undefined') {
    cancelAnimationFrame(handle);
  } else {
    clearTimeout(handle);
  }
}
