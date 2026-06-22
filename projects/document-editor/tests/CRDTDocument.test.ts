/**
 * CRDT Document Tests
 *
 * Tests the core CRDT functionality including:
 * - Basic insert/delete operations
 * - Concurrent operation convergence
 * - Remote operation application
 */

import { CRDTDocument } from '../src/crdt/CRDTDocument';

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
    console.log(`  ✗ ${message} (expected: "${expected}", got: "${actual}")`);
  }
}

export function runCRDTTests(): void {
  console.log('\n=== CRDT Document Tests ===\n');

  // Test 1: Basic insertion
  console.log('Test 1: Basic insertion');
  {
    const doc = new CRDTDocument('site1');
    doc.insert(0, 'H');
    doc.insert(1, 'e');
    doc.insert(2, 'l');
    doc.insert(3, 'l');
    doc.insert(4, 'o');
    assertEqual(doc.getText(), 'Hello', 'Should insert characters sequentially');
    assertEqual(doc.length, 5, 'Length should be 5');
  }

  // Test 2: Insert at beginning
  console.log('\nTest 2: Insert at beginning');
  {
    const doc = new CRDTDocument('site1');
    doc.insert(0, 'World');
    doc.insert(0, 'Hello ');
    assertEqual(doc.getText(), 'Hello World', 'Should insert at beginning');
  }

  // Test 3: Deletion
  console.log('\nTest 3: Deletion');
  {
    const doc = new CRDTDocument('site1');
    doc.insert(0, 'Hello World');
    doc.delete(5); // Delete space
    assertEqual(doc.getText(), 'HelloWorld', 'Should delete character at position');
  }

  // Test 4: Multiple deletions
  console.log('\nTest 4: Multiple deletions');
  {
    const doc = new CRDTDocument('site1');
    doc.insert(0, 'Hello World');
    // Delete " World" (positions 5-10)
    for (let i = 0; i < 6; i++) {
      doc.delete(5);
    }
    assertEqual(doc.getText(), 'Hello', 'Should delete multiple characters');
  }

  // Test 5: Two independent replicas converge
  console.log('\nTest 5: Two replicas converge (sequential inserts)');
  {
    const doc1 = new CRDTDocument('site1');
    const doc2 = new CRDTDocument('site2');

    // Both start with "Hello"
    const ops1: any[] = [];
    for (let i = 0; i < 5; i++) {
      const { op } = doc1.insert(i, 'Hello'[i]);
      ops1.push(op);
    }

    // Apply doc1's operations to doc2
    for (const op of ops1) {
      doc2.applyRemoteOp(op);
    }

    assertEqual(doc1.getText(), 'Hello', 'Doc1 should have "Hello"');
    assertEqual(doc2.getText(), 'Hello', 'Doc2 should converge to "Hello"');
  }

  // Test 6: Concurrent inserts from different sites
  console.log('\nTest 6: Concurrent inserts convergence');
  {
    const doc1 = new CRDTDocument('site1');
    const doc2 = new CRDTDocument('site2');

    // Both insert at position 0 concurrently
    const { op: op1 } = doc1.insert(0, 'A');
    const { op: op2 } = doc2.insert(0, 'B');

    // Apply remote operations
    doc1.applyRemoteOp(op2);
    doc2.applyRemoteOp(op1);

    // Both should have the same text (order determined by tie-breaking)
    assertEqual(doc1.getText(), doc2.getText(), 'Both replicas should converge to same text');
    assertEqual(doc1.getText().length, 2, 'Both characters should be present');
  }

  // Test 7: Concurrent delete and insert
  console.log('\nTest 7: Concurrent delete and insert');
  {
    const doc1 = new CRDTDocument('site1');
    const doc2 = new CRDTDocument('site2');

    // Set up shared state: "Hello"
    const setupOps: any[] = [];
    for (let i = 0; i < 5; i++) {
      const { op } = doc1.insert(i, 'Hello'[i]);
      setupOps.push(op);
    }
    for (const op of setupOps) {
      doc2.applyRemoteOp(op);
    }

    // doc1 deletes 'o', doc2 inserts '!' after 'o'
    const delOp = doc1.delete(4); // Delete 'o'
    const { op: insOp } = doc2.insert(5, '!'); // Insert after 'o'

    // Apply remote operations
    if (delOp) doc2.applyRemoteOp(delOp);
    doc1.applyRemoteOp(insOp);

    // Both should converge (delete is logical/tombstone)
    assertEqual(doc1.getText(), doc2.getText(), 'Concurrent delete+insert should converge');
  }

  // Test 8: Export and import state
  console.log('\nTest 8: Export and import state');
  {
    const doc1 = new CRDTDocument('site1');
    doc1.insert(0, 'Hello');
    doc1.insert(5, ' World');

    const state = doc1.exportState();
    const doc2 = new CRDTDocument('site2');
    doc2.importState(state);

    assertEqual(doc1.getText(), doc2.getText(), 'Imported doc should match exported doc');
  }

  // Test 9: Empty document
  console.log('\nTest 9: Empty document');
  {
    const doc = new CRDTDocument('site1');
    assertEqual(doc.getText(), '', 'Empty document should have empty text');
    assertEqual(doc.length, 0, 'Empty document should have length 0');
    assert(doc.isEmpty, 'Empty document should report isEmpty');
  }

  // Test 10: GetCharacters
  console.log('\nTest 10: GetCharacters');
  {
    const doc = new CRDTDocument('site1');
    doc.insert(0, 'AB');
    doc.delete(0); // Delete 'A'

    const chars = doc.getCharacters();
    assertEqual(chars.filter(c => !c.deleted).length, 1, 'Should have 1 non-deleted character');
    assertEqual(chars.filter(c => c.deleted).length, 1, 'Should have 1 deleted character');
  }

  console.log(`\n=== CRDT Tests Complete: ${passed} passed, ${failed} failed ===\n`);
}

// Run if executed directly
if (require.main === module) {
  runCRDTTests();
  process.exit(failed > 0 ? 1 : 0);
}
