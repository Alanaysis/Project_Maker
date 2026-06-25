/**
 * 表单引擎核心类型定义
 *
 * 定义表单引擎中所有使用的类型接口
 */

// ==================== 字段类型 ====================

/** 支持的字段类型 */
export type FieldType =
  | 'text'
  | 'number'
  | 'email'
  | 'password'
  | 'textarea'
  | 'select'
  | 'checkbox'
  | 'radio'
  | 'date'
  | 'file';

/** 选项（用于 select/radio） */
export interface FieldOption {
  label: string;
  value: string | number;
  disabled?: boolean;
}

/** 验证规则类型 */
export type ValidatorType =
  | 'required'
  | 'minLength'
  | 'maxLength'
  | 'min'
  | 'max'
  | 'pattern'
  | 'email'
  | 'custom';

/** 单个验证规则 */
export interface ValidationRule {
  type: ValidatorType;
  value?: string | number | RegExp;
  message: string;
  validator?: (value: any, formData?: Record<string, any>) => boolean;
}

/** 字段定义 */
export interface FieldSchema {
  name: string;
  type: FieldType;
  label: string;
  placeholder?: string;
  defaultValue?: any;
  options?: FieldOption[];
  validation?: ValidationRule[];
  disabled?: boolean;
  hidden?: boolean;
  /** 字段依赖：当指定字段满足条件时才显示 */
  dependsOn?: {
    field: string;
    value: any;
  };
  /** 自定义 CSS 类名 */
  className?: string;
  /** 字段描述/帮助文本 */
  description?: string;
}

/** 表单 Schema 定义 */
export interface FormSchema {
  title: string;
  description?: string;
  fields: FieldSchema[];
  submitText?: string;
  resetText?: string;
}

// ==================== 表单状态 ====================

/** 字段错误信息 */
export interface FieldError {
  message: string;
  rule: ValidatorType;
}

/** 字段状态 */
export interface FieldState {
  value: any;
  touched: boolean;
  dirty: boolean;
  errors: FieldError[];
  valid: boolean;
}

/** 表单状态 */
export interface FormState {
  values: Record<string, any>;
  errors: Record<string, FieldError[]>;
  touched: Record<string, boolean>;
  dirty: Record<string, boolean>;
  valid: boolean;
  submitting: boolean;
  submitted: boolean;
}

// ==================== 渲染相关 ====================

/** 渲染上下文 */
export interface RenderContext {
  schema: FormSchema;
  state: FormState;
  handlers: FormHandlers;
}

/** 表单事件处理器 */
export interface FormHandlers {
  onChange: (name: string, value: any) => void;
  onBlur: (name: string) => void;
  onSubmit: () => void;
  onReset: () => void;
}

/** 渲染输出格式 */
export type RenderFormat = 'html' | 'json' | 'text';

/** 渲染结果 */
export interface RenderResult {
  format: RenderFormat;
  content: string;
}
