/**
 * 拖拽系统主入口
 *
 * 导出所有拖拽相关的类和类型
 */

// 核心类型
export * from './types';

// 工具函数
export {
  getElementRect,
  getElementCenter,
  getDistance,
  isPointInRect,
  getOverlapArea,
  cloneElement,
  setStyles,
  addClass,
  removeClass,
  toggleClass,
  generateId,
  throttle,
  debounce,
  getScrollParent,
  autoScroll,
  validateFileType,
  validateFileSize,
  formatFileSize,
  createFilePreview,
  EventBus,
} from './utils';

// 核心模块
export { DragManager } from './drag-manager';
export { Sortable } from './sortable';
export { FileUpload } from './file-upload';
