/**
 * 拖拽系统核心类型定义
 *
 * 定义了拖拽系统中使用的所有接口和类型
 */

/**
 * 拖拽事件类型
 */
export type DragEventType =
  | 'dragstart'   // 拖拽开始
  | 'dragmove'    // 拖拽移动
  | 'dragend'     // 拖拽结束
  | 'dragenter'   // 进入目标区域
  | 'dragleave'   // 离开目标区域
  | 'drop';       // 放下

/**
 * 坐标位置
 */
export interface Position {
  x: number;
  y: number;
}

/**
 * 尺寸
 */
export interface Size {
  width: number;
  height: number;
}

/**
 * 矩形区域
 */
export interface Rect {
  x: number;
  y: number;
  width: number;
  height: number;
}

/**
 * 拖拽事件数据
 */
export interface DragEventData {
  /** 拖拽元素 */
  element: HTMLElement;
  /** 鼠标位置 */
  position: Position;
  /** 拖拽偏移量 */
  offset: Position;
  /** 拖拽开始位置 */
  startPosition: Position;
  /** 拖拽预览元素 */
  preview?: HTMLElement;
  /** 附加数据 */
  data?: unknown;
  /** 事件类型 */
  type: DragEventType;
}

/**
 * 拖拽配置选项
 */
export interface DragOptions {
  /** 拖拽手柄选择器 */
  handle?: string;
  /** 拖拽数据 */
  data?: unknown;
  /** 是否启用拖拽预览 */
  enablePreview?: boolean;
  /** 预览元素克隆深度 */
  previewCloneDeep?: boolean;
  /** 自定义预览元素创建函数 */
  createPreview?: (element: HTMLElement) => HTMLElement;
  /** 拖拽开始回调 */
  onDragStart?: (event: DragEventData) => void;
  /** 拖拽移动回调 */
  onDragMove?: (event: DragEventData) => void;
  /** 拖拽结束回调 */
  onDragEnd?: (event: DragEventData) => void;
  /** 拖拽限制容器 */
  constrainTo?: HTMLElement;
  /** 是否自动滚动 */
  autoScroll?: boolean;
  /** 自动滚动速度 */
  autoScrollSpeed?: number;
  /** 拖拽延迟（毫秒） */
  delay?: number;
  /** 拖拽距离阈值 */
  distance?: number;
}

/**
 * 拖放目标配置选项
 */
export interface DropOptions {
  /** 接受的拖拽类型 */
  accept?: string;
  /** 接受的元素选择器 */
  acceptSelector?: string;
  /** 高亮样式类名 */
  activeClass?: string;
  /** 放下回调 */
  onDrop?: (event: DragEventData) => void;
  /** 进入目标回调 */
  onDragEnter?: (event: DragEventData) => void;
  /** 离开目标回调 */
  onDragLeave?: (event: DragEventData) => void;
  /** 拖拽悬停回调 */
  onDragOver?: (event: DragEventData) => void;
}

/**
 * 排序配置选项
 */
export interface SortableOptions extends DragOptions {
  /** 排序容器 */
  container: HTMLElement;
  /** 排序项选择器 */
  itemSelector: string;
  /** 拖拽占位符 */
  placeholder?: HTMLElement;
  /** 占位符类名 */
  placeholderClass?: string;
  /** 动画持续时间（毫秒） */
  animation?: number;
  /** 排序结束回调 */
  onSortEnd?: (data: SortEventData) => void;
  /** 排序变化回调 */
  onSortChange?: (data: SortEventData) => void;
  /** 是否禁用排序 */
  disabled?: boolean;
  /** 禁用项选择器 */
  disabledSelector?: string;
  /** 排序方向 */
  direction?: 'vertical' | 'horizontal' | 'auto';
  /** 是否允许跨容器排序 */
  group?: string;
  /** 跨容器排序回调 */
  onGroupChange?: (data: GroupSortEventData) => void;
}

/**
 * 排序事件数据
 */
export interface SortEventData {
  /** 排序元素 */
  element: HTMLElement;
  /** 旧索引 */
  oldIndex: number;
  /** 新索引 */
  newIndex: number;
  /** 排序容器 */
  container: HTMLElement;
  /** 排序项列表 */
  items: HTMLElement[];
}

/**
 * 跨容器排序事件数据
 */
export interface GroupSortEventData extends SortEventData {
  /** 源容器 */
  fromContainer: HTMLElement;
  /** 目标容器 */
  toContainer: HTMLElement;
}

/**
 * 文件上传配置选项
 */
export interface FileUploadOptions {
  /** 上传区域元素 */
  dropZone: HTMLElement;
  /** 接受的文件类型 */
  accept?: string[];
  /** 最大文件大小（字节） */
  maxSize?: number;
  /** 最大文件数量 */
  maxFiles?: number;
  /** 是否支持多文件 */
  multiple?: boolean;
  /** 高亮样式类名 */
  activeClass?: string;
  /** 文件添加回调 */
  onFileAdd?: (file: File) => void;
  /** 文件移除回调 */
  onFileRemove?: (file: File) => void;
  /** 上传进度回调 */
  onProgress?: (progress: UploadProgress) => void;
  /** 上传完成回调 */
  onComplete?: (result: UploadResult) => void;
  /** 上传错误回调 */
  onError?: (error: UploadError) => void;
  /** 文件验证回调 */
  onValidate?: (file: File) => boolean | string;
  /** 是否自动生成预览 */
  autoPreview?: boolean;
  /** 预览容器 */
  previewContainer?: HTMLElement;
}

/**
 * 上传进度
 */
export interface UploadProgress {
  /** 已上传字节数 */
  loaded: number;
  /** 总字节数 */
  total: number;
  /** 进度百分比 */
  percent: number;
  /** 对应的文件 */
  file: File;
}

/**
 * 上传结果
 */
export interface UploadResult {
  /** 成功上传的文件 */
  success: File[];
  /** 上传失败的文件 */
  failed: UploadError[];
  /** 总耗时（毫秒） */
  duration: number;
}

/**
 * 上传错误
 */
export interface UploadError {
  /** 文件 */
  file: File;
  /** 错误信息 */
  message: string;
  /** 错误代码 */
  code: ErrorCode;
}

/**
 * 错误代码
 */
export enum ErrorCode {
  FILE_TOO_LARGE = 'FILE_TOO_LARGE',
  FILE_TYPE_NOT_ACCEPTED = 'FILE_TYPE_NOT_ACCEPTED',
  TOO_MANY_FILES = 'TOO_MANY_FILES',
  UPLOAD_FAILED = 'UPLOAD_FAILED',
  VALIDATION_FAILED = 'VALIDATION_FAILED',
}

/**
 * 拖拽状态
 */
export enum DragState {
  IDLE = 'idle',
  PENDING = 'pending',
  DRAGGING = 'dragging',
}

/**
 * 事件处理器类型
 */
export type EventHandler<T = unknown> = (data: T) => void;

/**
 * 事件监听器移除函数
 */
export type RemoveEventListener = () => void;
