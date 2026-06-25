/**
 * 示例：侦听器
 *
 * 演示 watch() API 的各种用法。
 */

import { reactive, computed, watch } from '../src';

// 表单验证示例
const form = reactive({
  username: '',
  password: '',
  email: '',
});

// 用户名验证
const usernameError = computed(() => {
  if (form.username.length === 0) return '用户名不能为空';
  if (form.username.length < 3) return '用户名至少3个字符';
  if (form.username.length > 20) return '用户名最多20个字符';
  return '';
});

// 密码验证
const passwordError = computed(() => {
  if (form.password.length === 0) return '密码不能为空';
  if (form.password.length < 6) return '密码至少6个字符';
  return '';
});

// 邮箱验证
const emailError = computed(() => {
  if (form.email.length === 0) return '邮箱不能为空';
  if (!form.email.includes('@')) return '邮箱格式不正确';
  return '';
});

// 表单是否有效
const isFormValid = computed(() =>
  usernameError.value === '' &&
  passwordError.value === '' &&
  emailError.value === ''
);

console.log('=== 表单验证示例 ===\n');

// 侦听表单有效性变化
watch(
  () => isFormValid.value,
  (valid) => {
    console.log(`  表单有效性: ${valid ? '有效' : '无效'}`);
  }
);

// 侦听每个字段的错误
watch(
  () => usernameError.value,
  (err) => { if (err) console.log(`  [用户名] ${err}`); }
);

watch(
  () => passwordError.value,
  (err) => { if (err) console.log(`  [密码] ${err}`); }
);

watch(
  () => emailError.value,
  (err) => { if (err) console.log(`  [邮箱] ${err}`); }
);

// 模拟用户输入
console.log('用户输入用户名 "ab":');
form.username = 'ab';

console.log('\n用户输入密码 "123":');
form.password = '123';

console.log('\n用户输入邮箱 "test":');
form.email = 'test';

console.log('\n用户修正用户名为 "alice":');
form.username = 'alice';

console.log('\n用户修正密码为 "password123":');
form.password = 'password123';

console.log('\n用户修正邮箱为 "alice@example.com":');
form.email = 'alice@example.com';

console.log('\n最终状态:');
console.log(`  用户名错误: "${usernameError.value}"`);
console.log(`  密码错误: "${passwordError.value}"`);
console.log(`  邮箱错误: "${emailError.value}"`);
console.log(`  表单有效: ${isFormValid.value}`);

// 取消侦听示例
console.log('\n=== 取消侦听示例 ===\n');

const counter = reactive({ value: 0 });

const unwatch = watch(
  () => counter.value,
  (newVal) => {
    console.log(`  counter = ${newVal}`);
  }
);

counter.value = 1;
counter.value = 2;

console.log('取消侦听...');
unwatch();

counter.value = 3;
counter.value = 4;
console.log('(取消后不再输出变化)');
