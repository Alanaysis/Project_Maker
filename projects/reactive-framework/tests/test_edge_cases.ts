/**
 * 边界情况测试
 */

import { reactive, ref, isReactive, toRaw } from '../src/reactive';
import { computed } from '../src/computed';
import { watch } from '../src/watch';
import { Dep } from '../src/dep';
import { Watcher } from '../src/watcher';

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
  console.log('\n--- edge cases tests ---');

  // Test: 对象内包含数组
  {
    const state = reactive({ items: [1, 2, 3], count: 0 });
    let updateCount = 0;

    const watcher = new Watcher(
      () => state.items.length,
      () => { updateCount++; },
      { sync: true }
    );

    state.items.push(4);
    assertEqual(updateCount, 1, 'Array push triggers watcher');

    state.items.pop();
    assertEqual(updateCount, 2, 'Array pop triggers watcher');

    watcher.teardown();
  }

  // Test: 对象内包含 null
  {
    const state = reactive({ data: null as any });
    assertEqual(state.data, null, 'Null value is preserved');

    state.data = { value: 1 };
    assertEqual(state.data.value, 1, 'Null replaced with object');
    assert(isReactive(state.data), 'New object is also reactive');
  }

  // Test: 多层嵌套
  {
    const state = reactive({
      level1: {
        level2: {
          level3: { value: 'deep' }
        }
      }
    });

    assertEqual(state.level1.level2.level3.value, 'deep', 'Deep nested value is accessible');

    let captured: string | undefined;
    const watcher = new Watcher(
      () => state.level1.level2.level3.value,
      (newVal) => { captured = newVal; },
      { sync: true }
    );

    state.level1.level2.level3.value = 'updated';
    assertEqual(captured, 'updated', 'Deep nested change detected');

    watcher.teardown();
  }

  // Test: Symbol 属性
  {
    const sym = Symbol('test');
    const state = reactive({ [sym]: 'symbol value' } as any);
    assertEqual(state[sym], 'symbol value', 'Symbol property is accessible');
  }

  // Test: computed 嵌套 computed
  {
    const state = reactive({ x: 1 });
    const doubled = computed(() => state.x * 2);
    const quadrupled = computed(() => doubled.value * 2);

    assertEqual(quadrupled.value, 4, 'Nested computed value is correct');

    state.x = 5;
    assertEqual(quadrupled.value, 20, 'Nested computed updates correctly');
  }

  // Test: watch 同值不触发
  {
    const state = reactive({ x: 1 });
    let callCount = 0;

    watch(
      () => state.x,
      () => { callCount++; },
      { sync: true }
    );

    state.x = 1; // 同值
    assertEqual(callCount, 0, 'Same value does not trigger callback');
  }

  // Test: 循环引用安全
  {
    const state = reactive({} as any);
    state.self = state;
    assertEqual(state.self, state, 'Self-reference returns same proxy');
  }

  // Test: ref 嵌套
  {
    const count = ref(0);
    const doubled = computed(() => count.value * 2);

    assertEqual(doubled.value, 0, 'Computed on ref works');

    count.value = 5;
    assertEqual(doubled.value, 10, 'Computed on ref updates');
  }

  // Test: Watcher teardown 后不再收集依赖
  {
    const state = reactive({ x: 0 });
    let callCount = 0;

    const watcher = new Watcher(
      () => state.x,
      () => { callCount++; },
      { sync: true }
    );

    state.x = 1;
    assertEqual(callCount, 1, 'Before teardown: callback called');

    watcher.teardown();

    state.x = 2;
    assertEqual(callCount, 1, 'After teardown: callback not called');
  }

  // Test: 检查 Dep.target 清理
  {
    // 确保没有泄漏的活跃 Watcher
    assertEqual(Dep.target, null, 'Dep.target is null after all operations');
  }

  console.log(`\n  edge cases results: ${passed} passed, ${failed} failed`);
}
