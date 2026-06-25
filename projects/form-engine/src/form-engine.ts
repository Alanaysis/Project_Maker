/**
 * 表单引擎核心
 *
 * 管理表单的生命周期：
 * 初始化 → 用户输入 → 验证 → 提交
 *
 * 核心职责：
 * 1. 管理表单状态（values, errors, touched, dirty）
 * 2. 处理字段变更
 * 3. 执行验证
 * 4. 处理提交
 */

import {
  FormSchema,
  FormState,
  FieldSchema,
  FieldError,
  FieldState,
  FormHandlers
} from './types';
import { validateField, validateForm, ValidationResult } from './validator';

/** 提交回调类型 */
export type SubmitHandler = (values: Record<string, any>) => void | Promise<void>;

/** 状态变更回调 */
export type StateChangeCallback = (state: FormState) => void;

/**
 * FormEngine - 表单引擎核心类
 *
 * 使用示例：
 * ```ts
 * const engine = new FormEngine(schema);
 * engine.onSubmit((values) => console.log(values));
 * engine.setValue('username', 'hello');
 * engine.submit();
 * ```
 */
export class FormEngine {
  private schema: FormSchema;
  private state: FormState;
  private submitHandlers: SubmitHandler[] = [];
  private stateChangeCallbacks: StateChangeCallback[] = [];

  constructor(schema: FormSchema) {
    this.schema = schema;
    this.state = this.createInitialState(schema);
  }

  /**
   * 根据 Schema 创建初始状态
   */
  private createInitialState(schema: FormSchema): FormState {
    const values: Record<string, any> = {};
    const errors: Record<string, FieldError[]> = {};
    const touched: Record<string, boolean> = {};
    const dirty: Record<string, boolean> = {};

    for (const field of schema.fields) {
      values[field.name] = field.defaultValue ?? this.getDefaultValue(field);
      errors[field.name] = [];
      touched[field.name] = false;
      dirty[field.name] = false;
    }

    return {
      values,
      errors,
      touched,
      dirty,
      valid: true,
      submitting: false,
      submitted: false
    };
  }

  /**
   * 根据字段类型获取默认值
   */
  private getDefaultValue(field: FieldSchema): any {
    switch (field.type) {
      case 'checkbox':
        return false;
      case 'number':
        return 0;
      case 'select':
        return field.options && field.options.length > 0 ? field.options[0].value : '';
      default:
        return '';
    }
  }

  /**
   * 触发状态变更通知
   */
  private notifyStateChange(): void {
    for (const callback of this.stateChangeCallbacks) {
      callback(this.state);
    }
  }

  // ==================== 公共 API ====================

  /**
   * 获取当前表单 Schema
   */
  getSchema(): FormSchema {
    return this.schema;
  }

  /**
   * 获取当前表单状态（只读副本）
   */
  getState(): FormState {
    return { ...this.state };
  }

  /**
   * 获取单个字段的值
   */
  getValue(name: string): any {
    return this.state.values[name];
  }

  /**
   * 获取所有表单值
   */
  getValues(): Record<string, any> {
    return { ...this.state.values };
  }

  /**
   * 设置字段值
   *
   * @param name - 字段名
   * @param value - 字段值
   * @param touch - 是否标记为已触摸（默认 true）
   */
  setValue(name: string, value: any, touch: boolean = true): void {
    const field = this.schema.fields.find(f => f.name === name);
    if (!field) {
      console.warn(`Field "${name}" not found in schema`);
      return;
    }

    const oldValue = this.state.values[name];
    this.state.values[name] = value;

    if (touch) {
      this.state.touched[name] = true;
    }

    // 标记为脏（值被修改过）
    if (value !== oldValue) {
      this.state.dirty[name] = true;
    }

    // 验证字段
    const result = validateField(value, field.validation || [], this.state.values);
    this.state.errors[name] = result.errors;

    // 更新表单整体有效性
    this.state.valid = Object.values(this.state.errors).every(
      errs => errs.length === 0
    );

    this.notifyStateChange();
  }

  /**
   * 设置字段为已触摸状态
   */
  setTouched(name: string): void {
    this.state.touched[name] = true;
    this.notifyStateChange();
  }

  /**
   * 获取字段状态
   */
  getFieldState(name: string): FieldState | null {
    const field = this.schema.fields.find(f => f.name === name);
    if (!field) return null;

    return {
      value: this.state.values[name],
      touched: this.state.touched[name],
      dirty: this.state.dirty[name],
      errors: this.state.errors[name],
      valid: this.state.errors[name].length === 0
    };
  }

  /**
   * 获取字段可见性（考虑 dependsOn）
   */
  isFieldVisible(field: FieldSchema): boolean {
    if (field.hidden) return false;
    if (!field.dependsOn) return true;

    const dependentValue = this.state.values[field.dependsOn.field];
    return dependentValue === field.dependsOn.value;
  }

  /**
   * 获取可见字段列表
   */
  getVisibleFields(): FieldSchema[] {
    return this.schema.fields.filter(f => this.isFieldVisible(f));
  }

  /**
   * 验证整个表单
   */
  validate(): boolean {
    const visibleFields = this.getVisibleFields();
    const results = validateForm(this.state.values, visibleFields);

    for (const [name, result] of Object.entries(results)) {
      this.state.errors[name] = result.errors;
      this.state.touched[name] = true;
    }

    this.state.valid = Object.values(this.state.errors).every(
      errs => errs.length === 0
    );

    this.notifyStateChange();
    return this.state.valid;
  }

  /**
   * 提交表单
   */
  async submit(): Promise<boolean> {
    this.state.submitted = true;

    // 验证表单
    const isValid = this.validate();
    if (!isValid) {
      return false;
    }

    this.state.submitting = true;
    this.notifyStateChange();

    try {
      // 执行提交回调
      for (const handler of this.submitHandlers) {
        await handler(this.state.values);
      }
      return true;
    } catch (error) {
      console.error('Form submission error:', error);
      return false;
    } finally {
      this.state.submitting = false;
      this.notifyStateChange();
    }
  }

  /**
   * 重置表单
   */
  reset(): void {
    this.state = this.createInitialState(this.schema);
    this.notifyStateChange();
  }

  /**
   * 注册提交回调
   */
  onSubmit(handler: SubmitHandler): void {
    this.submitHandlers.push(handler);
  }

  /**
   * 注册状态变更回调
   */
  onStateChange(callback: StateChangeCallback): void {
    this.stateChangeCallbacks.push(callback);
  }

  /**
   * 获取表单处理器（用于渲染）
   */
  getHandlers(): FormHandlers {
    return {
      onChange: (name: string, value: any) => this.setValue(name, value),
      onBlur: (name: string) => this.setTouched(name),
      onSubmit: () => { this.submit(); },
      onReset: () => this.reset()
    };
  }
}
