/**
 * 边界情况测试
 */

import { FormEngine } from '../src/form-engine';
import { FormRenderer } from '../src/renderer';
import { validateField, rules } from '../src/validator';
import { FormSchema } from '../src/types';

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

export function testEdgeCases(): void {
  console.log('\n--- edge case tests ---');

  // Test: 空表单（无字段）
  {
    const schema: FormSchema = {
      title: '空表单',
      fields: []
    };

    const engine = new FormEngine(schema);
    assertEqual(engine.getState().valid, true, 'empty form: valid by default');
    assertEqual(engine.getVisibleFields().length, 0, 'empty form: no visible fields');

    const renderer = new FormRenderer();
    const result = renderer.render(schema, engine.getState());
    assert(result.content.includes('空表单'), 'empty form: renders title');
  }

  // Test: 条件字段显示
  {
    const schema: FormSchema = {
      title: '条件表单',
      fields: [
        {
          name: 'hasAddress',
          type: 'checkbox',
          label: '有地址',
          defaultValue: false
        },
        {
          name: 'address',
          type: 'textarea',
          label: '地址',
          dependsOn: {
            field: 'hasAddress',
            value: true
          }
        }
      ]
    };

    const engine = new FormEngine(schema);

    // 初始状态：address 不可见
    assertEqual(engine.isFieldVisible(schema.fields[1]), false, 'conditional: address hidden when hasAddress=false');
    assertEqual(engine.getVisibleFields().length, 1, 'conditional: only 1 visible field');

    // 设置 hasAddress = true
    engine.setValue('hasAddress', true);
    assertEqual(engine.isFieldVisible(schema.fields[1]), true, 'conditional: address visible when hasAddress=true');
    assertEqual(engine.getVisibleFields().length, 2, 'conditional: 2 visible fields');
  }

  // Test: disabled 字段
  {
    const schema: FormSchema = {
      title: 'Disabled Test',
      fields: [
        { name: 'locked', type: 'text', label: '锁定', disabled: true, defaultValue: 'readonly' }
      ]
    };

    const engine = new FormEngine(schema);
    assertEqual(engine.getValue('locked'), 'readonly', 'disabled: default value is set');
  }

  // Test: 自定义验证器
  {
    const rule = rules.custom(
      (value, formData) => {
        if (!formData) return true;
        return value === formData['password'];
      },
      '两次密码不一致'
    );

    const result1 = validateField('abc', [rule], { password: 'abc' });
    assertEqual(result1.valid, true, 'custom validator: matching passwords');

    const result2 = validateField('abc', [rule], { password: 'xyz' });
    assertEqual(result2.valid, false, 'custom validator: non-matching passwords');
  }

  // Test: 多次提交
  {
    const schema: FormSchema = {
      title: 'Submit Test',
      fields: [
        { name: 'value', type: 'text', label: '值', defaultValue: 'test' }
      ]
    };

    const engine = new FormEngine(schema);
    let submitCount = 0;

    engine.onSubmit(() => {
      submitCount++;
    });

    engine.submit().then(() => {
      engine.submit().then(() => {
        assertEqual(submitCount, 2, 'multiple submit: handler called twice');
      });
    });
  }

  // Test: 异步提交
  {
    const schema: FormSchema = {
      title: 'Async Test',
      fields: [
        { name: 'value', type: 'text', label: '值', defaultValue: 'test' }
      ]
    };

    const engine = new FormEngine(schema);
    let completed = false;

    engine.onSubmit(async () => {
      await new Promise(resolve => setTimeout(resolve, 10));
      completed = true;
    });

    engine.submit().then(success => {
      assertEqual(success, true, 'async submit: returns true');
      assertEqual(completed, true, 'async submit: async handler completed');
    });
  }

  // Test: 提交失败处理
  {
    const schema: FormSchema = {
      title: 'Error Submit',
      fields: [
        { name: 'value', type: 'text', label: '值', defaultValue: 'test' }
      ]
    };

    const engine = new FormEngine(schema);

    engine.onSubmit(() => {
      throw new Error('提交失败');
    });

    engine.submit().then(success => {
      assertEqual(success, false, 'error submit: returns false on error');
      assertEqual(engine.getState().submitting, false, 'error submit: submitting is reset');
    });
  }

  // Test: 不存在的字段名
  {
    const schema: FormSchema = {
      title: 'Test',
      fields: [{ name: 'exists', type: 'text', label: '存在' }]
    };

    const engine = new FormEngine(schema);
    // 不应该抛出异常
    engine.setValue('nonexistent', 'value');
    assertEqual(engine.getValue('nonexistent'), undefined, 'nonexistent field: setValue does not crash');
    assertEqual(engine.getFieldState('nonexistent'), null, 'nonexistent field: getFieldState returns null');
  }

  // Test: 数值字段验证
  {
    const ruleMin = rules.min(0);
    const ruleMax = rules.max(100);

    assertEqual(validateField(0, [ruleMin]).valid, true, 'number: 0 >= 0 is valid');
    assertEqual(validateField(-1, [ruleMin]).valid, false, 'number: -1 >= 0 is invalid');
    assertEqual(validateField(100, [ruleMax]).valid, true, 'number: 100 <= 100 is valid');
    assertEqual(validateField(101, [ruleMax]).valid, false, 'number: 101 <= 100 is invalid');
  }

  // Test: 模式验证字符串形式
  {
    const rule = rules.pattern('^[0-9]+$', '只允许数字');
    assertEqual(validateField('123', [rule]).valid, true, 'pattern string: "123" matches');
    assertEqual(validateField('abc', [rule]).valid, false, 'pattern string: "abc" does not match');
  }

  // Test: 渲染器空字段列表
  {
    const schema: FormSchema = {
      title: 'Empty Render',
      fields: []
    };

    const engine = new FormEngine(schema);
    const renderer = new FormRenderer();
    const result = renderer.render(schema, engine.getState());

    assert(result.content.includes('Empty Render'), 'empty render: title is rendered');
    assert(result.content.includes('form-fields'), 'empty render: form-fields container exists');
  }

  console.log(`\n  Edge case tests: ${passed} passed, ${failed} failed`);
  if (failed > 0) {
    process.exitCode = 1;
  }
}
