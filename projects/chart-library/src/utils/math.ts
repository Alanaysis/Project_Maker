/**
 * 数学工具函数
 */

/**
 * 线性插值
 */
export function lerp(a: number, b: number, t: number): number {
  return a + (b - a) * t;
}

/**
 * 将值限制在范围内
 */
export function clamp(value: number, min: number, max: number): number {
  return Math.min(Math.max(value, min), max);
}

/**
 * 计算数组的最小最大值
 */
export function getMinMax(data: number[]): { min: number; max: number } {
  if (data.length === 0) {
    return { min: 0, max: 0 };
  }

  let min = Infinity;
  let max = -Infinity;

  for (const value of data) {
    if (value < min) min = value;
    if (value > max) max = value;
  }

  return { min, max };
}

/**
 * 计算优雅的刻度值
 */
export function calculateNiceTicks(min: number, max: number, targetCount: number = 5): number[] {
  if (min === max) {
    return [min];
  }

  const range = max - min;
  const roughStep = range / targetCount;
  const magnitude = Math.pow(10, Math.floor(Math.log10(roughStep)));
  const residual = roughStep / magnitude;

  let niceStep: number;
  if (residual <= 1.5) niceStep = magnitude;
  else if (residual <= 3) niceStep = 2 * magnitude;
  else if (residual <= 7) niceStep = 5 * magnitude;
  else niceStep = 10 * magnitude;

  const niceMin = Math.floor(min / niceStep) * niceStep;
  const niceMax = Math.ceil(max / niceStep) * niceStep;

  const ticks: number[] = [];
  for (let tick = niceMin; tick <= niceMax + niceStep * 0.5; tick += niceStep) {
    ticks.push(parseFloat(tick.toPrecision(12)));
  }

  return ticks;
}

/**
 * 计算饼图角度
 */
export function calculatePieAngles(values: number[]): { start: number; end: number }[] {
  const total = values.reduce((sum, val) => sum + val, 0);
  if (total === 0) {
    return values.map(() => ({ start: 0, end: 0 }));
  }

  const angles: { start: number; end: number }[] = [];
  let currentAngle = -Math.PI / 2;

  for (const value of values) {
    const sliceAngle = (value / total) * Math.PI * 2;
    angles.push({
      start: currentAngle,
      end: currentAngle + sliceAngle,
    });
    currentAngle += sliceAngle;
  }

  return angles;
}

/**
 * 计算点到圆心的距离
 */
export function distance(x1: number, y1: number, x2: number, y2: number): number {
  return Math.sqrt(Math.pow(x2 - x1, 2) + Math.pow(y2 - y1, 2));
}

/**
 * 判断点是否在矩形内
 */
export function isPointInRect(
  px: number, py: number,
  rx: number, ry: number, rw: number, rh: number
): boolean {
  return px >= rx && px <= rx + rw && py >= ry && py <= ry + rh;
}

/**
 * 判断点是否在圆弧内
 */
export function isPointInArc(
  px: number, py: number,
  cx: number, cy: number, radius: number,
  startAngle: number, endAngle: number
): boolean {
  const dist = distance(px, py, cx, cy);
  if (dist > radius) return false;

  let angle = Math.atan2(py - cy, px - cx);
  if (angle < -Math.PI / 2) {
    angle += Math.PI * 2;
  }

  return angle >= startAngle && angle <= endAngle;
}

/**
 * 格式化数字
 */
export function formatNumber(value: number, decimals: number = 0): string {
  if (Math.abs(value) >= 1000000) {
    return (value / 1000000).toFixed(1) + 'M';
  }
  if (Math.abs(value) >= 1000) {
    return (value / 1000).toFixed(1) + 'K';
  }
  return value.toFixed(decimals);
}
