/**
 * 表单验证器
 *
 * 提供各种验证规则的实现，支持：
 * - 内置验证器（required, minLength, maxLength, min, max, pattern, email）
 * - 自定义验证器
 * - 跨字段验证
 */

import { ValidationRule, FieldError, FieldSchema, ValidatorType } from './types';

/** 验证结果 */
export interface ValidationResult {
  valid: boolean;
  errors: FieldError[];
}

/** 内置验证器 */
const builtInValidators: Record<ValidatorType, (value: any, ruleValue?: any) => boolean> = {
  required: (value: any) => {
    if (value === null || value === undefined) return false;
    if (typeof value === 'string') return value.trim().length > 0;
    if (Array.isArray(value)) return value.length > 0;
    return true;
  },

  minLength: (value: any, minLen: number) => {
    if (typeof value !== 'string') return true;
    return value.length >= minLen;
  },

  maxLength: (value: any, maxLen: number) => {
    if (typeof value !== 'string') return true;
    return value.length <= maxLen;
  },

  min: (value: any, minVal: number) => {
    const num = Number(value);
    if (isNaN(num)) return true;
    return num >= minVal;
  },

  max: (value: any, maxVal: number) => {
    const num = Number(value);
    if (isNaN(num)) return true;
    return num <= maxVal;
  },

  pattern: (value: any, pattern: string | RegExp) => {
    if (typeof value !== 'string') return true;
    const regex = typeof pattern === 'string' ? new RegExp(pattern) : pattern;
    return regex.test(value);
  },

  email: (value: any) => {
    if (typeof value !== 'string') return true;
    // RFC 5322 简化版邮箱验证
    const emailRegex = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
    return emailRegex.test(value);
  },

  custom: (value: any) => {
    // 自定义验证器由外部提供，此处返回 true
    return true;
  }
};

/**
 * 验证单个字段
 *
 * @param value - 字段值
 * @param rules - 验证规则列表
 * @param formData - 完整表单数据（用于跨字段验证）
 * @returns 验证结果
 */
export function validateField(
  value: any,
  rules: ValidationRule[],
  formData?: Record<string, any>
): ValidationResult {
  const errors: FieldError[] = [];

  for (const rule of rules) {
    let isValid: boolean;

    // 自定义验证器优先
    if (rule.type === 'custom' && rule.validator) {
      isValid = rule.validator(value, formData);
    } else {
      const validator = builtInValidators[rule.type];
      if (!validator) {
        console.warn(`Unknown validator type: ${rule.type}`);
        continue;
      }
      isValid = validator(value, rule.value);
    }

    if (!isValid) {
      errors.push({
        message: rule.message,
        rule: rule.type
      });
    }
  }

  return {
    valid: errors.length === 0,
    errors
  };
}

/**
 * 验证整个表单
 *
 * @param values - 表单值
 * @param fields - 字段定义
 * @returns 所有字段的验证结果
 */
export function validateForm(
  values: Record<string, any>,
  fields: FieldSchema[]
): Record<string, ValidationResult> {
  const results: Record<string, ValidationResult> = {};

  for (const field of fields) {
    // 跳过隐藏字段
    if (field.hidden) continue;

    const value = values[field.name];
    const rules = field.validation || [];

    results[field.name] = validateField(value, rules, values);
  }

  return results;
}

/**
 * 创建验证规则的便捷函数
 */
export const rules = {
  required(message: string = '此字段为必填项'): ValidationRule {
    return { type: 'required', message };
  },

  minLength(min: number, message?: string): ValidationRule {
    return {
      type: 'minLength',
      value: min,
      message: message || `最少需要 ${min} 个字符`
    };
  },

  maxLength(max: number, message?: string): ValidationRule {
    return {
      type: 'maxLength',
      value: max,
      message: message || `最多允许 ${max} 个字符`
    };
  },

  min(min: number, message?: string): ValidationRule {
    return {
      type: 'min',
      value: min,
      message: message || `最小值为 ${min}`
    };
  },

  max(max: number, message?: string): ValidationRule {
    return {
      type: 'max',
      value: max,
      message: message || `最大值为 ${max}`
    };
  },

  pattern(regex: RegExp | string, message: string): ValidationRule {
    return { type: 'pattern', value: regex, message };
  },

  email(message: string = '请输入有效的邮箱地址'): ValidationRule {
    return { type: 'email', message };
  },

  custom(
    validator: (value: any, formData?: Record<string, any>) => boolean,
    message: string
  ): ValidationRule {
    return { type: 'custom', message, validator };
  }
};
