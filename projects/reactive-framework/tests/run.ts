/**
 * 测试运行器
 */

import { testReactive } from './test_reactive';
import { testComputed } from './test_computed';
import { testWatch } from './test_watch';
import { testEdgeCases } from './test_edge_cases';

console.log('=== Reactive Framework Tests ===');

let totalPassed = 0;
let totalFailed = 0;

// 运行所有测试套件
testReactive();
testComputed();
testWatch();
testEdgeCases();

console.log('\n=== Test Summary ===');
console.log('All test suites completed.');
