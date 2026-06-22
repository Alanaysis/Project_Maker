/**
 * Document Editor Tests
 *
 * Tests the main editor class including:
 * - Text insertion and deletion
 * - Formatting operations
 * - Version control
 * - Collaboration (simulated)
 */

import { DocumentEditor } from '../src/editor/DocumentEditor';
import { CRDTOperation } from '../src/crdt/CRDTDocument';

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

export function runEditorTests(): void {
  console.log('\n=== Document Editor Tests ===\n');

  // Test 1: Basic text insertion
  console.log('Test 1: Basic text insertion');
  {
    const editor = new DocumentEditor({ siteId: 'test1', authorName: 'Alice' });
    editor.insertText('Hello');
    assertEqual(editor.getText(), 'Hello', 'Should insert "Hello"');
    assertEqual(editor.length, 5, 'Length should be 5');
  }

  // Test 2: Text deletion
  console.log('\nTest 2: Text deletion');
  {
    const editor = new DocumentEditor({ siteId: 'test1', authorName: 'Alice' });
    editor.insertText('Hello World');
    editor.deleteBefore(6); // Delete "World" + space
    assertEqual(editor.getText(), 'Hello', 'Should delete characters before cursor');
  }

  // Test 3: Insert at specific position
  console.log('\nTest 3: Insert at specific position');
  {
    const editor = new DocumentEditor({ siteId: 'test1', authorName: 'Alice' });
    editor.insertText('Hello World');
    editor.insertTextAt(5, ' Beautiful');
    assertEqual(editor.getText(), 'Hello Beautiful World', 'Should insert at position 5');
  }

  // Test 4: Delete range
  console.log('\nTest 4: Delete range');
  {
    const editor = new DocumentEditor({ siteId: 'test1', authorName: 'Alice' });
    editor.insertText('Hello Beautiful World');
    editor.deleteRange(5, 15); // Delete " Beautiful"
    assertEqual(editor.getText(), 'Hello World', 'Should delete range');
  }

  // Test 5: Apply bold formatting
  console.log('\nTest 5: Apply bold formatting');
  {
    const editor = new DocumentEditor({ siteId: 'test1', authorName: 'Alice' });
    editor.insertText('Hello World');
    editor.applyFormat('bold', 0, 5);

    const spans = editor.getFormattedContent();
    const helloSpan = spans.find(s => s.text === 'Hello');
    assert(helloSpan !== undefined, 'Should find "Hello" span');
    assert(helloSpan!.marks.includes('bold'), '"Hello" should be bold');

    const worldSpan = spans.find(s => s.text === ' World');
    assert(worldSpan !== undefined, 'Should find " World" span');
    assert(!worldSpan!.marks.includes('bold'), '"World" should not be bold');
  }

  // Test 6: Toggle formatting
  console.log('\nTest 6: Toggle formatting');
  {
    const editor = new DocumentEditor({ siteId: 'test1', authorName: 'Alice' });
    editor.insertText('Hello');

    editor.toggleFormat('bold', 0, 5);
    let marks = editor.getFormatManager().getMarksAt(2);
    assert(marks.includes('bold'), 'Should be bold after first toggle');

    editor.toggleFormat('bold', 0, 5);
    marks = editor.getFormatManager().getMarksAt(2);
    assert(!marks.includes('bold'), 'Should not be bold after second toggle');
  }

  // Test 7: Version history
  console.log('\nTest 7: Version history');
  {
    const editor = new DocumentEditor({ siteId: 'test1', authorName: 'Alice' });
    editor.insertText('Hello');
    editor.commit('Version 1');

    editor.insertText(' World');
    editor.commit('Version 2');

    const versions = editor.getVersions();
    assertEqual(versions.length, 2, 'Should have 2 versions');
    assertEqual(versions[0].text, 'Hello', 'First version should have "Hello"');
    assertEqual(versions[1].text, 'Hello World', 'Second version should have "Hello World"');
  }

  // Test 8: Revert to previous version
  console.log('\nTest 8: Revert to previous version');
  {
    const editor = new DocumentEditor({ siteId: 'test1', authorName: 'Alice' });
    editor.insertText('Hello');
    const v1 = editor.commit('Version 1');

    editor.insertText(' World');
    editor.commit('Version 2');

    editor.revertTo(v1.id);
    assertEqual(editor.getText(), 'Hello', 'Should revert to version 1');
  }

  // Test 9: Tag a version
  console.log('\nTest 9: Tag a version');
  {
    const editor = new DocumentEditor({ siteId: 'test1', authorName: 'Alice' });
    editor.insertText('Release version');
    const v = editor.commit('Release', 'v1.0');

    assertEqual(v.tag, 'v1.0', 'Version should have tag "v1.0"');
  }

  // Test 10: Collaboration - simulated remote operations
  console.log('\nTest 10: Collaboration - simulated remote operations');
  {
    const editor1 = new DocumentEditor({ siteId: 'site1', authorName: 'Alice' });
    const editor2 = new DocumentEditor({ siteId: 'site2', authorName: 'Bob' });

    // Alice inserts text
    editor1.insertText('Hello');
    const doc1 = editor1.getDocument();
    const chars1 = doc1.getCharacters();

    // Get Alice's operations and apply to Bob
    // (In a real system, these would be transmitted over the network)
    for (const char of chars1) {
      if (!char.deleted) {
        // Simulate the insert operation
        const op: CRDTOperation = {
          type: 'insert',
          char: {
            id: char.id,
            value: char.char,
            deleted: false,
            parentId: null,
            timestamp: Date.now(),
          },
          siteId: 'site1',
          clock: char.id.clock,
        };
        editor2.applyRemoteOperation(op);
      }
    }

    // Bob should see Alice's text (may be in different order due to CRDT, but same content)
    assertEqual(editor2.getText().length, 5, 'Bob should see 5 characters');
  }

  // Test 11: Cursor operations
  console.log('\nTest 11: Cursor operations');
  {
    const editor = new DocumentEditor({ siteId: 'test1', authorName: 'Alice' });
    editor.insertText('Hello');
    editor.setCursor(3);
    assertEqual(editor.getCursor(), 3, 'Cursor should be at position 3');

    editor.setCursor(10); // Beyond end
    assertEqual(editor.getCursor(), 5, 'Cursor should be clamped to document length');

    editor.setCursor(-1); // Before start
    assertEqual(editor.getCursor(), 0, 'Cursor should be clamped to 0');
  }

  // Test 12: Render with formatting
  console.log('\nTest 12: Render with formatting');
  {
    const editor = new DocumentEditor({ siteId: 'test1', authorName: 'Alice' });
    editor.insertText('Hello World');
    editor.applyFormat('bold', 0, 5);
    editor.applyFormat('italic', 6, 11);

    const rendered = editor.render();
    assert(rendered.includes('**Hello**'), 'Should render bold as **text**');
    assert(rendered.includes('*World*'), 'Should render italic as *text*');
  }

  // Test 13: Event listeners
  console.log('\nTest 13: Event listeners');
  {
    const editor = new DocumentEditor({ siteId: 'test1', authorName: 'Alice' });
    let changeCount = 0;
    editor.on('text:change', () => changeCount++);

    editor.insertText('A');
    editor.insertText('B');
    editor.deleteBefore(1);

    assertEqual(changeCount, 3, 'Should fire 3 text:change events');
  }

  // Test 14: Collaboration session
  console.log('\nTest 14: Collaboration session');
  {
    const editor = new DocumentEditor({ siteId: 'test1', authorName: 'Alice' });
    editor.joinSession('Alice');
    assert(editor.getPeers().length === 1, 'Should have 1 peer after joining');

    editor.leaveSession();
    const peers = editor.getPeers();
    assert(peers.length === 0 || !peers[0].connected, 'Should have no connected peers after leaving');
  }

  // Test 15: Diff between versions
  console.log('\nTest 15: Diff between versions');
  {
    const editor = new DocumentEditor({ siteId: 'test1', authorName: 'Alice' });
    editor.insertText('Hello');
    const v1 = editor.commit('Version 1');

    editor.insertText(' World');
    const diffs = editor.diffWith(v1.id);
    assertEqual(diffs.length, 1, 'Should have 1 diff');
    assertEqual(diffs[0].added, ' World', 'Should show " World" was added');
  }

  console.log(`\n=== Editor Tests Complete: ${passed} passed, ${failed} failed ===\n`);
}

if (require.main === module) {
  runEditorTests();
  process.exit(failed > 0 ? 1 : 0);
}
