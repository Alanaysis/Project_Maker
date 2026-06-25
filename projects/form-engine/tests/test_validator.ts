/**
 * 验证器测试
 */

import { validateField, validateForm, rules } from '../src/validator';
import { ValidationRule, FieldSchema } from '../src/types';

let passed = 0;
let failed = 0;

function assert(condition: boolean, message: string): void {
  if (condition) {
    passed++;
    console.log(`  PASS: ${message}`);
  } else {
    failed++;
    console.error(`  FAIL: ${message}`);
  }
}

function assertEqual(actual: any, expected: any, message: string): void {
  if (actual === expected) {
    passed++;
    console.log(`  PASS: ${message}`);
  } else {
    failed++;
    console.error(`  FAIL: ${message} (expected: ${JSON.stringify(expected)}, got: ${JSON.stringify(actual)})`);
  }
}

export function testValidator(): void {
  console.log('\n--- validator tests ---');

  // Test: required 规则
  {
    const rule = rules.required();
    assertEqual(validateField('', [rule]).valid, false, 'required: empty string is invalid');
    assertEqual(validateField('hello', [rule]).valid, true, 'required: non-empty string is valid');
    assertEqual(validateField(null, [rule]).valid, false, 'required: null is invalid');
    assertEqual(validateField(undefined, [rule]).valid, false, 'required: undefined is invalid');
    assertEqual(validateField([], [rule]).valid, false, 'required: empty array is invalid');
    assertEqual(validateField([1], [rule]).valid, true, 'required: non-empty array is valid');
  }

  // Test: minLength 规则
  {
    const rule = rules.minLength(3);
    assertEqual(validateField('ab', [rule]).valid, false, 'minLength: "ab" < 3 is invalid');
    assertEqual(validateField('abc', [rule]).valid, true, 'minLength: "abc" >= 3 is valid');
    assertEqual(validateField('abcd', [rule]).valid, true, 'minLength: "abcd" >= 3 is valid');
  }

  // Test: maxLength 规则
  {
    const rule = rules.maxLength(5);
    assertEqual(validateField('hello', [rule]).valid, true, 'maxLength: "hello" <= 5 is valid');
    assertEqual(validateField('hello world', [rule]).valid, false, 'maxLength: "hello world" > 5 is invalid');
  }

  // Test: min 规则
  {
    const rule = rules.min(10);
    assertEqual(validateField(5, [rule]).valid, false, 'min: 5 < 10 is invalid');
    assertEqual(validateField(10, [rule]).valid, true, 'min: 10 >= 10 is valid');
    assertEqual(validateField(15, [rule]).valid, true, 'min: 15 >= 10 is valid');
  }

  // Test: max 规则
  {
    const rule = rules.max(100);
    assertEqual(validateField(50, [rule]).valid, true, 'max: 50 <= 100 is valid');
    assertEqual(validateField(100, [rule]).valid, true, 'max: 100 <= 100 is valid');
    assertEqual(validateField(101, [rule]).valid, false, 'max: 101 > 100 is invalid');
  }

  // Test: pattern 规则
  {
    const rule = rules.pattern(/^[A-Z]+$/, '只允许大写字母');
    assertEqual(validateField('ABC', [rule]).valid, true, 'pattern: "ABC" matches /^[A-Z]+$/');
    assertEqual(validateField('abc', [rule]).valid, false, 'pattern: "abc" does not match /^[A-Z]+$/');
    assertEqual(validateField('Abc', [rule]).valid, false, 'pattern: "Abc" does not match /^[A-Z]+$/');
  }

  // Test: email 规则
  {
    const rule = rules.email();
    assertEqual(validateField('user@example.com', [rule]).valid, true, 'email: valid email');
    assertEqual(validateField('invalid-email', [rule]).valid, false, 'email: invalid email');
    assertEqual(validateField('user@', [rule]).valid, false, 'email: incomplete email');
    assertEqual(validateField('@example.com', [rule]).valid, false, 'email: missing local part');
  }

  // Test: 自定义验证器
  {
    const rule = rules.custom(
      (value) => value === 'confirm',
      '请输入 confirm'
    );
    assertEqual(validateField('confirm', [rule]).valid, true, 'custom: "confirm" passes');
    assertEqual(validateField('wrong', [rule]).valid, false, 'custom: "wrong" fails');
  }

  // Test: 多规则组合
  {
    const fieldRules = [
      rules.required('用户名不能为空'),
      rules.minLength(3, '用户名至少3个字符'),
      rules.maxLength(20, '用户名最多20个字符')
    ];

    assertEqual(validateField('', fieldRules).valid, false, 'multi-rules: empty string fails');
    assertEqual(validateField('ab', fieldRules).valid, false, 'multi-rules: "ab" fails minLength');
    assertEqual(validateField('abc', fieldRules).valid, true, 'multi-rules: "abc" passes all');
    assertEqual(validateField('a'.repeat(21), fieldRules).valid, false, 'multi-rules: 21 chars fails maxLength');
  }

  // Test: 多规则返回正确数量的错误
  {
    const fieldRules = [
      rules.required(),
      rules.minLength(5)
    ];
    const result = validateField('', fieldRules);
    assertEqual(result.errors.length, 2, 'error count: empty string has 2 errors (required + minLength)');
  }

  // Test: validateForm
  {
    const fields: FieldSchema[] = [
      {
        name: 'username',
        type: 'text',
        label: '用户名',
        validation: [rules.required(), rules.minLength(3)]
      },
      {
        name: 'email',
        type: 'email',
        label: '邮箱',
        validation: [rules.required(), rules.email()]
      },
      {
        name: 'age',
        type: 'number',
        label: '年龄',
        validation: [rules.min(0), rules.max(150)]
      }
    ];

    const result1 = validateForm({ username: 'ab', email: 'bad', age: 200 }, fields);
    assertEqual(result1['username'].valid, false, 'validateForm: short username invalid');
    assertEqual(result1['email'].valid, false, 'validateForm: bad email invalid');
    assertEqual(result1['age'].valid, false, 'validateForm: age 200 invalid');

    const result2 = validateForm({ username: 'john', email: 'john@example.com', age: 25 }, fields);
    assertEqual(result2['username'].valid, true, 'validateForm: valid username');
    assertEqual(result2['email'].valid, true, 'validateForm: valid email');
    assertEqual(result2['age'].valid, true, 'validateForm: valid age');
  }

  // Test: 隐藏字段跳过验证
  {
    const fields: FieldSchema[] = [
      {
        name: 'secret',
        type: 'text',
        label: 'Secret',
        hidden: true,
        validation: [rules.required()]
      }
    ];
    const result = validateForm({}, fields);
    assertEqual(result['secret'], undefined, 'validateForm: hidden fields are skipped');
  }

  console.log(`\n  Validator tests: ${passed} passed, ${failed} failed`);
  if (failed > 0) {
    process.exitCode = 1;
  }
}
