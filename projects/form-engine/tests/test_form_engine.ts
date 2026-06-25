/**
 * 表单引擎测试
 */

import { FormEngine } from '../src/form-engine';
import { rules } from '../src/validator';
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

const testSchema: FormSchema = {
  title: '测试表单',
  description: '这是一个测试表单',
  fields: [
    {
      name: 'username',
      type: 'text',
      label: '用户名',
      placeholder: '请输入用户名',
      defaultValue: '',
      validation: [
        rules.required('用户名不能为空'),
        rules.minLength(3, '用户名至少3个字符')
      ]
    },
    {
      name: 'email',
      type: 'email',
      label: '邮箱',
      placeholder: '请输入邮箱',
      validation: [
        rules.required('邮箱不能为空'),
        rules.email('请输入有效的邮箱')
      ]
    },
    {
      name: 'age',
      type: 'number',
      label: '年龄',
      defaultValue: 0,
      validation: [
        rules.min(0, '年龄不能为负'),
        rules.max(150, '年龄不能超过150')
      ]
    },
    {
      name: 'agree',
      type: 'checkbox',
      label: '同意协议',
      defaultValue: false
    }
  ]
};

export function testFormEngine(): void {
  console.log('\n--- form engine tests ---');

  // Test: 初始化
  {
    const engine = new FormEngine(testSchema);
    const state = engine.getState();

    assertEqual(state.values['username'], '', 'init: username default value');
    assertEqual(state.values['email'], '', 'init: email default value');
    assertEqual(state.values['age'], 0, 'init: age default value');
    assertEqual(state.values['agree'], false, 'init: agree default value');
    assertEqual(state.valid, true, 'init: form is valid initially');
    assertEqual(state.submitting, false, 'init: not submitting');
    assertEqual(state.submitted, false, 'init: not submitted');
  }

  // Test: 设置值
  {
    const engine = new FormEngine(testSchema);
    engine.setValue('username', 'john');

    assertEqual(engine.getValue('username'), 'john', 'setValue: value is updated');
    const fieldState = engine.getFieldState('username');
    assertEqual(fieldState?.touched, true, 'setValue: field is touched');
    assertEqual(fieldState?.dirty, true, 'setValue: field is dirty');
  }

  // Test: 验证触发
  {
    const engine = new FormEngine(testSchema);
    engine.setValue('username', 'ab');

    const fieldState = engine.getFieldState('username');
    assertEqual(fieldState?.valid, false, 'validation: short username is invalid');
    assertEqual(fieldState?.errors.length, 1, 'validation: has 1 error');
    assertEqual(fieldState?.errors[0].rule, 'minLength', 'validation: error is minLength');
  }

  // Test: 表单整体有效性
  {
    const engine = new FormEngine(testSchema);
    engine.setValue('username', 'ab');
    assertEqual(engine.getState().valid, false, 'form validity: invalid when field has error');

    engine.setValue('username', 'john');
    // 触发 email 验证
    engine.setValue('email', '');
    assertEqual(engine.getState().valid, false, 'form validity: invalid when required field is empty');
  }

  // Test: getValue / getValues
  {
    const engine = new FormEngine(testSchema);
    engine.setValue('username', 'alice');
    engine.setValue('email', 'alice@example.com');

    assertEqual(engine.getValue('username'), 'alice', 'getValue: returns correct value');
    const values = engine.getValues();
    assertEqual(values['username'], 'alice', 'getValues: contains username');
    assertEqual(values['email'], 'alice@example.com', 'getValues: contains email');
  }

  // Test: setTouched
  {
    const engine = new FormEngine(testSchema);
    assertEqual(engine.getFieldState('username')?.touched, false, 'setTouched: initially not touched');

    engine.setTouched('username');
    assertEqual(engine.getFieldState('username')?.touched, true, 'setTouched: now touched');
  }

  // Test: reset
  {
    const engine = new FormEngine(testSchema);
    engine.setValue('username', 'john');
    engine.setValue('email', 'john@example.com');

    engine.reset();
    assertEqual(engine.getValue('username'), '', 'reset: username is reset');
    assertEqual(engine.getValue('email'), '', 'reset: email is reset');
    assertEqual(engine.getFieldState('username')?.touched, false, 'reset: touched is reset');
    assertEqual(engine.getFieldState('username')?.dirty, false, 'reset: dirty is reset');
    assertEqual(engine.getState().submitted, false, 'reset: submitted is reset');
  }

  // Test: submit with valid form
  {
    const engine = new FormEngine(testSchema);
    let submittedValues: Record<string, any> | null = null;

    engine.onSubmit((values) => {
      submittedValues = values;
    });

    engine.setValue('username', 'john');
    engine.setValue('email', 'john@example.com');
    engine.setValue('age', 25);

    engine.submit().then(success => {
      assertEqual(success, true, 'submit: returns true for valid form');
      assertEqual(submittedValues?.['username'], 'john', 'submit: callback receives correct values');
    });
  }

  // Test: submit with invalid form
  {
    const engine = new FormEngine(testSchema);
    let submitted = false;

    engine.onSubmit(() => {
      submitted = true;
    });

    // 不设置必填字段
    engine.submit().then(success => {
      assertEqual(success, false, 'submit: returns false for invalid form');
      assertEqual(submitted, false, 'submit: callback not called for invalid form');
      assertEqual(engine.getState().submitted, true, 'submit: submitted flag is set');
    });
  }

  // Test: onStateChange callback
  {
    const engine = new FormEngine(testSchema);
    let stateChanges = 0;

    engine.onStateChange(() => {
      stateChanges++;
    });

    engine.setValue('username', 'john');
    assertEqual(stateChanges, 1, 'onStateChange: called on setValue');

    engine.reset();
    assertEqual(stateChanges, 2, 'onStateChange: called on reset');
  }

  // Test: getSchema
  {
    const engine = new FormEngine(testSchema);
    const schema = engine.getSchema();
    assertEqual(schema.title, '测试表单', 'getSchema: returns correct title');
    assertEqual(schema.fields.length, 4, 'getSchema: returns correct field count');
  }

  // Test: getHandlers
  {
    const engine = new FormEngine(testSchema);
    const handlers = engine.getHandlers();

    assert(typeof handlers.onChange === 'function', 'getHandlers: onChange is function');
    assert(typeof handlers.onBlur === 'function', 'getHandlers: onBlur is function');
    assert(typeof handlers.onSubmit === 'function', 'getHandlers: onSubmit is function');
    assert(typeof handlers.onReset === 'function', 'getHandlers: onReset is function');
  }

  // Test: handlers.onChange
  {
    const engine = new FormEngine(testSchema);
    const handlers = engine.getHandlers();

    handlers.onChange('username', 'test');
    assertEqual(engine.getValue('username'), 'test', 'handlers.onChange: updates value');
  }

  // Test: handlers.onReset
  {
    const engine = new FormEngine(testSchema);
    const handlers = engine.getHandlers();

    engine.setValue('username', 'john');
    handlers.onReset();
    assertEqual(engine.getValue('username'), '', 'handlers.onReset: resets form');
  }

  console.log(`\n  Form engine tests: ${passed} passed, ${failed} failed`);
  if (failed > 0) {
    process.exitCode = 1;
  }
}
