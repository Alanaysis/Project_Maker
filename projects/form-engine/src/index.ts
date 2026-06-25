/**
 * 表单引擎 - 入口文件
 *
 * 导出所有公共 API
 */

// 核心类
export { FormEngine } from './form-engine';
export type { SubmitHandler, StateChangeCallback } from './form-engine';
export { FormRenderer } from './renderer';

// 验证器
export { validateField, validateForm, rules } from './validator';
export type { ValidationResult } from './validator';

// 类型
export type {
  FieldType,
  FieldOption,
  ValidatorType,
  ValidationRule,
  FieldSchema,
  FormSchema,
  FieldError,
  FieldState,
  FormState,
  RenderContext,
  FormHandlers,
  RenderFormat,
  RenderResult
} from './types';
