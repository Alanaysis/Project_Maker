/**
 * Format Manager Tests
 *
 * Tests the rich text formatting functionality including:
 * - Applying and removing marks
 * - Getting marks at specific positions
 * - Format span generation
 * - Position adjustment after insert/delete
 */

import { FormatManager } from '../src/formatting/FormatTypes';

let passed = 0;
let failed = 0;

function assert(condition: boolean, message: string): void {
  if (condition) {
    passed++;
    console.log(`  ✓ ${message}`);
  } else {
    failed++;
    console.log(`  ✗ ${message}`);
  }
}

function assertEqual(actual: any, expected: any, message: string): void {
  if (actual === expected) {
    passed++;
    console.log(`  ✓ ${message}`);
  } else {
    failed++;
    console.log(`  ✗ ${message} (expected: ${JSON.stringify(expected)}, got: ${JSON.stringify(actual)})`);
  }
}

export function runFormatTests(): void {
  console.log('\n=== Format Manager Tests ===\n');

  // Test 1: Apply bold mark
  console.log('Test 1: Apply bold mark');
  {
    const fm = new FormatManager();
    fm.applyMark('bold', 0, 5, 'site1');
    const marks = fm.getMarksAt(2);
    assertEqual(marks.length, 1, 'Should have 1 mark');
    assertEqual(marks[0], 'bold', 'Mark should be bold');
  }

  // Test 2: Apply italic mark
  console.log('\nTest 2: Apply italic mark');
  {
    const fm = new FormatManager();
    fm.applyMark('italic', 3, 8, 'site1');
    const marks = fm.getMarksAt(5);
    assertEqual(marks.length, 1, 'Should have 1 mark');
    assertEqual(marks[0], 'italic', 'Mark should be italic');
  }

  // Test 3: Multiple marks at same position
  console.log('\nTest 3: Multiple marks at same position');
  {
    const fm = new FormatManager();
    fm.applyMark('bold', 0, 10, 'site1');
    fm.applyMark('italic', 5, 15, 'site1');
    const marks = fm.getMarksAt(7);
    assertEqual(marks.length, 2, 'Should have 2 marks');
    assert(marks.includes('bold'), 'Should include bold');
    assert(marks.includes('italic'), 'Should include italic');
  }

  // Test 4: Remove mark
  console.log('\nTest 4: Remove mark');
  {
    const fm = new FormatManager();
    fm.applyMark('bold', 0, 10, 'site1');
    fm.removeMark('bold', 0, 10, 'site1');
    const marks = fm.getMarksAt(5);
    assertEqual(marks.length, 0, 'Should have no marks after removal');
  }

  // Test 5: Get formatted spans
  console.log('\nTest 5: Get formatted spans');
  {
    const fm = new FormatManager();
    fm.applyMark('bold', 0, 5, 'site1');
    const spans = fm.getFormattedSpans('Hello World');
    assert(spans.length >= 2, 'Should have at least 2 spans');
    assertEqual(spans[0].text, 'Hello', 'First span should be "Hello"');
    assert(spans[0].marks.includes('bold'), 'First span should be bold');
    assertEqual(spans[1].text, ' World', 'Second span should be " World"');
    assertEqual(spans[1].marks.length, 0, 'Second span should have no marks');
  }

  // Test 6: Adjust for insert
  console.log('\nTest 6: Adjust for insert');
  {
    const fm = new FormatManager();
    fm.applyMark('bold', 5, 10, 'site1');
    fm.adjustForInsert(3, 2); // Insert 2 chars at position 3
    const marks = fm.getMarksAt(7); // Position 5 shifted to 7
    assertEqual(marks.length, 1, 'Should have 1 mark at shifted position');
    assertEqual(marks[0], 'bold', 'Mark should be bold');
  }

  // Test 7: Adjust for delete
  console.log('\nTest 7: Adjust for delete');
  {
    const fm = new FormatManager();
    fm.applyMark('bold', 5, 10, 'site1');
    fm.adjustForDelete(2, 2); // Delete 2 chars at position 2
    const marks = fm.getMarksAt(3); // Position 5 shifted to 3
    assertEqual(marks.length, 1, 'Should have 1 mark at shifted position');
    assertEqual(marks[0], 'bold', 'Mark should be bold');
  }

  // Test 8: Export and import
  console.log('\nTest 8: Export and import');
  {
    const fm1 = new FormatManager();
    fm1.applyMark('bold', 0, 5, 'site1');
    fm1.applyMark('italic', 3, 8, 'site1');

    const state = fm1.exportState();
    const fm2 = new FormatManager();
    fm2.importState(state);

    const marks1 = fm1.getMarksAt(4);
    const marks2 = fm2.getMarksAt(4);
    assertEqual(marks1.length, marks2.length, 'Imported marks should match');
  }

  console.log(`\n=== Format Tests Complete: ${passed} passed, ${failed} failed ===\n`);
}

if (require.main === module) {
  runFormatTests();
  process.exit(failed > 0 ? 1 : 0);
}
