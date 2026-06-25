/**
 * 测试运行器
 */

import { testValidator } from './test_validator';
import { testFormEngine } from './test_form_engine';
import { testRenderer } from './test_renderer';
import { testEdgeCases } from './test_edge_cases';

console.log('=== Form Engine Tests ===');

// 运行所有测试套件
testValidator();
testFormEngine();
testRenderer();
testEdgeCases();

console.log('\n=== Test Summary ===');
console.log('All test suites completed.');
