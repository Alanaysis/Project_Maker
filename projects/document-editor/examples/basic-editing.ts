/**
 * ============================================================
 * Example: Basic Editing
 * ============================================================
 *
 * Demonstrates basic text editing operations with the DocumentEditor.
 *
 * Run: npx ts-node examples/basic-editing.ts
 */

import { DocumentEditor } from '../src/editor/DocumentEditor';

console.log('=== Basic Editing Example ===\n');

// Create an editor instance
const editor = new DocumentEditor({
  siteId: 'user-1',
  authorName: 'Alice',
});

// 1. Insert text
console.log('1. Inserting text...');
editor.insertText('Hello');
console.log(`   Text: "${editor.getText()}"`);
console.log(`   Length: ${editor.length}`);
console.log(`   Cursor: ${editor.getCursor()}`);

// 2. Insert more text
console.log('\n2. Inserting more text...');
editor.insertText(' World');
console.log(`   Text: "${editor.getText()}"`);

// 3. Delete text
console.log('\n3. Deleting text...');
editor.deleteBefore(6); // Delete " World"
console.log(`   After deleting: "${editor.getText()}"`);

// 4. Insert at specific position
console.log('\n4. Inserting at position...');
editor.insertTextAt(5, ' Beautiful');
console.log(`   Text: "${editor.getText()}"`);

// 5. Delete a range
console.log('\n5. Deleting range...');
editor.deleteRange(5, 15); // Delete " Beautiful"
console.log(`   Text: "${editor.getText()}"`);

// 6. Move cursor and insert
console.log('\n6. Moving cursor and inserting...');
editor.setCursor(5);
editor.insertText(' Dear');
console.log(`   Text: "${editor.getText()}"`);
console.log(`   Cursor: ${editor.getCursor()}`);

// 7. Get formatted content
console.log('\n7. Formatted content:');
const spans = editor.getFormattedContent();
for (const span of spans) {
  const marks = span.marks.length > 0 ? ` [${span.marks.join(', ')}]` : '';
  console.log(`   "${span.text}"${marks}`);
}

console.log('\n=== Basic Editing Complete ===');
