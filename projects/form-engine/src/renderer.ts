/**
 * 表单渲染器
 *
 * 将表单 Schema 和状态渲染为 HTML 字符串
 *
 * 支持：
 * - 各种字段类型
 * - 错误信息显示
 * - 条件字段显示
 * - 自定义 CSS 类
 */

import {
  FormSchema,
  FormState,
  FieldSchema,
  FieldOption,
  RenderResult,
  RenderFormat
} from './types';

/**
 * HTML 转义
 */
function escapeHtml(str: string): string {
  return str
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

/**
 * 渲染器类
 *
 * 将 FormSchema + FormState 渲染为 HTML
 */
export class FormRenderer {
  /**
   * 渲染表单
   *
   * @param schema - 表单 Schema
   * @param state - 表单状态
   * @returns HTML 字符串
   */
  render(schema: FormSchema, state: FormState): RenderResult {
    const fieldsHtml = schema.fields
      .filter(field => !field.hidden)
      .map(field => this.renderField(field, state))
      .join('\n');

    const html = `<form class="form-engine" data-form-title="${escapeHtml(schema.title)}">
  <h2 class="form-title">${escapeHtml(schema.title)}</h2>
  ${schema.description ? `<p class="form-description">${escapeHtml(schema.description)}</p>` : ''}
  <div class="form-fields">
    ${fieldsHtml}
  </div>
  <div class="form-actions">
    <button type="submit" class="btn btn-submit">${escapeHtml(schema.submitText || '提交')}</button>
    <button type="reset" class="btn btn-reset">${escapeHtml(schema.resetText || '重置')}</button>
  </div>
</form>`;

    return {
      format: 'html',
      content: html
    };
  }

  /**
   * 渲染单个字段
   */
  private renderField(field: FieldSchema, state: FormState): string {
    const value = state.values[field.name];
    const errors = state.errors[field.name] || [];
    const touched = state.touched[field.name] || false;
    const hasErrors = touched && errors.length > 0;
    const errorClass = hasErrors ? ' field-error' : '';
    const className = field.className ? ` ${field.className}` : '';

    let fieldHtml: string;

    switch (field.type) {
      case 'text':
      case 'email':
      case 'password':
      case 'number':
      case 'date':
        fieldHtml = this.renderInput(field, value);
        break;
      case 'textarea':
        fieldHtml = this.renderTextarea(field, value);
        break;
      case 'select':
        fieldHtml = this.renderSelect(field, value);
        break;
      case 'checkbox':
        fieldHtml = this.renderCheckbox(field, value);
        break;
      case 'radio':
        fieldHtml = this.renderRadio(field, value);
        break;
      default:
        fieldHtml = this.renderInput(field, value);
    }

    const errorHtml = hasErrors
      ? `<div class="field-errors">${errors.map(e => `<span class="error-message">${escapeHtml(e.message)}</span>`).join('')}</div>`
      : '';

    const descriptionHtml = field.description
      ? `<span class="field-description">${escapeHtml(field.description)}</span>`
      : '';

    return `    <div class="form-field${errorClass}${className}" data-field-name="${escapeHtml(field.name)}">
      <label class="field-label" for="field-${escapeHtml(field.name)}">${escapeHtml(field.label)}</label>
      ${fieldHtml}
      ${descriptionHtml}
      ${errorHtml}
    </div>`;
  }

  /**
   * 渲染输入框
   */
  private renderInput(field: FieldSchema, value: any): string {
    const attrs = [
      `type="${field.type}"`,
      `id="field-${escapeHtml(field.name)}"`,
      `name="${escapeHtml(field.name)}"`,
      `value="${escapeHtml(String(value ?? ''))}"`
    ];

    if (field.placeholder) {
      attrs.push(`placeholder="${escapeHtml(field.placeholder)}"`);
    }
    if (field.disabled) {
      attrs.push('disabled');
    }

    return `      <input ${attrs.join(' ')} />`;
  }

  /**
   * 渲染文本区域
   */
  private renderTextarea(field: FieldSchema, value: any): string {
    const attrs = [
      `id="field-${escapeHtml(field.name)}"`,
      `name="${escapeHtml(field.name)}"`
    ];

    if (field.placeholder) {
      attrs.push(`placeholder="${escapeHtml(field.placeholder)}"`);
    }
    if (field.disabled) {
      attrs.push('disabled');
    }

    return `      <textarea ${attrs.join(' ')}>${escapeHtml(String(value ?? ''))}</textarea>`;
  }

  /**
   * 渲染下拉选择
   */
  private renderSelect(field: FieldSchema, value: any): string {
    const attrs = [
      `id="field-${escapeHtml(field.name)}"`,
      `name="${escapeHtml(field.name)}"`
    ];

    if (field.disabled) {
      attrs.push('disabled');
    }

    const options = (field.options || [])
      .map(opt => {
        const selected = opt.value === value ? ' selected' : '';
        const disabled = opt.disabled ? ' disabled' : '';
        return `        <option value="${escapeHtml(String(opt.value))}"${selected}${disabled}>${escapeHtml(opt.label)}</option>`;
      })
      .join('\n');

    return `      <select ${attrs.join(' ')}>
${options}
      </select>`;
  }

  /**
   * 渲染复选框
   */
  private renderCheckbox(field: FieldSchema, value: any): string {
    const checked = value ? ' checked' : '';
    const disabled = field.disabled ? ' disabled' : '';

    return `      <input type="checkbox" id="field-${escapeHtml(field.name)}" name="${escapeHtml(field.name)}" value="true"${checked}${disabled} />`;
  }

  /**
   * 渲染单选按钮组
   */
  private renderRadio(field: FieldSchema, value: any): string {
    const options = (field.options || [])
      .map(opt => {
        const checked = opt.value === value ? ' checked' : '';
        const disabled = opt.disabled || field.disabled ? ' disabled' : '';
        const id = `field-${escapeHtml(field.name)}-${escapeHtml(String(opt.value))}`;
        return `      <label class="radio-label">
        <input type="radio" name="${escapeHtml(field.name)}" value="${escapeHtml(String(opt.value))}" id="${id}"${checked}${disabled} />
        ${escapeHtml(opt.label)}
      </label>`;
      })
      .join('\n');

    return options;
  }

  /**
   * 渲染为纯文本格式
   */
  renderAsText(schema: FormSchema, state: FormState): RenderResult {
    const lines: string[] = [];
    lines.push(`=== ${schema.title} ===`);
    if (schema.description) {
      lines.push(schema.description);
    }
    lines.push('');

    for (const field of schema.fields) {
      if (field.hidden) continue;

      const value = state.values[field.name];
      const errors = state.errors[field.name] || [];
      const touched = state.touched[field.name] || false;

      lines.push(`${field.label}: ${value}`);
      if (field.description) {
        lines.push(`  (${field.description})`);
      }
      if (touched && errors.length > 0) {
        for (const error of errors) {
          lines.push(`  [ERROR] ${error.message}`);
        }
      }
    }

    return {
      format: 'text',
      content: lines.join('\n')
    };
  }

  /**
   * 渲染为 JSON 格式
   */
  renderAsJson(schema: FormSchema, state: FormState): RenderResult {
    const output = {
      title: schema.title,
      description: schema.description,
      fields: schema.fields
        .filter(f => !f.hidden)
        .map(field => ({
          name: field.name,
          label: field.label,
          type: field.type,
          value: state.values[field.name],
          errors: state.errors[field.name] || [],
          touched: state.touched[field.name] || false,
          valid: (state.errors[field.name] || []).length === 0
        })),
      valid: state.valid,
      submitting: state.submitting
    };

    return {
      format: 'json',
      content: JSON.stringify(output, null, 2)
    };
  }
}
