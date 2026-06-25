/**
 * 注册表单示例
 *
 * 演示：
 * - 跨字段验证（密码确认）
 * - 多种字段类型
 * - 选项选择
 */

import { FormEngine, FormRenderer, rules, FormSchema } from '../src';

// 定义注册表单 Schema
const registrationSchema: FormSchema = {
  title: '用户注册',
  description: '创建您的账号',
  submitText: '注册',
  fields: [
    {
      name: 'username',
      type: 'text',
      label: '用户名',
      placeholder: '请输入用户名',
      description: '3-20个字符，只能包含字母和数字',
      validation: [
        rules.required('请输入用户名'),
        rules.minLength(3, '用户名至少3个字符'),
        rules.maxLength(20, '用户名最多20个字符'),
        rules.pattern(/^[a-zA-Z0-9]+$/, '用户名只能包含字母和数字')
      ]
    },
    {
      name: 'email',
      type: 'email',
      label: '邮箱',
      placeholder: '请输入邮箱地址',
      validation: [
        rules.required('请输入邮箱'),
        rules.email('请输入有效的邮箱地址')
      ]
    },
    {
      name: 'password',
      type: 'password',
      label: '密码',
      placeholder: '请输入密码',
      description: '至少8个字符，包含字母和数字',
      validation: [
        rules.required('请输入密码'),
        rules.minLength(8, '密码至少8个字符'),
        rules.pattern(
          /^(?=.*[a-zA-Z])(?=.*\d).+$/,
          '密码必须包含字母和数字'
        )
      ]
    },
    {
      name: 'confirmPassword',
      type: 'password',
      label: '确认密码',
      placeholder: '请再次输入密码',
      validation: [
        rules.required('请确认密码'),
        rules.custom(
          (value, formData) => value === formData?.['password'],
          '两次输入的密码不一致'
        )
      ]
    },
    {
      name: 'gender',
      type: 'radio',
      label: '性别',
      options: [
        { label: '男', value: 'male' },
        { label: '女', value: 'female' },
        { label: '保密', value: 'secret' }
      ],
      defaultValue: 'secret'
    },
    {
      name: 'role',
      type: 'select',
      label: '角色',
      options: [
        { label: '普通用户', value: 'user' },
        { label: '开发者', value: 'developer' },
        { label: '管理员', value: 'admin' }
      ],
      defaultValue: 'user'
    },
    {
      name: 'bio',
      type: 'textarea',
      label: '个人简介',
      placeholder: '介绍一下自己...',
      validation: [
        rules.maxLength(200, '简介最多200个字符')
      ]
    },
    {
      name: 'agreeTerms',
      type: 'checkbox',
      label: '我已阅读并同意用户协议',
      validation: [
        rules.custom(
          (value) => value === true,
          '请同意用户协议'
        )
      ]
    }
  ]
};

// 创建表单引擎实例
const engine = new FormEngine(registrationSchema);
const renderer = new FormRenderer();

// 注册提交回调
engine.onSubmit(async (values) => {
  console.log('\n[提交] 注册信息:');
  console.log(`  用户名: ${values.username}`);
  console.log(`  邮箱: ${values.email}`);
  console.log(`  性别: ${values.gender}`);
  console.log(`  角色: ${values.role}`);
  console.log(`  简介: ${values.bio || '(未填写)'}`);
  console.log('\n模拟注册中...');
  await new Promise(resolve => setTimeout(resolve, 500));
  console.log('注册成功!');
});

// 模拟用户操作
console.log('=== 注册表单示例 ===\n');

// 1. 显示初始表单
console.log('1. 初始表单:');
const initialText = renderer.renderAsText(registrationSchema, engine.getState());
console.log(initialText.content);

// 2. 用户填写表单
console.log('\n2. 用户填写表单:');
engine.setValue('username', 'alice123');
engine.setValue('email', 'alice@example.com');
engine.setValue('password', 'pass1234');
engine.setValue('confirmPassword', 'pass1234');
engine.setValue('gender', 'female');
engine.setValue('role', 'developer');
engine.setValue('bio', '全栈开发者，喜欢开源');
engine.setValue('agreeTerms', true);

// 3. 显示验证结果
console.log('\n3. 验证结果:');
const state = engine.getState();
console.log(`表单有效: ${state.valid}`);
for (const field of registrationSchema.fields) {
  const fieldState = engine.getFieldState(field.name);
  if (fieldState) {
    const status = fieldState.valid ? '✓' : '✗';
    console.log(`  ${status} ${field.label}: ${fieldState.value}`);
    if (!fieldState.valid) {
      for (const error of fieldState.errors) {
        console.log(`    - ${error.message}`);
      }
    }
  }
}

// 4. 提交表单
console.log('\n4. 提交表单:');
engine.submit().then(success => {
  console.log(`提交结果: ${success ? '成功' : '失败'}`);
});

// 5. 测试密码不一致的情况
console.log('\n5. 测试密码不一致:');
const engine2 = new FormEngine(registrationSchema);
engine2.setValue('username', 'bob');
engine2.setValue('email', 'bob@example.com');
engine2.setValue('password', 'password123');
engine2.setValue('confirmPassword', 'different456');

const confirmState = engine2.getFieldState('confirmPassword');
console.log(`密码确认验证: ${confirmState?.valid ? '通过' : '失败'}`);
if (confirmState && !confirmState.valid) {
  console.log(`错误: ${confirmState.errors.map(e => e.message).join(', ')}`);
}
