/**
 * 示例：基本响应式数据
 *
 * 演示如何使用 reactive() 创建响应式对象，
 * 以及数据变化如何自动触发更新。
 */

import { reactive, watch } from '../src';

// 创建响应式状态
const state = reactive({
  count: 0,
  message: 'Hello Reactive',
  user: {
    name: 'Alice',
    age: 25,
  },
});

// 侦听 count 变化
watch(
  () => state.count,
  (newVal, oldVal) => {
    console.log(`[count] ${oldVal} -> ${newVal}`);
  }
);

// 侦听嵌套属性变化
watch(
  () => state.user.age,
  (newVal, oldVal) => {
    console.log(`[user.age] ${oldVal} -> ${newVal}`);
  }
);

// 修改数据 - 自动触发更新
console.log('\n--- 修改 count ---');
state.count = 1;
state.count = 2;
state.count = 3;

console.log('\n--- 修改嵌套属性 ---');
state.user.age = 26;
state.user.age = 27;

console.log('\n--- 新增属性 ---');
(state as any).newProp = '动态添加的属性';
console.log(`newProp: ${(state as any).newProp}`);

console.log('\n--- 删除属性 ---');
delete (state as any).newProp;
console.log(`newProp after delete: ${(state as any).newProp}`);
