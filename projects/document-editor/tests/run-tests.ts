/**
 * Test Runner
 *
 * Runs all test suites for the document editor.
 */

import { runCRDTTests } from './CRDTDocument.test';
import { runFormatTests } from './FormatManager.test';
import { runVersionHistoryTests } from './VersionHistory.test';
import { runEditorTests } from './DocumentEditor.test';

console.log('╔════════════════════════════════════════════════════════════╗');
console.log('║           Document Editor - Test Suite                    ║');
console.log('╚════════════════════════════════════════════════════════════╝');

let totalPassed = 0;
let totalFailed = 0;

// Capture test results by wrapping console.log
const originalLog = console.log;
const results: string[] = [];

function runSuite(name: string, fn: () => void): void {
  const passed = { count: 0 };
  const failed = { count: 0 };

  // Run the test suite
  fn();
}

// Run all test suites
runSuite('CRDT Document', runCRDTTests);
runSuite('Format Manager', runFormatTests);
runSuite('Version History', runVersionHistoryTests);
runSuite('Document Editor', runEditorTests);

console.log('\n╔════════════════════════════════════════════════════════════╗');
console.log('║                    ALL TESTS COMPLETE                     ║');
console.log('╚════════════════════════════════════════════════════════════╝');
