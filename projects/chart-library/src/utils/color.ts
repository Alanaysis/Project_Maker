/**
 * 颜色工具函数
 */

/**
 * 默认调色板
 */
export const DEFAULT_COLORS = [
  '#4e79a7', '#f28e2b', '#e15759', '#76b7b2',
  '#59a14f', '#edc948', '#b07aa1', '#ff9da7',
  '#9c755f', '#bab0ac',
];

/**
 * 解析颜色字符串为 RGBA 对象
 */
export function parseColor(color: string): { r: number; g: number; b: number; a: number } {
  // 处理十六进制颜色
  if (color.startsWith('#')) {
    const hex = color.slice(1);
    let r: number, g: number, b: number;

    if (hex.length === 3) {
      r = parseInt(hex[0] + hex[0], 16);
      g = parseInt(hex[1] + hex[1], 16);
      b = parseInt(hex[2] + hex[2], 16);
    } else {
      r = parseInt(hex.slice(0, 2), 16);
      g = parseInt(hex.slice(2, 4), 16);
      b = parseInt(hex.slice(4, 6), 16);
    }

    return { r, g, b, a: 1 };
  }

  // 处理 rgb/rgba 颜色
  const match = color.match(/rgba?\((\d+),\s*(\d+),\s*(\d+)(?:,\s*([\d.]+))?\)/);
  if (match) {
    return {
      r: parseInt(match[1]),
      g: parseInt(match[2]),
      b: parseInt(match[3]),
      a: match[4] ? parseFloat(match[4]) : 1,
    };
  }

  // 默认返回黑色
  return { r: 0, g: 0, b: 0, a: 1 };
}

/**
 * 转换为 RGBA 字符串
 */
export function toRGBA(r: number, g: number, b: number, a: number = 1): string {
  return `rgba(${r}, ${g}, ${b}, ${a})`;
}

/**
 * 调整颜色透明度
 */
export function withAlpha(color: string, alpha: number): string {
  const { r, g, b } = parseColor(color);
  return toRGBA(r, g, b, alpha);
}

/**
 * 颜色变亮
 */
export function lighten(color: string, amount: number): string {
  const { r, g, b, a } = parseColor(color);
  const newR = Math.min(255, r + amount);
  const newG = Math.min(255, g + amount);
  const newB = Math.min(255, b + amount);
  return toRGBA(newR, newG, newB, a);
}

/**
 * 颜色变暗
 */
export function darken(color: string, amount: number): string {
  const { r, g, b, a } = parseColor(color);
  const newR = Math.max(0, r - amount);
  const newG = Math.max(0, g - amount);
  const newB = Math.max(0, b - amount);
  return toRGBA(newR, newG, newB, a);
}

/**
 * 生成渐变色
 */
export function generateGradientColors(startColor: string, endColor: string, steps: number): string[] {
  const start = parseColor(startColor);
  const end = parseColor(endColor);

  const colors: string[] = [];
  for (let i = 0; i < steps; i++) {
    const t = i / (steps - 1);
    const r = Math.round(start.r + (end.r - start.r) * t);
    const g = Math.round(start.g + (end.g - start.g) * t);
    const b = Math.round(start.b + (end.b - start.b) * t);
    colors.push(toRGBA(r, g, b));
  }

  return colors;
}

/**
 * 获取对比色（黑色或白色）
 */
export function getContrastColor(color: string): string {
  const { r, g, b } = parseColor(color);
  const luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255;
  return luminance > 0.5 ? '#000000' : '#ffffff';
}
