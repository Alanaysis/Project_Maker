/**
 * watch() 测试
 */

import { reactive } from '../src/reactive';
import { watch } from '../src/watch';

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

export function testWatch(): void {
  console.log('\n--- watch() tests ---');

  // Test: 基本侦听
  {
    const state = reactive({ count: 0 });
    const changes: Array<{ newVal: number; oldVal: number }> = [];

    watch(
      () => state.count,
      (newVal, oldVal) => {
        changes.push({ newVal, oldVal });
      },
      { sync: true }
    );

    state.count = 1;
    state.count = 2;

    assertEqual(changes.length, 2, 'Two changes recorded');
    assertEqual(changes[0].newVal, 1, 'First change new value');
    assertEqual(changes[0].oldVal, 0, 'First change old value');
    assertEqual(changes[1].newVal, 2, 'Second change new value');
    assertEqual(changes[1].oldVal, 1, 'Second change old value');
  }

  // Test: immediate 选项
  {
    const state = reactive({ value: 'initial' });
    let capturedValue: string | undefined;

    watch(
      () => state.value,
      (newVal) => {
        capturedValue = newVal;
      },
      { immediate: true, sync: true }
    );

    assertEqual(capturedValue, 'initial', 'Immediate callback with current value');
  }

  // Test: 取消侦听
  {
    const state = reactive({ x: 0 });
    let callCount = 0;

    const unwatch = watch(
      () => state.x,
      () => { callCount++; },
      { sync: true }
    );

    state.x = 1;
    assertEqual(callCount, 1, 'Callback called before unwatch');

    unwatch();

    state.x = 2;
    assertEqual(callCount, 1, 'Callback not called after unwatch');
  }

  // Test: 侦听嵌套属性
  {
    const state = reactive({ user: { name: 'Alice', age: 25 } });
    let lastAge: number | undefined;

    watch(
      () => state.user.age,
      (newVal) => {
        lastAge = newVal;
      },
      { sync: true }
    );

    state.user.age = 26;
    assertEqual(lastAge, 26, 'Nested property change detected');
  }

  // Test: 侦听多个值
  {
    const state = reactive({ a: 1, b: 2 });
    let sumHistory: number[] = [];

    watch(
      () => state.a + state.b,
      (newVal) => {
        sumHistory.push(newVal);
      },
      { sync: true }
    );

    state.a = 10;
    state.b = 20;

    assertEqual(sumHistory.length, 2, 'Multiple dependency changes detected');
    assertEqual(sumHistory[0], 12, 'First sum is correct');
    assertEqual(sumHistory[1], 30, 'Second sum is correct');
  }

  console.log(`\n  watch() results: ${passed} passed, ${failed} failed`);
}
