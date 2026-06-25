/**
 * 示例：Todo 应用（命令行版）
 *
 * 用响应式框架模拟一个简单的 Todo 状态管理。
 */

import { reactive, computed, watch } from '../src';

interface Todo {
  id: number;
  text: string;
  completed: boolean;
}

const state = reactive({
  todos: [] as Todo[],
  filter: 'all' as 'all' | 'active' | 'completed',
  nextId: 1,
});

// 计算属性：过滤后的 todos
const filteredTodos = computed(() => {
  switch (state.filter) {
    case 'active':
      return state.todos.filter(t => !t.completed);
    case 'completed':
      return state.todos.filter(t => t.completed);
    default:
      return state.todos;
  }
});

// 计算属性：统计信息
const stats = computed(() => {
  const total = state.todos.length;
  const completed = state.todos.filter(t => t.completed).length;
  const active = total - completed;
  return { total, completed, active };
});

// 动作函数
function addTodo(text: string): void {
  state.todos.push({
    id: state.nextId++,
    text,
    completed: false,
  });
}

function toggleTodo(id: number): void {
  const todo = state.todos.find(t => t.id === id);
  if (todo) {
    todo.completed = !todo.completed;
  }
}

function removeTodo(id: number): void {
  const index = state.todos.findIndex(t => t.id === id);
  if (index !== -1) {
    state.todos.splice(index, 1);
  }
}

function setFilter(filter: 'all' | 'active' | 'completed'): void {
  state.filter = filter;
}

console.log('=== Todo 应用示例 ===\n');

// 侦听统计变化
watch(
  () => `${stats.value.active} 个待办, ${stats.value.completed} 个已完成`,
  (newVal) => {
    console.log(`  [统计] ${newVal}`);
  }
);

// 添加 todos
console.log('添加待办事项:');
addTodo('学习响应式原理');
addTodo('实现依赖收集');
addTodo('编写测试用例');
addTodo('撰写文档');

// 显示所有
console.log('\n所有待办:');
for (const todo of filteredTodos.value) {
  const mark = todo.completed ? '[x]' : '[ ]';
  console.log(`  ${mark} ${todo.id}. ${todo.text}`);
}

// 完成一些
console.log('\n完成第1和第3项:');
toggleTodo(1);
toggleTodo(3);

// 查看待办
console.log('\n查看待办 (filter=active):');
setFilter('active');
for (const todo of filteredTodos.value) {
  console.log(`  [ ] ${todo.id}. ${todo.text}`);
}

// 查看已完成
console.log('\n查看已完成 (filter=completed):');
setFilter('completed');
for (const todo of filteredTodos.value) {
  console.log(`  [x] ${todo.id}. ${todo.text}`);
}

// 删除一个
console.log('\n删除第2项:');
removeTodo(2);

// 最终状态
console.log('\n最终状态 (filter=all):');
setFilter('all');
for (const todo of filteredTodos.value) {
  const mark = todo.completed ? '[x]' : '[ ]';
  console.log(`  ${mark} ${todo.id}. ${todo.text}`);
}

console.log(`\n统计: ${stats.value.total} 总计, ${stats.value.active} 待办, ${stats.value.completed} 已完成`);
