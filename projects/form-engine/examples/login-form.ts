/**
 * 登录表单示例
 *
 * 演示基本的表单引擎用法：
 * - 创建表单 Schema
 * - 验证
 * - 提交处理
 */

import { FormEngine, FormRenderer, rules, FormSchema } from '../src';

// 定义登录表单 Schema
const loginSchema: FormSchema = {
  title: '用户登录',
  description: '请输入您的账号和密码',
  submitText: '登录',
  resetText: '重置',
  fields: [
    {
      name: 'username',
      type: 'text',
      label: '用户名',
      placeholder: '请输入用户名',
      validation: [
        rules.required('请输入用户名'),
        rules.minLength(3, '用户名至少3个字符')
      ]
    },
    {
      name: 'password',
      type: 'password',
      label: '密码',
      placeholder: '请输入密码',
      validation: [
        rules.required('请输入密码'),
        rules.minLength(6, '密码至少6个字符')
      ]
    },
    {
      name: 'remember',
      type: 'checkbox',
      label: '记住我',
      defaultValue: false
    }
  ]
};

// 创建表单引擎实例
const engine = new FormEngine(loginSchema);
const renderer = new FormRenderer();

// 注册提交回调
engine.onSubmit(async (values) => {
  console.log('\n[提交] 登录信息:');
  console.log(`  用户名: ${values.username}`);
  console.log(`  记住我: ${values.remember ? '是' : '否'}`);
  console.log('\n模拟登录中...');
  await new Promise(resolve => setTimeout(resolve, 500));
  console.log('登录成功!');
});

// 监听状态变更
engine.onStateChange((state) => {
  const usernameState = engine.getFieldState('username');
  const passwordState = engine.getFieldState('password');

  if (usernameState?.touched && !usernameState.valid) {
    console.log(`[验证] 用户名: ${usernameState.errors.map(e => e.message).join(', ')}`);
  }
  if (passwordState?.touched && !passwordState.valid) {
    console.log(`[验证] 密码: ${passwordState.errors.map(e => e.message).join(', ')}`);
  }
});

// 模拟用户操作
console.log('=== 登录表单示例 ===\n');

// 1. 初始状态渲染
console.log('1. 初始状态:');
const initialRender = renderer.render(loginSchema, engine.getState());
console.log(initialRender.content);

// 2. 用户输入
console.log('\n2. 用户输入:');
engine.setValue('username', 'ab');  // 太短
console.log('设置用户名: ab');

engine.setValue('password', '123');  // 太短
console.log('设置密码: 123');

// 3. 验证失败后渲染
console.log('\n3. 验证结果 (带错误信息):');
const errorRender = renderer.render(loginSchema, engine.getState());
console.log(errorRender.content);

// 4. 用户修正输入
console.log('\n4. 用户修正输入:');
engine.setValue('username', 'alice');
engine.setValue('password', 'password123');
engine.setValue('remember', true);
console.log('设置用户名: alice');
console.log('设置密码: password123');
console.log('设置记住我: true');

// 5. 验证通过后提交
console.log('\n5. 提交表单:');
engine.submit().then(success => {
  console.log(`提交结果: ${success ? '成功' : '失败'}`);

  // 6. 最终状态
  console.log('\n6. 最终状态 (JSON):');
  const jsonRender = renderer.renderAsJson(loginSchema, engine.getState());
  console.log(jsonRender.content);
});
