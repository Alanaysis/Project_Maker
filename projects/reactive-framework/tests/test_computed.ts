/**
 * computed() 测试
 */

import { reactive } from '../src/reactive';
import { computed } from '../src/computed';

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

export function testComputed(): void {
  console.log('\n--- computed() tests ---');

  // Test: 基本计算属性
  {
    const state = reactive({ a: 1, b: 2 });
    const sum = computed(() => state.a + state.b);

    assertEqual(sum.value, 3, 'Computed value is correct');
  }

  // Test: 惰性求值（缓存）
  {
    const state = reactive({ x: 1 });
    let evalCount = 0;

    const doubled = computed(() => {
      evalCount++;
      return state.x * 2;
    });

    // 第一次访问触发求值
    assertEqual(doubled.value, 2, 'First access returns correct value');
    assertEqual(evalCount, 1, 'Getter called once on first access');

    // 第二次访问不重新求值（缓存）
    assertEqual(doubled.value, 2, 'Second access returns cached value');
    assertEqual(evalCount, 1, 'Getter not called again (cached)');

    // 依赖变化后重新求值
    state.x = 5;
    assertEqual(doubled.value, 10, 'Re-evaluated after dependency change');
    assertEqual(evalCount, 2, 'Getter called again after change');
  }

  // Test: 链式计算属性
  {
    const state = reactive({ price: 100, tax: 0.1 });
    const taxAmount = computed(() => state.price * state.tax);
    const total = computed(() => state.price + taxAmount.value);

    assertEqual(taxAmount.value, 10, 'Tax amount is correct');
    assertEqual(total.value, 110, 'Total is correct');

    state.price = 200;
    assertEqual(taxAmount.value, 20, 'Tax amount updated');
    assertEqual(total.value, 220, 'Total updated');
  }

  // Test: computed 作为 watcher 的数据源
  {
    const state = reactive({ items: [1, 2, 3] });
    const total = computed(() => state.items.reduce((s, n) => s + n, 0));

    let watchValue = 0;
    const { Watcher } = require('../src/watcher');
    const watcher = new Watcher(
      () => total.value,
      (newVal: number) => { watchValue = newVal; },
      { sync: true }
    );

    // 修改已追踪的元素（reduce 追踪了 items[0], items[1], items[2]）
    state.items[0] = 10;
    assertEqual(total.value, 15, 'Computed updates when tracked element changes');
    assertEqual(watchValue, 15, 'Watcher triggered by computed change');

    watcher.teardown();
  }

  console.log(`\n  computed() results: ${passed} passed, ${failed} failed`);
}
