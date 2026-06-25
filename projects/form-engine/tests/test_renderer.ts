/**
 * 渲染器测试
 */

import { FormRenderer } from '../src/renderer';
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

function assertContains(str: string, substring: string, message: string): void {
  if (str.includes(substring)) {
    passed++;
    console.log(`  PASS: ${message}`);
  } else {
    failed++;
    console.error(`  FAIL: ${message} (string does not contain "${substring}")`);
  }
}

const testSchema: FormSchema = {
  title: '测试表单',
  description: '表单描述',
  submitText: '提交',
  resetText: '重置',
  fields: [
    {
      name: 'username',
      type: 'text',
      label: '用户名',
      placeholder: '请输入用户名',
      validation: [rules.required()]
    },
    {
      name: 'email',
      type: 'email',
      label: '邮箱',
      validation: [rules.required(), rules.email()]
    },
    {
      name: 'role',
      type: 'select',
      label: '角色',
      options: [
        { label: '管理员', value: 'admin' },
        { label: '用户', value: 'user' }
      ]
    },
    {
      name: 'gender',
      type: 'radio',
      label: '性别',
      options: [
        { label: '男', value: 'male' },
        { label: '女', value: 'female' }
      ]
    },
    {
      name: 'agree',
      type: 'checkbox',
      label: '同意协议'
    },
    {
      name: 'bio',
      type: 'textarea',
      label: '简介',
      placeholder: '请输入简介'
    }
  ]
};

export function testRenderer(): void {
  console.log('\n--- renderer tests ---');
  const renderer = new FormRenderer();

  // Test: 基本 HTML 渲染
  {
    const engine = new FormEngine(testSchema);
    const state = engine.getState();
    const result = renderer.render(testSchema, state);

    assertEqual(result.format, 'html', 'render: format is html');
    assertContains(result.content, '<form', 'render: contains form tag');
    assertContains(result.content, '测试表单', 'render: contains form title');
    assertContains(result.content, '表单描述', 'render: contains description');
    assertContains(result.content, '提交', 'render: contains submit button');
    assertContains(result.content, '重置', 'render: contains reset button');
  }

  // Test: 字段渲染
  {
    const engine = new FormEngine(testSchema);
    const state = engine.getState();
    const result = renderer.render(testSchema, state);

    assertContains(result.content, 'name="username"', 'render: contains username field');
    assertContains(result.content, 'name="email"', 'render: contains email field');
    assertContains(result.content, 'name="role"', 'render: contains role select');
    assertContains(result.content, 'type="radio"', 'render: contains radio buttons');
    assertContains(result.content, 'type="checkbox"', 'render: contains checkbox');
    assertContains(result.content, '<textarea', 'render: contains textarea');
  }

  // Test: 选项渲染
  {
    const engine = new FormEngine(testSchema);
    const state = engine.getState();
    const result = renderer.render(testSchema, state);

    assertContains(result.content, '管理员', 'render: contains option label');
    assertContains(result.content, 'value="admin"', 'render: contains option value');
    assertContains(result.content, 'value="male"', 'render: contains radio value');
  }

  // Test: placeholder 渲染
  {
    const engine = new FormEngine(testSchema);
    const state = engine.getState();
    const result = renderer.render(testSchema, state);

    assertContains(result.content, 'placeholder="请输入用户名"', 'render: contains placeholder');
  }

  // Test: 错误信息渲染
  {
    const engine = new FormEngine(testSchema);
    // 触发验证：设置 username 为已触摸，但值为空（违反 required）
    engine.setValue('username', '');
    const state = engine.getState();
    const result = renderer.render(testSchema, state);

    assertContains(result.content, '此字段为必填项', 'render: shows required error message');
    assertContains(result.content, 'field-error', 'render: has error class');
  }

  // Test: 隐藏字段不渲染
  {
    const schemaWithHidden: FormSchema = {
      title: 'Hidden Test',
      fields: [
        { name: 'visible', type: 'text', label: '可见字段' },
        { name: 'hidden', type: 'text', label: '隐藏字段', hidden: true }
      ]
    };

    const state = new FormEngine(schemaWithHidden).getState();
    const result = renderer.render(schemaWithHidden, state);

    assertContains(result.content, '可见字段', 'render: visible field is rendered');
    assert(!result.content.includes('隐藏字段'), 'render: hidden field is not rendered');
  }

  // Test: 纯文本渲染
  {
    const engine = new FormEngine(testSchema);
    engine.setValue('username', 'john');
    const state = engine.getState();
    const result = renderer.renderAsText(testSchema, state);

    assertEqual(result.format, 'text', 'renderAsText: format is text');
    assertContains(result.content, '=== 测试表单 ===', 'renderAsText: contains title');
    assertContains(result.content, '用户名: john', 'renderAsText: contains field value');
  }

  // Test: JSON 渲染
  {
    const engine = new FormEngine(testSchema);
    engine.setValue('username', 'john');
    const state = engine.getState();
    const result = renderer.renderAsJson(testSchema, state);

    assertEqual(result.format, 'json', 'renderAsJson: format is json');

    const json = JSON.parse(result.content);
    assertEqual(json.title, '测试表单', 'renderAsJson: correct title');
    assert(json.fields.length > 0, 'renderAsJson: has fields');
    assertEqual(json.fields[0].value, 'john', 'renderAsJson: correct field value');
  }

  // Test: 禁用字段
  {
    const schemaWithDisabled: FormSchema = {
      title: 'Disabled Test',
      fields: [
        { name: 'locked', type: 'text', label: '锁定字段', disabled: true }
      ]
    };

    const state = new FormEngine(schemaWithDisabled).getState();
    const result = renderer.render(schemaWithDisabled, state);

    assertContains(result.content, 'disabled', 'render: disabled field has disabled attribute');
  }

  // Test: 字段描述渲染
  {
    const schemaWithDesc: FormSchema = {
      title: 'Desc Test',
      fields: [
        { name: 'field', type: 'text', label: '字段', description: '这是帮助文本' }
      ]
    };

    const state = new FormEngine(schemaWithDesc).getState();
    const result = renderer.render(schemaWithDesc, state);

    assertContains(result.content, '这是帮助文本', 'render: field description is rendered');
  }

  // Test: XSS 防护
  {
    const xssSchema: FormSchema = {
      title: '<script>alert("xss")</script>',
      fields: [
        {
          name: 'field',
          type: 'text',
          label: '<img onerror="alert(1)">',
          placeholder: '"><script>',
          defaultValue: 'value'
        }
      ]
    };

    const state = new FormEngine(xssSchema).getState();
    const result = renderer.render(xssSchema, state);

    // HTML 标签被转义为 &lt; 和 &gt;
    assert(!result.content.includes('<script>alert("xss")</script>'), 'xss: script tags are escaped');
    assert(result.content.includes('&lt;script&gt;'), 'xss: script tags are properly escaped');
    assert(!result.content.includes('<img'), 'xss: img tags are escaped');
    assert(result.content.includes('&lt;img'), 'xss: img tags are properly escaped');
  }

  console.log(`\n  Renderer tests: ${passed} passed, ${failed} failed`);
  if (failed > 0) {
    process.exitCode = 1;
  }
}
