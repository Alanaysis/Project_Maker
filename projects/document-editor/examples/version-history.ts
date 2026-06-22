/**
 * ============================================================
 * Example: Version History
 * ============================================================
 *
 * Demonstrates version control features including commits,
 * tags, diffs, and reverting.
 *
 * Run: npx ts-node examples/version-history.ts
 */

import { DocumentEditor } from '../src/editor/DocumentEditor';

console.log('=== Version History Example ===\n');

const editor = new DocumentEditor({
  siteId: 'user-1',
  authorName: 'Alice',
});

// Create initial version
console.log('1. Creating initial version...');
editor.insertText('The quick brown fox');
const v1 = editor.commit('Initial draft', 'draft-1');
console.log(`   Version: ${v1.id} - "${v1.text}"`);
console.log(`   Tag: ${v1.tag}`);

// Edit and commit
console.log('\n2. Editing and committing...');
editor.insertText(' jumps over the lazy dog');
const v2 = editor.commit('Complete sentence');
console.log(`   Version: ${v2.id} - "${v2.text}"`);

// More edits
console.log('\n3. More edits...');
editor.setCursor(4);
editor.insertText('very ');
const v3 = editor.commit('Added emphasis');
console.log(`   Version: ${v3.id} - "${editor.getText()}"`);

// View all versions
console.log('\n4. All versions:');
const versions = editor.getVersions();
for (const v of versions) {
  console.log(`   ${v.id}: "${v.text}" by ${v.author} - ${v.message}`);
}

// Compute diff
console.log('\n5. Diff between v3 and v1:');
const diffs = editor.diffWith(v1.id);
for (const diff of diffs) {
  console.log(`   Type: ${diff.type}`);
  console.log(`   Position: ${diff.position}`);
  console.log(`   Removed: "${diff.removed}"`);
  console.log(`   Added: "${diff.added}"`);
}

// Revert to v1
console.log('\n6. Reverting to v1...');
editor.revertTo(v1.id);
console.log(`   After revert: "${editor.getText()}"`);

// Tag the reverted version
console.log('\n7. Tagging the reverted version...');
const currentVersion = editor.getVersions()[editor.getVersions().length - 1];
editor.getVersions(); // Refresh
console.log(`   Current versions: ${editor.getVersions().length}`);

console.log('\n=== Version History Complete ===');
