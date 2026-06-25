/**
 * 图表库入口文件
 */

export { LineChart } from './charts/LineChart';
export { BarChart } from './charts/BarChart';
export { PieChart } from './charts/PieChart';

export { Chart } from './core/Chart';
export type { ChartData, Dataset, ChartOptions, Padding } from './core/Chart';

export { CanvasRenderer } from './core/Canvas';
export type { CanvasOptions } from './core/Canvas';

export { LinearScale, CategoryScale } from './core/Scale';
export type { Scale } from './core/Scale';

export { EventManager } from './core/Event';
export type { ChartEvent, EventHandler } from './core/Event';

export * from './utils/math';
export * from './utils/color';
