/**
 * ============================================================
 * Example: Collaborative Editing
 * ============================================================
 *
 * Demonstrates real-time collaborative editing between two peers
 * using CRDT-based conflict resolution.
 *
 * Run: npx ts-node examples/collaborative-editing.ts
 *
 * ⭐ KEY CONCEPT: CRDT Convergence
 * Both peers edit independently, and their documents converge
 * to the same state without a central coordinator.
 */

import { DocumentEditor } from '../src/editor/DocumentEditor';

console.log('=== Collaborative Editing Example ===\n');

// Create two editor instances (simulating two users)
const alice = new DocumentEditor({
  siteId: 'alice',
  authorName: 'Alice',
});

const bob = new DocumentEditor({
  siteId: 'bob',
  authorName: 'Bob',
});

// Join collaboration session
alice.joinSession('Alice');
bob.joinSession('Bob');

console.log('1. Alice and Bob join the session');
console.log(`   Alice's peers: ${alice.getPeers().map(p => p.name).join(', ')}`);
console.log(`   Bob's peers: ${bob.getPeers().map(p => p.name).join(', ')}`);

// Alice types first
console.log('\n2. Alice types "Hello "');
alice.insertText('Hello ');
console.log(`   Alice's doc: "${alice.getText()}"`);
console.log(`   Bob's doc: "${bob.getText()}" (not synced yet)`);

// Simulate sending Alice's operations to Bob
console.log('\n3. Syncing Alice -> Bob...');
const aliceDoc = alice.getDocument();
const aliceChars = aliceDoc.getCharacters();
for (const char of aliceChars) {
  if (!char.deleted) {
    // In a real system, this would be transmitted over WebSocket
    bob.applyRemoteOperation({
      type: 'insert',
      char: {
        id: char.id,
        value: char.char,
        deleted: false,
        parentId: null,
        timestamp: Date.now(),
      },
      siteId: 'alice',
      clock: char.id.clock,
    });
  }
}
console.log(`   Bob's doc after sync: "${bob.getText()}"`);

// Both edit concurrently
console.log('\n4. Concurrent editing:');
console.log('   Alice inserts "Dear" at position 6');
console.log('   Bob inserts "World" at position 6');

alice.insertTextAt(6, 'Dear');
bob.insertTextAt(6, 'World');

console.log(`   Alice's doc: "${alice.getText()}"`);
console.log(`   Bob's doc: "${bob.getText()}"`);

// Apply formatting
console.log('\n5. Applying formatting:');
alice.applyFormat('bold', 0, 5); // Bold "Hello"
console.log(`   Alice applies bold to "Hello"`);

const aliceSpans = alice.getFormattedContent();
console.log('   Alice\'s formatted content:');
for (const span of aliceSpans) {
  const marks = span.marks.length > 0 ? ` [${span.marks.join(', ')}]` : '';
  console.log(`     "${span.text}"${marks}`);
}

// Version control
console.log('\n6. Version control:');
alice.commit('Initial version');
alice.insertText('!');
const v2 = alice.commit('Added exclamation');

console.log(`   Alice created ${alice.getVersions().length} versions`);
console.log(`   Latest version: "${v2.text}"`);

// Revert to previous version
console.log('\n7. Reverting to v1:');
alice.revertTo(alice.getVersions()[0].id);
console.log(`   After revert: "${alice.getText()}"`);

// Leave session
console.log('\n8. Leaving session:');
alice.leaveSession();
bob.leaveSession();
console.log('   Both peers left the session');

console.log('\n=== Collaborative Editing Complete ===');
console.log('\n💡 KEY TAKEAWAY: CRDTs enable conflict-free merging');
console.log('   even when users edit simultaneously.');
