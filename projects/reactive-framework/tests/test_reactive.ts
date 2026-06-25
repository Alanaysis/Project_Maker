/**
 * reactive() 测试
 */

import { reactive, isReactive, toRaw, ref } from '../src/reactive';
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

export function testReactive(): void {
  console.log('\n--- reactive() tests ---');

  // Test: 基本响应式
  {
    const state = reactive({ count: 0 });
    assertEqual(state.count, 0, 'Initial value is correct');

    state.count = 1;
    assertEqual(state.count, 1, 'Value updates correctly');
  }

  // Test: 嵌套对象自动代理
  {
    const state = reactive({ nested: { value: 1 } });
    assertEqual(state.nested.value, 1, 'Nested value is accessible');

    state.nested.value = 2;
    assertEqual(state.nested.value, 2, 'Nested value updates');
  }

  // Test: 新增属性
  {
    const state = reactive({} as any);
    state.newKey = 'hello';
    assertEqual(state.newKey, 'hello', 'New property is added and readable');
  }

  // Test: 删除属性
  {
    const state = reactive({ a: 1, b: 2 } as any);
    delete state.a;
    assertEqual(state.a, undefined, 'Property is deleted');
    assertEqual(state.b, 2, 'Other properties remain');
  }

  // Test: isReactive
  {
    const raw = { x: 1 };
    const proxy = reactive(raw);
    assert(isReactive(proxy), 'Proxy is identified as reactive');
    assert(!isReactive(raw), 'Raw object is not reactive');
  }

  // Test: toRaw
  {
    const raw = { x: 1 };
    const proxy = reactive(raw);
    assertEqual(toRaw(proxy), raw, 'toRaw returns original object');
  }

  // Test: 不重复代理
  {
    const raw = { x: 1 };
    const proxy1 = reactive(raw);
    const proxy2 = reactive(raw);
    assertEqual(proxy1, proxy2, 'Same raw object returns same proxy');
  }

  // Test: ref
  {
    const count = ref(0);
    assertEqual(count.value, 0, 'ref initial value');

    count.value = 5;
    assertEqual(count.value, 5, 'ref updated value');
  }

  // Test: 数组操作
  {
    const arr = reactive([1, 2, 3]);
    assertEqual(arr.length, 3, 'Array length is correct');

    arr.push(4);
    assertEqual(arr.length, 4, 'Array push works');

    arr[0] = 10;
    assertEqual(arr[0], 10, 'Array index update works');
  }

  // Test: 依赖收集与通知
  {
    const state = reactive({ count: 0 });
    let callCount = 0;

    const watcher = new Watcher(
      () => state.count,
      (newVal, oldVal) => {
        callCount++;
        assertEqual(newVal, 1, 'Watcher receives new value');
        assertEqual(oldVal, 0, 'Watcher receives old value');
      },
      { sync: true }
    );

    state.count = 1;
    assertEqual(callCount, 1, 'Watcher callback called once');

    // 同值不触发
    state.count = 1;
    assertEqual(callCount, 1, 'Same value does not trigger callback');

    watcher.teardown();
  }

  // Test: 多个 Watcher
  {
    const state = reactive({ x: 0 });
    let countA = 0;
    let countB = 0;

    const watcherA = new Watcher(
      () => state.x,
      () => { countA++; },
      { sync: true }
    );

    const watcherB = new Watcher(
      () => state.x,
      () => { countB++; },
      { sync: true }
    );

    state.x = 1;
    assertEqual(countA, 1, 'Watcher A triggered');
    assertEqual(countB, 1, 'Watcher B triggered');

    watcherA.teardown();
    watcherB.teardown();
  }

  console.log(`\n  reactive() results: ${passed} passed, ${failed} failed`);
}
