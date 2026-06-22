/**
 * Version History Tests
 *
 * Tests the version control functionality including:
 * - Creating versions (commits)
 * - Reverting to previous versions
 * - Tagging versions
 * - Computing diffs
 */

import { VersionHistory } from '../src/history/VersionHistory';

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

export function runVersionHistoryTests(): void {
  console.log('\n=== Version History Tests ===\n');

  // Test 1: Create initial version
  console.log('Test 1: Create initial version');
  {
    const history = new VersionHistory();
    const v = history.commit('Hello', [], 'Alice', 'Initial commit');
    assertEqual(v.text, 'Hello', 'Version should contain "Hello"');
    assertEqual(v.author, 'Alice', 'Author should be Alice');
    assertEqual(v.parentId, null, 'First version should have no parent');
    assertEqual(history.size, 1, 'Should have 1 version');
  }

  // Test 2: Create multiple versions
  console.log('\nTest 2: Create multiple versions');
  {
    const history = new VersionHistory();
    history.commit('Hello', [], 'Alice', 'v1');
    history.commit('Hello World', [], 'Bob', 'v2');
    history.commit('Hello World!', [], 'Alice', 'v3');

    assertEqual(history.size, 3, 'Should have 3 versions');
    const versions = history.getAllVersions();
    assertEqual(versions.length, 3, 'Should return all 3 versions');
    assertEqual(versions[2].text, 'Hello World!', 'Latest version should have correct text');
  }

  // Test 3: Get current version
  console.log('\nTest 3: Get current version');
  {
    const history = new VersionHistory();
    history.commit('A', [], 'Alice', 'v1');
    history.commit('AB', [], 'Alice', 'v2');

    const current = history.getCurrentVersion();
    assert(current !== undefined, 'Should have a current version');
    assertEqual(current!.text, 'AB', 'Current version should have latest text');
  }

  // Test 4: Revert to a version
  console.log('\nTest 4: Revert to a version');
  {
    const history = new VersionHistory();
    const v1 = history.commit('Hello', [], 'Alice', 'v1');
    history.commit('Hello World', [], 'Alice', 'v2');

    const reverted = history.revertTo(v1.id);
    assert(reverted !== undefined, 'Revert should succeed');
    assertEqual(reverted!.text, 'Hello', 'Reverted version should have v1 text');
    assertEqual(history.size, 3, 'Should have 3 versions (including revert)');
  }

  // Test 5: Tag a version
  console.log('\nTest 5: Tag a version');
  {
    const history = new VersionHistory();
    const v1 = history.commit('Hello', [], 'Alice', 'v1');
    history.tagVersion(v1.id, 'v1.0-release');

    const tagged = history.getVersionByTag('v1.0-release');
    assert(tagged !== undefined, 'Should find version by tag');
    assertEqual(tagged!.id, v1.id, 'Tagged version should be v1');
  }

  // Test 6: Compute diff - insert
  console.log('\nTest 6: Compute diff - insert');
  {
    const history = new VersionHistory();
    const diffs = history.computeDiff('Hello', 'Hello World');
    assertEqual(diffs.length, 1, 'Should have 1 diff');
    assertEqual(diffs[0].type, 'insert', 'Diff type should be insert');
    assertEqual(diffs[0].added, ' World', 'Should add " World"');
    assertEqual(diffs[0].removed, '', 'Should remove nothing');
  }

  // Test 7: Compute diff - delete
  console.log('\nTest 7: Compute diff - delete');
  {
    const history = new VersionHistory();
    const diffs = history.computeDiff('Hello World', 'Hello');
    assertEqual(diffs.length, 1, 'Should have 1 diff');
    assertEqual(diffs[0].type, 'delete', 'Diff type should be delete');
    assertEqual(diffs[0].removed, ' World', 'Should remove " World"');
  }

  // Test 8: Compute diff - replace
  console.log('\nTest 8: Compute diff - replace');
  {
    const history = new VersionHistory();
    const diffs = history.computeDiff('Hello World', 'Hi World');
    assertEqual(diffs.length, 1, 'Should have 1 diff');
    assertEqual(diffs[0].type, 'replace', 'Diff type should be replace');
    assertEqual(diffs[0].removed, 'Hello', 'Should remove "Hello"');
    assertEqual(diffs[0].added, 'Hi', 'Should add "Hi"');
  }

  // Test 9: Compute diff - no change
  console.log('\nTest 9: Compute diff - no change');
  {
    const history = new VersionHistory();
    const diffs = history.computeDiff('Hello', 'Hello');
    assertEqual(diffs.length, 0, 'Should have no diffs for identical text');
  }

  // Test 10: Export and import
  console.log('\nTest 10: Export and import');
  {
    const history1 = new VersionHistory();
    history1.commit('A', [], 'Alice', 'v1');
    history1.commit('AB', [], 'Bob', 'v2');

    const state = history1.exportState();
    const history2 = new VersionHistory();
    history2.importState(state);

    assertEqual(history2.size, 2, 'Imported history should have 2 versions');
    const current = history2.getCurrentVersion();
    assertEqual(current!.text, 'AB', 'Imported current version should match');
  }

  console.log(`\n=== Version History Tests Complete: ${passed} passed, ${failed} failed ===\n`);
}

if (require.main === module) {
  runVersionHistoryTests();
  process.exit(failed > 0 ? 1 : 0);
}
